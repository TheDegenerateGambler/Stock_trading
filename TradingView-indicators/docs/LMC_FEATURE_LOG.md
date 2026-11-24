# 📋 Liquidity + Momentum Confluence (LMC) — Feature Log

> **Script:** `Liquidity Momentum Confluence.pine`
> **Short title:** LMC
> **Type:** Pine Script v5 overlay indicator
> **License:** CC BY-NC-SA 4.0
> **Origin:** Rewrite of LuxAlgo Liquidity Swings + Elder's Bull Bear Power + Bollinger Bands
> **Last major update:** 2026-07-10

---

## 🎯 Overview

LMC is an all-in-one overlay indicator for TradingView designed to give a single-glance view of:
1. **Where liquidity sits** on the chart (swing highs/lows with volume/count filtering)
2. **Momentum bias** via Elder's Bull Bear Power
3. **Volatility context** via Bollinger Bands
4. **High-probability entries** via a confluence engine that combines all three
5. **Broader market context** via a US-equity market internals dashboard

It was built specifically for a SPY/QQQ intraday trader on the free-tier of TradingView (2-indicator limit), which is why all functionality lives in a single script.

---

## 🧩 Core Features

### 🌊 Liquidity Swings (LuxAlgo-inspired, refactored)
- Pivot-based detection of swing highs/lows
- Configurable pivot lookback (or auto-tuned)
- Two zone modes:
  - **Wick Extremity** — zone from body edge to wick tip (recommended)
  - **Full Range** — zone spans the entire candle
- Volume + count aggregation for each zone (how many bars have re-tested)
- Filter zones by minimum Count or Volume
- Zones automatically:
  - Extend right while active
  - Close/dash when swept (price crosses the level)
- Unified pivot-high / pivot-low logic via `processSide()` function (no code duplication)

### 📉 Bollinger Bands
- Standard `SMA ± Mult × StDev`
- Configurable length + multiplier (or auto-tuned)
- Optional fill between upper/lower with adjustable transparency
- %B and BB Width calculated for the dashboard

### 📈 Trend EMA
- Configurable EMA length (default 50 or 100 based on TF)
- Line colored green when price > EMA, red when below
- Optional trend filter that blocks BBP signals against the regime

### ⚡ BBP Momentum Signals (Elder's Bull Bear Power)
- `bullPower = high − EMA(close, N)`
- `bearPower = low − EMA(close, N)`
- `BBP = bullPower + bearPower`
- Signal fires on BBP zero-crossings
- **Filters** (all optional & configurable):
  - **Cooldown** — min bars between same-direction signals (prevents whipsaw)
  - **BB Filter** — only bull cross if price was near lower BB in last N bars (oversold reversal)
  - **ATR Minimum** — skip signals when the bar range is too small
  - **Trend Filter** — only take signals with regime
- Visual: user chooses Arrow / Label / Both (default: Arrow)

### ⭐ Confluence Signals (THE MONEY SHOT)
Fires only when ALL three align:
1. BBP zero-cross in that direction
2. Recent liquidity sweep (opposite side within last N bars)
3. Price at BB extreme (lower half for bulls, upper half for bears)

Displayed with a larger ★ arrow/label in a distinct color. Rare but high-conviction — the reason all three systems are merged.

### 🤖 Auto-Tuning Engine
Script measures `ATR%` volatility and `timeframe.in_seconds()` and self-adjusts:
- Pivot lookback (5–20 typical)
- BBP cooldown (2–8 bars)
- Sweep lookback for confluence (3–20 bars)
- BB multiplier (1.8 / 2.0 / 2.5 based on Low/Med/High vol)
- Trend EMA length (50 or 100 by TF)
- BB filter lookback

Three modes exposed:
- **Auto (Recommended)** — dynamic self-adjustment
- **Manual** — use exposed inputs directly
- **Preset: SPY/QQQ [5m|15m|1h|4h|Daily]** — hand-tuned values per timeframe

### 📋 Live Dashboard
Configurable position (5 corners) + text size (4 sizes).

Currently a **22-row** table showing:

