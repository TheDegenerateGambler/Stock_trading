---
Project:        premarket_scanner
Doc:            COMPLIANCE_CHECKLIST.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# GDPR Compliance Checklist - premarket_scanner

Context: personal market-scanning tool; processes public market data only.

| # | Rule | How we comply | Evidence |
|---|------|---------------|----------|
| 1 | Lawful processing | Legitimate interest (personal use); public data only. | PRIVACY.md §Lawful basis |
| 2 | Data minimisation | Tickers/prices/public news only; symbols-only outbound; no credentials on disk. | PRIVACY.md §Data minimisation, DATA_INVENTORY.md |
| 3 | Right of access | All output is plain files the owner holds. | OPERATIONS.md §Inspecting stored data |
| 4 | Right to rectification | Re-run to regenerate from fresh data. | PRIVACY.md §User rights |
| 5 | Right to erasure | Documented purge of `output/`. | RETENTION.md §Full purge procedure |
| 6 | Retention & deletion | Output overwritten each scan; cache TTL ~7 days; nothing outside the folder. | RETENTION.md |
| 7 | Security of processing | Local-only, localhost report server, key in env not source. | SECURITY.md |
| 8 | Breach reporting | Not applicable - no personal data of third parties is collected or transmitted. | PRIVACY.md §Out of scope, SECURITY.md §Network surface |

---
Related: PRIVACY.md, DATA_INVENTORY.md, RETENTION.md
