---
Project:        daytrade_picker
Doc:            OPERATIONS.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Operations - daytrade_picker

## Install

```
cd daytrade_picker
pip install -r requirements.txt
```

## Alpha Vantage key

Set it via environment variable (no key ships in source):

```
set AV_API_KEY=YOUR_KEY_HERE        # Windows
# export AV_API_KEY=YOUR_KEY_HERE   # macOS/Linux
```

Get a free key at https://www.alphavantage.co/support/#api-key . Without a key,
AV-dependent features (screener + sentiment) are disabled.

## Run

```
python pick.py                 # full run, 30-min interval (opens browser)
python pick.py --once          # one scan then exit
python pick.py --no-browser    # skip auto-open
python pick.py --interval 15   # scan every 15 min
python pick.py --port 9000     # custom HTTP port
run.bat                        # Windows launcher
```

The report opens at `http://127.0.0.1:8766/report.html` and auto-refreshes.

## Inspecting stored data

| File | Contents |
|------|----------|
| `output/report.html` | Human-readable report (picks, regime, news). |
| `output/live_data.json` | Machine-readable picks + live data. |

## Troubleshooting

| Symptom | Likely cause / fix |
|---------|--------------------|
| No picks / AV errors | Missing key or daily budget (25 calls) spent. |
| Regime banner "unavailable" | yfinance fetch failed this cycle; non-fatal, retries next scan. |
| Empty news sidebar | RSS fetch failed/slow; refreshes every `WALTER_REFRESH_MIN`. |
| Port in use | Use `--port N`. |

## Purging state

```
Remove-Item -Recurse -Force .\output
```

See RETENTION.md.

---
Related: CONFIGURATION.md, RETENTION.md, DEVELOPMENT.md
