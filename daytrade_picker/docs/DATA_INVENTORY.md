---
Project:        daytrade_picker
Doc:            DATA_INVENTORY.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Data Inventory - daytrade_picker

Usage context: **personal** market-scanning tool run by its owner locally.

## Personal data fields processed

**None.** The picker processes only **public market data**: ticker
prices/volumes, technical indicators, regime data, news sentiment, and public
RSS headlines. No personal data of the user or any individual is processed.

| Field | Source | Purpose | On-disk location | Retention |
|-------|--------|---------|------------------|-----------|
| Ticker / price / volume | Alpha Vantage / yfinance (public) | Screen + score picks | `output/live_data.json`, report HTML | See RETENTION.md |
| News sentiment | Alpha Vantage (public) | Conviction input | Same | See RETENTION.md |
| Regime (SPY/QQQ/IWM/VIX) | yfinance (public) | Regime banner | Same | See RETENTION.md |
| News headlines | Walter Bloomberg RSS (public) | Sidebar | Same | See RETENTION.md |

Headlines are public journalism; they may mention people only incidentally as
part of public reporting and are stored verbatim, not analysed for individuals.

## Personal data fields explicitly NOT processed

- No user identity, account, login, or contact data.
- No brokerage credentials, balances, or positions.
- No location / device identifiers.
- The Alpha Vantage API key is a service credential, not personal data, and is
  never written to `output/`.

## Third parties

- **Alpha Vantage** - screener + sentiment (read-only; only ticker symbols sent).
- **Yahoo / yfinance** - bars + regime (read-only).
- **Walter Bloomberg RSS** - public headline feed (read-only).

No data about the user is sent to any third party.

---
Related: PRIVACY.md, RETENTION.md, SECURITY.md
