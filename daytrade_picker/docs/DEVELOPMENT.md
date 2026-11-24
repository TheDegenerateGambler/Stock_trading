---
Project:        daytrade_picker
Doc:            DEVELOPMENT.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Development - daytrade_picker

## Local setup

```
python -m venv .venv
.venv\Scripts\activate         # Windows
pip install -r requirements.txt
```

`.venv/` and `output/` are git-ignored.

## Layout

```
daytrade_picker/
├── pick.py              entry + scan loop + local HTTP server + news thread
├── config.py           AV settings, scan sizes, scoring thresholds
├── alphavantage.py     rate-limited AV client (screener + sentiment)
├── indicators.py       pure EMA/MACD/VWAP/ATR
├── scorer.py           LONG/SHORT conviction + entry/stop/target
├── market_regime.py    SPY/QQQ/IWM + VIX regime banner
├── walter_bloomberg.py RSS headlines sidebar feed
├── report_builder.py   HTML + JSON writers
├── html_styles.py      CSS + JS for the report
├── requirements.txt
├── run.bat
└── docs/               (incl. grandfathered FEATURE_LOG.md)
```

## Conventions

- **Config over literals** - scan sizes, intervals, thresholds in `config.py`;
  update CONFIGURATION.md in the same change.
- **Keep `indicators.py` pure** - no I/O, so it stays unit-testable.
- **Route AV through `alphavantage.py`** so the free-tier throttle/budget holds.
- **No secrets in source** - AV key via `AV_API_KEY` only.
- **Degrade gracefully** - a failed regime/news fetch must not abort a scan.
- The legacy `FEATURE_LOG.md` is grandfathered; log material changes in
  `CHANGELOG.md` going forward.

## Adding an indicator or scoring rule

1. Add a pure function to `indicators.py` (or a threshold to `config.py`).
2. Use it in `scorer.py`; keep LONG/SHORT conviction interpretable.
3. Surface it in `report_builder.py` + the JSON.
4. Update CONFIGURATION.md, MODULES.md, CHANGELOG.md.

## Dependency-add policy

Prefer the existing stack (`requests`, `yfinance`, `feedparser`, numeric libs).
Justify heavyweight additions and pin them in `requirements.txt`.

---
Related: TESTING.md, MODULES.md, CONFIGURATION.md
