---
Project:        swing_options_scanner
Doc:            CONFIGURATION.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Configuration - swing_options_scanner

Every tunable lives in `config.py`.

## Budget

| Constant | Default | Meaning |
|----------|---------|---------|
| `BUDGET_USD` | 110 | Target contract-cost cap (USD). |
| `MAX_CONTRACT_COST` | 150 | Allowed overshoot ceiling. |
| `CAD_TO_USD_RATE` | 0.72 | Display-only conversion. |

## Direction & universe

| Constant | Default | Meaning |
|----------|---------|---------|
| `DIRECTION` | `BOTH` | `CALL` / `PUT` / `BOTH`. |
| `PRICE_MIN` / `PRICE_MAX` | 10 / 100 | Stock price band (keeps contracts affordable). |
| `MIN_AVG_VOLUME` | 5,000,000 | Liquidity floor. |
| `UNIVERSE_CAP` | 1200 | Max tickers scanned. |

## Options selection (swing timeframe)

| Constant | Default | Meaning |
|----------|---------|---------|
| `DTE_MIN` / `DTE_MAX` | 21 / 45 | Days-to-expiration window. |
| `DELTA_MIN` / `DELTA_MAX` | 0.30 / 0.50 | Target delta (slightly OTM). |
| `MIN_OI` | 500 | Minimum open interest. |
| `MIN_VOLUME` | 50 | Minimum contract volume. |
| `MAX_SPREAD_PCT` | 0.15 | Max `(ask-bid)/mid`. |

## Earnings avoidance

| Constant | Default | Meaning |
|----------|---------|---------|
| `SKIP_EARNINGS_DAYS` | 30 | Skip tickers with earnings within N days (IV crush). |

## Trade rules

| Constant | Default | Meaning |
|----------|---------|---------|
| `TARGET_1_PCT` | 0.50 | First profit target (+50%). |
| `TARGET_2_PCT` | 1.00 | Second profit target (+100%). |
| `STOP_LOSS_PCT` | 0.40 | Stop loss (-40%). |
| `TIME_STOP_DAYS` | 14 | Exit if no move within 2 weeks. |

## Scoring (`SCORE_WEIGHTS`, composite 0-100)

| Key | Default | Component |
|-----|---------|-----------|
| `trend` | 30 | Price vs 20/50 EMA, EMA stack. |
| `momentum` | 20 | RSI sweet-spot + MACD alignment. |
| `volume` | 15 | RVOL + absolute liquidity. |
| `sentiment` | 15 | AV `NEWS_SENTIMENT` (optional). |
| `liquidity` | 10 | OI + spread. |
| `budget_fit` | 10 | Cheaper contract = more upside per $. |
| `TRADE_THRESHOLD_SCORE` | 50 | Only surface picks ≥ this. |

## Alpha Vantage

| Constant | Default | Notes |
|----------|---------|-------|
| `AV_API_KEY` | env `AV_API_KEY`, else `PASTE_YOUR_KEY_HERE` | **No key in source.** Optional; enables sentiment. |
| `AV_DAILY_BUDGET` / `AV_CALLS_PER_MIN` | 25 / 5 | Free-tier limits. |

## Secrets note

No key ships in source. The previously-committed key was scrubbed; rotate it on
Alpha Vantage if you used it, and set the new one via `AV_API_KEY`.

---
Related: MODULES.md, OPERATIONS.md, SECURITY.md