**Core (rows 0–9):**
| Row | Content |
|---|---|
| 0 | `SYMBOL • TF` header + Tuning Mode indicator |
| 1 | TF/Vol classification (Scalp/Intraday/Swing/Position/Daily+ × Low/Med/High) |
| 2 | Trend (🟢 BULL / 🔴 BEAR) |
| 3 | BBP value with ▲/▼ |
| 4 | %B |
| 5 | BB Width |
| 6 | Near Hi (nearest swing high + distance %) |
| 7 | Near Lo (nearest swing low + distance %) |
| 8 | Last Sig (last signal type + bars ago) |
| 9 | Effective auto-tuned params |

**Market Internals (rows 10–20, if enabled).** Order groups internals **by exchange** — NYSE block first, then NASDAQ block — so all SPY-relevant data sits together and all QQQ-relevant data sits together:
| Row | Content |
|---|---|
| 10 | 🌐 Internals header + "X/9 live" indicator |
| 11 | VIX (🟢/🟡/🔴 + value) |
| 12 | TICK NY |
| 13 | TRIN NY (inverted: LOW = green) |
| 14 | Breadth NY |
| 15 | TICK NQ |
| 16 | TRIN NQ (inverted: LOW = green) |
| 17 | Breadth NQ |
| 18 | DXY (with % change vs prev day) |
| 19 | Sectors (XLY/XLP ratio change) |
| 20 | Composite BIAS row |

### 🌐 Market Internals
Fetched via `request.security()` with `ignore_invalid_symbol=true` so non-US instruments don't crash. Each internal is classified as 🟢 green / 🟡 yellow / 🔴 red / ⚪ na based on user-configurable thresholds.

**9 lights tracked:**
1. **VIX** (`TVC:VIX`) — < 15 green, 15–22 yellow, > 22 red
2. **TICK NYSE** (`USI:TICK.NY`) — > +500 green, ±500 yellow, < -500 red
3. **TICK NASDAQ** (`USI:TICK.NQ`) — same thresholds
4. **Breadth NYSE** (`USI:ADVDEC.NY`) — same thresholds
5. **Breadth NASDAQ** (`USI:ADVDEC.NQ`) — same thresholds
6. **TRIN NYSE** (`USI:TRIN.NY`) — **inverted:** < 0.8 green (buying pressure), 0.8–1.2 yellow, > 1.2 red (selling pressure)
7. **TRIN NASDAQ** (`USI:TRIN.NQ`) — same thresholds
8. **DXY** (`TVC:DXY`) — falling > 0.1% green, ±0.1% yellow, rising > 0.1% red (inverse — dollar down = risk-on)
9. **Sectors** (`AMEX:XLY` / `AMEX:XLP` ratio) — rising green, falling red

**Composite BIAS** (range -9..+9):
- ≥ +5: 🟢 STRONG BULL
- +2 to +4: 🟢 BULLISH
- -1 to +1: 🟡 NEUTRAL
- -2 to -4: 🔴 BEARISH
- ≤ -5: 🔴 STRONG BEAR

---

## 🔔 Alerts (12 total)

| # | Alert Name | Trigger |
|---|---|---|
| 1 | Bullish BBP Signal | BBP zero-cross up (with all active filters) |
| 2 | Bearish BBP Signal | BBP zero-cross down |
| 3 | ★ Bullish Confluence | BBP bull + recent sweep + BB extreme |
| 4 | ★ Bearish Confluence | BBP bear + recent sweep + BB extreme |
| 5 | Swing High Swept | Close crosses above active swing high |
| 6 | Swing Low Swept | Close crosses below active swing low |
| 7 | 🚨 VIX Spike | VIX crosses above configurable level (default 25) |
| 8 | 🚨 TICK Extreme | TICK NY or NQ crosses ±1000 |
| 9 | 🚨 TRIN Panic Selling | TRIN NY or NQ crosses above 2.0 (capitulation) |
| 10 | 🚨 TRIN Panic Buying | TRIN NY or NQ crosses below 0.5 (euphoria) |
| 11 | 🔄 BIAS Flip → Bullish | Composite bias transitions to bullish |
| 12 | 🔄 BIAS Flip → Bearish | Composite bias transitions to bearish |

---

## 📜 Change Log

### 2026-07-09 (session 1) — Initial rewrite
Started from user's original mash-up of LuxAlgo Liquidity Swings + Bollinger Bands + BBP zero-cross signals. Complete rewrite:

