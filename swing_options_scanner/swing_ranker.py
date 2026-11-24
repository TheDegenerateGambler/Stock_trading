"""
swing_ranker.py — Compose the final swing score for a candidate.

Combines:
  - Technical scores (trend, momentum, volume) — from technical_screener
  - Sentiment score — Alpha Vantage NEWS_SENTIMENT (optional, throttled)
  - Options scores (liquidity, budget_fit) — from options_selector

Final composite: 0–100.
Only picks scoring >= config.TRADE_THRESHOLD_SCORE are surfaced.
"""
from __future__ import annotations
import time
from typing import Dict, Optional

import requests

import config

# ─────────────────────────────────────────────────────────────
# Alpha Vantage NEWS_SENTIMENT (rate-limited)
# ─────────────────────────────────────────────────────────────
_AV_CALLS_THIS_MINUTE = 0
_AV_MINUTE_START = 0.0
_AV_CALLS_TODAY = 0
_AV_SENTIMENT_CACHE: Dict[str, Dict] = {}
_AV_TTL_SECONDS = 3600  # cache sentiment for 1 hour per ticker


def _av_throttle() -> None:
    """Respect AV free tier: 5 calls/min."""
    global _AV_CALLS_THIS_MINUTE, _AV_MINUTE_START
    now = time.time()
    if now - _AV_MINUTE_START > 60:
        _AV_MINUTE_START = now
        _AV_CALLS_THIS_MINUTE = 0
    if _AV_CALLS_THIS_MINUTE >= config.AV_CALLS_PER_MIN:
        wait = 60 - (now - _AV_MINUTE_START) + 1
        if wait > 0:
            time.sleep(wait)
        _AV_MINUTE_START = time.time()
        _AV_CALLS_THIS_MINUTE = 0


def _fetch_av_sentiment(ticker: str) -> Optional[Dict]:
    """Return AV NEWS_SENTIMENT summary for a ticker, or None."""
    global _AV_CALLS_THIS_MINUTE, _AV_CALLS_TODAY

    if not config.AV_ENABLED:
        return None
    if _AV_CALLS_TODAY >= config.AV_DAILY_BUDGET:
        return None

    # Cache
    cached = _AV_SENTIMENT_CACHE.get(ticker)
    if cached and (time.time() - cached["_ts"]) < _AV_TTL_SECONDS:
        return cached["data"]

    _av_throttle()

    try:
        params = {
            "function": "NEWS_SENTIMENT",
            "tickers":  ticker,
            "limit":    20,
            "apikey":   config.AV_API_KEY,
        }
        r = requests.get(config.AV_BASE_URL, params=params, timeout=15)
        _AV_CALLS_THIS_MINUTE += 1
        _AV_CALLS_TODAY += 1
        if r.status_code != 200:
            return None
        data = r.json() or {}
        if "Information" in data or "Note" in data:
            # Rate-limited or budget hit
            return None
        _AV_SENTIMENT_CACHE[ticker] = {"_ts": time.time(), "data": data}
        return data
    except Exception:
        return None


def _sentiment_score(ticker: str, direction: str) -> float:
    """Return 0..1 sentiment fit for the desired direction."""
    data = _fetch_av_sentiment(ticker)
    if not data:
        return 0.5  # neutral when unknown

    feed = data.get("feed", []) or []
    if not feed:
        return 0.5

    ticker_scores = []
    for article in feed[:20]:
        for ts in article.get("ticker_sentiment", []):
            if ts.get("ticker", "").upper() == ticker.upper():
                try:
                    ticker_scores.append(float(ts.get("ticker_sentiment_score", 0)))
                except Exception:
                    pass

    if not ticker_scores:
        return 0.5

    avg = sum(ticker_scores) / len(ticker_scores)   # roughly -0.35 to +0.35
    # Normalize to [0, 1]
    norm = max(-0.35, min(0.35, avg)) / 0.35        # -1..+1
    if direction == "CALL":
        return (norm + 1) / 2                        # bullish sentiment → higher
    else:
        return (1 - norm) / 2                        # bearish sentiment → higher


def rank(tech: Dict, contract: Dict, direction: str,
         earnings_days: Optional[int]) -> Dict:
    """
    Combine all component scores into a final 0–100 composite.
    Attaches: composite_score, score_sentiment, direction, earnings info.
    """
    sent_w = config.SCORE_WEIGHTS["sentiment"]

    # Sentiment (throttled — may be neutral if AV budget hit)
    sent_norm = _sentiment_score(tech["ticker"], direction)
    score_sentiment = round(sent_w * sent_norm, 1)

    # Sum components (from tech + contract + here)
    composite = (
        tech.get("score_trend", 0)         +
        tech.get("score_momentum", 0)      +
        tech.get("score_volume", 0)        +
        score_sentiment                    +
        contract.get("score_liquidity", 0) +
        contract.get("score_budget_fit", 0)
    )

    # Small penalty if earnings during hold window
    earnings_flag = "N/A"
    if earnings_days is not None:
        if 0 <= earnings_days <= config.SKIP_EARNINGS_DAYS:
            composite *= 0.6   # heavy penalty (should be pre-filtered but safety net)
            earnings_flag = f"⚠️ Earnings in {earnings_days}d"
        elif earnings_days < 0:
            earnings_flag = f"Earnings passed ({abs(earnings_days)}d ago)"
        else:
            earnings_flag = f"Next earnings in {earnings_days}d ✅"

    return {
        "direction":          direction,
        "score_sentiment":    score_sentiment,
        "sentiment_norm":     round(sent_norm, 3),
        "composite_score":    round(composite, 1),
        "earnings_days":      earnings_days,
        "earnings_flag":      earnings_flag,
    }