#!/usr/bin/env python3
"""
Quarterly estimated tax planner for US freelancers / sole props (educational).

Combines income-by-source + Schedule C–style expenses (+ optional mileage) into
a simplified SE + federal + state planning estimate and per-quarter remaining.

NOT tax advice. Brackets / std deduction / mileage rate are EDITABLE defaults
for 2026-style planning — verify against current IRS pubs and your CPA.

Usage:
  python3 quarterly_tax_estimator.py \\
    --income ../samples/sample_income_by_source.csv \\
    --expenses ../samples/sample_schedule_c_expenses.csv \\
    --mileage ../samples/sample_mileage_log.csv \\
    --months-elapsed 6 \\
    --already-paid 3200 \\
    --state-rate 0.05
"""
from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# Illustrative 2026-ish single filer ordinary brackets (VERIFY — educational only)
FED_BRACKETS_SINGLE = [
    (11925, 0.10),
    (48475, 0.12),
    (103350, 0.22),
    (197300, 0.24),
    (250525, 0.32),
    (626350, 0.35),
    (float("inf"), 0.37),
]
STD_DEDUCTION_SINGLE = 15750.0  # illustrative planning default
SE_RATE = 0.153
SE_TAXABLE_PCT = 0.9235
SE_DEDUCTION_PCT = 0.5


def money(s: str) -> float:
    s = (s or "").replace("$", "").replace(",", "").strip()
    if not s:
        return 0.0
    return round(float(s), 2)


