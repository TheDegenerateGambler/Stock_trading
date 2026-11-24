# Swing Options Scanner

Finds **2–4 week swing trade options plays** (calls & puts) that fit a small
account budget. Purpose-built for a **$110 USD (~$153 CAD)** account trading
on National Bank Direct Brokerage or any similar small-account setup.

Answers the question:

> *"I've got $110. What options can I buy today that have a realistic shot
> at a good swing gain over the next 2–4 weeks?"*

---

## What it does

For every ticker in the S&P 500 + Russell 1000 universe (~1,500 tickers,
filtered to price $10–$100 with avg volume > 5M):

1. **Analyzes the daily chart** — computes 20/50 EMA, RSI(14), MACD, ATR(14),
   RVOL and assigns a direction bias (`BULLISH` / `BEARISH` / `NEUTRAL`).
2. **Checks earnings** — skips any ticker with earnings inside the swing hold
   window (default: next 30 days) to avoid IV crush.
3. **Picks the best options contract** — from CBOE's free 15-min-delayed feed:
   - Expiry: **21–45 DTE**
   - Delta: **0.30–0.50** (slightly OTM)
   - OI ≥ 500, spread ≤ 15% of mid
   - **Cost ≤ your budget** (default $110 USD)
4. **Attaches a trade plan** — entry price cap, break-even, +50%/+100%
   profit targets, -40% stop loss, R:R, and a 14-day time stop.
5. **Ranks by composite score (0–100)** combining:
   - Trend (30) — price vs EMAs, EMA stack
   - Momentum (20) — RSI sweet-spot + MACD alignment
   - Volume (15) — RVOL + absolute liquidity
   - Sentiment (15) — Alpha Vantage NEWS_SENTIMENT (optional)
   - Options liquidity (10) — OI + spread
   - Budget fit (10) — cheaper contract = more upside per $

Only picks with **composite ≥ 50** are surfaced.

---

## Output

### Console
Compact ranked table with ticker, direction, score, contract, cost,
break-even, target 1, R:R, and earnings status.

### HTML (`output/swing_options_scanner.html`)
- Ranked cards for each pick
- Full setup summary + contract details + trade plan
- **Embedded TradingView daily chart** per ticker
- Link-outs to TradingView options chain & full chart
- Auto-refreshes every 5 min
- Dark theme

### JSON (`output/swing_picks.json`)
Full pick data for programmatic use.

---

## Install

```bash
cd Stock_trading/swing_options_scanner
pip install -r requirements.txt
```

Optional (for news sentiment): set an Alpha Vantage API key via the
`AV_API_KEY` environment variable (no key is bundled in source).
```bash
set AV_API_KEY=YOUR_KEY_HERE
```

---

## Usage

```bash
# Full scan (BOTH directions, $110 USD, opens browser)
python scanner.py
# or double-click run.bat

# Run once and exit (no HTTP server)
python scanner.py --once

# Only these tickers
python scanner.py --tickers AMD,PLTR,SOFI,F

# Override budget (e.g., you have $200 to spend)
python scanner.py --budget 200

# Calls only / Puts only
python scanner.py --dir CALL
python scanner.py --dir PUT

# Loosen score threshold to see more picks
python scanner.py --min-score 40

# Custom port + no browser auto-open
python scanner.py --port 8770 --no-browser

# Force fresh universe rebuild (bypass 7-day cache)
python scanner.py --refresh-universe

# ── Earnings season overrides (use when the market is in earnings season) ──

# Ignore earnings entirely (for exploration / testing)
python scanner.py --ignore-earnings

# Only skip if earnings within 7 days (looser than default 30)
python scanner.py --earnings-skip-days 7
```

> **⚠️ Earnings-season note.** In heavy earnings periods (mid-Jan, mid-Apr,
> mid-Jul, mid-Oct), the default 30-day earnings filter can eliminate almost
> every candidate. That's the tool working correctly — but if you want to
> see picks anyway (accepting the IV-crush risk), use `--ignore-earnings`
> or lower `--earnings-skip-days` to 7. Every pick's report clearly labels
> the exact days-to-earnings so you know what you're getting into.

---

## How the trade plan works

For each pick, the report shows:

| Field | Meaning |
|---|---|
| **Max entry** | Mid price × 1.05 — don't pay more than this |
| **Break-even at expiry** | Stock price where option = $0 P&L at expiration |
| **Stock move needed** | % move from spot to reach break-even |
| **Target 1 (+50%)** | First profit target — sell half here |
| **Target 2 (+100%)** | Second profit target — sell the rest |
| **Stop (-40%)** | Cut the loss if premium drops here |
| **Reward:Risk** | R:R at Target 1 (should be ≥ 1.25:1) |
| **Time stop** | Hard exit date if the trade isn't working (default 14 days) |

