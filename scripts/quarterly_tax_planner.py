#!/usr/bin/env python3
"""
Freelancer Quarterly Tax & Estimated-Payment Planner
----------------------------------------------------
SE-aware *planning* estimate from income + Schedule-C-style expense rollups.
Not tax advice. Simplified model for organization only.
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def load_kv(path: Path) -> Dict[str, str]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    return {r["key"].strip(): r["value"].strip() for r in rows if r.get("key")}


def load_rows(path: Path) -> List[dict]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def fnum(x: str, default: float = 0.0) -> float:
    try:
        return float(str(x).replace(",", "").replace("$", "").strip())
    except (ValueError, TypeError):
        return default


def sum_income(rows: List[dict]) -> Tuple[float, Dict[str, float]]:
    by_q: Dict[str, float] = defaultdict(float)
    total = 0.0
    for r in rows:
        net = fnum(r.get("net_usd"))
        if not net and (r.get("gross_usd") or r.get("fees_usd")):
            net = fnum(r.get("gross_usd")) - fnum(r.get("fees_usd"))
        q = (r.get("period") or "").strip() or "unknown"
        by_q[q] += net
        total += net
    return total, dict(by_q)


def sum_expenses(rows: List[dict]) -> Tuple[float, Dict[str, float], Dict[str, float]]:
    by_q: Dict[str, float] = defaultdict(float)
    by_label: Dict[str, float] = defaultdict(float)
    total = 0.0
    for r in rows:
        amt = fnum(r.get("amount_usd"))
        q = (r.get("period") or "").strip() or "unknown"
        label = (r.get("schedule_c_label") or "Other").strip()
        by_q[q] += amt
        by_label[label] += amt
        total += amt
    return total, dict(by_q), dict(by_label)


def estimate(net_profit: float, inputs: Dict[str, str]) -> dict:
    """
    Simplified planning model:
      SE base ≈ net_profit * se_deduction_rate   (if profit > 0)
      SE tax  ≈ SE base * se_tax_rate
      Income tax proxy ≈ max(net_profit - 0.5*SE tax, 0) * ordinary_marginal_rate
        (half of SE tax is traditionally deductible — simplified)
      State ≈ net_profit * state_effective_rate
      Additional Medicare ≈ SE base * additional_medicare_rate (if set)
    """
    se_rate = fnum(inputs.get("se_tax_rate"), 0.153)
    se_base_rate = fnum(inputs.get("se_deduction_rate"), 0.9235)
    ordinary = fnum(inputs.get("ordinary_marginal_rate"), 0.22)
    add_med = fnum(inputs.get("additional_medicare_rate"), 0.0)
    state = fnum(inputs.get("state_effective_rate"), 0.0)

    profit = max(net_profit, 0.0)
    se_base = profit * se_base_rate
    se_tax = se_base * se_rate
    add_med_tax = se_base * add_med
    # Rough taxable ordinary income proxy after 1/2 SE deduction
    ordinary_base = max(profit - 0.5 * se_tax, 0.0)
    federal_income_proxy = ordinary_base * ordinary
    state_tax = profit * state
    federal_total = se_tax + add_med_tax + federal_income_proxy
    grand = federal_total + state_tax
    return {
        "net_profit": net_profit,
        "se_base": se_base,
        "se_tax": se_tax,
        "additional_medicare": add_med_tax,
        "federal_income_proxy": federal_income_proxy,
        "federal_total_est": federal_total,
        "state_est": state_tax,
        "total_est": grand,
        "effective_blended": (grand / profit) if profit else 0.0,
    }


def payments_paid(rows: List[dict]) -> Tuple[float, float]:
    fed = state = 0.0
    for r in rows:
        fed += fnum(r.get("federal_paid_usd"))
        state += fnum(r.get("state_paid_usd"))
    return fed, state


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Quarterly tax planner (estimates only)")
    ap.add_argument("--income", type=Path, required=True)
    ap.add_argument("--expenses", type=Path, required=True)
    ap.add_argument("--inputs", type=Path, required=True)
    ap.add_argument("--payments", type=Path, help="Quarterly payments log CSV")
    ap.add_argument("--remaining-quarters", type=int, default=0,
                    help="If >0, split remaining federal estimate across N quarters")
    args = ap.parse_args(argv)

    for path in (args.income, args.expenses, args.inputs):
        if not path.exists():
            print(f"Missing: {path}", file=sys.stderr)
            return 1

    income_total, income_by_q = sum_income(load_rows(args.income))
    exp_total, exp_by_q, exp_by_label = sum_expenses(load_rows(args.expenses))
    inputs = load_kv(args.inputs)
    net_profit = income_total - exp_total
    est = estimate(net_profit, inputs)

    fed_paid_file = fnum(inputs.get("ytd_federal_estimated_paid"))
    state_paid_file = fnum(inputs.get("ytd_state_estimated_paid"))
    if args.payments and args.payments.exists():
        fed_paid_log, state_paid_log = payments_paid(load_rows(args.payments))
        # Prefer max of inputs vs log so sample stays consistent if both present
        fed_paid = max(fed_paid_file, fed_paid_log)
        state_paid = max(state_paid_file, state_paid_log)
    else:
        fed_paid, state_paid = fed_paid_file, state_paid_file

    fed_remaining = max(est["federal_total_est"] - fed_paid, 0.0)
    state_remaining = max(est["state_est"] - state_paid, 0.0)

    # Infer remaining quarters from income periods if not set
    rq = args.remaining_quarters
    if rq <= 0:
        seen = {q for q in income_by_q if q.startswith("202") or q.startswith("Q") or "-Q" in q}
        # crude: if Q3 present and Q4 absent → 1 remaining, etc.
        labels = set()
        for q in income_by_q:
            if "Q1" in q:
                labels.add(1)
            if "Q2" in q:
                labels.add(2)
            if "Q3" in q:
                labels.add(3)
            if "Q4" in q:
                labels.add(4)
        rq = max(4 - max(labels or [0]), 1)

    print("=== Quarterly Tax Planner (ESTIMATE ONLY — NOT TAX ADVICE) ===")
    print(f"Tax year:           {inputs.get('tax_year', '')}")
    print(f"Income (net):       ${income_total:,.2f}")
    print(f"Expenses:           ${exp_total:,.2f}")
    print(f"Net profit:         ${net_profit:,.2f}")
    print("---")
    print(f"SE tax (proxy):     ${est['se_tax']:,.2f}")
    print(f"Add’l Medicare:     ${est['additional_medicare']:,.2f}")
    print(f"Ordinary tax proxy: ${est['federal_income_proxy']:,.2f}")
    print(f"Federal total est:  ${est['federal_total_est']:,.2f}")
    print(f"State est:          ${est['state_est']:,.2f}")
    print(f"Combined est:       ${est['total_est']:,.2f}  (blended {est['effective_blended']:.1%} of profit)")
    print("---")
    print(f"Federal paid YTD:   ${fed_paid:,.2f}")
    print(f"State paid YTD:     ${state_paid:,.2f}")
    print(f"Federal remaining:  ${fed_remaining:,.2f}")
    print(f"State remaining:    ${state_remaining:,.2f}")
    print(f"Suggested next fed: ${fed_remaining / rq:,.2f}  across {rq} remaining quarter(s)")
    print(f"Suggested next st:  ${state_remaining / rq:,.2f}")
    print("--- Income by period ---")
    for q in sorted(income_by_q):
        print(f"  {q}: ${income_by_q[q]:,.2f} net  (exp ${exp_by_q.get(q, 0.0):,.2f})")
    print("--- Top Schedule C–style labels ---")
    for label, amt in sorted(exp_by_label.items(), key=lambda x: -x[1])[:8]:
        print(f"  {label}: ${amt:,.2f}")
    print("Confirm all figures with a CPA before paying or filing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
