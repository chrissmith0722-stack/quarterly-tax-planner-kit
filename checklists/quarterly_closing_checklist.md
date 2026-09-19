# Quarterly Closing Checklist — Freelancer Tax & Reserve

**Use at:** Q1 (Apr 15), Q2 (Jun 15), Q3 (Sep 15), Q4 (Jan 15 next year) — confirm current IRS due dates.  
**Not tax advice.**

## A. Books freeze
- [ ] Export income-by-source CSV for the quarter (clients, platforms, products)  
- [ ] Export / update Schedule C–style expenses for the quarter  
- [ ] Enter mileage for the quarter; confirm rate used  
- [ ] Pull YTD net after platform fees (Seller Ledger kit optional handoff)  

## B. Estimate
- [ ] Run `scripts/quarterly_tax_estimator.py` with `--months-elapsed` through quarter end  
- [ ] Enter `--already-paid` = sum of prior 1040-ES / state estimates  
- [ ] Note `per_remaining_quarter` and effective rate  
- [ ] Sanity-check vs last quarter — big swings → review income spike or missing expenses  

## C. Lockbox & pay
- [ ] Run `tax_reserve_lockbox.py --next-payment <amount>`  
- [ ] Transfer shortfall from operating account → tax savings **before** due date  
- [ ] Pay federal estimate; record confirmation in `estimated_payment_log`  
- [ ] Pay state estimate (if applicable); record confirmation  
- [ ] Post `withdrawal_payment` rows in lockbox ledger  

## D. Archive
- [ ] Save script output text: `archives/estimate_YYYY-Qn.txt`  
- [ ] Zip CSVs for the quarter  
- [ ] Update annual notes (rate changes, equipment purchases, home-office %)  

## E. Explicit non-goals (avoid Cashflow Kit overlap)
- [ ] Do **not** rebuild a full monthly income/expense/invoice dashboard here  
- [ ] Monthly money-close stays in **Solo Freelancer Cashflow Kit**  
- [ ] This checklist is **tax-estimate + reserve** only  
