---
Project:        options_daytrader
Doc:            DATA_FLOW.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Data Flow - options_daytrader

End-to-end trace of one scan (~10:05 ET). Example values are illustrative.

## Trigger

```
python daytrader.py            # loop every 5 min, 09:30-12:00 ET
python daytrader.py --once     # single scan then exit
python daytrader.py --force    # bypass the session gate
```

## Step-by-step

1. **Seed** (`config.PREMARKET_PICKS_JSON`): read
   `../premarket_scanner/output/premarket_picks.json` → up to 10 gap-up
   candidates (e.g. `NVDA`, `PLTR`, ...). Missing file → ETFs only.

2. **Score ETFs** (`signal_engine`) for SPY and QQQ using 1-/5-min bars:
   VWAP position, 9/20 EMA cross, RSI(14), MACD histogram, RVOL, gap, and AV
   sentiment, weighted by `SIGNAL_WEIGHTS`. e.g. SPY composite `+41` →
   **CALL** (≥ `TRADE_THRESHOLD_SCORE` 35).

3. **Score candidates** concurrently (`CONCURRENT_WORKERS`) with the same engine.

4. **Pick contracts** (`options_chain` + `options_ranker`) for each CALL/PUT:
   fetch chain (CBOE → yfinance), choose Δ 0.30-0.45 with OI > 500, vol > 100,
   spread ≤ 15%; expiry 0DTE for SPY/QQQ, next Friday otherwise. e.g. SPY
   `+0.38Δ` 0DTE call, mid `$1.80`.

5. **Risk levels**: from underlying ATR - stop `mid - ATR*0.5*|Δ|`, target
   `mid + ATR*1.0*|Δ|`, suggested max entry `mid * 1.05`.

6. **Report** (`report_builder`): write
   - `output/options_daytrader.html` (TradingView widgets, auto-refresh 60 s)
   - `output/options_daytrader.json`
   and print a console table (SPY, QQQ, best gap-up play, watchlist).

7. **Serve / loop**: report at `http://127.0.0.1:<port>/`; rescan every
   `INTERVAL_MIN`; exit at 12:00 ET.

## Data latency note

Option quotes (CBOE and yfinance) are ~15 minutes delayed; 1-min underlying
signals are current. Every scan is labelled accordingly.

## What crosses a boundary

- **Network (read-only):** CBOE delayed-quotes JSON, Yahoo/yfinance bars + chain
  fallback. TradingView widgets load in the browser viewing the report.
- **Disk:** reads the premarket seed JSON; writes only under `output/`.
- **Local HTTP:** report on `127.0.0.1` (localhost only).

---
Related: ARCHITECTURE.md, MODULES.md, OPERATIONS.md
