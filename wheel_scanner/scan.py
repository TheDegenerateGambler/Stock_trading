"""
Main entry point for the Canadian Wheel Scanner (cash-secured puts).

Usage:
    python scan.py                          # default: monthly, CAD watchlist
    python scan.py --weekly                 # weeklies on US + TSX weekly watchlists
    python scan.py --weekly --us-only       # weeklies on US names only
    python scan.py --weekly --tsx-only      # weeklies on TSX blue-chips only
    python scan.py BTO.TO SOFI              # scan custom tickers

Outputs written to ./output/:
    - wheel_candidates.csv
    - wheel_candidates.html
    - wheel_candidates.txt
    - wheel_candidates.json
"""
from __future__ import annotations

import argparse
import sys
from typing import Iterable

from config import (
    ACCOUNT_BUDGET_CAD,
    CANADIAN_WHEEL_WATCHLIST,
    CONTRACT_SIZE,
    DEFAULT_USD_CAD,
    MAX_STOCK_PRICE_CAD,
    MIN_STOCK_PRICE_CAD,
    OPTION_COMMISSION_PER_CONTRACT,
    OPTION_COMMISSION_PER_CONTRACT_USD,
    WEEKLY_TSX_WATCHLIST,
    WEEKLY_US_WATCHLIST,
)
from data_provider import get_stock_snapshot, polite_sleep
from report_builder import write_reports
from wheel_analyzer import (
    WheelCandidate,
    find_best_put_across_expirations,
    score_candidates,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Canadian Wheel Scanner (CSP)")
    p.add_argument(
        "tickers",
        nargs="*",
        help="Optional custom ticker list. Defaults to the watchlist based on mode.",
    )
    p.add_argument(
        "--weekly",
        action="store_true",
        help="Weekly-options mode: 4-14 DTE, tighter liquidity, US+TSX weekly watchlists.",
    )
    p.add_argument(
        "--us-only",
        action="store_true",
        help="In weekly mode, scan only US-listed tickers.",
    )
    p.add_argument(
        "--tsx-only",
        action="store_true",
        help="In weekly mode, scan only TSX-listed tickers.",
    )
    p.add_argument(
        "--max-price",
        type=float,
        default=None,
        help=f"Max stock price in native currency. Default: ${MAX_STOCK_PRICE_CAD:.2f} "
             f"(monthly mode) or budget/100 (weekly mode).",
    )
    p.add_argument(
        "--min-price",
        type=float,
        default=MIN_STOCK_PRICE_CAD,
        help=f"Min stock price (default ${MIN_STOCK_PRICE_CAD:.2f}).",
    )
    p.add_argument(
        "--budget",
        type=float,
        default=ACCOUNT_BUDGET_CAD,
        help=f"Total cash budget in CAD (default ${ACCOUNT_BUDGET_CAD:.2f}).",
    )
    p.add_argument(
        "--usd-cad",
        type=float,
        default=DEFAULT_USD_CAD,
        help=f"USD-to-CAD FX rate for affordability check (default {DEFAULT_USD_CAD}).",
    )
    return p.parse_args()


def choose_watchlist(args: argparse.Namespace) -> list[str]:
    if args.tickers:
        return args.tickers
    if not args.weekly:
        return CANADIAN_WHEEL_WATCHLIST
    # Weekly mode
    if args.us_only:
        return WEEKLY_US_WATCHLIST
    if args.tsx_only:
        return WEEKLY_TSX_WATCHLIST
    return WEEKLY_US_WATCHLIST + WEEKLY_TSX_WATCHLIST


def scan(
    tickers: Iterable[str],
    max_price_native: float,
    min_price_native: float,
    weekly: bool,
    budget: float,
    usd_cad: float,
) -> list[WheelCandidate]:
    candidates: list[WheelCandidate] = []
    skipped: list[tuple[str, str]] = []

    ticker_list = list(tickers)
    print(f"\nScanning {len(ticker_list)} tickers {'(WEEKLY mode)' if weekly else '(monthly mode)'}...\n")

    for i, ticker in enumerate(ticker_list, 1):
        print(f"[{i}/{len(ticker_list)}] {ticker}")
        snap = get_stock_snapshot(ticker)
        polite_sleep(0.3)
        if snap is None:
            skipped.append((ticker, "no data"))
            continue

        cur = (snap.currency or "CAD").upper()
        print(f"    price ${snap.price:.2f} {cur}  ({snap.name})")

        # Compute affordability limit in native currency
        # Budget is always in CAD; convert for USD names.
        if cur == "USD":
            budget_native = budget / usd_cad
        elif cur == "CAD":
            budget_native = budget
        else:
            skipped.append((ticker, f"unsupported currency ({cur})"))
            continue

        # Effective max stock price = min(user max, budget/100 in native currency)
        # (You can't buy 100 shares if 100*price > your CAD budget converted.)
        effective_max = min(max_price_native, budget_native / CONTRACT_SIZE)

        if snap.price > effective_max:
            skipped.append(
                (ticker, f"price ${snap.price:.2f} > affordable ${effective_max:.2f} {cur}")
            )
            continue
        if snap.price < min_price_native:
            skipped.append((ticker, f"price < ${min_price_native:.2f}"))
            continue

        cand = find_best_put_across_expirations(
            snap, weekly=weekly, budget=budget, usd_cad=usd_cad
        )
        if cand is None:
            reason = "no valid put in weekly window" if weekly else "no valid put in DTE/OTM window"
            skipped.append((ticker, reason))
            continue

        print(f"    -> ${cand.strike:.2f} put exp {cand.expiration} "
              f"({cand.dte}d)  premium ${cand.premium_cad:.2f} {cur}  "
              f"ann yield {cand.annualized_yield_pct*100:.1f}%")
        candidates.append(cand)

    if skipped:
        print("\nSkipped:")
        for t, reason in skipped:
            print(f"  - {t}: {reason}")

    return candidates


def main() -> int:
    args = parse_args()

    if args.us_only and args.tsx_only:
        print("Error: --us-only and --tsx-only are mutually exclusive.")
        return 2

    tickers = choose_watchlist(args)
    mode_label = "WEEKLY" if args.weekly else "MONTHLY"

    # Default max price: for monthly, use MAX_STOCK_PRICE_CAD; for weekly, use budget/100 in native.
    # (Native max is enforced later per-ticker.)
    if args.max_price is not None:
        max_price = args.max_price
    else:
        max_price = MAX_STOCK_PRICE_CAD if not args.weekly else 1e9  # weekly: only budget bounds it

    print("=" * 74)
    print(f"CANADIAN WHEEL SCANNER — CSP  [{mode_label}]")
    print(f"  Broker fees: $0 stock, ${OPTION_COMMISSION_PER_CONTRACT:.2f}/opt CAD, "
          f"${OPTION_COMMISSION_PER_CONTRACT_USD:.2f}/opt USD (NBDB)")
    print(f"  Budget:      ${args.budget:,.2f} CAD  (USD-equiv ${args.budget/args.usd_cad:,.2f})")
    if args.weekly:
        print(f"  Max strike:  budget/100 = ${args.budget/CONTRACT_SIZE:.2f} CAD  "
              f"(${args.budget/args.usd_cad/CONTRACT_SIZE:.2f} USD)")
    else:
        print(f"  Price band:  ${args.min_price:.2f} – ${max_price:.2f}  (CAD watchlist)")
    print(f"  Watchlist:   {len(tickers)} tickers")
    print("=" * 74)

    candidates = scan(
        tickers,
        max_price_native=max_price,
        min_price_native=args.min_price,
        weekly=args.weekly,
        budget=args.budget,
        usd_cad=args.usd_cad,
    )

    if not candidates:
        print("\nNo candidates matched. Try relaxing filters in config.py.")
        write_reports([])
        return 1

    ranked = score_candidates(candidates)

    print("\n" + "=" * 74)
    print(f"TOP CANDIDATES ({len(ranked)}):")
    print("=" * 74)
    for i, c in enumerate(ranked[:10], 1):
        print(f"{i:2d}. [{c.score:5.2f}] {c.ticker:10s} {c.currency}  "
              f"${c.strike:6.2f} put  {c.expiration}  "
              f"({c.dte:2d}d)  ann {c.annualized_yield_pct*100:5.1f}%  "
              f"collat ${c.collateral_in_cad:7,.0f} CAD-eq")

    paths = write_reports(ranked)
    print("\nReports written:")
    for k, v in paths.items():
        print(f"  {k:5s}: {v}")
    print("\nOpen the HTML report in a browser for the prettiest view.")
    print("Remember: verify all quotes with your broker. Not financial advice.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())