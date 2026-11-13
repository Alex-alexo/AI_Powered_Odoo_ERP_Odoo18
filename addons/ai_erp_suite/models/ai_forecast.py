from odoo import fields, models


class AIErpForecast(models.Model):
    _name = "ai.erp.forecast"
    _description = "AI ERP Inventory Demand Forecast"
    _order = "create_date desc, id desc"

    name = fields.Char(required=True)
    product_id = fields.Many2one("product.product", required=True, index=True)
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company, index=True)
    history_months = fields.Integer(required=True)
    history_start = fields.Date(required=True)
    history_end = fields.Date(required=True)
    horizon_days = fields.Integer(required=True)
    historical_qty = fields.Float(digits="Product Unit of Measure")
    average_monthly_qty = fields.Float(digits="Product Unit of Measure")
    forecast_qty = fields.Float(digits="Product Unit of Measure")
    current_free_qty = fields.Float(digits="Product Unit of Measure")
    recommended_replenishment_qty = fields.Float(digits="Product Unit of Measure")
    method = fields.Char(default="Simple historical monthly average")
    note = fields.Text()
