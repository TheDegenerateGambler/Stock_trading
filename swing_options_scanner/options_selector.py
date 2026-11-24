"""
options_selector.py — Pick the best swing options contract for a ticker.

Uses ../options_daytrader/cboe_client.py as primary data source (free,
delayed 15 min, native greeks). Falls back to yfinance chain if CBOE fails.

Filters:
  - Expiration: 21–45 DTE (swing window)
  - Delta: 0.30–0.50 (magnitude; sign preserved for puts)
  - OI >= MIN_OI, volume >= MIN_VOLUME
  - Bid/ask spread <= MAX_SPREAD_PCT of mid
  - Contract mid × 100 <= MAX_CONTRACT_COST (budget fit)

Scoring within valid contracts:
  budget-fit + delta proximity to 0.40 + liquidity + spread tightness
"""
from __future__ import annotations
import re
import sys
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

import requests

import config

# NOTE: We deliberately do NOT sys.path.insert options_daytrader's directory
# because it contains a module named `report_builder` that would shadow ours.
# We re-implement CBOE fetch locally below (small, self-contained).
_HAS_CBOE = True


_OCC_RE = re.compile(r"^([A-Z]+)(\d{2})(\d{2})(\d{2})([CP])(\d{8})$")
_CBOE_URL = "https://cdn.cboe.com/api/global/delayed_quotes/options/{sym}.json"
_HEADERS = {"User-Agent": "Mozilla/5.0 (swing_options_scanner/1.0)"}


# ─────────────────────────────────────────────────────────────
# Local CBOE fetch (independent — no shared cache dir issues)
# ─────────────────────────────────────────────────────────────
def _fetch_cboe(symbol: str) -> Optional[Dict]:
    try:
        r = requests.get(_CBOE_URL.format(sym=symbol.upper()),
                         headers=_HEADERS, timeout=15)
        if r.status_code != 200:
            return None
        data = r.json()
        return data if data and "data" in data else None
    except Exception:
        return None


def _parse_occ(occ: str) -> Optional[Dict]:
    m = _OCC_RE.match(occ)
    if not m:
        return None
    ticker, yy, mm, dd, right, strike_raw = m.groups()
    try:
        exp = date(2000 + int(yy), int(mm), int(dd))
        return {
            "ticker": ticker,
            "expiry_date": exp,
            "right":  right,
            "strike": int(strike_raw) / 1000.0,
        }
    except Exception:
        return None


def _get_contracts_cboe(ticker: str, direction: str) -> List[Dict]:
    payload = _fetch_cboe(ticker)
    if not payload:
        return []
    opts = payload["data"].get("options", []) or []
    right_wanted = "C" if direction == "CALL" else "P"
    today = date.today()

    out = []
    for o in opts:
        occ = o.get("option", "")
        parsed = _parse_occ(occ)
        if not parsed or parsed["right"] != right_wanted:
            continue
        exp_date = parsed["expiry_date"]
        dte = (exp_date - today).days
        if dte < config.DTE_MIN or dte > config.DTE_MAX:
            continue

        try:
            bid = float(o.get("bid", 0) or 0)
            ask = float(o.get("ask", 0) or 0)
            last = float(o.get("last_trade_price", 0) or 0)
            mid = (bid + ask) / 2.0 if (bid > 0 and ask > 0) else (last or 0.0)
            if mid <= 0:
                continue
            spread_pct = ((ask - bid) / mid) if (mid > 0 and ask > bid) else 1.0
            delta = float(o.get("delta", 0) or 0)
            if right_wanted == "P" and delta > 0:
                delta = -delta

            out.append({
                "contractSymbol": occ,
                "ticker":         parsed["ticker"],
                "strike":         round(parsed["strike"], 2),
                "type":           "call" if right_wanted == "C" else "put",
                "expiry":         exp_date.strftime("%Y-%m-%d"),
                "days_to_expiry": dte,
                "bid":            round(bid, 2),
                "ask":            round(ask, 2),
                "mid":            round(mid, 2),
                "last":           round(last, 2),
                "cost_per_ct":    round(mid * 100, 2),
                "volume":         int(o.get("volume", 0) or 0),
                "openInterest":   int(o.get("open_interest", 0) or 0),
                "impliedVolatility": round(float(o.get("iv", 0) or 0), 4),
                "delta":          round(delta, 3),
                "gamma":          round(float(o.get("gamma", 0) or 0), 4),
                "theta":          round(float(o.get("theta", 0) or 0), 4),
                "vega":           round(float(o.get("vega", 0) or 0), 4),
                "spread_pct":     round(spread_pct, 4),
                "source":         "cboe",
            })
        except Exception:
            continue
    return out


# ─────────────────────────────────────────────────────────────
# yfinance fallback (no greeks — approximate via Black-Scholes)
# ─────────────────────────────────────────────────────────────
def _bs_delta(spot: float, strike: float, dte: int, iv: float,
              right: str) -> float:
    """Simple Black-Scholes delta approximation."""
    import math
    if dte <= 0 or iv <= 0 or spot <= 0 or strike <= 0:
        return 0.0
    T = dte / 365.0
    r = config.RISK_FREE_RATE
    try:
        d1 = (math.log(spot / strike) + (r + 0.5 * iv * iv) * T) / (iv * math.sqrt(T))
        # Standard normal CDF
        cdf = 0.5 * (1 + math.erf(d1 / math.sqrt(2)))
        return cdf if right == "C" else (cdf - 1)
    except Exception:
        return 0.0


