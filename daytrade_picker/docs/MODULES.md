---
Project:        daytrade_picker
Doc:            MODULES.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Modules - daytrade_picker

Per-file reference. In-code docstrings are authoritative for fine detail. See
also the grandfathered `FEATURE_LOG.md` for narrative history.

## `config.py`
Alpha Vantage (`AV_API_KEY` from env, no key in source; `AV_BASE_URL`,
`AV_ENABLED`, `AV_DAILY_BUDGET` 25, `AV_CALLS_PER_MIN` 5), scanner settings
(`TOP_N_PICKS` 10, `SCAN_CANDIDATES` 20, `REFRESH_INTERVAL` 30,
`WALTER_REFRESH_MIN` 5, `MAX_WALTER_ITEMS` 30), and scoring thresholds
(`RSI_OVERSOLD` 35, etc.). See CONFIGURATION.md.

## `pick.py`
Entry point.
- `_Handler` - localhost `SimpleHTTPRequestHandler` with no-cache headers,
  serving `output/`.
- `start_server` / `_find_port` - bind the report server.
- `_wb_loop` - background thread refreshing Walter Bloomberg RSS.
- `run_scan(session)` - one scan: candidates → score → regime → write.
- `_build_and_write`, `_print_summary` - render helpers.
- `main()` - argparse (`--once`, `--no-browser`, `--interval N`, `--port N`),
  starts the server, runs the loop (incl. a midday rescan).

## `alphavantage.py`
- rate-limited AV client (`_throttle`): screener (top gainers / most active) and
  `NEWS_SENTIMENT`. `params["apikey"] = config.AV_API_KEY`. Returns parsed JSON
  or `None`.

## `indicators.py`
- pure functions: `calc_ema`, `calc_macd`, `calc_vwap`, `calc_atr`. No I/O;
  unit-testable.

## `scorer.py`
- combines technicals + sentiment into a LONG/SHORT conviction score and
  attaches entry, stop, and a 2:1 R:R target.

## `market_regime.py`
- `fetch_regime() -> dict` - SPY/QQQ/IWM day change % + VIX via yfinance → a
  regime classification + guidance string; returns an "unavailable" result on
  fetch failure (`_safe`, `_chg`, `_last` helpers).

## `walter_bloomberg.py`
- fetches + parses the Walter Bloomberg RSS feed; exposes recent headlines
  (title/source/time) for the report sidebar; caches between refreshes.

## `report_builder.py`
- `_esc` + writers that render `output/report.html` and `output/live_data.json`,
  plus a live-news partial. Uses `html_styles.py` for CSS/JS.

## `html_styles.py`
- the report's CSS + JavaScript (auto-refresh, layout, theming) as string
  constants.

---
Related: ARCHITECTURE.md, CONFIGURATION.md, DATA_FLOW.md
