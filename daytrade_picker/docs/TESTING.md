---
Project:        daytrade_picker
Doc:            TESTING.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Testing - daytrade_picker

No formal suite yet; exercised manually. The cleanest unit-test seam is
`indicators.py` (pure math).

## Smoke test

```
python pick.py --once --no-browser
```

Runs a single scan without opening a browser; confirm picks print and
`output/report.html` + `output/live_data.json` appear.

## Testing each layer in isolation

| Layer | How to exercise |
|-------|-----------------|
| Indicators | In a REPL: `from indicators import calc_ema, calc_macd, calc_vwap, calc_atr` and feed known series; assert expected values. |
| AV client | With `AV_API_KEY` set, call the screener/sentiment functions in `alphavantage.py`; confirm JSON or a clean `None`. |
| Scorer | Feed synthetic indicator + sentiment inputs to `scorer.py`; confirm LONG/SHORT + entry/stop/target (2:1 R:R). |
| Regime | `from market_regime import fetch_regime; fetch_regime()`; confirm a regime dict or the "unavailable" fallback. |
| News | Run `--once`; confirm the sidebar populates (or degrades cleanly if RSS fails). |
| Report | Open `output/report.html`; inspect `output/live_data.json`. |

## Dry-run tips

- `--once` avoids the 30-minute loop.
- Without an AV key, AV features are disabled - good for testing the non-AV
  paths (indicators, regime, report) offline-ish.

## Adding automated tests

Start with `indicators.py` - it is pure and deterministic. Then test the
`scorer.py` decision boundaries with synthetic inputs. Stub `requests`/
`yfinance`/`feedparser` to stay offline (see the VideoClipper tests for the stub
pattern).

---
Related: DEVELOPMENT.md, MODULES.md, OPERATIONS.md
