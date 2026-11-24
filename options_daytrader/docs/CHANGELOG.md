---
Project:        options_daytrader
Doc:            CHANGELOG.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Changelog - options_daytrader

Dated entries (this project does not ship a numbered artefact).

## 2026-11-23 - Full docs
- Added the full Full-profile documentation set under `docs/` per the workspace
  DOCUMENTATION_STANDARD (Owner: The Gambler, Classification: Public), including
  the four GDPR-facing docs (public-market-data framing).
- Documented the optional Unusual Whales flow token as environment-only (never
  committed).
- No functional source changes.

## (Pre-docs) - Working baseline
Live options picker for 09:30-12:00 ET: composite signal engine
(VWAP/EMA/RSI/MACD/RVOL/gap/sentiment → score in [-100, +100]), SPY/QQQ always
plus gap-up candidates seeded from premarket_scanner, options chain from CBOE
(native greeks) with yfinance fallback, Δ 0.30-0.45 contract selection with
OI/volume/spread filters and ATR stop/target, console + HTML (TradingView
widgets) + JSON output, localhost report server, 5-min loop. History before this
date was not logged per change.

---
Related: ARCHITECTURE.md, MODULES.md, DEVELOPMENT.md
