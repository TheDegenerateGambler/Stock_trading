---
Project:        options_daytrader
Doc:            OPERATIONS.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Operations - options_daytrader

## Install

```
cd Stock_trading/options_daytrader
pip install -r requirements.txt
```

## Prerequisite: premarket seed (optional but recommended)

The gap-up candidates come from the sibling scanner's output at
`../premarket_scanner/output/premarket_picks.json`. Run the premarket scanner
earlier in the morning to populate it. If the file is missing, the picker still
runs on SPY and QQQ only.

## Run

```
python daytrader.py              # loop every 5 min, 09:30-12:00 ET (opens browser)
python daytrader.py --once       # one scan then exit
python daytrader.py --force      # bypass the session gate (run any time)
python daytrader.py --interval 3 --no-browser --port 8770
run.bat                          # Windows launcher
```

The report is served locally (default port in `config.py`) and auto-refreshes
every 60 s with live TradingView widgets.

## Reading a pick

Each pick shows direction (CALL/PUT), confidence, the chosen contract (strike,
expiry, Δ, greeks), mid price, and ATR-derived entry/stop/target. A contract
flagged `LOW LIQUIDITY` means no contract passed the OI/volume/spread filters and
the closest ATM was used instead.

## Inspecting stored data

| File | Contents |
|------|----------|
| `output/options_daytrader.html` | Human-readable report with charts. |
| `output/options_daytrader.json` | Machine-readable picks. |

## Troubleshooting

| Symptom | Likely cause / fix |
|---------|--------------------|
| "outside session" / no run | Use `--force` to bypass the 09:30-12:00 ET gate. |
| Only SPY/QQQ, no gap-ups | Premarket seed JSON missing; run premarket_scanner first. |
| Quotes look stale | Expected - options feeds are ~15 min delayed; underlying signals are current. |
| CBOE fetch failed | Falls back to yfinance (Δ via Black-Scholes); a transient CBOE outage. |
| Port in use | Change with `--port N`. |

## Purging state

```
Remove-Item -Recurse -Force .\output
```

See RETENTION.md.

---
Related: CONFIGURATION.md, RETENTION.md, DEVELOPMENT.md
