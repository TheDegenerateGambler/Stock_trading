---
Project:        daytrade_picker
Doc:            CONFIGURATION.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Configuration - daytrade_picker

Every tunable lives in `config.py`.

## Alpha Vantage

| Constant | Default | Notes |
|----------|---------|-------|
| `AV_API_KEY` | env `AV_API_KEY`, else `PASTE_YOUR_KEY_HERE` | **No key in source.** Set via env var or a local `.env`. |
| `AV_BASE_URL` | `https://www.alphavantage.co/query` | API endpoint. |
| `AV_ENABLED` | derived | True only when a real key is present. |
| `AV_DAILY_BUDGET` | 25 | Free-tier daily call cap. |
| `AV_CALLS_PER_MIN` | 5 | Free-tier per-minute cap. |

## Scanner settings

| Constant | Default | Meaning |
|----------|---------|---------|
| `TOP_N_PICKS` | 10 | Final picks displayed. |
| `SCAN_CANDIDATES` | 20 | Gainers/actives scored per scan. |
| `REFRESH_INTERVAL` | 30 | Minutes between full scans. |
| `WALTER_REFRESH_MIN` | 5 | Minutes between RSS refreshes. |
| `MAX_WALTER_ITEMS` | 30 | Headlines shown in the sidebar. |

## Scoring thresholds

| Constant | Default | Meaning |
|----------|---------|---------|
| `RSI_OVERSOLD` | 35 | Oversold threshold feeding LONG bias. |
| (other thresholds) | see `config.py` | RSI/MACD/VWAP/ATR gates used by `scorer.py`. |

## CLI overrides

| Flag | Meaning |
|------|---------|
| `--once` | Single scan then exit. |
| `--no-browser` | Don't auto-open the report. |
| `--interval N` | Override the scan interval (minutes). |
| `--port N` | Report server port (default 8766). |

## Secrets note

No key ships in source. The previously-committed Alpha Vantage key was scrubbed
and the README updated; if you used it, **rotate it** on Alpha Vantage and set
the new one via `AV_API_KEY`.

---
Related: MODULES.md, OPERATIONS.md, SECURITY.md
