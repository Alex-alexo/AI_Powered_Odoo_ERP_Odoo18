from odoo import fields, models


class AIErpMessage(models.Model):
    _name = "ai.erp.message"
    _description = "AI ERP Conversation Message"
    _order = "id asc"

    conversation_id = fields.Many2one("ai.erp.conversation", required=True, ondelete="cascade", index=True)
    company_id = fields.Many2one("res.company", required=True, index=True)
    role = fields.Selection([
        ("user", "User"),
        ("assistant", "AI Assistant"),
    ], required=True)
    content = fields.Text(required=True)
