"""
report_builder.py — Writes HTML report, JSON dump, and console table.
"""
from __future__ import annotations
import html
import json
from pathlib import Path
from typing import Dict, List

import config

OUT = Path(config.OUTPUT_DIR)
OUT.mkdir(parents=True, exist_ok=True)


def render_console(picks, now_str, next_scan, budget, universe_size, scanned):
    lines = []
    lines.append("=" * 100)
    lines.append("  PREMARKET SCAN - " + now_str +
                 "  |  universe=" + str(universe_size) +
                 "  scanned_with_PM=" + str(scanned) +
                 "  |  " + budget)
    lines.append("=" * 100)
    lines.append("  Filters: gap_pct > " + str(config.GAP_MIN_PCT) + "%  |  " +
                 "price > $" + str(config.PRICE_MIN) + "  |  " +
                 "premarket_volume > " + format(config.PM_VOLUME_MIN, ",") + "  |  " +
                 "top " + str(config.TOP_N) + " by gap_pct DESC")
    lines.append("-" * 100)
    if not picks:
        lines.append("  No tickers passed the premarket filters.")
    else:
        header = "  {:<3}{:<8}{:>9}{:>8}{:>12}  {:<8}{:>6}  {:<12}  {}".format(
            "#", "TICKER", "PRICE", "GAP%", "PM VOL", "SENT", "SCORE", "CATALYST", "HEADLINE")
        lines.append(header)
        lines.append("  " + "-" * 96)
        for i, p in enumerate(picks, 1):
            sent_short = p.get("sentiment_label", "Neutral").replace("Somewhat-", "S-")[:7]
            head = ""
            if p.get("headlines"):
                head = p["headlines"][0].get("title", "")[:52]
            line = "  {:<3}{:<8}${:>7.2f}{:>7.2f}%{:>12,}  {:<8}{:>6.2f}  {:<12}  {}".format(
                i,
                p["ticker"],
                p["price"],
                p["gap_pct"],
                p["premarket_volume"],
                sent_short,
                p.get("sentiment_score", 0.5),
                p.get("catalyst", "Other"),
                head,
            )
            lines.append(line)
    lines.append("-" * 100)
    lines.append("  Next scan: " + next_scan)
    lines.append("=" * 100)
    text = "\n".join(lines)
    print(text)
    return text


def write_json(picks, meta):
    path = OUT / "premarket_picks.json"
    payload = {"meta": meta, "picks": picks}
    try:
        path.write_text(json.dumps(payload, indent=2, default=str))
    except Exception as e:
        print("  [report] JSON write failed: " + str(e))


_CSS = """
:root { --bg:#0b0f17; --panel:#131a26; --panel2:#1a2333; --border:#2a3548;
        --text:#e5edf7; --dim:#8a96a8; --accent:#4ea1ff;
        --pos:#26d07c; --neg:#ff5c6c; }
* { box-sizing: border-box; }
body { font-family: -apple-system, "Segoe UI", Roboto, sans-serif;
       background: var(--bg); color: var(--text); margin:0; padding:24px; }
header { display:flex; justify-content:space-between; align-items:baseline;
         flex-wrap:wrap; gap:12px; margin-bottom:16px; }
h1 { margin:0; font-size:22px; color:var(--accent); }
.meta { color:var(--dim); font-size:13px; }
.filters { background:var(--panel); padding:10px 14px; border-radius:8px;
           border:1px solid var(--border); font-size:13px; color:var(--dim);
           margin-bottom:16px; }
.filters b { color:var(--text); }
table { width:100%; border-collapse:collapse; background:var(--panel);
        border-radius:8px; overflow:hidden; border:1px solid var(--border); }
th, td { padding:10px 12px; text-align:left; border-bottom:1px solid var(--border);
         font-size:13px; vertical-align:top; }
th { background:var(--panel2); color:var(--dim); font-weight:600;
     text-transform:uppercase; font-size:11px; letter-spacing:0.5px; }
tr:last-child td { border-bottom:none; }
td.num { text-align:right; font-variant-numeric:tabular-nums; }
.ticker { font-weight:700; color:var(--accent); font-size:14px; }
.gap-pos { color:var(--pos); font-weight:600; }
.gap-neg { color:var(--neg); font-weight:600; }
.badge { display:inline-block; padding:2px 8px; border-radius:12px;
         font-size:11px; font-weight:600; }
.b-bull  { background:rgba(38,208,124,0.15); color:var(--pos); }
.b-sbull { background:rgba(38,208,124,0.08); color:var(--pos); }
.b-neu   { background:rgba(138,150,168,0.15); color:var(--dim); }
.b-sbear { background:rgba(255,92,108,0.08); color:var(--neg); }
.b-bear  { background:rgba(255,92,108,0.15); color:var(--neg); }
.cat { display:inline-block; padding:2px 8px; border-radius:6px;
       background:rgba(78,161,255,0.12); color:var(--accent);
       font-size:11px; font-weight:600; }
.cat-Offering, .cat-Legal { background:rgba(255,92,108,0.12); color:var(--neg); }
.cat-Other { background:rgba(138,150,168,0.12); color:var(--dim); }
.news { margin:6px 0 0 0; padding-left:0; list-style:none; font-size:12px; }
.news li { margin:4px 0; color:var(--dim); }
.news a { color:var(--text); text-decoration:none; }
.news a:hover { color:var(--accent); text-decoration:underline; }
.news .src { color:var(--dim); font-size:11px; margin-left:6px; }
.empty { padding:40px; text-align:center; color:var(--dim); font-size:14px;
         background:var(--panel); border:1px solid var(--border); border-radius:8px; }
footer { margin-top:16px; color:var(--dim); font-size:11px; text-align:center; }
"""


