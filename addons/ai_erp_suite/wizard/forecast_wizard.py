from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta

from odoo import fields, models, _
from odoo.exceptions import AccessError, ValidationError


class AIErpForecastWizard(models.TransientModel):
    _name = "ai.erp.forecast.wizard"
    _description = "Inventory Demand Forecast Wizard"

    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)
    product_id = fields.Many2one("product.product", required=True, domain="[('active', '=', True)]")
    history_months = fields.Integer(default=6, required=True)
    horizon_days = fields.Integer(default=30, required=True)

    def action_generate_forecast(self):
        self.ensure_one()
        if self.company_id not in self.env.companies:
            raise AccessError(_("You do not have access to the selected company."))
        if not 3 <= self.history_months <= 24:
            raise ValidationError(_("History must be between 3 and 24 months."))
        if not 7 <= self.horizon_days <= 180:
            raise ValidationError(_("Forecast horizon must be between 7 and 180 days."))
        today = date.today()
        current_month_start = date(today.year, today.month, 1)
        start_date = current_month_start - relativedelta(months=self.history_months)
        start_dt = datetime.combine(start_date, time.min)
        end_dt = datetime.combine(current_month_start, time.min)
        lines = self.env["sale.order.line"].with_company(self.company_id).search([
            ("order_id.company_id", "=", self.company_id.id),
            ("product_id", "=", self.product_id.id),
            ("order_id.state", "in", ["sale", "done"]),
            ("order_id.date_order", ">=", fields.Datetime.to_string(start_dt)),
            ("order_id.date_order", "<", fields.Datetime.to_string(end_dt)),
        ])
        monthly = {}
        for offset in range(self.history_months):
            month = start_date + relativedelta(months=offset)
            monthly[(month.year, month.month)] = 0.0
        for line in lines:
            if not line.order_id.date_order:
                continue
            order_date = fields.Datetime.to_datetime(line.order_id.date_order)
            key = (order_date.year, order_date.month)
            if key in monthly:
                monthly[key] += line.product_uom._compute_quantity(line.product_uom_qty, self.product_id.uom_id)
        historical_total = sum(monthly.values())
        average_monthly = historical_total / float(self.history_months)
        forecast_qty = average_monthly * (self.horizon_days / 30.4375)
        product = self.product_id.with_company(self.company_id)
        free_qty = product.free_qty
        recommended = max(forecast_qty - free_qty, 0.0)
        forecast = self.env["ai.erp.forecast"].create({
            "name": _("%s - %s day forecast") % (product.display_name, self.horizon_days),
            "product_id": product.id,
            "company_id": self.company_id.id,
            "history_months": self.history_months,
            "history_start": start_date,
            "history_end": current_month_start - relativedelta(days=1),
            "horizon_days": self.horizon_days,
            "historical_qty": historical_total,
            "average_monthly_qty": average_monthly,
            "forecast_qty": forecast_qty,
            "current_free_qty": free_qty,
            "recommended_replenishment_qty": recommended,
            "method": "Simple historical monthly average (baseline)",
            "note": _("This is a baseline forecast calculated from confirmed sales order quantities. It is not a trained machine-learning model and does not yet account for seasonality, supplier lead time, safety stock, or planned promotions."),
        })
        return {
            "type": "ir.actions.act_window",
            "name": _("Inventory Forecast"),
            "res_model": "ai.erp.forecast",
            "res_id": forecast.id,
            "view_mode": "form",
            "target": "current",
        }
