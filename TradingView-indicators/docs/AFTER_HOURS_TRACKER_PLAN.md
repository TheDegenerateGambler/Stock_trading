# 🌙 After-Hours / Extended Hours Move Tracker — Design Plan

> **Status:** DEFERRED — plan saved for future implementation
> **Date drafted:** 2026-07-09
> **Target:** Add-on feature for `Liquidity Momentum Confluence.pine` (LMC)

---

## 🎯 Problem Statement

TradingView displays extended-hours data (premarket, after-hours, and overnight futures), and big moves during these sessions often set the tone for the next regular trading day. Currently LMC has no visibility into what's happening outside of Regular Trading Hours (RTH, 9:30 AM – 4:00 PM ET). We want to surface:

- Overnight/after-hours price moves in SPY/QQQ
- Overnight futures direction (ES/NQ)
- Alerts when moves cross a "significant" threshold
- Optional integration with the composite BIAS score so the morning verdict factors in overnight sentiment

---

## 📊 Five Design Options Considered

### **Option A — Overnight Gap Tracker** (simplest)
Measure the move from prior day 4:00 PM close → current AH/premarket price.
```
Overnight Δ:  +0.42%  ($2.45)  🟢
Gap Status:   Premarket
```
- ✅ Simple, one calculation
- ❌ Doesn't show intra-session range

### **Option B — After-Hours Range Tracker**
Track the full high/low range during extended hours (4pm–9:30am ET).
```
AH High:      585.20  (+0.51%)
AH Low:       582.10  (-0.03%)
AH Range:     0.54%
```
- ✅ Shows volatility of the overnight session
- ❌ Doesn't tell you direction

### **Option C — Big Move Alert / Threshold** (most actionable)
Fires an alert when after-hours move exceeds a threshold (e.g., ±0.5%).
```
🚨 SPY moved +1.2% in after-hours
```
- ✅ Pushes info to you when it matters
- ❌ Only fires on threshold cross; no continuous visibility

### **Option D — Futures-Based Overnight Sentiment** (most professional)
Since ETFs like SPY have thin AH volume, watch ES/NQ futures which trade nearly 24h.
```
ES Overnight: +0.32%  🟢
NQ Overnight: -0.18%  🔴
Bias:         Mixed
```
- ✅ Cleaner signal than thin SPY AH prints
- ❌ Requires two more `request.security()` calls

### **Option E — All of the Above** ⭐ RECOMMENDED
Comprehensive dashboard row block combining A + B + C + D.

---

## ⭐ Recommended Design

**Option E** with these enhancements:
- ATR-adaptive "big move" threshold (2× current ATR%) instead of fixed 0.5%
- Fold significant AH move into the composite BIAS score (so morning verdict factors in overnight sentiment)
- Auto-disable on non-24h instruments (crypto, foreign stocks)

### 📋 Dashboard Section Mockup

```
─────────────────────────────
 🌙 Extended Hours
─────────────────────────────
 Session:     🟢 RTH / 🌙 AH / 🌅 Premkt / ⚪ Closed
 SPY AH:      +0.42%  🟢  (vs 4PM close)
 ES:          +0.35%  🟢
 NQ:          +0.28%  🟢
 AH Range:    0.54%
 Big Move:    ⚪ Normal  /  🚨 SIGNIFICANT
─────────────────────────────
```

### 🔔 New Alerts (3)

1. **🚨 Big AH Move (Bullish)** — overnight move > +threshold
2. **🚨 Big AH Move (Bearish)** — overnight move < -threshold
3. **🌅 Gap Alert** — fires at market open if gap > threshold (great for gap-trading strategies)

### ⚙️ New Inputs

| Input | Default | Purpose |
|---|---|---|
| Enable Extended Hours tracker | true | Master toggle |
| Big Move threshold | 0.5% | Fixed threshold |
| Use ATR-adaptive threshold | true | Overrides fixed with 2× ATR% |
| ES futures symbol | `CME_MINI:ES1!` | Overridable |
| NQ futures symbol | `CME_MINI:NQ1!` | Overridable |
| Fold into BIAS score | true | Add ±1 to composite when big move detected |

---

## 🛠️ Technical Implementation Notes

### Session Detection

```pine
inRTH  = session.ismarket
inPre  = session.ispremarket
inPost = session.ispostmarket
inExt  = inPre or inPost
```

### Reference Points

Track two anchors using `var`:
```pine
var float lastRTHClose = na
if not inRTH[1] and inRTH  // start of RTH session — no-op
    na
if inRTH and not inRTH[1] == false  // during RTH
    lastRTHClose := close  // update continuously; freezes at 4pm
```

