"""
report_builder.py — Console + HTML for the options day trader.

HTML sections:
  - SPY & QQQ big cards (side by side, TradingView charts)
  - Top gap-up options play card (TradingView chart)
  - Watchlist table (secondary candidates)
"""
from __future__ import annotations
import html
import json
from pathlib import Path
from typing import Dict, List, Optional

import config

OUT = Path(config.OUTPUT_DIR)
OUT.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────────────────────
# Console
# ─────────────────────────────────────────────────────────────
def _dir_glyph(direction):
    return {"CALL": "^ CALL", "PUT": "v PUT", "NO-TRADE": "- NO-TRADE"}.get(direction, direction)


def _fmt_pick_console(p):
    """Format one pick (with optional contract) as multi-line text."""
    lines = []
    hdr = "  " + p["ticker"] + "  " + _dir_glyph(p["direction"]) + \
          "  price $" + "{:.2f}".format(p["price"]) + \
          "  ({:+.2f}%)".format(p["change_pct"]) + \
          "  conf " + str(p["confidence"])
    lines.append(hdr)
    if p.get("contract"):
        c = p["contract"]
        liq_flag = " [LOW LIQ]" if c.get("low_liquidity") else ""
        lines.append(
            "    " + c["type"].upper() + " " + str(c["strike"]) +
            " exp " + c["expiry"] +
            "  mid $" + "{:.2f}".format(c["mid"]) +
            "  Δ" + "{:.2f}".format(c["delta"]) +
            "  OI " + "{:,}".format(c["openInterest"]) +
            "  vol " + "{:,}".format(c["volume"]) +
            liq_flag
        )
        lines.append(
            "    entry<= $" + "{:.2f}".format(c["entry_max"]) +
            "  stop $" + "{:.2f}".format(c["stop"]) +
            "  target $" + "{:.2f}".format(c["target"]) +
            "  R:R 1:" + "{:.2f}".format(c["risk_reward"]) +
            "  risk/ct $" + "{:.2f}".format(c["risk_per_contract"])
        )
    if p.get("rationale"):
        lines.append("    " + " · ".join(p["rationale"][:5]))
    return "\n".join(lines)


def render_console(etf_picks, top_pick, watchlist, meta, call_flow=None):
    lines = []
    lines.append("=" * 100)
    lines.append("  OPTIONS DAY TRADER — " + meta["now_str"] +
                 "   (quotes ~15 min delayed)")
    lines.append("=" * 100)

    lines.append("")
    lines.append("  ETF PICKS")
    if etf_picks:
        for p in etf_picks:
            lines.append(_fmt_pick_console(p))
            lines.append("")
    else:
        lines.append("    (ETF signals not available.)")
        lines.append("")

    lines.append("  TOP GAP-UP OPTIONS PLAY")
    if top_pick:
        lines.append(_fmt_pick_console(top_pick))
    else:
        lines.append("    No qualifying gap-up options play.")

    lines.append("")
    lines.append("  WATCHLIST (secondary)")
    if watchlist:
        for p in watchlist[:10]:
            lines.append(
                "    " + p["ticker"] +
                "  " + _dir_glyph(p["direction"]) +
                "  conf " + str(p["confidence"]) +
                "  $" + "{:.2f}".format(p["price"])
            )
    else:
        lines.append("    (empty)")
    lines.append("")
    lines.append("  Next scan: " + meta.get("next_scan", "(none)"))
    # Call flow section (multi-day flow — 0DTE excluded from ranking tables)
    if call_flow:
        lines.append("")
        lines.append("  SPY / QQQ CALL FLOW  (1-30 DTE, excl. 0DTE, top 5 by volume)")
        lines.append("  " + "-" * 96)
        for tkr in ("SPY", "QQQ"):
            r = call_flow.get(tkr)
            if not r:
                lines.append("    " + tkr + ": no data")
                continue
            tot = r.get("totals", {})
            em = r.get("expected_move") or {}
            em_line = ""
            if em:
                em_line = ("   EM (exp " + em["expiry"] +
                           ", " + str(em["dte"]) + "d): +/-$" +
                           "{:.2f}".format(em["em_dollars"]) +
                           " (+/-{:.2f}%)".format(em["em_pct"]) +
                           " range $" + "{:.2f}".format(em["range_low"]) +
                           "-$" + "{:.2f}".format(em["range_high"]))
            lines.append("    " + tkr + "  spot $" + "{:.2f}".format(r.get("spot", 0)) +
                         "  vol " + "{:,}".format(tot.get("volume", 0)) +
                         "  $prem $" + "{:,.0f}".format(tot.get("dollar_premium", 0)) +
                         em_line)
            for row in r.get("top_volume", [])[:5]:
                lines.append(
                    "      $" + "{:>7.2f}".format(row["strike"]) +
                    " " + row["expiry"] +
                    " (" + "{:>2d}".format(row["dte"]) + "d)" +
                    " " + "{:>+6.2f}%".format(row["moneyness_pct"]) +
                    "  vol " + "{:>7,}".format(row["volume"]) +
                    "  OI " + "{:>7,}".format(row["open_interest"]) +
                    "  $prem " + "${:>11,.0f}".format(row["dollar_premium"])
                )

    lines.append("=" * 100)
    lines.append("  Not financial advice. Manage your own risk.")
    lines.append("=" * 100)

    text = "\n".join(lines)
    print(text)
    return text


