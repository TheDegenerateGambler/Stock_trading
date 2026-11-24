---
Project:        options_daytrader
Doc:            SECURITY.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Security - options_daytrader

## Auth model

None for core operation. CBOE and yfinance are public, unauthenticated,
read-only feeds. The only optional credential is an **Unusual Whales** flow
token, used only if the flow stub is enabled.

## Secret handling

- `UNUSUAL_WHALES_TOKEN` is read from the environment and defaults to empty.
  **Never hardcode or commit it.** The flow integration is a stub and inert
  unless both `UNUSUAL_WHALES_ENABLED` and a token are set.
- This project ships **no API keys** in source and needs no Alpha Vantage key of
  its own (it reads sentiment from the premarket scanner's output).
- `.env`, `*.key`, and `output/` are git-ignored.

## Network surface

Outbound, read-only:

- **CBOE** - `cdn.cboe.com/api/global/delayed_quotes/options/{sym}.json`.
- **Yahoo / yfinance** - underlying bars + chain fallback.
- **TradingView** - chart/options widgets load in the browser viewing the report
  (not fetched by the Python process).

Inbound: a **localhost-only** HTTP server serving the `output/` report.

## Redaction policy

The report holds only public market/options data. There is no personal data. The
premarket seed JSON it reads likewise contains only public tickers/headlines. Do
not commit the live `output/` folder.

## Threat model & limitations

| Concern | Position |
|---------|----------|
| Token leakage | Env-only; `.gitignore` excludes `.env`/`*.key`. |
| Local server exposure | Bound to localhost; not reachable off-box. |
| Delayed data | Options quotes ~15 min delayed; do not treat as execution prices. |
| Data trust | CBOE/yfinance outages are handled by fallback / skip, not fatal. |

---
Related: PRIVACY.md, CONFIGURATION.md, OPERATIONS.md
