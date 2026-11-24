---
Project:        options_daytrader
Doc:            CONFIGURATION.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Configuration - options_daytrader

Every tunable lives in `config.py`.

## Session

| Constant | Default | Meaning |
|----------|---------|---------|
| `START_HOUR_ET` / `START_MIN_ET` | 9 / 30 | Session start (ET). |
| `STOP_HOUR_ET` / `STOP_MIN_ET` | 12 / 0 | Auto-exit time (ET). |
| `INTERVAL_MIN` | 5 | Minutes between scans. |
| `ETF_TICKERS` | `["SPY", "QQQ"]` | Always scanned. |

## Signal scoring

| Constant | Default | Meaning |
|----------|---------|---------|
| `SIGNAL_WEIGHTS` | vwap 20, ema_cross 20, rsi 10, macd 15, rvol 10, sentiment 15, gap 10 | Weights for the composite score in [-100, +100]. |
| `TRADE_THRESHOLD_SCORE` | 35 | abs score ≥ this ⇒ CALL (bull) / PUT (bear); else NO-TRADE. |

## Contract selection

| Constant | Default | Meaning |
|----------|---------|---------|
| `DELTA_MIN` / `DELTA_MAX` | 0.30 / 0.45 | Target delta band. |
| `MIN_OI` | 500 | Minimum open interest. |
| `MIN_VOLUME` | 100 | Minimum contract volume. |
| `MAX_SPREAD_PCT` | 0.15 | Max `(ask-bid)/mid`. |
| `ETF_EXPIRY_MODE` | `0DTE` | Expiry policy for SPY/QQQ (`0DTE`/`NEAREST`/`NEXT_FRIDAY`). |
| `OTHER_EXPIRY_MODE` | `NEXT_FRIDAY` | Expiry policy for other tickers. |

## Risk / reward (from underlying ATR)

| Constant | Default | Meaning |
|----------|---------|---------|
| `ATR_STOP_MULT` | 0.5 | Stop = `mid - ATR * this * |Δ|`. |
| `ATR_TARGET_MULT` | 1.0 | Target = `mid + ATR * this * |Δ|`. |

## Data sources / misc

| Constant | Default | Meaning |
|----------|---------|---------|
| `UNUSUAL_WHALES_ENABLED` | `False` | Enable the flow stub. |
| `UNUSUAL_WHALES_TOKEN` | env `UNUSUAL_WHALES_TOKEN` | Flow API token (never hardcode). |
| `CONCURRENT_WORKERS` | 8 | Threads for scanning candidates. |
| `PREMARKET_PICKS_JSON` | `../premarket_scanner/output/premarket_picks.json` | Gap-up seed from the sibling project. |

## Secrets note

Any flow token must come from the environment (`UNUSUAL_WHALES_TOKEN`); never
commit it. This project needs no Alpha Vantage key of its own - it reuses the
premarket scanner's sentiment output.

---
Related: MODULES.md, OPERATIONS.md, SECURITY.md
