"""
daytrader.py — Options Day Trader main entry.

Every 5 minutes from 9:30 AM to 12:00 PM ET, this script:
  1. Analyzes SPY and QQQ (always) and picks a 0DTE (or nearest weekly) contract.
  2. Loads today's top-10 gap-up picks from premarket_scanner/output/premarket_picks.json
     and picks the single best options play across them.
  3. Writes a console table + HTML report (with TradingView charts).

Usage:
  python daytrader.py                  # loop until 12:00 PM ET
  python daytrader.py --once           # one scan and exit
  python daytrader.py --force          # ignore session bounds
  python daytrader.py --no-browser
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
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))

# Add premarket_scanner FIRST (lower priority), then HERE at the top
# so `import config` always resolves to options_daytrader/config.py.
PM_DIR = os.path.abspath(os.path.join(HERE, "..", "premarket_scanner"))
if os.path.isdir(PM_DIR) and PM_DIR not in sys.path:
    sys.path.append(PM_DIR)   # append (lowest priority)

# Prepend HERE so our config wins over premarket_scanner's config
if HERE in sys.path:
    sys.path.remove(HERE)
sys.path.insert(0, HERE)

import config
import signal_engine
import options_ranker
import report_builder as report
import unusualwhales_stub  # noqa (loaded for future use)
import call_flow

# Optional AV news
try:
    import alphavantage_client as av_client
    _AV_OK = True
except Exception:
    av_client = None
    _AV_OK = False

try:
    from zoneinfo import ZoneInfo
    _ET = ZoneInfo("America/New_York")
except Exception:
    _ET = None


OUT = Path(config.OUTPUT_DIR)
OUT.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────────────────────
# HTTP server
# ─────────────────────────────────────────────────────────────
class _Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
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
    threading.Thread(target=srv.serve_forever, daemon=True, name="dt-http").start()
    return rp


# ─────────────────────────────────────────────────────────────
# Time helpers
# ─────────────────────────────────────────────────────────────
def now_et():
    return datetime.now(_ET) if _ET else datetime.now()


def is_in_session(dt=None):
    dt = dt or now_et()
    start = dt.replace(hour=config.START_HOUR_ET, minute=config.START_MIN_ET,
                       second=0, microsecond=0)
    stop  = dt.replace(hour=config.STOP_HOUR_ET, minute=config.STOP_MIN_ET,
                       second=0, microsecond=0)
    return start <= dt < stop


def past_session(dt=None):
    dt = dt or now_et()
    stop = dt.replace(hour=config.STOP_HOUR_ET, minute=config.STOP_MIN_ET,
                      second=0, microsecond=0)
    return dt >= stop


def fmt_time(dt):
    return dt.strftime("%Y-%m-%d %I:%M:%S %p ET")


# ─────────────────────────────────────────────────────────────
# Load premarket picks (candidates)
# ─────────────────────────────────────────────────────────────
def load_premarket_candidates() -> List[Dict]:
    """Read premarket_scanner/output/premarket_picks.json."""
    import json
    p = Path(config.PREMARKET_PICKS_JSON)
    if not p.exists():
        print("  [candidates] premarket_picks.json not found: " + str(p))
        return []
    try:
        raw = json.loads(p.read_text())
        picks = raw.get("picks", [])
        print("  [candidates] " + str(len(picks)) + " premarket picks loaded")
        return picks
    except Exception as e:
        print("  [candidates] failed to load: " + str(e))
        return []


# ─────────────────────────────────────────────────────────────
# Ticker analysis pipeline
# ─────────────────────────────────────────────────────────────
def analyze_and_pick(ticker: str, sentiment: Optional[Dict],
                     is_etf: bool) -> Optional[Dict]:
    """Run signal engine + options ranker for one ticker."""
    sig = signal_engine.analyze(ticker, sentiment)
    if sig is None:
        return None

    contract = None
    if sig["direction"] in ("CALL", "PUT"):
        try:
            contract = options_ranker.pick_best(
                ticker, sig["price"], sig["atr"], sig["direction"], is_etf)
        except Exception as e:
            print("  [rank] " + ticker + " error: " + str(e))
            contract = None
    sig["contract"] = contract
    sig["is_etf"]   = is_etf
    return sig


def _get_sentiment_map(candidates: List[Dict]) -> Dict[str, Dict]:
    """Reuse AV sentiment already fetched by premarket scanner (embedded in picks)."""
    out = {}
    for c in candidates:
        t = c.get("ticker")
        if not t:
            continue
        # premarket_scanner already stores sentiment fields on the pick
        raw = c.get("raw_sentiment", 0.0)
        out[t] = {
            "raw_avg": raw,
            "sentiment_label": c.get("sentiment_label", "Neutral"),
            "sentiment_score": c.get("sentiment_score", 0.5),
        }
    return out


# ─────────────────────────────────────────────────────────────
# Scan
# ─────────────────────────────────────────────────────────────
def run_scan() -> Dict:
    t0 = time.time()
    print("")
    print("[" + now_et().strftime("%H:%M:%S ET") + "] === OPTIONS SCAN ===")

    # 1. ETFs
    etf_picks = []
    for etf in config.ETF_TICKERS:
        r = analyze_and_pick(etf, sentiment=None, is_etf=True)
        if r is None:
            print("  [etf] " + etf + " analysis failed")
            continue
        etf_picks.append(r)
        print("  [etf] " + etf + " " + r["direction"] +
              " conf " + str(r["confidence"]) +
              " price $" + "{:.2f}".format(r["price"]))

    # 2. Premarket candidates
    candidates = load_premarket_candidates()
    sent_map = _get_sentiment_map(candidates)
    tickers = [c["ticker"] for c in candidates
               if c.get("ticker") and c["ticker"] not in config.ETF_TICKERS]

    scored: List[Dict] = []
    if tickers:
        print("  [scan] Analyzing " + str(len(tickers)) + " candidates...")
        with ThreadPoolExecutor(max_workers=config.CONCURRENT_WORKERS) as pool:
            futures = {pool.submit(analyze_and_pick,
                                   t, sent_map.get(t), False): t for t in tickers}
            for fut in as_completed(futures):
                res = fut.result()
                if res is not None:
                    scored.append(res)

    scored.sort(key=lambda p: p["confidence"], reverse=True)

    # Top pick: highest-confidence *tradeable* candidate (with contract)
    top_pick = None
    for p in scored:
        if p["direction"] in ("CALL", "PUT") and p.get("contract"):
            top_pick = p
            break
    # else: fall back to highest confidence overall (may be NO-TRADE)
    if top_pick is None and scored:
        top_pick = scored[0]

    # Watchlist: next 10 (excluding top_pick)
    watchlist = [p for p in scored if p is not top_pick][:10]

    # 3. SPY/QQQ call-side flow (top-bought calls, 1-30 DTE, excludes 0DTE)
    print("  [flow] Analyzing SPY/QQQ call flow (1-30 DTE, excl. 0DTE)...")
    try:
        call_flow_data = call_flow.analyze(
            list(config.ETF_TICKERS), dte_max=30, dte_min=1, top_n=10)
    except Exception as e:
        print("  [flow] error: " + str(e))
        call_flow_data = {}

    elapsed = time.time() - t0
    print("  [scan] complete in " + "{:.1f}".format(elapsed) + "s")

    return {
        "etf_picks": etf_picks,
        "top_pick":  top_pick,
        "watchlist": watchlist,
        "call_flow": call_flow_data,
    }


# ─────────────────────────────────────────────────────────────
# Emit outputs
# ─────────────────────────────────────────────────────────────
def emit(result: Dict, next_scan_dt: Optional[datetime]) -> None:
    now = now_et()
    meta = {
        "now_str":   fmt_time(now),
        "next_scan": next_scan_dt.strftime("%I:%M %p ET") if next_scan_dt else "(none)",
        "session":   {"start": "9:30 AM ET", "stop": "12:00 PM ET"},
        "config": {
            "delta_min":  config.DELTA_MIN,
            "delta_max":  config.DELTA_MAX,
            "min_oi":     config.MIN_OI,
            "min_volume": config.MIN_VOLUME,
            "interval_min": config.INTERVAL_MIN,
        },
    }

    report.render_console(result["etf_picks"], result["top_pick"],
                          result["watchlist"], meta,
                          call_flow=result.get("call_flow"))
    report.write_html(result["etf_picks"], result["top_pick"],
                      result["watchlist"], meta,
                      call_flow=result.get("call_flow"))
    report.write_json({"meta": meta, **result})


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description="Options Day Trader")
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--force", action="store_true",
                    help="Run outside 9:30-12:00 ET session")
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("--interval", type=int, default=config.INTERVAL_MIN)
    ap.add_argument("--port", type=int, default=config.HTTP_PORT)
    args = ap.parse_args()

    port = start_server(args.port)
    url  = "http://127.0.0.1:" + str(port) + "/options_daytrader.html"

    print("=" * 60)
    print("  OPTIONS DAY TRADER")
    print("=" * 60)
    print("  Session       : " +
          "{:02d}:{:02d}".format(config.START_HOUR_ET, config.START_MIN_ET) +
          " AM - " +
          "{:02d}:{:02d}".format(config.STOP_HOUR_ET, config.STOP_MIN_ET) +
          " PM ET")
    print("  Interval      : " + str(args.interval) + " min")
    print("  ETFs          : " + ", ".join(config.ETF_TICKERS))
    print("  Delta target  : " + str(config.DELTA_MIN) + " - " + str(config.DELTA_MAX))
    print("  Report URL    : " + url)
    print("  AV enabled    : " + str(_AV_OK and getattr(av_client, "config", None) is not None
                                     if av_client else False))
    print("=" * 60)

    if not args.no_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    # If past session and not forced/once, do one scan then exit
    if past_session() and not args.force and not args.once:
        print("")
        print("  Past 12:00 PM ET -> running one scan then exiting.")
        result = run_scan()
        emit(result, None)
        print("")
        print("Done. Report: " + url)
        return 0

    # First scan
    result = run_scan()
    next_dt = now_et() + timedelta(minutes=args.interval)
    emit(result, next_dt)

    if args.once:
        print("")
        print("--once: done. Report: " + url)
        return 0

    # Loop until session end
    try:
        while True:
            if past_session(next_dt) and not args.force:
                print("")
                print("  Next scan " + next_dt.strftime("%I:%M %p ET") +
                      " is past 12:00 PM ET -> exiting.")
                break

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

            result = run_scan()
            next_dt = now_et() + timedelta(minutes=args.interval)
            emit(result, next_dt)

    except KeyboardInterrupt:
        print("")
        print("Stopped by user.")
        return 0

    print("")
    print("Final report: " + url)
    return 0


if __name__ == "__main__":
    sys.exit(main())
