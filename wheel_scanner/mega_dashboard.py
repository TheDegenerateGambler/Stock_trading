"""
Mega wheel dashboard — a single HTML page with:
  - Header (budget, FX, timestamp, run duration)
  - Combined Top-10 leaderboard across all sections
  - One collapsible section per scan (puts + calls, monthly + weekly)
  - Live search box that filters all tables client-side
  - Colored score badges

The user opens this HTML file and sees everything in one place.
"""
from __future__ import annotations

import html
import os
from dataclasses import asdict
from datetime import datetime
from typing import Any

from cc_analyzer import CCCandidate
from config import DASHBOARD_HTML, OUTPUT_DIR
from wheel_analyzer import WheelCandidate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _pct(v: float | None) -> str:
    if v is None:
        return ""
    return f"{v * 100:.1f}%"


def _usd(v: float | None, cur: str = "") -> str:
    if v is None:
        return ""
    prefix = f"${v:,.2f}"
    return f"{prefix} {cur}".strip() if cur else prefix


def _score_class(score: float) -> str:
    if score >= 70:
        return "score-hi"
    if score >= 45:
        return "score-mid"
    return "score-lo"


def _row_type_badge(kind: str) -> str:
    color = {
        "PUT": "#1f2937",
        "CALL": "#065f46",
    }.get(kind, "#6b7280")
    return (f'<span class="badge" style="background:{color}">'
            f'{kind}</span>')


def _mode_badge(mode: str) -> str:
    color = {
        "monthly": "#4b5563",
        "weekly":  "#b45309",
    }.get(mode, "#6b7280")
    return (f'<span class="badge" style="background:{color}">'
            f'{mode}</span>')


# ---------------------------------------------------------------------------
# Row renderers
# ---------------------------------------------------------------------------
def _put_row(c: WheelCandidate) -> str:
    cur = c.currency
    weekly = getattr(c, "weekly", False)
    mode_lbl = "weekly" if weekly else "monthly"
    return f"""
      <tr data-ticker="{html.escape(c.ticker)}"
          data-score="{c.score}"
          data-yield="{c.annualized_yield_pct}"
          data-currency="{cur}"
          data-mode="{mode_lbl}"
          data-kind="PUT">
        <td class="score-cell"><span class="score {_score_class(c.score)}">{c.score:.1f}</span></td>
        <td>{_row_type_badge("PUT")} {_mode_badge(mode_lbl)}</td>
        <td><strong>{html.escape(c.ticker)}</strong><br><span class="tiny">{html.escape(c.name)}</span></td>
        <td>{cur}</td>
        <td>{_usd(c.stock_price)}</td>
        <td>{_usd(c.strike)} <span class="tiny">{_pct(c.otm_pct)} OTM</span></td>
        <td>{c.expiration}<br><span class="tiny">{c.dte}d</span></td>
        <td>{_usd(c.bid)} / {_usd(c.ask)}<br><span class="tiny">spread {_pct(c.spread_pct)}</span></td>
        <td>OI {c.open_interest}<br><span class="tiny">IV {_pct(c.implied_vol)}</span></td>
        <td>{_usd(c.collateral_in_cad)} CAD-eq<br><span class="tiny">{_usd(c.collateral_cad)} {cur}</span></td>
        <td>{_usd(c.net_premium_in_cad)} CAD-eq<br><span class="tiny">{_usd(c.net_premium_cad)} {cur} net</span></td>
        <td><strong>{_pct(c.annualized_yield_pct)}</strong><br><span class="tiny">{_pct(c.net_yield_pct)} period</span></td>
        <td>{_usd(c.breakeven)}<br><span class="tiny">{_pct(c.downside_cushion_pct)} cushion</span></td>
        <td class="notes">{html.escape(c.notes)}</td>
      </tr>"""