# ─────────────────────────────────────────────────────────────
# JSON
# ─────────────────────────────────────────────────────────────
def write_json(payload):
    try:
        (OUT / "options_daytrader.json").write_text(
            json.dumps(payload, indent=2, default=str))
    except Exception as e:
        print("  [report] JSON write failed: " + str(e))


# ─────────────────────────────────────────────────────────────
# HTML
# ─────────────────────────────────────────────────────────────
_CSS = """
:root { --bg:#0b0f17; --panel:#131a26; --panel2:#1a2333; --border:#2a3548;
        --text:#e5edf7; --dim:#8a96a8; --accent:#4ea1ff;
        --pos:#26d07c; --neg:#ff5c6c; --warn:#ffb74d; }
* { box-sizing: border-box; }
body { font-family: -apple-system, "Segoe UI", Roboto, sans-serif;
       background: var(--bg); color: var(--text); margin:0; padding:20px; }
header { display:flex; justify-content:space-between; align-items:baseline;
         flex-wrap:wrap; gap:12px; margin-bottom:14px; }
h1 { margin:0; font-size:20px; color:var(--accent); }
h2 { font-size:15px; color:var(--dim); text-transform:uppercase;
     letter-spacing:1px; margin:22px 0 10px 0; }
.meta { color:var(--dim); font-size:12px; }
.grid { display:grid; grid-template-columns:1fr 1fr; gap:14px; }
.card { background:var(--panel); border:1px solid var(--border);
        border-radius:10px; padding:14px; }
.card.big { padding:14px 16px; }
.ticker { font-weight:700; color:var(--accent); font-size:22px; }
.badge { display:inline-block; padding:3px 10px; border-radius:14px;
         font-size:12px; font-weight:700; margin-left:8px; vertical-align:middle; }
.b-call    { background:rgba(38,208,124,0.15); color:var(--pos); }
.b-put     { background:rgba(255,92,108,0.15); color:var(--neg); }
.b-notrade { background:rgba(138,150,168,0.15); color:var(--dim); }
.b-lowliq  { background:rgba(255,183,77,0.15); color:var(--warn); margin-left:6px; }
.row { display:flex; justify-content:space-between; margin:6px 0; font-size:13px; }
.row .k { color:var(--dim); }
.row .v { color:var(--text); font-variant-numeric:tabular-nums; }
.conf-bar { height:6px; background:var(--panel2); border-radius:3px; margin:8px 0; overflow:hidden; }
.conf-bar > div { height:100%; background:var(--accent); }
.rationale { color:var(--dim); font-size:12px; margin-top:6px; line-height:1.5; }
.contract { background:var(--panel2); border-radius:8px; padding:10px; margin-top:10px; font-size:13px; }
.contract .cline { display:flex; justify-content:space-between; margin:4px 0; }
.chart { height:260px; margin-top:10px; border-radius:8px; overflow:hidden;
         background:var(--panel2); }
.actions { margin-top:10px; display:flex; gap:8px; flex-wrap:wrap; }
.btn { display:inline-block; padding:6px 12px; border-radius:6px;
       background:var(--panel2); color:var(--accent);
       border:1px solid var(--border); text-decoration:none;
       font-size:12px; font-weight:600; }
.btn:hover { background:var(--border); color:var(--text); }
table.watch { width:100%; border-collapse:collapse; background:var(--panel);
              border-radius:8px; overflow:hidden; border:1px solid var(--border); }
table.watch th, table.watch td { padding:8px 12px; text-align:left;
     border-bottom:1px solid var(--border); font-size:13px; }
table.watch th { background:var(--panel2); color:var(--dim); font-size:11px;
     text-transform:uppercase; letter-spacing:.5px; }
table.watch tr:last-child td { border-bottom:none; }
.num { text-align:right !important; font-variant-numeric:tabular-nums; }
footer { margin-top:16px; color:var(--dim); font-size:11px; text-align:center; }
/* Call flow section */
.flow-card { background:var(--panel); border:1px solid var(--border);
             border-radius:10px; padding:14px; }
.flow-card h3 { margin:0 0 4px 0; font-size:16px; color:var(--accent); }
.flow-card .flow-sub { color:var(--dim); font-size:12px; margin-bottom:10px; }
.flow-card h4 { margin:14px 0 6px 0; font-size:11px; color:var(--dim);
                text-transform:uppercase; letter-spacing:.6px; font-weight:600; }
table.flow { width:100%; border-collapse:collapse; font-size:12px;
             background:var(--panel2); border-radius:6px; overflow:hidden; }
table.flow th, table.flow td { padding:5px 8px; text-align:right;
     border-bottom:1px solid var(--border); font-variant-numeric:tabular-nums; }
table.flow th { background:var(--bg); color:var(--dim); font-size:10px;
     text-transform:uppercase; letter-spacing:.4px; font-weight:600; }
table.flow td.strike, table.flow th.strike { text-align:left; color:var(--accent); font-weight:600; }
table.flow td.exp { text-align:left; color:var(--dim); }
table.flow tr:last-child td { border-bottom:none; }
table.flow tr.itm td.strike { color:var(--pos); }
table.flow tr.otm td.strike { color:var(--warn); }
.flow-note { color:var(--dim); font-size:11px; margin-top:10px; font-style:italic; }
.em-box { background: linear-gradient(90deg, rgba(78,161,255,0.10), rgba(38,208,124,0.08));
          border:1px solid rgba(78,161,255,0.35); border-radius:8px;
          padding:10px 12px; margin:8px 0 12px 0; font-size:13px; }
.em-box .em-label { color:var(--dim); font-size:10px; text-transform:uppercase;
                    letter-spacing:.6px; margin-bottom:4px; }
.em-box .em-value { font-size:18px; font-weight:700; color:var(--accent);
                    font-variant-numeric:tabular-nums; }
.em-box .em-range { color:var(--text); font-size:13px; margin-top:4px;
                    font-variant-numeric:tabular-nums; }
.em-box .em-meta  { color:var(--dim); font-size:11px; margin-top:4px; }
"""


