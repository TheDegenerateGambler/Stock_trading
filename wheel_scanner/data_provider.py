"""
Data provider: fetches current stock prices and option chains via yfinance.

yfinance TSX symbols use the ".TO" suffix. Options data on TSX names via
Yahoo Finance is generally available but sometimes sparse or delayed —
always verify with your broker before trading.
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import pandas as pd

try:
    import yfinance as yf
except ImportError as e:
    raise SystemExit(
        "yfinance is required. Install with: pip install -r requirements.txt"
    ) from e


@dataclass
class StockSnapshot:
    ticker: str
    price: float
    currency: str
    name: str
    avg_volume: Optional[float]
    market_cap: Optional[float]
    dividend_yield: Optional[float]


def get_stock_snapshot(ticker: str) -> Optional[StockSnapshot]:
    """Return a lightweight snapshot for a single ticker, or None on failure."""
    try:
        t = yf.Ticker(ticker)
        # fast_info is much quicker and doesn't hammer Yahoo
        fi = t.fast_info

        price = _safe_float(getattr(fi, "last_price", None))
        if price is None or price <= 0:
            # fallback to history
            hist = t.history(period="5d", auto_adjust=False)
            if hist is None or hist.empty:
                return None
            price = float(hist["Close"].iloc[-1])

        currency = getattr(fi, "currency", "CAD") or "CAD"

        # info can be slow / rate limited; try but don't fail
        name = ticker
        div_yield = None
        market_cap = _safe_float(getattr(fi, "market_cap", None))
        avg_volume = _safe_float(getattr(fi, "three_month_average_volume", None))

        try:
            info = t.info or {}
            name = info.get("shortName") or info.get("longName") or ticker
            div_yield = _safe_float(info.get("dividendYield"))
            if market_cap is None:
                market_cap = _safe_float(info.get("marketCap"))
            if avg_volume is None:
                avg_volume = _safe_float(info.get("averageVolume"))
        except Exception:
            pass

        return StockSnapshot(
            ticker=ticker,
            price=float(price),
            currency=currency,
            name=name,
            avg_volume=avg_volume,
            market_cap=market_cap,
            dividend_yield=div_yield,
        )
    except Exception as e:
        print(f"  [warn] failed to fetch {ticker}: {e}")
        return None


def get_option_expirations(ticker: str) -> list[str]:
    """Return a list of option expiration date strings (YYYY-MM-DD) or []."""
    try:
        t = yf.Ticker(ticker)
        return list(t.options or [])
    except Exception as e:
        print(f"  [warn] no option expirations for {ticker}: {e}")
        return []


def get_put_chain(ticker: str, expiration: str) -> Optional[pd.DataFrame]:
    """Return the puts DataFrame for a given expiration, or None."""
    try:
        t = yf.Ticker(ticker)
        chain = t.option_chain(expiration)
        puts = chain.puts
        if puts is None or puts.empty:
            return None
        return puts.copy()
    except Exception as e:
        print(f"  [warn] failed to fetch put chain for {ticker} {expiration}: {e}")
        return None


def get_call_chain(ticker: str, expiration: str) -> Optional[pd.DataFrame]:
    """Return the calls DataFrame for a given expiration, or None."""
    try:
        t = yf.Ticker(ticker)
        chain = t.option_chain(expiration)
        calls = chain.calls
        if calls is None or calls.empty:
            return None
        return calls.copy()
    except Exception as e:
        print(f"  [warn] failed to fetch call chain for {ticker} {expiration}: {e}")
        return None


def dte_from_expiration(expiration: str) -> int:
    """Days to expiration from today (UTC)."""
    exp = datetime.strptime(expiration, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    return max(0, (exp.date() - now.date()).days)


def _safe_float(x) -> Optional[float]:
    try:
        if x is None:
            return None
        v = float(x)
        if math.isnan(v) or math.isinf(v):
            return None
        return v
    except (TypeError, ValueError):
        return None


def polite_sleep(seconds: float = 0.4) -> None:
    """Small delay to avoid hammering Yahoo Finance."""
    time.sleep(seconds)