---
Project:        swing_options_scanner
Doc:            CHANGELOG.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Changelog - swing_options_scanner

Dated entries (this project does not ship a numbered artefact).

## 2026-11-23 - Full docs + security hardening
- Added the full Full-profile documentation set under `docs/` per the workspace
  DOCUMENTATION_STANDARD (Owner: The Gambler, Classification: Public), including
  the four GDPR-facing docs (public-market-data framing).
- Scrubbed the hardcoded Alpha Vantage key from `config.py`; the key now comes
  only from `AV_API_KEY`. Corrected the README's "bundled fallback key" wording.
  **Owner action:** rotate the previously-committed key.
- `.gitignore` already excludes `.env`/`*.key`/`output/`/`.venv/`.
- No functional source changes.

## (Pre-docs) - Working baseline
Swing options scanner for small accounts (~$110 budget): S&P 500 + Russell 1000
universe filtered to $10-$100 / >5M vol, daily technical bias, earnings-window
avoidance, CBOE contract selection (DTE 21-45, Δ 0.30-0.50, OI/spread/budget),
composite 0-100 scoring with optional AV sentiment, trade plan
(targets/stop/R:R/time stop), console + HTML (TradingView charts) + JSON output.
History before this date was not logged per change.

---
Related: ARCHITECTURE.md, MODULES.md, DEVELOPMENT.md
