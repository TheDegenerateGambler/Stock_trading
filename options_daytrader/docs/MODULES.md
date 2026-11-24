---
Project:        options_daytrader
Doc:            MODULES.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Modules - options_daytrader

Per-file reference. In-code docstrings are authoritative for fine detail.

## `config.py`
Session (`START_*`/`STOP_*` 09:30-12:00 ET, `INTERVAL_MIN` 5), `ETF_TICKERS`
(SPY, QQQ), `SIGNAL_WEIGHTS` (vwap 20, ema_cross 20, rsi 10, macd 15, rvol 10,
sentiment 15, gap 10), `TRADE_THRESHOLD_SCORE` (35), contract rules
(`DELTA_MIN/MAX` 0.30-0.45, `MIN_OI` 500, `MIN_VOLUME` 100, `MAX_SPREAD_PCT`
0.15, expiry modes), ATR multipliers (`ATR_STOP_MULT` 0.5, `ATR_TARGET_MULT`
1.0), `UNUSUAL_WHALES_*` (stub, token from env), `CONCURRENT_WORKERS` (8),
`PREMARKET_PICKS_JSON` seed path. See CONFIGURATION.md.

## `daytrader.py`
Entry point.
- `_Handler` - quiet localhost `SimpleHTTPRequestHandler` (no-cache) serving
  `output/`.
- scan loop: seed → score ETFs + candidates → rank contracts → report; every
  `INTERVAL_MIN`; exits at the ET stop time.
- `main()` - argparse (`--once`, `--force`, `--interval N`, `--no-browser`,
  `--port N`), starts the server, runs the loop.

## `signal_engine.py`
- computes per-ticker 1-/5-min indicators (VWAP position, 9/20 EMA cross,
  RSI(14), MACD histogram, RVOL, gap) + AV sentiment, combines them with
  `SIGNAL_WEIGHTS` into a composite score in [-100, +100]; maps to
  CALL / PUT / NO-TRADE with a confidence from `TRADE_THRESHOLD_SCORE`.

## `options_chain.py`
- fetches an options chain: **CBOE first** (`cboe_client`), **yfinance fallback**
  (`Ticker.option_chain()`); normalises contracts into a common shape.

## `cboe_client.py`
- CBOE delayed-quotes JSON client
  (`cdn.cboe.com/api/global/delayed_quotes/options/{sym}.json`); returns
  contracts with native greeks (Δ Γ Θ ν).

## `options_ranker.py`
- selects a contract in the Δ 0.30-0.45 band meeting `MIN_OI`, `MIN_VOLUME`, and
  `MAX_SPREAD_PCT`; chooses expiry per policy (0DTE for ETFs, next Friday
  otherwise); falls back to closest ATM flagged `LOW LIQUIDITY`; attaches
  entry/stop/target from underlying ATR.

## `call_flow.py`
- optional options-flow analysis path (CLI-capable); contributes a flow signal
  when enabled.

## `unusualwhales_stub.py`
- stub for an Unusual Whales flow integration; inert unless
  `UNUSUAL_WHALES_ENABLED` and a token are set.

## `report_builder.py`
- renders the console table, the HTML report (live TradingView chart widgets +
  options-chain link-outs, auto-refresh 60 s) → `output/options_daytrader.html`,
  and `output/options_daytrader.json`.

---
Related: ARCHITECTURE.md, CONFIGURATION.md, DATA_FLOW.md
