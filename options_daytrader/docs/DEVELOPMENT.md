---
Project:        options_daytrader
Doc:            DEVELOPMENT.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Development - options_daytrader

## Local setup

```
python -m venv .venv
.venv\Scripts\activate         # Windows
pip install -r requirements.txt
```

`.venv/` and `output/` are git-ignored.

## Layout

```
options_daytrader/
├── daytrader.py           entry + 5-min loop + local HTTP server
├── config.py              session, weights, contract rules
├── signal_engine.py       composite directional score (-100..100)
├── options_chain.py       chain fetch (CBOE → yfinance)
├── cboe_client.py         CBOE delayed-quotes JSON + native greeks
├── options_ranker.py      contract selection + ATR stop/target
├── call_flow.py           optional options-flow path
├── unusualwhales_stub.py  inert flow stub (enable via config)
├── report_builder.py      console + HTML (TradingView widgets) + JSON
├── requirements.txt
├── run.bat
└── docs/
```

## Conventions

- **Config over literals** - weights, thresholds, Δ band, expiry policy all live
  in `config.py`; update CONFIGURATION.md in the same change.
- **US/Eastern time** for the session; always specify TZ.
- **CBOE first, yfinance fallback** - prefer native greeks; only compute
  Black-Scholes Δ in the fallback path.
- **No secrets in source** - any flow token comes from `UNUSUAL_WHALES_TOKEN`.
- **Reuse the premarket seed** rather than re-fetching sentiment.

## Adding a signal to the engine

1. Compute the indicator in `signal_engine.py`.
2. Add its weight to `config.SIGNAL_WEIGHTS` (keep the composite interpretable in
   [-100, +100]).
3. Surface it in `report_builder.py` and the JSON record.
4. Update CONFIGURATION.md, MODULES.md, CHANGELOG.md.

## Dependency-add policy

Prefer the existing stack (`requests`, `yfinance`, numeric libs). Justify
heavyweight additions and pin them in `requirements.txt`.

---
Related: TESTING.md, MODULES.md, CONFIGURATION.md
