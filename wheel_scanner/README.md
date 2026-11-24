# 🇨🇦 Canadian Wheel Scanner

Finds the best **cash-secured put (CSP)** and **covered call (CC)** candidates for a small account at **National Bank Direct Brokerage (NBDB)**.

## ⚡ One-click usage

Just run:

```bat
wheel.bat
```

Double-click `wheel.bat` (or run it from a terminal). It will:

1. Set up its own Python virtual environment on the first run.
2. Scan **everything** — monthly + weekly puts + calls across cheap TSX names, TSX blue-chips, and liquid US names.
3. Build **one HTML dashboard** with a Top-10 leaderboard + all sections + a live search box.
4. **Open the dashboard in your default browser** when done.

That's it. No flags to remember.

---

## What gets scanned

| Section | Universe | DTE | Best for |
|---|---|---|---|
| 🇨🇦 Monthly Puts — Cheap TSX | ~30 names ≤ $10 CAD | 20-55d | $1,000 CAD starter accounts |
| 🇨🇦 Monthly Covered Calls — Cheap TSX (buy-write) | Same | 20-55d | Same |
| 🇺🇸 Weekly Puts — US names | Ford, SOFI, INTC, etc. | 4-14d | USD accounts, faster premium cycles |
| 🇨🇦 Weekly Puts — TSX blue-chips | RY, BNS, ENB, etc. | 4-14d | Larger accounts ($6k+) |
| 🇺🇸 Weekly Covered Calls — US names (buy-write) | Same US universe | 4-14d | USD accounts |
| 📂 Covered Calls — Your Positions | From `my_positions.json` (optional) | 20-55d | If you own shares already |

The dashboard also includes:
- 🏆 **Top 10 Overall** — best trades from every section, sorted by score
- 🔎 **Live search** — type a ticker to filter every table instantly
- 🟢🟡⚪ **Color-coded scores** — green ≥ 70, amber ≥ 45, grey below

---

## Optional: track your existing positions

Copy `my_positions.example.json` to `my_positions.json` and fill in your holdings:

```json
[
  {"ticker": "BTO.TO", "cost_basis": 4.85, "shares": 100},
  {"ticker": "F",      "cost_basis": 11.80, "shares": 100}
]
```

Next `wheel.bat` run will add a **"Covered Calls — Your Positions"** section with strikes at/above your cost basis (never lock in a loss).

If the file doesn't exist, the section is silently skipped.

## What is "The Wheel"?

1. **Sell a cash-secured put** on a stock you'd be happy to own.
2. If not assigned → keep the premium, repeat.
3. If assigned → you now own 100 shares at the strike price.
4. **Sell covered calls** at or above your cost basis.
5. If called away → keep premium + capital gain, restart step 1.

## Broker assumptions (NBDB)
- **$0 commission** on stock buys/sells
- **$6.95 per options contract** (flat, up to 6 contracts)
- Prices in **CAD**

Configured in [`config.py`](config.py).

## Advanced usage (per-scanner CLIs)

`wheel.bat` runs everything. But if you want granular control, the individual scanners are still available:

### CSP scanner only (Wheel Step 1)
```bat
cd Stock_trading\wheel_scanner
run.bat
```

### Covered call scanner only (Wheel Step 2)
```bat
:: Buy-write scan (planning to buy 100 shares + immediately sell a call)
run_cc.bat --buy-write

:: You already own shares (format TICKER:COST_BASIS:SHARES)
run_cc.bat --positions BTO.TO:5.20:100 BB.TO:4.80:100

:: Run BOTH scanners and produce the combined dashboard
run_cc.bat --buy-write --run-puts
```

### Manual install (any OS)
```bash
python -m venv .venv
.venv\Scripts\activate         # Windows
# source .venv/bin/activate    # macOS/Linux
pip install -r requirements.txt
python scan.py                             # puts
python scan_cc.py --buy-write              # calls (buy-write)
python scan_cc.py --positions BTO.TO:5.20  # calls (existing position)
```

### Weekly mode (US + TSX large-caps)
```bat
:: Best CSPs on weekly-optionable US names (Ford, SOFI, INTC, etc.)
run.bat --weekly --us-only

:: Best CSPs on weekly-optionable TSX names (RY, BNS, ENB…) — needs bigger budget
run.bat --weekly --tsx-only --budget 8000

:: Both, with full wheel dashboard (puts + calls)
run_cc.bat --buy-write --weekly --run-puts
```

