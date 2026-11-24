---
Project:        premarket_scanner
Doc:            MODULES.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Modules - premarket_scanner

Per-file reference. In-code docstrings are authoritative for fine detail.

## `config.py`
All tunables. Hard filters: `GAP_MIN_PCT` (5.0), `PRICE_MIN` (3.0),
`PM_VOLUME_MIN` (50,000), `TOP_N` (10). Schedule: `LOOP_INTERVAL_MIN` (20),
`STOP_HOUR_ET`/`STOP_MIN_ET` (9:20), premarket window `PM_START_*`/`PM_END_*`
(04:00-09:30 ET). Alpha Vantage: `AV_API_KEY` (env `AV_API_KEY`, no key in
source), `AV_BASE_URL`, `AV_ENABLED`, `AV_DAILY_BUDGET` (25), `AV_CALLS_PER_MIN`
(5). Plus universe sources / fallback. See CONFIGURATION.md.

## `scanner.py`
Entry point.
- `_Handler` - quiet `SimpleHTTPRequestHandler` with no-cache headers, serving
  the `output/` directory.
- scan loop: builds universe → premarket filter → news enrich → report; sleeps
  `LOOP_INTERVAL_MIN`; exits at the ET stop time.
- `main()` - argparse (`--once`, etc.), starts the server, runs the loop.

## `universe.py`
- builds the scan universe from AV `TOP_GAINERS_LOSERS` + S&P 500 + Russell 1000
  (Wikipedia scrape with a browser User-Agent), deduped, cached ~7 days, capped
  at 1,200. Falls back to `config.FALLBACK_UNIVERSE` if Wikipedia fails.
- `build_universe(force_refresh=False) -> list[str]`.

## `premarket_data.py`
- concurrent yfinance fetch of premarket bars for the universe; computes
  `gap_pct = (premarket_last - prev_close) / prev_close * 100` and applies the
  hard filters; returns the filtered, ranked rows.

## `news_fetcher.py`
- for each top pick: AV `NEWS_SENTIMENT` → normalized 0-1 score + label + top-4
  headlines; auto-categorises a catalyst (Earnings / Guidance / FDA-Clinical /
  M&A / Analyst / Offering / Partnership / Legal / Insider / Product / Contract /
  Other). Falls back to `yfinance.Ticker.news` when the AV budget is exhausted.

## `alphavantage_client.py`
- self-contained rate-limited AV client; throttles to `AV_CALLS_PER_MIN` and
  tracks the `AV_DAILY_BUDGET`. Returns parsed JSON or `None` on failure.

## `report_builder.py`
- `write_*` helpers that render the console table, the auto-refreshing HTML
  report (`output/premarket_report.html`), and the JSON picks
  (`output/premarket_picks.json`, consumed by the options_daytrader project).

---
Related: ARCHITECTURE.md, CONFIGURATION.md, DATA_FLOW.md
