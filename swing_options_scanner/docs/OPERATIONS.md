---
Project:        swing_options_scanner
Doc:            OPERATIONS.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Operations - swing_options_scanner

## Install

```
cd Stock_trading/swing_options_scanner
pip install -r requirements.txt
```

## Alpha Vantage key (optional, for sentiment)

```
set AV_API_KEY=YOUR_KEY_HERE        # Windows
# export AV_API_KEY=YOUR_KEY_HERE   # macOS/Linux
```

No key ships in source. Without one the scanner still runs; the sentiment
component of the score is simply unavailable.

## Run

```
python scanner.py        # full scan then serve the report
run.bat                  # Windows launcher
```

The HTML report auto-refreshes every 5 minutes and embeds a TradingView daily
chart per pick.

## Reading a pick

Each card shows ticker, direction, composite score, the chosen contract
(strike/expiry/Δ), cost vs. budget, break-even, +50%/+100% targets, -40% stop,
R:R, the 14-day time stop, and earnings status.

## Inspecting stored data

| File | Contents |
|------|----------|
| `output/swing_options_scanner.html` | Human-readable ranked report. |
| `output/swing_picks.json` | Machine-readable picks. |
| `output/earnings_cache.json` | Cached next-earnings dates. |

## Troubleshooting

| Symptom | Likely cause / fix |
|---------|--------------------|
| Few/no picks | Market offers little meeting all filters (score ≥ 50, budget, DTE, Δ); loosen a threshold in `config.py`. |
| Sentiment absent | No AV key or budget spent; scoring proceeds without it. |
| A ticker skipped | Earnings within `SKIP_EARNINGS_DAYS`. |
| First run slow | Building the universe + warming the earnings cache. |
| Port in use | Stop the conflicting process or change the port. |

## Purging state

```
Remove-Item -Recurse -Force .\output
```

Also clears the earnings cache; see RETENTION.md.

---
Related: CONFIGURATION.md, RETENTION.md, DEVELOPMENT.md
