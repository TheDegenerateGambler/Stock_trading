"""
trade_builder.py — Attach trade plan (entry/target/stop) to each pick.

Adds these fields to a pick:
  - entry_max_premium:  suggested max entry price (mid × 1.05 for slippage)
  - break_even_stock:   stock price where option = 0 P&L at expiry
  - target_1_premium:   +50% profit target
  - target_2_premium:   +100% profit target
  - stop_premium:       -40% stop loss
  - profit_target_1_$:  $ gain at target 1 per contract
  - profit_target_2_$:  $ gain at target 2 per contract
  - risk_$_per_ct:      $ loss at stop per contract
  - reward_risk:        R:R at target 1
  - stock_move_needed_pct: % move in underlying to break even
  - time_stop_date:     ISO date for time-based exit
"""
from __future__ import annotations
from datetime import date, timedelta
from typing import Dict

import config


def build(pick: Dict, spot: float, direction: str) -> Dict:
    """Attach a complete trade plan to a pick dict (in place + returned)."""
    mid    = float(pick.get("mid", 0)) or 0.0
    strike = float(pick.get("strike", 0)) or 0.0

    # Entry: 5% over mid to allow slippage
    entry_max = round(mid * 1.05, 2)

    # Profit targets & stop (percentages of premium)
    target_1 = round(mid * (1 + config.TARGET_1_PCT), 2)
    target_2 = round(mid * (1 + config.TARGET_2_PCT), 2)
    stop     = round(max(0.01, mid * (1 - config.STOP_LOSS_PCT)), 2)

    # $ per contract (options are 100 shares)
    profit_1 = round((target_1 - mid) * 100, 2)
    profit_2 = round((target_2 - mid) * 100, 2)
    risk     = round((mid - stop) * 100, 2)
    rr       = round(profit_1 / risk, 2) if risk > 0 else 0.0

    # Break-even at expiration
    if direction == "CALL":
        break_even = strike + mid
        stock_move_needed_pct = ((break_even - spot) / spot) * 100 if spot > 0 else 0
    else:  # PUT
        break_even = strike - mid
        stock_move_needed_pct = ((spot - break_even) / spot) * 100 if spot > 0 else 0

    # Time stop
    time_stop = (date.today() + timedelta(days=config.TIME_STOP_DAYS)).isoformat()

    pick["entry_max_premium"]      = entry_max
    pick["break_even_stock"]       = round(break_even, 2)
    pick["stock_move_needed_pct"]  = round(stock_move_needed_pct, 2)
    pick["target_1_premium"]       = target_1
    pick["target_2_premium"]       = target_2
    pick["stop_premium"]           = stop
    pick["profit_target_1_$"]      = profit_1
    pick["profit_target_2_$"]      = profit_2
    pick["risk_$_per_ct"]          = risk
    pick["reward_risk"]            = rr
    pick["time_stop_date"]         = time_stop
    return pick


if __name__ == "__main__":
    # Test with a fake contract
    sample = {
        "mid": 1.10,
        "strike": 67.50,
        "days_to_expiry": 30,
    }
    result = build(sample, spot=62.40, direction="CALL")
    for k, v in result.items():
        print(f"  {k}: {v}")