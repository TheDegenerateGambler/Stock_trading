---
Project:        premarket_scanner
Doc:            DEVELOPMENT.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Development - premarket_scanner

## Local setup

```
python -m venv .venv
.venv\Scripts\activate         # Windows
pip install -r requirements.txt
```

The virtualenv (`.venv/`) and `output/` are git-ignored.

## Layout

```
premarket_scanner/
├── scanner.py              entry + loop + local HTTP server
├── config.py               thresholds, schedule, AV settings
├── universe.py             build/cache the ticker universe
├── premarket_data.py       concurrent yfinance premarket bars + filter
├── news_fetcher.py         AV sentiment + catalyst + yfinance fallback
├── alphavantage_client.py  rate-limited AV client
├── report_builder.py       console + HTML + JSON output
├── requirements.txt
├── run.bat
└── docs/
```

## Conventions

- **Config over literals.** New tunables go in `config.py` + a CONFIGURATION.md
  row in the same change.
- **US/Eastern time** for anything schedule-related; always specify the TZ.
- **Respect the AV free tier.** Route all AV calls through
  `alphavantage_client.py` so the budget/throttle is honoured.
- **No secrets in source.** The AV key comes from `AV_API_KEY` only.
- **Keep the report self-contained.** HTML/JSON are written under `output/`.

## Adding a filter or signal

1. Add the threshold to `config.py`.
2. Apply it in `premarket_data.py` (bars/filter) or `news_fetcher.py` (catalyst).
3. Surface the new column in `report_builder.py` (console + HTML + JSON).
4. Update CONFIGURATION.md, MODULES.md, CHANGELOG.md.

## Dependency-add policy

Prefer the existing stack (`yfinance`, `requests`, `pandas`, `lxml`). Justify
any heavyweight addition and pin it in `requirements.txt`.

---
Related: TESTING.md, MODULES.md, CONFIGURATION.md
