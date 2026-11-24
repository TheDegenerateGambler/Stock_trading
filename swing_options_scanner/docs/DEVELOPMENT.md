---
Project:        swing_options_scanner
Doc:            DEVELOPMENT.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Development - swing_options_scanner

## Local setup

```
python -m venv .venv
.venv\Scripts\activate         # Windows
pip install -r requirements.txt
```

`.venv/` and `output/` are git-ignored.

## Layout

```
swing_options_scanner/
├── scanner.py              entry + local HTTP server
├── config.py              budget, filters, DTE/Δ, weights, AV
├── universe_builder.py    S&P500 + Russell1000 + price/vol filter
├── technical_screener.py  daily EMA/RSI/MACD/ATR/RVOL + bias
├── earnings_calendar.py   next-earnings lookup + cache
├── swing_ranker.py        composite 0-100 score
├── options_selector.py    CBOE contract selection within budget
├── trade_builder.py       entry/targets/stop/R:R/time stop
├── report_builder.py      console + HTML + swing_picks.json
├── requirements.txt
├── run.bat
└── docs/
```

## Conventions

- **Config over literals** - budget, filters, DTE/Δ, weights, trade rules all in
  `config.py`; update CONFIGURATION.md in the same change.
- **Earnings-aware by default** - do not loosen `SKIP_EARNINGS_DAYS` without
  understanding IV-crush risk.
- **No secrets in source** - AV key via `AV_API_KEY` only.
- **Budget is a first-class filter** - keep cost in both the selector and the
  score.
- Most modules have a `__main__` smoke test - keep them working.

## Adding a scoring component

1. Compute it in `swing_ranker.py` (or feed from `technical_screener.py`).
2. Add its weight to `config.SCORE_WEIGHTS` (keep the total interpretable as
   0-100).
3. Surface it in `report_builder.py` + the JSON.
4. Update CONFIGURATION.md, MODULES.md, CHANGELOG.md.

## Dependency-add policy

Prefer the existing stack (`yfinance`, `requests`, numeric libs). Justify
heavyweight additions and pin them in `requirements.txt`.

---
Related: TESTING.md, MODULES.md, CONFIGURATION.md
