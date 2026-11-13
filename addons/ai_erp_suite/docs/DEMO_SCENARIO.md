# Demo Scenario: ATS Technology Solutions PLC

Use fictional transactions in the `ai_erp_training` database.

## Master data

- Company: ATS Technology Solutions PLC
- Currency: ETB (configure company currency only if appropriate for the test database)
- Suppliers: Ethiopian Computer Supplier PLC, Addis Technology Supplier
- Customers: Demo Customer A, Demo Customer B
- Products: Desktop PC, Laptop, Printer, Router

## Transactions to create

1. Create confirmed sales orders for Desktop PCs and Printers across at least three complete calendar months. Deliver some quantities if testing stock availability.
2. Create and post a customer invoice with a due date in the past and a remaining balance to test receivables alerts.
3. Create and post a vendor bill in the test environment to populate the assistant aggregate snapshot.
4. Create a text-based fictional supplier invoice PDF (no real personal or financial data) with two lines to test extraction.
5. Configure a test AI provider key, then ask the assistant for a recent aggregate sales/invoice overview.

## Expected demonstration

- The assistant gives aggregate figures only and does not execute transactions.
- Invoice processing produces editable extraction results and a draft vendor bill that still requires review and posting by an accountant.
- Forecasting shows a moving-average baseline for a selected stockable product.
- Business insights identify the overdue invoice and products with zero/negative free stock, where applicable.
