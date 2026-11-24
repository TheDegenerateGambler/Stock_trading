"""
Report builder: writes ranked wheel candidates to CSV, HTML, and a
human-readable TXT summary.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Iterable

import pandas as pd

from config import (
    ACCOUNT_BUDGET_CAD,
    OPTION_COMMISSION_PER_CONTRACT,
    OUTPUT_CSV,
    OUTPUT_DIR,
    OUTPUT_HTML,
    OUTPUT_TXT,
)
from wheel_analyzer import WheelCandidate


def _ensure_output_dir() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(here, OUTPUT_DIR)
    os.makedirs(out, exist_ok=True)
    return out


def build_dataframe(candidates: Iterable[WheelCandidate]) -> pd.DataFrame:
    rows = [c.to_row() for c in candidates]
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    cols = [
        "score", "ticker", "name", "currency", "weekly",
        "stock_price", "strike", "otm_pct",
        "expiration", "dte", "bid", "ask", "mid", "spread_pct",
        "open_interest", "volume", "implied_vol",
        "collateral_cad", "premium_cad", "net_premium_cad",
        "collateral_in_cad", "net_premium_in_cad",
        "net_yield_pct", "annualized_yield_pct",
        "breakeven", "downside_cushion_pct", "notes",
    ]
    cols = [c for c in cols if c in df.columns]
    return df[cols]


def write_reports(candidates: list[WheelCandidate]) -> dict:
    out_dir = _ensure_output_dir()
    df = build_dataframe(candidates)

    csv_path = os.path.join(out_dir, OUTPUT_CSV)
    html_path = os.path.join(out_dir, OUTPUT_HTML)
    txt_path = os.path.join(out_dir, OUTPUT_TXT)
    json_path = os.path.join(out_dir, "wheel_candidates.json")

    if df.empty:
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("No wheel candidates found. Try relaxing filters in config.py.\n")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write("<html><body><h1>No wheel candidates found.</h1></body></html>")
        return {"csv": csv_path, "html": html_path, "txt": txt_path, "json": json_path}

    df.to_csv(csv_path, index=False)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump([c.to_row() for c in candidates], f, indent=2, default=str)

    # ---------- Text report ----------
    lines = []
    lines.append("=" * 100)
    lines.append("CANADIAN WHEEL SCANNER — CASH-SECURED PUT CANDIDATES")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Budget: ${ACCOUNT_BUDGET_CAD:,.2f} CAD   "
                 f"Option commission: ${OPTION_COMMISSION_PER_CONTRACT:.2f}/contract (NBDB)")
    lines.append("=" * 100)
    lines.append("")

    for i, c in enumerate(candidates, 1):
        cur = getattr(c, "currency", "CAD")
        weekly_tag = " (WEEKLY)" if getattr(c, "weekly", False) else ""
        lines.append(f"#{i}  [Score {c.score:5.2f}]  {c.ticker}  —  {c.name}{weekly_tag}")
        lines.append(f"    Stock price:      ${c.stock_price:.2f} {cur}")
        lines.append(f"    Sell put:         ${c.strike:.2f} strike, exp {c.expiration} ({c.dte} DTE)")
        lines.append(f"    Bid/Ask/Mid:      ${c.bid:.2f} / ${c.ask:.2f} / ${c.mid:.2f}   "
                     f"(spread {c.spread_pct*100:.1f}%)")
        lines.append(f"    OI / Volume / IV: {c.open_interest} / {c.volume} / {c.implied_vol*100:.1f}%")
        collateral_in_cad = getattr(c, "collateral_in_cad", c.collateral_cad)
        net_prem_in_cad = getattr(c, "net_premium_in_cad", c.net_premium_cad)
        if cur == "CAD":
            lines.append(f"    Collateral req:   ${c.collateral_cad:,.2f} CAD  "
                         f"({collateral_in_cad/ACCOUNT_BUDGET_CAD*100:.0f}% of budget)")
        else:
            lines.append(f"    Collateral req:   ${c.collateral_cad:,.2f} {cur}  "
                         f"(≈ ${collateral_in_cad:,.2f} CAD, "
                         f"{collateral_in_cad/ACCOUNT_BUDGET_CAD*100:.0f}% of budget)")
        lines.append(f"    Premium (gross):  ${c.premium_cad:.2f} {cur}")
        commission_note = "$6.95 CAD" if cur == "CAD" else "$1.25 USD"
        lines.append(f"    Premium (net):    ${c.net_premium_cad:.2f} {cur} "
                     f"(≈ ${net_prem_in_cad:.2f} CAD, after {commission_note} comm)")
        lines.append(f"    Yield:            {c.net_yield_pct*100:.2f}% period   "
                     f"{c.annualized_yield_pct*100:.1f}% annualized")
        lines.append(f"    Breakeven:        ${c.breakeven:.2f} {cur}   "
                     f"Downside cushion: {c.downside_cushion_pct*100:.1f}%")
        lines.append(f"    OTM:              {c.otm_pct*100:.1f}% below spot")
        if c.notes:
            lines.append(f"    Notes:            {c.notes}")
        lines.append("")

    lines.append("-" * 100)
    lines.append("Reminders:")
    lines.append("  * Verify option quotes with your broker before trading — Yahoo data can be stale/wide.")
    lines.append("  * Only sell puts on stocks you're willing to OWN at the strike price.")
    lines.append("  * If assigned, next step is to sell covered calls at or above your cost basis.")
    lines.append("  * Watch for ex-dividend dates (early assignment risk on ITM calls).")
    lines.append("  * Not financial advice.")
    lines.append("")

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    # ---------- HTML report ----------
    html = _build_html(df)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    return {"csv": csv_path, "html": html_path, "txt": txt_path, "json": json_path}


def _build_html(df: pd.DataFrame) -> str:
    # Pretty formatting for the HTML table
    fmt_df = df.copy()
    pct_cols = ["otm_pct", "spread_pct", "net_yield_pct", "annualized_yield_pct", "downside_cushion_pct", "implied_vol"]
    money_cols = ["stock_price", "strike", "bid", "ask", "mid", "collateral_cad", "premium_cad", "net_premium_cad", "breakeven"]

    for col in pct_cols:
        if col in fmt_df.columns:
            fmt_df[col] = fmt_df[col].apply(lambda v: f"{v*100:.2f}%" if pd.notna(v) else "")
    for col in money_cols:
        if col in fmt_df.columns:
            fmt_df[col] = fmt_df[col].apply(lambda v: f"${v:,.2f}" if pd.notna(v) else "")

    table_html = fmt_df.to_html(index=False, classes="wheel", border=0, escape=False)

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Canadian Wheel Scanner</title>
<style>
body {{ font-family: -apple-system, Segoe UI, Arial, sans-serif; margin: 24px; background: #fafafa; color: #222; }}
h1 {{ margin-bottom: 4px; }}
.sub {{ color: #666; margin-bottom: 20px; }}
table.wheel {{ border-collapse: collapse; width: 100%; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
table.wheel th, table.wheel td {{ padding: 8px 10px; border-bottom: 1px solid #eee; text-align: right; font-size: 13px; }}
table.wheel th {{ background: #1f2937; color: white; text-align: right; position: sticky; top: 0; }}
table.wheel td:nth-child(2), table.wheel td:nth-child(3) {{ text-align: left; }}
table.wheel tr:hover {{ background: #f3f4f6; }}
.footer {{ margin-top: 20px; color: #666; font-size: 12px; }}
</style>
</head>
<body>
<h1>🇨🇦 Canadian Wheel Scanner — Cash-Secured Put Candidates</h1>
<div class="sub">
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} &nbsp;|&nbsp;
Budget: ${ACCOUNT_BUDGET_CAD:,.2f} CAD &nbsp;|&nbsp;
Option commission: ${OPTION_COMMISSION_PER_CONTRACT:.2f}/contract (NBDB)
</div>
{table_html}
<div class="footer">
Data via Yahoo Finance (may be delayed). Verify all quotes with your broker. Not financial advice.
</div>
</body>
</html>"""