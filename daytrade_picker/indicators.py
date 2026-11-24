"""
indicators.py — Pure-Python technical indicator calculations.
No external dependencies beyond standard math.
"""
from __future__ import annotations
import math
from typing import List, Tuple


def safe(val, default=0.0):
    try:
        f = float(val)
        return default if (f != f or math.isinf(f)) else f
    except Exception:
        return default


def calc_rsi(closes: List[float], period: int = 14) -> float:
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


def calc_ema(values: List[float], period: int) -> List[float]:
    if not values:
        return []
    k = 2.0 / (period + 1)
    result = [values[0]]
    for v in values[1:]:
        result.append(v * k + result[-1] * (1 - k))
    return result


def calc_macd(closes: List[float],
              fast: int = 12, slow: int = 26, signal: int = 9
              ) -> Tuple[float, float, float]:
    """Returns (macd_line, signal_line, histogram)."""
    if len(closes) < slow + signal:
        return 0.0, 0.0, 0.0
    ema_fast = calc_ema(closes, fast)
    ema_slow = calc_ema(closes, slow)
    macd_series = [f - s for f, s in zip(ema_fast, ema_slow)]
    sig_series = calc_ema(macd_series, signal)
    macd_line = macd_series[-1]
    sig_line = sig_series[-1]
    hist = macd_line - sig_line
    return round(macd_line, 4), round(sig_line, 4), round(hist, 4)


def calc_vwap(highs: List[float], lows: List[float],
              closes: List[float], volumes: List[float]) -> float:
    """Cumulative VWAP for the day."""
    cum_pv = 0.0
    cum_v = 0.0
    for h, l, c, v in zip(highs, lows, closes, volumes):
        typ = (h + l + c) / 3.0
        cum_pv += typ * v
        cum_v += v
    return round(cum_pv / cum_v, 4) if cum_v > 0 else closes[-1] if closes else 0.0


def calc_atr(highs: List[float], lows: List[float],
             closes: List[float], period: int = 14) -> float:
    """Average True Range."""
    if len(highs) < 2:
        return 0.0
    trs = []
    for i in range(1, len(highs)):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )
        trs.append(tr)
    window = trs[-period:] if len(trs) >= period else trs
    return round(sum(window) / len(window), 4) if window else 0.0