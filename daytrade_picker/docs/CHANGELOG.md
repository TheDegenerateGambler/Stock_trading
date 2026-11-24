---
Project:        daytrade_picker
Doc:            CHANGELOG.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Changelog - daytrade_picker

Dated entries (this project does not ship a numbered artefact). See the legacy
`FEATURE_LOG.md` for earlier narrative history.

## 2026-11-23 - Full docs + security hardening
- Added the full Full-profile documentation set under `docs/` per the workspace
  DOCUMENTATION_STANDARD (Owner: The Gambler, Classification: Public), including
  the four GDPR-facing docs (public-market-data framing).
- Kept the existing `FEATURE_LOG.md` and `docs/README.md` as grandfathered
  extras (the FEATURE_LOG now records the AV-key fix as resolved).
- Scrubbed the hardcoded Alpha Vantage key from `config.py` (now env-only) and
  added `.gitignore`. **Owner action:** rotate the previously-committed key.
- No functional source changes.

## 2026-07-10 (session 1) - Docs backfilled (legacy scheme)
- Created the original `FEATURE_LOG.md` + `docs/README.md` pointer.
- Flagged the hardcoded AV key (now fixed, see above).

## (Pre-docs) - Working baseline
Day-trade picker: AV screener + yfinance technicals + Walter Bloomberg RSS;
EMA/MACD/VWAP/ATR indicators; LONG/SHORT conviction with entry/stop/2:1 target;
SPY/QQQ/IWM + VIX regime banner; top-10 picks every 30 min (plus a midday
rescan); console + HTML (localhost server) + JSON output. History before
2026-07-10 was captured in the README baseline, not per change.

---
Related: ARCHITECTURE.md, MODULES.md, DEVELOPMENT.md
