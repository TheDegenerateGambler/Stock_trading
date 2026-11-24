"""
unusualwhales_stub.py — Placeholder adapter for Unusual Whales data.

Currently DISABLED (no free public API, no user subscription).

If in the future you obtain an official API key, replace this module with
real fetchers for:
  - options flow / sweeps
  - unusual activity
  - dark pool prints
and wire it into signal_engine.py as an extra bull/bear signal.
"""
from __future__ import annotations
from typing import Dict, Optional

import config


def enabled() -> bool:
    return bool(config.UNUSUAL_WHALES_ENABLED and config.UNUSUAL_WHALES_TOKEN)


def get_flow(ticker: str) -> Optional[Dict]:
    """
    Would return: {
      'net_premium':    +$1.2M,   # calls - puts (last 30 min)
      'sweep_count':    5,
      'unusual_score':  0.75,
      'top_alerts': [ { 'strike': ..., 'expiry': ..., 'side': 'BUY', 'premium': ... } ]
    }
    """
    if not enabled():
        return None
    # TODO: implement once user has UW API access
    return None


def to_signal(flow: Optional[Dict]) -> float:
    """Convert a flow dict to a bull/bear signal in [-1, +1]."""
    if not flow:
        return 0.0
    # Placeholder logic
    net = flow.get("net_premium", 0)
    if net > 500_000:
        return +0.8
    if net > 100_000:
        return +0.4
    if net < -500_000:
        return -0.8
    if net < -100_000:
        return -0.4
    return 0.0