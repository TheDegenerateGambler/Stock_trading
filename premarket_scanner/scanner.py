"""
scanner.py — Premarket Scanner main entry point.

Filters:
  gap_pct > 5   AND   price > $3   AND   premarket_volume > 50,000
Result: top 10 by gap_pct DESC, with news catalyst + AV sentiment.

Loop: every 20 minutes until 09:20 AM ET, then exit.

Usage:
  python scanner.py                # loop until 9:20 AM ET, opens browser
  python scanner.py --once         # single scan, exit
  python scanner.py --no-browser   # do not open browser
  python scanner.py --force        # bypass 9:20 AM cutoff for testing
  python scanner.py --refresh-universe   # force refresh S&P/Russell list
"""
from __future__ import annotations
import argparse
import functools
import http.server
import os
import socket
import socketserver
import sys
import threading
import time
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path

# stdout UTF-8
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import config
import universe as universe_mod
import premarket_data
import news_fetcher
import alphavantage_client as av
import report_builder as report

try:
    from zoneinfo import ZoneInfo
    _ET = ZoneInfo("America/New_York")
except Exception:
    _ET = None


OUT = Path(config.OUTPUT_DIR)
OUT.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────────────────────
# Small HTTP server for viewing the report
# ─────────────────────────────────────────────────────────────
class _Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


def _find_port(p, tries=20):
    for i in range(tries):
        with socket.socket() as s:
            try:
                s.bind(("127.0.0.1", p + i))
                return p + i
            except OSError:
                continue
    return p


def start_server(port):
    rp = _find_port(port)
    h  = functools.partial(_Handler, directory=str(OUT))
    srv = socketserver.ThreadingTCPServer(("127.0.0.1", rp), h)
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True, name="pm-http").start()
    return rp


# ─────────────────────────────────────────────────────────────
# Time helpers
# ─────────────────────────────────────────────────────────────
def now_et():
    return datetime.now(_ET) if _ET else datetime.now()


def past_cutoff(dt=None):
    dt = dt or now_et()
    cutoff = dt.replace(hour=config.STOP_HOUR_ET,
                        minute=config.STOP_MIN_ET,
                        second=0, microsecond=0)
    return dt >= cutoff


def fmt_time(dt):
    return dt.strftime("%Y-%m-%d %I:%M:%S %p ET")


# ─────────────────────────────────────────────────────────────
# Single scan
# ─────────────────────────────────────────────────────────────
def run_scan(refresh_universe=False):
    t0 = time.time()
    print("")
    print("[" + now_et().strftime("%H:%M:%S ET") + "] === PREMARKET SCAN ===")

    # 1. Universe
    tickers = universe_mod.build_universe(force_refresh=refresh_universe)

    # 2. Premarket data (concurrent yfinance)
    print("  Fetching premarket bars for " + str(len(tickers)) + " tickers...")
    rows = premarket_data.fetch_premarket(tickers)
    print("  Tickers with premarket data: " + str(len(rows)))

    # 3. Apply filters + cap at 10
    picks = premarket_data.apply_filters(rows)
    print("  After filters: " + str(len(picks)) + " picks")

    # 4. Enrich with news + sentiment (top 10 only)
    if picks:
        print("  Fetching news + sentiment for top " + str(len(picks)) + "...")
        picks = news_fetcher.enrich(picks)

    elapsed = time.time() - t0
    print("  Scan complete in " + "{:.1f}".format(elapsed) + "s")

    return picks, len(tickers), len(rows)


