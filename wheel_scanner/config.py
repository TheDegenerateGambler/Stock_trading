"""
Configuration for the Canadian Wheel Scanner.

Broker: National Bank Direct Brokerage (NBDB)
  - $0 commission on stock buys/sells
  - $6.95 flat per options contract (up to and including 6 contracts)
    -> so 1 contract = $6.95, 6 contracts = $41.70
  - No exercise/assignment fees on equities (as of latest published schedule; verify)

Budget: $1,000 CAD to start.

Strategy: The Wheel
  1. Sell cash-secured put (CSP) on a stock you're willing to own.
  2. If assigned, sell covered calls (CC) above your cost basis.
  3. Repeat.

This scanner ranks Canadian TSX stocks under $10 CAD that:
  - Have listed options on the Montreal Exchange (MX)
  - Fit within a $1,000 CAD cash-secured put budget (strike * 100 <= budget)
  - Have reasonable option liquidity
  - Offer attractive annualized premium yield
"""

# ---------------------------------------------------------------------------
# Broker fee model  (National Bank Direct Brokerage)
# ---------------------------------------------------------------------------
STOCK_COMMISSION = 0.0            # NBDB: free stock trades (CAD & US)
OPTION_COMMISSION_PER_CONTRACT = 6.95       # CAD options (TSX / MX)
OPTION_COMMISSION_PER_CONTRACT_USD = 1.25   # US options (approx, verify)
OPTION_MAX_FLAT_CONTRACTS = 6     # flat pricing up to 6 contracts, verify beyond

# Approx CAD:USD FX conversion cost NBDB charges on FX conversions.
# Not applied per-trade in the scanner (informational), just shown in reports.
FX_SPREAD_ESTIMATE = 0.015        # ~1.5% each way

# Rough CAD per 1 USD, used only to convert USD prices/premiums into CAD-equivalent
# for the affordability filter and reporting. Override at CLI with --usd-cad.
DEFAULT_USD_CAD = 1.36

# ---------------------------------------------------------------------------
# Account settings
# ---------------------------------------------------------------------------
ACCOUNT_BUDGET_CAD = 1000.0
MAX_STOCK_PRICE_CAD = 10.00       # only look at names under this price
MIN_STOCK_PRICE_CAD = 2.00        # avoid true penny stocks
CONTRACT_SIZE = 100               # standard equity option contract

# ---------------------------------------------------------------------------
# Watchlist: Canadian TSX stocks that (historically) trade under $10 CAD
# and have listed options on the Montreal Exchange.
#
# yfinance uses ".TO" suffix for TSX-listed stocks.
# ---------------------------------------------------------------------------
CANADIAN_WHEEL_WATCHLIST = [
    # --- Gold & precious metals miners ---
    "BTO.TO",   # B2Gold Corp
    "NGD.TO",   # New Gold
    "IMG.TO",   # IAMGOLD
    "ELD.TO",   # Eldorado Gold (sometimes over $10, filter dynamically)
    "OGC.TO",   # OceanaGold
    "EQX.TO",   # Equinox Gold
    "LUG.TO",   # Lundin Gold (often over $10, filter)
    "ARIS.TO",  # Aris Mining

    # --- Base metals ---
    "HBM.TO",   # Hudbay Minerals
    "CS.TO",    # Capstone Copper
    "ERO.TO",   # Ero Copper (often over $10, filter)
    "LUN.TO",   # Lundin Mining (often over $10, filter)

    # --- Energy: Oil & Gas ---
    "BTE.TO",   # Baytex Energy
    "ATH.TO",   # Athabasca Oil
    "VET.TO",   # Vermilion Energy
    "MEG.TO",   # MEG Energy (often over $10, filter)
    "CPG.TO",   # Crescent Point Energy (often over $10 now, filter)
    "OBE.TO",   # Obsidian Energy
    "PEY.TO",   # Peyto Exploration (often over $10, filter)
    "TVE.TO",   # Tamarack Valley
    "NVA.TO",   # NuVista Energy (often over $10, filter)

    # --- Tech ---
    "BB.TO",    # BlackBerry

    # --- Cannabis (very volatile, high IV) ---
    "WEED.TO",  # Canopy Growth
    "ACB.TO",   # Aurora Cannabis
    "CRON.TO",  # Cronos Group
    "TLRY.TO",  # Tilray (dual-listed)
    "OGI.TO",   # OrganiGram

    # --- Airlines / travel ---
    "AC.TO",    # Air Canada (usually >$10, filter)

    # --- Media / other ---
    "CGX.TO",   # Cineplex
    "CJT.TO",   # Cargojet (usually >$10, filter)
]

# ---------------------------------------------------------------------------
# Weekly-friendly watchlist
# Tickers here are known to have WEEKLY options and are affordable-ish for
# small/medium accounts. Mostly US-listed (best weekly liquidity in the world),
# plus a handful of TSX blue-chips with weeklies on MX.
# ---------------------------------------------------------------------------
WEEKLY_US_WATCHLIST = [
    # --- Cheap ($5-$15 USD) with liquid weeklies ---
    "F",        # Ford Motor
    "SOFI",     # SoFi Technologies
    "PLTR",     # Palantir (may be >$15 now, filter dynamically)
    "NIO",      # NIO Inc
    "RIVN",     # Rivian
    "LCID",     # Lucid Motors
    "PLUG",     # Plug Power
    "OPEN",     # Opendoor
    "T",        # AT&T (~$20 range, verify)
    "BAC",      # Bank of America (~$35, verify)
    "CCL",      # Carnival Cruise
    "SNAP",     # Snap Inc
    "GRAB",     # Grab
    "AAL",      # American Airlines
    "MARA",     # Marathon Digital
    "RIOT",     # Riot Platforms
    "CLSK",     # CleanSpark
    "WBD",      # Warner Bros Discovery
    "PARA",     # Paramount

    # --- Slightly more expensive ($15-$40) but great weekly liquidity ---
    "INTC",     # Intel
    "AMD",      # AMD (usually much higher, filter)
    "UBER",     # Uber
    "GM",       # General Motors
    "PFE",      # Pfizer
    "VZ",       # Verizon
    "KO",       # Coca-Cola
    "XOM",      # Exxon (higher, filter)
    "CVX",      # Chevron (higher, filter)
]