def _get_contracts_yf(ticker: str, spot: float, direction: str) -> List[Dict]:
    try:
        import yfinance as yf
        t = yf.Ticker(ticker)
        expiries = t.options or []
    except Exception:
        return []

    today = date.today()
    right_wanted = "C" if direction == "CALL" else "P"
    out = []

    for exp_str in expiries:
        try:
            exp = datetime.strptime(exp_str, "%Y-%m-%d").date()
        except Exception:
            continue
        dte = (exp - today).days
        if dte < config.DTE_MIN or dte > config.DTE_MAX:
            continue

        try:
            chain = t.option_chain(exp_str)
            df = chain.calls if direction == "CALL" else chain.puts
        except Exception:
            continue
        if df is None or df.empty:
            continue

        for _, row in df.iterrows():
            try:
                bid = float(row.get("bid", 0) or 0)
                ask = float(row.get("ask", 0) or 0)
                last = float(row.get("lastPrice", 0) or 0)
                mid = (bid + ask) / 2.0 if (bid > 0 and ask > 0) else (last or 0.0)
                if mid <= 0:
                    continue
                strike = float(row.get("strike", 0))
                iv = float(row.get("impliedVolatility", 0) or 0)
                spread_pct = ((ask - bid) / mid) if (mid > 0 and ask > bid) else 1.0
                delta = _bs_delta(spot, strike, dte, iv, right_wanted)

                out.append({
                    "contractSymbol": row.get("contractSymbol", ""),
                    "ticker":         ticker,
                    "strike":         round(strike, 2),
                    "type":           "call" if right_wanted == "C" else "put",
                    "expiry":         exp_str,
                    "days_to_expiry": dte,
                    "bid":            round(bid, 2),
                    "ask":            round(ask, 2),
                    "mid":            round(mid, 2),
                    "last":           round(last, 2),
                    "cost_per_ct":    round(mid * 100, 2),
                    "volume":         int(row.get("volume", 0) or 0),
                    "openInterest":   int(row.get("openInterest", 0) or 0),
                    "impliedVolatility": round(iv, 4),
                    "delta":          round(delta, 3),
                    "gamma":          0.0,
                    "theta":          0.0,
                    "vega":           0.0,
                    "spread_pct":     round(spread_pct, 4),
                    "source":         "yfinance",
                })
            except Exception:
                continue
    return out


# ─────────────────────────────────────────────────────────────
# Filter + score
# ─────────────────────────────────────────────────────────────
def _filter_valid(contracts: List[Dict]) -> List[Dict]:
    valid = []
    for c in contracts:
        d = abs(c["delta"])
        if d < config.DELTA_MIN or d > config.DELTA_MAX:
            continue
        if c["openInterest"] < config.MIN_OI:
            continue
        if c["volume"] < config.MIN_VOLUME:
            continue
        if c["spread_pct"] > config.MAX_SPREAD_PCT:
            continue
        if c["cost_per_ct"] > config.MAX_CONTRACT_COST:
            continue
        valid.append(c)
    return valid


def _score_contract(c: Dict) -> float:
    """0..1 composite for options-side ranking."""
    d = abs(c["delta"])
    target_delta = 0.40
    delta_fit = 1.0 - min(1.0, abs(d - target_delta) / 0.20)

    liq = min(1.0, c["openInterest"] / 5000.0)
    spread_fit = max(0.0, 1.0 - c["spread_pct"] / config.MAX_SPREAD_PCT)

    # Prefer cheaper (more upside per $)
    budget_fit = max(0.0, 1.0 - c["cost_per_ct"] / config.MAX_CONTRACT_COST)

    return (delta_fit * 0.35 + liq * 0.25 +
            spread_fit * 0.20 + budget_fit * 0.20)


def pick_best_contract(ticker: str, spot: float,
                       direction: str) -> Optional[Dict]:
    """
    Return the best contract for `ticker` in `direction` (CALL|PUT).
    None if no valid contract fits budget/liquidity constraints.
    """
    if direction not in ("CALL", "PUT"):
        return None

    # Try CBOE first (has native greeks, faster, 1 request)
    contracts = _get_contracts_cboe(ticker, direction)
    if not contracts:
        contracts = _get_contracts_yf(ticker, spot, direction)
    if not contracts:
        return None

    valid = _filter_valid(contracts)
    if not valid:
        return None

    valid.sort(key=_score_contract, reverse=True)
    winner = dict(valid[0])
    raw_score = _score_contract(winner)
    winner["options_score_raw"] = round(raw_score, 3)

    # ── Options-side score components for composite ──
    # Split raw 0..1 score into liquidity and budget_fit portions
    liq_w        = config.SCORE_WEIGHTS["liquidity"]
    budget_w     = config.SCORE_WEIGHTS["budget_fit"]

    liq = min(1.0, winner["openInterest"] / 5000.0)
    spread_fit = max(0.0, 1.0 - winner["spread_pct"] / config.MAX_SPREAD_PCT)
    budget_fit = max(0.0, 1.0 - winner["cost_per_ct"] / config.MAX_CONTRACT_COST)

    winner["score_liquidity"] = round(liq_w * (0.6 * liq + 0.4 * spread_fit), 1)
    winner["score_budget_fit"] = round(budget_w * budget_fit, 1)

    return winner


if __name__ == "__main__":
    # Manual smoke test
    for t, s, d in [("AMD", 150.0, "CALL"), ("F", 12.0, "CALL")]:
        c = pick_best_contract(t, s, d)
        if c:
            print(f"{t} {d}: {c['contractSymbol']}  strike=${c['strike']}  "
                  f"mid=${c['mid']}  cost=${c['cost_per_ct']}  Δ={c['delta']}  "
                  f"dte={c['days_to_expiry']}  src={c['source']}")
        else:
            print(f"{t} {d}: no valid contract")
