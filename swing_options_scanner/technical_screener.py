"""
technical_screener.py — Daily-timeframe technical screener for swing trades.

For each ticker:
  - Pull ~90 daily bars via yfinance
  - Compute: price, avg_volume, 20/50 EMA, RSI(14), MACD, ATR(14), RVOL
  - Determine direction bias (BULLISH / BEARISH / NEUTRAL)
  - Score trend (0-30), momentum (0-20), volume (0-15)

Reuses indicator math from ../daytrade_picker/indicators.py by importing it
via sys.path insertion.
"""
from __future__ import annotations
import os
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple

import config

# Note: We don't sys.path.insert daytrade_picker's dir because it contains
# a `config.py` and `report_builder.py` that would shadow ours. We just
# inline the indicator math below (it's pure-Python, small).

def _fallback_calc_rsi(closes, period=14):
    if len(closes) < period + 1:
        return 50.0
    gains, losses = [], []
    for i in range(1, len(closes)):
        d = closes[i] - closes[i - 1]
        gains.append(max(d, 0.0))
        losses.append(max(-d, 0.0))
    avg_g = sum(gains[-period:]) / period
    avg_l = sum(losses[-period:]) / period
    if avg_l == 0:
        return 100.0
    rs = avg_g / avg_l
    return round(100 - (100 / (1 + rs)), 1)

def _fallback_calc_ema(values, period):
    if not values:
        return []
    k = 2.0 / (period + 1)
    result = [values[0]]
    for v in values[1:]:
        result.append(v * k + result[-1] * (1 - k))
    return result

def _fallback_calc_macd(closes, fast=12, slow=26, signal=9):
    if len(closes) < slow + signal:
        return 0.0, 0.0, 0.0
    ef = _fallback_calc_ema(closes, fast)
    es = _fallback_calc_ema(closes, slow)
    m = [f - s for f, s in zip(ef, es)]
    sig = _fallback_calc_ema(m, signal)
    return round(m[-1], 4), round(sig[-1], 4), round(m[-1] - sig[-1], 4)

def _fallback_calc_atr(highs, lows, closes, period=14):
    if len(highs) < 2:
        return 0.0
    trs = []
    for i in range(1, len(highs)):
        trs.append(max(highs[i] - lows[i],
                       abs(highs[i] - closes[i - 1]),
                       abs(lows[i] - closes[i - 1])))
    w = trs[-period:] if len(trs) >= period else trs
    return round(sum(w) / len(w), 4) if w else 0.0

calc_rsi  = _fallback_calc_rsi
calc_ema  = _fallback_calc_ema
calc_macd = _fallback_calc_macd
calc_atr  = _fallback_calc_atr

# Best-effort: try to load daytrade_picker's implementations via a scoped
# import so we don't pollute sys.path. If it fails, we've already got working
# fallbacks above.
try:
    import importlib.util
    _ind_path = os.path.join(config.DAYTRADE_PICKER_DIR, "indicators.py")
    if os.path.isfile(_ind_path):
        _spec = importlib.util.spec_from_file_location("_dp_indicators", _ind_path)
        _mod = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_mod)
        calc_rsi  = getattr(_mod, "calc_rsi", calc_rsi)
        calc_ema  = getattr(_mod, "calc_ema", calc_ema)
        calc_macd = getattr(_mod, "calc_macd", calc_macd)
        calc_atr  = getattr(_mod, "calc_atr", calc_atr)
except Exception:
    pass


def _unused_placeholder_start():
    """placeholder marker — original inline fallbacks below are unused."""
    def calc_rsi(closes, period=14):
        if len(closes) < period + 1:
            return 50.0
        gains, losses = [], []
        for i in range(1, len(closes)):
            d = closes[i] - closes[i - 1]
            gains.append(max(d, 0.0))
            losses.append(max(-d, 0.0))
        avg_g = sum(gains[-period:]) / period
        avg_l = sum(losses[-period:]) / period
        if avg_l == 0:
            return 100.0
        rs = avg_g / avg_l
        return round(100 - (100 / (1 + rs)), 1)

    def calc_ema(values, period):
        if not values:
            return []
        k = 2.0 / (period + 1)
        result = [values[0]]
        for v in values[1:]:
            result.append(v * k + result[-1] * (1 - k))
        return result

    def calc_macd(closes, fast=12, slow=26, signal=9):
        if len(closes) < slow + signal:
            return 0.0, 0.0, 0.0
        ef = calc_ema(closes, fast)
        es = calc_ema(closes, slow)
        m = [f - s for f, s in zip(ef, es)]
        sig = calc_ema(m, signal)
        return round(m[-1], 4), round(sig[-1], 4), round(m[-1] - sig[-1], 4)

    def calc_atr(highs, lows, closes, period=14):
        if len(highs) < 2:
            return 0.0
        trs = []
        for i in range(1, len(highs)):
            trs.append(max(highs[i] - lows[i],
                           abs(highs[i] - closes[i - 1]),
                           abs(lows[i] - closes[i - 1])))
        w = trs[-period:] if len(trs) >= period else trs
        return round(sum(w) / len(w), 4) if w else 0.0


