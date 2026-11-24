---
Project:        daytrade_picker
Doc:            ARCHITECTURE.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Architecture - daytrade_picker

A standalone day-trading stock picker. Every 30 minutes it scans US markets for
the top 10 high-conviction day trades, outputs LONG/SHORT direction with entry /
stop / 2:1 target, and serves a live HTML report with a Walter Bloomberg news
sidebar and a market-regime banner.

## Module map

```
                    pick.py  (entry + scan loop + local HTTP server)
                        │
   ┌───────────┬────────┼─────────┬──────────────┬───────────────┐
   ▼           ▼        ▼         ▼              ▼               ▼
alphavantage  indicators  scorer  market_regime  walter_bloomberg report_builder
(screener +   (EMA/MACD/  (LONG/   (SPY/QQQ/IWM   (RSS headlines   (HTML + JSON)
 news/        VWAP/ATR)   SHORT     + VIX regime)   sidebar feed)    + html_styles
 sentiment)              conviction)                                  (CSS/JS)

              config.py  ← AV settings, scan sizes, scoring thresholds
```

## Why each module exists

- **`pick.py`** - entry point; runs the scan loop (default 30 min), serves the
  report over a localhost HTTP server, and runs a background thread that
  refreshes the Walter Bloomberg RSS. Also handles a midday rescan.
- **`config.py`** - AV settings, scan sizes (`TOP_N_PICKS` 10, `SCAN_CANDIDATES`
  20), intervals, and scoring thresholds.
- **`alphavantage.py`** - rate-limited AV client: screener (gainers/actives) +
  news sentiment.
- **`indicators.py`** - pure technical indicators (EMA, MACD, VWAP, ATR).
- **`scorer.py`** - combines indicators + sentiment into a LONG/SHORT conviction
  and attaches entry/stop/target (2:1 R:R).
- **`market_regime.py`** - fetches SPY/QQQ/IWM day change + VIX to classify the
  broad regime shown as a banner.
- **`walter_bloomberg.py`** - fetches the Walter Bloomberg RSS headlines for the
  report sidebar.
- **`report_builder.py` / `html_styles.py`** - writes the HTML report + JSON;
  CSS/JS live in `html_styles.py`.

## Data flow

1. `alphavantage` → candidate gainers/actives (`SCAN_CANDIDATES`).
2. `indicators` + `alphavantage` sentiment → `scorer` → LONG/SHORT conviction +
   entry/stop/target; keep `TOP_N_PICKS`.
3. `market_regime` → regime banner; `walter_bloomberg` → news sidebar.
4. `report_builder` → `output/report.html` + `output/live_data.json`.
5. `pick`'s HTTP server serves the report; a background thread refreshes news.

## Design properties

- **Local-only; read-only data.** Writes under `output/`; report server binds to
  localhost.
- **AV free-tier aware.** All AV calls route through the throttled client.
- **Resilient loop.** A failed data pull degrades gracefully (e.g. regime shows
  "unavailable") rather than aborting the scan.

---
Related: MODULES.md, DATA_FLOW.md, CONFIGURATION.md
