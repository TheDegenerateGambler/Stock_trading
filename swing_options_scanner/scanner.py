"""
scanner.py — Main entry point for the Swing Options Scanner.

Flow:
  1. Build universe (S&P 500 + Russell 1000, cached 7 days)
  2. Filter universe by price/volume via technical_screener (concurrent)
  3. For each survivor: check earnings safety
  4. For each surviving direction (CALL if BULLISH, PUT if BEARISH, or both):
       pick best contract fitting budget & liquidity
  5. Rank by composite score
  6. Attach trade plan (entry/target/stop)
  7. Output console + HTML + JSON
  8. Launch local HTTP server + open browser (optional)

Usage:
  python scanner.py              # full scan, open browser
  python scanner.py --once       # scan once & exit (no server)
  python scanner.py --tickers AMD,PLTR,SOFI   # only these tickers
  python scanner.py --budget 200 # override budget
  python scanner.py --dir CALL   # calls only
  python scanner.py --no-browser
  python scanner.py --port 8770
"""
from __future__ import annotations
import argparse
import http.server
import os
import socketserver
import sys
import threading
import time
import webbrowser
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional

import config
import universe_builder
import technical_screener
import earnings_calendar
import options_selector
import trade_builder
import swing_ranker
import report_builder


# ─────────────────────────────────────────────────────────────
# Args
# ─────────────────────────────────────────────────────────────
def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Swing Options Scanner")
    ap.add_argument("--tickers", type=str, default="",
                    help="Comma-separated tickers to override the universe")
    ap.add_argument("--budget", type=float, default=None,
                    help="Max contract cost in USD (overrides config)")
    ap.add_argument("--dir", type=str, default=None,
                    choices=["CALL", "PUT", "BOTH"],
                    help="Direction (overrides config)")
    ap.add_argument("--min-score", type=float, default=None,
                    help="Minimum composite score threshold")
    ap.add_argument("--top", type=int, default=None,
                    help="Number of top picks to output")
    ap.add_argument("--once", action="store_true",
                    help="Run one scan and exit (no HTTP server)")
    ap.add_argument("--no-browser", action="store_true",
                    help="Don't auto-open the browser")
    ap.add_argument("--port", type=int, default=None,
                    help="HTTP port for the report viewer")
    ap.add_argument("--refresh-universe", action="store_true",
                    help="Force rebuild of the ticker universe")
    ap.add_argument("--ignore-earnings", action="store_true",
                    help="Don't skip tickers with earnings in the hold window")
    ap.add_argument("--earnings-skip-days", type=int, default=None,
                    help="Override SKIP_EARNINGS_DAYS (e.g. 7 to only skip if earnings within a week)")
    return ap.parse_args()


# ─────────────────────────────────────────────────────────────
# Ticker processing
# ─────────────────────────────────────────────────────────────
def _process_ticker(ticker: str, direction_mode: str) -> List[Dict]:
    """Return zero or more pick dicts for a ticker (may be CALL, PUT, or both)."""
    picks = []
    try:
        tech = technical_screener.analyze(ticker)
        if not tech:
            return picks

        # Decide which directions to try
        directions = []
        if direction_mode == "BOTH":
            if tech["direction"] == "BULLISH":
                directions = ["CALL"]
            elif tech["direction"] == "BEARISH":
                directions = ["PUT"]
            # NEUTRAL: skip
        elif direction_mode == "CALL" and tech["direction"] != "BEARISH":
            directions = ["CALL"]
        elif direction_mode == "PUT" and tech["direction"] != "BULLISH":
            directions = ["PUT"]

        if not directions:
            return picks

        # Earnings check (fetched once, cached)
        earnings_days = earnings_calendar.get_days_to_earnings(ticker)
        # Sentinel: config.SKIP_EARNINGS_DAYS < 0 means "don't skip anything"
        if config.SKIP_EARNINGS_DAYS >= 0:
            skip_window = config.SKIP_EARNINGS_DAYS
            if (earnings_days is not None and 0 <= earnings_days <= skip_window):
                # Skip: earnings during hold window
                return picks

        for direction in directions:
            contract = options_selector.pick_best_contract(
                ticker, tech["price"], direction)
            if not contract:
                continue

            # Attach trade plan
            trade_builder.build(contract, tech["price"], direction)

            # Compose final score
            rank_info = swing_ranker.rank(tech, contract, direction, earnings_days)

            pick = dict(tech)                     # copy technicals
            pick["spot"] = tech["price"]
            pick["contract"] = contract
            pick.update(rank_info)
            picks.append(pick)

    except Exception as e:
        print(f"  [scanner] {ticker}: error ({e})")
    return picks


