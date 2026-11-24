---
Project:        wheel_scanner
Doc:            MODULES.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Modules - wheel_scanner

Per-file reference. In-code docstrings are authoritative for fine detail.

## `config.py`
Broker fee model (`STOCK_COMMISSION` 0, `OPTION_COMMISSION_PER_CONTRACT` 6.95
CAD, USD variant, flat-to-6-contracts), FX (`FX_SPREAD_ESTIMATE`,
`DEFAULT_USD_CAD` 1.36), account settings (`ACCOUNT_BUDGET_CAD` 1000,
`MIN/MAX_STOCK_PRICE_CAD` 2-10, `CONTRACT_SIZE` 100), and the Canadian / US
watchlists. Also output paths (`OUTPUT_DIR`, `DASHBOARD_HTML`). See
CONFIGURATION.md.

## `run_all.py`
One-click orchestrator.
- `main() -> int` - runs all scan sections (monthly/weekly CSP + CC across
  TSX-cheap, TSX blue-chip, US; optional positions), builds the Top-10
  leaderboard, and writes the mega dashboard. Accepts `--usd-cad`. Section
  errors are caught and surfaced as banners.

## `scan.py`
- CSP scan entry. `parse_args()` + `main()` - scan the put side and render a
  report.

## `scan_cc.py`
- Covered-call scan entry (incl. `--buy-write`). `parse_args()` + `main()`.

## `data_provider.py`
- `StockSnapshot` dataclass (ticker, price, currency, name, avg_volume,
  market_cap, dividend_yield).
- `get_stock_snapshot(ticker) -> StockSnapshot|None` and option-chain fetchers
  via yfinance (`.TO` suffix for TSX). Degrades gracefully on sparse/missing
  data.

## `wheel_analyzer.py`
- `WheelCandidate` dataclass + CSP scoring: annualised premium yield, option
  liquidity, affordability (`strike*100 <= budget`), and overall score.

## `cc_analyzer.py`
- `CCCandidate` dataclass + covered-call scoring, incl. buy-write economics and
  (for positions) strikes at/above cost basis so a loss is never locked in.

## `report_builder.py` / `cc_report_builder.py`
- Render the put / call sections to console + HTML fragments consumed by the
  mega dashboard.

## `mega_dashboard.py`
- Builds the single combined HTML page: header (budget/FX/timestamp/duration),
  combined Top-10 leaderboard, collapsible per-scan sections, client-side search,
  colored score badges. Writes to `config.DASHBOARD_HTML`.

## Launchers
- `wheel.bat` - set up venv (first run) + run `run_all.py` + open the dashboard.
- `run_cc.bat` / `run.bat` - targeted launchers for the CC / put scans.

## `my_positions.example.json`
- Template the user copies to `my_positions.json` to track existing holdings
  (`ticker`, `cost_basis`, `shares`). If absent, the positions section is
  skipped.

---
Related: ARCHITECTURE.md, CONFIGURATION.md, DATA_FLOW.md
