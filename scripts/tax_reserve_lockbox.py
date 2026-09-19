#!/usr/bin/env python3
"""
Tax reserve lockbox tracker.

Reads deposit / estimated-payment rows and reports balance, QTD funding,
and whether the next quarterly payment looks covered.

Usage:
  python3 tax_reserve_lockbox.py --ledger ../samples/sample_tax_reserve_lockbox.csv
  python3 tax_reserve_lockbox.py --ledger ../samples/sample_tax_reserve_lockbox.csv \\
      --next-payment 3200 --label 2026-Q2
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import List, Optional


def money(s: str) -> float:
    s = (s or "").replace("$", "").replace(",", "").strip()
    if not s:
        return 0.0
    return round(float(s), 2)


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Tax reserve lockbox balance + coverage")
    p.add_argument("--ledger", type=Path, required=True)
    p.add_argument("--next-payment", type=float, default=None, help="Upcoming estimated payment amount")
    p.add_argument("--label", default="", help="Label for next payment (e.g. 2026-Q2)")
    args = p.parse_args(argv)

    deposits = 0.0
    withdrawals = 0.0
    adjustments = 0.0
    last_balance = None
    by_q_deposits = {}
    rows = []
    with args.ledger.open(newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if not any((v or "").strip() for v in row.values()):
                continue
            first = next(iter(row.values()))
            if str(first).strip().startswith("#"):
                continue
            rows.append(row)

    print(f"{'date':<12} {'direction':<22} {'amount':>10} {'balance':>10}  quarter")
    for r in rows:
        direction = (r.get("direction") or "").strip().lower()
        amt = money(r.get("amount") or "0")
        bal = r.get("balance_after")
        bal_f = money(bal) if bal not in (None, "") else None
        q = (r.get("quarter_applied") or "").strip()
        if direction == "deposit":
            deposits += amt
            by_q_deposits[q] = by_q_deposits.get(q, 0.0) + amt
        elif direction == "withdrawal_payment":
            withdrawals += amt
        elif direction == "adjustment":
            adjustments += amt
        if bal_f is not None:
            last_balance = bal_f
        print(f"{(r.get('date') or ''):<12} {direction:<22} {amt:10.2f} {(bal_f if bal_f is not None else 0):10.2f}  {q}")

    computed = round(deposits - withdrawals + adjustments, 2)
    print("\n=== Lockbox summary ===")
    print(f"  Deposits:     {deposits:,.2f}")
    print(f"  Payments out: {withdrawals:,.2f}")
    print(f"  Adjustments:  {adjustments:,.2f}")
    print(f"  Computed bal: {computed:,.2f}")
    if last_balance is not None:
        print(f"  Ledger bal:   {last_balance:,.2f}")
        if abs(computed - last_balance) > 0.05:
            print("  WARNING: computed balance ≠ last balance_after — check running total.")
    print("\n  Deposits by quarter applied:")
    for k in sorted(by_q_deposits.keys()):
        print(f"    {k or 'unlabeled'}: {by_q_deposits[k]:,.2f}")

    bal = last_balance if last_balance is not None else computed
    if args.next_payment is not None:
        gap = round(args.next_payment - bal, 2)
        label = args.label or "next payment"
        print(f"\n=== Coverage — {label} ===")
        print(f"  Balance:     {bal:,.2f}")
        print(f"  Due:         {args.next_payment:,.2f}")
        if gap <= 0:
            print(f"  Status:      COVERED (surplus {abs(gap):,.2f})")
        else:
            print(f"  Status:      SHORT by {gap:,.2f} — transfer before due date")

    print("\nDisclaimer: Bookkeeping helper only — not tax advice.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
