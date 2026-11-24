---
Project:        options_daytrader
Doc:            ARCHITECTURE.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Architecture - options_daytrader

A live options picker for the 09:30-12:00 ET window. Each scan it answers:
"CALLS or PUTS right now, and which contract?" - always for SPY and QQQ, plus
the best qualifying gap-up play seeded from the premarket_scanner.

## Module map

```
                 daytrader.py  (entry + 5-min loop + local HTTP server)
                        │
        ┌───────────────┼───────────────┬───────────────┐
        ▼               ▼               ▼               ▼
  signal_engine.py  options_chain.py  options_ranker.py  report_builder.py
  (VWAP/EMA/RSI/    (CBOE first,      (pick contract by   (console + HTML
   MACD/RVOL/gap/    yfinance          Δ/OI/vol/spread +   with TradingView
   sentiment →       fallback)         ATR stop/target)    widgets + JSON)
   score -100..100)        │
        │                  ▼
        │            cboe_client.py  (delayed_quotes JSON + native greeks)
        │            call_flow.py / unusualwhales_stub.py (optional flow)
        ▼
  seeds: ../premarket_scanner/output/premarket_picks.json

               config.py  ← session, weights, contract rules (imported by all)
```

## Why each module exists

- **`daytrader.py`** - entry point; runs the 5-min scan loop during the session,
  serves the report over a localhost HTTP server, auto-exits at 12:00 ET.
- **`config.py`** - session window, `SIGNAL_WEIGHTS`, `TRADE_THRESHOLD_SCORE`,
  contract-selection rules (Δ band, OI/volume/spread, expiry policy), ATR
  stop/target multipliers, premarket seed path.
- **`signal_engine.py`** - computes the composite directional score in
  [-100, +100] from VWAP, 9/20 EMA cross, RSI, MACD histogram, RVOL, gap, and AV
  sentiment, weighted by `SIGNAL_WEIGHTS`.
- **`options_chain.py`** - fetches the chain (CBOE primary, yfinance fallback).
- **`cboe_client.py`** - CBOE delayed-quotes JSON client; provides native greeks
  (Δ Γ Θ ν).
- **`options_ranker.py`** - selects a contract in the Δ 0.30-0.45 band meeting
  OI/volume/spread rules; attaches entry/stop/target from the underlying ATR.
- **`call_flow.py` / `unusualwhales_stub.py`** - optional options-flow signal
  (stub unless enabled/credentialed).
- **`report_builder.py`** - console table + HTML report (live TradingView
  widgets, auto-refresh) + JSON.

## Data flow

1. `config.PREMARKET_PICKS_JSON` seeds gap-up candidates from premarket_scanner.
2. `signal_engine` scores SPY, QQQ, and each candidate → CALL / PUT / NO-TRADE.
3. For actionable signals, `options_chain` + `options_ranker` pick a contract
   and compute stop/target.
4. `report_builder` writes `output/options_daytrader.html` + `.json`.
5. `daytrader`'s HTTP server serves the report locally.

## Design properties

- **Local-only; read-only delayed data.** Option quotes are ~15 min delayed
  (CBOE & yfinance); 1-min underlying signals are current. The picker labels this.
- **Budget-free for options** (CBOE JSON is free); reuses AV sentiment already
  computed by premarket_scanner.
- **Time-boxed** to the 09:30-12:00 ET session; `--force` bypasses the gate.

---
Related: MODULES.md, DATA_FLOW.md, CONFIGURATION.md
