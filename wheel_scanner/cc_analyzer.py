"""
Covered Call analyzer.

Given a stock snapshot, an optional cost basis, and its call option chain,
find the best OTM covered call candidate and rank it.

Supports:
  - Monthly mode (default) and Weekly mode (--weekly)
  - Currency-aware commissions (CAD $6.95 / USD $1.25 on NBDB)
  - Two operating modes:
      "position"   — user owns 100+ shares at a known cost basis
      "buy-write"  — no existing position; cost basis = current price
"""
from __future__ import annotations

import math
from dataclasses import dataclass, asdict
from typing import Optional

import pandas as pd

from config import (
    CALL_STRIKE_OTM_MAX_PCT,
    CALL_STRIKE_OTM_MIN_PCT,
    CC_MAX_DTE,
    CC_MIN_DTE,
    CC_WEIGHT_ANNUALIZED_YIELD,
    CC_WEIGHT_DOWNSIDE_PROTECTION,
    CC_WEIGHT_LIQUIDITY,
    CC_WEIGHT_UPSIDE_ROOM,
    CONTRACT_SIZE,
    DEFAULT_USD_CAD,
    MAX_BID_ASK_SPREAD_PCT,
    MIN_BID,
    MIN_OPEN_INTEREST,
    OPTION_COMMISSION_PER_CONTRACT,
    OPTION_COMMISSION_PER_CONTRACT_USD,
    WEEKLY_MAX_BID_ASK_SPREAD_PCT,
    WEEKLY_MAX_DTE,
    WEEKLY_MIN_BID,
    WEEKLY_MIN_DTE,
    WEEKLY_MIN_OPEN_INTEREST,
)
from data_provider import (
    StockSnapshot,
    dte_from_expiration,
    get_call_chain,
    get_option_expirations,
    polite_sleep,
)


@dataclass
class CCCandidate:
    ticker: str
    name: str
    currency: str
    mode: str
    stock_price: float
    cost_basis: float
    shares_held: int
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
    premium_cad: float               # native currency (schema kept)
    net_premium_cad: float           # native currency
    premium_in_cad: float            # CAD-equivalent
    net_premium_in_cad: float        # CAD-equivalent
    static_yield_pct: float
    static_yield_ann_pct: float
    if_called_profit_cad: float      # native currency
    if_called_profit_in_cad: float   # CAD-equivalent
    if_called_yield_pct: float
    if_called_yield_ann_pct: float
    downside_protection_pct: float
    upside_room_pct: float
    spread_pct: float
    score: float
    weekly: bool
    notes: str

    def to_row(self) -> dict:
        return asdict(self)


def find_best_call_for_expiration(
    snapshot: StockSnapshot,
    expiration: str,
    calls: pd.DataFrame,
    cost_basis: Optional[float],
    shares_held: int,
    mode: str,
    weekly: bool = False,
    usd_cad: float = DEFAULT_USD_CAD,
) -> Optional[CCCandidate]:
    """From a calls DataFrame, pick the best OTM call for a covered call."""
    dte = dte_from_expiration(expiration)
    min_dte = WEEKLY_MIN_DTE if weekly else CC_MIN_DTE
    max_dte = WEEKLY_MAX_DTE if weekly else CC_MAX_DTE
    if dte < min_dte or dte > max_dte:
        return None

    price = snapshot.price
    if price <= 0:
        return None

    if cost_basis is None or cost_basis <= 0:
        cost_basis = price

    currency = (snapshot.currency or "CAD").upper()
    is_usd = currency == "USD"
    commission = OPTION_COMMISSION_PER_CONTRACT_USD if is_usd else OPTION_COMMISSION_PER_CONTRACT
    fx = usd_cad if is_usd else 1.0

    # OTM window above current price
    min_strike = price * (1.0 + CALL_STRIKE_OTM_MIN_PCT)
    max_strike = price * (1.0 + CALL_STRIKE_OTM_MAX_PCT)

    # Never allow strike below cost basis (avoid locking in a loss on assignment)
    strike_floor = max(min_strike, cost_basis)

    # Threshold selection
    min_oi = WEEKLY_MIN_OPEN_INTEREST if weekly else MIN_OPEN_INTEREST
    max_spread = WEEKLY_MAX_BID_ASK_SPREAD_PCT if weekly else MAX_BID_ASK_SPREAD_PCT
    min_bid = WEEKLY_MIN_BID if weekly else MIN_BID

    df = calls.copy()
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

    df = df[df["strike"] >= strike_floor]
    df = df[df["strike"] <= max_strike]
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

    df["premium"] = df["mid"] * CONTRACT_SIZE
    df["net_premium"] = df["premium"] - commission
    df = df[df["net_premium"] > 0]
    if df.empty:
        return None

    df["if_called_profit"] = (df["strike"] - cost_basis) * CONTRACT_SIZE + df["net_premium"]
    cost_capital = cost_basis * CONTRACT_SIZE
    df["static_yield"] = df["net_premium"] / cost_capital
    df["static_yield_ann"] = df["static_yield"] * (365.0 / max(dte, 1))
    df["if_called_yield"] = df["if_called_profit"] / cost_capital
    df["if_called_yield_ann"] = df["if_called_yield"] * (365.0 / max(dte, 1))

    row = df.sort_values("if_called_yield_ann", ascending=False).iloc[0]

    strike = float(row["strike"])
    bid = float(row["bid"])
    ask = float(row["ask"])
    mid = float(row["mid"])
    premium = float(row["premium"])
    net_premium = float(row["net_premium"])
    if_called_profit = float(row["if_called_profit"])

    notes = []
    if weekly:
        notes.append("weekly")
    if is_usd:
        notes.append(f"USD (fx {usd_cad:.3f})")
    if snapshot.dividend_yield:
        notes.append(f"div yield {snapshot.dividend_yield * 100:.1f}%")
    if snapshot.avg_volume and snapshot.avg_volume < 200_000:
        notes.append("low avg vol")
    if mode == "position" and cost_basis > price:
        notes.append(f"underwater: basis ${cost_basis:.2f} > spot ${price:.2f}")
    if mode == "buy-write":
        notes.append("buy-write")

    return CCCandidate(
        ticker=snapshot.ticker,
        name=snapshot.name,
        currency=currency,
        mode=mode,
        stock_price=price,
        cost_basis=float(cost_basis),
        shares_held=int(shares_held),
        expiration=expiration,
        dte=dte,
        strike=strike,
        bid=bid,
        ask=ask,
        mid=mid,
        open_interest=int(row["openInterest"]),
        volume=int(row["volume"]),
        implied_vol=float(row["impliedVolatility"]),
        otm_pct=(strike - price) / price if price > 0 else 0.0,
        premium_cad=premium,
        net_premium_cad=net_premium,
        premium_in_cad=premium * fx,
        net_premium_in_cad=net_premium * fx,
        static_yield_pct=float(row["static_yield"]),
        static_yield_ann_pct=float(row["static_yield_ann"]),
        if_called_profit_cad=if_called_profit,
        if_called_profit_in_cad=if_called_profit * fx,
        if_called_yield_pct=float(row["if_called_yield"]),
        if_called_yield_ann_pct=float(row["if_called_yield_ann"]),
        downside_protection_pct=net_premium / (price * CONTRACT_SIZE) if price > 0 else 0.0,
        upside_room_pct=(strike - price) / price if price > 0 else 0.0,
        spread_pct=float(row["spread_pct"]),
        score=0.0,
        weekly=weekly,
        notes="; ".join(notes),
    )


