"""
premarket_data.py — Fetch premarket bar data for a list of tickers via yfinance,
concurrently, and compute gap_pct + premarket_volume.

Definitions:
  premarket_window   = 04:00 – 09:30 ET on today's date
  premarket_volume   = sum of 1-min bar volumes inside the window
  premarket_last     = last close of a 1-min bar inside the window
  prev_close         = yesterday's regular-session close (from daily bars)
  gap_pct            = (premarket_last - prev_close) / prev_close * 100
  price              = premarket_last (used for the price>3 filter)
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, time as dtime
from typing import Dict, List, Optional
import warnings

import config

try:
    from zoneinfo import ZoneInfo
    _ET = ZoneInfo("America/New_York")
except Exception:
    _ET = None  # pragma: no cover

# Silence yfinance / pandas noisy warnings
warnings.filterwarnings("ignore")


def _to_et(ts):
    """Convert a pandas Timestamp (tz-aware or naive) to ET."""
    if _ET is None:
        return ts
    try:
        if ts.tzinfo is None:
            # yfinance intraday timestamps are usually tz-aware; if not, assume UTC
            import pytz
            ts = ts.tz_localize("UTC")
        return ts.tz_convert(_ET)
    except Exception:
        return ts


def _fetch_one(ticker: str) -> Optional[Dict]:
    """Fetch one ticker's premarket stats. Returns None if it doesn't qualify or errors."""
    try:
        import yfinance as yf

        yf_ticker = yf.Ticker(ticker)

        # 1-minute bars including pre/post
        intraday = yf_ticker.history(period="2d", interval="1m",
                                      prepost=True, auto_adjust=False)
        if intraday is None or intraday.empty:
            return None

        # Daily bar for prev_close (last completed session)
        daily = yf_ticker.history(period="5d", interval="1d",
                                   prepost=False, auto_adjust=False)
        if daily is None or daily.empty:
            return None

        # Convert to ET and slice to today's premarket window
        idx = intraday.index
        if getattr(idx, "tz", None) is None:
            intraday = intraday.tz_localize("UTC")
        intraday = intraday.tz_convert(_ET) if _ET else intraday

        now_et = datetime.now(_ET) if _ET else datetime.now()
        today = now_et.date()

        pm_start = dtime(config.PM_START_HOUR_ET, config.PM_START_MIN_ET)
        pm_end   = dtime(config.PM_END_HOUR_ET,   config.PM_END_MIN_ET)

        mask_today = intraday.index.date == today
        pm = intraday[mask_today]
        if pm.empty:
            return None

        # keep bars within [04:00, 09:30) ET
        pm = pm[(pm.index.time >= pm_start) & (pm.index.time < pm_end)]
        if pm.empty:
            return None

        premarket_volume = int(pm["Volume"].fillna(0).sum())
        premarket_last   = float(pm["Close"].dropna().iloc[-1])

        # prev_close = last daily bar strictly before today
        prev_daily = daily[daily.index.date < today]
        if prev_daily.empty:
            prev_close = float(daily["Close"].iloc[-2]) if len(daily) >= 2 else float(daily["Close"].iloc[-1])
        else:
            prev_close = float(prev_daily["Close"].iloc[-1])

        if prev_close <= 0:
            return None

        gap_pct = (premarket_last - prev_close) / prev_close * 100.0

        return {
            "ticker":            ticker,
            "price":             round(premarket_last, 4),
            "prev_close":        round(prev_close, 4),
            "gap_pct":           round(gap_pct, 3),
            "premarket_volume":  premarket_volume,
            "premarket_bars":    int(len(pm)),
        }
    except Exception:
        return None


def fetch_premarket(tickers: List[str],
                    max_workers: int = None) -> List[Dict]:
    """
    Concurrent fetch. Returns a list of dicts (one per ticker that has premarket
    data). Missing / errored tickers are silently skipped.
    """
    if max_workers is None:
        max_workers = config.CONCURRENT_WORKERS

    results: List[Dict] = []
    total = len(tickers)
    done = 0

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_fetch_one, t): t for t in tickers}
        for fut in as_completed(futures):
            done += 1
            if done % 50 == 0 or done == total:
                print(f"  [premarket] {done}/{total} tickers fetched, "
                      f"{len(results)} with PM data...")
            row = fut.result()
            if row is not None:
                results.append(row)

    return results


def apply_filters(rows: List[Dict]) -> List[Dict]:
    """Apply the task's three hard filters and sort by gap_pct DESC. Caps at TOP_N."""
    filtered = [
        r for r in rows
        if r["gap_pct"] > config.GAP_MIN_PCT
        and r["price"] > config.PRICE_MIN
        and r["premarket_volume"] > config.PM_VOLUME_MIN
    ]
    filtered.sort(key=lambda x: x["gap_pct"], reverse=True)
    return filtered[: config.TOP_N]