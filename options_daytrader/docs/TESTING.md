---
Project:        options_daytrader
Doc:            TESTING.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Testing - options_daytrader

No automated suite yet; the project is exercised manually. `call_flow.py` has a
`__main__` CLI entry useful for isolating the flow path.

## Smoke tests

```
# One full scan, bypassing the session gate (any time of day)
python daytrader.py --once --force --no-browser

# Exercise the options-flow path alone
python call_flow.py
```

## Testing each layer in isolation

| Layer | How to exercise |
|-------|-----------------|
| Signal engine | `--once --force`; confirm SPY/QQQ show a composite score + CALL/PUT/NO-TRADE. |
| Premarket seed | Ensure `../premarket_scanner/output/premarket_picks.json` exists; confirm gap-ups appear in the watchlist. |
| CBOE chain | Run during/after market hours; confirm greeks (Δ Γ Θ ν) populate from CBOE. |
| yfinance fallback | Temporarily force CBOE to fail; confirm Δ is computed via Black-Scholes. |
| Contract ranker | Confirm chosen contracts sit in Δ 0.30-0.45 and meet OI/volume/spread; watch for `LOW LIQUIDITY` flags. |
| Report | Open `output/options_daytrader.html`; inspect `output/options_daytrader.json`. |

## Dry-run tips

- `--force` runs outside 09:30-12:00 ET for off-hours testing (quotes will be
  the last delayed snapshot).
- `--no-browser` avoids opening a tab each scan.
- `--interval` shortens the loop while iterating.

## Adding automated tests

Target the pure-ish logic: the composite scoring in `signal_engine.py` (feed it
synthetic indicator inputs) and the contract-filter predicates in
`options_ranker.py`. Stub `requests`/`yfinance` to stay offline.

---
Related: DEVELOPMENT.md, MODULES.md, OPERATIONS.md
