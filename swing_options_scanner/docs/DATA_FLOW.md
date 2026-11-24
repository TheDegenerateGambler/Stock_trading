---
Project:        swing_options_scanner
Doc:            DATA_FLOW.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Data Flow - swing_options_scanner

End-to-end trace of one scan. Example values are illustrative.

## Trigger

```
python scanner.py
```

## Step-by-step

1. **Universe** (`universe_builder.build_universe`): S&P 500 + Russell 1000 →
   filter to price $10-$100, avg volume > 5M → cap at `UNIVERSE_CAP` (1200).
   e.g. ~900 tickers.

2. **Technical screen** (`technical_screener.analyze`) per ticker: 20/50 EMA,
   RSI(14), MACD, ATR(14), RVOL → bias. e.g. `AMD` → BULLISH.

3. **Earnings gate** (`earnings_calendar.get_days_to_earnings`): if earnings fall
   within `SKIP_EARNINGS_DAYS` (30), drop the ticker to avoid IV crush. e.g.
   `AMD` earnings in 44 days → kept.

4. **Contract selection** (`options_selector`) from the CBOE feed: DTE 21-45,
   Δ 0.30-0.50, OI ≥ 500, spread ≤ 15%, cost ≤ `MAX_CONTRACT_COST`. e.g. a 35-DTE
   `AMD` call, Δ 0.38, mid $1.05 → cost $105 ≤ budget.

5. **Rank** (`swing_ranker`): composite 0-100 from trend (30) + momentum (20) +
   volume (15) + sentiment (15, AV optional) + liquidity (10) + budget-fit (10).
   Keep if ≥ `TRADE_THRESHOLD_SCORE` (50). e.g. `AMD` → 68.

6. **Trade plan** (`trade_builder`): entry cap, break-even, +50%/+100% targets,
   -40% stop, R:R, 14-day time stop.

7. **Report** (`report_builder`): write
   - `output/swing_options_scanner.html` (TradingView daily charts, auto-refresh
     5 min, dark theme)
   - `output/swing_picks.json`
   and print a ranked console table.

8. **Serve** (`scanner._QuietHandler`): report served from `output/` on a local
   port.

## What crosses a boundary

- **Network (read-only):** Wikipedia (universe), Yahoo/yfinance (bars +
  earnings), CBOE (options chain), Alpha Vantage (optional sentiment).
  TradingView charts load in the browser viewing the report.
- **Disk:** writes under `output/` (incl. `earnings_cache.json`).
- **Local HTTP:** report on localhost only.

---
Related: ARCHITECTURE.md, MODULES.md, OPERATIONS.md