### Suggested execution
1. **Enter** at or below "Max entry" (use a limit order — never market on options)
2. **Sell half** at Target 1, move stop to break-even on the rest
3. **Sell the rest** at Target 2 or if it approaches expiration ITM
4. **Cut** at Stop or Time stop, whichever hits first

---

## Configuration

All knobs are in `config.py`. Key ones:

```python
BUDGET_USD          = 110       # max contract cost
MAX_CONTRACT_COST   = 150       # allow slight overshoot
PRICE_MIN           = 10.0      # stock price floor
PRICE_MAX           = 100.0     # stock price ceiling
DTE_MIN             = 21        # 3 weeks
DTE_MAX             = 45        # 6.5 weeks
DELTA_MIN           = 0.30
DELTA_MAX           = 0.50
MIN_OI              = 500
MIN_VOLUME          = 50
MAX_SPREAD_PCT      = 0.15
SKIP_EARNINGS_DAYS  = 30
TARGET_1_PCT        = 0.50      # +50%
TARGET_2_PCT        = 1.00      # +100%
STOP_LOSS_PCT       = 0.40      # -40%
TRADE_THRESHOLD_SCORE = 50      # min composite score
TOP_N               = 10
```

---

## Files

| File | Purpose |
|---|---|
| `config.py` | All thresholds, weights, and paths |
| `universe_builder.py` | S&P 500 + Russell 1000 ticker universe (cached 7 days) |
| `earnings_calendar.py` | Days-to-next-earnings via yfinance (cached 24 h) |
| `technical_screener.py` | Daily EMA/RSI/MACD/ATR/RVOL + direction bias + component scores |
| `options_selector.py` | CBOE chain fetch → filter → pick best contract fitting budget |
| `trade_builder.py` | Attach entry/target/stop/R:R/time-stop to a pick |
| `swing_ranker.py` | Add sentiment score + compose final composite |
| `report_builder.py` | Console + HTML (TradingView embeds) + JSON output |
| `scanner.py` | Main entry: universe → workers → rank → report → server |
| `run.bat` | Windows launcher |
| `requirements.txt` | Python deps |

---

## Data sources

| Data | Source | Notes |
|---|---|---|
| Daily bars | yfinance | ~15 s delay, free |
| Options chain | **CBOE** `cdn.cboe.com/api/global/delayed_quotes/options/{sym}.json` | Official free JSON, ~15 min delay, **native greeks** |
| Options fallback | yfinance option_chain() | If CBOE fails; Δ via Black-Scholes |
| Earnings dates | yfinance `Ticker.get_earnings_dates()` | Cached 24 h |
| Sentiment | Alpha Vantage NEWS_SENTIMENT | Free tier: 25/day, 5/min |
| Charts | TradingView Advanced Chart Widget | Embedded free |

---

## Reused infrastructure

This module deliberately reuses code from your existing stack:

- **Indicators** — imported from `../daytrade_picker/indicators.py`
- **CBOE options endpoint & OCC parsing pattern** — matches `../options_daytrader/cboe_client.py`
- **Universe pattern** — same S&P/Russell fetch as `../premarket_scanner/universe.py`
- **Alpha Vantage key** — shared with premarket scanner via env var

If you already run those modules, no new API keys or logins are needed.

---

## National Bank Direct Brokerage notes

NBDB charges **$6.95 flat for up to 5 option contracts** per trade. On the
default $110 budget:

- Round-trip commission = **$13.90**
- Break-even on fees requires ~**13% gain** on premium
- The scanner's default profit targets (+50% / +100%) clear this easily
- Every pick's R:R is calculated **before** commissions — subtract $13.90
  from Target 1 profit and Stop loss when sizing

---

## Limitations & honest caveats

- **Options data is ~15 min delayed.** Fine for swing entries at open/close;
  double-check live prices in your broker before hitting send.
- **Earnings via yfinance** occasionally misses or misreports dates. Always
  verify the ticker's next earnings date manually before entering.
- **Alpha Vantage sentiment** has a 25 calls/day free-tier limit. If exhausted
  mid-scan, remaining tickers get neutral (0.5) sentiment scores.
- **This is a research tool.** It flags candidates worth investigating.
  It does not know your risk tolerance, portfolio context, or macro view.
- **Not financial advice.** Options can and do go to zero. Only risk what
  you can afford to lose.

---

## Disclaimer

Educational tool. Not financial advice. Signals only. Manage your own risk,
size positions responsibly, and never trade what you can't afford to lose.