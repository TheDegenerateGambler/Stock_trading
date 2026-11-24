"""
alphavantage.py — Alpha Vantage API client for DayTrade Picker.

Endpoints used (free tier, 25 calls/day):
  - TOP_GAINERS_LOSERS    (1 call, cache 30 min)
  - NEWS_SENTIMENT        (1 call per ticker, cache 60 min)
  - GLOBAL_QUOTE          (1 call per ticker, cache 5 min)
  - FEDERAL_FUNDS_RATE    (1 call, cache 24h)

Includes:
  - Rate limiter (max 5 calls/min for free tier)
  - Daily budget tracker (persisted to disk)
  - In-memory + file cache
"""
from __future__ import annotations
import json
import time
import threading
from pathlib import Path
from typing import Optional
import requests

import config

# ─────────────────────────────────────────────────────────────
# Cache
# ─────────────────────────────────────────────────────────────
_CACHE_DIR = Path(config.OUTPUT_DIR) / "av_cache"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)

_mem_cache: dict = {}
_cache_lock = threading.Lock()


def _cache_path(key: str) -> Path:
    safe = key.replace("/", "_").replace(":", "_").replace(" ", "_")
    return _CACHE_DIR / f"{safe}.json"


def _load_cache(key: str, ttl_minutes: int) -> Optional[object]:
    with _cache_lock:
        if key in _mem_cache:
            val, ts = _mem_cache[key]
            if time.time() - ts < ttl_minutes * 60:
                return val
        p = _cache_path(key)
        if p.exists():
            try:
                raw = json.loads(p.read_text())
                if time.time() - raw["_ts"] < ttl_minutes * 60:
                    _mem_cache[key] = (raw["data"], raw["_ts"])
                    return raw["data"]
            except Exception:
                pass
    return None


def _save_cache(key: str, data) -> None:
    with _cache_lock:
        ts = time.time()
        _mem_cache[key] = (data, ts)
        p = _cache_path(key)
        try:
            p.write_text(json.dumps({"_ts": ts, "data": data}))
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────
# Rate limiter & daily budget
# ─────────────────────────────────────────────────────────────
_rate_lock = threading.Lock()
_call_times: list = []
_daily_count = [0]

BUDGET_FILE = Path(config.OUTPUT_DIR) / "av_budget.json"
Path(config.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)


def _load_daily_count() -> int:
    try:
        if BUDGET_FILE.exists():
            raw = json.loads(BUDGET_FILE.read_text())
            if time.time() - raw.get("reset_ts", 0) > 86400:
                return 0
            return raw.get("count", 0)
    except Exception:
        pass
    return 0


def _save_daily_count(count: int) -> None:
    try:
        existing = {}
        if BUDGET_FILE.exists():
            try:
                existing = json.loads(BUDGET_FILE.read_text())
            except Exception:
                pass
        if time.time() - existing.get("reset_ts", 0) > 86400:
            existing = {"reset_ts": time.time(), "count": count}
        else:
            existing["count"] = count
        BUDGET_FILE.write_text(json.dumps(existing))
    except Exception:
        pass


# Init from disk on import
_daily_count[0] = _load_daily_count()


def remaining_budget() -> int:
    return max(0, config.AV_DAILY_BUDGET - _daily_count[0])


def _throttle() -> None:
    """Enforce max AV_CALLS_PER_MIN calls/minute."""
    with _rate_lock:
        now = time.time()
        _call_times[:] = [t for t in _call_times if now - t < 60]
        if len(_call_times) >= config.AV_CALLS_PER_MIN:
            sleep_for = 60 - (now - _call_times[0]) + 0.5
            if sleep_for > 0:
                print(f"  [AV] Rate limit pause: {sleep_for:.1f}s...")
                time.sleep(sleep_for)
        _call_times.append(time.time())
        _daily_count[0] += 1
        _save_daily_count(_daily_count[0])


