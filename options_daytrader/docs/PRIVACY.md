---
Project:        options_daytrader
Doc:            PRIVACY.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Privacy - options_daytrader

## Lawful basis

**Legitimate interest (personal use).** The owner runs the picker on their own
machine for personal trading research. No third party's personal data is the
object of processing.

## Data minimisation decisions

- **Public data only** - prices, indicators, options chains, and reused public
  sentiment; never user or third-party personal data.
- **Symbols-only outbound** - CBOE/yfinance requests carry only ticker symbols.
- **No credentials on disk** - the optional flow token stays in the environment.
- **Ephemeral output** - each scan overwrites the previous report/JSON.
- **Reuse over re-fetch** - sentiment is read from the premarket scanner rather
  than re-querying a third party.

## User rights

- **Access:** output is plain files the owner holds (`output/*.html/.json`).
- **Rectification:** re-run to regenerate from fresh data.
- **Erasure:** delete `output/` (see RETENTION.md).

## Privacy-by-design assertions

- Runs locally; the report server binds to localhost only.
- No analytics, telemetry, or account system.
- Options quotes are clearly labelled as ~15 min delayed, informational only.

## Out of scope

- Not financial advice; outputs are informational.
- Does not place trades or connect to any brokerage.
- Does not verify third-party market/options data accuracy.

---
Related: DATA_INVENTORY.md, RETENTION.md, COMPLIANCE_CHECKLIST.md
