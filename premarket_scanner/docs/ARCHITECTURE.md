---
Project:        premarket_scanner
Doc:            ARCHITECTURE.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Architecture - premarket_scanner

A command-line premarket gap-up scanner. It builds a US-equity universe, fetches
premarket bars, filters for gap-ups, enriches the top picks with news/sentiment,
and serves an auto-refreshing HTML report from a tiny local HTTP server.

## Module map

```
              scanner.py  (entry point + loop + local HTTP server)
                   │
   ┌───────────────┼───────────────┬──────────────────┐
   ▼               ▼               ▼                  ▼
universe.py   premarket_data.py  news_fetcher.py   report_builder.py
(build + cache (concurrent       (AV NEWS_SENTIMENT (console table +
 S&P500/R1000   yfinance          + catalyst tag    HTML + JSON)
 + AV movers)   premarket bars)   + yfinance fallback)
                                         │
                                         ▼
                              alphavantage_client.py
                              (rate-limited AV client)

              config.py  ← thresholds, schedule, AV settings (imported by all)
```

## Why each module exists

- **`scanner.py`** - entry point. Parses args, runs the scan loop every
  `LOOP_INTERVAL_MIN` until the ET stop time, and serves the report over a local
  HTTP server (`_Handler`).
- **`config.py`** - all tunables: hard filters (`GAP_MIN_PCT`, `PRICE_MIN`,
  `PM_VOLUME_MIN`, `TOP_N`), schedule, premarket window, AV settings, universe
  sources.
- **`universe.py`** - builds the scan universe (AV movers + S&P 500 + Russell
  1000 from Wikipedia, with a static fallback), deduped and cached ~7 days,
  capped at 1,200 tickers.
- **`premarket_data.py`** - concurrent yfinance fetch of premarket bars; computes
  `gap_pct` and applies the hard filters.
- **`news_fetcher.py`** - for the top picks, fetches AV `NEWS_SENTIMENT`, tags a
  catalyst category, and falls back to `yfinance.Ticker.news` if the AV budget is
  exhausted.
- **`alphavantage_client.py`** - self-contained, rate-limited Alpha Vantage
  client (respects the free-tier daily/per-minute budget).
- **`report_builder.py`** - renders the console table, the HTML report
  (auto-refresh), and the JSON picks file.

## Data flow

1. `universe` → list of candidate tickers.
2. `premarket_data` → premarket bars → `gap_pct` → hard filters → top-N.
3. `news_fetcher` → sentiment + catalyst + headlines for the top-N.
4. `report_builder` → `output/premarket_report.html` + `output/premarket_picks.json`.
5. `scanner`'s HTTP server serves the report at `http://127.0.0.1:8767/`.

## Design properties

- **Local-only + read-only data.** Reads public market data; writes only to
  `output/`. The HTTP server binds to localhost.
- **Budget-aware.** The AV client throttles to the free-tier limits; news falls
  back to yfinance when the budget is spent.
- **Time-boxed.** The loop auto-exits at the ET stop time; premarket bars only
  exist 04:00-09:30 ET (0 picks outside that window is expected, not a bug).

---
Related: MODULES.md, DATA_FLOW.md, CONFIGURATION.md
