"""
config.py — Options Day Trader configuration.

Session: 9:30 AM – 12:00 PM ET (user trades 9:30–12:00).
Runs every 5 min, always outputs SPY + QQQ picks + top gap-up options play.
"""
from __future__ import annotations
import os

# ─────────────────────────────────────────────────────────────
# Session
# ─────────────────────────────────────────────────────────────
START_HOUR_ET = 9
START_MIN_ET  = 30
STOP_HOUR_ET  = 12
STOP_MIN_ET   = 0
INTERVAL_MIN  = 5    # rescan cadence

# ─────────────────────────────────────────────────────────────
# ETFs always scanned
# ─────────────────────────────────────────────────────────────
ETF_TICKERS = ["SPY", "QQQ"]

# ─────────────────────────────────────────────────────────────
# Signal weights (composite score in [-100, +100])
# ─────────────────────────────────────────────────────────────
SIGNAL_WEIGHTS = {
    "vwap":       20,   # price above/below VWAP
    "ema_cross":  20,   # 9 vs 20 EMA on 5-min
    "rsi":        10,
    "macd":       15,
    "rvol":       10,
    "sentiment":  15,   # AV news sentiment
    "gap":        10,   # gap fill / sustain
}

# Confidence threshold (abs score) — above this we call it a real trade
TRADE_THRESHOLD_SCORE = 35   # ≥35 (bull) or ≤-35 (bear)

# ─────────────────────────────────────────────────────────────
# Options contract selection
# ─────────────────────────────────────────────────────────────
DELTA_MIN = 0.30
DELTA_MAX = 0.45

MIN_OI       = 500
MIN_VOLUME   = 100
MAX_SPREAD_PCT = 0.15   # (ask-bid)/mid <= 15%

# Expiry policy: 0DTE for ETFs, nearest weekly (Friday) for others
ETF_EXPIRY_MODE   = "0DTE"        # 0DTE | NEAREST | NEXT_FRIDAY
OTHER_EXPIRY_MODE = "NEXT_FRIDAY"

# Risk/reward from underlying ATR
ATR_STOP_MULT   = 0.5
ATR_TARGET_MULT = 1.0

# ─────────────────────────────────────────────────────────────
# Data sources
# ─────────────────────────────────────────────────────────────
UNUSUAL_WHALES_ENABLED = False  # set True + creds to enable (stub only)
UNUSUAL_WHALES_TOKEN   = os.getenv("UNUSUAL_WHALES_TOKEN", "")

# Concurrency for scanning candidates
CONCURRENT_WORKERS = 8

# ─────────────────────────────────────────────────────────────
# Premarket seed
# ─────────────────────────────────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
PREMARKET_PICKS_JSON = os.path.abspath(os.path.join(
    _HERE, "..", "premarket_scanner", "output", "premarket_picks.json"))

# ─────────────────────────────────────────────────────────────
# HTTP + output
# ─────────────────────────────────────────────────────────────
HTTP_PORT  = 8768
OUTPUT_DIR = os.path.join(_HERE, "output")

# Risk-free rate (for Black-Scholes fallback)
RISK_FREE_RATE = 0.05