**Bugs fixed:**
- Removed orphaned `ph_bx` / `pl_bx` global box objects (leaked memory)
- Gated `request.security_lower_tf()` behind `intraPrecision` flag → later removed entirely due to Pine v5 type system issues
- Fixed BB filter that was too strict (exact-bar match) → now uses rolling lookback window
- Initialized `crossed` booleans as `false` (was `na`)
- Deduplicated signal visuals (arrow OR label, not both)

**New features added:**
- 🤖 Auto-tuning engine with volatility + TF detection
- 5 hand-tuned presets for SPY/QQQ (5m, 15m, 1h, 4h, Daily)
- ⭐ Confluence signal engine (BBP + liquidity sweep + BB extreme)
- 📈 Optional trend EMA regime filter
- ⚡ BBP signal cooldown to prevent whipsaw
- ATR minimum filter (optional)
- BB fill option
- 📋 Live dashboard with 10 core rows
- 6 alert conditions
- Full tooltip coverage on all inputs
- Refactored duplicate pivot-high/low code into single `processSide()` function

### 2026-07-09 (session 2) — Bug hunting (multiple compile/runtime errors)
Several Pine v5 syntax gotchas encountered and fixed:

1. **Tuple ternary at top level not allowed** → wrapped preset resolver in `switch`-based function
2. **`request.security_lower_tf` cannot be ternary-gated** → refactored, then eventually removed the LTF path entirely
3. **Multi-line ternary in `posMap()` failed** → converted to `switch`
4. **User-defined function inside `if` block not allowed** → moved `fmtSigned` to global scope
5. **`array.size()` on `na` array on bar 0** → added `not na()` guard, then simplified `getCount()` by removing LTF branch entirely
6. **LuxAlgo LTF path removed** → simpler, more robust `getCount()` using only standard-bar volume

### 2026-07-09 (session 3) — Market Internals added
Added 🌐 Market Internals section to dashboard:
- 5-light system: VIX, TICK, Breadth, DXY, Sectors
- Composite BIAS row aggregating all lights
- 3 new alerts: VIX spike, TICK extreme, BIAS flip

### 2026-07-09 (session 4) — TradingView symbol fix + NASDAQ expansion
User reported `USI:ADVDEC` failing to load. Investigated TradingView symbol search — the older combined symbol was split into exchange-specific variants (`.NY`, `.NQ`, `.US`, etc.).

**Fixes:**
- Updated defaults: `USI:TICK` → `USI:TICK.NY`, `USI:ADVDEC` → `USI:ADVDEC.NY`
- Added NASDAQ companions: `USI:TICK.NQ`, `USI:ADVDEC.NQ`
- Bumped light count from 5 → 7 (added TICK NQ and Breadth NQ)
- Bumped dashboard row count from 18 → 20
- Recalibrated BIAS thresholds for 7-light range (±2 minimum to leave neutral, ±4 for "STRONG")
- Updated TICK Extreme alert to fire on NY OR NQ crossing threshold
- Added tooltips explaining `.NY` for SPY vs `.NQ` for QQQ

### 2026-07-10 (session 5) — TRIN internals added
User suggested pairing TICK with TRIN (the classic order-flow duo). TICK measures direction/intensity; TRIN (Arms Index) measures volume-weighted quality of the move. Added NYSE + NASDAQ TRIN for symmetry with existing TICK/Breadth pairs.

TRIN uses **inverted classification** — this is the main gotcha: LOW TRIN = buying pressure (green), HIGH TRIN = selling pressure (red). Opposite of TICK/Breadth.

**Changes:**
- Added `USI:TRIN.NY` and `USI:TRIN.NQ` symbol inputs
- Added TRIN thresholds: green < 0.8, red > 1.2 (yellow between)
- Added panic levels: SELL > 2.0 (capitulation bottom), BUY < 0.5 (euphoric top)
- Bumped light count from 7 → 9; recalibrated BIAS STRONG threshold from ±4 → ±5 (BULLISH/BEARISH remains at ±2 — same trigger point as before, just STRONG got proportionally stricter)
- Dashboard row count 20 → 22; added TRIN NY + TRIN NQ; rows subsequently regrouped by exchange (NY block: TICK/TRIN/Breadth, then NQ block: TICK/TRIN/Breadth) so all SPY-relevant data sits together and all QQQ-relevant data sits together
- 2 new alerts: TRIN Panic Selling + TRIN Panic Buying — both use `ta.crossover`/`ta.crossunder` (not `>`/`<`) so alerts only fire on the *transition* into extreme territory, preventing spam if TRIN stays elevated for many bars
- Updated `enableInternals` tooltip to mention TRIN
- Live count text: "X/7 live" → "X/9 live"

