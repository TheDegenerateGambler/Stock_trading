"""
report_builder.py — Build HTML report and live JSON files.
"""
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import config
from html_styles import CSS, JS

OUT = Path(config.OUTPUT_DIR)
OUT.mkdir(parents=True, exist_ok=True)


def _esc(s):
    return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

def _dir_cls(d):
    return {"LONG":"long","SHORT":"short"}.get(d,"skip")

def _dir_arrow(d):
    return {"LONG":"▲ LONG","SHORT":"▼ SHORT"}.get(d,"—")

def _sent_cls(score):
    if score >= 0.65: return "bull"
    if score <= 0.35: return "bear"
    return "neutral"


def _pick_card(pick, rank):
    d    = pick["direction"]
    dcls = _dir_cls(d)
    t    = _esc(pick["ticker"])
    en   = pick["entry"]
    st   = pick["stop"]
    tg   = pick["target"]
    sp   = pick["stop_pct"]
    tp   = pick["target_pct"]
    sigs = " · ".join(_esc(s) for s in pick.get("signals",[]))
    sc   = pick.get("sentiment_score", 0.5)
    sl   = _esc(pick.get("sentiment_label","Neutral"))
    sb   = int(sc * 100)
    scls = _sent_cls(sc)
    hl   = _esc(pick.get("top_headline",""))
    arts = pick.get("articles",0)
    ob   = pick.get("options_bias","neutral")
    cp   = pick.get("cp_ratio",1.0)
    if ob == "bullish":
        opts = f'<span class="opts bull">Calls {cp:.1f}:1</span>'
    elif ob == "bearish":
        opts = '<span class="opts bear">Puts dominant</span>'
    else:
        opts = '<span class="opts neutral">Options neutral</span>'
    hl_html = f'<div class="pick-headline">&ldquo;{hl}&rdquo;</div>' if hl else ""
    rr = f"{tp/sp:.1f}" if sp > 0 else "—"
    return (
        f'<div class="pick-card {dcls}">'
        f'<div class="pick-top">'
        f'<span class="pick-rank">#{rank}</span>'
        f'<span class="pick-ticker">{t}</span>'
        f'<span class="pick-dir {dcls}">{_dir_arrow(d)}</span>'
        f'{opts}</div>'
        f'<div class="pick-levels">'
        f'<div class="pick-level"><div class="lbl">Entry</div><div class="val entry">${en:.2f}</div></div>'
        f'<div class="pick-level"><div class="lbl">Stop</div><div class="val stop">${st:.2f}</div><div class="pct">-{sp:.1f}%</div></div>'
        f'<div class="pick-level"><div class="lbl">Target</div><div class="val target">${tg:.2f}</div><div class="pct">+{tp:.1f}%</div></div>'
        f'<div class="pick-level"><div class="lbl">R:R</div><div class="val" style="color:#e3b341">1:{rr}</div></div>'
        f'</div>'
        f'<div class="pick-signals">{sigs}</div>'
        f'<div class="sentiment-row">'
        f'<div class="sent-bar-bg"><div class="sent-bar {scls}" style="width:{sb}%"></div></div>'
        f'<span class="sent-label {sl}">{sl}</span>'
        f'<span class="sent-articles">({arts} articles)</span>'
        f'</div>{hl_html}</div>'
    )


def _regime_bar(regime):
    bias  = regime.get("bias","choppy")
    label = _esc(regime.get("label","UNKNOWN"))
    vix   = regime.get("vix",0.0)
    spy   = regime.get("spy_chg",0.0)
    qqq   = regime.get("qqq_chg",0.0)
    guide = _esc(regime.get("guidance",""))
    bcls  = {"bull":"bull","bear":"bear"}.get(bias,"choppy")
    sc    = lambda v: "#3fb950" if v >= 0 else "#f85149"
    sg    = lambda v: "+" if v >= 0 else ""
    return (
        f'<div class="regime-bar">'
        f'<span class="badge {bcls}">{label}</span>'
        f'&nbsp; VIX {vix:.1f} &nbsp;'
        f'SPY <span style="color:{sc(spy)}">{sg(spy)}{spy:.1f}%</span> &nbsp;'
        f'QQQ <span style="color:{sc(qqq)}">{sg(qqq)}{qqq:.1f}%</span>'
        f'<div class="guidance">{guide}</div></div>'
    )


def build_html(picks, regime, wb_items, generated_at, budget_status, next_scan):
    now_str = generated_at.strftime("%I:%M %p ET")
    picks_html = ""
    if picks:
        picks_html = "".join(_pick_card(p, i+1) for i, p in enumerate(picks))
    else:
        picks_html = '<div class="no-picks">No high-conviction picks this scan. Market may be choppy — wait for clearer setups.</div>'

    wb_html = ""
    if wb_items:
        for item in wb_items[:config.MAX_WALTER_ITEMS]:
            title = _esc(item.get("title",""))
            url   = item.get("url","#")
            age   = item.get("age","")
            wb_html += f'<div class="wb-item"><span class="wb-age">{age}</span> <a href="{url}" target="_blank">{title}</a></div>'
    else:
        wb_html = '<div class="wb-empty">Fetching headlines...</div>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>DayTrade Picks — {now_str}</title>
<style>{CSS}</style>
</head>
<body>
<div class="header">
  <h1>🎯 DayTrade Picks</h1>
  <span class="meta">{now_str} &nbsp;·&nbsp; Next scan: {next_scan} &nbsp;·&nbsp; {len(picks)} picks</span>
  <span class="av-budget">AV: <span>{budget_status}</span></span>
</div>
<div class="layout">
  <div class="picks-panel">
    {_regime_bar(regime)}
    <h2>Top {len(picks)} High-Conviction Picks</h2>
    {picks_html}
  </div>
  <div class="wb-panel">
    <h3>📡 Walter Bloomberg</h3>
    <div class="wb-subtitle" id="wb-subtitle">Real-time macro feed</div>
    <div id="wb-feed">{wb_html}</div>
  </div>
</div>
<div class="disclaimer">
  ⚠ These are data-driven signals, not financial advice. Always use stop losses and manage your own risk.
</div>
<script>{JS}</script>
</body>
</html>"""


def write_report(picks, regime, wb_items, generated_at, budget_status, next_scan):
    html = build_html(picks, regime, wb_items, generated_at, budget_status, next_scan)
    (OUT / "report.html").write_text(html, encoding="utf-8")


def write_live_data(picks, regime, generated_at, budget_status, next_scan):
    data = {
        "updated":       generated_at.isoformat(),
        "picks_count":   len(picks),
        "regime":        regime.get("label",""),
        "budget":        budget_status,
        "next_scan":     next_scan,
    }
    (OUT / "live_data.json").write_text(json.dumps(data), encoding="utf-8")


def write_live_walter(wb_items, fetched_ago):
    data = {
        "fetched_ago": fetched_ago,
        "items": [
            {"title": i.get("title","")[:160], "url": i.get("url","#"), "age": i.get("age","")}
            for i in wb_items[:config.MAX_WALTER_ITEMS]
        ]
    }
    (OUT / "live_walter.json").write_text(json.dumps(data), encoding="utf-8")