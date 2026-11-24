---
Project:        wheel_scanner
Doc:            DATA_INVENTORY.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Data Inventory - wheel_scanner

Usage context: **personal** trading tool run by its owner locally. Unlike the
other scanners, this one can optionally read the owner's **own holdings**.

## Personal data fields processed

The scanner itself processes public market data. The **optional**
`my_positions.json` file contains the owner's own financial holdings - personal
financial data about the owner, provided by the owner, stored only locally.

| Field | Source | Purpose | On-disk location | Retention |
|-------|--------|---------|------------------|-----------|
| Holding ticker | `my_positions.json` (owner-provided) | CC-on-positions section | `my_positions.json` (git-ignored) | Until the owner deletes it |
| Cost basis | `my_positions.json` | Keep CC strikes ≥ cost basis | Same | Until deleted |
| Share count | `my_positions.json` | Size the covered-call | Same | Until deleted |
| Prices / option chains | yfinance (public) | Scan + score | `output/` dashboard/JSON | See RETENTION.md |

The holdings belong to the **owner about themselves**; no third party's personal
data is involved. The file is never transmitted anywhere - it is read locally
and reflected only into the local dashboard.

## Personal data fields explicitly NOT processed

- No third-party personal data.
- No account login, credentials, or brokerage connection (the tool does not log
  in anywhere).
- No location / device identifiers.
- No names/contact details.

## Third parties

- **Yahoo / yfinance** - prices + option chains (read-only; only public ticker
  symbols are sent). Your holdings are **never** sent to yfinance or anyone else.

No data leaves the machine except public ticker lookups.

---
Related: PRIVACY.md, RETENTION.md, SECURITY.md
