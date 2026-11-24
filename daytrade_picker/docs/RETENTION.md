---
Project:        daytrade_picker
Doc:            RETENTION.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Retention & Deletion - daytrade_picker

## On-disk artefacts

| Artefact | Path | Size cap | Automatic deletion | Manual purge |
|----------|------|----------|--------------------|--------------|
| HTML report | `output/report.html` | n/a | Overwritten each scan | Delete `output/` |
| Live data JSON | `output/live_data.json` | n/a | Overwritten each scan | Delete `output/` |

All artefacts contain public market data and public headlines only. There is no
database or hidden state, and `output/` is git-ignored.

## Full purge procedure

```
# From the project folder (Windows PowerShell)
Remove-Item -Recurse -Force .\output
```

That removes the report and live-data JSON. To remove the tool entirely, delete
the `daytrade_picker/` folder and its `.venv`.

---
Related: DATA_INVENTORY.md, PRIVACY.md, OPERATIONS.md
