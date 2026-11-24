"""
Wheel analyzer: given a stock snapshot and its option chain, find the best
cash-secured put candidate for our budget and rank it.

Supports:
  - Monthly mode (default) — original 20-55 DTE window, CAD watchlist
  - Weekly mode (--weekly) — 4-14 DTE, tighter liquidity thresholds, US or TSX
  - Currency-aware commissions (CAD $6.95, USD $1.25 for NBDB)
  - CAD-denominated budget converted to native currency for affordability check
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Optional

import math
import pandas as pd

from config import (
    ACCOUNT_BUDGET_CAD,
    CONTRACT_SIZE,
    DEFAULT_USD_CAD,
    MAX_BID_ASK_SPREAD_PCT,
    MIN_BID,
    MIN_DTE,
    MAX_DTE,
    MIN_OPEN_INTEREST,
    OPTION_COMMISSION_PER_CONTRACT,
    OPTION_COMMISSION_PER_CONTRACT_USD,
    PUT_STRIKE_OTM_MAX_PCT,
    PUT_STRIKE_OTM_MIN_PCT,
    WEEKLY_MIN_DTE,
    WEEKLY_MAX_DTE,
    WEEKLY_MIN_OPEN_INTEREST,
    WEEKLY_MAX_BID_ASK_SPREAD_PCT,
    WEEKLY_MIN_BID,
    WEIGHT_AFFORDABILITY,
    WEIGHT_ANNUALIZED_YIELD,
    WEIGHT_LIQUIDITY,
    WEIGHT_SAFETY,
)
from data_provider import (
    StockSnapshot,
    dte_from_expiration,
    get_option_expirations,
    get_put_chain,
    polite_sleep,
)


@dataclass
class WheelCandidate:
    ticker: str
    name: str
    stock_price: float
    currency: str                # "CAD" or "USD"
    expiration: str
    dte: int
    strike: float
    bid: float
    ask: float
    mid: float
    open_interest: int
    volume: int
    implied_vol: float
    otm_pct: float
    collateral_cad: float        # collateral in native currency (name kept for schema stability)
    premium_cad: float           # premium in native currency
    net_premium_cad: float       # net premium after commission
    collateral_in_cad: float     # collateral expressed in CAD (for cross-currency comparison)
    net_premium_in_cad: float    # net premium expressed in CAD
    net_yield_pct: float
    annualized_yield_pct: float
    breakeven: float
    downside_cushion_pct: float
    spread_pct: float
    score: float
    weekly: bool
    notes: str

    def to_row(self) -> dict:
        return asdict(self)


def find_best_put_for_expiration(
    snapshot: StockSnapshot,
    expiration: str,
    puts: pd.DataFrame,
    weekly: bool = False,
    budget: float = ACCOUNT_BUDGET_CAD,
    usd_cad: float = DEFAULT_USD_CAD,
) -> Optional[WheelCandidate]:
    """From a puts DataFrame, pick the best OTM put that fits the budget."""
    dte = dte_from_expiration(expiration)
    min_dte = WEEKLY_MIN_DTE if weekly else MIN_DTE
    max_dte = WEEKLY_MAX_DTE if weekly else MAX_DTE
    if dte < min_dte or dte > max_dte:
        return None

    price = snapshot.price
    if price <= 0:
        return None

    currency = (snapshot.currency or "CAD").upper()
    is_usd = currency == "USD"
    commission = OPTION_COMMISSION_PER_CONTRACT_USD if is_usd else OPTION_COMMISSION_PER_CONTRACT

    # Budget is in CAD; convert to native currency to bound the strike
    budget_native = (budget / usd_cad) if is_usd else budget
    max_affordable_strike = budget_native / CONTRACT_SIZE

    min_strike = price * (1.0 - PUT_STRIKE_OTM_MAX_PCT)
    max_strike = price * (1.0 - PUT_STRIKE_OTM_MIN_PCT)

    min_oi = WEEKLY_MIN_OPEN_INTEREST if weekly else MIN_OPEN_INTEREST
    max_spread = WEEKLY_MAX_BID_ASK_SPREAD_PCT if weekly else MAX_BID_ASK_SPREAD_PCT
    min_bid = WEEKLY_MIN_BID if weekly else MIN_BID

    df = puts.copy()
    for col, default in [
        ("bid", 0.0), ("ask", 0.0), ("lastPrice", 0.0),
        ("openInterest", 0), ("volume", 0), ("impliedVolatility", 0.0),
    ]:
        if col not in df.columns:
            df[col] = default
    df["bid"] = df["bid"].fillna(0.0)
    df["ask"] = df["ask"].fillna(0.0)
    df["openInterest"] = df["openInterest"].fillna(0).astype(int)
    df["volume"] = df["volume"].fillna(0).astype(int)
    df["impliedVolatility"] = df["impliedVolatility"].fillna(0.0)

    df = df[df["strike"] >= min_strike]
    df = df[df["strike"] <= max_strike]
    df = df[df["strike"] <= max_affordable_strike]
    df = df[df["bid"] >= min_bid]
    df = df[df["openInterest"] >= min_oi]
    if df.empty:
        return None

    df["mid"] = (df["bid"] + df["ask"]) / 2.0
    df = df[df["mid"] > 0]
    df["spread_pct"] = (df["ask"] - df["bid"]).clip(lower=0) / df["mid"].replace(0, math.nan)
    df["spread_pct"] = df["spread_pct"].fillna(1.0)
    df = df[df["spread_pct"] <= max_spread]
    if df.empty:
        return None

    df["collateral"] = df["strike"] * CONTRACT_SIZE
    df["premium"] = df["mid"] * CONTRACT_SIZE
    df["net_premium"] = df["premium"] - commission
    df = df[df["net_premium"] > 0]
    if df.empty:
        return None
    df["net_yield"] = df["net_premium"] / df["collateral"]
    df["ann_yield"] = df["net_yield"] * (365.0 / max(dte, 1))

    row = df.sort_values("ann_yield", ascending=False).iloc[0]

    strike = float(row["strike"])
    bid = float(row["bid"])
    ask = float(row["ask"])
    mid = float(row["mid"])
    breakeven = strike - mid
    downside_cushion = (price - breakeven) / price if price > 0 else 0.0

    collateral_native = float(row["collateral"])
    premium_native = float(row["premium"])
    net_premium_native = float(row["net_premium"])

    # CAD-equivalents for cross-currency comparison
    fx = usd_cad if is_usd else 1.0
    collateral_cad_eq = collateral_native * fx
    net_premium_cad_eq = net_premium_native * fx

    notes = []
    if weekly:
        notes.append("weekly")
    if is_usd:
        notes.append(f"USD (fx {usd_cad:.3f})")
    if snapshot.dividend_yield:
        notes.append(f"div yield {snapshot.dividend_yield * 100:.1f}%")
    if snapshot.avg_volume and snapshot.avg_volume < 200_000:
        notes.append("low avg vol")

    return WheelCandidate(
        ticker=snapshot.ticker,
        name=snapshot.name,
        stock_price=price,
        currency=currency,
        expiration=expiration,
        dte=dte,
        strike=strike,
        bid=bid,
        ask=ask,
        mid=mid,
        open_interest=int(row["openInterest"]),
        volume=int(row["volume"]),
        implied_vol=float(row["impliedVolatility"]),
        otm_pct=(price - strike) / price,
        collateral_cad=collateral_native,
        premium_cad=premium_native,
        net_premium_cad=net_premium_native,
        collateral_in_cad=collateral_cad_eq,
        net_premium_in_cad=net_premium_cad_eq,
        net_yield_pct=float(row["net_yield"]),
        annualized_yield_pct=float(row["ann_yield"]),
        breakeven=breakeven,
        downside_cushion_pct=downside_cushion,
        spread_pct=float(row["spread_pct"]),
        score=0.0,
        weekly=weekly,
        notes="; ".join(notes),
    )


def find_best_put_across_expirations(
    snapshot: StockSnapshot,
    weekly: bool = False,
    budget: float = ACCOUNT_BUDGET_CAD,
    usd_cad: float = DEFAULT_USD_CAD,
) -> Optional[WheelCandidate]:
    """Scan all valid expirations and return the best CSP for this stock."""
    expirations = get_option_expirations(snapshot.ticker)
    if not expirations:
        return None

    min_dte = WEEKLY_MIN_DTE if weekly else MIN_DTE
    max_dte = WEEKLY_MAX_DTE if weekly else MAX_DTE

    best: Optional[WheelCandidate] = None
    for exp in expirations:
        try:
            dte = dte_from_expiration(exp)
        except Exception:
            continue
        if dte < min_dte or dte > max_dte:
            continue

        puts = get_put_chain(snapshot.ticker, exp)
        polite_sleep(0.3)
        if puts is None:
            continue

        cand = find_best_put_for_expiration(
            snapshot, exp, puts, weekly=weekly, budget=budget, usd_cad=usd_cad
        )
        if cand is None:
            continue
        if best is None or cand.annualized_yield_pct > best.annualized_yield_pct:
            best = cand

    return best


def score_candidates(candidates: list[WheelCandidate]) -> list[WheelCandidate]:
    """Assign a composite 0-100 score to each candidate."""
    if not candidates:
        return candidates

    ann_yields = [c.annualized_yield_pct for c in candidates]
    ois = [c.open_interest for c in candidates]
    spreads = [c.spread_pct for c in candidates]
    cushions = [c.downside_cushion_pct for c in candidates]
    # Use CAD-equivalent collateral so USD & CAD names compete on the same axis
    collaterals = [c.collateral_in_cad for c in candidates]

    def norm(v, arr, higher_is_better=True):
        if not arr:
            return 0.0
        lo, hi = min(arr), max(arr)
        if hi - lo < 1e-9:
            return 0.5
        n = (v - lo) / (hi - lo)
        return n if higher_is_better else 1.0 - n

    for c in candidates:
        yield_sub = norm(c.annualized_yield_pct, ann_yields, True)
        oi_sub = norm(c.open_interest, ois, True)
        spread_sub = norm(c.spread_pct, spreads, False)
        liquidity_sub = 0.6 * oi_sub + 0.4 * spread_sub
        safety_sub = norm(c.downside_cushion_pct, cushions, True)
        afford_sub = norm(c.collateral_in_cad, collaterals, False)

        composite = (
            WEIGHT_ANNUALIZED_YIELD * yield_sub
            + WEIGHT_LIQUIDITY * liquidity_sub
            + WEIGHT_SAFETY * safety_sub
            + WEIGHT_AFFORDABILITY * afford_sub
        )
        c.score = round(composite * 100.0, 2)

    return sorted(candidates, key=lambda x: x.score, reverse=True)
