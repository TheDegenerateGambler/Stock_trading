"""
config.py — DayTrade Picker configuration.

► PUT YOUR ALPHA VANTAGE API KEY HERE (or set env var AV_API_KEY):
"""
import os

# ─────────────────────────────────────────────────────────────
# Alpha Vantage
# ─────────────────────────────────────────────────────────────
AV_API_KEY  = os.getenv("AV_API_KEY", "PASTE_YOUR_KEY_HERE")
AV_BASE_URL = "https://www.alphavantage.co/query"
AV_ENABLED  = bool(AV_API_KEY and AV_API_KEY != "PASTE_YOUR_KEY_HERE")

# Free tier: 25 calls/day, 5 calls/min max
# Budget plan: 15 morning + 8 midday + 2 buffer = 25
AV_DAILY_BUDGET     = 25
AV_CALLS_PER_MIN    = 5   # stay under free tier rate limit

# ─────────────────────────────────────────────────────────────
# Scanner settings
# ─────────────────────────────────────────────────────────────
TOP_N_PICKS         = 10      # final picks to display
SCAN_CANDIDATES     = 20      # how many gainers/actives to score
REFRESH_INTERVAL    = 30      # minutes between full scans
WALTER_REFRESH_MIN  = 5       # minutes between RSS refresh
MAX_WALTER_ITEMS    = 30      # headlines to show in sidebar

# Scoring thresholds
RSI_OVERSOLD        = 35
RSI_OVERBOUGHT      = 65
RVOL_HIGH           = 2.0     # relative volume threshold
MIN_PRICE           = 5.0     # skip penny stocks
MIN_AVG_VOLUME      = 500_000 # min avg daily volume

# Risk/reward
ATR_STOP_MULT       = 1.0     # stop = entry ± 1×ATR
ATR_TARGET_MULT     = 2.0     # target = entry ± 2×ATR (2:1 R:R)

# ─────────────────────────────────────────────────────────────
# HTTP server
# ─────────────────────────────────────────────────────────────
HTTP_PORT           = 8766    # different from Alphabrowser (8765)
OUTPUT_DIR          = "output"

# ─────────────────────────────────────────────────────────────
# Walter Bloomberg RSS
# ─────────────────────────────────────────────────────────────
WALTER_BLOOMBERG_RSS = "https://feeds.feedburner.com/WalterBloombergMacro"
WALTER_BLOOMBERG_ALT = "https://walter-bloomberg.com/feed/"  # fallback

# ─────────────────────────────────────────────────────────────
# Market regime tickers (yfinance, free)
# ─────────────────────────────────────────────────────────────
REGIME_TICKERS = {
    "SPY": "S&P 500",
    "QQQ": "NASDAQ",
    "IWM": "Russell 2000",
    "VIX": "^VIX",
}
VIX_TICKER          = "^VIX"
VIX_HIGH_THRESHOLD  = 20.0    # VIX > 20 = elevated risk → tighter stops
VIX_EXTREME         = 30.0    # VIX > 30 = extreme fear → skip longs