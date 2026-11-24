# 📋 DayTrade Picker — Feature Log

> **Repo:** `daytrade_picker`
> **Type:** Python 3 CLI + local HTTP dashboard
> **License:** _unspecified_ (personal project)
> **Last major update:** 2026-07-10

---

## 🎯 Overview

**DayTrade Picker** is a standalone Python app that scans US equities every 30 minutes and picks the top 10 high-conviction day-trade candidates as **LONG** or **SHORT**. It combines:

- **Alpha Vantage** free tier (top movers screener + per-ticker news sentiment)
- **yfinance** (intraday bars, options chain, market regime — free)
- **Walter Bloomberg RSS** (real-time macro headlines sidebar)

Output is dual: a formatted console summary and a live-refreshing HTML report at `http://127.0.0.1:8766/report.html` that opens in the browser automatically. Each pick includes entry, ATR-based stop, and 2:1 R:R target.

Built for a solo trader running against the AV free-tier daily budget (25 calls/day). Designed so the expensive AV calls happen twice per day (morning + midday) and all subsequent refreshes are yfinance-only.

---

## 🧩 Core Features

### 🔹 Two-Tier Scanning Strategy
- **Morning scan** (first run) — 1 AV screener call + up to 10 AV sentiment calls
- **Midday refresh** (11:00 AM – 1:00 PM ET, auto) — 1 AV screener + up to 7 sentiment
- **Loop refresh** (every 30 min after) — yfinance only, 0 AV calls
- Daily AV budget ≈ 19–21 of 25 calls, leaving 4–6 buffer

### 🔹 Candidate Sourcing (`scorer.build_candidates`)
- Pulls top gainers/losers/most-active from AV `TOP_GAINERS_LOSERS`
- Merges the three lists, deduplicates, keeps up to `SCAN_CANDIDATES` (default 20)
- Filters out penny stocks (< `MIN_PRICE`) and thin volume (< `MIN_AVG_VOLUME`)

### 🔹 Signal Scoring (`scorer.py`)
Each candidate is scored against 8 signals; needs **3+ bull** for LONG, **3+ bear** for SHORT:

| Signal | Bull condition | Bear condition |
|---|---|---|
| RSI (14) | 30–65 | > 65 (overbought) |
| MACD histogram | rising | falling |
| Price vs VWAP | above | below |
| Relative volume | ≥ 2× | — |
| Gap | up ≥ 1% | down ≤ −1% |
| Options flow | calls > puts (open interest) | puts > calls |
| AV news sentiment | score ≥ 0.65 | score ≤ 0.35 |
| Market regime | bull | bear |

### 🔹 Technical Indicators (`indicators.py`)
- Pure-Python RSI, MACD, VWAP, ATR — no `talib` dependency
- Feeds off 5-min bars from yfinance

### 🔹 Market Regime (`market_regime.py`)
- Fetches SPY, QQQ, IWM, VIX via yfinance (free)
- Classifies bias: BULL / BEAR / CHOPPY
- VIX thresholds: > 20 elevated, > 30 extreme (skip longs)
- Provides guidance line for the report banner

### 🔹 Walter Bloomberg RSS Sidebar (`walter_bloomberg.py`)
- Fetches `https://feeds.feedburner.com/WalterBloombergMacro` every 5 min in a background thread
- Fallback URL if primary fails
- Cap of 30 headlines in the sidebar
- Runs independently of the scan loop

### 🔹 Risk / Reward
- Entry = current price
- Stop = entry ± (`ATR_STOP_MULT` × ATR)  (default 1.0×)
- Target = entry ± (`ATR_TARGET_MULT` × ATR) (default 2.0×)
- Enforces minimum 2:1 R:R

### 🔹 Local HTTP Dashboard
- `pick.py` starts a `ThreadingTCPServer` on `HTTP_PORT` (default 8766)
- Auto-finds next open port if 8766 is taken
- Serves `output/report.html` with no-store cache headers
- Auto-opens browser on first run (opt-out via `--no-browser`)
- Report is re-rendered after every scan; browser page auto-refreshes

### 🔹 Rate Limiting & Caching (`alphavantage.py`)
- Rate limiter: max `AV_CALLS_PER_MIN` (5/min)
- Daily budget tracking with `remaining_budget()`, `get_budget_status()`
- Top-movers response cached 30 min to avoid duplicate calls within a scan cycle