Alternative cleaner approach:
```pine
lastRTHClose = request.security(syminfo.tickerid, "D", close[1])
```

### Move Calculation

```pine
overnightMovePct = (close - lastRTHClose) / lastRTHClose * 100
```

### Futures Data

```pine
symES = input.symbol("CME_MINI:ES1!", "ES Futures", group="🌙 Extended Hours")
symNQ = input.symbol("CME_MINI:NQ1!", "NQ Futures", group="🌙 Extended Hours")

esPrice     = request.security(symES, timeframe.period, close, ignore_invalid_symbol=true)
esPrevClose = request.security(symES, "D", close[1],       ignore_invalid_symbol=true)
esMovePct   = not na(esPrice) and not na(esPrevClose) and esPrevClose != 0 ? (esPrice - esPrevClose) / esPrevClose * 100 : na
```

### Adaptive Threshold

```pine
atrPct = ta.atr(14) / close * 100
adaptiveThreshold = useAdaptive ? atrPct * 2.0 : fixedThresholdPct
bigMoveBull = not na(overnightMovePct) and overnightMovePct >  adaptiveThreshold
bigMoveBear = not na(overnightMovePct) and overnightMovePct < -adaptiveThreshold
```

### BIAS Integration

If enabled, extend the greenCount/redCount calculation:
```pine
ahLightGreen = bigMoveBull ? 1 : 0
ahLightRed   = bigMoveBear ? 1 : 0
greenCount += ahLightGreen
redCount   += ahLightRed
// (and update naCount / validCount accordingly)
```

Then BIAS score becomes -8..+8 range and thresholds may need re-tuning.

### Table Row Count

Bump `table.new(..., 2, 20, ...)` to `2, 27` (7 more rows for the new section).

---

## ⚠️ Caveats & Gotchas

1. **User must enable Extended Hours on their chart.** Right-click chart → Settings → Symbol → "Extended Trading Hours". Without this, Pine only sees RTH data — the AH move will always be 0.

2. **SPY/QQQ AH volume is thin.** A big % move on 100 shares means little. Futures (ES/NQ) are more reliable indicators of true overnight sentiment.

3. **"Big move" definition is regime-dependent.** ±0.5% in a low-vol regime is huge; in a high-vol regime it's noise. That's why ATR-adaptive is recommended.

4. **Non-24h instruments.** Crypto/forex trade 24/7 — the concept of "overnight" doesn't apply. Auto-disable on these via `syminfo.type` check.

5. **Gap alert timing.** Should fire only on the *first RTH bar* of a new session, detected via `session.ismarket and not session.ismarket[1]`. Ensure it doesn't repeat.

6. **Weekend/holiday handling.** Friday 4pm close → Monday 9:30am open is a 65-hour gap. Formula should still work (uses prior daily close) but move sizes will be larger. Consider a separate "weekend gap" annotation.

---

## ❓ Open Decisions Awaiting User Input

Before implementing, need answers on:

1. **Which option** (A/B/C/D/E)? Recommendation: **E**
2. **Include ES/NQ futures data**? Recommendation: **Yes**
3. **Fold AH move into BIAS score**? Recommendation: **Yes**
4. **Fixed threshold or ATR-adaptive**? Recommendation: **ATR-adaptive**
5. **Alerts** — 3 proposed sufficient, or add "AH range breakout"?

---

## 🎯 Estimated Impact

- **New inputs:** ~7
- **New global variables:** ~10
- **New dashboard rows:** ~7 (bumps table from 20 → ~27 rows)
- **New alerts:** 3 (bumps total alerts from 10 → 13)
- **New `request.security()` calls:** 2 (ES + NQ)
- **Additional compute cost:** Minimal (~2 more HTF fetches per bar)
- **Complexity:** Moderate — session detection + reference-point tracking are the trickiest parts

---

## 🔗 Related Files

- `../Liquidity Momentum Confluence.pine` — target for integration
- `./LMC_FEATURE_LOG.md` — current LMC feature inventory

---

## 📌 Notes For Future Session

If a new AI session picks this up:

1. Read `LMC_FEATURE_LOG.md` first for current state of the script
2. Ask the user the 5 open decisions above
3. Implement in incremental patches (inputs → data fetch → session logic → dashboard rows → alerts → BIAS integration)
4. Test on SPY during premarket to verify session detection works
5. Handle the "before first RTH close of ever" edge case (na safety)