---
Project:        wheel_scanner
Doc:            DATA_FLOW.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Data Flow - wheel_scanner

End-to-end trace of one `wheel.bat` / `run_all.py` run. Example values are
illustrative.

## Trigger

```
wheel.bat                 # one-click: venv + run_all.py + open dashboard
python run_all.py         # same, without the launcher
python scan.py            # puts only
python scan_cc.py --buy-write   # calls only (buy-write)
```

## Step-by-step

1. **Config + universes** (`config`): budget $1,000 CAD, price band $2-$10 CAD,
   watchlists (TSX-cheap, TSX blue-chip, US). FX default 1.36 (override
   `--usd-cad`).

2. **Optional positions**: if `my_positions.json` exists, load the user's
   holdings (e.g. `{"ticker":"BTO.TO","cost_basis":4.85,"shares":100}`) for the
   "Covered Calls - Your Positions" section.

3. **Market data** (`data_provider`): for each ticker, yfinance price snapshot +
   option chain. e.g. `BTO.TO` price $4.90 CAD.

4. **Score CSPs** (`wheel_analyzer`): for affordable strikes
   (`strike*100 <= budget`), compute annualised premium yield + liquidity →
   `WheelCandidate` with a score. e.g. `BTO.TO` $4.50 put, 30 DTE → score 72.

5. **Score CCs** (`cc_analyzer`): buy-write economics for the same names; for
   positions, only strikes ≥ cost basis (never lock in a loss).

6. **Aggregate + render**: `report_builder` / `cc_report_builder` build each
   section; `run_all` computes the **Top-10 Overall** leaderboard across all
   sections.

7. **Mega dashboard** (`mega_dashboard`): one HTML page with header, Top-10,
   collapsible sections, client-side search, and score badges → written under
   `output/`.

8. **Open**: the launcher opens the dashboard in the default browser.

## What crosses a boundary

- **Network (read-only):** Yahoo/yfinance prices + option chains.
- **Disk:** reads optional `my_positions.json`; writes the dashboard + any
  intermediate JSON under `output/`.
- **No HTTP server** - the dashboard is a static file opened directly (unlike the
  other scanners).

---
Related: ARCHITECTURE.md, MODULES.md, OPERATIONS.md
