"""
config.py — Swing Options Scanner configuration.

Purpose:
  Scan the market for 2–4 week swing trade options (calls & puts) that
  fit a small account budget (default $110 USD ≈ $153 CAD).

Filters:
  - Stock price $10–$100 (keeps contracts affordable)
  - Avg volume > 5M (liquidity)
  - No earnings in the hold window (avoid IV crush)
  - Options: OI > 500, volume > 50, spread <= 15% of mid
  - Delta 0.30–0.50 (slightly OTM)

Ranks setups by composite score:
  Trend + Momentum + Volume + Sentiment + Options liquidity + Budget fit
"""
from __future__ import annotations
import os

# ─────────────────────────────────────────────────────────────
# Budget (default $110 USD ≈ $153 CAD @ ~0.72)
# ─────────────────────────────────────────────────────────────
BUDGET_USD          = 110      # target contract cost cap
MAX_CONTRACT_COST   = 150      # allow small overshoot
CAD_TO_USD_RATE     = 0.72     # for display only

# ─────────────────────────────────────────────────────────────
# Direction — scan both by default
# ─────────────────────────────────────────────────────────────
DIRECTION = "BOTH"   # "CALL" | "PUT" | "BOTH"

# ─────────────────────────────────────────────────────────────
# Universe filters
# ─────────────────────────────────────────────────────────────
PRICE_MIN           = 10.0
PRICE_MAX           = 100.0
MIN_AVG_VOLUME      = 5_000_000
UNIVERSE_CAP        = 1200

# ─────────────────────────────────────────────────────────────
# Options selection — swing timeframe
# ─────────────────────────────────────────────────────────────
DTE_MIN             = 21       # 3 weeks
DTE_MAX             = 45       # ~6.5 weeks
DELTA_MIN           = 0.30
DELTA_MAX           = 0.50
MIN_OI              = 500
MIN_VOLUME          = 50
MAX_SPREAD_PCT      = 0.15

# ─────────────────────────────────────────────────────────────
# Earnings avoidance
# ─────────────────────────────────────────────────────────────
SKIP_EARNINGS_DAYS  = 30       # skip if earnings within N days

# ─────────────────────────────────────────────────────────────
# Trade rules (attached to each pick)
# ─────────────────────────────────────────────────────────────
TARGET_1_PCT        = 0.50     # +50% profit target #1
TARGET_2_PCT        = 1.00     # +100% profit target #2
STOP_LOSS_PCT       = 0.40     # -40% stop loss
TIME_STOP_DAYS      = 14       # exit if no move within 2 weeks

# ─────────────────────────────────────────────────────────────
# Scoring weights (composite score 0–100)
# ─────────────────────────────────────────────────────────────
SCORE_WEIGHTS = {
    "trend":       30,   # price vs 20/50 EMA, EMA stack
    "momentum":    20,   # RSI in sweet spot + MACD
    "volume":      15,   # RVOL, avg vol
    "sentiment":   15,   # AV NEWS_SENTIMENT
    "liquidity":   10,   # OI + spread
    "budget_fit":  10,   # cheaper = more upside per $
}

TRADE_THRESHOLD_SCORE = 50   # only surface picks scoring >= 50

# ─────────────────────────────────────────────────────────────
# Alpha Vantage (reuses key from premarket_scanner if set)
# ─────────────────────────────────────────────────────────────
AV_API_KEY  = os.getenv("AV_API_KEY", "PASTE_YOUR_KEY_HERE")
AV_BASE_URL = "https://www.alphavantage.co/query"
AV_ENABLED  = bool(AV_API_KEY and AV_API_KEY != "PASTE_YOUR_KEY_HERE")

AV_DAILY_BUDGET  = 25     # free tier limit
AV_CALLS_PER_MIN = 5

# ─────────────────────────────────────────────────────────────
# Universe sources (reuse from premarket_scanner)
# ─────────────────────────────────────────────────────────────
UNIVERSE_CACHE_DAYS = 7
SP500_URL   = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
RUSSELL_URL = "https://en.wikipedia.org/wiki/Russell_1000_Index"

FALLBACK_UNIVERSE = [
    # Mid-price liquid names that fit $10-$100 range
    "AMD","INTC","F","BAC","T","VZ","PFE","KO","PEP","CSCO",
    "GM","UBER","LYFT","SNAP","PINS","SOFI","PLTR","HOOD","AFRM","UPST",
    "COIN","RIVN","LCID","NIO","XPEV","LI","BABA","JD","PDD","DKNG",
    "CVNA","GME","AMC","BB","NOK","SNAP","RBLX","ROKU","SPOT","ZM",
    "PYPL","SQ","SHOP","ABNB","DASH","MRO","OXY","XOM","CVX","HAL",
    "SLB","FCX","AA","X","CLF","MU","MRVL","ON","STX","WDC",
    "DELL","HPQ","IBM","ORCL","CRM","NOW","WBA","CVS","TGT","KR",
    "M","JWN","BBY","LOW","HD","DIS","NFLX","PARA","WBD","T",
]

# ─────────────────────────────────────────────────────────────
# Runtime
# ─────────────────────────────────────────────────────────────
CONCURRENT_WORKERS = 12
YF_TIMEOUT_SEC     = 15
TOP_N              = 10       # top picks to output

# ─────────────────────────────────────────────────────────────
# HTTP + output
# ─────────────────────────────────────────────────────────────
HTTP_PORT  = 8769

_HERE = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(_HERE, "output")

# Path to premarket_scanner's cboe_client (reused)
OPTIONS_DAYTRADER_DIR = os.path.abspath(os.path.join(
    _HERE, "..", "options_daytrader"))
PREMARKET_SCANNER_DIR = os.path.abspath(os.path.join(
    _HERE, "..", "premarket_scanner"))
DAYTRADE_PICKER_DIR   = os.path.abspath(os.path.join(
    _HERE, "..", "daytrade_picker"))

# Risk-free rate (for BS fallback if CBOE misses greeks)
RISK_FREE_RATE = 0.05