# ─────────────────────────────────────────────────────────────
# Output writer
# ─────────────────────────────────────────────────────────────
def emit(picks, universe_size, scanned, next_scan_dt):
    now = now_et()
    now_str   = fmt_time(now)
    next_str  = next_scan_dt.strftime("%I:%M %p ET") if next_scan_dt else "(none)"
    budget    = av.get_budget_status()

    meta = {
        "now_str":       now_str,
        "next_scan":     next_str,
        "budget":        budget,
        "universe_size": universe_size,
        "scanned":       scanned,
        "filters": {
            "gap_min_pct":   config.GAP_MIN_PCT,
            "price_min":     config.PRICE_MIN,
            "pm_volume_min": config.PM_VOLUME_MIN,
            "top_n":         config.TOP_N,
        },
    }

    report.render_console(picks, now_str, next_str, budget, universe_size, scanned)
    report.write_html(picks, meta)
    report.write_json(picks, meta)


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description="Premarket Scanner")
    ap.add_argument("--once", action="store_true", help="One scan then exit")
    ap.add_argument("--no-browser", action="store_true", help="Do not open browser")
    ap.add_argument("--force", action="store_true",
                    help="Bypass the 9:20 AM ET cutoff (for testing)")
    ap.add_argument("--refresh-universe", action="store_true",
                    help="Force rebuild the ticker universe")
    ap.add_argument("--port", type=int, default=config.HTTP_PORT)
    args = ap.parse_args()

    port = start_server(args.port)
    url  = "http://127.0.0.1:" + str(port) + "/premarket_report.html"

    print("=" * 60)
    print("  PREMARKET SCANNER")
    print("=" * 60)
    print("  Filters       : gap>" + str(config.GAP_MIN_PCT) +
          "%  price>$" + str(config.PRICE_MIN) +
          "  PM_vol>" + format(config.PM_VOLUME_MIN, ",") +
          "  top " + str(config.TOP_N))
    print("  Loop interval : " + str(config.LOOP_INTERVAL_MIN) + " min")
    print("  Stops at      : {:02d}:{:02d} AM ET".format(
        config.STOP_HOUR_ET, config.STOP_MIN_ET))
    print("  AV enabled    : " + str(config.AV_ENABLED))
    print("  Report URL    : " + url)
    print("=" * 60)

    if not args.no_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    # ── First scan ──
    if past_cutoff() and not args.force and not args.once:
        print("")
        print("  Current time is past " +
              "{:02d}:{:02d} AM ET".format(config.STOP_HOUR_ET, config.STOP_MIN_ET) +
              " -> running one scan then exiting.")
        picks, uni, scanned = run_scan(refresh_universe=args.refresh_universe)
        emit(picks, uni, scanned, next_scan_dt=None)
        print("")
        print("Done. Report: " + url)
        return 0

    picks, uni, scanned = run_scan(refresh_universe=args.refresh_universe)
    next_dt = now_et() + timedelta(minutes=config.LOOP_INTERVAL_MIN)
    emit(picks, uni, scanned, next_dt)

    if args.once:
        print("")
        print("--once: done. Report: " + url)
        return 0

    # ── Loop ──
    try:
        while True:
            if past_cutoff(next_dt) and not args.force:
                print("")
                print("  Next scan " + next_dt.strftime("%I:%M %p ET") +
                      " is past cutoff " +
                      "{:02d}:{:02d} AM ET".format(config.STOP_HOUR_ET, config.STOP_MIN_ET) +
                      " -> exiting.")
                break

            # Sleep until next_dt
            while True:
                now = now_et()
                remaining = (next_dt - now).total_seconds()
                if remaining <= 0:
                    break
                mm, ss = divmod(int(remaining), 60)
                sys.stdout.write("\r  Next scan in {:02d}:{:02d}   ".format(mm, ss))
                sys.stdout.flush()
                time.sleep(min(30, max(1, remaining)))
            print("")

            picks, uni, scanned = run_scan()
            next_dt = now_et() + timedelta(minutes=config.LOOP_INTERVAL_MIN)
            emit(picks, uni, scanned, next_dt)

    except KeyboardInterrupt:
        print("")
        print("Stopped by user.")
        return 0

    print("")
    print("Final report: " + url)
    return 0


if __name__ == "__main__":
    sys.exit(main())