# ─────────────────────────────────────────────────────────────
# Main scan
# ─────────────────────────────────────────────────────────────
def run_scan(direction_mode: str, min_score: float, top_n: int,
             tickers_override: Optional[List[str]] = None,
             refresh_universe: bool = False) -> List[Dict]:
    """Run one full scan and return ranked picks."""

    # 1. Universe
    if tickers_override:
        tickers = [t.upper() for t in tickers_override if t.strip()]
        print(f"  [scanner] Using override tickers: {tickers}")
    else:
        tickers = universe_builder.build_universe(force_refresh=refresh_universe)

    print(f"  [scanner] Scanning {len(tickers)} tickers...")
    print(f"  [scanner] Direction mode: {direction_mode}")
    print(f"  [scanner] Budget: ${config.BUDGET_USD} USD (max contract "
          f"${config.MAX_CONTRACT_COST})")

    # 2. Concurrent processing
    all_picks: List[Dict] = []
    with ThreadPoolExecutor(max_workers=config.CONCURRENT_WORKERS) as ex:
        futures = {ex.submit(_process_ticker, t, direction_mode): t
                   for t in tickers}
        done = 0
        for fut in as_completed(futures):
            done += 1
            if done % 25 == 0:
                print(f"  [scanner] progress: {done}/{len(tickers)}  "
                      f"(picks so far: {len(all_picks)})")
            try:
                res = fut.result()
                if res:
                    all_picks.extend(res)
            except Exception as e:
                t = futures[fut]
                print(f"  [scanner] {t}: worker error ({e})")

    # 3. Filter & rank
    qualified = [p for p in all_picks if p["composite_score"] >= min_score]
    qualified.sort(key=lambda p: p["composite_score"], reverse=True)
    top = qualified[:top_n]

    print(f"  [scanner] {len(all_picks)} raw picks -> {len(qualified)} "
          f"scoring >= {min_score} -> top {len(top)}")
    return top


# ─────────────────────────────────────────────────────────────
# HTTP server
# ─────────────────────────────────────────────────────────────
class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # silence logs


def _start_http_server(port: int) -> None:
    os.chdir(config.OUTPUT_DIR)
    with socketserver.TCPServer(("", port), _QuietHandler) as httpd:
        httpd.serve_forever()


def _open_browser(port: int) -> None:
    time.sleep(1)  # let server start
    url = f"http://localhost:{port}/swing_options_scanner.html"
    try:
        webbrowser.open(url)
    except Exception:
        print(f"  [scanner] Open manually: {url}")


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────
def main() -> int:
    args = parse_args()

    # Apply overrides
    if args.budget is not None:
        config.BUDGET_USD = float(args.budget)
        config.MAX_CONTRACT_COST = float(args.budget) * 1.35
    if args.dir is not None:
        config.DIRECTION = args.dir
    if args.ignore_earnings:
        config.SKIP_EARNINGS_DAYS = -1   # sentinel: never skip
    elif args.earnings_skip_days is not None:
        config.SKIP_EARNINGS_DAYS = args.earnings_skip_days

    direction_mode = config.DIRECTION
    min_score = args.min_score if args.min_score is not None else config.TRADE_THRESHOLD_SCORE
    top_n     = args.top if args.top is not None else config.TOP_N
    port      = args.port if args.port is not None else config.HTTP_PORT

    ticker_override = None
    if args.tickers.strip():
        ticker_override = [t.strip() for t in args.tickers.split(",")]

    Path(config.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    picks = run_scan(direction_mode, min_score, top_n,
                     tickers_override=ticker_override,
                     refresh_universe=args.refresh_universe)
    elapsed = time.time() - t0
    print(f"  [scanner] Scan complete in {elapsed:.1f}s")

    report_builder.write_all(picks)

    if args.once:
        return 0

    # Start HTTP server + open browser
    print(f"\n  [scanner] Serving report at http://localhost:{port}/swing_options_scanner.html")
    print(f"  [scanner] Press Ctrl+C to stop.\n")

    server_thread = threading.Thread(
        target=_start_http_server, args=(port,), daemon=True)
    server_thread.start()

    if not args.no_browser:
        threading.Thread(target=_open_browser, args=(port,), daemon=True).start()

    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n  [scanner] Stopped by user.")
        return 0


if __name__ == "__main__":
    sys.exit(main())