"""
alphavantage_client.py — Slim AV client for the premarket scanner.

Reuses the same throttle + cache pattern as daytrade_picker/alphavantage.py,
but is self-contained (no cross-package imports).

Endpoints:
  - TOP_GAINERS_LOSERS   (cache 30 min)
  - NEWS_SENTIMENT       (cache 30 min per ticker)
"""
from __future__ import annotations
import json
import time
import threading
from pathlib import Path
from typing import Optional, List, Dict
import requests

import config

_CACHE_DIR = Path(config.OUTPUT_DIR) / "av_cache"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)

_mem_cache: dict = {}
_cache_lock = threading.Lock()
_rate_lock  = threading.Lock()
_call_times: list = []
_daily_count = [0]

BUDGET_FILE = Path(config.OUTPUT_DIR) / "av_budget.json"


# ─────────────────────────────────────────────────────────────
# Cache helpers
# ─────────────────────────────────────────────────────────────
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
        try:
            _cache_path(key).write_text(json.dumps({"_ts": ts, "data": data}))
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────
# Budget & throttle
# ─────────────────────────────────────────────────────────────
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


_daily_count[0] = _load_daily_count()


def remaining_budget() -> int:
    return max(0, config.AV_DAILY_BUDGET - _daily_count[0])


def get_budget_status() -> str:
    used = _daily_count[0]
    return f"{used}/{config.AV_DAILY_BUDGET} AV calls used today ({remaining_budget()} remaining)"


def _throttle() -> None:
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
    if not config.AV_ENABLED:
        return None
    if remaining_budget() <= 0:
        print(f"  [AV] Daily budget exhausted. Skipping.")
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
# Public: TOP_GAINERS_LOSERS
# ─────────────────────────────────────────────────────────────
def get_top_gainers_losers() -> Dict:
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


# ─────────────────────────────────────────────────────────────
# Public: NEWS_SENTIMENT
# ─────────────────────────────────────────────────────────────
def get_news_sentiment(ticker: str, limit_headlines: int = 4) -> Dict:
    """
    Returns dict:
      {
        sentiment_score:  float 0-1  (normalized, 0.5 = neutral)
        sentiment_label:  Bullish / Somewhat-Bullish / Neutral / Somewhat-Bearish / Bearish
        raw_avg:          float -1..+1
        articles:         int
        headlines: [ { title, url, source, published, sentiment (raw) } ... ]
      }
    """
    key = f"news_sentiment_{ticker.upper()}"
    cached = _load_cache(key, 30)
    if cached is not None:
        return cached

    _neutral = {
        "sentiment_score": 0.5,
        "sentiment_label": "Neutral",
        "raw_avg": 0.0,
        "articles": 0,
        "headlines": [],
    }

    if remaining_budget() <= 0:
        return _neutral

    print(f"  [AV] NEWS_SENTIMENT: {ticker}...")
    data = _call({
        "function": "NEWS_SENTIMENT",
        "tickers":  ticker.upper(),
        "sort":     "LATEST",
        "limit":    "20",
    })
    if not data:
        return _neutral

    feed = data.get("feed", [])
    if not feed:
        return _neutral

    scores: List[float] = []
    headlines: List[Dict] = []
    for article in feed:
        my_score = 0.0
        for ts in article.get("ticker_sentiment", []):
            if ts.get("ticker", "").upper() == ticker.upper():
                try:
                    my_score = float(ts.get("ticker_sentiment_score", 0.0))
                    scores.append(my_score)
                except Exception:
                    pass
                break
        headlines.append({
            "title":     article.get("title", "")[:200],
            "url":       article.get("url", "#"),
            "source":    article.get("source", ""),
            "published": article.get("time_published", "")[:15],
            "sentiment": round(my_score, 3),
        })

    raw_avg = sum(scores) / len(scores) if scores else 0.0
    norm    = (raw_avg + 1.0) / 2.0

    if   raw_avg >=  0.35: label = "Bullish"
    elif raw_avg >=  0.15: label = "Somewhat-Bullish"
    elif raw_avg <= -0.35: label = "Bearish"
    elif raw_avg <= -0.15: label = "Somewhat-Bearish"
    else:                  label = "Neutral"

    result = {
        "sentiment_score": round(norm, 3),
        "sentiment_label": label,
        "raw_avg":         round(raw_avg, 3),
        "articles":        len(feed),
        "headlines":       headlines[:limit_headlines],
    }
    _save_cache(key, result)
    return result