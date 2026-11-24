---
Project:        wheel_scanner
Doc:            CONFIGURATION.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Configuration - wheel_scanner

Every tunable lives in `config.py` (plus a couple of CLI overrides).

## Broker fee model (NBDB)

| Constant | Default | Meaning |
|----------|---------|---------|
| `STOCK_COMMISSION` | 0.0 | Free stock trades at NBDB. |
| `OPTION_COMMISSION_PER_CONTRACT` | 6.95 | CAD options flat fee (to 6 contracts). |
| `OPTION_COMMISSION_PER_CONTRACT_USD` | 1.25 | US options approx (verify). |
| `OPTION_MAX_FLAT_CONTRACTS` | 6 | Flat-pricing contract cap. |
| `FX_SPREAD_ESTIMATE` | 0.015 | ~1.5% FX cost (informational). |
| `DEFAULT_USD_CAD` | 1.36 | CAD per USD; override with `--usd-cad`. |

## Account settings

| Constant | Default | Meaning |
|----------|---------|---------|
| `ACCOUNT_BUDGET_CAD` | 1000.0 | Cash available to secure a put. |
| `MAX_STOCK_PRICE_CAD` | 10.00 | Only consider names at/under this. |
| `MIN_STOCK_PRICE_CAD` | 2.00 | Avoid true penny stocks. |
| `CONTRACT_SIZE` | 100 | Shares per equity option contract. |

Affordability filter: a CSP is in-budget when `strike * CONTRACT_SIZE <=
ACCOUNT_BUDGET_CAD`.

## Watchlists

| Constant | Meaning |
|----------|---------|
| `CANADIAN_WHEEL_WATCHLIST` | Cheap TSX names (`.TO`) with MX-listed options. |
| (US / blue-chip lists) | Liquid US names + TSX blue-chips used by the weekly scans. |

Edit the lists to add/remove names. TSX symbols use the yfinance `.TO` suffix.

## Output

| Constant | Meaning |
|----------|---------|
| `OUTPUT_DIR` | Where reports/dashboard are written. |
| `DASHBOARD_HTML` | Path of the combined mega dashboard. |

## CLI overrides

| Flag | Applies to | Meaning |
|------|-----------|---------|
| `--usd-cad` | `run_all.py` / scans | Override the FX rate for the run. |
| `--buy-write` | `scan_cc.py` | Score buy-write covered calls. |

## Secrets note

This project uses **no API keys** (yfinance only). The only user-provided file is
`my_positions.json` (personal holdings), which is local and git-ignored.

---
Related: MODULES.md, OPERATIONS.md, SECURITY.md
