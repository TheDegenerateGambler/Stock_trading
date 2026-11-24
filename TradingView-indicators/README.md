# TradingView Indicators

Custom Pine Script v5 indicators for TradingView charts, built for a SPY/QQQ
intraday workflow on TradingView's free tier (2-indicator limit).

## Indicators

| Script | Purpose |
|--------|---------|
| `Liquidity Momentum Confluence.pine` | **LMC** — all-in-one overlay: liquidity swings, Elder's Bull-Bear Power, Bollinger Bands, trend EMA, market-internals dashboard, and a confluence signal engine. |
| `CCI Custom Signals.pine` | A CCI-based custom signal indicator. |
| `Daily Fibonacci Retracement.pine` | Daily Fibonacci retracement levels. |

## Usage

Pine Script runs **inside TradingView** — there is nothing to install locally.
Open the Pine Editor, paste a script, and click **Add to chart**. See
[`docs/OPERATIONS.md`](docs/OPERATIONS.md) for details.

## Documentation

See [`docs/`](docs/):

| Doc | Purpose |
|-----|---------|
| [OVERVIEW.md](docs/OVERVIEW.md) | What each indicator does, data & privacy |
| [OPERATIONS.md](docs/OPERATIONS.md) | Adding an indicator to a chart |
| [CHANGELOG.md](docs/CHANGELOG.md) | Release notes |
| [LMC_FEATURE_LOG.md](docs/LMC_FEATURE_LOG.md) | Full LMC feature inventory |
| [AFTER_HOURS_TRACKER_PLAN.md](docs/AFTER_HOURS_TRACKER_PLAN.md) | Deferred feature spec |
