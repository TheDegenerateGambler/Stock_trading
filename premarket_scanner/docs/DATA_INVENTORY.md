---
Project:        premarket_scanner
Doc:            DATA_INVENTORY.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Data Inventory - premarket_scanner

Usage context: **personal** market-scanning tool run by its owner on their own
machine.

## Personal data fields processed

**None.** The scanner processes only **public market data**: ticker symbols,
prices/volumes, gap percentages, and publicly published news headlines +
sentiment scores. It does not process any personal data about the user or any
identifiable individual.

| Field | Source | Purpose | On-disk location | Retention |
|-------|--------|---------|------------------|-----------|
| Ticker / price / volume | yfinance (public) | Compute gap + filter | `output/premarket_picks.json`, report HTML | See RETENTION.md |
| News headline / sentiment | Alpha Vantage / yfinance (public) | Catalyst context | Same | See RETENTION.md |

News headlines are public journalism; they may mention people (e.g. executives)
only incidentally as part of public reporting, and are stored verbatim, not
indexed or analysed for individuals.

## Personal data fields explicitly NOT processed

- No user identity, account, login, or contact data.
- No brokerage credentials or positions.
- No location / device identifiers.
- The optional Alpha Vantage API key is a service credential, not personal data,
  and is never written to `output/`.

## Third parties

- **Alpha Vantage** - movers + news sentiment (read-only API calls; only ticker
  symbols are sent).
- **Yahoo / yfinance** - premarket bars + news fallback (read-only).
- **Wikipedia** - index membership scraping (read-only).

No data about the user is sent to any third party; requests contain only public
ticker symbols.

---
Related: PRIVACY.md, RETENTION.md, SECURITY.md
