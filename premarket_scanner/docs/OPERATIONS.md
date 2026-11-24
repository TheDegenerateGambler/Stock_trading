---
Project:        premarket_scanner
Doc:            OPERATIONS.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Operations - premarket_scanner

## Install

```
cd Stock_trading/premarket_scanner
pip install -r requirements.txt
```

Dependencies: `yfinance`, `requests`, `pandas`, `lxml` (Wikipedia scraping).

## Alpha Vantage key (optional, for sentiment)

Set it via environment variable (no key ships in source):

```
set AV_API_KEY=YOUR_KEY_HERE        # Windows
# export AV_API_KEY=YOUR_KEY_HERE   # macOS/Linux
```

Without a key the scanner still runs; news falls back to yfinance headlines.

## Run

```
python scanner.py            # loop every 20 min until 9:20 AM ET
python scanner.py --once     # one scan then exit
run.bat                      # Windows launcher
```

The report is served at `http://127.0.0.1:8767/premarket_report.html` and
auto-refreshes every 60 s.

## Inspecting stored data

Everything written is under `output/`:

| File | Contents |
|------|----------|
| `output/premarket_report.html` | Human-readable report. |
| `output/premarket_picks.json` | Machine-readable top picks (also read by options_daytrader). |
| universe cache | Cached ticker universe (~7-day TTL). |

## Troubleshooting

| Symptom | Likely cause / fix |
|---------|--------------------|
| 0 picks | Outside the 04:00-09:30 ET premarket window (expected), or nothing gapped > 5%. |
| First run slow (~30-60 s) | Building the universe cache from Wikipedia. |
| Sentiment all Neutral | AV key missing or daily budget spent → yfinance fallback. |
| Port in use | Another process holds 8767; stop it or change the port. |
| Wikipedia 403 | Scrape blocked; the static `FALLBACK_UNIVERSE` is used. |

## Purging state

```
Remove-Item -Recurse -Force .\output
```

Also clears the universe cache; see RETENTION.md.

---
Related: CONFIGURATION.md, RETENTION.md, DEVELOPMENT.md
