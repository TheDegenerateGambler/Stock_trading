---
Project:        premarket_scanner
Doc:            GLOSSARY.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Glossary - premarket_scanner

| Term | Meaning |
|------|---------|
| **Premarket** | Trading session before the 09:30 ET US open (bars available ~04:00-09:30 ET). |
| **Gap / gap_pct** | `(premarket_last - prev_close) / prev_close * 100`; how far a stock has moved before the open. |
| **prev_close** | The previous regular-session closing price. |
| **Premarket volume** | Shares traded during the premarket window. |
| **Universe** | The set of tickers scanned each run (AV movers + S&P 500 + Russell 1000 + fallback). |
| **AV / Alpha Vantage** | Market-data API used for movers (`TOP_GAINERS_LOSERS`) and `NEWS_SENTIMENT`. |
| **TOP_GAINERS_LOSERS** | AV endpoint listing the day's top gainers / most active names. |
| **NEWS_SENTIMENT** | AV endpoint returning headlines + a normalised sentiment score/label. |
| **Catalyst** | Auto-tagged reason a stock is moving (Earnings / Guidance / M&A / FDA-Clinical / etc.). |
| **Sentiment label** | Bullish / Somewhat-Bullish / Neutral / Somewhat-Bearish / Bearish. |
| **yfinance** | Yahoo Finance scraper library used for bars and a news fallback. |
| **Free tier** | AV free plan limits: 25 calls/day, 5 calls/min (see `AV_DAILY_BUDGET`, `AV_CALLS_PER_MIN`). |
| **ET** | US/Eastern time, the reference timezone for the schedule. |
| **S&P 500 / Russell 1000** | US equity indices whose membership seeds the universe (scraped from Wikipedia). |

---
Related: ARCHITECTURE.md, CONFIGURATION.md, MODULES.md
