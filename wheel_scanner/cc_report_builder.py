"""
Report builder for Covered Call candidates.
Writes CSV / HTML / TXT / JSON, and a combined wheel dashboard (puts+calls).
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Iterable

import pandas as pd

from cc_analyzer import CCCandidate
from config import (
    ACCOUNT_BUDGET_CAD,
    CC_OUTPUT_CSV,
    CC_OUTPUT_HTML,
    CC_OUTPUT_TXT,
    DASHBOARD_HTML,
    OPTION_COMMISSION_PER_CONTRACT,
    OUTPUT_DIR,
)


def _ensure_output_dir() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(here, OUTPUT_DIR)
    os.makedirs(out, exist_ok=True)
    return out


def build_cc_dataframe(candidates: Iterable[CCCandidate]) -> pd.DataFrame:
    rows = [c.to_row() for c in candidates]
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    cols = [
        "score", "ticker", "name", "currency", "weekly", "mode",
        "stock_price", "cost_basis", "shares_held",
        "strike", "otm_pct",
        "expiration", "dte",
        "bid", "ask", "mid", "spread_pct",
        "open_interest", "volume", "implied_vol",
        "premium_cad", "net_premium_cad",
        "premium_in_cad", "net_premium_in_cad",
        "static_yield_pct", "static_yield_ann_pct",
        "if_called_profit_cad", "if_called_profit_in_cad",
        "if_called_yield_pct", "if_called_yield_ann_pct",
        "downside_protection_pct", "upside_room_pct",
        "notes",
    ]
    cols = [c for c in cols if c in df.columns]
    return df[cols]


def _fmt_df(df: pd.DataFrame, pct_cols: list, money_cols: list) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    for col in pct_cols:
        if col in df.columns:
            df[col] = df[col].apply(lambda v: f"{v*100:.2f}%" if pd.notna(v) else "")
    for col in money_cols:
        if col in df.columns:
            df[col] = df[col].apply(lambda v: f"${v:,.2f}" if pd.notna(v) else "")
    return df


CC_PCT_COLS = [
    "otm_pct", "spread_pct", "implied_vol",
    "static_yield_pct", "static_yield_ann_pct",
    "if_called_yield_pct", "if_called_yield_ann_pct",
    "downside_protection_pct", "upside_room_pct",
]
CC_MONEY_COLS = [
    "stock_price", "cost_basis", "strike", "bid", "ask", "mid",
    "premium_cad", "net_premium_cad", "if_called_profit_cad",
]

PUT_PCT_COLS = [
    "otm_pct", "spread_pct", "net_yield_pct",
    "annualized_yield_pct", "downside_cushion_pct", "implied_vol",
]
PUT_MONEY_COLS = [
    "stock_price", "strike", "bid", "ask", "mid",
    "collateral_cad", "premium_cad", "net_premium_cad", "breakeven",
]


def write_cc_reports(candidates: list[CCCandidate]) -> dict:
    out_dir = _ensure_output_dir()
    df = build_cc_dataframe(candidates)

    csv_path = os.path.join(out_dir, CC_OUTPUT_CSV)
    html_path = os.path.join(out_dir, CC_OUTPUT_HTML)
    txt_path = os.path.join(out_dir, CC_OUTPUT_TXT)
    json_path = os.path.join(out_dir, "cc_candidates.json")

    if df.empty:
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("No covered-call candidates found. Try relaxing filters in config.py.\n")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write("<html><body><h1>No covered-call candidates found.</h1></body></html>")
        return {"csv": csv_path, "html": html_path, "txt": txt_path, "json": json_path}

    df.to_csv(csv_path, index=False)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump([c.to_row() for c in candidates], f, indent=2, default=str)

    # ---------- TXT report ----------
    lines = []
    lines.append("=" * 100)
    lines.append("CANADIAN WHEEL SCANNER — COVERED CALL CANDIDATES")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Budget: ${ACCOUNT_BUDGET_CAD:,.2f} CAD   "
                 f"Option commission: ${OPTION_COMMISSION_PER_CONTRACT:.2f}/contract (NBDB)")
    lines.append("=" * 100)
    lines.append("")

    for i, c in enumerate(candidates, 1):
        lines.append(f"#{i}  [Score {c.score:5.2f}]  {c.ticker}  —  {c.name}  ({c.mode})")
        lines.append(f"    Position:         {c.shares_held} shares @ ${c.cost_basis:.2f} cost basis")
        lines.append(f"    Current price:    ${c.stock_price:.2f} CAD")
        lines.append(f"    Sell call:        ${c.strike:.2f} strike, exp {c.expiration} ({c.dte} DTE)")
        lines.append(f"    Bid/Ask/Mid:      ${c.bid:.2f} / ${c.ask:.2f} / ${c.mid:.2f}   "
                     f"(spread {c.spread_pct*100:.1f}%)")
        lines.append(f"    OI / Volume / IV: {c.open_interest} / {c.volume} / {c.implied_vol*100:.1f}%")
        lines.append(f"    Premium (gross):  ${c.premium_cad:.2f} CAD")
        lines.append(f"    Premium (net):    ${c.net_premium_cad:.2f} CAD (after ${OPTION_COMMISSION_PER_CONTRACT:.2f} comm)")
        lines.append(f"    Static yield:     {c.static_yield_pct*100:.2f}% period   "
                     f"{c.static_yield_ann_pct*100:.1f}% annualized (premium only)")
        lines.append(f"    If-called yield:  {c.if_called_yield_pct*100:.2f}% period   "
                     f"{c.if_called_yield_ann_pct*100:.1f}% annualized (premium + cap gain)")
        lines.append(f"    Max profit:       ${c.if_called_profit_cad:.2f} CAD if called at ${c.strike:.2f}")
        lines.append(f"    Downside prot:    {c.downside_protection_pct*100:.2f}% (premium as % of stock price)")
        lines.append(f"    Upside cap:       ${c.strike:.2f} ({c.upside_room_pct*100:.1f}% above spot)")
        breakeven = c.cost_basis - (c.net_premium_cad / 100.0)
        lines.append(f"    Breakeven:        ${breakeven:.2f} (cost basis - net premium/100)")
        if c.notes:
            lines.append(f"    Notes:            {c.notes}")
        lines.append("")

    lines.append("-" * 100)
    lines.append("Reminders:")
    lines.append("  * Only sell calls when you already own (or are buying) the 100 shares.")
    lines.append("  * Strike is set at or above cost basis so assignment locks in a profit, not a loss.")
    lines.append("  * Watch ex-dividend dates — ITM calls can be assigned early to capture the dividend.")
    lines.append("  * Verify quotes with NBDB before placing the order. Not financial advice.")
    lines.append("")

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    # ---------- HTML report ----------
    html = _build_cc_html(df)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    return {"csv": csv_path, "html": html_path, "txt": txt_path, "json": json_path}


def _build_cc_html(df: pd.DataFrame) -> str:
    fmt_df = _fmt_df(df, CC_PCT_COLS, CC_MONEY_COLS)
    table_html = fmt_df.to_html(index=False, classes="wheel", border=0, escape=False)

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Canadian Wheel Scanner — Covered Calls</title>
<style>
body {{ font-family: -apple-system, Segoe UI, Arial, sans-serif; margin: 24px; background: #fafafa; color: #222; }}
h1 {{ margin-bottom: 4px; }}
.sub {{ color: #666; margin-bottom: 20px; }}
table.wheel {{ border-collapse: collapse; width: 100%; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
table.wheel th, table.wheel td {{ padding: 8px 10px; border-bottom: 1px solid #eee; text-align: right; font-size: 13px; }}
table.wheel th {{ background: #065f46; color: white; text-align: right; position: sticky; top: 0; }}
table.wheel td:nth-child(2), table.wheel td:nth-child(3), table.wheel td:nth-child(4) {{ text-align: left; }}
table.wheel tr:hover {{ background: #f3f4f6; }}
.footer {{ margin-top: 20px; color: #666; font-size: 12px; }}
</style>
</head>
<body>
<h1>🇨🇦 Canadian Wheel Scanner — Covered Call Candidates</h1>
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


# ---------------------------------------------------------------------------
# Combined wheel dashboard: puts + calls side by side
# ---------------------------------------------------------------------------
def write_dashboard(put_candidates, cc_candidates) -> str:
    """
    Build a combined HTML page with top CSPs and top CCs.
    put_candidates: list of WheelCandidate (from wheel_analyzer) or None
    cc_candidates:  list of CCCandidate (from cc_analyzer) or None
    """
    from report_builder import build_dataframe as build_put_df

    out_dir = _ensure_output_dir()
    dash_path = os.path.join(out_dir, DASHBOARD_HTML)

    put_df = build_put_df(put_candidates) if put_candidates else pd.DataFrame()
    cc_df = build_cc_dataframe(cc_candidates) if cc_candidates else pd.DataFrame()

    put_fmt = _fmt_df(put_df, PUT_PCT_COLS, PUT_MONEY_COLS)
    cc_fmt = _fmt_df(cc_df, CC_PCT_COLS, CC_MONEY_COLS)

    put_table = (
        put_fmt.to_html(index=False, classes="wheel", border=0, escape=False)
        if not put_fmt.empty
        else "<p><em>No cash-secured put candidates found.</em></p>"
    )
    cc_table = (
        cc_fmt.to_html(index=False, classes="wheel", border=0, escape=False)
        if not cc_fmt.empty
        else "<p><em>No covered-call candidates found.</em></p>"
    )

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Canadian Wheel Dashboard</title>
<style>
body {{ font-family: -apple-system, Segoe UI, Arial, sans-serif; margin: 24px; background: #fafafa; color: #222; }}
h1 {{ margin-bottom: 4px; }}
h2 {{ margin-top: 32px; padding-bottom: 6px; border-bottom: 2px solid #ddd; }}
h2.puts {{ color: #1f2937; }}
h2.calls {{ color: #065f46; }}
.sub {{ color: #666; margin-bottom: 20px; }}
table.wheel {{ border-collapse: collapse; width: 100%; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.08); margin-bottom: 24px; }}
table.wheel th, table.wheel td {{ padding: 7px 9px; border-bottom: 1px solid #eee; text-align: right; font-size: 12px; }}
table.wheel th {{ color: white; text-align: right; position: sticky; top: 0; }}
h2.puts + table.wheel th {{ background: #1f2937; }}
h2.calls + table.wheel th {{ background: #065f46; }}
table.wheel td:nth-child(2), table.wheel td:nth-child(3), table.wheel td:nth-child(4) {{ text-align: left; }}
table.wheel tr:hover {{ background: #f3f4f6; }}
.footer {{ margin-top: 20px; color: #666; font-size: 12px; }}
.legend {{ background: #fff8e1; border-left: 4px solid #f59e0b; padding: 10px 14px; margin: 12px 0 24px; font-size: 13px; }}
</style>
</head>
<body>
<h1>🇨🇦 Canadian Wheel Dashboard</h1>
<div class="sub">
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} &nbsp;|&nbsp;
Budget: ${ACCOUNT_BUDGET_CAD:,.2f} CAD &nbsp;|&nbsp;
Option commission: ${OPTION_COMMISSION_PER_CONTRACT:.2f}/contract (NBDB)
</div>
<div class="legend">
<strong>Wheel workflow:</strong>
Start with a <em>cash-secured put</em> from the top table. If assigned (stock drops below strike at expiry),
you own 100 shares — switch to the <em>covered call</em> table with your cost basis to keep earning premium.
</div>

<h2 class="puts">🛡️ Cash-Secured Put Candidates (Wheel Step 1)</h2>
{put_table}

<h2 class="calls">📞 Covered Call Candidates (Wheel Step 2)</h2>
{cc_table}

<div class="footer">
Data via Yahoo Finance (may be delayed). Verify all quotes with your broker. Not financial advice.
</div>
</body>
</html>"""

    with open(dash_path, "w", encoding="utf-8") as f:
        f.write(html)
    return dash_path
