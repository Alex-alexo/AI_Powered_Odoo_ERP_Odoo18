from odoo.tests.common import TransactionCase


class TestAIErpModels(TransactionCase):
    def test_conversation_creation_defaults(self):
        conversation = self.env["ai.erp.conversation"].create({
            "name": "Test conversation",
        })
        self.assertEqual(conversation.user_id, self.env.user)
        self.assertEqual(conversation.company_id, self.env.company)
        self.assertEqual(conversation.state, "open")

    def test_insight_creation(self):
        insight = self.env["ai.erp.insight"].create({
            "title": "Test alert",
            "category": "operations",
            "severity": "info",
            "description": "Test description",
        })
        self.assertEqual(insight.state, "open")
        self.assertEqual(insight.company_id, self.env.company)
