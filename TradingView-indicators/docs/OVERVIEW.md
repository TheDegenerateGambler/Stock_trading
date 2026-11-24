---
Project:        TradingView-indicators
Doc:            OVERVIEW.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Overview - TradingView-indicators

A collection of custom Pine Script v5 indicators for TradingView charts, built
for a SPY/QQQ intraday workflow on TradingView's free tier (2-indicator limit),
which is why the flagship packs everything into one script.

## Scripts

| Script | Purpose |
|--------|---------|
| `Liquidity Momentum Confluence.pine` | **LMC** - the flagship all-in-one overlay: liquidity swings (LuxAlgo-inspired), Elder's Bull-Bear Power momentum, Bollinger Bands, a trend EMA, a market-internals dashboard, and a confluence signal engine. See `LMC_FEATURE_LOG.md` for the full feature inventory. |
| `CCI Custom Signals.pine` | A CCI-based custom signal indicator. |
| `Daily Fibonacci Retracement.pine` | Daily Fibonacci retracement levels. |

Pine Script runs **inside TradingView** - there is nothing to install or run
locally; you paste a script into the TradingView Pine Editor and add it to a
chart.

## Other docs in this folder

- `LMC_FEATURE_LOG.md` - detailed living feature inventory for the LMC indicator
  (project-specific extra, grandfathered).
- `AFTER_HOURS_TRACKER_PLAN.md` - deferred feature spec for an extended-hours
  tracker (project-specific extra).
- `README.md` - pointer to the shared workspace docs and the root standard.

## Data & Privacy

This project processes **no personal data**. The scripts are chart indicators
that run inside TradingView on market data; they do not read, store, or transmit
any user personal data from this repository. It is therefore exempt from
`DATA_INVENTORY.md`, `RETENTION.md`, `PRIVACY.md`, and `COMPLIANCE_CHECKLIST.md`
per the workspace documentation standard.

---
Related: OPERATIONS.md, CHANGELOG.md