def _call(params: dict) -> Optional[dict]:
    """Make one AV API call with throttling and graceful error handling."""
    if not config.AV_ENABLED:
        print("  [AV] ⚠ No API key set in config.py — AV calls skipped.")
        return None
    if remaining_budget() <= 0:
        print(f"  [AV] Daily budget exhausted ({config.AV_DAILY_BUDGET}/{config.AV_DAILY_BUDGET}). Skipping.")
        return None

    params["apikey"] = config.AV_API_KEY
    _throttle()

    try:
        r = requests.get(config.AV_BASE_URL, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()

        if "Note" in data:
            print(f"  [AV] Rate note: {str(data['Note'])[:80]}")
            time.sleep(65)
            return None
        if "Information" in data:
            print(f"  [AV] Info: {str(data['Information'])[:80]}")
            return None

        return data
    except Exception as e:
        print(f"  [AV] Request error: {e}")
        return None


# ─────────────────────────────────────────────────────────────
# Public endpoints
# ─────────────────────────────────────────────────────────────

def get_top_gainers_losers() -> dict:
    """
    TOP_GAINERS_LOSERS — 1 call, cache 30 min.
    Returns dict with keys: top_gainers, top_losers, most_actively_traded
    Each item has: ticker, price, change_amount, change_percentage, volume
    """
    key = "top_gainers_losers"
    cached = _load_cache(key, 30)
    if cached is not None:
        return cached

    print("  [AV] Fetching TOP_GAINERS_LOSERS...")
    data = _call({"function": "TOP_GAINERS_LOSERS"})
    if not data:
        return {}

    result = {
        "top_gainers":          data.get("top_gainers", []),
        "top_losers":           data.get("top_losers", []),
        "most_actively_traded": data.get("most_actively_traded", []),
        "last_updated":         data.get("last_updated", ""),
    }
    _save_cache(key, result)
    return result


def get_news_sentiment(ticker: str) -> dict:
    """
    NEWS_SENTIMENT for one ticker — 1 call, cache 60 min.
    Returns: {sentiment_score (0-1), sentiment_label, articles, top_headlines, raw_avg}
    0.0 = very bearish, 0.5 = neutral, 1.0 = very bullish
    """
    key = f"news_sentiment_{ticker.upper()}"
    cached = _load_cache(key, 60)
    if cached is not None:
        return cached

    _neutral = {
        "sentiment_score": 0.5,
        "sentiment_label": "Neutral",
        "articles": 0,
        "top_headlines": [],
        "raw_avg": 0.0,
    }

    if remaining_budget() <= 0:
        return _neutral

    print(f"  [AV] NEWS_SENTIMENT: {ticker}...")
    data = _call({
        "function": "NEWS_SENTIMENT",
        "tickers": ticker.upper(),
        "sort": "LATEST",
        "limit": "10",
    })
    if not data:
        return _neutral

    feed = data.get("feed", [])
    if not feed:
        return _neutral

    scores = []
    headlines = []
    for article in feed[:10]:
        for ts in article.get("ticker_sentiment", []):
            if ts.get("ticker", "").upper() == ticker.upper():
                try:
                    scores.append(float(ts.get("ticker_sentiment_score", 0.0)))
                except Exception:
                    pass
                break
        title = article.get("title", "")
        if title:
            headlines.append({
                "title":  title[:120],
                "url":    article.get("url", "#"),
                "source": article.get("source", ""),
                "published": article.get("time_published", "")[:8],
            })

    raw_avg = sum(scores) / len(scores) if scores else 0.0
    # AV ticker_sentiment_score range: -1.0 to +1.0
    norm = (raw_avg + 1.0) / 2.0  # normalise to 0-1

    if raw_avg >= 0.35:
        label = "Bullish"
    elif raw_avg >= 0.15:
        label = "Somewhat-Bullish"
    elif raw_avg <= -0.35:
        label = "Bearish"
    elif raw_avg <= -0.15:
        label = "Somewhat-Bearish"
    else:
        label = "Neutral"

    result = {
        "sentiment_score":  round(norm, 3),
        "sentiment_label":  label,
        "articles":         len(feed),
        "top_headlines":    headlines[:3],
        "raw_avg":          round(raw_avg, 3),
    }
    _save_cache(key, result)
    return result


def get_global_quote(ticker: str) -> dict:
    """
    GLOBAL_QUOTE — 1 call per ticker, cache 5 min.
    Returns: {price, open, high, low, volume, prev_close, change, change_pct}
    """
    key = f"global_quote_{ticker.upper()}"
    cached = _load_cache(key, 5)
    if cached is not None:
        return cached

    if remaining_budget() <= 0:
        return {}

    data = _call({"function": "GLOBAL_QUOTE", "symbol": ticker.upper()})
    if not data:
        return {}

    q = data.get("Global Quote", {})
    if not q:
        return {}

    def _f(k):
        try:
            v = q.get(k, "0")
            return float(str(v).replace("%", "").strip() or 0)
        except Exception:
            return 0.0

    result = {
        "price":      _f("05. price"),
        "open":       _f("02. open"),
        "high":       _f("03. high"),
        "low":        _f("04. low"),
        "volume":     int(_f("06. volume")),
        "prev_close": _f("08. previous close"),
        "change":     _f("09. change"),
        "change_pct": _f("10. change percent"),
    }
    _save_cache(key, result)
    return result


def get_market_quotes() -> dict:
    """
    Fetch SPY, QQQ, IWM quotes — up to 3 calls, cache 5 min each.
    Returns {"SPY": {...}, "QQQ": {...}, "IWM": {...}}
    """
    tickers = ["SPY", "QQQ", "IWM"]
    result = {}
    for t in tickers:
        q = get_global_quote(t)
        if q:
            result[t] = q
    return result


def get_federal_funds_rate() -> dict:
    """
    FEDERAL_FUNDS_RATE — 1 call, cache 24h.
    Returns: {rate, date, is_fed_day (approx)}
    """
    key = "federal_funds_rate"
    cached = _load_cache(key, 60 * 24)
    if cached is not None:
        return cached

    if remaining_budget() <= 0:
        return {"rate": None, "date": "", "is_fed_day": False}

    print("  [AV] Fetching FEDERAL_FUNDS_RATE...")
    data = _call({
        "function": "FEDERAL_FUNDS_RATE",
        "interval": "monthly",
        "datatype": "json",
    })
    if not data:
        return {"rate": None, "date": "", "is_fed_day": False}

    series = data.get("data", [])
    if not series:
        return {"rate": None, "date": "", "is_fed_day": False}

    latest = series[0]
    try:
        rate = float(latest.get("value", 0))
    except Exception:
        rate = 0.0

    result = {
        "rate":       round(rate, 2),
        "date":       latest.get("date", ""),
        "is_fed_day": False,  # simple flag — real FOMC calendar would need separate source
    }
    _save_cache(key, result)
    return result


def get_budget_status() -> str:
    """Return human-readable budget status string."""
    used = _daily_count[0]
    remaining = remaining_budget()
    return f"{used}/{config.AV_DAILY_BUDGET} calls used today ({remaining} remaining)"