def _cc_row(c: CCCandidate) -> str:
    cur = getattr(c, "currency", "CAD")
    weekly = getattr(c, "weekly", False)
    mode_lbl = "weekly" if weekly else "monthly"
    breakeven = c.cost_basis - (c.net_premium_cad / 100.0)
    return f"""
      <tr data-ticker="{html.escape(c.ticker)}"
          data-score="{c.score}"
          data-yield="{c.if_called_yield_ann_pct}"
          data-currency="{cur}"
          data-mode="{mode_lbl}"
          data-kind="CALL">
        <td class="score-cell"><span class="score {_score_class(c.score)}">{c.score:.1f}</span></td>
        <td>{_row_type_badge("CALL")} {_mode_badge(mode_lbl)}<br><span class="tiny">{html.escape(c.mode)}</span></td>
        <td><strong>{html.escape(c.ticker)}</strong><br><span class="tiny">{html.escape(c.name)}</span></td>
        <td>{cur}</td>
        <td>{_usd(c.stock_price)}<br><span class="tiny">basis {_usd(c.cost_basis)}</span></td>
        <td>{_usd(c.strike)} <span class="tiny">{_pct(c.otm_pct)} above</span></td>
        <td>{c.expiration}<br><span class="tiny">{c.dte}d</span></td>
        <td>{_usd(c.bid)} / {_usd(c.ask)}<br><span class="tiny">spread {_pct(c.spread_pct)}</span></td>
        <td>OI {c.open_interest}<br><span class="tiny">IV {_pct(c.implied_vol)}</span></td>
        <td>{_usd(c.if_called_profit_cad)} {cur}<br><span class="tiny">max if called</span></td>
        <td>{_usd(c.net_premium_cad)} {cur} net<br><span class="tiny">gross {_usd(c.premium_cad)}</span></td>
        <td><strong>{_pct(c.if_called_yield_ann_pct)}</strong><br><span class="tiny">if-called ann</span></td>
        <td>{_usd(breakeven)}<br><span class="tiny">{_pct(c.downside_protection_pct)} prot</span></td>
        <td class="notes">{html.escape(c.notes)}</td>
      </tr>"""


PUT_HEAD = (
    "<tr>"
    "<th>Score</th><th>Type</th><th>Ticker</th><th>Cur</th>"
    "<th>Spot</th><th>Strike</th><th>Expiration</th>"
    "<th>Bid/Ask</th><th>Liquidity</th>"
    "<th>Collateral</th><th>Premium</th><th>Ann Yield</th>"
    "<th>Breakeven</th><th>Notes</th>"
    "</tr>"
)

CC_HEAD = (
    "<tr>"
    "<th>Score</th><th>Type</th><th>Ticker</th><th>Cur</th>"
    "<th>Spot / Basis</th><th>Strike</th><th>Expiration</th>"
    "<th>Bid/Ask</th><th>Liquidity</th>"
    "<th>Max Profit</th><th>Premium</th><th>If-Called Ann</th>"
    "<th>Breakeven</th><th>Notes</th>"
    "</tr>"
)


def _render_section(title: str, kind: str, items: list, error: str | None) -> str:
    slug = title.replace(" ", "-").replace("/", "-").lower()
    if error:
        return f"""
      <section id="{slug}">
        <h2>{html.escape(title)}</h2>
        <div class="error-banner">⚠️ This section failed: <code>{html.escape(error)}</code></div>
      </section>"""
    if not items:
        return f"""
      <section id="{slug}">
        <h2>{html.escape(title)}</h2>
        <p class="empty">No candidates matched. Try relaxing filters in <code>config.py</code>.</p>
      </section>"""

    head = PUT_HEAD if kind == "put" else CC_HEAD
    row_fn = _put_row if kind == "put" else _cc_row
    rows_html = "".join(row_fn(x) for x in items)
    return f"""
      <section id="{slug}">
        <h2>{html.escape(title)} <span class="count">({len(items)} candidates)</span></h2>
        <div class="tbl-wrap">
          <table class="wheel">
            <thead>{head}</thead>
            <tbody>{rows_html}</tbody>
          </table>
        </div>
      </section>"""


