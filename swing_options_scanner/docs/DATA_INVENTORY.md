---
Project:        swing_options_scanner
Doc:            DATA_INVENTORY.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Data Inventory - swing_options_scanner

Usage context: **personal** trading-research tool run by its owner locally.

## Personal data fields processed

**None.** The scanner handles only **public market data**: prices, indicators,
options chains, earnings dates, and public news sentiment. No personal data of
the user or any individual is processed.

| Field | Source | Purpose | On-disk location | Retention |
|-------|--------|---------|------------------|-----------|
| Daily bars / indicators | yfinance (public) | Trend/momentum bias | `output/swing_picks.json`, report HTML | See RETENTION.md |
| Next-earnings date | yfinance (public) | Skip IV-crush names | `output/earnings_cache.json` | Cached; see RETENTION.md |
| Options chain + greeks | CBOE (public) | Contract selection | Same as picks | See RETENTION.md |
| News sentiment | Alpha Vantage (public) | Optional score input | Echoed into report | See RETENTION.md |

## Personal data fields explicitly NOT processed

- No user identity, account, login, or contact data.
- No brokerage credentials, balances, or positions.
- No location / device identifiers.
- The optional AV API key is a service credential, not personal data, and is
  never written to `output/`.

## Third parties

- **Alpha Vantage** - optional news sentiment (read-only; only ticker symbols
  sent).
- **Yahoo / yfinance** - bars + earnings (read-only).
- **CBOE** - options chain (read-only).
- **Wikipedia** - index membership (read-only).
- **TradingView** - chart widgets load in the browser (not by the Python
  process).

No data about the user is sent to any third party.

---
Related: PRIVACY.md, RETENTION.md, SECURITY.md
