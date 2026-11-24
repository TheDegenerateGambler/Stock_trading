---
Project:        swing_options_scanner
Doc:            SECURITY.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Security - swing_options_scanner

## Auth model

None for the tool itself. The only credential is an optional **Alpha Vantage API
key**, used read-only for news sentiment.

## Secret handling

- The AV key is read from the `AV_API_KEY` environment variable. **No key ships
  in source** (`config.py` falls back to `PASTE_YOUR_KEY_HERE`, which disables
  AV).
- A real key previously lived in source as a fallback and was scrubbed. If you
  used it, **rotate it** on Alpha Vantage - a committed key is considered burned.
- `.env`, `*.key`, and `output/` are git-ignored.

## Network surface

Outbound, read-only:

- **Wikipedia** - universe membership.
- **Yahoo / yfinance** - daily bars + earnings dates.
- **CBOE** - delayed options chain.
- **Alpha Vantage** - optional news sentiment (needs the key).
- **TradingView** - daily chart widgets load in the browser viewing the report.

Inbound: a **localhost-only** HTTP server serving the `output/` report.

## Redaction policy

The report holds only public market/options data (tickers, prices, contracts,
public headlines). There is no personal data. Do not commit the live `output/`
folder (it is git-ignored anyway).

## Threat model & limitations

| Concern | Position |
|---------|----------|
| Key leakage | Env-only; `.gitignore` excludes `.env`/`*.key`. |
| Local server exposure | Bound to localhost; not reachable off-box. |
| Delayed data | CBOE quotes ~15 min delayed; informational only. |
| Data trust | yfinance/CBOE outages are skipped or fall back, not fatal. |

---
Related: PRIVACY.md, CONFIGURATION.md, OPERATIONS.md
