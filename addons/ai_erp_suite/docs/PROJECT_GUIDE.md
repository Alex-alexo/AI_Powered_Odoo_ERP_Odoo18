# Project Guide: AI-Powered ERP Management System Using Odoo 18

## 1. Project purpose

Extend Odoo 18 with carefully scoped AI-assisted capabilities while keeping Odoo as the authoritative transactional system. The MVP targets ATS Technology Solutions PLC as a simulated Ethiopian trading company.

## 2. Implemented MVP scope

| Capability | Implemented behavior | Human control |
|---|---|---|
| Business assistant | LLM summarizes a restricted aggregate KPI snapshot | User reads and verifies the response |
| Invoice extraction | PDF text extraction and structured field/line extraction | User chooses supplier/account/tax and reviews draft bill |
| Inventory forecast | Moving-average baseline from confirmed sales quantities | User decides whether to replenish |
| Business insights | Rule-based overdue receivable and zero/negative free-stock alerts | Manager reviews and dismisses/resolves alerts |

## 3. Architecture

```text
Odoo 18 Web Client
       |
       v
Custom Add-on: ai_erp_suite
       |
       +---- Odoo ORM / Security / Multi-company context
       |        +---- account.move
       |        +---- sale.order.line
       |        +---- product.product
       |        +---- custom AI conversation / insight / forecast models
       |
       +---- AI Provider Adapter (server-side only)
       |        +---- chat-completions API
       |        +---- structured JSON extraction
       |
       +---- PDF text reader (pypdf)
       |
       v
PostgreSQL + Odoo filestore
```

## 4. Data flow and trust boundaries

### Assistant

Odoo calculates aggregate totals using ORM queries for the selected company. The external provider receives the user's question plus a limited snapshot. It does not receive customer names, vendor names, employee records, line-level journal data, or raw database access from this module.

### Invoice extraction

The uploaded PDF is read on the Odoo server. Extracted text is sent to the configured AI provider to identify candidate invoice fields. The result is untrusted input. The user must review it, choose the supplier, expense/asset account and tax, then create a draft vendor bill. Standard Odoo accounting validation and posting remain in control.

### Forecast

Confirmed sales order quantities are aggregated by month. The arithmetic mean is used as a baseline and scaled to the requested horizon. The calculation is transparent and stored with its method and limitations.

### Rule-based insights

The wizard checks posted overdue customer invoices and free stock for up to 500 active products. The generated records are alerts, not accounting adjustments.

## 5. Suggested full-project extensions

1. Add an OCR adapter and support image-only invoices, with explicit data-protection controls.
2. Add sales forecasting with seasonal naive, moving average, Random Forest, and gradient boosting baselines.
3. Add inventory forecasting evaluation with chronological train/validation/test splits and MAE, RMSE, and MASE.
4. Add ML-based anomaly detection, keeping a review queue and false-positive feedback.
5. Add procurement lead-time and vendor performance analytics.
6. Add OWL-based chat interface with streamed responses and safe tool routing.
7. Add an executive dashboard with drill-down actions that enforce Odoo ACLs and record rules.
8. Add automated tests, CI, deployment scripts, backups, monitoring, and provider cost tracking.

## 6. Suggested acceptance criteria

- A normal user can create and access only their own conversations.
- A manager can configure one active AI endpoint per company.
- The assistant does not create or modify transactional ERP records.
- A text-based supplier invoice can be extracted into editable candidate fields.
- The system cannot create a vendor bill until required supplier/account/line data is selected.
- The created vendor bill remains in draft state.
- A forecast calculation is reproducible from the same historical sales orders and parameters.
- Rule-based insight generation records only the stated checks and does not claim to be a complete audit.
