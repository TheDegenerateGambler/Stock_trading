"""
One-click orchestrator: runs every wheel scanner and builds ONE mega HTML dashboard.

Sections produced (in order):
  1. Monthly CSPs on cheap TSX names (default watchlist, <= $10 CAD)
  2. Monthly buy-write CCs on same names
  3. Weekly CSPs on liquid US names (Ford, SOFI, INTC, etc.)
  4. Weekly CSPs on TSX blue-chips (RY, BNS, ENB, etc.)
  5. Weekly buy-write CCs on US names
  6. (optional) CCs on your existing positions from my_positions.json

Also builds a "Top 10 Overall" combined leaderboard sorted by score across all
sections.

Errors in any one section are caught and displayed as a banner — other sections
still run.

Usage:
    python run_all.py
"""
from __future__ import annotations

import json
import os
import sys
import traceback
from dataclasses import asdict
from datetime import datetime
from typing import Any

from cc_analyzer import CCCandidate, find_best_call_across_expirations, score_cc_candidates
from config import (
    ACCOUNT_BUDGET_CAD,
    CANADIAN_WHEEL_WATCHLIST,
    CC_BUY_WRITE_ENFORCE_BUDGET,
    CONTRACT_SIZE,
    DEFAULT_USD_CAD,
    MAX_STOCK_PRICE_CAD,
    MIN_STOCK_PRICE_CAD,
    OUTPUT_DIR,
    WEEKLY_TSX_WATCHLIST,
    WEEKLY_US_WATCHLIST,
)
from data_provider import get_stock_snapshot, polite_sleep
from wheel_analyzer import (
    WheelCandidate,
    find_best_put_across_expirations,
    score_candidates,
)


# ---------------------------------------------------------------------------
# Section runners
# Each returns (title, ranked_list, error_str_or_None)
# ---------------------------------------------------------------------------
def _scan_put_section(
    title: str,
    tickers: list[str],
    weekly: bool,
    max_price_native: float,
    usd_cad: float,
) -> tuple[str, list[WheelCandidate], str | None]:
    print(f"\n{'='*74}\n>> {title}\n{'='*74}")
    try:
        cands: list[WheelCandidate] = []
        for i, ticker in enumerate(tickers, 1):
            print(f"  [{i}/{len(tickers)}] {ticker}", flush=True)
            snap = get_stock_snapshot(ticker)
            polite_sleep(0.3)
            if snap is None:
                continue
            cur = (snap.currency or "CAD").upper()
            if cur == "USD":
                budget_native = ACCOUNT_BUDGET_CAD / usd_cad
            elif cur == "CAD":
                budget_native = ACCOUNT_BUDGET_CAD
            else:
                continue
            effective_max = min(max_price_native, budget_native / CONTRACT_SIZE)
            if snap.price > effective_max or snap.price < MIN_STOCK_PRICE_CAD:
                continue
            cand = find_best_put_across_expirations(
                snap, weekly=weekly, budget=ACCOUNT_BUDGET_CAD, usd_cad=usd_cad
            )
            if cand:
                cands.append(cand)
        ranked = score_candidates(cands) if cands else []
        return title, ranked, None
    except Exception as e:
        traceback.print_exc()
        return title, [], f"{type(e).__name__}: {e}"


def _scan_cc_section(
    title: str,
    tickers: list[str] | None,
    positions: list[tuple[str, float, int]] | None,
    weekly: bool,
    max_price_native: float,
    usd_cad: float,
) -> tuple[str, list[CCCandidate], str | None]:
    print(f"\n{'='*74}\n>> {title}\n{'='*74}")
    try:
        cands: list[CCCandidate] = []

        if positions:
            for i, (ticker, cost, shares) in enumerate(positions, 1):
                print(f"  [{i}/{len(positions)}] {ticker} (basis ${cost:.2f})", flush=True)
                snap = get_stock_snapshot(ticker)
                polite_sleep(0.3)
                if snap is None:
                    continue
                cand = find_best_call_across_expirations(
                    snap, cost_basis=cost, shares_held=shares, mode="position",
                    weekly=weekly, usd_cad=usd_cad,
                )
                if cand:
                    cands.append(cand)

        if tickers:
            for i, ticker in enumerate(tickers, 1):
                print(f"  [{i}/{len(tickers)}] {ticker}", flush=True)
                snap = get_stock_snapshot(ticker)
                polite_sleep(0.3)
                if snap is None:
                    continue
                cur = (snap.currency or "CAD").upper()
                if cur == "USD":
                    budget_native = ACCOUNT_BUDGET_CAD / usd_cad
                elif cur == "CAD":
                    budget_native = ACCOUNT_BUDGET_CAD
                else:
                    continue
                enforce = CC_BUY_WRITE_ENFORCE_BUDGET
                effective_max = min(max_price_native, budget_native / CONTRACT_SIZE) if enforce else max_price_native
                if snap.price > effective_max or snap.price < MIN_STOCK_PRICE_CAD:
                    continue
                cand = find_best_call_across_expirations(
                    snap, cost_basis=None, shares_held=100, mode="buy-write",
                    weekly=weekly, usd_cad=usd_cad,
                )
                if cand:
                    cands.append(cand)

        ranked = score_cc_candidates(cands) if cands else []
        return title, ranked, None
    except Exception as e:
        traceback.print_exc()
        return title, [], f"{type(e).__name__}: {e}"


