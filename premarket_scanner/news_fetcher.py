"""
news_fetcher.py — Enrich picks with news catalyst + sentiment.

Primary source : Alpha Vantage NEWS_SENTIMENT   (score + labeled sentiment)
Fallback       : yfinance Ticker.news           (headlines only, sentiment=Neutral)

Also tags each pick with a Catalyst category based on headline keywords:
  Earnings / FDA / M&A / Guidance / Analyst / Offering / Partnership /
  Legal / Insider / Other
"""
from __future__ import annotations
import re
from datetime import datetime
from typing import Dict, List

import config
import alphavantage_client as av


# ─────────────────────────────────────────────────────────────
# Catalyst tagging
# ─────────────────────────────────────────────────────────────
_CATALYST_RULES = [
    ("Earnings",     re.compile(r"\b(earnings|q[1-4]\s*results|eps|beats|misses|reports\s+q|quarterly\s+results)\b", re.I)),
    ("Guidance",     re.compile(r"\b(guidance|outlook|raises\s+forecast|cuts\s+forecast|reaffirms)\b", re.I)),
    ("FDA/Clinical", re.compile(r"\b(fda|phase\s*[123]|clinical\s+trial|approval|breakthrough\s+therapy|topline)\b", re.I)),
    ("M&A",          re.compile(r"\b(acquires?|acquisition|merger|to\s+acquire|buyout|takeover|going\s+private)\b", re.I)),
    ("Analyst",      re.compile(r"\b(upgrade[sd]?|downgrade[sd]?|price\s+target|initiates?\s+coverage|reiterates?)\b", re.I)),
    ("Offering",     re.compile(r"\b(offering|dilution|prices\s+\$|secondary|share\s+sale|registered\s+direct)\b", re.I)),
    ("Partnership",  re.compile(r"\b(partnership|collaboration|deal\s+with|signs\s+agreement|joint\s+venture)\b", re.I)),
    ("Legal",        re.compile(r"\b(lawsuit|sued|settlement|doj|sec\s+charges|investigation|subpoena)\b", re.I)),
    ("Insider",      re.compile(r"\b(insider\s+(buy|sell)|13d|form\s+4|stake|ceo\s+buys)\b", re.I)),
    ("Product",      re.compile(r"\b(launch|unveils|introduces|new\s+product|releases)\b", re.I)),
    ("Contract",     re.compile(r"\b(contract\s+award|wins\s+contract|selected\s+by|awarded)\b", re.I)),
]


def _tag_catalyst(headlines: List[Dict]) -> str:
    """Return the first matching catalyst category, or 'Other'."""
    for h in headlines:
        title = h.get("title", "")
        for label, rx in _CATALYST_RULES:
            if rx.search(title):
                return label
    return "Other"


# ─────────────────────────────────────────────────────────────
# yfinance news fallback
# ─────────────────────────────────────────────────────────────
def _yf_news(ticker: str, limit: int) -> List[Dict]:
    try:
        import yfinance as yf
        news = yf.Ticker(ticker).news or []
    except Exception:
        return []

    out = []
    for item in news[:limit]:
        # yfinance news schema changed across versions; handle both.
        content = item.get("content", item)
        title   = content.get("title") or item.get("title") or ""
        url     = ""
        if isinstance(content.get("canonicalUrl"), dict):
            url = content["canonicalUrl"].get("url", "")
        url = url or content.get("link") or item.get("link", "#")
        source  = ""
        prov = content.get("provider") or {}
        if isinstance(prov, dict):
            source = prov.get("displayName", "")
        source = source or item.get("publisher", "")
        pub_ts = item.get("providerPublishTime") or 0
        try:
            pub = datetime.fromtimestamp(pub_ts).strftime("%Y%m%dT%H%M") if pub_ts else ""
        except Exception:
            pub = ""

        out.append({
            "title":     str(title)[:200],
            "url":       url or "#",
            "source":    source,
            "published": pub,
            "sentiment": 0.0,
        })
    return out


# ─────────────────────────────────────────────────────────────
# Public
# ─────────────────────────────────────────────────────────────
def enrich(picks: List[Dict]) -> List[Dict]:
    """
    For each pick, add:
      sentiment_score  (0..1)
      sentiment_label
      raw_sentiment    (-1..1)
      catalyst         (category string)
      headlines        (list of up to NEWS_HEADLINES dicts)
      news_source      ('alphavantage' | 'yfinance' | 'none')
    """
    for p in picks:
        ticker = p["ticker"]
        news = av.get_news_sentiment(ticker, limit_headlines=config.NEWS_HEADLINES)
        headlines = news.get("headlines", [])
        source = "alphavantage" if headlines else "none"

        if not headlines:
            yf_h = _yf_news(ticker, config.NEWS_HEADLINES)
            if yf_h:
                headlines = yf_h
                source = "yfinance"

        catalyst = _tag_catalyst(headlines) if headlines else "Other"

        p["sentiment_score"] = news.get("sentiment_score", 0.5)
        p["sentiment_label"] = news.get("sentiment_label", "Neutral")
        p["raw_sentiment"]   = news.get("raw_avg", 0.0)
        p["catalyst"]        = catalyst
        p["headlines"]       = headlines[: config.NEWS_HEADLINES]
        p["news_source"]     = source

    return picks