def _direction_badge(direction):
    cls = {"CALL": "b-call", "PUT": "b-put", "NO-TRADE": "b-notrade"}.get(direction, "b-notrade")
    return "<span class='badge " + cls + "'>" + html.escape(direction) + "</span>"


def _tv_exchange_prefix(ticker):
    """Guess an exchange prefix for TradingView URL. SPY=AMEX, QQQ=NASDAQ."""
    return {
        "SPY": "AMEX",
        "QQQ": "NASDAQ",
        "IWM": "AMEX",
        "DIA": "AMEX",
    }.get(ticker, "")


def _tv_chain_url(ticker):
    prefix = _tv_exchange_prefix(ticker)
    sym = (prefix + ":" + ticker) if prefix else ticker
    # URL-encode the colon
    sym_enc = sym.replace(":", "%3A")
    return "https://www.tradingview.com/options/chain/?symbol=" + sym_enc


def _tv_chart_url(ticker):
    prefix = _tv_exchange_prefix(ticker)
    sym = (prefix + ":" + ticker) if prefix else ticker
    sym_enc = sym.replace(":", "%3A")
    return "https://www.tradingview.com/chart/?symbol=" + sym_enc


def _tv_widget(ticker, height=260):
    """TradingView Advanced Chart Widget iframe."""
    sym = "AMEX:" + ticker if ticker in ("SPY",) else ("NASDAQ:" + ticker if ticker == "QQQ" else ticker)
    div_id = "tv_" + ticker.replace("-", "_")
    return (
        "<div class='chart' id='" + div_id + "'></div>"
        "<script type='text/javascript' src='https://s3.tradingview.com/tv.js'></script>"
        "<script type='text/javascript'>"
        "new TradingView.widget({"
        "\"width\":\"100%\",\"height\":" + str(height) + ","
        "\"symbol\":\"" + sym + "\","
        "\"interval\":\"5\","
        "\"timezone\":\"America/New_York\","
        "\"theme\":\"dark\","
        "\"style\":\"1\","
        "\"locale\":\"en\","
        "\"toolbar_bg\":\"#131a26\","
        "\"enable_publishing\":false,"
        "\"hide_top_toolbar\":true,"
        "\"hide_legend\":false,"
        "\"save_image\":false,"
        "\"container_id\":\"" + div_id + "\""
        "});"
        "</script>"
    )


