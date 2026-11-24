---
Project:        premarket_scanner
Doc:            TESTING.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Testing - premarket_scanner

This project has no automated test suite yet; it is exercised manually. Several
modules expose a `__main__` smoke test.

## Smoke tests

```
# Build the universe and print its size
python universe.py

# One full scan then exit (no loop, no waiting)
python scanner.py --once
```

`python universe.py` runs `build_universe(force_refresh=True)` and prints the
total ticker count - a quick check that the Wikipedia scrape / fallback works.

## Testing each layer in isolation

| Layer | How to exercise |
|-------|-----------------|
| Universe | `python universe.py` (force refresh + count). |
| Premarket bars + filter | `python scanner.py --once` during 04:00-09:30 ET; confirm picks appear. |
| News / sentiment | Run `--once` with `AV_API_KEY` set; confirm sentiment labels and catalysts populate. |
| yfinance fallback | Run `--once` with no key (or budget spent); confirm Neutral headlines. |
| Report output | After a scan, open `output/premarket_report.html` and inspect `output/premarket_picks.json`. |

## Dry-run tips

- Outside the premarket window the scanner reports 0 picks - this is expected,
  not a failure. Test the universe/report layers independently as above.
- Use `--once` to avoid the 20-minute loop while testing.

## Adding automated tests

Good first targets are the pure-ish helpers: `gap_pct` computation and the
catalyst-categorisation logic in `news_fetcher.py`. Stub `requests`/`yfinance`
to keep tests offline (see the VideoClipper tests for the stub pattern).

---
Related: DEVELOPMENT.md, MODULES.md, OPERATIONS.md
