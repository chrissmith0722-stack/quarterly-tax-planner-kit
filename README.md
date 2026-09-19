# Quarterly Tax Planner Kit

**Public preview repo** for the 2026 freelancer quarterly tax & estimated-payment planner.  
**Commercial zip (full buyer package):** `quarterly-tax-dashboard.zip` in the publish-ready pack.  
**Price target:** **$27** (range **$27–$34**) · Channels: **Gumroad** (+ Etsy optional)

SE-aware quarterly estimates + tax reserve lockbox. Import totals from Cashflow Kit (or any books) — this kit does **not** rebuild monthly P&L / invoice aging sheets.

| Product | Job |
|---------|-----|
| Cashflow Kit | Monthly income · expenses · invoices · simple reserve % |
| **This kit** | Quarterly SE-aware estimate · payment split · mileage · Schedule C–style rollup · tax lockbox · CPA handoff |

---

## Buy / sell this

### Buyers
- **Paid package** ships as `quarterly-tax-dashboard.zip` once the Gumroad listing is live (link TBD after publish).
- This GitHub repo is the **open preview** (schemas, samples, scripts, checklists, Sheets formulas) under MIT so you can evaluate fit before buying the packaged listing + planner bundle.

### Sellers (Chris — income path)
1. Upload **`/workspace/outputs/publish-ready/quarterly-tax-dashboard.zip`** to Gumroad as the downloadable file.
2. Paste title/description from `LISTING.md` in this repo (also inside the zip).
3. Set price **$27** (stretch **$34** after reviews / bundle with Cashflow).
4. Publish → optionally list on Etsy later.  
**Blocked without Chris:** Gumroad (and Etsy) login + publish click. Agents cannot publish marketplaces without that login. Stripe Price IDs for owned-checkout are also Chris-only.

**Companion SKUs (same publish-ready folder):** `cashflow-kit.zip` ($19 first-dollar), `seller-ledger.zip` ($19), `invoice-pack.zip` ($12).

---

## What you get

### Docs
| File | Role |
|------|------|
| `LISTING.md` | Gumroad/Etsy paste |
| `SHEETS-FORMULAS.md` | Macro-free Sheets formula guide |
| `checklists/quarterly-close.md` | Quarter-end SOP |
| `checklists/cpa-handoff.md` | Year-end packet list |
| `checklists/quarterly_closing_checklist.md` | Detailed quarterly close (tax + lockbox) |
| `sops/QUICK-START.md` | 12-minute setup |

### Schemas
| File | Role |
|------|------|
| `schemas/income_by_source_schema.csv` / `income-by-source.csv` | Income rollup |
| `schemas/schedule_c_expenses_schema.csv` / `schedule-c-categories.csv` | Expense labels |
| `schemas/mileage_log_schema.csv` / `mileage-log.csv` | Miles log |
| `schemas/estimated_payment_log_schema.csv` / `quarterly-payments-log.csv` | Payments made |
| `schemas/estimated-tax-inputs.csv` | Editable rates (SE, ordinary, state…) |
| `schemas/tax_reserve_lockbox_schema.csv` | Lockbox deposit/withdrawal ledger |

### Samples (fictional demo year)
`samples/sample_income_by_source.csv`, `sample_schedule_c_expenses.csv`, `sample_mileage_log.csv`, `sample_tax_reserve_lockbox.csv`, plus hyphenated twins + `sample-estimated-tax-inputs.csv` / `sample-quarterly-payments-log.csv`.

### Calculators (Python 3, stdlib only)
| Script | Role |
|--------|------|
| `scripts/quarterly_tax_estimator.py` | Annualize YTD → remaining ÷ quarters + monthly lockbox suggestion |
| `scripts/quarterly_tax_planner.py` | SE-aware estimate from income/expense/inputs/payments CSVs |
| `scripts/tax_reserve_lockbox.py` | Lockbox balance + coverage vs next payment |

---

## Quick start

```bash
cd scripts
python3 quarterly_tax_estimator.py \
  --income ../samples/sample_income_by_source.csv \
  --expenses ../samples/sample_schedule_c_expenses.csv \
  --mileage ../samples/sample_mileage_log.csv \
  --months-elapsed 9 --already-paid 2800 --state-rate 0.032

python3 tax_reserve_lockbox.py \
  --ledger ../samples/sample_tax_reserve_lockbox.csv \
  --next-payment 1843.70 --label 2026-Q4
```

---

## Disclaimer

**Not a CPA service. Not legal or tax advice. Not affiliated with the IRS.**  
Simplified planning models only. Confirm with a licensed professional before paying or filing.

## License

MIT