# ---------------------------------------------------------------------------
# Positions file (optional)
# ---------------------------------------------------------------------------
def load_positions_file() -> list[tuple[str, float, int]]:
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "my_positions.json")
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        out = []
        for p in data:
            out.append((
                str(p["ticker"]).upper(),
                float(p["cost_basis"]),
                int(p.get("shares", 100)),
            ))
        return out
    except Exception as e:
        print(f"  [warn] failed to read my_positions.json: {e}")
        return []


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    usd_cad = DEFAULT_USD_CAD
    started = datetime.now()

    print(f"\n>>> Running the WHEEL — one-click, all sections")
    print(f"    Budget: ${ACCOUNT_BUDGET_CAD:,.2f} CAD    FX: {usd_cad} USD/CAD")

    sections_puts: list[tuple[str, list[WheelCandidate], str | None]] = []
    sections_calls: list[tuple[str, list[CCCandidate], str | None]] = []

    # -- Section 1: Monthly CSPs, cheap TSX
    sections_puts.append(_scan_put_section(
        title="🇨🇦 Monthly Puts — Cheap TSX (≤ $10 CAD)",
        tickers=CANADIAN_WHEEL_WATCHLIST,
        weekly=False,
        max_price_native=MAX_STOCK_PRICE_CAD,
        usd_cad=usd_cad,
    ))

    # -- Section 2: Monthly buy-write CCs, cheap TSX
    sections_calls.append(_scan_cc_section(
        title="🇨🇦 Monthly Covered Calls — Cheap TSX (buy-write)",
        tickers=CANADIAN_WHEEL_WATCHLIST,
        positions=None,
        weekly=False,
        max_price_native=MAX_STOCK_PRICE_CAD,
        usd_cad=usd_cad,
    ))

    # -- Section 3: Weekly CSPs, US names
    sections_puts.append(_scan_put_section(
        title="🇺🇸 Weekly Puts — Liquid US names (Ford, SOFI, INTC, etc.)",
        tickers=WEEKLY_US_WATCHLIST,
        weekly=True,
        max_price_native=1e9,   # budget-bound only
        usd_cad=usd_cad,
    ))

    # -- Section 4: Weekly CSPs, TSX blue-chips
    sections_puts.append(_scan_put_section(
        title="🇨🇦 Weekly Puts — TSX blue-chips (RY, BNS, ENB, etc.)",
        tickers=WEEKLY_TSX_WATCHLIST,
        weekly=True,
        max_price_native=1e9,
        usd_cad=usd_cad,
    ))

    # -- Section 5: Weekly buy-write CCs, US names
    sections_calls.append(_scan_cc_section(
        title="🇺🇸 Weekly Covered Calls — Liquid US names (buy-write)",
        tickers=WEEKLY_US_WATCHLIST,
        positions=None,
        weekly=True,
        max_price_native=1e9,
        usd_cad=usd_cad,
    ))

    # -- Section 6 (optional): CCs on user positions
    positions = load_positions_file()
    if positions:
        sections_calls.append(_scan_cc_section(
            title="📂 Covered Calls — Your Positions (from my_positions.json)",
            tickers=None,
            positions=positions,
            weekly=False,   # try monthly first; user can create a weekly file variant later
            max_price_native=1e9,
            usd_cad=usd_cad,
        ))

    # -- Build the mega dashboard
    from mega_dashboard import build_mega_dashboard
    finished = datetime.now()
    out_path = build_mega_dashboard(
        put_sections=sections_puts,
        cc_sections=sections_calls,
        started=started,
        finished=finished,
        budget_cad=ACCOUNT_BUDGET_CAD,
        usd_cad=usd_cad,
    )
    print(f"\n>>> Mega dashboard: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())