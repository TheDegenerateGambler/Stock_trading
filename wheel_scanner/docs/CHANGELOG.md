---
Project:        wheel_scanner
Doc:            CHANGELOG.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Changelog - wheel_scanner

Dated entries (this project does not ship a numbered artefact).

## 2026-11-23 - Full docs + repo hygiene
- Added the full Full-profile documentation set under `docs/` per the workspace
  DOCUMENTATION_STANDARD (Owner: The Gambler, Classification: Public), including
  the four GDPR-facing docs. Unlike the sibling scanners, the GDPR docs here
  cover the owner's optional personal holdings (`my_positions.json`).
- **Added `.gitignore`** excluding `.venv/`, `output/`, `.env`/`*.key`, and
  `my_positions.json`. A full virtualenv (`.venv/`) had been committed; it is now
  untracked. **Owner action:** if `.venv/` or `my_positions.json` ever entered
  git history, scrub history (or start the public repo fresh) before publishing.
- No functional source changes.

## (Pre-docs) - Working baseline
One-click Canadian Wheel scanner for a ~$1,000 CAD NBDB account: monthly/weekly
CSPs + covered calls across cheap TSX names, TSX blue-chips, and liquid US names;
yfinance prices + option chains; NBDB fee model + affordability filter; optional
CCs on user positions (strikes ≥ cost basis); combined mega HTML dashboard with
Top-10 leaderboard + client-side search. History before this date was not logged
per change.

---
Related: ARCHITECTURE.md, MODULES.md, DEVELOPMENT.md
