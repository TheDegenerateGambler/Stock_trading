---
Project:        TradingView-indicators
Doc:            OPERATIONS.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Operations - TradingView-indicators

These are Pine Script v5 indicators that run inside TradingView. There is no
local install, build step, or runtime - TradingView compiles and runs Pine on
its servers.

## Adding an indicator to a chart

1. Open a chart on [tradingview.com](https://www.tradingview.com/).
2. Open **Pine Editor** (bottom panel).
3. Open the desired `.pine` file from this folder and copy its full contents.
4. Paste into the Pine Editor, replacing any existing code.
5. Click **Add to chart**.
6. (Optional) **Save** the script in TradingView so it appears under your
   indicators.

## Free-tier note

TradingView's free plan allows **2 indicators per chart**. The LMC script is
deliberately all-in-one so a single slot covers liquidity, momentum, volatility,
trend, internals, and confluence signals at once.

## Configuring

Each indicator exposes inputs via the chart's indicator **Settings** (gear icon)
once added. See `LMC_FEATURE_LOG.md` for the LMC inputs and their meaning.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Script won't compile | Ensure the chart's Pine version is v5 and you pasted the whole file. |
| "Too many indicators" | Free tier caps at 2 per chart; remove one or use LMC's combined view. |
| Market-internals rows blank | Some internals symbols require a data subscription / market hours. |

---
Related: OVERVIEW.md, CHANGELOG.md
