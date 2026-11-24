---
Project:        wheel_scanner
Doc:            OPERATIONS.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Operations - wheel_scanner

## One-click usage

```
wheel.bat
```

Double-click (or run) `wheel.bat`. It sets up its own virtualenv on the first
run, scans everything (monthly + weekly puts + calls across cheap TSX names, TSX
blue-chips, and liquid US names), builds one HTML dashboard with a Top-10
leaderboard + live search, and opens it in your browser.

## Manual install / run

```
python -m venv .venv
.venv\Scripts\activate         # Windows
pip install -r requirements.txt
python run_all.py              # full mega dashboard
python scan.py                 # puts only
python scan_cc.py --buy-write  # calls only (buy-write)
python run_all.py --usd-cad 1.38   # override FX
```

Requires `yfinance`, `requests`, `pandas`, `lxml`.

## Optional: track your existing positions

Copy `my_positions.example.json` to `my_positions.json` and fill in holdings:

```json
[
  {"ticker": "BTO.TO", "cost_basis": 4.85, "shares": 100},
  {"ticker": "F",      "cost_basis": 11.80, "shares": 100}
]
```

The next run adds a **"Covered Calls - Your Positions"** section with strikes
at/above your cost basis (never lock in a loss). If the file is absent, the
section is silently skipped. **This file holds personal financial data - keep it
local; it is git-ignored.**

## Inspecting stored data

| Path | Contents |
|------|----------|
| `output/` dashboard HTML | The combined report you open. |
| `output/` intermediate JSON | Per-scan data (if written). |
| `my_positions.json` | Your holdings (only if you created it). |

## Troubleshooting

| Symptom | Likely cause / fix |
|---------|--------------------|
| Sparse/empty option data on a TSX name | Yahoo options data for TSX can be thin/delayed; verify with your broker. |
| A section shows an error banner | That scan failed; others still ran - check the banner message. |
| Positions section missing | `my_positions.json` not present or malformed. |
| FX looks off | Pass `--usd-cad` with the current rate. |

## Purging state

```
Remove-Item -Recurse -Force .\output
# and, if you created it:
Remove-Item -Force .\my_positions.json
```

See RETENTION.md for the full procedure.

---
Related: CONFIGURATION.md, RETENTION.md, DEVELOPMENT.md
