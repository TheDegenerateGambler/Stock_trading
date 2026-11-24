# 🎯 DayTrade Picker

Standalone day-trading stock picker powered by **Alpha Vantage** (free tier) + **yfinance** + **Walter Bloomberg RSS**.

Scans US markets for the top 10 high-conviction day trades every 30 minutes.
Outputs **LONG / SHORT** direction with entry, stop, and 2:1 R:R target.

---

## Quick Start

```powershell
cd daytrade_picker
pip install -r requirements.txt
```

**Add your Alpha Vantage API key** — edit `config.py` line 11:
```python
AV_API_KEY = "PASTE_YOUR_KEY_HERE"
```
Get a free key at: https://www.alphavantage.co/support/#api-key

```powershell
python pick.py
```

Opens `http://127.0.0.1:8766/report.html` automatically.

---

## Flags

```
python pick.py                    # full run, 30-min interval
python pick.py --once             # one scan then exit
python pick.py --no-browser       # skip auto-open
python pick.py --interval 15      # scan every 15 min
python pick.py --port 9000        # custom HTTP port
```

---

## What It Does Each Scan

| Step | Source | API Credits |
|---|---|---|
| Pre-screen top movers | AV `TOP_GAINERS_LOSERS` | 1 call |
| News sentiment per ticker | AV `NEWS_SENTIMENT` | 1 per ticker |
| 5-min intraday bars (RSI, MACD, VWAP, RVOL, ATR) | yfinance | 0 |
| Options chain call/put bias | yfinance | 0 |
| Market regime (SPY/QQQ/VIX) | yfinance | 0 |
| Walter Bloomberg macro feed | Free RSS | 0 |

---

## AV Budget (Free Tier: 25 calls/day)

| Time | Session | AV Calls |
|---|---|---|
| Market open | Morning scan | 11 (1 screener + 10 sentiment) |
| ~12:00 PM ET | Midday refresh | 8 (1 screener + 7 sentiment) |
| Every 30 min | Loop refresh | 0 (yfinance only) |
| **Daily total** | | **~19-21 / 25** |

---

## Scoring Logic

Need **3+ bull signals** for LONG, **3+ bear signals** for SHORT.

| Signal | Bull | Bear |
|---|---|---|
| RSI | 30-65 | >65 overbought |
| MACD histogram | Rising | Falling |
| Price vs VWAP | Above | Below |
| Relative volume | ≥2× | — |
| Gap | Up ≥1% | Down ≤-1% |
| Options flow | Calls dominating | Puts dominating |
| AV sentiment | Score ≥0.65 | Score ≤0.35 |
| Market regime | Bull | Bear |

**Risk/reward:** Stop = 1×ATR, Target = 2×ATR (minimum 2:1 ratio).

---

## Output

```
==============================================================
  DAYTRADE PICKS — 09:30 AM ET  |  BULL  VIX 14.2
==============================================================
   1. NVDA   ▲ LONG   $131.20  stop $129.50  tgt $134.00
      RSI 55  MACD+  Above VWAP  RVOL 3.1x
      "NVDA wins $4B data center contract"

   2. TSLA   ▼ SHORT  $248.00  stop $251.00  tgt $243.00
      RSI 72 OB  MACD-  Below VWAP  Puts>Calls
      "Tesla delivery miss reported"
==============================================================
  AV: 12/25 calls used today (13 remaining)
  Market trending up (SPY +0.4%, QQQ +0.6%). Favour longs.
==============================================================
  ⚠  Signals only — not financial advice. Manage your own risk.
==============================================================
```

Plus the HTTP page at `http://127.0.0.1:8766/report.html` with:
- Pick cards with sentiment bar, entry/stop/target levels
- Walter Bloomberg real-time macro sidebar
- Market regime banner (VIX, SPY, QQQ)
- Auto-refreshes every 30 min

---

## Files

```
daytrade_picker/
  pick.py              THE launcher
  config.py            API key + all settings
  alphavantage.py      AV client (rate limiter + cache)
  walter_bloomberg.py  RSS feed fetcher
  market_regime.py     SPY/QQQ/VIX regime detection
  scorer.py            Signal scoring + LONG/SHORT decision
  indicators.py        RSI, MACD, VWAP, ATR (pure Python)
  report_builder.py    HTML + JSON writer
  html_styles.py       CSS + JavaScript
  requirements.txt
  output/              Generated files (report.html, live_data.json, etc.)
```

---

## Disclaimer

These are **data-driven signals, not financial advice**. No screener has a guaranteed win rate. Always use stop losses, size positions appropriately, and make your own trading decisions.