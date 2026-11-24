"""
pick.py — DayTrade Picker main entry point.

Usage:  python pick.py
        python pick.py --once        (one scan, then exit)
        python pick.py --no-browser  (don't auto-open browser)
"""
from __future__ import annotations
import sys, os

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import argparse
import functools
import http.server
import logging
import socket
import socketserver
import threading
import time
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import config
import alphavantage as av
import walter_bloomberg as wb
import market_regime
import scorer
import report_builder

logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s: %(message)s")

OUT = Path(config.OUTPUT_DIR)
OUT.mkdir(parents=True, exist_ok=True)

# shared state
_picks: List[Dict] = []
_regime: Dict = {}
_midday_done = [False]
_state_lock = threading.Lock()


# ── HTTP server ───────────────────────────────────────────────
class _Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        self.send_header("Pragma", "no-cache")
        super().end_headers()


def _find_port(p, tries=20):
    for i in range(tries):
        with socket.socket() as s:
            try:
                s.bind(("127.0.0.1", p + i)); return p + i
            except OSError:
                continue
    return p


def start_server(port):
    rp = _find_port(port)
    h  = functools.partial(_Handler, directory=str(OUT))
    srv = socketserver.ThreadingTCPServer(("127.0.0.1", rp), h)
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True, name="http").start()
    return rp


# ── Walter Bloomberg background thread ───────────────────────
def _wb_loop():
    wb.refresh()
    report_builder.write_live_walter(wb.get_headlines(), wb.get_last_fetch_age())
    while True:
        time.sleep(config.WALTER_REFRESH_MIN * 60)
        try:
            wb.refresh()
            report_builder.write_live_walter(wb.get_headlines(), wb.get_last_fetch_age())
        except Exception as e:
            print(f"  [WB] refresh error: {e}")


# ── Scan ──────────────────────────────────────────────────────
def run_scan(session="morning"):
    global _picks, _regime
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] === {session.upper()} SCAN ===")

    # 1. AV top movers (1 call cached 30 min)
    av_data = av.get_top_gainers_losers()
    candidates = scorer.build_candidates(av_data) if av_data else []
    print(f"  Candidates: {len(candidates)}")

    # 2. Market regime via yfinance (free)
    regime = market_regime.fetch_regime()
    print(f"  Regime: {regime.get('label','?')}  VIX {regime.get('vix',0):.1f}")

    # 3. AV sentiment (budget-aware)
    limits = {"morning": 10, "midday": 7, "refresh": 0}
    slimit = min(limits.get(session, 0), max(0, av.remaining_budget() - 1))
    sentiments = {}
    if slimit > 0:
        tickers = [c["ticker"] for c in candidates[:slimit]]
        print(f"  AV sentiment: {len(tickers)} tickers...")
        for t in tickers:
            sentiments[t] = av.get_news_sentiment(t)
    print(f"  {av.get_budget_status()}")

    # 4. Score via yfinance (free)
    print(f"  Scoring {len(candidates)} candidates...")
    picks = []
    bias = regime.get("bias", "choppy")
    for c in candidates:
        t = c["ticker"]
        sent = sentiments.get(t, {"sentiment_score": 0.5, "sentiment_label": "Neutral",
                                   "articles": 0, "top_headlines": []})
        p = scorer.score_ticker(t, sent, bias, av_price=c.get("av_price", 0.0))
        if p:
            p["av_change_pct"] = c.get("av_change_pct", 0.0)
            p["av_source"]     = c.get("source", "")
            picks.append(p)
            if len(picks) >= config.TOP_N_PICKS:
                break

    # Sort: LONG first by bull signals, then SHORT by bear signals
    longs  = sorted([p for p in picks if p["direction"] == "LONG"],
                    key=lambda x: x["bull_signals"], reverse=True)
    shorts = sorted([p for p in picks if p["direction"] == "SHORT"],
                    key=lambda x: x["bear_signals"], reverse=True)
    picks = (longs + shorts)[:config.TOP_N_PICKS]

    with _state_lock:
        _picks[:] = picks
        _regime.clear()
        _regime.update(regime)

    print(f"  {len(picks)} picks: {len(longs)} LONG, {len(shorts)} SHORT")
    return picks, regime


def _build_and_write(next_scan_str):
    with _state_lock:
        picks  = list(_picks)
        regime = dict(_regime)
    wb_items = wb.get_headlines()
    now = datetime.now()
    report_builder.write_report(picks, regime, wb_items, now,
                                 av.get_budget_status(), next_scan_str)
    report_builder.write_live_data(picks, regime, now,
                                    av.get_budget_status(), next_scan_str)
    report_builder.write_live_walter(wb_items, wb.get_last_fetch_age())


