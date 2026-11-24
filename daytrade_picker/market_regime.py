"""
market_regime.py — Detect current market regime using yfinance (free).

Returns: bull / bear / choppy + VIX level + risk guidance.
Uses yfinance for SPY, QQQ, IWM, VIX — no API credits consumed.
"""
from __future__ import annotations
import warnings
warnings.filterwarnings("ignore")
from typing import Dict
import config

_CACHE: Dict = {}
_CACHE_TS: float = 0.0
_CACHE_TTL = 300  # 5 min


def _safe(val, default=0.0):
    try:
        f = float(val)
        return default if f != f else f
    except Exception:
        return default


def fetch_regime() -> Dict:
    """
    Fetch SPY, QQQ, IWM day change % and VIX level via yfinance.
    Returns regime dict with keys:
      label, vix, spy_chg, qqq_chg, iwm_chg,
      risk_level (low/elevated/extreme),
      bias (bull/bear/choppy),
      guidance (string for display)
    """
    import time
    global _CACHE, _CACHE_TS
    if _CACHE and time.time() - _CACHE_TS < _CACHE_TTL:
        return _CACHE

    result = {
        "label":     "Unknown",
        "vix":       0.0,
        "spy_chg":   0.0,
        "qqq_chg":   0.0,
        "iwm_chg":   0.0,
        "risk_level": "unknown",
        "bias":      "choppy",
        "guidance":  "",
    }

    try:
        import yfinance as yf
        tickers = yf.download(
            ["SPY", "QQQ", "IWM", "^VIX"],
            period="2d", interval="1d",
            group_by="ticker", progress=False, auto_adjust=True,
        )

        def _chg(sym):
            try:
                df = tickers[sym].dropna()
                if len(df) >= 2:
                    prev = _safe(df["Close"].iloc[-2])
                    curr = _safe(df["Close"].iloc[-1])
                    return round((curr - prev) / prev * 100, 2) if prev else 0.0
                return 0.0
            except Exception:
                return 0.0

        def _last(sym):
            try:
                df = tickers[sym].dropna()
                return _safe(df["Close"].iloc[-1]) if len(df) >= 1 else 0.0
            except Exception:
                return 0.0

        spy_chg = _chg("SPY")
        qqq_chg = _chg("QQQ")
        iwm_chg = _chg("IWM")
        vix     = _last("^VIX")

        # Regime detection
        avg_chg = (spy_chg + qqq_chg) / 2

        if vix >= config.VIX_EXTREME:
            risk_level = "extreme"
            bias = "bear"
            label = "EXTREME FEAR"
            guidance = f"VIX {vix:.1f} — extreme volatility. Avoid new longs. Shorts only with tight stops."
        elif vix >= config.VIX_HIGH_THRESHOLD:
            risk_level = "elevated"
            if avg_chg >= 0.3:
                bias = "bull"
                label = "ELEVATED RISK / BULL"
            elif avg_chg <= -0.3:
                bias = "bear"
                label = "ELEVATED RISK / BEAR"
            else:
                bias = "choppy"
                label = "ELEVATED RISK / CHOPPY"
            guidance = f"VIX {vix:.1f} — elevated risk. Reduce position size, widen stops."
        else:
            risk_level = "low"
            if avg_chg >= 0.3:
                bias = "bull"
                label = "BULL"
                guidance = f"Market trending up (SPY {spy_chg:+.1f}%, QQQ {qqq_chg:+.1f}%). Favour longs."
            elif avg_chg <= -0.3:
                bias = "bear"
                label = "BEAR"
                guidance = f"Market trending down (SPY {spy_chg:+.1f}%, QQQ {qqq_chg:+.1f}%). Favour shorts."
            else:
                bias = "choppy"
                label = "CHOPPY / NEUTRAL"
                guidance = "Market flat. Be selective — only high-conviction setups."

        result.update({
            "label":      label,
            "vix":        round(vix, 1),
            "spy_chg":    spy_chg,
            "qqq_chg":    qqq_chg,
            "iwm_chg":    iwm_chg,
            "risk_level": risk_level,
            "bias":       bias,
            "guidance":   guidance,
        })

    except Exception as e:
        print(f"  [Regime] yfinance fetch failed: {e}")
        result["guidance"] = "Market data unavailable."

    import time
    _CACHE = result
    _CACHE_TS = time.time()
    return result