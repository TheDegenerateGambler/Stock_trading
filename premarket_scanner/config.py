"""
config.py — Premarket Scanner configuration.

Filters (per task spec):
  - gap_pct > 5
  - price > $3
  - premarket_volume > 50,000
  - Keep top 10 by gap_pct DESC

Loop cadence:
  - Every 20 minutes until 9:20 AM ET, then exit.
"""
from __future__ import annotations
import os

# ─────────────────────────────────────────────────────────────
# Alpha Vantage (reuses same key as daytrade_picker if set)
# ─────────────────────────────────────────────────────────────
AV_API_KEY  = os.getenv("AV_API_KEY", "PASTE_YOUR_KEY_HERE")
AV_BASE_URL = "https://www.alphavantage.co/query"
AV_ENABLED  = bool(AV_API_KEY and AV_API_KEY != "PASTE_YOUR_KEY_HERE")

AV_DAILY_BUDGET  = 25
AV_CALLS_PER_MIN = 5

# ─────────────────────────────────────────────────────────────
# Hard filter thresholds (per task)
# ─────────────────────────────────────────────────────────────
GAP_MIN_PCT   = 5.0        # gap_pct > 5
PRICE_MIN     = 3.0        # price > $3
PM_VOLUME_MIN = 50_000     # premarket_volume > 50,000
TOP_N         = 10         # cap results at 10

# ─────────────────────────────────────────────────────────────
# Schedule — loop every 20 min until 9:20 AM ET
# ─────────────────────────────────────────────────────────────
LOOP_INTERVAL_MIN = 20
STOP_HOUR_ET      = 9
STOP_MIN_ET       = 20

# Premarket window (Eastern Time)
PM_START_HOUR_ET = 4
PM_START_MIN_ET  = 0
PM_END_HOUR_ET   = 9
PM_END_MIN_ET    = 30

# ─────────────────────────────────────────────────────────────
# News / sentiment
# ─────────────────────────────────────────────────────────────
NEWS_HEADLINES = 4   # top 4 headlines per top-10 pick

# ─────────────────────────────────────────────────────────────
# Universe
# ─────────────────────────────────────────────────────────────
UNIVERSE_CACHE_DAYS = 7
SP500_URL   = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
RUSSELL_URL = "https://en.wikipedia.org/wiki/Russell_1000_Index"

# Fallback static list (in case Wikipedia fetch fails on first run)
FALLBACK_UNIVERSE = [
    "AAPL","MSFT","NVDA","AMZN","GOOGL","GOOG","META","TSLA","AVGO","BRK-B",
    "LLY","V","JPM","WMT","XOM","UNH","MA","JNJ","PG","HD",
    "COST","ORCL","BAC","ABBV","NFLX","KO","MRK","CVX","AMD","PEP",
    "TMO","LIN","ADBE","CRM","MCD","CSCO","ACN","ABT","WFC","IBM",
    "GE","DIS","QCOM","AXP","INTC","T","VZ","MU","PLTR","SNOW",
    "COIN","SOFI","RIVN","LCID","F","GM","BA","UBER","LYFT","SHOP",
    "SQ","PYPL","ROKU","SPOT","ZM","DKNG","CVNA","BYND","GME","AMC",
    "BB","NOK","SNAP","PINS","HOOD","AFRM","UPST","DASH","ABNB","RBLX",
]

# ─────────────────────────────────────────────────────────────
# Runtime
# ─────────────────────────────────────────────────────────────
CONCURRENT_WORKERS = 12
YF_TIMEOUT_SEC     = 15
UNIVERSE_CAP       = 1200   # safety cap on total universe size

# ─────────────────────────────────────────────────────────────
# HTTP server (report viewer)
# ─────────────────────────────────────────────────────────────
HTTP_PORT  = 8767

# Anchor output directory to the module folder so it's independent of cwd.
_HERE = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(_HERE, "output")
