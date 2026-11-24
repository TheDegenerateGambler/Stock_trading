# Stock Trading

A collection of personal stock/options trading tools and indicators. Each lives
in its own subfolder with its own `README.md` and `docs/` set.

## Projects

| Folder | What it is | Language |
|--------|-----------|----------|
| [`daytrade_picker/`](daytrade_picker/) | Top-10 day-trade picker (AV + yfinance + Walter Bloomberg RSS); LONG/SHORT with entry/stop/2:1 target. | Python |
| [`premarket_scanner/`](premarket_scanner/) | Premarket gap-up scanner with news catalysts + sentiment. | Python |
| [`options_daytrader/`](options_daytrader/) | Live 09:30-12:00 ET options CALL/PUT picker (CBOE + yfinance). | Python |
| [`swing_options_scanner/`](swing_options_scanner/) | 2-4 week swing options scanner for small accounts. | Python |
| [`wheel_scanner/`](wheel_scanner/) | Canadian cash-secured-put / covered-call "Wheel" scanner (NBDB). | Python |
| [`TradingView-indicators/`](TradingView-indicators/) | Custom Pine Script v5 indicators (LMC, CCI, Fib). | Pine Script |

Open any subfolder for how to install and run it, and see its `docs/` for full
documentation.

## Not financial advice

These tools are informational and personal. They do not place trades. All market
and options data is public and, for options, typically ~15 minutes delayed.

## Secrets

No API keys are committed. Where a tool uses Alpha Vantage, the key must come
from the `AV_API_KEY` environment variable.

## License

Most of this repository is licensed under the **MIT License** - see
[`LICENSE`](LICENSE).

**Exception:** [`TradingView-indicators/`](TradingView-indicators/) is licensed
separately under **CC BY-NC-SA 4.0** (it is a rewrite drawing on LuxAlgo and
Elder's work). See [`TradingView-indicators/LICENSE`](TradingView-indicators/LICENSE).
