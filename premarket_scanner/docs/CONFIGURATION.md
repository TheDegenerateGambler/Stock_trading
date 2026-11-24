---
Project:        premarket_scanner
Doc:            CONFIGURATION.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Configuration - premarket_scanner

Every tunable lives in `config.py`. This table is the authoritative reference.

## Hard filter thresholds

| Constant | Default | Meaning |
|----------|---------|---------|
| `GAP_MIN_PCT` | 5.0 | Keep tickers gapping up more than this %. |
| `PRICE_MIN` | 3.0 | Minimum premarket price (USD). |
| `PM_VOLUME_MIN` | 50,000 | Minimum premarket volume. |
| `TOP_N` | 10 | Keep this many, ranked by `gap_pct` DESC. |

`gap_pct = (premarket_last - prev_close) / prev_close * 100`.

## Schedule / session

| Constant | Default | Meaning |
|----------|---------|---------|
| `LOOP_INTERVAL_MIN` | 20 | Minutes between scans. |
| `STOP_HOUR_ET` / `STOP_MIN_ET` | 9 / 20 | Loop exits at this ET time. |
| `PM_START_HOUR_ET` / `PM_START_MIN_ET` | 4 / 0 | Premarket window start (ET). |
| `PM_END_HOUR_ET` / `PM_END_MIN_ET` | 9 / 30 | Premarket window end (ET). |

Premarket bars from yfinance only exist 04:00-09:30 ET; outside that window a
scan reports 0 picks (expected).

## Alpha Vantage

| Constant | Default | Notes |
|----------|---------|-------|
| `AV_API_KEY` | env `AV_API_KEY`, else `PASTE_YOUR_KEY_HERE` | **No key in source.** Set via env var or a local `.env`. |
| `AV_BASE_URL` | `https://www.alphavantage.co/query` | API endpoint. |
| `AV_ENABLED` | derived | True only when a real key is present. |
| `AV_DAILY_BUDGET` | 25 | Free-tier daily call cap. |
| `AV_CALLS_PER_MIN` | 5 | Free-tier per-minute cap. |

## Universe

| Constant | Default | Notes |
|----------|---------|-------|
| `FALLBACK_UNIVERSE` | static list | Used if the Wikipedia scrape fails. |
| (universe cap) | 1,200 | Runtime cap on scanned tickers. |

## Secrets note

No key ships in source. The previously-committed key was scrubbed; if you used
it, rotate it on Alpha Vantage and provide the new one via `AV_API_KEY`.

---
Related: MODULES.md, OPERATIONS.md, SECURITY.md
