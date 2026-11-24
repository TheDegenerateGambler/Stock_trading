# Premarket Scanner

A premarket gap-up scanner that finds the top 10 movers before the US open,
scored with news catalysts and Alpha Vantage sentiment.

## Filters (hard-coded per task)

| Filter | Threshold |
|---|---|
| `gap_pct` | > **5%** |
| `price` | > **$3** |
| `premarket_volume` | > **50,000** |
| Result | Top **10** by `gap_pct` DESC |

`gap_pct` = `(premarket_last − prev_close) / prev_close × 100`

## Schedule

- Runs a scan **every 20 minutes**.
- **Exits automatically at 9:20 AM ET** (US premarket end).
- Yfinance premarket bars are only available during **04:00 – 09:30 ET**;
  outside this window the scanner will report 0 picks (expected).

## Universe

Union of (deduped, cached 7 days):

1. **Alpha Vantage `TOP_GAINERS_LOSERS`** (fresh every run, top_gainers + most_actively_traded)
2. **S&P 500** — scraped from Wikipedia
3. **Russell 1000** — scraped from Wikipedia
4. Static fallback (`config.FALLBACK_UNIVERSE`) if Wikipedia fails

Capped at 1,200 tickers for runtime.

## Catalyst / News

For each of the top 10, the scanner fetches:
- **Alpha Vantage `NEWS_SENTIMENT`** — normalized 0–1 score + label
  (Bullish / Somewhat-Bullish / Neutral / Somewhat-Bearish / Bearish)
- **Top 4 headlines** (title, source, published, URL)
- **Auto-categorized catalyst**: Earnings / Guidance / FDA-Clinical / M&A /
  Analyst / Offering / Partnership / Legal / Insider / Product / Contract / Other

Falls back to `yfinance.Ticker.news` if AV budget is exhausted.

## Output

- **Console** — pretty table
- **HTML** — `output/premarket_report.html` (auto-refreshes every 60 s)
- **JSON** — `output/premarket_picks.json`
- Report is served on `http://127.0.0.1:8767/premarket_report.html`

## Install

```bash
cd Stock_trading/premarket_scanner
pip install -r requirements.txt
```

Requires: `yfinance`, `requests`, `pandas`, `lxml` (for Wikipedia scraping).

## Usage

```bash
# Loop every 20 min until 9:20 AM ET, opens browser
python scanner.py

# Or double-click on Windows:
run.bat

# One-shot scan and exit
python scanner.py --once

# Force run past the 9:20 AM cutoff (testing)
python scanner.py --force

# Rebuild the S&P/Russell universe cache
python scanner.py --refresh-universe

# Don't open the browser automatically
python scanner.py --no-browser
```

## Alpha Vantage API key

The scanner reuses the same AV key pattern as `daytrade_picker`. Set it via:

- Environment variable `AV_API_KEY`, **or**
- Edit `config.py` and set `AV_API_KEY = "your-key-here"`.

Free-tier budget: 25 calls / day.
- 1 call → `TOP_GAINERS_LOSERS` (cached 30 min)
- Up to 10 calls / scan → `NEWS_SENTIMENT` for the top 10 (cached 30 min)

If the daily budget is exhausted, the scanner falls back to yfinance news
(headlines only, sentiment = Neutral) and keeps running.

## Files

| File | Purpose |
|---|---|
| `config.py` | Filter thresholds, schedule, AV settings |
| `universe.py` | S&P 500 + Russell 1000 + AV movers builder |
| `premarket_data.py` | Concurrent yfinance premarket bar fetch + filter |
| `news_fetcher.py` | AV NEWS_SENTIMENT + catalyst tagging + yfinance fallback |
| `alphavantage_client.py` | Rate-limited AV client (self-contained) |
| `report_builder.py` | Console table + HTML + JSON writers |
| `scanner.py` | Main entry point + 20-min loop |
| `run.bat` | Windows launcher |

## Notes / Caveats

- **Yfinance premarket bars** are only populated during the 04:00–09:30 ET
  session. Outside this window (e.g., late night or after 9:30 AM),
  the scanner will show 0 picks — this is not a bug.
- Yfinance is a scraper; occasional rate-limits / empty responses per ticker
  are silently skipped.
- The first run takes ~30–60 s to build the universe cache from Wikipedia.
  Subsequent runs are much faster.

## Disclaimer

Signals only — **not financial advice**. Manage your own risk.