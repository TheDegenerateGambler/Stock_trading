"""
options_ranker.py — Pick the single best contract for a given direction + score.

Strategy:
  1. First pass: strictly-liquid contracts within delta target.
  2. If none, fall back to closest-to-ATM contract regardless of liquidity
     (with a low_liquidity=True flag).
  3. Score = liquidity * spread_tightness * proximity_to_delta_center.

Then attaches entry / stop / target based on underlying ATR + contract delta.
"""
from __future__ import annotations
from typing import Dict, List, Optional

import config
import options_chain as chain_mod


def _score_contract(c: Dict) -> float:
    """Higher is better."""
    d = abs(c["delta"])
    target_center = (config.DELTA_MIN + config.DELTA_MAX) / 2.0
    d_penalty = 1.0 - min(1.0, abs(d - target_center) / 0.20)   # 0..1
    liq = min(1.0, c["openInterest"] / 5000.0)
    spread_ok = max(0.0, 1.0 - c["spread_pct"] / config.MAX_SPREAD_PCT)
    return d_penalty * 0.5 + liq * 0.3 + spread_ok * 0.2


def _fallback_atm(contracts: List[Dict], spot: float) -> Optional[Dict]:
    """If no liquid contract passes, pick closest-strike-to-spot with any bid."""
    if not contracts:
        return None
    with_bids = [c for c in contracts if c["mid"] > 0]
    pool = with_bids or contracts
    pool.sort(key=lambda c: abs(c["strike"] - spot))
    if not pool:
        return None
    winner = pool[0]
    winner["low_liquidity"] = True
    return winner


def _attach_levels(pick: Dict, spot: float, atr: float, direction: str) -> Dict:
    """Attach entry/stop/target for the option premium using ATR × |delta|."""
    delta = abs(pick["delta"]) or 0.3
    mid   = pick["mid"] or 0.05

    # Underlying move sizes (in $)
    stop_underlying_move   = atr * config.ATR_STOP_MULT
    target_underlying_move = atr * config.ATR_TARGET_MULT

    # Premium moves ≈ delta × underlying move
    stop_premium_move   = stop_underlying_move   * delta
    target_premium_move = target_underlying_move * delta

    # Cap stop distance at 50% of premium to avoid stops that risk 100% of cost
    max_premium_loss = mid * 0.5
    stop_premium_move = min(stop_premium_move, max_premium_loss)

    stop   = max(0.01, mid - stop_premium_move)
    target = mid + target_premium_move

    # Suggested max entry: 5% over mid to allow for slippage
    entry_max = round(mid * 1.05, 2)

    risk_per_ct = round((mid - stop) * 100, 2)   # $ per contract
    reward_per_ct = round((target - mid) * 100, 2)
    rr = round(reward_per_ct / risk_per_ct, 2) if risk_per_ct > 0 else 0.0

    pick["entry_max"]     = entry_max
    pick["stop"]           = round(stop, 2)
    pick["target"]         = round(target, 2)
    pick["risk_per_contract"]   = risk_per_ct
    pick["reward_per_contract"] = reward_per_ct
    pick["risk_reward"]    = rr
    return pick


def pick_best(ticker: str, spot: float, atr: float,
              direction: str, is_etf: bool) -> Optional[Dict]:
    """
    Returns the best contract dict enriched with entry/stop/target,
    or None if the chain is entirely unavailable.
    """
    if direction not in ("CALL", "PUT"):
        return None

    all_contracts = chain_mod.get_contracts(ticker, spot, direction, is_etf)
    if not all_contracts:
        return None

    liquid = chain_mod.filter_liquid(all_contracts)
    if liquid:
        liquid.sort(key=_score_contract, reverse=True)
        winner = dict(liquid[0])
        winner["low_liquidity"] = False
    else:
        winner = _fallback_atm(all_contracts, spot)
        if not winner:
            return None

    return _attach_levels(winner, spot, atr, direction)