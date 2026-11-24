"""
universe.py — Builds the ticker universe for the premarket scanner.

Sources (union, deduped):
  1. Alpha Vantage TOP_GAINERS_LOSERS  (top_gainers + most_actively_traded)
  2. S&P 500 list (Wikipedia, scraped via pandas.read_html)
  3. Russell 1000 list (Wikipedia)
  4. Static fallback (config.FALLBACK_UNIVERSE) if Wikipedia fails

Cached to output/universe_cache.json for UNIVERSE_CACHE_DAYS days.
"""
from __future__ import annotations
import json
import time
from pathlib import Path
from typing import List

import config

_CACHE_FILE = Path(config.OUTPUT_DIR) / "universe_cache.json"
Path(config.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────────────────────
# Cache
# ─────────────────────────────────────────────────────────────
def _load_cache() -> List[str] | None:
    if not _CACHE_FILE.exists():
        return None
    try:
        raw = json.loads(_CACHE_FILE.read_text())
        age_days = (time.time() - raw.get("_ts", 0)) / 86400
        if age_days < config.UNIVERSE_CACHE_DAYS:
            tickers = raw.get("tickers", [])
            if tickers:
                return tickers
    except Exception:
        pass
    return None


def _save_cache(tickers: List[str]) -> None:
    try:
        _CACHE_FILE.write_text(json.dumps({
            "_ts": time.time(),
            "count": len(tickers),
            "tickers": tickers,
        }))
    except Exception as e:
        print(f"  [universe] cache save failed: {e}")


# ─────────────────────────────────────────────────────────────
# Sources
# ─────────────────────────────────────────────────────────────
_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
       "AppleWebKit/537.36 (KHTML, like Gecko) "
       "Chrome/124.0.0.0 Safari/537.36")


def _fetch_html(url: str) -> str | None:
    """Fetch a Wikipedia page with a browser User-Agent (avoids 403)."""
    try:
        import requests
        r = requests.get(url, headers={"User-Agent": _UA}, timeout=15)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"  [universe] HTTP fetch failed for {url}: {e}")
        return None


def _fetch_sp500() -> List[str]:
    html_text = _fetch_html(config.SP500_URL)
    if not html_text:
        return []
    try:
        import pandas as pd
        from io import StringIO
        tables = pd.read_html(StringIO(html_text))
        df = tables[0]
        col = "Symbol" if "Symbol" in df.columns else df.columns[0]
        syms = [str(s).strip().upper().replace(".", "-") for s in df[col].tolist()]
        return [s for s in syms if s and s.isascii() and len(s) <= 6]
    except Exception as e:
        print(f"  [universe] S&P 500 parse failed: {e}")
        return []


def _fetch_russell1000() -> List[str]:
    html_text = _fetch_html(config.RUSSELL_URL)
    if not html_text:
        return []
    try:
        import pandas as pd
        from io import StringIO
        tables = pd.read_html(StringIO(html_text))
        for df in tables:
            cols = [str(c) for c in df.columns]
            for candidate in ("Symbol", "Ticker", "Ticker symbol"):
                if candidate in cols:
                    syms = [str(s).strip().upper().replace(".", "-")
                            for s in df[candidate].tolist()]
                    syms = [s for s in syms if s and s.isascii() and len(s) <= 6]
                    if len(syms) > 100:
                        return syms
        return []
    except Exception as e:
        print(f"  [universe] Russell 1000 parse failed: {e}")
        return []


def _fetch_av_movers() -> List[str]:
    """Pull tickers from AV TOP_GAINERS_LOSERS (cached in alphavantage_client)."""
    try:
        import alphavantage_client as av
        data = av.get_top_gainers_losers()
        if not data:
            return []
        tickers = set()
        for bucket in ("top_gainers", "most_actively_traded"):
            for row in data.get(bucket, []):
                t = str(row.get("ticker", "")).strip().upper()
                if t:
                    tickers.add(t)
        return sorted(tickers)
    except Exception as e:
        print(f"  [universe] AV movers fetch failed: {e}")
        return []


# ─────────────────────────────────────────────────────────────
# Public
# ─────────────────────────────────────────────────────────────
def build_universe(force_refresh: bool = False) -> List[str]:
    """Return the deduped ticker universe. Uses cache when fresh."""
    if not force_refresh:
        cached = _load_cache()
        if cached:
            print(f"  [universe] Using cached universe: {len(cached)} tickers")
            # Still add AV movers on top (they change daily)
            movers = _fetch_av_movers()
            merged = sorted(set(cached) | set(movers))
            return merged[: config.UNIVERSE_CAP]

    print("  [universe] Building fresh universe...")
    sp = _fetch_sp500()
    print(f"  [universe] S&P 500: {len(sp)} tickers")
    ru = _fetch_russell1000()
    print(f"  [universe] Russell 1000: {len(ru)} tickers")
    mv = _fetch_av_movers()
    print(f"  [universe] AV movers: {len(mv)} tickers")

    combined = set(sp) | set(ru) | set(mv)
    if len(combined) < 100:
        print("  [universe] Combined < 100 — using fallback list")
        combined |= set(config.FALLBACK_UNIVERSE)

    tickers = sorted(t for t in combined if t and t.isascii())
    tickers = tickers[: config.UNIVERSE_CAP]
    _save_cache(tickers)
    print(f"  [universe] Final universe: {len(tickers)} tickers")
    return tickers


if __name__ == "__main__":
    u = build_universe(force_refresh=True)
    print(f"Total: {len(u)}")
    print("First 20:", u[:20])