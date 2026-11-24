---
Project:        wheel_scanner
Doc:            ARCHITECTURE.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Architecture - wheel_scanner

A one-click scanner for **the Wheel** strategy (cash-secured puts + covered
calls) sized for a small Canadian account at National Bank Direct Brokerage
(NBDB). It scans cheap TSX names, TSX blue-chips, and liquid US names, scores
candidates, and builds a single HTML "mega dashboard".

## Module map

```
                 wheel.bat / run_all.py  (one-click orchestrator)
                        │
        ┌───────────────┼────────────────────────┐
        ▼               ▼                         ▼
     scan.py        scan_cc.py              (optional) my_positions.json
   (CSP scan)    (covered-call scan)        user holdings → CC vs cost basis
        │               │
        ▼               ▼
  wheel_analyzer    cc_analyzer
  (CSP scoring,     (CC scoring,
   WheelCandidate)   CCCandidate)
        │               │
        ▼               ▼
  data_provider.py  (yfinance prices + option chains; StockSnapshot)
        │
        ▼
  report_builder.py / cc_report_builder.py / mega_dashboard.py
  (per-scan HTML + the combined Top-10 mega dashboard)

              config.py  ← broker fees, budget, price band, watchlists
```

## Why each module exists

- **`run_all.py`** - the one-click orchestrator. Runs every scan (monthly/weekly
  CSPs + CCs across TSX-cheap, TSX blue-chip, and US universes, plus optional
  positions), aggregates a Top-10 leaderboard, and builds the mega dashboard.
  Errors in one section are caught so others still run.
- **`scan.py`** - cash-secured put (CSP) scan entry point.
- **`scan_cc.py`** - covered-call (CC) scan entry point (incl. buy-write).
- **`config.py`** - broker fee model, budget (`ACCOUNT_BUDGET_CAD` 1000), price
  band ($2-$10 CAD), FX assumptions, and the Canadian watchlists.
- **`data_provider.py`** - yfinance prices + option chains; `StockSnapshot`
  dataclass. TSX symbols use the `.TO` suffix.
- **`wheel_analyzer.py`** - CSP candidate scoring → `WheelCandidate`.
- **`cc_analyzer.py`** - covered-call candidate scoring → `CCCandidate`.
- **`report_builder.py` / `cc_report_builder.py`** - per-scan HTML/console
  rendering for puts / calls.
- **`mega_dashboard.py`** - the single combined HTML page: header, Top-10
  leaderboard, collapsible per-scan sections, client-side search, score badges.
- **`wheel.bat` / `run_cc.bat` / `run.bat`** - Windows launchers (venv setup +
  run + open the dashboard).

## Data flow

1. `run_all` picks universes from `config` (+ optional `my_positions.json`).
2. `data_provider` fetches prices + chains (yfinance).
3. `wheel_analyzer` / `cc_analyzer` score candidates (premium yield, liquidity,
   affordability vs. budget, strike vs. cost basis for positions).
4. `report_builder` / `cc_report_builder` render sections.
5. `mega_dashboard` combines them into `output/` HTML; the launcher opens it.

## Design properties

- **Small-account + NBDB-aware** - affordability (`strike*100 <= budget`) and the
  broker fee model are first-class.
- **Local-only, read-only market data** (yfinance). No API keys.
- **Optional personal holdings** - `my_positions.json` is user-provided, local,
  and git-ignored (see DATA_INVENTORY.md / PRIVACY.md).

---
Related: MODULES.md, DATA_FLOW.md, CONFIGURATION.md
