"""
signal_engine.py — Compute technical signals + composite score per ticker.

Returns for each ticker:
{
  "ticker": "SPY",
  "price": 543.20,
  "change_pct": 0.4,
  "atr": 2.15,
  "signals": {  # each in [-1, +1]
     "vwap": +1, "ema_cross": +1, "rsi": +0.3, "macd": +0.8,
     "rvol": +0.5, "sentiment": +0.6, "gap": +0.4
  },
  "score": 62,           # weighted, in [-100, +100]
  "direction": "CALL",   # CALL / PUT / NO-TRADE
  "confidence": 62,      # abs(score) capped 0..100
  "rationale": [ "Above VWAP", "9/20 bull cross 5m", ... ],
  "bars_1m": <pandas DataFrame>,   # for chart hover / later use
}
"""
from __future__ import annotations
from datetime import datetime, time as dtime
from typing import Dict, Optional
import warnings

import config

try:
    from zoneinfo import ZoneInfo
    _ET = ZoneInfo("America/New_York")
except Exception:
    _ET = None

warnings.filterwarnings("ignore")


# ─────────────────────────────────────────────────────────────
# Indicator helpers
# ─────────────────────────────────────────────────────────────
def _rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, 1e-9)
    return 100 - (100 / (1 + rs))


def _macd(series, fast=12, slow=26, signal=9):
    ef = series.ewm(span=fast, adjust=False).mean()
    es = series.ewm(span=slow, adjust=False).mean()
    macd = ef - es
    sig = macd.ewm(span=signal, adjust=False).mean()
    hist = macd - sig
    return macd, sig, hist


