---
Project:        daytrade_picker
Doc:            GLOSSARY.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Glossary - daytrade_picker

| Term | Meaning |
|------|---------|
| **Day trade** | A position opened and closed within the same trading day. |
| **LONG / SHORT** | Betting the price rises / falls. |
| **Conviction score** | The scorer's confidence in a LONG/SHORT pick. |
| **Entry / stop / target** | Suggested entry price, protective stop, and profit target. |
| **R:R (2:1)** | Reward-to-risk ratio; target distance is twice the stop distance. |
| **EMA** | Exponential moving average. |
| **MACD** | Moving Average Convergence Divergence momentum indicator. |
| **VWAP** | Volume-weighted average price. |
| **ATR** | Average True Range (volatility), used to size stop/target. |
| **RSI** | Relative Strength Index; `RSI_OVERSOLD` (35) feeds LONG bias. |
| **Market regime** | Broad risk-on/off read from SPY/QQQ/IWM day change + VIX. |
| **VIX** | Volatility index; high = fear/risk-off. |
| **Screener (gainers/actives)** | AV lists of top gainers / most active names seeding candidates. |
| **NEWS_SENTIMENT** | AV endpoint giving a normalised sentiment score. |
| **Walter Bloomberg** | A fast financial-news RSS feed shown in the report sidebar. |
| **AV / Alpha Vantage** | Market-data API (screener + sentiment); free-tier limited. |
| **Free tier** | AV limits: 25 calls/day, 5/min (`AV_DAILY_BUDGET`, `AV_CALLS_PER_MIN`). |
| **Midday rescan** | An extra scan the loop performs around midday. |

---
Related: ARCHITECTURE.md, CONFIGURATION.md, MODULES.md