def _print_summary(picks, regime):
    now = datetime.now().strftime("%I:%M %p ET")
    print(f"\n{'='*62}")
    print(f"  DAYTRADE PICKS — {now}  |  {regime.get('label','?')}  VIX {regime.get('vix',0):.1f}")
    print(f"{'='*62}")
    if not picks:
        print("  No high-conviction picks this scan.")
    for i, p in enumerate(picks, 1):
        arrow = "▲" if p["direction"] == "LONG" else "▼"
        dir_lbl = f"{arrow} {p['direction']:<5}"
        sigs = "  ".join(p.get("signals", [])[:4])
        print(f"  {i:2}. {p['ticker']:<6} {dir_lbl}  "
              f"${p['entry']:.2f}  stop ${p['stop']:.2f}  tgt ${p['target']:.2f}")
        print(f"      {sigs}")
        if p.get("top_headline"):
            print(f"      \"{p['top_headline'][:80]}\"")
    print(f"\n  {av.get_budget_status()}")
    print(f"  {regime.get('guidance','')}")
    print(f"{'='*62}")
    print("  ⚠  Signals only — not financial advice. Manage your own risk.")
    print(f"{'='*62}\n")


# ── Main ──────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(description="DayTrade Picker")
    p.add_argument("--once",       action="store_true", help="One scan then exit")
    p.add_argument("--no-browser", action="store_true", help="Don't open browser")
    p.add_argument("--interval",   type=int, default=config.REFRESH_INTERVAL)
    p.add_argument("--port",       type=int, default=config.HTTP_PORT)
    args = p.parse_args()

    if not config.AV_ENABLED:
        print("\n" + "!"*60)
        print("  WARNING: No Alpha Vantage API key set!")
        print("  Edit daytrade_picker/config.py and set AV_API_KEY.")
        print("  The scanner will run with yfinance only (no AV data).")
        print("!"*60 + "\n")

    # Start HTTP server
    port = start_server(args.port)
    url  = f"http://127.0.0.1:{port}/report.html"

    print("╔══════════════════════════════════════════════════════════╗")
    print("║            DAYTRADE PICKER — POWERED BY AV + YFINANCE   ║")
    print("╠══════════════════════════════════════════════════════════╣")
    print(f"║  Report URL    : {url}")
    print(f"║  Scan interval : {args.interval} minutes")
    print(f"║  AV key        : {'configured' if config.AV_ENABLED else 'NOT SET — edit config.py'}")
    print(f"║  AV budget     : {config.AV_DAILY_BUDGET} calls/day")
    print(f"║  Walter Bloomberg RSS: every {config.WALTER_REFRESH_MIN} min")
    print("╚══════════════════════════════════════════════════════════╝\n")

    # Start Walter Bloomberg background refresh
    wb_thread = threading.Thread(target=_wb_loop, daemon=True, name="walter-bloomberg")
    wb_thread.start()
    print("→ Walter Bloomberg RSS: started\n")

    # First scan (morning)
    picks, regime = run_scan("morning")
    _print_summary(picks, regime)

    next_scan = (datetime.now().replace(second=0, microsecond=0))
    next_scan_str = next_scan.strftime("%I:%M %p")
    _build_and_write(next_scan_str)
    print(f"  Report: {url}")

    if not args.no_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    if args.once:
        print("\n--once: done.")
        return 0

    # Loop
    interval_sec = args.interval * 60
    scan_count = [1]

    try:
        while True:
            # Count down to next scan
            for remaining in range(interval_sec, 0, -30):
                # Check if it's midday and we haven't done midday scan yet
                hour = datetime.now().hour
                if 11 <= hour < 13 and not _midday_done[0]:
                    _midday_done[0] = True
                    picks, regime = run_scan("midday")
                    _print_summary(picks, regime)
                    ns = datetime.now().strftime("%I:%M %p")
                    _build_and_write(ns)
                m, s = divmod(remaining, 60)
                print(f"  Next scan in {m:02d}:{s:02d}  ", end="\r", flush=True)
                time.sleep(min(30, remaining))

            print()
            scan_count[0] += 1
            # After first morning+midday, subsequent scans are "refresh" (0 AV calls)
            session = "refresh"
            picks, regime = run_scan(session)
            _print_summary(picks, regime)
            ns = datetime.now().strftime("%I:%M %p")
            _build_and_write(ns)

    except KeyboardInterrupt:
        print("\n\nStopping DayTrade Picker. Goodbye.")
        return 0


if __name__ == "__main__":
    sys.exit(main())