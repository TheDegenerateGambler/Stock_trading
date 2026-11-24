---
Project:        premarket_scanner
Doc:            RETENTION.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Retention & Deletion - premarket_scanner

## On-disk artefacts

| Artefact | Path | Size cap | Automatic deletion | Manual purge |
|----------|------|----------|--------------------|--------------|
| HTML report | `output/premarket_report.html` | n/a | Overwritten each scan | Delete `output/` |
| Picks JSON | `output/premarket_picks.json` | n/a | Overwritten each scan | Delete `output/` |
| Universe cache | cache file (~7-day TTL) | n/a | Refreshed after TTL | Delete the cache / `output/` |

All artefacts contain **public market data only**. Nothing is stored outside the
project folder; there is no database and no hidden state. `output/` is
git-ignored, so none of it is published.

## Full purge procedure

```
# From the project folder (Windows PowerShell)
Remove-Item -Recurse -Force .\output
```

That removes the report, picks JSON, and universe cache. To remove the tool
entirely, delete the `premarket_scanner/` folder and its `.venv`.

---
Related: DATA_INVENTORY.md, PRIVACY.md, OPERATIONS.md
