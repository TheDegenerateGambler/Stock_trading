"""
Covered Call scanner CLI (with weekly + US watchlist support).

Modes:
  1. Position mode — you already own shares:
       python scan_cc.py --positions BTO.TO:5.20:100 F:11.80:100
     Format: TICKER:COST_BASIS:SHARES

  2. Buy-write mode — no existing position, plan to buy + sell a call:
       python scan_cc.py --buy-write                  # monthly, CAD watchlist
       python scan_cc.py --buy-write --weekly         # weeklies on US+TSX
       python scan_cc.py --buy-write --weekly --us-only
       python scan_cc.py --buy-write --weekly --tsx-only

Combine with --run-puts to also run the CSP scanner and get the combined
wheel dashboard HTML.

Outputs go to ./output/:
    cc_candidates.csv / html / txt / json
    wheel_dashboard.html   (if --dashboard or --run-puts)
"""
from __future__ import annotations

import argparse
import sys

from cc_analyzer import (
    CCCandidate,
    find_best_call_across_expirations,
    score_cc_candidates,
)
from cc_report_builder import write_cc_reports, write_dashboard
from config import (
    ACCOUNT_BUDGET_CAD,
    CANADIAN_WHEEL_WATCHLIST,
    CC_BUY_WRITE_ENFORCE_BUDGET,
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


def parse_position(pos: str) -> tuple[str, float, int]:
    """Parse 'TICKER:COST:SHARES' -> (ticker, cost_basis, shares)."""
    parts = pos.split(":")
    if len(parts) < 2 or len(parts) > 3:
        raise argparse.ArgumentTypeError(
            f"Invalid position '{pos}'. Expected TICKER:COST[:SHARES]"
        )
    ticker = parts[0].strip().upper()
    try:
        cost = float(parts[1])
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid cost basis in '{pos}'")
    shares = 100
    if len(parts) == 3:
        try:
            shares = int(parts[2])
        except ValueError:
            raise argparse.ArgumentTypeError(f"Invalid share count in '{pos}'")
    if shares < 100:
        print(f"  [warn] {ticker}: {shares} shares — need at least 100 to write a CC")
    return ticker, cost, shares


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Canadian Covered Call Scanner")
    p.add_argument("--positions", nargs="+", default=[],
                   help="Positions owned, format TICKER:COST_BASIS[:SHARES].")
    p.add_argument("--buy-write", action="store_true",
                   help="Scan watchlist for buy-write setups.")
    p.add_argument("--tickers", nargs="*", default=None,
                   help="Custom tickers for buy-write scan.")
    p.add_argument("--weekly", action="store_true",
                   help="Weekly-options mode (4-14 DTE).")
    p.add_argument("--us-only", action="store_true",
                   help="Weekly mode: use only US watchlist.")
    p.add_argument("--tsx-only", action="store_true",
                   help="Weekly mode: use only TSX watchlist.")
    p.add_argument("--max-price", type=float, default=None,
                   help="Max stock price in native currency.")
    p.add_argument("--min-price", type=float, default=MIN_STOCK_PRICE_CAD)
    p.add_argument("--budget", type=float, default=ACCOUNT_BUDGET_CAD)
    p.add_argument("--usd-cad", type=float, default=DEFAULT_USD_CAD)
    p.add_argument("--no-budget-enforce", action="store_true",
                   help="Don't enforce 100 shares fit in budget (buy-write).")
    p.add_argument("--run-puts", action="store_true",
                   help="Also run CSP scanner + build combined dashboard.")
    p.add_argument("--dashboard", action="store_true",
                   help="Build the combined wheel dashboard HTML.")
    return p.parse_args()


def choose_buy_write_watchlist(args: argparse.Namespace) -> list[str]:
    if args.tickers:
        return args.tickers
    if not args.weekly:
        return CANADIAN_WHEEL_WATCHLIST
    if args.us_only:
        return WEEKLY_US_WATCHLIST
    if args.tsx_only:
        return WEEKLY_TSX_WATCHLIST
    return WEEKLY_US_WATCHLIST + WEEKLY_TSX_WATCHLIST


def scan_positions(
    positions: list[tuple[str, float, int]],
    weekly: bool = False,
    usd_cad: float = DEFAULT_USD_CAD,
) -> list[CCCandidate]:
    out: list[CCCandidate] = []
    label = "WEEKLY" if weekly else "monthly"
    print(f"\nScanning {len(positions)} positions ({label})...\n")
    for i, (ticker, cost, shares) in enumerate(positions, 1):
        print(f"[{i}/{len(positions)}] {ticker}  (basis ${cost:.2f}, {shares} sh)")
        snap = get_stock_snapshot(ticker)
        polite_sleep(0.3)
        if snap is None:
            print("    [skip] no data")
            continue
        print(f"    spot ${snap.price:.2f} {snap.currency}  ({snap.name})")

        cand = find_best_call_across_expirations(
            snap, cost_basis=cost, shares_held=shares, mode="position",
            weekly=weekly, usd_cad=usd_cad,
        )
        if cand is None:
            print("    [skip] no valid call above cost basis")
            continue
        print(f"    -> ${cand.strike:.2f} call exp {cand.expiration} "
              f"({cand.dte}d)  premium ${cand.premium_cad:.2f} {cand.currency}  "
              f"if-called ann {cand.if_called_yield_ann_pct*100:.1f}%")
        out.append(cand)
    return out


def scan_buy_write(
    tickers: list[str],
    max_price_native: float,
    min_price_native: float,
    budget: float,
    enforce_budget: bool,
    weekly: bool = False,
    usd_cad: float = DEFAULT_USD_CAD,
) -> list[CCCandidate]:
    out: list[CCCandidate] = []
    skipped: list[tuple[str, str]] = []
    label = "WEEKLY" if weekly else "monthly"
    print(f"\nBuy-write scanning {len(tickers)} tickers ({label})...\n")

    for i, ticker in enumerate(tickers, 1):
        print(f"[{i}/{len(tickers)}] {ticker}")
        snap = get_stock_snapshot(ticker)
        polite_sleep(0.3)
        if snap is None:
            skipped.append((ticker, "no data"))
            continue

        cur = (snap.currency or "CAD").upper()
        print(f"    price ${snap.price:.2f} {cur}")

        if cur == "USD":
            budget_native = budget / usd_cad
        elif cur == "CAD":
            budget_native = budget
        else:
            skipped.append((ticker, f"unsupported currency ({cur})"))
            continue

        if enforce_budget:
            effective_max = min(max_price_native, budget_native / CONTRACT_SIZE)
        else:
            effective_max = max_price_native

        if snap.price > effective_max:
            skipped.append(
                (ticker, f"price ${snap.price:.2f} > affordable ${effective_max:.2f} {cur}")
            )
            continue
        if snap.price < min_price_native:
            skipped.append((ticker, f"price < ${min_price_native:.2f}"))
            continue

        cand = find_best_call_across_expirations(
            snap, cost_basis=None, shares_held=100, mode="buy-write",
            weekly=weekly, usd_cad=usd_cad,
        )
        if cand is None:
            reason = "no valid call in weekly window" if weekly else "no valid call in DTE/OTM window"
            skipped.append((ticker, reason))
            continue
        print(f"    -> ${cand.strike:.2f} call exp {cand.expiration} "
              f"({cand.dte}d)  premium ${cand.premium_cad:.2f} {cand.currency}  "
              f"if-called ann {cand.if_called_yield_ann_pct*100:.1f}%")
        out.append(cand)

    if skipped:
        print("\nSkipped:")
        for t, reason in skipped:
            print(f"  - {t}: {reason}")

    return out


def maybe_run_puts(weekly: bool, usd_cad: float, tickers: list[str]):
    """Run the CSP scanner in-process and return its ranked candidates."""
    print("\n" + "=" * 70)
    print(f"Also running CSP scanner ({'WEEKLY' if weekly else 'monthly'})...")
    print("=" * 70)
    from scan import scan as run_put_scan
    from wheel_analyzer import score_candidates as score_puts
    from report_builder import write_reports as write_put_reports

    max_price = 1e9 if weekly else MAX_STOCK_PRICE_CAD

    put_candidates = run_put_scan(
        tickers,
        max_price_native=max_price,
        min_price_native=MIN_STOCK_PRICE_CAD,
        weekly=weekly,
        budget=ACCOUNT_BUDGET_CAD,
        usd_cad=usd_cad,
    )
    put_ranked = score_puts(put_candidates) if put_candidates else []
    if put_ranked:
        write_put_reports(put_ranked)
    return put_ranked


def main() -> int:
    args = parse_args()

    if not args.positions and not args.buy_write:
        print("Error: specify either --positions or --buy-write (or both).")
        print("Example:")
        print("  python scan_cc.py --positions BTO.TO:5.20:100")
        print("  python scan_cc.py --buy-write")
        print("  python scan_cc.py --buy-write --weekly")
        return 2

    if args.us_only and args.tsx_only:
        print("Error: --us-only and --tsx-only are mutually exclusive.")
        return 2

    mode_label = "WEEKLY" if args.weekly else "MONTHLY"
    print("=" * 74)
    print(f"CANADIAN COVERED CALL SCANNER  [{mode_label}]")
    print(f"  Broker fees: $0 stock, ${OPTION_COMMISSION_PER_CONTRACT:.2f}/opt CAD, "
          f"${OPTION_COMMISSION_PER_CONTRACT_USD:.2f}/opt USD (NBDB)")
    print(f"  Budget:      ${args.budget:,.2f} CAD  (USD-equiv ${args.budget/args.usd_cad:,.2f})")
    print("=" * 74)

    # Default max price: monthly = $10 native (legacy), weekly = unlimited (budget-bound)
    if args.max_price is not None:
        max_price = args.max_price
    else:
        max_price = MAX_STOCK_PRICE_CAD if not args.weekly else 1e9

    candidates: list[CCCandidate] = []

    if args.positions:
        positions = [parse_position(p) for p in args.positions]
        candidates.extend(scan_positions(positions, weekly=args.weekly, usd_cad=args.usd_cad))

    if args.buy_write:
        tickers = choose_buy_write_watchlist(args)
        enforce = CC_BUY_WRITE_ENFORCE_BUDGET and not args.no_budget_enforce
        candidates.extend(
            scan_buy_write(
                tickers,
                max_price_native=max_price,
                min_price_native=args.min_price,
                budget=args.budget,
                enforce_budget=enforce,
                weekly=args.weekly,
                usd_cad=args.usd_cad,
            )
        )

    if not candidates:
        print("\nNo covered-call candidates matched. Try relaxing filters.")
        write_cc_reports([])
        return 1

    ranked = score_cc_candidates(candidates)

    print("\n" + "=" * 74)
    print(f"TOP CC CANDIDATES ({len(ranked)}):")
    print("=" * 74)
    for i, c in enumerate(ranked[:10], 1):
        print(f"{i:2d}. [{c.score:5.2f}] {c.ticker:10s} {c.currency} {c.mode:10s}  "
              f"${c.strike:6.2f} call  {c.expiration}  "
              f"({c.dte:2d}d)  if-called {c.if_called_yield_ann_pct*100:5.1f}%  "
              f"premium ${c.premium_cad:5.0f}")

    paths = write_cc_reports(ranked)
    print("\nCC reports written:")
    for k, v in paths.items():
        print(f"  {k:5s}: {v}")

    put_ranked = None
    if args.run_puts:
        # Use the same watchlist selection logic for the CSP scanner
        put_tickers = choose_buy_write_watchlist(args)
        put_ranked = maybe_run_puts(args.weekly, args.usd_cad, put_tickers)

    if args.run_puts or args.dashboard:
        dash_path = write_dashboard(put_ranked, ranked)
        print(f"\nCombined dashboard: {dash_path}")

    print("\nOpen the HTML report(s) in a browser for the prettiest view.")
    print("Remember: verify all quotes with your broker. Not financial advice.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