def find_best_call_across_expirations(
    snapshot: StockSnapshot,
    cost_basis: Optional[float] = None,
    shares_held: int = 100,
    mode: str = "buy-write",
    weekly: bool = False,
    usd_cad: float = DEFAULT_USD_CAD,
) -> Optional[CCCandidate]:
    """Scan all valid expirations for the best CC on this stock."""
    expirations = get_option_expirations(snapshot.ticker)
    if not expirations:
        return None

    min_dte = WEEKLY_MIN_DTE if weekly else CC_MIN_DTE
    max_dte = WEEKLY_MAX_DTE if weekly else CC_MAX_DTE

    best: Optional[CCCandidate] = None
    for exp in expirations:
        try:
            dte = dte_from_expiration(exp)
        except Exception:
            continue
        if dte < min_dte or dte > max_dte:
            continue

        calls = get_call_chain(snapshot.ticker, exp)
        polite_sleep(0.3)
        if calls is None:
            continue

        cand = find_best_call_for_expiration(
            snapshot, exp, calls, cost_basis, shares_held, mode,
            weekly=weekly, usd_cad=usd_cad,
        )
        if cand is None:
            continue
        if best is None or cand.if_called_yield_ann_pct > best.if_called_yield_ann_pct:
            best = cand

    return best


def score_cc_candidates(candidates: list[CCCandidate]) -> list[CCCandidate]:
    """Assign 0-100 composite score to each CC candidate."""
    if not candidates:
        return candidates

    ann_yields = [c.if_called_yield_ann_pct for c in candidates]
    ois = [c.open_interest for c in candidates]
    spreads = [c.spread_pct for c in candidates]
    upsides = [c.upside_room_pct for c in candidates]
    protections = [c.downside_protection_pct for c in candidates]

    def norm(v, arr, higher_is_better=True):
        if not arr:
            return 0.0
        lo, hi = min(arr), max(arr)
        if hi - lo < 1e-9:
            return 0.5
        n = (v - lo) / (hi - lo)
        return n if higher_is_better else 1.0 - n

    for c in candidates:
        yield_sub = norm(c.if_called_yield_ann_pct, ann_yields, True)
        oi_sub = norm(c.open_interest, ois, True)
        spread_sub = norm(c.spread_pct, spreads, False)
        liquidity_sub = 0.6 * oi_sub + 0.4 * spread_sub
        upside_sub = norm(c.upside_room_pct, upsides, True)
        protection_sub = norm(c.downside_protection_pct, protections, True)

        composite = (
            CC_WEIGHT_ANNUALIZED_YIELD * yield_sub
            + CC_WEIGHT_LIQUIDITY * liquidity_sub
            + CC_WEIGHT_UPSIDE_ROOM * upside_sub
            + CC_WEIGHT_DOWNSIDE_PROTECTION * protection_sub
        )
        c.score = round(composite * 100.0, 2)

    return sorted(candidates, key=lambda x: x.score, reverse=True)
