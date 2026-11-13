# AI-Powered ERP Suite for Odoo 18

**Package:** `ai_erp_suite`  
**Version:** 18.0.1.0.0  
**Type:** Custom Odoo 18 add-on / portfolio MVP  
**Organization in examples:** ATS Technology Solutions PLC

## What is included

This installable add-on provides four working feature areas:

1. **AI Business Assistant** – creates private conversations and sends questions to an OpenAI-compatible chat-completions endpoint. The assistant receives a limited, aggregate, read-only business snapshot (recent posted customer invoices, vendor bills, overdue receivables, and a sample of stock availability). It does not execute ERP transactions.
2. **Supplier Invoice Extraction** – reads selectable text from a PDF using `pypdf`, asks the configured AI endpoint to extract structured header/line data, lets an employee review and correct it, and creates an **unposted draft vendor bill**. The employee chooses the supplier, expense/asset account, and purchase taxes. It never posts the bill.
3. **Inventory Demand Forecast Baseline** – calculates a simple monthly-average demand baseline from confirmed sales order quantities and compares the forecast with current free stock. This is explicitly a baseline, not a trained machine-learning model.
4. **Business Insights** – generates rule-based alerts for overdue customer invoices and products with zero/negative free stock (up to 500 active products sampled). These are operational checks, not an audit or ML anomaly detector.

This package is a practical MVP and learning project. It is **not** a complete production ERP implementation, not certified accounting software, and not a replacement for Odoo's native controls or professional review.

## Compatibility

- Odoo 18.0 (Community or Enterprise; depends on installed standard modules)
- Python version supported by your Odoo 18 installation
- PostgreSQL version supported by your Odoo installation
- Python packages: `requests`, `pypdf`
- Standard Odoo apps required: Accounting, Sales, Purchase, Inventory

The module uses standard Odoo models and APIs. A real installation test against the exact Odoo 18 build and edition is still required before production deployment.

## Installation (Windows example)

1. Back up your Odoo database and filestore.
2. Extract the project ZIP. Copy the `ai_erp_suite` folder into your custom addons directory, for example:

   `D:\ERP Training\Odoo\odoo-custom\ai_erp_suite`

3. Install the Python dependencies using the same Python environment that runs Odoo:

   ```powershell
   python -m pip install -r "D:\ERP Training\Odoo\odoo-custom\ai_erp_suite\requirements.txt"
   ```

4. Confirm that your `odoo.conf` has the custom addons directory in `addons_path`. Keep your existing core addons path and append the custom path; do not replace the existing path.
5. Restart the Odoo service/server.
6. Open Odoo and activate Developer Mode.
7. Go to Apps → Update Apps List.
8. Search for **AI-Powered ERP Suite** and install it.
9. Assign users to the **AI ERP User** or **AI ERP Manager** group from Settings → Users & Companies → Users. The manager group controls AI provider configuration.

For safe learning, use a new database such as `ai_erp_training`. Do not install or test new modules directly in your existing ATS warehouse database without a verified backup.

## AI provider setup

1. Open **AI ERP → Configuration** as an AI ERP Manager.
2. Create one configuration for the relevant company.
3. Enter an HTTPS OpenAI-compatible chat-completions endpoint, model name, API key, and timeout.
4. Save the configuration.
5. Test with a non-sensitive business question in AI ERP → Business Assistant.

Default endpoint: `https://api.openai.com/v1/chat/completions`  
Default model label: `gpt-4o-mini` (availability and pricing are controlled by the provider; change it if needed).

For a local OpenAI-compatible service, HTTP is permitted only for `localhost`, `127.0.0.1`, or `::1`. Do not expose a local inference endpoint publicly without authentication and TLS.

### Credential and data warning

The API key is stored in an Odoo model field in the database and access to configuration is restricted to the manager group. This is not equivalent to a dedicated secrets vault. Restrict database/server access, encrypt backups, and consider an external secrets manager for production. Do not use real confidential records during initial testing. The assistant sends aggregate KPI context and the user's prompt to the configured provider. Invoice extraction sends extracted PDF text to the provider. Obtain organizational approval and confirm the provider's data-handling terms before using real invoices or personal data.