def _contract_html(c):
    if not c:
        return "<div class='contract'><i>No qualifying options contract found.</i></div>"
    low_liq = "<span class='badge b-lowliq'>LOW LIQUIDITY</span>" if c.get("low_liquidity") else ""
    src = c.get("source", "yfinance")
    src_label = "CBOE" if src == "cboe" else "yfinance"

    greeks_line = ""
    if c.get("gamma") is not None or c.get("theta") is not None:
        greeks_line = (
            "<div class='cline'><span class='k'>Γ · Θ · ν</span>"
            "<span class='v'>" + "{:.4f}".format(c.get("gamma", 0)) +
            " · " + "{:.4f}".format(c.get("theta", 0)) +
            " · " + "{:.4f}".format(c.get("vega", 0)) + "</span></div>"
        )

    return (
        "<div class='contract'>"
        "<div class='cline'><span class='k'>Contract</span>"
        "<span class='v'>" + html.escape(c["type"].upper()) + " " + str(c["strike"]) +
        " · exp " + html.escape(c["expiry"]) + low_liq + "</span></div>"
        "<div class='cline'><span class='k'>Mid / Δ / IV</span>"
        "<span class='v'>$" + "{:.2f}".format(c["mid"]) +
        " · Δ " + "{:.2f}".format(c["delta"]) +
        " · " + "{:.1f}".format(c.get("impliedVolatility", 0) * 100) + "%</span></div>"
        + greeks_line +
        "<div class='cline'><span class='k'>OI / Vol / Spread</span>"
        "<span class='v'>" + "{:,}".format(c["openInterest"]) +
        " · " + "{:,}".format(c["volume"]) +
        " · " + "{:.1f}".format(c["spread_pct"] * 100) + "%</span></div>"
        "<div class='cline'><span class='k'>Entry &lt;=</span>"
        "<span class='v'>$" + "{:.2f}".format(c["entry_max"]) + "</span></div>"
        "<div class='cline'><span class='k'>Stop / Target</span>"
        "<span class='v'>$" + "{:.2f}".format(c["stop"]) +
        " / $" + "{:.2f}".format(c["target"]) +
        "  (R:R 1:" + "{:.2f}".format(c["risk_reward"]) + ")</span></div>"
        "<div class='cline'><span class='k'>Risk / Reward per contract</span>"
        "<span class='v'>$" + "{:.2f}".format(c["risk_per_contract"]) +
        " / $" + "{:.2f}".format(c["reward_per_contract"]) + "</span></div>"
        "<div class='cline'><span class='k'>Source</span>"
        "<span class='v meta'>" + src_label + "</span></div>"
        "</div>"
    )