Weekly mode uses tighter filters (OI ≥ 50, spread ≤ 20%, bid ≥ $0.03), 4–14 DTE, and switches commissions automatically:
**$6.95 CAD per contract for TSX** / **$1.25 USD per contract for US** (NBDB).

The scanner is currency-aware: it converts your CAD budget to USD for affordability checks on US names using `--usd-cad` (default 1.36).

### CLI options
```
python scan.py --help
  tickers ...              Custom ticker list
  --weekly                 Weekly-options mode (4-14 DTE, US+TSX watchlists)
  --us-only                Weekly: US watchlist only
  --tsx-only               Weekly: TSX watchlist only
  --max-price   Max stock price in NATIVE currency (default $10 monthly)
  --min-price   Min stock price (default $2)
  --budget      Cash budget CAD (default $1000)
  --usd-cad     FX rate for USD affordability check (default 1.36)

python scan_cc.py --help
  --positions TICKER:COST[:SHARES] ...   Existing holdings
  --buy-write                            Scan watchlist for buy-write setups
  --tickers ...                          Custom buy-write tickers
  --weekly                               Weekly-options mode
  --us-only / --tsx-only                 Weekly watchlist filter
  --no-budget-enforce                    Ignore $1000 budget in buy-write mode
  --usd-cad                              FX rate (default 1.36)
  --run-puts                             Also run CSP scanner + build dashboard
  --dashboard                            Just build the combined dashboard
```

## Outputs
Written to `./output/`:

**CSP (puts) reports:**
- `wheel_candidates.html` / `.csv` / `.txt` / `.json`

**CC (calls) reports:**
- `cc_candidates.html` / `.csv` / `.txt` / `.json`

**Combined:**
- `wheel_dashboard.html` — top puts + top calls on one page (best starting view)

## How it ranks

### Cash-secured puts (0–100 composite)
| Weight | Factor | Rationale |
|---|---|---|
| 45% | **Annualized net yield** | Premium ÷ collateral × 365/DTE, after $6.95 commission |
| 25% | **Liquidity** | Open interest (60%) + tight bid/ask spread (40%) |
| 20% | **Downside cushion** | How far the breakeven is below current price |
| 10% | **Affordability** | Rewards using less of the $1,000 budget so you can diversify |

### Covered calls (0–100 composite)
| Weight | Factor | Rationale |
|---|---|---|
| 45% | **Annualized if-called yield** | (Premium + capital gain to strike) ÷ cost basis × 365/DTE, after commission |
| 25% | **Liquidity** | Open interest (60%) + tight bid/ask spread (40%) |
| 20% | **Upside room** | Distance from spot to strike — more room = less likely to be capped early |
| 10% | **Downside protection** | Premium as % of stock price — cushion if the stock drops |

Both fully configurable in `config.py`.

## Filters applied

**Cash-secured puts:**
- Stock price between `$2.00` and `$10.00` CAD
- Strike × 100 ≤ your budget (default $1,000)
- 20–55 DTE (target ~30-45)
- Strike is 2–12% below current price (OTM put)
- Open interest ≥ 20, bid ≥ $0.05, spread ≤ 35% of mid
- Net premium after commission > $0

**Covered calls:**
- 20–55 DTE
- Strike is 2–10% above current price (OTM call)
- **Strike ≥ cost basis** (never lock in a loss if assigned)
- In buy-write mode, 100 shares must fit within $1,000 budget (disable with `--no-budget-enforce`)
- Same liquidity filters as puts

## Default watchlist

Curated list of TSX stocks under $10 that (historically) have listed options on the Montreal Exchange — includes gold miners, base metals, oil & gas, BlackBerry, cannabis, and a few others. See [`config.py`](config.py) for the full list.

Names that drift above $10 are filtered out dynamically.

## Files

