---
Project:        swing_options_scanner
Doc:            PRIVACY.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Privacy - swing_options_scanner

## Lawful basis

**Legitimate interest (personal use).** The owner runs the scanner on their own
machine for personal swing-trade research. No third party's personal data is the
object of processing.

## Data minimisation decisions

- **Public data only** - prices, indicators, options chains, earnings dates, and
  optional public sentiment; never user or third-party personal data.
- **Symbols-only outbound** - requests carry only public ticker symbols.
- **No credentials on disk** - the optional AV key stays in the environment.
- **Ephemeral output** - each scan overwrites the report/JSON; the earnings
  cache holds only public dates.

## User rights

- **Access:** output is plain files the owner holds (`output/*`).
- **Rectification:** re-run to regenerate from fresh data.
- **Erasure:** delete `output/` (see RETENTION.md).

## Privacy-by-design assertions

- Runs locally; the report server binds to localhost only.
- No analytics, telemetry, or account system.
- Options quotes are informational and ~15 min delayed.

## Out of scope

- Not financial advice; outputs are informational.
- Does not place trades or connect to any brokerage.
- Does not verify third-party market/options data accuracy.

---
Related: DATA_INVENTORY.md, RETENTION.md, COMPLIANCE_CHECKLIST.md