# ---------------------------------------------------------------------------
# Combined leaderboard (top 10 across all sections)
# ---------------------------------------------------------------------------
def _render_leaderboard(all_items: list[tuple[str, Any]]) -> str:
    """all_items = list of (section_title, candidate). Sort by score desc, top 10."""
    if not all_items:
        return ""
    # Sort by score
    sorted_items = sorted(all_items, key=lambda x: x[1].score, reverse=True)[:10]

    rows = []
    for section, c in sorted_items:
        # Detect kind by class
        is_cc = isinstance(c, CCCandidate)
        kind = "CALL" if is_cc else "PUT"
        cur = getattr(c, "currency", "CAD")
        weekly = getattr(c, "weekly", False)
        mode = "weekly" if weekly else "monthly"
        if is_cc:
            yield_str = _pct(c.if_called_yield_ann_pct) + " if-called"
            premium_str = _usd(c.net_premium_cad) + " " + cur
            desc = f"{_usd(c.strike)} {cur} call {c.expiration}"
        else:
            yield_str = _pct(c.annualized_yield_pct) + " ann"
            premium_str = _usd(c.net_premium_in_cad) + " CAD-eq"
            desc = f"{_usd(c.strike)} {cur} put {c.expiration}"
        rows.append(f"""
          <tr>
            <td class="score-cell"><span class="score {_score_class(c.score)}">{c.score:.1f}</span></td>
            <td>{_row_type_badge(kind)} {_mode_badge(mode)}</td>
            <td><strong>{html.escape(c.ticker)}</strong> <span class="tiny">({cur})</span></td>
            <td>{desc}</td>
            <td>{premium_str}</td>
            <td><strong>{yield_str}</strong></td>
            <td class="tiny">{html.escape(section)}</td>
          </tr>""")
    return f"""
      <section id="leaderboard">
        <h2>🏆 Top 10 Overall <span class="count">(ranked across all sections)</span></h2>
        <div class="tbl-wrap">
          <table class="wheel">
            <thead>
              <tr><th>Score</th><th>Type</th><th>Ticker</th><th>Trade</th>
                  <th>Premium</th><th>Yield</th><th>Section</th></tr>
            </thead>
            <tbody>{''.join(rows)}</tbody>
          </table>
        </div>
      </section>"""


# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------
def _ensure_output_dir() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(here, OUTPUT_DIR)
    os.makedirs(out, exist_ok=True)
    return out


def build_mega_dashboard(
    put_sections: list[tuple[str, list[WheelCandidate], str | None]],
    cc_sections: list[tuple[str, list[CCCandidate], str | None]],
    started: datetime,
    finished: datetime,
    budget_cad: float,
    usd_cad: float,
) -> str:
    """Build the single HTML dashboard and return its path."""
    out_dir = _ensure_output_dir()
    dash_path = os.path.join(out_dir, DASHBOARD_HTML)

    # Combined leaderboard input: (section_title, candidate)
    all_items: list[tuple[str, Any]] = []
    for title, items, _err in put_sections:
        for c in items:
            all_items.append((title, c))
    for title, items, _err in cc_sections:
        for c in items:
            all_items.append((title, c))

    leaderboard_html = _render_leaderboard(all_items)

    # Nav links
    nav_links = ['<a href="#leaderboard">🏆 Top 10</a>']
    section_htmls = []

    for title, items, err in put_sections:
        slug = title.replace(" ", "-").replace("/", "-").lower()
        nav_links.append(f'<a href="#{slug}">{html.escape(title)}</a>')
        section_htmls.append(_render_section(title, "put", items, err))

    for title, items, err in cc_sections:
        slug = title.replace(" ", "-").replace("/", "-").lower()
        nav_links.append(f'<a href="#{slug}">{html.escape(title)}</a>')
        section_htmls.append(_render_section(title, "cc", items, err))

    duration = (finished - started).total_seconds()

    total_candidates = sum(len(x[1]) for x in put_sections) + sum(len(x[1]) for x in cc_sections)

    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>🇨🇦 Wheel Dashboard</title>
