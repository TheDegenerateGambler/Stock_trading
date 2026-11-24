---
Project:        options_daytrader
Doc:            DATA_INVENTORY.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Data Inventory - options_daytrader

Usage context: **personal** trading-research tool run by its owner locally.

## Personal data fields processed

**None.** The picker handles only **public market data**: underlying prices,
indicators, options chains/greeks, and sentiment scores reused from the
premarket scanner's output. No personal data of the user or any individual is
processed.

| Field | Source | Purpose | On-disk location | Retention |
|-------|--------|---------|------------------|-----------|
| Underlying bars / indicators | yfinance (public) | Directional signal | `output/options_daytrader.json`, report HTML | See RETENTION.md |
| Options chain + greeks | CBOE / yfinance (public) | Contract selection | Same | See RETENTION.md |
| Sentiment score | premarket_scanner output (public news) | Signal input | Read-only input; echoed into report | See RETENTION.md |

## Personal data fields explicitly NOT processed

- No user identity, account, login, or contact data.
- No brokerage credentials, balances, or positions.
- No location / device identifiers.
- The optional Unusual Whales token is a service credential, not personal data,
  and is never written to `output/`.

## Third parties

- **CBOE** - delayed options quotes (read-only; only ticker symbols sent).
- **Yahoo / yfinance** - bars + chain fallback (read-only).
- **TradingView** - chart/options widgets load in the browser (not by the Python
  process).
- **Unusual Whales** - only if the flow stub is explicitly enabled with a token.

No data about the user is sent to any third party.

---
Related: PRIVACY.md, RETENTION.md, SECURITY.md
