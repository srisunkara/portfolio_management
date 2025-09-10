Sample CSVs for API testing

File: transactions_by_name_sample.csv
- Use with POST /transactions/bulk-by-name-csv (exact route prefix may vary; check your FastAPI router mounting path).
- Encoding: UTF-8 (no BOM recommended).
- Date format: YYYY-MM-DD.
- Required headers:
  portfolio_name, security_ticker, external_platform_name, transaction_date, transaction_type, transaction_qty, transaction_price
- Optional headers (can be left empty):
  transaction_fee, transaction_fee_percent, carry_fee, carry_fee_percent, management_fee, management_fee_percent, external_manager_fee, external_manager_fee_percent

Notes
- The service matches portfolio/security/platform by NAME or TICKER (case-insensitive). Ensure you have these records created in your database before uploading, otherwise those rows will be returned under "excluded" in the response.
- The last row in the sample intentionally uses unknown names to demonstrate an excluded row and show the response shape.

Example cURL
curl -X POST \
  -H "Content-Type: multipart/form-data" \
  -F "file=@transactions_by_name_sample.csv" \
  http://localhost:8000/transactions/bulk-by-name-csv
