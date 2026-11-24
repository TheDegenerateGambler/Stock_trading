"""
cboe_client.py — Official CBOE delayed options chain (free, 15-min delay).

Endpoint (public, no auth):
  https://cdn.cboe.com/api/global/delayed_quotes/options/{SYMBOL}.json

Returns:
  {
    'data': {
      'current_price': ..., 'bid': ..., 'ask': ...,
      'options': [ { 'option': 'SPY260710C00450000',
                     'bid', 'ask', 'iv', 'open_interest', 'volume',
                     'delta', 'gamma', 'vega', 'theta', 'rho',
                     'theo', 'last_trade_price', ... }, ... ]
    }
  }

Advantage over yfinance:
  - Native greeks (Δ Γ Θ ν ρ) — no Black-Scholes computation needed.
  - Full chain in ONE request (yfinance = one per expiry).
  - Official public JSON — no scraping / TOS issues.
"""
from __future__ import annotations
import json
import re
import time
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import requests

import config

_CACHE_DIR = Path(config.OUTPUT_DIR) / "cboe_cache"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)

_BASE_URL = "https://cdn.cboe.com/api/global/delayed_quotes/options/{sym}.json"
_HEADERS  = {"User-Agent": "Mozilla/5.0 (compatible; options-daytrader/1.0)"}

# OCC symbol parser: TICKERyymmdd[CP]strike*1000 (padded to 8)
_OCC_RE = re.compile(r"^([A-Z]+)(\d{2})(\d{2})(\d{2})([CP])(\d{8})$")

# Cache: 30-second TTL (data is 15-min delayed anyway; heavy caching is fine)
_TTL_SECONDS = 30


def _cache_path(sym: str) -> Path:
    return _CACHE_DIR / (sym.upper() + ".json")


def _load_cache(sym: str) -> Optional[Dict]:
    p = _cache_path(sym)
    if not p.exists():
        return None
    try:
        raw = json.loads(p.read_text())
        if time.time() - raw.get("_ts", 0) < _TTL_SECONDS:
            return raw.get("data")
    except Exception:
        pass
    return None


def _save_cache(sym: str, data: Dict) -> None:
    try:
        _cache_path(sym).write_text(json.dumps({"_ts": time.time(), "data": data}))
    except Exception:
        pass


def _parse_occ(occ: str) -> Optional[Dict]:
    """Parse an OCC option symbol into components."""
    m = _OCC_RE.match(occ)
    if not m:
        return None
    ticker, yy, mm, dd, right, strike_raw = m.groups()
    try:
        year = 2000 + int(yy)
        exp = date(year, int(mm), int(dd))
        strike = int(strike_raw) / 1000.0
        return {
            "ticker": ticker,
            "expiry": exp.strftime("%Y-%m-%d"),
            "expiry_date": exp,
            "right":  right,          # 'C' or 'P'
            "strike": strike,
        }
    except Exception:
        return None


def fetch_raw(symbol: str) -> Optional[Dict]:
    """Fetch (or return cached) full CBOE payload for a symbol."""
    cached = _load_cache(symbol)
    if cached is not None:
        return cached
    try:
        r = requests.get(_BASE_URL.format(sym=symbol.upper()),
                         headers=_HEADERS, timeout=15)
        if r.status_code != 200:
            print("  [cboe] " + symbol + " HTTP " + str(r.status_code))
            return None
        data = r.json()
        if not data or "data" not in data:
            return None
        _save_cache(symbol, data)
        return data
    except Exception as e:
        print("  [cboe] " + symbol + " fetch error: " + str(e))
        return None


def get_spot(symbol: str) -> Optional[float]:
    """Return CBOE's current_price for the underlying."""
    payload = fetch_raw(symbol)
    if not payload:
        return None
    try:
        return float(payload["data"].get("current_price", 0)) or None
    except Exception:
        return None


def _pick_expiry(available: List[date], mode: str) -> Optional[date]:
    if not available:
        return None
    available = sorted(set(available))
    today = date.today()

    if mode == "0DTE":
        for d in available:
            if d == today:
                return d
        for d in available:
            if d >= today:
                return d
    elif mode == "NEXT_FRIDAY":
        days_ahead = (4 - today.weekday()) % 7   # Friday=4
        target = today + timedelta(days=days_ahead)
        for d in available:
            if d >= target:
                return d
    for d in available:
        if d >= today:
            return d
    return available[-1] if available else None


def get_contracts(ticker: str, spot: float, direction: str,
                  is_etf: bool) -> List[Dict]:
    """
    Return contract dicts in the same shape as options_chain.get_contracts()
    so it's a drop-in replacement.
    """
    if direction not in ("CALL", "PUT"):
        return []

    payload = fetch_raw(ticker)
    if not payload:
        return []

    opts = payload["data"].get("options", []) or []
    if not opts:
        return []

    right_wanted = "C" if direction == "CALL" else "P"

    # Bucket by expiry
    by_exp: Dict[date, List[Dict]] = {}
    for o in opts:
        occ = o.get("option", "")
        parsed = _parse_occ(occ)
        if not parsed:
            continue
        if parsed["right"] != right_wanted:
            continue
        by_exp.setdefault(parsed["expiry_date"], []).append((o, parsed))

    mode = config.ETF_EXPIRY_MODE if is_etf else config.OTHER_EXPIRY_MODE
    exp_date = _pick_expiry(list(by_exp.keys()), mode)
    if exp_date is None:
        return []

    exp_str = exp_date.strftime("%Y-%m-%d")
    days_to = max(0, (exp_date - date.today()).days)

    out = []
    for o, parsed in by_exp[exp_date]:
        try:
            bid = float(o.get("bid", 0) or 0)
            ask = float(o.get("ask", 0) or 0)
            last = float(o.get("last_trade_price", 0) or 0)
            mid  = (bid + ask) / 2.0 if (bid > 0 and ask > 0) else (last or 0.0)
            spread_pct = ((ask - bid) / mid) if (mid > 0 and ask > bid) else 1.0
            delta = float(o.get("delta", 0) or 0)
            # CBOE returns positive delta for puts too; normalize
            if right_wanted == "P" and delta > 0:
                delta = -delta

            out.append({
                "contractSymbol":    o.get("option", ""),
                "strike":            round(parsed["strike"], 2),
                "type":              "call" if right_wanted == "C" else "put",
                "expiry":            exp_str,
                "days_to_expiry":    days_to,
                "bid":               round(bid, 2),
                "ask":               round(ask, 2),
                "mid":               round(mid, 2),
                "last":              round(last, 2),
                "volume":            int(o.get("volume", 0) or 0),
                "openInterest":      int(o.get("open_interest", 0) or 0),
                "impliedVolatility": round(float(o.get("iv", 0) or 0), 4),
                "delta":             round(delta, 3),
                "gamma":             round(float(o.get("gamma", 0) or 0), 4),
                "theta":             round(float(o.get("theta", 0) or 0), 4),
                "vega":              round(float(o.get("vega", 0) or 0), 4),
                "spread_pct":        round(spread_pct, 4),
                "source":            "cboe",
            })
        except Exception:
            continue

    return out