---
Project:        wheel_scanner
Doc:            TESTING.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Testing - wheel_scanner

No formal automated suite yet; the scanner is exercised manually end-to-end.

## Smoke tests

```
# Full run (slowest, most complete)
python run_all.py

# Individual sides
python scan.py
python scan_cc.py --buy-write
```

A successful run writes the mega dashboard under `output/` and (via the
launcher) opens it.

## Testing each layer in isolation

| Layer | How to exercise |
|-------|-----------------|
| Data provider | In a REPL: `from data_provider import get_stock_snapshot; get_stock_snapshot("BTO.TO")` - confirm a `StockSnapshot` or clean `None`. |
| CSP scoring | Run `scan.py`; confirm affordable strikes only (`strike*100 <= budget`) and sane annualised yields. |
| CC scoring | Run `scan_cc.py --buy-write`; confirm buy-write economics. |
| Positions path | Create `my_positions.json`; confirm the "Your Positions" section appears with strikes ≥ cost basis. |
| Dashboard | Open the `output/` dashboard; confirm Top-10, sections, and the search box work. |
| FX override | `python run_all.py --usd-cad 1.40`; confirm USD names convert accordingly. |

## Dry-run tips

- yfinance option data for TSX names can be sparse/delayed; a thin result is not
  necessarily a bug. Cross-check a known-liquid name (e.g. `F`) to isolate code
  issues from data gaps.
- Section errors are caught and shown as banners, so one bad ticker won't abort
  the whole run.

## Adding automated tests

Best unit-test targets are the pure economics: the fee model and affordability
math in `config`/analyzers, annualised-yield computation, and the
cost-basis-floor rule in `cc_analyzer.py`. Stub `yfinance` to stay offline (see
the VideoClipper tests for the stub pattern).

---
Related: DEVELOPMENT.md, MODULES.md, OPERATIONS.md
