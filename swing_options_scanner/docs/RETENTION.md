---
Project:        swing_options_scanner
Doc:            RETENTION.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Retention & Deletion - swing_options_scanner

## On-disk artefacts

| Artefact | Path | Size cap | Automatic deletion | Manual purge |
|----------|------|----------|--------------------|--------------|
| HTML report | `output/swing_options_scanner.html` | n/a | Overwritten each scan | Delete `output/` |
| Picks JSON | `output/swing_picks.json` | n/a | Overwritten each scan | Delete `output/` |
| Earnings cache | `output/earnings_cache.json` | n/a | Refreshed as entries age | Delete `output/` |

All artefacts contain public market/options data only. There is no database or
hidden state, and `output/` is git-ignored.

## Full purge procedure

```
# From the project folder (Windows PowerShell)
Remove-Item -Recurse -Force .\output
```

That removes the report, picks JSON, and earnings cache. To remove the tool
entirely, delete the `swing_options_scanner/` folder and its `.venv`.

---
Related: DATA_INVENTORY.md, PRIVACY.md, OPERATIONS.md
