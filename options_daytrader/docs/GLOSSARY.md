---
Project:        options_daytrader
Doc:            GLOSSARY.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Glossary - options_daytrader

| Term | Meaning |
|------|---------|
| **0DTE** | Zero days to expiration - an option expiring the same trading day (used for SPY/QQQ). |
| **CALL / PUT** | Option giving the right to buy / sell the underlying at the strike. |
| **Delta (Δ)** | Option's price sensitivity to a $1 underlying move; target band 0.30-0.45. |
| **Gamma (Γ) / Theta (Θ) / Vega (ν)** | Rate of Δ change / time decay / volatility sensitivity. |
| **Greeks** | Collectively Δ Γ Θ ν; CBOE provides them natively, yfinance fallback computes Δ via Black-Scholes. |
| **OI (open interest)** | Outstanding contracts for a strike/expiry; liquidity proxy (`MIN_OI` 500). |
| **Spread** | `(ask - bid) / mid`; capped at `MAX_SPREAD_PCT` (15%). |
| **VWAP** | Volume-weighted average price; signal input. |
| **EMA cross** | 9- vs 20-period EMA relationship on the 5-min chart. |
| **RSI / MACD** | Momentum oscillators used as signal inputs. |
| **RVOL** | Relative volume vs. the typical volume at that time of day. |
| **Composite score** | Weighted sum of signals in [-100, +100]; `TRADE_THRESHOLD_SCORE` gates actionability. |
| **ATR** | Average True Range; drives stop/target distances. |
| **CBOE** | Cboe delayed-quotes JSON feed (primary options source). |
| **Black-Scholes** | Option-pricing model used to approximate Δ in the yfinance fallback. |
| **Gap-up** | A stock opening materially above its prior close; seeded from premarket_scanner. |
| **Session** | 09:30-12:00 ET window this tool operates in; `--force` bypasses it. |
| **Unusual Whales** | Third-party options-flow service; integration is a stub, off by default. |

---
Related: ARCHITECTURE.md, CONFIGURATION.md, MODULES.md
