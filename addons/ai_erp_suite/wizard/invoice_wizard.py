import base64
import io
from datetime import date

from odoo import fields, models, _, Command
from odoo.exceptions import AccessError, UserError, ValidationError


class AIErpInvoiceWizard(models.TransientModel):
    _name = "ai.erp.invoice.wizard"
    _description = "AI Supplier Invoice Extraction Wizard"

    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)
    file_data = fields.Binary(string="Supplier Invoice PDF", required=True, attachment=False)
    file_name = fields.Char(required=True)
    vendor_name = fields.Char(readonly=True)
    partner_id = fields.Many2one("res.partner", string="Supplier", domain="[('supplier_rank', '>', 0)]")
    invoice_reference = fields.Char(readonly=True)
    invoice_date = fields.Date(readonly=True)
    currency_id = fields.Many2one("res.currency", default=lambda self: self.env.company.currency_id)
    extracted_total = fields.Float(readonly=True)
    extraction_status = fields.Selection([
        ("draft", "Not extracted"), ("extracted", "Extracted - review required"),
    ], default="draft", readonly=True)
    line_ids = fields.One2many("ai.erp.invoice.line.wizard", "wizard_id", string="Extracted Invoice Lines")
    expense_account_id = fields.Many2one("account.account", string="Expense / Asset Account")
    tax_ids = fields.Many2many("account.tax", string="Purchase Taxes", domain="[('type_tax_use', '=', 'purchase')]" )

    def _extract_pdf_text(self):
        self.ensure_one()
        if self.company_id not in self.env.companies:
            raise AccessError(_("You do not have access to the selected company."))
        if not self.file_data:
            raise ValidationError(_("Upload a PDF invoice first."))
        raw = base64.b64decode(self.file_data)
        if len(raw) > 12 * 1024 * 1024:
            raise ValidationError(_("The PDF must be 12 MB or smaller."))
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise UserError(_("The pypdf package is missing. Install the requirements listed in the project README.")) from exc
        try:
            reader = PdfReader(io.BytesIO(raw))
            if reader.is_encrypted:
                raise UserError(_("Encrypted PDFs are not supported. Upload an unlocked PDF."))
            if len(reader.pages) > 20:
                raise UserError(_("The MVP supports invoices up to 20 pages."))
            text_parts = [(page.extract_text() or "") for page in reader.pages]
            text = "\n".join(text_parts).strip()
        except UserError:
            raise
        except Exception as exc:
            raise UserError(_("Could not read this PDF. Please check that it is a valid PDF file.")) from exc
        if not text:
            raise UserError(_("No selectable text was found. This MVP needs a text-based PDF; scanned invoices require an OCR service such as Tesseract or a document AI provider."))
        return text[:30000]

    def action_extract_invoice(self):
        self.ensure_one()
        if self.company_id not in self.env.companies:
            raise AccessError(_("You do not have access to the selected company."))
        config = self.env["ai.erp.config"].get_company_config(self.company_id)
        if not config or not config.api_key:
            raise UserError(_("Configure an AI provider first in AI ERP → Configuration."))
        invoice_text = self._extract_pdf_text()
        messages = [
            {
                "role": "system",
                "content": (
                    "Extract supplier invoice data from the supplied text. Return only a valid JSON object. "
                    "Use this schema: {vendor_name: string|null, invoice_number: string|null, "
                    "invoice_date: YYYY-MM-DD|null, currency_code: ISO currency code|null, "
                    "total: number|null, lines: [{description: string, quantity: number, unit_price: number}]}. "
                    "Do not invent missing values. If a line cannot be identified, omit it. "
                    "Do not calculate or guess tax rates. Amounts must be numeric without currency symbols."
                ),
            },
            {"role": "user", "content": "Invoice text:\n" + invoice_text},
        ]
        data = config.request_structured_json(messages)
        if not isinstance(data, dict) or not isinstance(data.get("lines", []), list):
            raise UserError(_("The AI returned an invalid invoice structure."))
        vendor_name = str(data.get("vendor_name") or "").strip()
        invoice_number = str(data.get("invoice_number") or "").strip()
        invoice_date = False
        if data.get("invoice_date"):
            try:
                invoice_date = fields.Date.to_date(data["invoice_date"])
            except (ValueError, TypeError):
                invoice_date = False
        currency = False
        if data.get("currency_code"):
            currency = self.env["res.currency"].search([("name", "=", str(data["currency_code"]).upper())], limit=1)
        partner = False
        if vendor_name:
            candidates = self.env["res.partner"].search([
                ("supplier_rank", ">", 0), ("name", "ilike", vendor_name),
            ], limit=5)
            exact = candidates.filtered(lambda p: p.name.strip().casefold() == vendor_name.casefold())
            if len(exact) == 1:
                partner = exact[0]
        line_commands = [Command.clear()]
        for item in data.get("lines", [])[:100]:
            if not isinstance(item, dict):
                continue
            try:
                quantity = float(item.get("quantity", 1) or 1)
                unit_price = float(item.get("unit_price", 0) or 0)
            except (TypeError, ValueError):
                continue
            description = str(item.get("description") or "Invoice line").strip()[:500]
            if quantity <= 0 or unit_price < 0:
                continue
            line_commands.append(Command.create({
                "name": description,
                "quantity": quantity,
                "price_unit": unit_price,
            }))
        if len(line_commands) <= 1:
            raise UserError(_("No usable invoice lines were extracted. Review the PDF or use a different document."))
        self.write({
            "vendor_name": vendor_name,
            "invoice_reference": invoice_number,
            "invoice_date": invoice_date,
            "currency_id": currency.id if currency else self.company_id.currency_id.id,
            "extracted_total": float(data.get("total") or 0),
            "partner_id": partner.id if partner else False,
            "line_ids": line_commands,
            "extraction_status": "extracted",
        })
        return True

    def action_create_draft_vendor_bill(self):
        self.ensure_one()
        if self.company_id not in self.env.companies:
            raise AccessError(_("You do not have access to the selected company."))
        if self.extraction_status != "extracted":
            raise UserError(_("Extract and review the invoice before creating a vendor bill."))
        if not self.partner_id:
            raise ValidationError(_("Select the correct supplier before creating the bill."))
        if not self.expense_account_id:
            raise ValidationError(_("Select the appropriate expense or asset account for the invoice lines."))
        if not self.line_ids:
            raise ValidationError(_("At least one invoice line is required."))
        invoice_lines = []
        for line in self.line_ids:
            vals = {
                "name": line.name,
                "quantity": line.quantity,
                "price_unit": line.price_unit,
                "account_id": self.expense_account_id.id,
            }
            if self.tax_ids:
                vals["tax_ids"] = [Command.set(self.tax_ids.ids)]
            invoice_lines.append(Command.create(vals))
        bill = self.env["account.move"].create({
            "move_type": "in_invoice",
            "company_id": self.company_id.id,
            "partner_id": self.partner_id.id,
            "currency_id": self.currency_id.id,
            "invoice_date": self.invoice_date or date.today(),
            "ref": self.invoice_reference or self.file_name,
            "invoice_line_ids": invoice_lines,
        })
        self.env["ir.attachment"].create({
            "name": self.file_name or "supplier_invoice.pdf",
            "type": "binary",
            "datas": self.file_data,
            "mimetype": "application/pdf",
            "res_model": "account.move",
            "res_id": bill.id,
        })
        return {
            "type": "ir.actions.act_window",
            "name": _("Draft Vendor Bill"),
            "res_model": "account.move",
            "res_id": bill.id,
            "view_mode": "form",
            "target": "current",
        }


class AIErpInvoiceLineWizard(models.TransientModel):
    _name = "ai.erp.invoice.line.wizard"
    _description = "AI Extracted Invoice Line"

    wizard_id = fields.Many2one("ai.erp.invoice.wizard", required=True, ondelete="cascade")
    name = fields.Char(required=True)
    quantity = fields.Float(required=True, default=1.0)
    price_unit = fields.Float(required=True)
