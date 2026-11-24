---
Project:        swing_options_scanner
Doc:            TESTING.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Testing - swing_options_scanner

No formal suite yet, but most modules ship a `__main__` smoke test, which makes
each layer independently runnable.

## Per-module smoke tests

```
python universe_builder.py      # build universe (force refresh) + print count
python technical_screener.py    # analyze a few sample tickers (AMD, PLTR, SOFI, F)
python earnings_calendar.py     # days-to-earnings for sample tickers
python options_selector.py      # select contracts for sample (ticker, price, dir)
python trade_builder.py         # build a trade plan from a fake contract
```

## Full run

```
python scanner.py               # end-to-end; then open the HTML report
```

## Testing each layer in isolation

| Layer | How to exercise |
|-------|-----------------|
| Universe | `python universe_builder.py` - confirm a sane ticker count after filters. |
| Technical bias | `python technical_screener.py` - confirm BULLISH/BEARISH/NEUTRAL + indicator values. |
| Earnings gate | `python earnings_calendar.py` - confirm days-to-earnings and caching. |
| Contract selection | `python options_selector.py` - confirm contracts honour DTE/Δ/OI/spread/budget. |
| Trade plan | `python trade_builder.py` - confirm targets/stop/R:R math on a known contract. |
| Report | `python scanner.py` then open `output/swing_options_scanner.html`. |

## Adding automated tests

Strong candidates for unit tests (mostly pure math): `trade_builder.py`
(targets/stop/break-even/R:R) and the scoring in `swing_ranker.py` (feed
synthetic inputs, assert weight contributions). Stub `requests`/`yfinance` to
stay offline (see the VideoClipper tests for the stub pattern).

---
Related: DEVELOPMENT.md, MODULES.md, OPERATIONS.md
