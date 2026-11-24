---
Project:        wheel_scanner
Doc:            RETENTION.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Retention & Deletion - wheel_scanner

## On-disk artefacts

| Artefact | Path | Size cap | Automatic deletion | Manual purge |
|----------|------|----------|--------------------|--------------|
| Mega dashboard | `output/` (HTML) | n/a | Overwritten each run | Delete `output/` |
| Intermediate scan JSON | `output/` | n/a | Overwritten each run | Delete `output/` |
| **Your holdings** | `my_positions.json` | n/a | **Never** - owner-managed | Delete the file |

`my_positions.json` holds personal financial data and is **only** created if the
owner copies the example and fills it in. It is git-ignored and never leaves the
machine.

## Full purge procedure

```
# From the project folder (Windows PowerShell)
Remove-Item -Recurse -Force .\output
Remove-Item -Force .\my_positions.json   # only if you created it
```

That removes all generated reports and your holdings file. To remove the tool
entirely, delete the `wheel_scanner/` folder and its `.venv`.

---
Related: DATA_INVENTORY.md, PRIVACY.md, OPERATIONS.md