def _pick_card_html(p, big=False):
    if not p:
        return "<div class='card'><i>Not available.</i></div>"
    conf_pct = min(100, max(0, int(p.get("confidence", 0))))
    dir_badge = _direction_badge(p["direction"])
    price_chg = "{:+.2f}%".format(p["change_pct"])
    chg_cls = "pos" if p["change_pct"] >= 0 else "neg"

    rationale_html = ""
    if p.get("rationale"):
        rationale_html = ("<div class='rationale'>" +
                          html.escape(" · ".join(p["rationale"][:6])) + "</div>")

    contract_html = _contract_html(p.get("contract"))
    chart_html = _tv_widget(p["ticker"], height=260)

    tv_chain = _tv_chain_url(p["ticker"])
    tv_chart = _tv_chart_url(p["ticker"])
    actions_html = (
        "<div class='actions'>"
        "<a class='btn' href='" + tv_chain + "' target='_blank' rel='noopener'>"
        "View options chain on TradingView →</a>"
        "<a class='btn' href='" + tv_chart + "' target='_blank' rel='noopener'>"
        "Open full chart</a>"
        "</div>"
    )

    card_class = "card big" if big else "card"
    return (
        "<div class='" + card_class + "'>"
        "<div><span class='ticker'>" + html.escape(p["ticker"]) + "</span>"
        + dir_badge + "</div>"
        "<div class='row'><span class='k'>Price</span>"
        "<span class='v'>$" + "{:.2f}".format(p["price"]) +
        "  <span class='meta'>" + price_chg + "</span></span></div>"
        "<div class='row'><span class='k'>VWAP · RSI · RVOL</span>"
        "<span class='v'>" + "{:.2f}".format(p.get("vwap", 0)) +
        " · " + "{:.0f}".format(p.get("rsi", 0)) +
        " · " + "{:.2f}".format(p.get("rvol", 0)) + "x</span></div>"
        "<div class='row'><span class='k'>Score</span>"
        "<span class='v'>" + "{:+.0f}".format(p.get("score", 0)) +
        "  (conf " + str(conf_pct) + ")</span></div>"
        "<div class='conf-bar'><div style='width:" + str(conf_pct) + "%'></div></div>"
        + rationale_html
        + contract_html
        + actions_html
        + chart_html +
        "</div>"
    )


def _watchlist_html(rows):
    if not rows:
        return "<div class='card'><i>Watchlist empty.</i></div>"
    trs = []
    for p in rows:
        chg_cls = "pos" if p["change_pct"] >= 0 else "neg"
        trs.append(
            "<tr>"
            "<td><b>" + html.escape(p["ticker"]) + "</b></td>"
            "<td>" + _direction_badge(p["direction"]) + "</td>"
            "<td class='num'>$" + "{:.2f}".format(p["price"]) + "</td>"
            "<td class='num'>{:+.2f}%</td>".format(p["change_pct"]) +
            "<td class='num'>" + str(p["confidence"]) + "</td>"
            "<td>" + html.escape(" · ".join(p.get("rationale", [])[:3])) + "</td>"
            "</tr>"
        )
    return (
        "<table class='watch'><thead><tr>"
        "<th>Ticker</th><th>Dir</th><th>Price</th><th>Chg</th>"
        "<th>Conf</th><th>Signals</th>"
        "</tr></thead><tbody>" + "".join(trs) + "</tbody></table>"
    )


# ─────────────────────────────────────────────────────────────
# Call flow HTML
# ─────────────────────────────────────────────────────────────
def _flow_row_class(row):
    """Highlight ITM (green) vs OTM (amber) rows."""
    m = row.get("moneyness_pct", 0)
    if m <= 0:
        return "itm"
    return "otm"


def _flow_table(rows, columns):
    """Render a small ranked table for call-flow section.

    columns: list of ("header", key, fmt) tuples. First col is the strike/expiry combo.
    """
    if not rows:
        return "<div class='meta'>No data.</div>"
    thead = "<tr>"
    for h, _k, _f in columns:
        cls = "strike" if _k == "_strike_exp" else ""
        thead += "<th class='" + cls + "'>" + html.escape(h) + "</th>"
    thead += "</tr>"

    trs = []
    for r in rows:
        row_cls = _flow_row_class(r)
        cells = ""
        for _h, key, fmt in columns:
            if key == "_strike_exp":
                cells += ("<td class='strike'>$" + "{:.2f}".format(r["strike"]) +
                          " <span class='exp'>" + r["expiry"] +
                          " (" + str(r["dte"]) + "d)</span></td>")
            elif key == "moneyness_pct":
                cells += "<td>{:+.2f}%</td>".format(r["moneyness_pct"])
            elif key == "vol_oi":
                voi = r.get("vol_oi", 0)
                voi_str = ">99" if voi >= 100 else "{:.2f}".format(voi)
                cells += "<td>" + voi_str + "</td>"
            elif key == "dollar_premium":
                cells += "<td>${:,.0f}</td>".format(r[key])
            elif fmt:
                cells += "<td>" + fmt.format(r.get(key, 0)) + "</td>"
            else:
                cells += "<td>" + str(r.get(key, "")) + "</td>"
        trs.append("<tr class='" + row_cls + "'>" + cells + "</tr>")

    return ("<table class='flow'><thead>" + thead + "</thead>"
            "<tbody>" + "".join(trs) + "</tbody></table>")


