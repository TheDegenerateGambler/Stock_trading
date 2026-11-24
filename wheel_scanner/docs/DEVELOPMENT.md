---
Project:        wheel_scanner
Doc:            DEVELOPMENT.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Development - wheel_scanner

## Local setup

```
python -m venv .venv
.venv\Scripts\activate         # Windows
pip install -r requirements.txt
```

`.venv/`, `output/`, and `my_positions.json` are git-ignored. **A committed
`.venv/` was removed from this repo on 2026-11-23** - never commit the
virtualenv.

## Layout

```
wheel_scanner/
├── run_all.py             one-click orchestrator → mega dashboard
├── scan.py                CSP scan
├── scan_cc.py             covered-call scan (incl. --buy-write)
├── config.py             broker fees, budget, price band, watchlists
├── data_provider.py      yfinance prices + option chains (StockSnapshot)
├── wheel_analyzer.py     CSP scoring (WheelCandidate)
├── cc_analyzer.py        CC scoring (CCCandidate)
├── report_builder.py     put-side rendering
├── cc_report_builder.py  call-side rendering
├── mega_dashboard.py     combined HTML dashboard
├── my_positions.example.json   positions template
├── wheel.bat / run.bat / run_cc.bat   Windows launchers
├── requirements.txt
└── docs/
```

## Conventions

- **Config over literals** - broker fees, budget, price band, watchlists all in
  `config.py`; update CONFIGURATION.md in the same change.
- **CAD-first, NBDB-aware** - keep the fee model and affordability
  (`strike*100 <= budget`) accurate; FX is informational + `--usd-cad`.
- **Never lock in a loss** - CC-on-positions strikes stay at/above cost basis.
- **TSX `.TO` suffix** for yfinance; expect thin options data and degrade
  gracefully.
- **No secrets** - yfinance only; the sole personal file is `my_positions.json`
  (local, git-ignored).

## Adding a universe or scan section

1. Add the ticker list to `config.py`.
2. Wire a scan call into `run_all.py` and render it via the report builders.
3. Ensure `mega_dashboard.py` includes the new section + leaderboard rows.
4. Update CONFIGURATION.md, MODULES.md, CHANGELOG.md.

## Dependency-add policy

Prefer the existing stack (`yfinance`, `pandas`, `requests`, `lxml`). Justify
heavyweight additions and pin them in `requirements.txt`.

---
Related: TESTING.md, MODULES.md, CONFIGURATION.md