WEEKLY_TSX_WATCHLIST = [
    # TSX names with actual weekly options on MX (usually large-cap only).
    # 100 shares of any of these needs several thousand CAD.
    "RY.TO",    # Royal Bank
    "TD.TO",    # TD Bank
    "BNS.TO",   # Scotiabank
    "BMO.TO",   # Bank of Montreal
    "CM.TO",    # CIBC
    "NA.TO",    # National Bank
    "ENB.TO",   # Enbridge
    "TRP.TO",   # TC Energy
    "SU.TO",    # Suncor
    "CNQ.TO",   # Canadian Natural Resources
    "SHOP.TO",  # Shopify (very high, filter)
    "BCE.TO",   # BCE
    "T.TO",     # Telus
    "MFC.TO",   # Manulife
    "SLF.TO",   # Sun Life
    "ABX.TO",   # Barrick Gold
    "NTR.TO",   # Nutrien
    "CP.TO",    # CP Rail (very high, filter)
    "CNR.TO",   # CN Rail (very high, filter)
]

# ---------------------------------------------------------------------------
# Option filtering thresholds
# ---------------------------------------------------------------------------
MIN_OPEN_INTEREST = 20            # minimum OI on the contract we consider
MIN_VOLUME_TODAY = 0              # today's volume can be 0 if OI is decent
MAX_BID_ASK_SPREAD_PCT = 0.35     # bid/ask spread <= 35% of mid price
MIN_BID = 0.05                    # ignore contracts with bid below $0.05

# Days to expiration window we want to look at (target 30-45 DTE for monthlies)
MIN_DTE = 20
MAX_DTE = 55

# ---------------------------------------------------------------------------
# Weekly-mode DTE window and filter relaxations
# ---------------------------------------------------------------------------
WEEKLY_MIN_DTE = 4                # skip 0-3 DTE (too much gamma / assignment risk)
WEEKLY_MAX_DTE = 14               # up to 2 weeks out
WEEKLY_MIN_OPEN_INTEREST = 50     # weeklies typically have higher OI, be stricter
WEEKLY_MAX_BID_ASK_SPREAD_PCT = 0.20   # weeklies should have tighter spreads
WEEKLY_MIN_BID = 0.03             # weekly premiums are smaller

# Put strike selection: target 20-30 delta puts (out-of-the-money)
# Since yfinance doesn't always give greeks reliably, we approximate:
# target strike is 3% - 10% below current price.
PUT_STRIKE_OTM_MIN_PCT = 0.02     # at least 2% OTM
PUT_STRIKE_OTM_MAX_PCT = 0.12     # up to 12% OTM

# ---------------------------------------------------------------------------
# Covered Call (CC) settings
# ---------------------------------------------------------------------------
# Call strike selection: target OTM calls above current price
CALL_STRIKE_OTM_MIN_PCT = 0.02    # at least 2% above spot
CALL_STRIKE_OTM_MAX_PCT = 0.10    # up to 10% above spot

# DTE window for CCs (usually similar to CSPs; kept separate for tunability)
CC_MIN_DTE = 20
CC_MAX_DTE = 55

# CC ranking weights (sum roughly to 1.0)
CC_WEIGHT_ANNUALIZED_YIELD = 0.45      # if-called annualized return
CC_WEIGHT_LIQUIDITY = 0.25             # OI + tight spread
CC_WEIGHT_UPSIDE_ROOM = 0.20           # room from spot to strike (upside preservation)
CC_WEIGHT_DOWNSIDE_PROTECTION = 0.10   # premium as % of stock price (cushion)

# In buy-write mode, enforce that 100 shares fit in the account budget
CC_BUY_WRITE_ENFORCE_BUDGET = True

# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
OUTPUT_DIR = "output"
OUTPUT_CSV = "wheel_candidates.csv"
OUTPUT_HTML = "wheel_candidates.html"
OUTPUT_TXT = "wheel_candidates.txt"

# Covered call outputs
CC_OUTPUT_CSV = "cc_candidates.csv"
CC_OUTPUT_HTML = "cc_candidates.html"
CC_OUTPUT_TXT = "cc_candidates.txt"

# Combined wheel dashboard
DASHBOARD_HTML = "wheel_dashboard.html"

# ---------------------------------------------------------------------------
# Ranking weights (sum roughly to 1.0) — for CSPs
# ---------------------------------------------------------------------------
WEIGHT_ANNUALIZED_YIELD = 0.45    # premium yield matters most
WEIGHT_LIQUIDITY = 0.25           # OI + tight spread
WEIGHT_SAFETY = 0.20              # distance from current price (OTM cushion)
WEIGHT_AFFORDABILITY = 0.10       # fits well within $1000 budget