def load_csv(path: Path) -> List[dict]:
    rows = []
    with path.open(newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            # skip fully empty
            if not any((v or "").strip() for v in row.values()):
                continue
            # skip comment rows mistaken as data
            first = next(iter(row.values())) if row else ""
            if str(first).strip().startswith("#"):
                continue
            rows.append(row)
    return rows


def sum_income(rows: List[dict]) -> Tuple[float, Dict[str, float]]:
    total = 0.0
    by_q: Dict[str, float] = {}
    for r in rows:
        net = money(r.get("net_amount") or "0")
        if not net:
            net = money(r.get("gross_amount") or "0") - money(r.get("fees_already_deducted") or "0")
        total += net
        q = (r.get("quarter") or "").strip() or "unknown"
        by_q[q] = by_q.get(q, 0.0) + net
    return round(total, 2), {k: round(v, 2) for k, v in sorted(by_q.items())}


def sum_expenses(rows: List[dict]) -> Tuple[float, Dict[str, float], Dict[str, float]]:
    total = 0.0
    by_cat: Dict[str, float] = {}
    by_q: Dict[str, float] = {}
    for r in rows:
        amt = money(r.get("deductible_amount") or "0")
        if not amt:
            amt = round(money(r.get("amount") or "0") * (money(r.get("business_pct") or "100") / 100.0), 2)
        total += amt
        cat = (r.get("category_code") or r.get("category_label") or "other").strip()
        by_cat[cat] = by_cat.get(cat, 0.0) + amt
        q = (r.get("quarter") or "").strip() or "unknown"
        by_q[q] = by_q.get(q, 0.0) + amt
    return (
        round(total, 2),
        {k: round(v, 2) for k, v in sorted(by_cat.items())},
        {k: round(v, 2) for k, v in sorted(by_q.items())},
    )


def sum_mileage(rows: List[dict]) -> Tuple[float, float]:
    miles = 0.0
    amount = 0.0
    for r in rows:
        m = money(r.get("miles") or "0")
        # if round_trip true and user entered one-way, they should already double;
        # we trust the miles column as business miles to claim
        miles += m
        amt = money(r.get("amount") or "0")
        if not amt:
            rate = money(r.get("rate_per_mile") or "0")
            amt = round(m * rate, 2)
        amount += amt
    return round(miles, 2), round(amount, 2)


def progressive_tax(taxable: float, brackets) -> float:
    tax = 0.0
    prev = 0.0
    for limit, rate in brackets:
        chunk = min(taxable, limit) - prev
        if chunk <= 0:
            break
        tax += chunk * rate
        prev = limit
        if taxable <= limit:
            break
    return round(tax, 2)


@dataclass
class Plan:
    income_ytd: float
    expenses_ytd: float
    mileage_deduction: float
    net_profit_ytd: float
    projected_annual: float
    se_tax: float
    income_tax_federal: float
    state_tax: float
    total_annual_estimate: float
    already_paid: float
    remaining: float
    per_remaining_quarter: float
    quarters_left: int
    effective_rate_on_net: float


def build_plan(
    net_profit_ytd: float,
    months_elapsed: float,
    already_paid: float,
    state_rate: float,
    std_deduction: float,
) -> Plan:
    if months_elapsed <= 0 or months_elapsed > 12:
        raise ValueError("months_elapsed must be in (0, 12]")
    projected = round(net_profit_ytd * (12.0 / months_elapsed), 2)
    se_base = projected * SE_TAXABLE_PCT
    se_tax = round(max(0.0, se_base) * SE_RATE, 2)
    se_deduction = round(se_tax * SE_DEDUCTION_PCT, 2)
    taxable = max(0.0, projected - se_deduction - std_deduction)
    income_tax = progressive_tax(taxable, FED_BRACKETS_SINGLE)
    state_tax = round(max(0.0, projected - std_deduction) * state_rate, 2)
    total = round(se_tax + income_tax + state_tax, 2)
    remaining = max(0.0, round(total - already_paid, 2))
    # Quarters left: rough from months
    q_done = int((months_elapsed - 1) // 3) + 1  # 1..4
    quarters_left = max(1, 4 - q_done + (0 if months_elapsed % 3 == 0 and months_elapsed < 12 else 0))
    # simpler: remaining calendar quarters including current if not past due
    month = int(round(months_elapsed))
    if month <= 3:
        quarters_left = 4
    elif month <= 6:
        quarters_left = 3
    elif month <= 9:
        quarters_left = 2
    else:
        quarters_left = 1
    per_q = round(remaining / quarters_left, 2) if quarters_left else remaining
    eff = round(total / projected, 4) if projected > 0 else 0.0
    return Plan(
        income_ytd=0.0,  # filled by caller
        expenses_ytd=0.0,
        mileage_deduction=0.0,
        net_profit_ytd=net_profit_ytd,
        projected_annual=projected,
        se_tax=se_tax,
        income_tax_federal=income_tax,
        state_tax=state_tax,
        total_annual_estimate=total,
        already_paid=already_paid,
        remaining=remaining,
        per_remaining_quarter=per_q,
        quarters_left=quarters_left,
        effective_rate_on_net=eff,
    )


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Freelancer quarterly tax estimate (planning)")
    p.add_argument("--income", type=Path, required=True)
    p.add_argument("--expenses", type=Path, required=True)
    p.add_argument("--mileage", type=Path, default=None)
    p.add_argument("--months-elapsed", type=float, required=True, help="e.g. 6 for end of June")
    p.add_argument("--already-paid", type=float, default=0.0, help="Estimated taxes already paid YTD")
    p.add_argument("--state-rate", type=float, default=0.05)
    p.add_argument("--std-deduction", type=float, default=STD_DEDUCTION_SINGLE)
    p.add_argument("--override-net", type=float, default=None, help="Skip CSV math; use this net profit YTD")
    args = p.parse_args(argv)

    income_ytd, income_by_q = sum_income(load_csv(args.income))
    exp_ytd, exp_by_cat, exp_by_q = sum_expenses(load_csv(args.expenses))
    miles, mile_amt = (0.0, 0.0)
    if args.mileage:
        miles, mile_amt = sum_mileage(load_csv(args.mileage))

    net = args.override_net if args.override_net is not None else round(income_ytd - exp_ytd - mile_amt, 2)
    plan = build_plan(net, args.months_elapsed, args.already_paid, args.state_rate, args.std_deduction)
    plan.income_ytd = income_ytd
    plan.expenses_ytd = exp_ytd
    plan.mileage_deduction = mile_amt

    print("=== Income by quarter ===")
    for k, v in income_by_q.items():
        print(f"  {k}: {v:,.2f}")
    print(f"  YTD income (net of platform fees already deducted): {income_ytd:,.2f}")

    print("\n=== Expenses by category (deductible) ===")
    for k, v in exp_by_cat.items():
        print(f"  {k}: {v:,.2f}")
    print(f"  YTD expenses: {exp_ytd:,.2f}")
    if args.mileage:
        print(f"  Mileage: {miles:.1f} mi → ${mile_amt:,.2f} deduction (rate from your log)")

    print("\n=== Profit bridge ===")
    print(f"  Income YTD:              {income_ytd:,.2f}")
    print(f"  − Expenses:              {exp_ytd:,.2f}")
    print(f"  − Mileage deduction:     {mile_amt:,.2f}")
    print(f"  = Net profit YTD:        {net:,.2f}")

    print("\n=== Annualized tax plan (EDUCATIONAL) ===")
    print(f"  Months elapsed:          {args.months_elapsed}")
    print(f"  Projected annual profit: {plan.projected_annual:,.2f}")
    print(f"  SE tax (~15.3% on 92.35%):{plan.se_tax:,.2f}")
    print(f"  Federal income tax:      {plan.income_tax_federal:,.2f}")
    print(f"  State tax @{args.state_rate:.1%}:     {plan.state_tax:,.2f}")
    print(f"  Total annual estimate:   {plan.total_annual_estimate:,.2f}")
    print(f"  Effective rate on profit:{plan.effective_rate_on_net:.1%}")
    print(f"  Already paid:            {plan.already_paid:,.2f}")
    print(f"  Remaining:               {plan.remaining:,.2f}")
    print(f"  ÷ {plan.quarters_left} quarter(s) left:   {plan.per_remaining_quarter:,.2f} each")

    # Suggested lockbox transfer this month
    monthly_set_aside = round(plan.total_annual_estimate / 12.0, 2)
    print("\n=== Reserve suggestion ===")
    print(f"  Smooth monthly lockbox transfer ≈ ${monthly_set_aside:,.2f}")
    print(f"  Or fund next quarter payment:    ${plan.per_remaining_quarter:,.2f}")

    print("\nDisclaimer: Not tax advice. Brackets/deductions/mileage are planning defaults.")
    print("Confirm with IRS instructions, state rules, and a CPA or tax software.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
