---
Project:        premarket_scanner
Doc:            DATA_FLOW.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Data Flow - premarket_scanner

End-to-end trace of one scan. Example values are illustrative.

## Trigger

```
python scanner.py          # loop every 20 min until 9:20 AM ET
python scanner.py --once   # single scan then exit
```

## Step-by-step (one scan at ~08:10 ET)

1. **Universe** (`universe.build_universe`): AV `TOP_GAINERS_LOSERS` (fresh) ∪
   S&P 500 ∪ Russell 1000 (Wikipedia, cached ~7 days) ∪ fallback → deduped,
   capped at 1,200 tickers. e.g. 1,180 symbols.

2. **Premarket bars** (`premarket_data.fetch_premarket`): concurrent yfinance
   pull of premarket last price, previous close, and premarket volume for each
   ticker. For `AAPL`: prev_close 190.00, pm_last 201.40, pm_vol 820,000.

3. **Filter + rank**: `gap_pct = (201.40 - 190.00)/190.00 * 100 = 6.0%`.
   Keep if `gap_pct > 5`, `price > 3`, `pm_volume > 50,000`. Sort by `gap_pct`
   DESC, keep `TOP_N` (10).

4. **News enrich** (`news_fetcher`): for each of the top 10, AV `NEWS_SENTIMENT`
   → score 0.42 ("Somewhat-Bullish"), top-4 headlines, catalyst tag e.g.
   "Earnings". If the AV daily budget is spent → `yfinance.Ticker.news`
   (headlines only, Neutral).

5. **Report** (`report_builder`): writes
   - `output/premarket_report.html` (auto-refresh 60 s)
   - `output/premarket_picks.json`
   and prints a console table.

6. **Serve** (`scanner._Handler`): report available at
   `http://127.0.0.1:8767/premarket_report.html`.

7. **Sleep / exit**: waits `LOOP_INTERVAL_MIN` (20) then rescans; the loop exits
   automatically at 09:20 ET.

## Downstream consumer

`output/premarket_picks.json` is read by the sibling **options_daytrader**
project as its gap-up seed list.

## What crosses a boundary

- **Network (read-only):** Wikipedia (universe), Alpha Vantage API (movers +
  sentiment), Yahoo/yfinance (bars + news fallback).
- **Disk:** writes only under `output/`.
- **Local HTTP:** report served on `127.0.0.1:8767` (localhost only).

---
Related: ARCHITECTURE.md, MODULES.md, OPERATIONS.md
