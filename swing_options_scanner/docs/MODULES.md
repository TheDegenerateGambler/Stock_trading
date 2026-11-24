---
Project:        swing_options_scanner
Doc:            MODULES.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Modules - swing_options_scanner

Per-file reference. In-code docstrings are authoritative for fine detail.

## `config.py`
Budget (`BUDGET_USD` 110, `MAX_CONTRACT_COST` 150, `CAD_TO_USD_RATE` 0.72),
`DIRECTION` (BOTH), universe filters (`PRICE_MIN/MAX` 10-100,
`MIN_AVG_VOLUME` 5M, `UNIVERSE_CAP` 1200), options selection (`DTE_MIN/MAX`
21-45, `DELTA_MIN/MAX` 0.30-0.50, `MIN_OI` 500, `MIN_VOLUME` 50,
`MAX_SPREAD_PCT` 0.15), `SKIP_EARNINGS_DAYS` (30), trade rules (`TARGET_1_PCT`
0.50, `TARGET_2_PCT` 1.00, `STOP_LOSS_PCT` 0.40, `TIME_STOP_DAYS` 14),
`SCORE_WEIGHTS` (trend 30, momentum 20, volume 15, sentiment 15, liquidity 10,
budget_fit 10), `TRADE_THRESHOLD_SCORE` (50), AV settings (key from env, no key
in source). See CONFIGURATION.md.

## `scanner.py`
Entry point.
- `_QuietHandler` - silent localhost `SimpleHTTPRequestHandler` serving `output/`.
- `parse_args()` + `main()` - orchestrate the pipeline and serve the report.

## `universe_builder.py`
- `build_universe(force_refresh=False) -> list[str]` - S&P 500 + Russell 1000,
  filtered to price $10-$100 and avg volume > 5M, capped at `UNIVERSE_CAP`.
  (`__main__` prints the total.)

## `technical_screener.py`
- `analyze(ticker) -> dict` - daily 20/50 EMA, RSI(14), MACD, ATR(14), RVOL and a
  directional bias (BULLISH / BEARISH / NEUTRAL). (`__main__` smoke-tests a few
  tickers.)

## `earnings_calendar.py`
- `get_days_to_earnings(ticker) -> int|None` - next earnings via yfinance
  (`calendar` / `get_earnings_dates`), cached to `output/earnings_cache.json`.
  Used to skip tickers with earnings within `SKIP_EARNINGS_DAYS`.

## `swing_ranker.py`
- composite 0-100 score from trend/momentum/volume/sentiment/liquidity/
  budget-fit using `SCORE_WEIGHTS`; AV `NEWS_SENTIMENT` optional (needs key).

## `options_selector.py`
- selects a contract from the CBOE feed meeting DTE 21-45, Δ 0.30-0.50, OI ≥
  500, spread ≤ 15%, and cost ≤ budget. (`__main__` smoke-tests sample tickers.)

## `trade_builder.py`
- builds the trade plan: entry cap, break-even, +50%/+100% targets, -40% stop,
  R:R, 14-day time stop. (`__main__` tests a fake contract.)

## `report_builder.py`
- console ranked table + HTML report (TradingView daily charts, link-outs,
  auto-refresh 5 min, dark theme) → `output/swing_options_scanner.html` and
  `output/swing_picks.json`.

---
Related: ARCHITECTURE.md, CONFIGURATION.md, DATA_FLOW.md
