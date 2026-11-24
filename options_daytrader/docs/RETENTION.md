---
Project:        options_daytrader
Doc:            RETENTION.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Retention & Deletion - options_daytrader

## On-disk artefacts

| Artefact | Path | Size cap | Automatic deletion | Manual purge |
|----------|------|----------|--------------------|--------------|
| HTML report | `output/options_daytrader.html` | n/a | Overwritten each scan | Delete `output/` |
| Picks JSON | `output/options_daytrader.json` | n/a | Overwritten each scan | Delete `output/` |

The picker **reads** `../premarket_scanner/output/premarket_picks.json` but does
not own it - that file is managed (and purged) by the premarket_scanner project.

All artefacts contain public market/options data only. There is no database or
hidden state, and `output/` is git-ignored.

## Full purge procedure

```
# From the project folder (Windows PowerShell)
Remove-Item -Recurse -Force .\output
```

To also clear the gap-up seed, purge the premarket scanner's `output/` (see that
project's RETENTION.md). To remove the tool entirely, delete the
`options_daytrader/` folder and its `.venv`.

---
Related: DATA_INVENTORY.md, PRIVACY.md, OPERATIONS.md
