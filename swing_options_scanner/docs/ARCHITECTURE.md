---
Project:        swing_options_scanner
Doc:            ARCHITECTURE.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Architecture - swing_options_scanner

A command-line scanner for **2-4 week swing options** (calls & puts) that fit a
small account (default $110 USD budget). It screens a large US-equity universe,
avoids earnings-window IV crush, selects an affordable contract, attaches a
trade plan, ranks by a composite 0-100 score, and serves an HTML report.

## Module map

```
                  scanner.py  (entry + local HTTP server)
                        │
   ┌──────────┬─────────┼──────────┬──────────────┬─────────────┐
   ▼          ▼         ▼          ▼              ▼             ▼
universe_   technical_  earnings_  swing_ranker  options_     trade_builder
builder.py  screener.py calendar.py  .py          selector.py   .py
(S&P500+    (EMA/RSI/   (skip if    (composite    (CBOE chain,  (entry cap,
 R1000,      MACD/ATR/   earnings    score 0-100,   DTE 21-45,    targets,
 price/vol   RVOL +      within      threshold 50)  Δ 0.30-0.50,  stop, R:R,
 filter)     bias)       window)                    OI/spread,    time stop)
                                                    budget cap)
                                         │
                                         ▼
                                  report_builder.py
                             (console + HTML + swing_picks.json)

              config.py  ← budget, filters, DTE/Δ, weights, AV (imported by all)
```

## Why each module exists

- **`scanner.py`** - entry point; orchestrates universe → screen → earnings →
  rank → contract → trade plan → report; serves the report locally.
- **`config.py`** - budget, direction, universe filters, options-selection
  rules, earnings avoidance, trade rules, `SCORE_WEIGHTS`, AV settings.
- **`universe_builder.py`** - builds the ticker universe (S&P 500 + Russell 1000)
  filtered to price $10-$100 and avg volume > 5M, capped at `UNIVERSE_CAP`.
- **`technical_screener.py`** - daily-chart indicators (20/50 EMA, RSI(14),
  MACD, ATR(14), RVOL) → directional bias (BULLISH / BEARISH / NEUTRAL).
- **`earnings_calendar.py`** - next-earnings date (yfinance), cached; used to
  skip tickers with earnings inside the hold window.
- **`swing_ranker.py`** - composite 0-100 score from trend/momentum/volume/
  sentiment/liquidity/budget-fit; AV `NEWS_SENTIMENT` optional.
- **`options_selector.py`** - picks a contract (CBOE feed): DTE 21-45, Δ
  0.30-0.50, OI ≥ 500, spread ≤ 15%, cost ≤ budget.
- **`trade_builder.py`** - attaches entry cap, break-even, +50%/+100% targets,
  -40% stop, R:R, and a 14-day time stop.
- **`report_builder.py`** - console table + HTML (TradingView daily charts,
  auto-refresh 5 min, dark theme) + `output/swing_picks.json`.

## Data flow

1. `universe_builder` → filtered tickers.
2. `technical_screener` → per-ticker bias; `earnings_calendar` drops IV-crush
   risks.
3. `options_selector` → an affordable contract per surviving ticker.
4. `swing_ranker` → composite score; keep ≥ `TRADE_THRESHOLD_SCORE` (50).
5. `trade_builder` → trade plan per pick.
6. `report_builder` → HTML + JSON; `scanner` serves it locally.

## Design properties

- **Small-account focused** - contract cost is a first-class filter and scoring
  input.
- **Earnings-aware** - deliberately avoids holding through earnings.
- **Local-only, read-only data**; AV sentiment is optional and budget-throttled.

---
Related: MODULES.md, DATA_FLOW.md, CONFIGURATION.md
