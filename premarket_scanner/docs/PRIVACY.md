---
Project:        premarket_scanner
Doc:            PRIVACY.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Privacy - premarket_scanner

## Lawful basis

**Legitimate interest (personal use).** The owner runs the scanner on their own
machine to research public market movers. No personal data of any third party is
the object of processing.

## Data minimisation decisions

- **Public data only.** The scanner handles tickers, prices, volumes, and public
  news - never user or third-party personal data.
- **Symbols-only outbound.** Requests to Alpha Vantage / Yahoo / Wikipedia carry
  only public ticker symbols; no user identity is transmitted.
- **No credentials stored on disk.** The optional AV key stays in the
  environment and is never written to `output/`.
- **Ephemeral, overwritten output.** Each scan overwrites the previous report.

## User rights

- **Access:** all output is plain files the owner holds (`output/*.html/.json`).
- **Rectification:** re-run to regenerate from fresh data.
- **Erasure:** delete `output/` (see RETENTION.md).

## Privacy-by-design assertions

- Runs locally; the report server binds to `127.0.0.1` only.
- No analytics, telemetry, or account system.
- News headlines are stored verbatim as public reporting; they are not mined for
  information about individuals.

## Out of scope

- The scanner does not give financial advice; outputs are informational.
- It does not verify the accuracy of third-party market/news data.

---
Related: DATA_INVENTORY.md, RETENTION.md, COMPLIANCE_CHECKLIST.md
