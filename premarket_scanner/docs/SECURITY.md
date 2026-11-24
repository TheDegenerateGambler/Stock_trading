---
Project:        premarket_scanner
Doc:            SECURITY.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Security - premarket_scanner

## Auth model

None for the tool itself. The only credential is an optional **Alpha Vantage
API key**, used read-only against the public AV API.

## Secret handling

- The AV key is read from the `AV_API_KEY` environment variable. **No key ships
  in source** (`config.py` falls back to `PASTE_YOUR_KEY_HERE`, which disables
  AV).
- A real key previously lived in source as a fallback; it was scrubbed. If you
  ever used it, **rotate it** on Alpha Vantage - a key that was committed is
  considered burned.
- `.env`, `*.key`, and `output/` are git-ignored.

## Network surface

Outbound, read-only:

- **Wikipedia** - universe scraping (S&P 500 / Russell 1000).
- **Alpha Vantage** - movers + news sentiment (needs the key).
- **Yahoo / yfinance** - premarket bars + news fallback.

Inbound: a **localhost-only** HTTP server on `127.0.0.1:8767` serving the
`output/` report. It is not exposed beyond the local machine.

## Redaction policy

The report contains only public market data (tickers, prices, public headlines).
There is no personal data. If you paste a sample picks JSON into docs, no
redaction is required, but avoid committing the live `output/` folder.

## Threat model & limitations

| Concern | Position |
|---------|----------|
| Key leakage | Env-only; `.gitignore` excludes `.env`/`*.key`. |
| Local server exposure | Bound to 127.0.0.1; not reachable off-box. |
| Data trust | yfinance is a scraper - occasional empty/rate-limited responses are skipped, not fatal. |
| No input validation of tickers | Universe comes from trusted sources (AV/Wikipedia/fallback). |

---
Related: PRIVACY.md, CONFIGURATION.md, OPERATIONS.md