---

## 🎛️ Configuration / Inputs

All in `config.py`:

| Setting | Default | Purpose |
|---|---|---|
| `AV_API_KEY` | env `AV_API_KEY` or hardcoded | Alpha Vantage free-tier key |
| `AV_DAILY_BUDGET` | 25 | Free tier daily call limit |
| `AV_CALLS_PER_MIN` | 5 | Free tier rate limit |
| `TOP_N_PICKS` | 10 | Final picks shown |
| `SCAN_CANDIDATES` | 20 | How many to score per scan |
| `REFRESH_INTERVAL` | 30 | Minutes between scans |
| `WALTER_REFRESH_MIN` | 5 | RSS refresh cadence |
| `RSI_OVERSOLD` / `RSI_OVERBOUGHT` | 35 / 65 | RSI thresholds |
| `RVOL_HIGH` | 2.0 | Relative volume threshold |
| `MIN_PRICE` | 5.0 | Skip penny stocks |
| `MIN_AVG_VOLUME` | 500,000 | Skip thin volume |
| `ATR_STOP_MULT` / `ATR_TARGET_MULT` | 1.0 / 2.0 | Risk multipliers |
| `HTTP_PORT` | 8766 | Local server port |
| `VIX_HIGH_THRESHOLD` / `VIX_EXTREME` | 20 / 30 | Regime risk thresholds |

CLI flags (`pick.py`):
- `--once` — one scan then exit
- `--no-browser` — don't auto-open browser
- `--interval N` — override REFRESH_INTERVAL
- `--port N` — override HTTP_PORT

---

## 🔔 Alerts / Outputs

**Console:** formatted table with rank, ticker, direction arrow, entry/stop/target, top signals, and top headline. Ends with AV budget status + regime guidance + risk disclaimer.

**HTTP endpoint:** `http://127.0.0.1:8766/report.html`
- Pick cards with sentiment bar, entry/stop/target
- Walter Bloomberg macro sidebar (auto-refreshing)
- Market regime banner (VIX/SPY/QQQ)

**Files written to `output/`:**
- `report.html` — full report
- `live_data.json` — JSON snapshot (picks + regime + timestamp)
- Walter Bloomberg live data (via `report_builder.write_live_walter`)

---

## 📜 Change Log

### 2026-07-10 (session 1) — Docs backfilled
- Created this `FEATURE_LOG.md` from source-code + README inspection.
- Added `docs/README.md` pointer to workspace-wide docs.
- Flagged hardcoded AV API key in `config.py` as a security TODO (see below).
- No source-code changes.

### _(Pre-docs history)_ — Working, feature-complete
Project already had a mature `README.md` prior to docs standardisation. Feature history before 2026-07-10 was not captured session-by-session; the README serves as the effective baseline. Future sessions should log incremental changes here.

---

## 🚧 Deferred Ideas / Backlog

### 🔐 Move AV key out of source
**Status:** ✅ fixed (2026-11-23) — key scrubbed from source
**Summary:** `config.py:11` previously hardcoded a real Alpha Vantage key as the
`AV_API_KEY` fallback. It is now `os.getenv("AV_API_KEY", "PASTE_YOUR_KEY_HERE")`,
so the key must come from the `AV_API_KEY` environment variable (or a local,
git-ignored `.env`). **Action still required by the owner:** the previously
committed key must be rotated (regenerated) on Alpha Vantage, since it was on
disk and is considered burned.

### 🔗 Bridge to TradingView LMC indicator
**Status:** idea only
**Summary:** Right now, moving from a pick in the DayTrade dashboard to the LMC-annotated TradingView chart is manual (copy ticker, paste). Options to close the loop:
1. Deep-link each pick card to `https://www.tradingview.com/chart/?symbol=<TICKER>` (easiest — one-line HTML change)
2. Copy-to-clipboard button per ticker
3. Write picks to a local `.txt` watchlist file that TradingView can import

### 🧪 Backtest mode
**Status:** idea only
**Summary:** Add `--backtest YYYY-MM-DD` that runs the scan against historical AV/yfinance data and measures how the picks would have performed intraday (peak favorable excursion vs 1×ATR stop). Would help calibrate the 3-signal threshold and ATR multipliers.

