---
Project:        wheel_scanner
Doc:            SECURITY.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Security - wheel_scanner

## Auth model

None. The scanner uses only public, unauthenticated yfinance data and has no
accounts, API keys, or servers.

## Secret handling

- **No API keys** anywhere in this project.
- The only sensitive local file is **`my_positions.json`** - the user's own
  holdings (ticker, cost basis, shares). It is **git-ignored** and must never be
  committed. Only `my_positions.example.json` (dummy data) is tracked.
- `.env`, `*.key`, `output/`, and `.venv/` are git-ignored.

## Important: a committed virtualenv was removed

A full `.venv/` (third-party site-packages) had been committed to this repo. It
was removed from tracking on 2026-11-23 and added to `.gitignore`. If the repo's
git history ever contained it, consider the history bloated - a fresh repo or a
history rewrite is the clean fix before publishing.

## Network surface

Outbound, read-only: **Yahoo / yfinance** for prices and option chains. No
inbound server - the dashboard is a static HTML file opened directly.

## Redaction policy

- Reports contain public market data (tickers, prices, option quotes) - no
  redaction needed.
- `my_positions.json` contains personal financial data; **never paste real
  holdings into docs**. The example file uses fabricated values.

## Threat model & limitations

| Concern | Position |
|---------|----------|
| Personal holdings leakage | `my_positions.json` is git-ignored; only the example is tracked. |
| Committed dependencies | `.venv/` removed from tracking + ignored. |
| Data trust | yfinance TSX options data can be sparse/delayed; verify with your broker before trading. |
| No secrets | Nothing to leak - no keys used. |

---
Related: PRIVACY.md, DATA_INVENTORY.md, OPERATIONS.md