def _expiry_summary_table(rows):
    if not rows:
        return "<div class='meta'>No data.</div>"
    trs = []
    for b in rows:
        trs.append(
            "<tr>"
            "<td class='strike'>" + html.escape(b["expiry"]) + "</td>"
            "<td>" + str(b["dte"]) + "d</td>"
            "<td>{:,}</td>".format(b["volume"]) +
            "<td>${:,.0f}</td>".format(b["dollar_premium"]) +
            "<td>{:,}</td>".format(b["contracts"]) +
            "</tr>"
        )
    return ("<table class='flow'><thead><tr>"
            "<th class='strike'>Expiry</th><th>DTE</th><th>Vol</th>"
            "<th>$ Premium</th><th>Strikes</th></tr></thead>"
            "<tbody>" + "".join(trs) + "</tbody></table>")


def _expected_move_box(em, spot):
    """Prominent expected-move display box."""
    if not em:
        return ("<div class='em-box'>"
                "<div class='em-label'>Expected Weekly Move</div>"
                "<div class='em-value meta'>Unavailable</div></div>")
    return (
        "<div class='em-box'>"
        "<div class='em-label'>Expected Weekly Move &nbsp;·&nbsp; exp " +
        html.escape(em["expiry"]) + " (" + str(em["dte"]) + "d)</div>"
        "<div class='em-value'>&plusmn;$" + "{:.2f}".format(em["em_dollars"]) +
        " &nbsp;(&plusmn;{:.2f}%)</div>".format(em["em_pct"]) +
        "<div class='em-range'>Range: <b>$" + "{:.2f}".format(em["range_low"]) +
        "</b> — <b>$" + "{:.2f}".format(em["range_high"]) + "</b>"
        " &nbsp;(spot $" + "{:.2f}".format(spot) + ")</div>"
        "<div class='em-meta'>ATM straddle $" +
        "{:.2f}".format(em["straddle"]) +
        " (call $" + "{:.2f}".format(em["call_mid"]) +
        " + put $" + "{:.2f}".format(em["put_mid"]) + ") &times; " +
        "{:.2f}".format(em["multiplier"]) + " &nbsp;·&nbsp; ATM strike $" +
        "{:.2f}".format(em["atm_strike"]) + "</div>"
        "</div>"
    )


