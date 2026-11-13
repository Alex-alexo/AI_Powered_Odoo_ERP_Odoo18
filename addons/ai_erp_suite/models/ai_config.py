import json
from urllib.parse import urlparse

import requests

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AIErpConfig(models.Model):
    _name = "ai.erp.config"
    _description = "AI ERP Provider Configuration"
    _rec_name = "company_id"

    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company,
        ondelete="cascade", index=True,
    )
    provider = fields.Selection(
        [("openai_compatible", "OpenAI-compatible API")],
        default="openai_compatible", required=True,
    )
    api_endpoint = fields.Char(
        string="Chat Completions Endpoint",
        required=True,
        default="https://api.openai.com/v1/chat/completions",
    )
    api_model = fields.Char(string="Model", required=True, default="gpt-4o-mini")
    api_key = fields.Char(string="API Key", groups="ai_erp_suite.group_ai_erp_manager")
    timeout_seconds = fields.Integer(default=45, required=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("company_unique", "unique(company_id)", "Only one AI provider configuration is allowed per company."),
    ]

    @api.constrains("api_endpoint", "timeout_seconds")
    def _check_endpoint_and_timeout(self):
        for rec in self:
            parsed = urlparse((rec.api_endpoint or "").strip())
            local_hosts = {"localhost", "127.0.0.1", "::1"}
            if parsed.scheme != "https" and not (parsed.scheme == "http" and parsed.hostname in local_hosts):
                raise ValidationError(_("Use an HTTPS endpoint. HTTP is allowed only for localhost/local development."))
            if not parsed.netloc:
                raise ValidationError(_("Enter a valid AI API endpoint."))
            if rec.timeout_seconds < 5 or rec.timeout_seconds > 180:
                raise ValidationError(_("Timeout must be between 5 and 180 seconds."))

    @api.model
    def get_company_config(self, company):
        return self.sudo().search([
            ("company_id", "=", company.id),
            ("active", "=", True),
        ], limit=1)

    def _request_chat(self, messages, json_mode=False):
        self.ensure_one()
        if not self.api_key:
            raise UserError(_("The AI API key has not been configured for this company."))
        headers = {
            "Authorization": "Bearer %s" % self.api_key.strip(),
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.api_model,
            "messages": messages,
            "temperature": 0.1,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        try:
            response = requests.post(
                self.api_endpoint.strip(),
                headers=headers,
                json=payload,
                timeout=(10, self.timeout_seconds),
            )
        except requests.RequestException as exc:
            raise UserError(_("Could not contact the configured AI service. Check the endpoint and network connection. Details: %s") % str(exc)) from exc
        if response.status_code >= 400:
            # Do not echo the response body: providers may include sensitive request details.
            raise UserError(_("The AI provider returned HTTP status %s. Check the provider configuration and model name.") % response.status_code)
        try:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise UserError(_("The AI provider returned an unexpected response format.")) from exc
        if not isinstance(content, str) or not content.strip():
            raise UserError(_("The AI provider returned an empty response."))
        return content.strip()

    def request_structured_json(self, messages):
        self.ensure_one()
        raw = self._request_chat(messages, json_mode=True)
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise UserError(_("The AI service did not return valid JSON. Please retry or use a different model.")) from exc
