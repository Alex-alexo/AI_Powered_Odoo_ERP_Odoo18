# Test Plan and Acceptance Checklist

Use a dedicated test database (for example `ai_erp_training`) with fictional data. Do not use real supplier invoices, customer data, or production financial information until your organization approves the data flow to the selected AI provider.

## A. Installation

- [ ] Install standard Accounting, Sales, Purchase, and Inventory applications.
- [ ] Install Python dependencies from `requirements.txt` in the Odoo runtime environment.
- [ ] Add the addon directory to `addons_path`, restart Odoo, update the Apps list, and install AI-Powered ERP Suite.
- [ ] Confirm that the AI ERP menu appears for a user assigned to AI ERP User.

## B. Roles and access

- [ ] A user without AI ERP User cannot open the AI ERP menu.
- [ ] An AI ERP User can create a conversation.
- [ ] A normal user cannot read another user's conversation by changing a URL or record ID.
- [ ] An AI ERP User cannot access provider configuration.
- [ ] An AI ERP Manager can configure a provider and access company conversations.
- [ ] Multi-company users can only access allowed-company insights and forecasts.

## C. AI assistant

- [ ] Without a provider configuration, sending a prompt returns a clear configuration message.
- [ ] With a test OpenAI-compatible endpoint, ask for the last-30-day aggregate invoice summary.
- [ ] Compare the reported figures against Odoo's posted invoice records using the same company and date range.
- [ ] Ask for customer-level information; the assistant should state that this MVP only provides aggregate metrics.
- [ ] Verify that no invoice, payment, purchase order, or stock movement is created by a chat request.
- [ ] Test invalid endpoint, bad API key, provider timeout, and malformed response handling.

## D. Invoice extraction

- [ ] Upload a small, text-based fictional supplier invoice PDF.
- [ ] Verify extracted supplier name, reference, date, currency, descriptions, quantities, and unit prices.
- [ ] Correct an intentionally wrong extracted line before bill creation.
- [ ] Confirm that missing supplier selection prevents bill creation.
- [ ] Confirm that missing expense/asset account prevents bill creation.
- [ ] Create a draft vendor bill and verify supplier, date, reference, currency, line values, selected account/taxes, and attached original PDF.
- [ ] Verify that the vendor bill is still draft and is not posted automatically.
- [ ] Test a scanned/image-only PDF; it should clearly report that selectable text/OCR is required.

## E. Inventory forecast

- [ ] Create confirmed sales orders for a test product across at least three historical months.
- [ ] Run a forecast using the same company, product, number of months, and horizon.
- [ ] Independently calculate total ordered quantity / number of history months * horizon_days / 30.4375.
- [ ] Verify the saved forecast and replenishment recommendation match the calculation.
- [ ] Test product with no sales history (forecast should be zero).
- [ ] Verify that the note identifies this method as a baseline and lists important omitted factors.

## F. Business insights

- [ ] Create a posted customer invoice with a due date in the past and a residual balance.
- [ ] Run the insight generator and verify an overdue receivable insight is created.
- [ ] Test with no overdue invoices and no zero/negative free-stock products.
- [ ] Verify that the wizard describes its 500-product sampling limit.
- [ ] Confirm that generated alerts do not post journal entries or change stock.

## G. Production readiness (not covered by the MVP)

- [ ] Review Odoo record rules and multi-company behavior with a security specialist.
- [ ] Move API credentials to an approved secrets management solution.
- [ ] Approve external AI-provider data processing and retention terms.
- [ ] Add tests for all supported Odoo 18 editions/builds and all configured localizations.
- [ ] Add OCR service only after security, data retention, and failure handling are designed.
- [ ] Validate tax/account mapping with a qualified accountant for the target jurisdiction.
- [ ] Perform load, backup/restore, monitoring, and disaster-recovery tests.
