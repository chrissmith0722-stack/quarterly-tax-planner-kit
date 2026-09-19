# Quick Start — Quarterly Tax & Cash-Flow Dashboard Kit (≈12 minutes)

**Positioning:** Tax-estimate premium for US freelancers / 1099s.  
**Not** a replacement for the Solo Freelancer Cashflow Kit (monthly income/expense/invoice close).

## 1. Smoke-test samples
```bash
cd scripts
python3 quarterly_tax_estimator.py \
  --income ../samples/sample_income_by_source.csv \
  --expenses ../samples/sample_schedule_c_expenses.csv \
  --mileage ../samples/sample_mileage_log.csv \
  --months-elapsed 6 \
  --already-paid 3200 \
  --state-rate 0.05

python3 tax_reserve_lockbox.py \
  --ledger ../samples/sample_tax_reserve_lockbox.csv \
  --next-payment 3500 \
  --label 2026-Q2
```

## 2. Copy schemas → your data folder
```bash
mkdir -p ../data
cp ../schemas/*_schema.csv ../data/
# replace schema comment files with real CSVs using the header row only
```

## 3. Fill YTD income & expenses
- Income: every 1099 client, Gumroad/Stripe **net**, other business cash in  
- Expenses: use `category_code` values from the schema comments (Schedule C–style labels)  
- Mileage: set `rate_per_mile` to the IRS standard rate **you** are using this year  

## 4. Run estimate at each quarter end
Set `--months-elapsed` to 3 / 6 / 9 / 12 and `--already-paid` to cumulative estimates paid.

## 5. Fund the lockbox monthly
Transfer ≈ `total_annual_estimate / 12` each month (from estimator output).  
Before each due date, run lockbox coverage check.

## Pairing with other SKUs
| SKU | Role |
|-----|------|
| Seller Ledger | Platform fee P&L → paste YTD **net** into income CSV |
| Cashflow Kit | Monthly operating close (invoices, burn, categories) |
| This kit | Quarterly SE/federal/state plan + tax reserve lockbox |