def _atr(df, period=14):
    high = df["High"]; low = df["Low"]; close = df["Close"]
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    import pandas as pd
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def _vwap(df):
    tp = (df["High"] + df["Low"] + df["Close"]) / 3.0
    vp = tp * df["Volume"]
    return vp.cumsum() / df["Volume"].cumsum().replace(0, 1e-9)


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────
def analyze(ticker: str, sentiment: Optional[Dict] = None) -> Optional[Dict]:
    """
    Fetch bars + compute signals. Returns None on data failure.
    `sentiment` = dict from news_fetcher.get_news_sentiment(); optional.
    """
    try:
        import yfinance as yf
        import pandas as pd

        yt = yf.Ticker(ticker)

        # 1-min bars for today
        bars1 = yt.history(period="2d", interval="1m", prepost=False, auto_adjust=False)
        # 5-min bars for last 5 days for EMA / MACD / ATR context
        bars5 = yt.history(period="5d", interval="5m", prepost=False, auto_adjust=False)

        if bars1 is None or bars1.empty or bars5 is None or bars5.empty:
            return None

        # ET slice for today's regular-session bars
        for df in (bars1, bars5):
            if getattr(df.index, "tz", None) is None:
                df.index = df.index.tz_localize("UTC")
            if _ET is not None:
                df.index = df.index.tz_convert(_ET)

        now_et = datetime.now(_ET) if _ET else datetime.now()
        today = now_et.date()

        today_1m = bars1[bars1.index.date == today]
        today_1m = today_1m[(today_1m.index.time >= dtime(9, 30))
                            & (today_1m.index.time < dtime(16, 0))]
        if today_1m.empty:
            # Before market open or after close — fall back to last available session
            unique_days = sorted(set(bars1.index.date))
            if not unique_days:
                return None
            last_day = unique_days[-1]
            today_1m = bars1[bars1.index.date == last_day]
            today_1m = today_1m[(today_1m.index.time >= dtime(9, 30))
                                & (today_1m.index.time < dtime(16, 0))]
            if today_1m.empty:
                return None

        # Current price + change vs prev daily close
        price = float(today_1m["Close"].dropna().iloc[-1])

        daily = yt.history(period="5d", interval="1d",
                            prepost=False, auto_adjust=False)
        prev_close = float(daily["Close"].iloc[-2]) if len(daily) >= 2 else price
        change_pct = (price - prev_close) / prev_close * 100.0 if prev_close else 0.0

        # ── Indicators ──
        # VWAP on today's 1-min
        v = _vwap(today_1m)
        vwap_now = float(v.iloc[-1]) if not v.empty else price

        # EMA cross on 5-min
        c5 = bars5["Close"]
        ema9 = c5.ewm(span=9, adjust=False).mean()
        ema20 = c5.ewm(span=20, adjust=False).mean()

        # RSI on 5-min (last)
        rsi_series = _rsi(c5, 14)
        rsi_now = float(rsi_series.iloc[-1]) if len(rsi_series) else 50.0

        # MACD histogram on 5-min
        _, _, hist = _macd(c5)
        hist_now = float(hist.iloc[-1]) if len(hist) else 0.0
        hist_prev = float(hist.iloc[-2]) if len(hist) >= 2 else hist_now

        # ATR on 5-min (converted to per-share $)
        atr_series = _atr(bars5, 14)
        atr_now = float(atr_series.iloc[-1]) if len(atr_series) else price * 0.005

        # RVOL: today's cumulative volume vs 20-day avg cumulative to same time-of-day
        vol_today = float(today_1m["Volume"].sum())
        # Simple RVOL proxy: today's avg 1m vol vs last-5-day avg
        avg_daily_vol = float(daily["Volume"].tail(20).mean()) if not daily.empty else 0.0
        # Estimate expected volume by now (fraction of trading day elapsed)
        first_ts = today_1m.index[0]
        elapsed_min = (today_1m.index[-1] - first_ts).total_seconds() / 60.0 + 1
        frac = min(1.0, elapsed_min / 390.0)   # 390 min in regular session
        expected = avg_daily_vol * frac if avg_daily_vol else 1
        rvol = vol_today / expected if expected else 1.0

        # Gap sustained: price vs today's open
        open_px = float(today_1m["Open"].iloc[0])
        gap_state = (price - open_px) / open_px if open_px else 0.0

        # ── Convert to unit signals in [-1, +1] ──
        s = {}
        rationale = []

        # VWAP
        vwap_diff = (price - vwap_now) / max(price, 1e-6)
        s["vwap"] = max(-1.0, min(1.0, vwap_diff / 0.005))   # ±0.5% band saturates
        rationale.append(f"{'Above' if s['vwap']>0 else 'Below'} VWAP ({vwap_now:.2f})")

        # EMA cross
        if len(ema9) and len(ema20):
            diff = float(ema9.iloc[-1] - ema20.iloc[-1])
            s["ema_cross"] = max(-1.0, min(1.0, diff / (price * 0.003)))
            rationale.append(
                f"9EMA {'>' if diff>0 else '<'} 20EMA (5m)"
            )
        else:
            s["ema_cross"] = 0.0

        # RSI
        if rsi_now >= 70:
            s["rsi"] = -0.4  # overbought, mild bearish reversion
            rationale.append(f"RSI {rsi_now:.0f} overbought")
        elif rsi_now <= 30:
            s["rsi"] = +0.4
            rationale.append(f"RSI {rsi_now:.0f} oversold")
        else:
            s["rsi"] = (rsi_now - 50) / 30.0
            rationale.append(f"RSI {rsi_now:.0f}")

        # MACD hist
        if hist_now > 0 and hist_now > hist_prev:
            s["macd"] = +0.8; rationale.append("MACD hist + rising")
        elif hist_now > 0:
            s["macd"] = +0.4; rationale.append("MACD hist positive")
        elif hist_now < 0 and hist_now < hist_prev:
            s["macd"] = -0.8; rationale.append("MACD hist - falling")
        elif hist_now < 0:
            s["macd"] = -0.4; rationale.append("MACD hist negative")
        else:
            s["macd"] = 0.0

        # RVOL
        if rvol >= 2.0:
            s["rvol"] = +0.7
            rationale.append(f"RVOL {rvol:.1f}x")
        elif rvol >= 1.3:
            s["rvol"] = +0.3
            rationale.append(f"RVOL {rvol:.1f}x")
        elif rvol <= 0.7:
            s["rvol"] = -0.3
            rationale.append(f"RVOL low {rvol:.1f}x")
        else:
            s["rvol"] = 0.0

        # Sentiment (AV NEWS_SENTIMENT -> raw_avg in [-1, +1])
        if sentiment:
            raw = float(sentiment.get("raw_avg", 0.0))
            s["sentiment"] = max(-1.0, min(1.0, raw))
            label = sentiment.get("sentiment_label", "")
            if label:
                rationale.append(f"News {label}")
        else:
            s["sentiment"] = 0.0

        # Gap sustained
        s["gap"] = max(-1.0, min(1.0, gap_state / 0.015))  # ±1.5% saturates
        if abs(gap_state) > 0.003:
            rationale.append(
                f"{'+' if gap_state>0 else ''}{gap_state*100:.2f}% vs open"
            )

        # ── Composite score ──
        w = config.SIGNAL_WEIGHTS
        score = sum(s[k] * w.get(k, 0) for k in s)   # ~[-100, +100]
        score = max(-100.0, min(100.0, score))

        if score >= config.TRADE_THRESHOLD_SCORE:
            direction = "CALL"
        elif score <= -config.TRADE_THRESHOLD_SCORE:
            direction = "PUT"
        else:
            direction = "NO-TRADE"

        return {
            "ticker": ticker,
            "price": round(price, 4),
            "prev_close": round(prev_close, 4),
            "change_pct": round(change_pct, 2),
            "atr": round(atr_now, 4),
            "vwap": round(vwap_now, 4),
            "rsi": round(rsi_now, 1),
            "rvol": round(rvol, 2),
            "signals": {k: round(v, 3) for k, v in s.items()},
            "score": round(score, 1),
            "direction": direction,
            "confidence": int(round(abs(score))),
            "rationale": rationale,
        }
    except Exception as e:
        print("  [signal] " + ticker + " error: " + str(e))
        return None
