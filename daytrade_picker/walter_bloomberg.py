"""
walter_bloomberg.py — Walter Bloomberg macro RSS feed fetcher.

Walter Bloomberg (@WalterBloomberg) is a real-time macro news aggregator
covering Fed headlines, economic data releases, geopolitical events.
Zero API credits — free RSS, updates continuously.
"""
from __future__ import annotations
import time
import threading
from typing import List, Dict
import config

_headlines: List[Dict] = []
_last_fetch: float = 0.0
_lock = threading.Lock()


def _age_label(ts: float) -> str:
    if not ts:
        return ""
    diff = time.time() - ts
    if diff < 60:
        return f"{int(diff)}s ago"
    if diff < 3600:
        return f"{int(diff / 60)}m ago"
    if diff < 86400:
        return f"{int(diff / 3600)}h ago"
    return f"{int(diff / 86400)}d ago"


def _fetch_feed(url: str) -> List[Dict]:
    items = []
    try:
        import feedparser
        feed = feedparser.parse(url)
        for entry in feed.entries[:config.MAX_WALTER_ITEMS]:
            title = entry.get("title", "").strip()
            if not title:
                continue
            pub_ts = 0.0
            try:
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    pub_ts = time.mktime(entry.published_parsed)
            except Exception:
                pass
            items.append({
                "title":  title[:200],
                "url":    entry.get("link", "#"),
                "age":    _age_label(pub_ts),
                "ts":     pub_ts,
                "source": "Walter Bloomberg",
            })
    except ImportError:
        print("  [WB] feedparser not installed — pip install feedparser")
    except Exception as e:
        print(f"  [WB] Feed error ({url[:50]}): {e}")
    return items


def refresh() -> List[Dict]:
    """Fetch latest headlines. Tries primary URL, falls back to alt."""
    global _last_fetch
    items = _fetch_feed(config.WALTER_BLOOMBERG_RSS)
    if not items:
        items = _fetch_feed(config.WALTER_BLOOMBERG_ALT)
    if not items:
        # Last resort: Google News search for Walter Bloomberg topics
        fallback = (
            "https://news.google.com/rss/search?"
            "q=Federal+Reserve+FOMC+CPI+jobs+report+macro+economy"
            "&hl=en-US&gl=US&ceid=US:en"
        )
        items = _fetch_feed(fallback)
    with _lock:
        _headlines.clear()
        _headlines.extend(sorted(items, key=lambda x: x["ts"], reverse=True))
        _last_fetch = time.time()
    return get_headlines()


def get_headlines() -> List[Dict]:
    with _lock:
        return list(_headlines)


def get_last_fetch_age() -> str:
    if not _last_fetch:
        return "never"
    return _age_label(_last_fetch)


def start_background_refresh() -> threading.Thread:
    """Start a daemon thread that refreshes every WALTER_REFRESH_MIN minutes."""
    def _loop():
        while True:
            try:
                refresh()
            except Exception as e:
                print(f"  [WB] Background refresh error: {e}")
            time.sleep(config.WALTER_REFRESH_MIN * 60)

    t = threading.Thread(target=_loop, name="walter-bloomberg-rss", daemon=True)
    t.start()
    return t