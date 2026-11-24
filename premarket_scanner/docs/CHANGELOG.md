---
Project:        premarket_scanner
Doc:            CHANGELOG.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Changelog - premarket_scanner

Dated entries (this project does not ship a numbered artefact).

## 2026-11-23 - Full docs + security hardening
- Added the full Full-profile documentation set under `docs/` per the workspace
  DOCUMENTATION_STANDARD (Owner: The Gambler, Classification: Public), including
  the four GDPR-facing docs (public-market-data framing).
- Scrubbed the hardcoded Alpha Vantage key from `config.py`; the key now comes
  only from the `AV_API_KEY` environment variable. **Owner action:** rotate the
  previously-committed key.
- Added `.gitignore` excluding `.env`/`*.key`/`output/`/`.venv/`.
- No functional source changes.

## (Pre-docs) - Working baseline
Premarket gap-up scanner: universe build (AV movers + S&P 500 + Russell 1000 +
fallback, cached), concurrent yfinance premarket bars, hard filters
(gap > 5%, price > $3, pm_vol > 50k, top 10), AV news sentiment + catalyst
tagging with yfinance fallback, console + HTML + JSON output, localhost report
server, 20-min loop exiting at 09:20 ET. History before this date was not logged
per change.

---
Related: ARCHITECTURE.md, MODULES.md, DEVELOPMENT.md
