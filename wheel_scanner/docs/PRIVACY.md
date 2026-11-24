---
Project:        wheel_scanner
Doc:            PRIVACY.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Privacy - wheel_scanner

## Lawful basis

**Own content / legitimate interest (personal use).** The owner runs the scanner
locally and may optionally record **their own** holdings. The only personal data
involved is the owner's data about themselves; no third party is involved.

## Data minimisation decisions

- **Holdings are optional and owner-provided.** Without `my_positions.json` the
  tool processes only public market data.
- **Holdings never leave the machine.** They are read locally and reflected only
  into the local dashboard; they are never sent to yfinance or any service.
- **Symbols-only outbound** - network requests carry only public ticker symbols.
- **No account/credentials** - the tool never logs into a brokerage.
- **Ephemeral reports** - the dashboard is overwritten each run.

## User rights

- **Access:** the owner's holdings are a plain JSON file they wrote
  (`my_positions.json`); reports are plain files under `output/`.
- **Rectification:** edit `my_positions.json` and re-run.
- **Erasure:** delete `my_positions.json` and `output/` (see RETENTION.md).

## Privacy-by-design assertions

- Fully local; no server, no telemetry, no account.
- Holdings data is git-ignored by default so it is never published.
- Only a fabricated `my_positions.example.json` is tracked in the repo.

## Out of scope

- Not financial advice; outputs are informational.
- Does not place trades or connect to a brokerage.
- yfinance TSX options data may be sparse/delayed - verify with your broker.

---
Related: DATA_INVENTORY.md, RETENTION.md, COMPLIANCE_CHECKLIST.md
