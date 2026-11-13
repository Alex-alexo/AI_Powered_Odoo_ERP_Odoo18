from odoo import fields, models


class AIErpInsight(models.Model):
    _name = "ai.erp.insight"
    _description = "AI ERP Business Insight"
    _order = "create_date desc, id desc"

    title = fields.Char(required=True)
    category = fields.Selection([
        ("receivable", "Accounts Receivable"),
        ("inventory", "Inventory"),
        ("operations", "Operations"),
    ], required=True, default="operations")
    severity = fields.Selection([
        ("info", "Information"),
        ("warning", "Warning"),
        ("critical", "Critical"),
    ], required=True, default="info")
    description = fields.Text(required=True)
    recommendation = fields.Text()
    state = fields.Selection([
        ("open", "Open"), ("dismissed", "Dismissed"), ("resolved", "Resolved"),
    ], default="open", required=True)
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company, index=True)
    source_model = fields.Char()

    def action_dismiss(self):
        self.write({"state": "dismissed"})
        return True

    def action_reopen(self):
        self.write({"state": "open"})
        return True