def _fetch_daily_bars(ticker: str, period: str = "6mo") -> Optional[Dict]:
    """
    Return dict of lists: open, high, low, close, volume (daily bars).

    Uses yf.Ticker(...).history() which is per-instance and thread-safe,
    unlike yf.download() which can cross-contaminate results in worker threads.
    """
    try:
        import yfinance as yf
        import numpy as np
        t = yf.Ticker(ticker)
        df = t.history(period=period, interval="1d",
                       auto_adjust=False, actions=False)
        if df is None or df.empty or len(df) < 50:
            return None

        # Newer yfinance sometimes returns MultiIndex columns even from
        # Ticker.history(); flatten defensively.
        if hasattr(df.columns, "nlevels") and df.columns.nlevels > 1:
            try:
                df.columns = df.columns.droplevel(1)
            except Exception:
                df.columns = df.columns.get_level_values(0)

        def _col(name):
            """Extract a column as a flat list of floats, tolerating dupes."""
            if name not in df.columns:
                return []
            col = df[name]
            if hasattr(col, "columns"):
                col = col.iloc[:, 0]
            arr = np.asarray(col, dtype=float).flatten()
            return [float(x) for x in arr if not np.isnan(x)]

        return {
            "open":   _col("Open"),
            "high":   _col("High"),
            "low":    _col("Low"),
            "close":  _col("Close"),
            "volume": _col("Volume"),
        }
    except Exception as e:
        print(f"  [tech] {ticker}: yfinance fetch failed ({e})")
        return None


def analyze(ticker: str) -> Optional[Dict]:
    """
    Return a dict of technical metrics + direction + component scores.
    None if data unavailable or fails universe price/volume filter.
    """
    bars = _fetch_daily_bars(ticker)
    if not bars:
        return None

    closes  = bars["close"]
    highs   = bars["high"]
    lows    = bars["low"]
    volumes = bars["volume"]

    if not closes or not volumes:
        return None

    price = closes[-1]
    avg_vol = sum(volumes[-20:]) / min(20, len(volumes))

    # ── Universe hard filters ──
    if price < config.PRICE_MIN or price > config.PRICE_MAX:
        return None
    if avg_vol < config.MIN_AVG_VOLUME:
        return None

    # ── Indicators ──
    ema20_series = calc_ema(closes, 20)
    ema50_series = calc_ema(closes, 50)
    ema20 = ema20_series[-1] if ema20_series else price
    ema50 = ema50_series[-1] if ema50_series else price

    rsi = calc_rsi(closes, 14)
    macd_line, macd_sig, macd_hist = calc_macd(closes)
    atr = calc_atr(highs, lows, closes, 14)

    today_vol = volumes[-1] if volumes else 0.0
    rvol = (today_vol / avg_vol) if avg_vol > 0 else 1.0

    # ── Direction bias ──
    bullish_signals = 0
    bearish_signals = 0

    if price > ema20:  bullish_signals += 1
    else:              bearish_signals += 1
    if price > ema50:  bullish_signals += 1
    else:              bearish_signals += 1
    if ema20 > ema50:  bullish_signals += 1
    else:              bearish_signals += 1
    if macd_hist > 0:  bullish_signals += 1
    else:              bearish_signals += 1
    if rsi > 55:       bullish_signals += 1
    elif rsi < 45:     bearish_signals += 1

    if bullish_signals >= 4:
        direction = "BULLISH"
    elif bearish_signals >= 4:
        direction = "BEARISH"
    else:
        direction = "NEUTRAL"

    # ── Component scoring (matches SCORE_WEIGHTS keys) ──
    trend_w = config.SCORE_WEIGHTS["trend"]
    mom_w   = config.SCORE_WEIGHTS["momentum"]
    vol_w   = config.SCORE_WEIGHTS["volume"]

    # Trend score
    if direction == "BULLISH":
        trend_score = trend_w * (bullish_signals / 5.0)
    elif direction == "BEARISH":
        trend_score = trend_w * (bearish_signals / 5.0)
    else:
        trend_score = trend_w * 0.3   # neutral gets partial credit

    # Momentum score — RSI in sweet spot + MACD alignment
    if direction == "BULLISH":
        rsi_ok = 1.0 if 50 <= rsi <= 70 else max(0.0, 1.0 - abs(rsi - 60) / 30)
        macd_ok = 1.0 if macd_hist > 0 else 0.0
    elif direction == "BEARISH":
        rsi_ok = 1.0 if 30 <= rsi <= 50 else max(0.0, 1.0 - abs(rsi - 40) / 30)
        macd_ok = 1.0 if macd_hist < 0 else 0.0
    else:
        rsi_ok, macd_ok = 0.3, 0.3
    momentum_score = mom_w * (0.6 * rsi_ok + 0.4 * macd_ok)

    # Volume score — RVOL and absolute liquidity
    rvol_score = min(1.0, rvol / 1.5)  # 1.5x avg = full credit
    liq_score  = min(1.0, avg_vol / 20_000_000)  # 20M avg = full credit
    volume_score = vol_w * (0.6 * rvol_score + 0.4 * liq_score)

    return {
        "ticker":         ticker,
        "price":          round(price, 2),
        "avg_volume":     int(avg_vol),
        "today_volume":   int(today_vol),
        "rvol":           round(rvol, 2),
        "ema20":          round(ema20, 2),
        "ema50":          round(ema50, 2),
        "rsi":            round(rsi, 1),
        "macd_line":      macd_line,
        "macd_signal":    macd_sig,
        "macd_hist":      macd_hist,
        "atr":            round(atr, 2),
        "atr_pct":        round((atr / price) * 100, 2) if price > 0 else 0,
        "direction":      direction,
        "bullish_signals": bullish_signals,
        "bearish_signals": bearish_signals,
        "score_trend":    round(trend_score, 1),
        "score_momentum": round(momentum_score, 1),
        "score_volume":   round(volume_score, 1),
    }


if __name__ == "__main__":
    for t in ["AMD", "PLTR", "SOFI", "F"]:
        r = analyze(t)
        if r:
            print(f"{t}: price=${r['price']}  dir={r['direction']}  "
                  f"scores T{r['score_trend']}/M{r['score_momentum']}/V{r['score_volume']}")
        else:
            print(f"{t}: filtered out or no data")