def _sent_class(label):
    return {
        "Bullish":          "b-bull",
        "Somewhat-Bullish": "b-sbull",
        "Neutral":          "b-neu",
        "Somewhat-Bearish": "b-sbear",
        "Bearish":          "b-bear",
    }.get(label, "b-neu")


def _row_html(i, p):
    gap_cls  = "gap-pos" if p["gap_pct"] >= 0 else "gap-neg"
    sent_cls = _sent_class(p.get("sentiment_label", "Neutral"))
    cat_raw  = p.get("catalyst", "Other")
    cat_safe = cat_raw.replace("/", "-").replace(" ", "-").replace("&", "and")

    heads = p.get("headlines", [])
    if heads:
        items = []
        for h in heads:
            title = html.escape(h.get("title", ""))[:180]
            url   = html.escape(h.get("url", "#"))
            src   = html.escape(h.get("source", ""))
            pub   = html.escape(h.get("published", ""))
            items.append(
                '<li><a href="' + url + '" target="_blank" rel="noopener">' + title + '</a>'
                '<span class="src">- ' + src + ' ' + pub + '</span></li>'
            )
        news_html = '<ul class="news">' + "".join(items) + '</ul>'
    else:
        news_html = '<ul class="news"><li><i>No news found.</i></li></ul>'

    parts = [
        "<tr>",
        "<td class='num'>" + str(i) + "</td>",
        "<td><span class='ticker'>" + html.escape(p["ticker"]) + "</span></td>",
        "<td class='num'>$" + "{:.2f}".format(p["price"]) + "</td>",
        "<td class='num " + gap_cls + "'>" + "{:+.2f}".format(p["gap_pct"]) + "%</td>",
        "<td class='num'>" + "{:,}".format(p["premarket_volume"]) + "</td>",
        "<td><span class='badge " + sent_cls + "'>"
        + html.escape(p.get("sentiment_label", "Neutral"))
        + "</span> <span class='meta'>"
        + "{:.2f}".format(p.get("sentiment_score", 0.5)) + "</span></td>",
        "<td><span class='cat cat-" + cat_safe + "'>" + html.escape(cat_raw) + "</span></td>",
        "<td>" + news_html + "</td>",
        "</tr>",
    ]
    return "".join(parts)


def write_html(picks, meta):
    path = OUT / "premarket_report.html"

    now_str     = meta.get("now_str", "")
    next_scan   = meta.get("next_scan", "")
    budget      = meta.get("budget", "")
    universe_sz = meta.get("universe_size", 0)
    scanned     = meta.get("scanned", 0)

    if picks:
        rows = "\n".join(_row_html(i, p) for i, p in enumerate(picks, 1))
        table_html = (
            "<table><thead><tr>"
            "<th>#</th><th>Ticker</th><th>Price</th><th>Gap %</th>"
            "<th>PM Vol</th><th>Sentiment</th><th>Catalyst</th>"
            "<th>News (top 4)</th>"
            "</tr></thead><tbody>" + rows + "</tbody></table>"
        )
    else:
        table_html = (
            '<div class="empty">'
            'No tickers passed the premarket filters this scan.<br>'
            '(Outside the 04:00-09:30 ET premarket window, yfinance returns no '
            'premarket bars - this is expected.)</div>'
        )

    filters_line = (
        "<div class='filters'><b>Filters:</b> "
        "gap_pct &gt; " + str(config.GAP_MIN_PCT) + "% &nbsp;&bull;&nbsp; "
        "price &gt; $" + str(config.PRICE_MIN) + " &nbsp;&bull;&nbsp; "
        "premarket_volume &gt; " + "{:,}".format(config.PM_VOLUME_MIN) + " &nbsp;&bull;&nbsp; "
        "top " + str(config.TOP_N) + " by <b>gap_pct DESC</b>"
        "</div>"
    )

    header_html = (
        "<header><div><h1>Premarket Scanner</h1>"
        "<div class='meta'>"
        "Scan: <b>" + html.escape(now_str) + "</b> &nbsp;&bull;&nbsp; "
        "Next scan: <b>" + html.escape(next_scan) + "</b> &nbsp;&bull;&nbsp; "
        "Universe: <b>" + str(universe_sz) + "</b> &nbsp;&bull;&nbsp; "
        "With PM data: <b>" + str(scanned) + "</b>"
        "</div></div>"
        "<div class='meta'>" + html.escape(budget) + "</div>"
        "</header>"
    )

    doc_parts = [
        "<!DOCTYPE html><html lang='en'><head>",
        "<meta charset='utf-8' />",
        "<meta http-equiv='refresh' content='60' />",
        "<title>Premarket Scanner - " + html.escape(now_str) + "</title>",
        "<style>" + _CSS + "</style>",
        "</head><body>",
        header_html,
        filters_line,
        table_html,
        "<footer>Signals only - not financial advice. Manage your own risk.</footer>",
        "</body></html>",
    ]
    try:
        path.write_text("".join(doc_parts), encoding="utf-8")
    except Exception as e:
        print("  [report] HTML write failed: " + str(e))
    return path