### 📊 Pick outcome tracking
**Status:** idea only
**Summary:** After each scan, append picks to `output/history.jsonl` with timestamp. On the next scan, look up prior picks' actual EOD/close prices and compute rolling hit rate. Show a "past week accuracy" widget in the sidebar.

### 🛰️ Discord / Telegram webhook
**Status:** idea only
**Summary:** Fire a webhook when a scan produces ≥ N picks with strong signals (e.g. 5+ bull signals in one direction). Useful when not sitting in front of the browser.

### 🇪🇺 Session-aware scanning
**Status:** idea only
**Summary:** Currently the loop runs 24/7. Should optionally clamp to US market hours (9:30 AM – 4:00 PM ET) and pause between sessions to save API budget.

### 🏷️ Sector diversification filter
**Status:** idea only
**Summary:** Right now the top-10 could all be tech. Optionally cap picks per sector (e.g. max 3 per GICS sector) to force diversification.

---

## 🐛 Debugging Reference

### Python / stdlib gotchas
- **`sys.stdout.reconfigure`** used at top of `pick.py` to force UTF-8 on Windows — needed for emoji/box-drawing characters in console output. Don't remove.
- **`socketserver.ThreadingTCPServer`** with `daemon_threads = True` — clean shutdown on Ctrl-C. Ensure any new server code sets this.
- **Port collision handling:** `_find_port()` tries up to 20 sequential ports before giving up. If dev is running multiple instances, actual port may differ from `--port`.
- **Walter Bloomberg RSS is unreliable** — feedburner has been flaky; the fallback `walter-bloomberg.com/feed/` should always be checked when adding new RSS logic.

### yfinance gotchas
- **Options chain calls can fail** for tickers without listed options — always guard with try/except and fall back to a neutral flow reading.
- **`Ticker.history(period="1d", interval="5m")`** occasionally returns an empty DataFrame outside RTH. Check `df.empty` before indexing.
- **Rate limits are undocumented** — yfinance scrapes Yahoo, so aggressive parallel calls will get throttled. Keep the scan sequential.

### Alpha Vantage gotchas
- **Free tier rate limit is enforced silently** — exceeding 5 calls/min returns a JSON payload with an `Information` field instead of the expected data. `alphavantage.py` handles this; new code must too.
- **Daily budget resets at midnight US Eastern**, not UTC.
- **Sentiment endpoint** returns labels like `Bullish` / `Somewhat-Bullish` / `Neutral` / `Somewhat-Bearish` / `Bearish` — don't parse as arbitrary strings.

### Threading model
- `pick.py` runs 3 threads: main (scan loop), `http` (server), `walter-bloomberg` (RSS refresh).
- Shared state (`_picks`, `_regime`) is guarded by `_state_lock`. Anything new that reads/writes those must acquire the lock.

---

## 📁 File Layout

```
daytrade_picker/
├── pick.py              ← main launcher, HTTP server, scan loop
├── config.py            ← all tunable settings + API key
├── alphavantage.py      ← AV client, rate limiter, budget tracker, cache
├── walter_bloomberg.py  ← RSS feed fetcher (background thread)
├── market_regime.py     ← SPY/QQQ/IWM/VIX regime classification
├── scorer.py            ← candidate building + signal scoring + LONG/SHORT decision
├── indicators.py        ← pure-Python RSI, MACD, VWAP, ATR
├── report_builder.py    ← HTML + JSON writers
├── html_styles.py       ← CSS + JavaScript for the report page
├── requirements.txt
├── run.bat              ← Windows launcher shortcut
├── README.md
├── output/              ← generated: report.html, live_data.json, etc.
└── docs/
    ├── FEATURE_LOG.md   ← this file
    └── README.md        ← pointer to workspace docs
```

---

## 📌 For A New AI Session Picking This Up

1. Read [`../../.workspace-docs/AI_ONBOARDING.md`](../../.workspace-docs/AI_ONBOARDING.md) first for workspace-wide context.
2. Read this file to understand the current state of this project.
3. Read the actual source files (`pick.py` is the entry point) before making changes.
4. Check the backlog — the AV key fix is the highest-priority open item.
5. Reference the debugging gotchas — avoid re-learning painful lessons about yfinance, AV rate limits, and threading.
6. Use surgical diffs (`replace_in_file`) not full rewrites for large files.

---

*End of feature log. Update this file whenever features are added, changed, or removed.*
