"""
earnings_calendar.py — Determine next earnings date for a ticker.

Uses yfinance's Ticker.calendar / get_earnings_dates() as primary source.
Cached to output/earnings_cache.json to avoid re-hitting Yahoo for every scan.

Returns:
  - days_to_earnings: int (days from today until next earnings; None if unknown)
  - is_safe(days_to_earnings, hold_days): True if earnings won't hit during hold
"""
from __future__ import annotations
import json
import time
from datetime import datetime, date, timezone
from pathlib import Path
from typing import Optional

import config

_CACHE_FILE = Path(config.OUTPUT_DIR) / "earnings_cache.json"
Path(config.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

# Cache earnings dates for 24 hours (they rarely change intraday)
_TTL_SECONDS = 86400


def _load_cache() -> dict:
    if not _CACHE_FILE.exists():
        return {}
    try:
        raw = json.loads(_CACHE_FILE.read_text())
        return raw if isinstance(raw, dict) else {}
    except Exception:
        return {}


def _save_cache(cache: dict) -> None:
    try:
        _CACHE_FILE.write_text(json.dumps(cache))
    except Exception:
        pass


def _get_cached(ticker: str) -> Optional[int]:
    cache = _load_cache()
    entry = cache.get(ticker.upper())
    if not entry:
        return None
    if time.time() - entry.get("_ts", 0) > _TTL_SECONDS:
        return None
    # Recompute days_to based on cached earnings date (not the cached
    # days_to, which was correct only at cache time)
    ed_str = entry.get("earnings_date")
    if not ed_str:
        return entry.get("days_to_earnings")
    try:
        ed = datetime.fromisoformat(ed_str).date()
        return (ed - date.today()).days
    except Exception:
        return entry.get("days_to_earnings")


def _set_cached(ticker: str, days_to: Optional[int],
                earnings_date: Optional[date]) -> None:
    cache = _load_cache()
    cache[ticker.upper()] = {
        "_ts": time.time(),
        "days_to_earnings": days_to,
        "earnings_date": earnings_date.isoformat() if earnings_date else None,
    }
    _save_cache(cache)


def get_days_to_earnings(ticker: str) -> Optional[int]:
    """
    Return days from today until the next earnings report, or None if unknown.
    Negative values mean the earnings date has passed (data lag).
    """
    cached = _get_cached(ticker)
    if cached is not None:
        return cached

    try:
        import yfinance as yf
        t = yf.Ticker(ticker)

        # Method 1: get_earnings_dates() — most reliable
        try:
            df = t.get_earnings_dates(limit=8)
            if df is not None and not df.empty:
                today = datetime.now(timezone.utc).date()
                future_dates = []
                for idx in df.index:
                    try:
                        d = idx.date() if hasattr(idx, "date") else idx
                        if d >= today:
                            future_dates.append(d)
                    except Exception:
                        continue
                if future_dates:
                    next_ed = min(future_dates)
                    days = (next_ed - date.today()).days
                    _set_cached(ticker, days, next_ed)
                    return days
        except Exception:
            pass

        # Method 2: calendar attribute
        try:
            cal = t.calendar
            if isinstance(cal, dict):
                ed = cal.get("Earnings Date")
                if isinstance(ed, list) and ed:
                    d = ed[0]
                    if hasattr(d, "date"):
                        d = d.date()
                    days = (d - date.today()).days
                    _set_cached(ticker, days, d)
                    return days
        except Exception:
            pass

    except Exception as e:
        print(f"  [earnings] {ticker}: fetch failed ({e})")

    # Unknown — cache the miss briefly so we don't hammer Yahoo
    _set_cached(ticker, None, None)
    return None


def is_safe(ticker: str, hold_days: int = 30) -> bool:
    """
    Return True if the earnings window is safe for a `hold_days` swing trade.
    Safe if:
      - Earnings date is unknown (None → treat as safe but flagged)
      - Earnings date is more than SKIP_EARNINGS_DAYS out
      - Earnings date is already in the past
    """
    days = get_days_to_earnings(ticker)
    if days is None:
        return True  # unknown — treat cautiously optimistic
    if days < 0:
        return True  # earnings passed (stale data)
    return days > max(hold_days, config.SKIP_EARNINGS_DAYS)


if __name__ == "__main__":
    for t in ["AAPL", "NVDA", "PLTR", "SOFI"]:
        d = get_days_to_earnings(t)
        safe = is_safe(t, 30)
        print(f"{t}: days_to_earnings={d}  safe_for_30d_hold={safe}")