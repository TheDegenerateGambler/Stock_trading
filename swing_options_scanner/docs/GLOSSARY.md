---
Project:        swing_options_scanner
Doc:            GLOSSARY.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Glossary - swing_options_scanner

| Term | Meaning |
|------|---------|
| **Swing trade** | A multi-day/multi-week hold (here 2-4 weeks), between day-trading and investing. |
| **DTE** | Days to expiration; selection window 21-45. |
| **Delta (Δ)** | Option price sensitivity to a $1 underlying move; target 0.30-0.50 (slightly OTM). |
| **OTM** | Out of the money - strike beyond the current price. |
| **IV crush** | Sharp implied-volatility drop (often post-earnings) that deflates option prices; avoided via the earnings gate. |
| **Earnings window** | Period around a company's earnings report; tickers with earnings within `SKIP_EARNINGS_DAYS` are skipped. |
| **OI (open interest)** | Outstanding contracts; liquidity proxy (`MIN_OI` 500). |
| **Spread** | `(ask - bid)/mid`; capped at `MAX_SPREAD_PCT` (15%). |
| **EMA (20/50)** | Exponential moving averages used for trend/bias. |
| **RSI / MACD** | Momentum indicators feeding the momentum score. |
| **ATR** | Average True Range; volatility measure. |
| **RVOL** | Relative volume vs. typical. |
| **Composite score** | 0-100 weighted sum (trend/momentum/volume/sentiment/liquidity/budget-fit); threshold 50. |
| **Budget fit** | Scoring component rewarding cheaper contracts (more upside per dollar). |
| **Break-even** | Underlying price at which the option position breaks even at expiry. |
| **Time stop** | Exit rule if the trade hasn't moved within `TIME_STOP_DAYS` (14). |
| **R:R** | Reward-to-risk ratio of the trade plan. |
| **CBOE** | Cboe delayed options-quote feed (contract source). |
| **AV / Alpha Vantage** | Optional news-sentiment source. |

---
Related: ARCHITECTURE.md, CONFIGURATION.md, MODULES.md