---

## 🚧 Deferred Ideas / Backlog

### 🌙 Extended Hours / After-Hours Tracker
**Status:** Design plan documented — awaiting user decisions
**Spec:** See [AFTER_HOURS_TRACKER_PLAN.md](./AFTER_HOURS_TRACKER_PLAN.md)
**Summary:** Add a "🌙 Extended Hours" dashboard section that tracks overnight SPY/QQQ moves, ES/NQ futures direction, and fires alerts on significant AH moves. Would optionally fold into the composite BIAS score.

### Other Ideas Discussed
- **Companion BBP pane indicator** — actual BBP histogram in a separate pane (would use user's 2nd TradingView free-tier slot)
- **Trade automation** — convert to a `strategy()` script with backtestable entries/exits, SL/TP logic
- **Signal history table** — show last N confluence signals with W/L/BE outcomes
- **Auto SL/TP levels** — draw suggested stops and targets from last swing
- **HTF overlay** — show higher-timeframe trend/bias while on lower TF
- **Session filters** — restrict signals to specific hours (NY/London/Asia)
- **Auto-disable internals on non-US tickers** — detect `syminfo.type` and skip the section for crypto/forex

---

## 🎬 Setup Instructions

### First-Time Install
1. Open TradingView, click "Pine Editor" at the bottom
2. Paste contents of `Liquidity Momentum Confluence.pine`
3. Click "Save" (name it whatever), then "Add to Chart"
4. Configure inputs — default is "Auto" which self-tunes

### Recommended: Chart Templates
Save different configs per instrument type:
1. Configure LMC on SPY with internals ON → right-click chart → Template → "Save as..." → "SPY Template"
2. Configure LMC on BTC with internals OFF → save as "Crypto Template"
3. One click switches everything

### Recommended Alerts To Enable
For SPY/QQQ intraday trading, at minimum:
- **★ Bullish Confluence** — A+ long setups
- **★ Bearish Confluence** — A+ short setups
- **🚨 VIX Spike** — market-wide fear alert (works on any chart)

### TradingView Chart Settings
- Right-click chart → Settings → Symbol → enable "Extended Trading Hours" if you want to see pre/post-market bars (matters if we later implement AH tracker)

---

## 🐛 Debugging Reference

Pine Script has no external debugger. Common workflow:

| Technique | Use Case |
|---|---|
| `plotchar(x, "name", "", location.top, display=display.data_window)` | Log variable to Data Window |
| `log.info("bbp={0}", bbp)` | Log to Editor's "Logs" tab (v5.9+) |
| `label.new(bar_index, high, "debug=" + str.tostring(x))` | On-chart debug tag |
| Dashboard rows | Best method for LMC — the info table doubles as a live debug panel |

Common Pine v5 gotchas encountered in this project (avoid if adding features):
- **No tuple-ternary at top level** — wrap in a function returning tuple via `switch`
- **No functions inside `if` blocks** — declare all `fnName() =>` at global scope
- **No multi-line ternaries** — use `switch` or single-line
- **No ternary-gated `request.security_lower_tf`** — call unconditionally, gate usage
- **`na` arrays crash `array.size()`** — guard with `not na()` first
- **`request.security` LTF vs regular return types differ** — can't mix in ternary

---

## 📁 File Layout

```
TradingView-indicators/
├── Liquidity Momentum Confluence.pine    ← main script
├── CCI Custom Signals.pine               ← other indicator (untouched)
├── Daily Fibonacci Retracement.pine      ← other indicator (untouched)
└── docs/
    ├── LMC_FEATURE_LOG.md                ← this file
    └── AFTER_HOURS_TRACKER_PLAN.md       ← deferred feature spec
```

---

## 📌 For A New AI Session Picking This Up

1. **Read this file first** to understand current state
2. **Read the pine file** to see actual implementation
3. **Check the backlog** — user may want one of the deferred ideas
4. **Reference the debugging gotchas** above — Pine v5 has quirks
5. **Always use `replace_in_file`** with small surgical diffs, not full rewrites — this file's size means `write_to_file` can truncate

---

*End of feature log. Update this file whenever features are added, changed, or removed.*
