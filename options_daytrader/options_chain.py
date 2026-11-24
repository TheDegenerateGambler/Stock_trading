"""
options_chain.py — Options chain fetcher.

Source priority:
  1. CBOE (official free delayed chain, full greeks) — cboe_client.py
  2. yfinance (fallback) — Black-Scholes delta computed manually

Returns per contract:
  {
    contractSymbol, strike, type ('call'/'put'), expiry,
    bid, ask, mid, last, volume, openInterest,
    impliedVolatility, delta, [gamma, theta, vega if CBOE],
    spread_pct, source ('cboe' | 'yfinance')
  }
"""
from __future__ import annotations
from datetime import datetime, date, timedelta
from math import log, sqrt, exp, erf
from typing import Dict, List, Optional
import warnings

import config

warnings.filterwarnings("ignore")


# ─────────────────────────────────────────────────────────────
# Black-Scholes delta (fallback when yfinance doesn't provide it)
# ─────────────────────────────────────────────────────────────
def _norm_cdf(x):
    return 0.5 * (1.0 + erf(x / sqrt(2.0)))


def bs_delta(spot: float, strike: float, t_years: float,
             iv: float, right: str, r: float = None) -> float:
    """Black-Scholes delta. right='c' or 'p'."""
    if r is None:
        r = config.RISK_FREE_RATE
    if t_years <= 0 or iv <= 0 or spot <= 0 or strike <= 0:
        # Very close to expiry — approximate by intrinsic
        if right == "c":
            return 1.0 if spot > strike else 0.0
        else:
            return -1.0 if spot < strike else 0.0
    try:
        d1 = (log(spot / strike) + (r + 0.5 * iv * iv) * t_years) / (iv * sqrt(t_years))
    except Exception:
        return 0.0
    if right == "c":
        return _norm_cdf(d1)
    return _norm_cdf(d1) - 1.0


# ─────────────────────────────────────────────────────────────
# Expiry picker
# ─────────────────────────────────────────────────────────────
def _pick_expiry(available: List[str], mode: str) -> Optional[str]:
    """Pick an expiry string from yfinance's `options` list ('YYYY-MM-DD')."""
    if not available:
        return None
    today = date.today()
    parsed = []
    for e in available:
        try:
            parsed.append((datetime.strptime(e, "%Y-%m-%d").date(), e))
        except Exception:
            continue
    parsed.sort()

    if mode == "0DTE":
        # Look for today's date first
        for d, e in parsed:
            if d == today:
                return e
        # else nearest future
        for d, e in parsed:
            if d >= today:
                return e
    elif mode == "NEXT_FRIDAY":
        # Next Friday (or today if it's Friday)
        days_ahead = (4 - today.weekday()) % 7   # Friday=4
        target = today + timedelta(days=days_ahead)
        # find first expiry >= target
        for d, e in parsed:
            if d >= target:
                return e
    # NEAREST or fallback
    for d, e in parsed:
        if d >= today:
            return e
    return parsed[-1][1] if parsed else None


# ─────────────────────────────────────────────────────────────
# Public: get filtered contracts for direction
# ─────────────────────────────────────────────────────────────
def get_contracts(ticker: str, spot: float, direction: str,
                  is_etf: bool) -> List[Dict]:
    """
    direction: 'CALL' or 'PUT'

    Tries CBOE first (official, has full greeks). Falls back to yfinance
    if CBOE returns nothing.
    """
    if direction not in ("CALL", "PUT"):
        return []

    # ── Primary: CBOE ──
    try:
        import cboe_client
        cboe_rows = cboe_client.get_contracts(ticker, spot, direction, is_etf)
        if cboe_rows:
            return cboe_rows
    except Exception as e:
        print("  [chain] CBOE " + ticker + " error: " + str(e))

    # ── Fallback: yfinance ──
    try:
        import yfinance as yf
        yt = yf.Ticker(ticker)
        expiries = list(yt.options or [])
        if not expiries:
            return []
    except Exception as e:
        print("  [chain] yfinance " + ticker + " options list failed: " + str(e))
        return []

    mode = config.ETF_EXPIRY_MODE if is_etf else config.OTHER_EXPIRY_MODE
    exp_str = _pick_expiry(expiries, mode)
    if not exp_str:
        return []

    try:
        chain = yt.option_chain(exp_str)
    except Exception as e:
        print("  [chain] yfinance " + ticker + " chain(" + exp_str + ") failed: " + str(e))
        return []

    df = chain.calls if direction == "CALL" else chain.puts
    if df is None or df.empty:
        return []

    right = "c" if direction == "CALL" else "p"

    # Time to expiry in years (assume 16:00 ET expiry)
    try:
        exp_date = datetime.strptime(exp_str, "%Y-%m-%d").date()
    except Exception:
        exp_date = date.today()
    days_to = max(0, (exp_date - date.today()).days)
    # if 0DTE, use hours remaining
    if days_to == 0:
        # Assume 4 hours avg remaining; fine for delta approximation
        t_years = max(1.0/365/24, 4.0 / (365.0 * 24.0))
    else:
        t_years = days_to / 365.0

    out = []
    for _, row in df.iterrows():
        try:
            strike = float(row.get("strike", 0))
            bid    = float(row.get("bid", 0) or 0)
            ask    = float(row.get("ask", 0) or 0)
            last   = float(row.get("lastPrice", 0) or 0)
            vol    = int(row.get("volume", 0) or 0)
            oi     = int(row.get("openInterest", 0) or 0)
            iv     = float(row.get("impliedVolatility", 0) or 0)
            mid    = (bid + ask) / 2.0 if (bid > 0 and ask > 0) else (last or 0.0)
            spread_pct = ((ask - bid) / mid) if (mid > 0 and ask > bid) else 1.0

            # Delta: yfinance chains rarely include greeks; compute via BS
            delta_val = bs_delta(spot, strike, t_years, iv if iv > 0 else 0.25, right)

            out.append({
                "contractSymbol":    str(row.get("contractSymbol", "")),
                "strike":            round(strike, 2),
                "type":              "call" if right == "c" else "put",
                "expiry":            exp_str,
                "days_to_expiry":    days_to,
                "bid":               round(bid, 2),
                "ask":               round(ask, 2),
                "mid":               round(mid, 2),
                "last":              round(last, 2),
                "volume":            vol,
                "openInterest":      oi,
                "impliedVolatility": round(iv, 4),
                "delta":             round(delta_val, 3),
                "spread_pct":        round(spread_pct, 4),
            })
        except Exception:
            continue

    return out


def filter_liquid(contracts: List[Dict]) -> List[Dict]:
    """Apply liquidity + delta filters from config."""
    out = []
    for c in contracts:
        if c["openInterest"] < config.MIN_OI:
            continue
        if c["volume"] < config.MIN_VOLUME:
            continue
        if c["spread_pct"] > config.MAX_SPREAD_PCT:
            continue
        if c["mid"] <= 0:
            continue
        d = abs(c["delta"])
        if d < config.DELTA_MIN or d > config.DELTA_MAX:
            continue
        out.append(c)
    return out