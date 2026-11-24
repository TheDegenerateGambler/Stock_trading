# Options Day Trader

A live options picker for the 9:30 AM – 12:00 PM ET window. Combines
technical signals with today's premarket gap-ups to answer one question:

> **What should I trade right now — CALLS or PUTS — and which contract?**

Always outputs a read on **SPY** and **QQQ** (which the user primarily trades),
plus the single best gap-up options play if one qualifies.

## What it does each scan (every 5 min)

1. **Analyzes SPY and QQQ** with 1-min + 5-min bars → computes:
   - VWAP position, 9/20 EMA cross, RSI(14), MACD histogram, RVOL, gap fill, ATR
   - Composite score ∈ [-100, +100] → **CALL / PUT / NO-TRADE** + confidence
2. **Loads today's top 10 gap-up picks** from
   `../premarket_scanner/output/premarket_picks.json` (reuses AV sentiment).
3. **Runs the same signal engine concurrently** on the 10 gap-up candidates.
4. **For each CALL/PUT signal**, pulls the options chain (**CBOE first, yfinance
   fallback**) and picks a contract in the **Δ 0.30 – 0.45** range with
   OI > 500, volume > 100, and spread ≤ 15% of mid.
   - **0DTE** for SPY/QQQ, **nearest Friday weekly** for other tickers.
   - Falls back to closest-strike ATM if no liquid contract passes, flagged
     `LOW LIQUIDITY`.
   - **CBOE provides native greeks (Δ Γ Θ ν)**; yfinance fallback uses Black-Scholes for Δ.
5. **Attaches entry / stop / target** using underlying ATR × Δ:
   - Stop = mid − ATR × 0.5 × |Δ|
   - Target = mid + ATR × 1.0 × |Δ|
   - Suggested max entry = mid × 1.05 (allow for slippage)
6. **Writes**:
   - Console table (SPY, QQQ, top gap-up play, watchlist)
   - `output/options_daytrader.html` with **live TradingView charts** for each
     pick and full contract details (auto-refresh every 60 s)
   - `output/options_daytrader.json`

## Session

- **Runs 9:30 AM – 12:00 PM ET** and auto-exits at 12:00.
- Rescan cadence: **every 5 minutes** (configurable).
- Options: `--once`, `--force` (bypass session), `--interval N`, `--no-browser`, `--port N`.

## Data sources

| Data | Source | Notes |
|---|---|---|
| Underlying 1-/5-min bars | **yfinance** | ~15 s delay |
| Options chain (primary) | **CBOE** `cdn.cboe.com/api/global/delayed_quotes/options/{sym}.json` | Official free JSON, ~15 min delay, **full greeks (Δ Γ Θ ν)** |
| Options chain (fallback) | **yfinance** `Ticker.option_chain()` | Used if CBOE fails; Δ via Black-Scholes |
| News / sentiment | Reused from `premarket_scanner` output | AV NEWS_SENTIMENT scores |
| Underlying charts | **TradingView Advanced Chart Widget** | Free, official embed |
| Options chain link-out | **TradingView options chain page** | Click-through button per pick |

**Data caveat:** All option quotes are ~15 minutes delayed (both CBOE and
yfinance are delayed feeds). Signals from 1-min bars on the underlying are
current; the option premium and Greeks lag by 15 min. The picker labels every
scan clearly. **CBOE gives us native greeks (Δ Γ Θ ν) so we don't have to
compute them via Black-Scholes** — this is a strict upgrade over yfinance.

### TradingView link-out

Each pick card in the HTML report has two buttons:
- **"View options chain on TradingView →"** — opens `https://www.tradingview.com/options/chain/?symbol=AMEX:SPY` (or NASDAQ:QQQ) in a new tab so you can eyeball the live chain visually.
- **"Open full chart"** — opens the full TradingView chart page.

## Install

```bash
cd Stock_trading/options_daytrader
pip install -r requirements.txt
```

## Usage

```bash
# Loop every 5 min from 9:30 AM to 12:00 PM ET (opens browser to report)
python daytrader.py
# or double-click run.bat

# Run one scan and exit
python daytrader.py --once

# Force scan outside the session window (for testing)
python daytrader.py --once --force

# Change interval or port
python daytrader.py --interval 3 --port 8770
```

## How it works end-to-end

```
┌───────────────────────────────────────────────────────────────┐
│  premarket_scanner (runs 4-9:20 AM)                           │
│  → output/premarket_picks.json  (top 10 gap-ups + sentiment) │
└─────────────────────────────┬─────────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────────┐
│  options_daytrader (runs 9:30 AM - 12:00 PM, every 5 min)     │
│                                                                │
│  For SPY, QQQ, and each premarket pick:                        │
│    signal_engine.analyze()   → direction + confidence          │
│    options_ranker.pick_best() → best contract in Δ 0.30-0.45   │
│                                                                │
│  Outputs:                                                      │
│    • console table                                             │
│    • output/options_daytrader.html   (TradingView charts)     │
│    • output/options_daytrader.json                             │
└───────────────────────────────────────────────────────────────┘
```

## Files

| File | Purpose |
|---|---|
| `config.py` | Session hours, signal weights, delta targets, liquidity thresholds |
| `signal_engine.py` | VWAP + 9/20 EMA + RSI + MACD + RVOL + gap + sentiment → composite score |
| `cboe_client.py` | **CBOE delayed options chain** — primary source, native greeks |
| `options_chain.py` | Router: CBOE first, yfinance fallback + Black-Scholes Δ |
| `options_ranker.py` | Pick best contract; attach entry/stop/target from ATR |
| `unusualwhales_stub.py` | Placeholder for future paid UW integration |
| `report_builder.py` | Console + HTML (TradingView widgets + chain link-outs) + JSON |
| `daytrader.py` | Main entry + 5-min loop + HTTP server |
| `run.bat` | Windows launcher |

## Recommended workflow

1. **04:00 – 09:20 AM ET** — run `premarket_scanner` (populates `premarket_picks.json`).
2. **09:30 AM ET** — start `options_daytrader`; it auto-loads the premarket picks
   and rescans every 5 min. Browser opens to the live report.
3. Trade off the report; the picker updates the top pick and SPY/QQQ direction
   as market conditions evolve.
4. **12:00 PM ET** — scanner auto-exits.

## Unusual Whales

Currently a **stub** (`unusualwhales_stub.py`). No public free API. If you
subscribe to UW's official API tier later, populate `UNUSUAL_WHALES_TOKEN`
env var and set `UNUSUAL_WHALES_ENABLED = True` in `config.py`; then flesh
out `get_flow()` and it will feed as an extra signal.

## Disclaimer

**Not financial advice.** Signals only. Options can go to zero. Manage your
own risk, size positions responsibly, and never trade what you can't afford
to lose.