## How to use the features

### AI Business Assistant

- AI ERP → Business Assistant → New.
- Enter a question and click **Send to AI**.
- Company-specific answers are limited to the aggregate snapshot described above.
- The AI cannot query arbitrary records or perform payments, invoice posting, purchases, or stock changes.

Example: “Summarize the posted customer invoice and vendor bill totals for the last 30 days.”

### Supplier invoice extraction

- AI ERP → Process Supplier Invoice.
- Upload a text-based PDF (maximum 12 MB and 20 pages).
- Click **Extract Invoice Data**.
- Review the extracted supplier, invoice reference/date, currency, lines, quantities, and prices.
- Select the correct supplier, expense/asset account, and purchase taxes.
- Click **Create Draft Vendor Bill**.
- Open the created bill, verify all information and tax treatment, and only then post it using normal Odoo accounting controls.

**Limitations:** Scanned image-only PDFs are not supported by this MVP because no OCR engine is bundled. Add a properly secured OCR service (for example Tesseract or a document AI API) if scanned invoices must be processed. AI extraction may be wrong; every field requires human verification. The extracted total is informational and is not used to post or reconcile the bill.

### Inventory forecast

- AI ERP → Generate Inventory Forecast.
- Select company, product, history months (3–24), and horizon (7–180 days).
- The baseline averages the confirmed sales order quantities over the selected complete historical months and scales that monthly average to the forecast horizon.
- Compare recommended replenishment with current free quantity.

This simple baseline does not model seasonality, supplier lead times, safety stock, promotions, returns, or stock-outs. Validate it against historical holdout periods before using it for purchasing decisions.

### Business insights

- AI ERP → Generate Business Insights.
- Select a company and click **Run Checks**.
- Review generated overdue receivable and low-free-stock alerts.

These checks are intentionally simple and should be expanded with company-specific thresholds and controls before production use.

## Security design

- Dedicated AI ERP user and manager groups.
- Conversation records are restricted to their owner; managers can access conversations in allowed companies.
- Company-level record rules for insights and forecasts.
- AI configuration access is manager-only.
- AI assistant context is aggregate and read-only; no arbitrary SQL or model names are accepted from the AI.
- Invoice extraction only creates draft vendor bills and requires user-selected supplier/account/taxes.
- No automatic payment, invoice posting, purchase confirmation, or stock adjustment is performed.

Before production, review multi-company rules, user groups, company-specific accounts/taxes, API endpoint allow-lists, logging, retention, rate limits, and data-processing approvals with your Odoo administrator/security owner.

## Development structure

```text
ai_erp_suite/
├── __manifest__.py
├── models/
│   ├── ai_config.py
│   ├── ai_conversation.py
│   ├── ai_message.py
│   ├── ai_insight.py
│   └── ai_forecast.py
├── wizard/
│   ├── invoice_wizard.py
│   ├── forecast_wizard.py
│   └── insight_wizard.py
├── security/
├── views/
├── tests/
└── docs/
```

## Known MVP limitations / next development steps

- No visual OWL chat client yet; the assistant uses standard Odoo form/list views.
- No scanned-PDF OCR; text-based PDF extraction only.
- The forecast is a moving-average baseline, not Random Forest, XGBoost, LSTM, or another trained ML model.
- No sales forecast model, supplier ranking, ML anomaly detection, executive KPI dashboard, or automatic procurement recommendation is included in this MVP.
- AI compatibility depends on a provider implementing the OpenAI chat-completions request/response shape. Structured invoice extraction uses JSON response mode.
- Additional automated tests, performance profiling, load testing, and a live installation against your precise Odoo 18 build must be completed before production.

See `docs/PROJECT_GUIDE.md` and `docs/TEST_PLAN.md` for the project specification and acceptance tests.
