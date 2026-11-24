---
Project:        daytrade_picker
Doc:            PRIVACY.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Privacy - daytrade_picker

## Lawful basis

**Legitimate interest (personal use).** The owner runs the picker on their own
machine to research public market movers. No third party's personal data is the
object of processing.

## Data minimisation decisions

- **Public data only** - prices, indicators, regime, sentiment, and public
  headlines; never user or third-party personal data.
- **Symbols-only outbound** - requests to AV / Yahoo carry only public ticker
  symbols; the RSS fetch is a public feed.
- **No credentials on disk** - the AV key stays in the environment.
- **Ephemeral output** - each scan overwrites the previous report/JSON.

## User rights

- **Access:** output is plain files the owner holds (`output/*`).
- **Rectification:** re-run to regenerate from fresh data.
- **Erasure:** delete `output/` (see RETENTION.md).

## Privacy-by-design assertions

- Runs locally; the report server binds to localhost only.
- No analytics, telemetry, or account system.
- Headlines are stored verbatim as public reporting; not mined for individuals.

## Out of scope

- Not financial advice; outputs are informational.
- Does not place trades or connect to a brokerage.
- Does not verify third-party market/news data accuracy.

---
Related: DATA_INVENTORY.md, RETENTION.md, COMPLIANCE_CHECKLIST.md
