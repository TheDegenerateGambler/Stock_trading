---
Project:        wheel_scanner
Doc:            GLOSSARY.md
Owner:          The Gambler
Classification: Public
Last updated:   2026-11-23
---

# Glossary - wheel_scanner

| Term | Meaning |
|------|---------|
| **The Wheel** | Sell a cash-secured put; if assigned, sell covered calls above cost basis; repeat. |
| **CSP (cash-secured put)** | Selling a put while holding enough cash to buy the shares if assigned. |
| **CC (covered call)** | Selling a call against 100 shares you own. |
| **Buy-write** | Buying shares and selling a covered call in one combined trade. |
| **Assignment** | Being obliged to buy (put) or sell (call) the shares when the option is exercised. |
| **Cost basis** | Your average purchase price per share; CC strikes stay at/above it to avoid locking in a loss. |
| **Annualised premium yield** | Option premium scaled to a yearly rate for comparison across expiries. |
| **DTE** | Days to expiration. |
| **OI / liquidity** | Open interest / how easily a contract can be traded. |
| **Strike** | The option's exercise price; affordability requires `strike * 100 <= budget`. |
| **Contract size** | Shares per equity option contract (100). |
| **NBDB** | National Bank Direct Brokerage - the broker whose fee model is used. |
| **TSX / `.TO`** | Toronto Stock Exchange; yfinance suffix for TSX-listed names. |
| **MX (Montreal Exchange)** | Where Canadian equity options are listed. |
| **FX / USD-CAD** | Currency conversion used to compare US names in CAD terms (`--usd-cad`). |
| **Watchlist** | Configured universes: cheap TSX names, TSX blue-chips, liquid US names. |
| **Mega dashboard** | The single combined HTML page with the Top-10 leaderboard and all sections. |
| **my_positions.json** | Optional local file of your own holdings (personal financial data; git-ignored). |

---
Related: ARCHITECTURE.md, CONFIGURATION.md, MODULES.md
