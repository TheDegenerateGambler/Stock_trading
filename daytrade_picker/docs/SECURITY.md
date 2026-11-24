---
Project:        daytrade_picker
Doc:            SECURITY.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Security - daytrade_picker

## Auth model

None for the tool itself. The only credential is an **Alpha Vantage API key**,
used read-only against the public AV API.

## Secret handling

- The AV key is read from the `AV_API_KEY` environment variable. **No key ships
  in source** (`config.py` falls back to `PASTE_YOUR_KEY_HERE`, which disables
  AV).
- A real key previously lived in source as a fallback and was scrubbed (and the
  README updated). If you ever used it, **rotate it** on Alpha Vantage - a
  committed key is considered burned.
- `.env`, `*.key`, and `output/` are git-ignored.

## Network surface

Outbound, read-only:

- **Alpha Vantage** - screener + news sentiment (needs the key).
- **Yahoo / yfinance** - bars + market-regime data.
- **Walter Bloomberg RSS** - news headlines for the sidebar.

Inbound: a **localhost-only** HTTP server on `127.0.0.1:8766` serving the
`output/` report. Not exposed off-box.

## Redaction policy

The report holds only public market data and public news headlines - no personal
data. If you paste a sample `live_data.json` into docs, no redaction is needed;
just avoid committing the live `output/` folder.

## Threat model & limitations

| Concern | Position |
|---------|----------|
| Key leakage | Env-only; `.gitignore` excludes `.env`/`*.key`. |
| Local server exposure | Bound to 127.0.0.1; not reachable off-box. |
| Data trust | AV/yfinance/RSS outages degrade gracefully (feature disabled or "unavailable"), not fatal. |
| Not advice | Picks are informational; no orders are placed. |

---
Related: PRIVACY.md, CONFIGURATION.md, OPERATIONS.md
