# Sheets-friendly formulas (macro-free)

Import the schema CSVs as tabs. Yellow = inputs. These formulas are planning aids only.

Assume:
- `Income` tab uses `schemas/income-by-source.csv` headers  
- `Expenses` tab uses `schemas/schedule-c-categories.csv`  
- `Inputs` tab is two columns: `key` | `value` (A/B)  
- `Payments` tab uses quarterly payments log headers  

## Named-style cell references on Inputs
| Key | Cell (example) |
|-----|----------------|
| se_tax_rate | `Inputs!B2` |
| se_deduction_rate | `Inputs!B3` |
| ordinary_marginal_rate | `Inputs!B4` |
| state_effective_rate | `Inputs!B6` |

(Or use `VLOOKUP("se_tax_rate", Inputs!A:B, 2, FALSE)`.)

## Totals
```
IncomeNet   = SUM(Income!F:F)          // net_usd column
ExpenseTot  = SUM(Expenses!C:C)        // amount_usd
NetProfit   = IncomeNet - ExpenseTot
```

## SE + ordinary proxy (same model as the Python script)
```
SEBase      = MAX(NetProfit, 0) * VLOOKUP("se_deduction_rate", Inputs!A:B, 2, FALSE)
SETax       = SEBase * VLOOKUP("se_tax_rate", Inputs!A:B, 2, FALSE)
OrdinaryBase= MAX(NetProfit - 0.5 * SETax, 0)
FedIncome   = OrdinaryBase * VLOOKUP("ordinary_marginal_rate", Inputs!A:B, 2, FALSE)
StateTax    = MAX(NetProfit, 0) * VLOOKUP("state_effective_rate", Inputs!A:B, 2, FALSE)
FedTotal    = SETax + FedIncome
Combined    = FedTotal + StateTax
```

## Remaining to pay
```
FedPaid     = SUM(Payments!D:D)   // or use Inputs ytd_federal_estimated_paid
FedRemain   = MAX(FedTotal - FedPaid, 0)
NextQuarter = FedRemain / RemainingQuarters   // put RemainingQuarters in a yellow cell
```

## Mileage
```
MilesAmount = Miles * Rate   // rate from Inputs irs_mileage_rate_usd — update yearly
```
Roll the year’s mileage total into Expenses as `Car and truck (mileage)` **or** keep separate for your CPA (don’t double-count).

## Relationship to Cashflow Kit
Copy quarterly **totals** from Cashflow Kit Dashboard / Income / Expenses into this workbook’s Income & Expenses tabs. Do not rebuild invoice aging here.
