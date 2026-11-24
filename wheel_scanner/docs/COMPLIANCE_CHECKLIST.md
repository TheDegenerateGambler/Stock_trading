---
Project:        wheel_scanner
Doc:            COMPLIANCE_CHECKLIST.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# GDPR Compliance Checklist - wheel_scanner

Context: personal wheel-strategy tool; processes public market data plus the
owner's own optional holdings (local only).

| # | Rule | How we comply | Evidence |
|---|------|---------------|----------|
| 1 | Lawful processing | Own content / legitimate interest; only the owner's own data + public market data. | PRIVACY.md §Lawful basis |
| 2 | Data minimisation | Holdings optional, local, never transmitted; symbols-only outbound; no credentials. | PRIVACY.md §Data minimisation, DATA_INVENTORY.md |
| 3 | Right of access | Holdings and reports are plain files the owner holds. | OPERATIONS.md §Inspecting stored data |
| 4 | Right to rectification | Edit `my_positions.json` and re-run. | PRIVACY.md §User rights |
| 5 | Right to erasure | Documented deletion of `my_positions.json` + `output/`. | RETENTION.md §Full purge procedure |
| 6 | Retention & deletion | Reports overwritten each run; holdings owner-managed; nothing outside the folder. | RETENTION.md |
| 7 | Security of processing | Local-only, no server, no keys; holdings git-ignored; committed `.venv/` removed. | SECURITY.md |
| 8 | Breach reporting | Not applicable - no third-party personal data; the only personal data is the owner's own, held locally and never transmitted. | PRIVACY.md §Out of scope, SECURITY.md |

---
Related: PRIVACY.md, DATA_INVENTORY.md, RETENTION.md