| File | Purpose |
|---|---|
| **`wheel.bat`** | 🚀 **One-click launcher** — runs everything, opens HTML |
| `run_all.py` | Orchestrator: runs all 5+ scans, builds mega dashboard |
| `mega_dashboard.py` | Single-page HTML builder (leaderboard, sections, search) |
| `my_positions.example.json` | Template — copy to `my_positions.json` to track holdings |
| `config.py` | All knobs: watchlist, budget, filters, ranking weights |
| `data_provider.py` | Fetches prices + option chains via yfinance |
| `scan.py` | **CSP scanner** CLI (advanced use) |
| `wheel_analyzer.py` | Finds best CSP per stock + composite ranking |
| `report_builder.py` | CSP report writer (CSV / HTML / TXT / JSON) |
| `scan_cc.py` | **CC scanner** CLI (advanced use) |
| `cc_analyzer.py` | Finds best CC per stock + composite ranking |
| `cc_report_builder.py` | CC report writer + old side-by-side dashboard |
| `run.bat` | Legacy: run just the CSP scanner |
| `run_cc.bat` | Legacy: run just the CC scanner |

## ⚠️ Important caveats

1. **Yahoo Finance option data for TSX names is often stale or wide.** Always verify quotes with your broker (NBDB) before placing an order.
2. **Only sell puts on stocks you're actually willing to own** at the strike price. If a gold miner or oil name dumps 30%, you'll be holding it.
3. **Small accounts eat commissions.** A $6.95 commission on a $15 premium is 46%. The scanner accounts for this, but you should mentally target premiums of at least $25–30 per contract to make it worthwhile.
4. **Sector concentration**: most sub-$10 TSX optionable names are miners/energy. If you wheel 2–3 of them, you're essentially all-in on commodities. Diversify with intent.
5. **Ex-dividend dates**: Canadian dividend-paying stocks can trigger early assignment on ITM calls. Watch the calendar.
6. **Not financial advice.** Educational tool only.

## Example workflow

### Phase 1 — Sell the put
1. Run `run_cc.bat --buy-write --run-puts` to get both scanners + the dashboard in one shot.
2. Open `output/wheel_dashboard.html`.
3. From the **Puts** table, pick a candidate whose stock **you'd be happy to own at the strike**.
4. In NBDB, pull up the options chain for that ticker on the Montreal Exchange.
5. **Verify** the bid, ask, open interest, and strike match roughly what the scanner shows.
6. Place a **Sell to Open PUT** limit order at the mid price (or slightly better).
7. If filled: log the trade (ticker, strike, expiration, premium) and mark your calendar.

### Phase 2 — If assigned, sell the call
8. On assignment, you own 100 shares. Note your **cost basis** (strike – premium received).
9. Run:
   ```bat
   run_cc.bat --positions TICKER.TO:COST_BASIS:100
   ```
   e.g. `run_cc.bat --positions BTO.TO:4.85:100`
10. Open `output/cc_candidates.html`, pick a strike **at or above your cost basis**.
11. Verify quote with NBDB → place a **Sell to Open CALL** limit order.
12. If not called: keep the premium, sell another call next cycle.
13. If called away: you locked in a profit → back to Phase 1.

## Example CC output (per candidate)

```
#1  [Score 84.10]  BTO.TO — B2Gold Corp  (position)
    Position:         100 shares @ $4.85 cost basis
    Current price:    $5.42 CAD
    Sell call:        $5.50 strike, exp 2026-08-15 (31 DTE)
    Bid/Ask/Mid:      $0.15 / $0.20 / $0.17   (spread 29.4%)
    OI / Volume / IV: 218 / 8 / 46.1%
    Premium (gross):  $17.50 CAD
    Premium (net):    $10.55 CAD (after $6.95 comm)
    Static yield:     0.22% period   2.6% annualized (premium only)
    If-called yield:  13.62% period 160.4% annualized (premium + cap gain)
    Max profit:       $75.55 CAD if called at $5.50
    Downside prot:    1.9% (premium as % of stock price)
    Upside cap:       $5.50 (1.5% above current)
    Breakeven:        $4.74 (cost basis - net premium/100)
```

## Next enhancements (ideas)
- [x] ~~Add a covered-call scanner for the post-assignment phase~~ ✅ done
- [ ] Pull IV rank / IV percentile for better timing
- [ ] Integrate ex-dividend calendar warnings (early-assignment risk on ITM calls)
- [ ] Add earnings-date filter (avoid selling options through earnings)
- [ ] Persistent trade log so the scanner knows your current open positions
- [ ] Rolling suggestions (when to roll an ITM call vs. accept assignment)
- [ ] Discord/Teams webhook for daily top-3 candidates
- [ ] Pull directly from Montreal Exchange for more accurate CAD option data