<style>
  :root {{
    --bg: #f7f7f9;
    --panel: #ffffff;
    --ink: #1f2937;
    --muted: #6b7280;
    --border: #e5e7eb;
    --hi: #16a34a;
    --mid: #f59e0b;
    --lo: #9ca3af;
    --accent: #2563eb;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    font-family: -apple-system, "Segoe UI", Roboto, Arial, sans-serif;
    background: var(--bg);
    color: var(--ink);
  }}
  header.top {{
    background: linear-gradient(90deg, #1f2937 0%, #065f46 100%);
    color: white;
    padding: 20px 28px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.08);
  }}
  header.top h1 {{ margin: 0 0 6px; font-size: 24px; }}
  header.top .stats {{
    display: flex; flex-wrap: wrap; gap: 20px; margin-top: 8px;
    font-size: 13px; opacity: 0.95;
  }}
  header.top .stats span b {{ color: #a7f3d0; }}
  nav.sticky {{
    position: sticky; top: 0; z-index: 100;
    background: white; border-bottom: 1px solid var(--border);
    padding: 10px 20px; overflow-x: auto; white-space: nowrap;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  }}
  nav.sticky a {{
    color: var(--accent); text-decoration: none; font-size: 13px;
    padding: 6px 10px; margin-right: 4px; border-radius: 6px;
    display: inline-block;
  }}
  nav.sticky a:hover {{ background: #eff6ff; }}
  .search-bar {{
    padding: 12px 20px; background: white; border-bottom: 1px solid var(--border);
    position: sticky; top: 43px; z-index: 90;
  }}
  .search-bar input {{
    width: 100%; max-width: 600px; padding: 9px 12px;
    border: 1px solid var(--border); border-radius: 8px;
    font-size: 14px; outline: none;
  }}
  .search-bar input:focus {{ border-color: var(--accent); }}
  main {{ padding: 20px 28px 60px; max-width: 1600px; margin: 0 auto; }}
  section {{
    background: var(--panel); border-radius: 10px;
    padding: 18px 20px; margin-bottom: 22px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  }}
  section h2 {{ margin: 0 0 12px; font-size: 18px; }}
  section h2 .count {{ color: var(--muted); font-weight: normal; font-size: 13px; }}
  .tbl-wrap {{ overflow-x: auto; }}
  table.wheel {{
    width: 100%; border-collapse: collapse; font-size: 12.5px;
  }}
  table.wheel th {{
    background: #f3f4f6; color: #1f2937;
    text-align: left; padding: 8px 10px;
    border-bottom: 2px solid var(--border);
    font-weight: 600; white-space: nowrap;
  }}
  table.wheel td {{
    padding: 8px 10px; border-bottom: 1px solid var(--border);
    vertical-align: top;
  }}
  table.wheel tr:hover td {{ background: #f9fafb; }}
  .tiny {{ font-size: 11px; color: var(--muted); }}
  .notes {{ font-size: 11px; color: var(--muted); max-width: 220px; }}
  .score-cell {{ min-width: 60px; }}
  .score {{
    display: inline-block; padding: 3px 8px; border-radius: 6px;
    font-weight: bold; color: white; font-size: 12px;
  }}
  .score-hi {{ background: var(--hi); }}
  .score-mid {{ background: var(--mid); }}
  .score-lo {{ background: var(--lo); }}
  .badge {{
    display: inline-block; padding: 2px 6px; border-radius: 4px;
    color: white; font-size: 10.5px; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.4px;
    margin-right: 2px;
  }}
  .empty {{ color: var(--muted); font-style: italic; }}
  .error-banner {{
    background: #fef2f2; border-left: 4px solid #dc2626;
    padding: 10px 14px; font-size: 13px; color: #7f1d1d;
    border-radius: 6px;
  }}
  footer.foot {{
    text-align: center; color: var(--muted); font-size: 12px;
    padding: 24px; margin-top: 20px; border-top: 1px solid var(--border);
  }}
</style>
</head>
<body>

<header class="top">
  <h1>🇨🇦 Wheel Dashboard</h1>
  <div class="stats">
    <span>Generated: <b>{finished.strftime('%Y-%m-%d %H:%M:%S')}</b></span>
    <span>Duration: <b>{duration:.1f}s</b></span>
    <span>Budget: <b>${budget_cad:,.2f} CAD</b></span>
    <span>FX: <b>{usd_cad:.3f} USD/CAD</b></span>
    <span>Total candidates: <b>{total_candidates}</b></span>
  </div>
</header>

<nav class="sticky">
  {' '.join(nav_links)}
</nav>

<div class="search-bar">
  <input id="q" type="search" placeholder="🔎 Filter by ticker or notes (e.g. BTO, F, weekly, USD, div)... ">
</div>

<main>
  {leaderboard_html}
  {''.join(section_htmls)}
</main>

<footer class="foot">
  Data via Yahoo Finance (may be delayed). NBDB fees: $6.95 CAD / $1.25 USD per option contract.
  Always verify quotes with your broker before trading. Not financial advice.
</footer>

<script>
  // Live client-side filter across every table row
  const q = document.getElementById('q');
  const allRows = () => document.querySelectorAll('table.wheel tbody tr');
  q.addEventListener('input', () => {{
    const needle = q.value.trim().toLowerCase();
    allRows().forEach(row => {{
      const txt = row.textContent.toLowerCase();
      row.style.display = (!needle || txt.includes(needle)) ? '' : 'none';
    }});
  }});
</script>

</body>
</html>
"""

    with open(dash_path, "w", encoding="utf-8") as f:
        f.write(html_doc)
    return dash_path
