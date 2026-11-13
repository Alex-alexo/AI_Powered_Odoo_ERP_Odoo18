from odoo import fields, models, _
from odoo.exceptions import AccessError


class AIErpInsightWizard(models.TransientModel):
    _name = "ai.erp.insight.wizard"
    _description = "Generate ERP Business Alerts"

    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)

    def action_generate_insights(self):
        self.ensure_one()
        if self.company_id not in self.env.companies:
            raise AccessError(_("You do not have access to the selected company."))
        Insight = self.env["ai.erp.insight"]
        Move = self.env["account.move"].with_company(self.company_id)
        overdue = Move.search([
            ("company_id", "=", self.company_id.id),
            ("state", "=", "posted"),
            ("move_type", "=", "out_invoice"),
            ("payment_state", "!=", "paid"),
            ("invoice_date_due", "<", fields.Date.today()),
        ])
        created_ids = []
        if overdue:
            residual = sum(abs(move.amount_residual_signed) for move in overdue)
            currency = self.company_id.currency_id
            created = Insight.create({
                "title": _("Overdue customer invoices require attention"),
                "category": "receivable",
                "severity": "warning" if len(overdue) < 10 else "critical",
                "company_id": self.company_id.id,
                "source_model": "account.move",
                "description": _("There are %s posted customer invoices past their due date, with a combined outstanding balance of %s %s in company currency.") % (len(overdue), currency.round(residual), currency.name),
                "recommendation": _("Review the aged receivables report, confirm disputed balances, and follow your approved collection process."),
            })
            created_ids.append(created.id)
        products = self.env["product.product"].with_company(self.company_id).search(
            [("active", "=", True)], limit=500
        )
        for product in products.filtered(lambda p: p.free_qty <= 0)[:20]:
            created = Insight.create({
                "title": _("No free stock: %s") % product.display_name,
                "category": "inventory",
                "severity": "warning",
                "company_id": self.company_id.id,
                "source_model": "product.product",
                "description": _("The product currently has zero or negative free quantity in the selected company context."),
                "recommendation": _("Review forecast demand, incoming receipts, reservations, and replenishment rules before creating a purchase order."),
            })
            created_ids.append(created.id)
        if not created_ids:
            created = Insight.create({
                "title": _("No rule-based alerts found"),
                "category": "operations",
                "severity": "info",
                "company_id": self.company_id.id,
                "description": _("The current checks did not find overdue customer invoices or zero/negative free stock in the sampled active products."),
                "recommendation": _("Run the checks again after new transactions are recorded. This does not replace a full audit or management review."),
            })
            created_ids.append(created.id)
        return {
            "type": "ir.actions.act_window",
            "name": _("Generated Business Insights"),
            "res_model": "ai.erp.insight",
            "view_mode": "list,form",
            "domain": [("id", "in", created_ids)],
            "target": "current",
        }