def _call_flow_card(result):
    if not result:
        return "<div class='flow-card'><i>No data.</i></div>"
    tkr = result["ticker"]
    spot = result.get("spot", 0)
    tot = result.get("totals", {})
    em = result.get("expected_move")
    dte_min = result.get("dte_min", 1)
    dte_max = result.get("dte_max", 30)

    header = (
        "<h3>" + html.escape(tkr) + " Calls</h3>"
        "<div class='flow-sub'>Spot <b>$" + "{:.2f}".format(spot) + "</b>"
        " &nbsp;·&nbsp; DTE window: <b>" + str(dte_min) + "-" + str(dte_max) + " days</b>"
        " (0DTE excluded from tables)"
        " &nbsp;·&nbsp; filtered call vol: <b>" + "{:,}".format(tot.get("volume", 0)) + "</b>"
        " &nbsp;·&nbsp; $ premium: <b>${:,.0f}</b>".format(tot.get("dollar_premium", 0)) +
        "</div>"
    )

    em_html = _expected_move_box(em, spot)

    vol_cols = [
        ("Strike / Exp",  "_strike_exp",    None),
        ("Δ%",            "moneyness_pct",  None),
        ("Vol",           "volume",         "{:,}"),
        ("OI",            "open_interest",  "{:,}"),
        ("V/OI",          "vol_oi",         None),
        ("$ Premium",     "dollar_premium", None),
    ]

    top_vol_h  = "<h4>Top by Volume (most-traded calls in window)</h4>" + \
                 _flow_table(result.get("top_volume", []), vol_cols)
    top_voi_h  = "<h4>Top by Vol/OI Ratio (fresh opening-flow proxy)</h4>" + \
                 _flow_table(result.get("top_vol_oi", []), vol_cols)
    top_prem_h = "<h4>Top by $ Premium (where the capital went)</h4>" + \
                 _flow_table(result.get("top_premium", []), vol_cols)
    exp_h      = "<h4>Expiry Rollup (all expiries incl. 0DTE, for reference)</h4>" + \
                 _expiry_summary_table(result.get("expiry_summary", []))

    tv_chain = _tv_chain_url(tkr)
    actions = ("<div class='actions'>"
               "<a class='btn' href='" + tv_chain + "' target='_blank' rel='noopener'>"
               "View " + html.escape(tkr) + " options chain on TradingView →</a></div>")

    return ("<div class='flow-card'>" + header + em_html +
            top_vol_h + top_voi_h + top_prem_h + exp_h + actions +
            "<div class='flow-note'>Green = ITM · Amber = OTM. "
            "Expected move = ATM straddle &times; 0.85 for nearest Friday (&ge;5 DTE). "
            "CBOE feed shows total volume (buys+sells combined); V/OI ratio is the "
            "best free proxy for calls being bought to open.</div>"
            "</div>")


def _call_flow_section(call_flow):
    if not call_flow:
        return "<div class='card'><i>Call flow data unavailable.</i></div>"
    cards = []
    for tkr in ("SPY", "QQQ"):
        r = call_flow.get(tkr)
        cards.append(_call_flow_card(r) if r else
                     "<div class='flow-card'><h3>" + tkr + "</h3>"
                     "<i>No data returned from CBOE.</i></div>")
    return "<div class='grid'>" + "".join(cards) + "</div>"


def write_html(etf_picks, top_pick, watchlist, meta, call_flow=None):
    path = OUT / "options_daytrader.html"

    now_str    = meta.get("now_str", "")
    next_scan  = meta.get("next_scan", "")

    etf_html = ""
    if etf_picks:
        cards = [_pick_card_html(p, big=True) for p in etf_picks]
        etf_html = "<div class='grid'>" + "".join(cards) + "</div>"
    else:
        etf_html = "<div class='card'><i>ETF picks not available.</i></div>"

    top_html = _pick_card_html(top_pick, big=True) if top_pick else \
        "<div class='card'><i>No qualifying gap-up options play right now.</i></div>"

    watch_html = _watchlist_html(watchlist or [])
    flow_html  = _call_flow_section(call_flow)

    doc_parts = [
        "<!DOCTYPE html><html lang='en'><head>",
        "<meta charset='utf-8' />",
        "<meta http-equiv='refresh' content='60' />",
        "<title>Options Day Trader - " + html.escape(now_str) + "</title>",
        "<style>" + _CSS + "</style>",
        "</head><body>",
        "<header><div><h1>Options Day Trader</h1>",
        "<div class='meta'>Scan: <b>" + html.escape(now_str) + "</b> &nbsp;&bull;&nbsp; ",
        "Next: <b>" + html.escape(next_scan) + "</b> &nbsp;&bull;&nbsp; ",
        "Quotes ~15 min delayed (CBOE / yfinance)</div></div></header>",
        "<h2>ETF Picks (SPY / QQQ)</h2>", etf_html,
        "<h2>SPY / QQQ Call Flow — Most-Bought Calls (1-30 DTE · excludes 0DTE) + Expected Weekly Move</h2>", flow_html,
        "<h2>Top Gap-Up Options Play</h2>", top_html,
        "<h2>Watchlist</h2>", watch_html,
        "<footer>Signals only. Not financial advice. Manage your own risk.</footer>",
        "</body></html>",
    ]
    try:
        path.write_text("".join(doc_parts), encoding="utf-8")
    except Exception as e:
        print("  [report] HTML write failed: " + str(e))
    return path
