---
Project:        daytrade_picker
Doc:            DATA_FLOW.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Data Flow - daytrade_picker

End-to-end trace of one scan. Example values are illustrative.

## Trigger

```
python pick.py              # loop every 30 min
python pick.py --once       # one scan then exit
```

## Step-by-step

1. **Candidates** (`alphavantage`): fetch top gainers / most active → take
   `SCAN_CANDIDATES` (20). e.g. `NVDA, PLTR, SOFI, ...`.

2. **Technicals** (`indicators`): for each candidate compute EMA, MACD, VWAP,
   ATR from recent bars.

3. **Sentiment** (`alphavantage` NEWS_SENTIMENT): normalised score per candidate
   (subject to the AV budget).

4. **Score** (`scorer`): combine technicals + sentiment into a LONG/SHORT
   conviction; attach entry, stop, and a 2:1 R:R target. Keep `TOP_N_PICKS` (10).
   e.g. `NVDA` → LONG, entry 120.50, stop 119.30, target 122.90.

5. **Regime** (`market_regime.fetch_regime`): SPY/QQQ/IWM day change + VIX →
   banner (e.g. "Risk-on, VIX 13.4") or "Market data unavailable" on failure.

6. **News sidebar** (`walter_bloomberg`): latest RSS headlines (up to
   `MAX_WALTER_ITEMS`), refreshed by a background thread every
   `WALTER_REFRESH_MIN` minutes.

7. **Report** (`report_builder` + `html_styles`): write
   - `output/report.html` (auto-refresh)
   - `output/live_data.json`

8. **Serve / loop** (`pick`): report at `http://127.0.0.1:8766/report.html`;
   rescan every `REFRESH_INTERVAL` (plus a midday rescan).

## What crosses a boundary

- **Network (read-only):** Alpha Vantage (screener + sentiment), Yahoo/yfinance
  (bars + regime), Walter Bloomberg RSS (headlines).
- **Disk:** writes only under `output/`.
- **Local HTTP:** report on `127.0.0.1:8766` (localhost only).

---
Related: ARCHITECTURE.md, MODULES.md, OPERATIONS.md
