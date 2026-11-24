"""
report_builder.py — Build console + HTML + JSON reports.
"""
from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import config

Path(config.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

_HTML_PATH = Path(config.OUTPUT_DIR) / "swing_options_scanner.html"
_JSON_PATH = Path(config.OUTPUT_DIR) / "swing_picks.json"


# ─────────────────────────────────────────────────────────────
# Console
# ─────────────────────────────────────────────────────────────
def print_console(picks: List[Dict]) -> None:
    if not picks:
        print("\n  [report] No qualifying swing setups found.\n")
        return

    print("\n" + "=" * 100)
    print(f"  SWING OPTIONS SCANNER  |  {len(picks)} picks  |  "
          f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Budget: ${config.BUDGET_USD} USD  (max contract ${config.MAX_CONTRACT_COST})")
    print("=" * 100)

    header = (f"  {'#':<3} {'TICKER':<7} {'DIR':<5} {'SCORE':<6} "
              f"{'SPOT':<8} {'CONTRACT':<28} {'COST':<8} "
              f"{'BE':<8} {'TGT1':<8} {'R:R':<5} {'EARN':<20}")
    print(header)
    print("  " + "-" * 98)

    for i, p in enumerate(picks, 1):
        tick = p["ticker"]
        direc = p["direction"]
        score = p["composite_score"]
        spot = p["spot"]
        strike = p["contract"]["strike"]
        typ = p["contract"]["type"][0].upper()
        exp_short = p["contract"]["expiry"][5:]  # MM-DD
        contract_display = f"{tick} {exp_short} {strike}{typ}"
        cost = p["contract"]["cost_per_ct"]
        be = p["contract"]["break_even_stock"]
        tgt1 = p["contract"]["profit_target_1_$"]
        rr = p["contract"]["reward_risk"]
        earn = p["earnings_flag"][:18]

        print(f"  {i:<3} {tick:<7} {direc:<5} {score:<6} "
              f"${spot:<7} {contract_display:<28} ${cost:<7} "
              f"${be:<7} +${tgt1:<6} {rr:<5} {earn:<20}")
    print("=" * 100 + "\n")


# ─────────────────────────────────────────────────────────────
# HTML
# ─────────────────────────────────────────────────────────────
def _html_head() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Swing Options Scanner</title>
<meta http-equiv="refresh" content="300">
<style>
  * { box-sizing: border-box; }
  body {
    background: #0d1117; color: #c9d1d9;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    margin: 0; padding: 20px;
  }
  h1 { color: #58a6ff; margin: 0 0 4px 0; }
  .sub { color: #8b949e; margin-bottom: 20px; font-size: 13px; }
  .banner {
    background: #1c2128; border: 1px solid #30363d; border-left: 4px solid #f0883e;
    padding: 12px 16px; border-radius: 6px; margin-bottom: 20px; font-size: 13px;
  }
  .grid {
    display: grid; grid-template-columns: repeat(auto-fill, minmax(500px, 1fr));
    gap: 16px;
  }
  .card {
    background: #161b22; border: 1px solid #30363d; border-radius: 10px;
    padding: 16px;
  }
  .card-header {
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 10px;
  }
  .ticker { font-size: 22px; font-weight: bold; color: #f0f6fc; }
  .direction {
    padding: 3px 10px; border-radius: 12px; font-size: 12px;
    font-weight: bold; margin-left: 8px;
  }
  .call { background: #196c2e; color: #7ee787; }
  .put  { background: #6c1e19; color: #ffa198; }
  .score {
    background: #1f6feb; color: white; padding: 3px 10px; border-radius: 12px;
    font-size: 12px; font-weight: bold;
  }
  .row {
    display: flex; justify-content: space-between; padding: 4px 0;
    border-bottom: 1px solid #21262d; font-size: 13px;
  }
  .row:last-child { border-bottom: none; }
  .label { color: #8b949e; }
  .val   { color: #c9d1d9; font-family: "SF Mono", Consolas, monospace; }
  .good  { color: #7ee787; }
  .warn  { color: #f0883e; }
  .bad   { color: #ffa198; }
  .section {
    background: #0d1117; border-radius: 6px; padding: 10px 12px; margin: 10px 0;
  }
  .section-title {
    font-size: 11px; color: #58a6ff; text-transform: uppercase;
    letter-spacing: 1px; margin-bottom: 6px; font-weight: bold;
  }
  .contract-symbol {
    font-family: "SF Mono", Consolas, monospace; background: #21262d;
    padding: 4px 8px; border-radius: 4px; font-size: 11px;
    word-break: break-all; margin-bottom: 8px;
  }
  .buttons { display: flex; gap: 8px; margin-top: 10px; }
  .btn {
    flex: 1; text-align: center; padding: 6px 10px; border-radius: 6px;
    background: #21262d; color: #58a6ff; text-decoration: none;
    font-size: 12px; border: 1px solid #30363d;
  }
  .btn:hover { background: #30363d; }
  .chart {
    margin-top: 10px; border-radius: 6px; overflow: hidden;
    height: 260px; background: #0d1117;
  }
  .disclaimer {
    color: #6e7681; font-size: 11px; margin-top: 24px; padding: 10px;
    border-top: 1px solid #30363d;
  }
  .empty { text-align: center; padding: 40px; color: #8b949e; }
</style>
</head>
<body>
"""


def _tradingview_iframe(symbol: str) -> str:
    """TradingView Advanced Chart Widget iframe (daily timeframe)."""
    tv_symbol = symbol.replace("-", ".")
    return (
        f'<iframe scrolling="no" allowtransparency="true" frameborder="0" '
        f'style="width:100%;height:100%;" '
        f'src="https://s.tradingview.com/widgetembed/?symbol={tv_symbol}'
        f'&interval=D&hidesidetoolbar=1&symboledit=1&saveimage=1&toolbarbg=f1f3f6'
        f'&studies=%5B%5D&theme=dark&style=1&timezone=America%2FNew_York'
        f'&withdateranges=1&showpopupbutton=1"></iframe>'
    )


def _pick_card(pick: Dict) -> str:
    c = pick["contract"]
    direction = pick["direction"]
    dir_class = "call" if direction == "CALL" else "put"

    if "in" in pick["earnings_flag"] and "d" in pick["earnings_flag"] and "!" in pick["earnings_flag"]:
        earn_class = "warn"
    elif "safe" in pick["earnings_flag"].lower() or "in " in pick["earnings_flag"]:
        earn_class = "good"
    else:
        earn_class = "val"

    tv_link = f"https://www.tradingview.com/options/chain/?symbol={pick['ticker']}"
    chart_link = f"https://www.tradingview.com/chart/?symbol={pick['ticker']}"

    return f"""
    <div class="card">
      <div class="card-header">
        <div>
          <span class="ticker">{pick['ticker']}</span>
          <span class="direction {dir_class}">{direction}</span>
        </div>
        <span class="score">Score: {pick['composite_score']}</span>
      </div>

      <div class="row"><span class="label">Spot / EMA20 / EMA50</span>
        <span class="val">${pick['spot']} / ${pick['ema20']} / ${pick['ema50']}</span></div>
      <div class="row"><span class="label">RSI(14) / MACD hist</span>
        <span class="val">{pick['rsi']} / {pick['macd_hist']:+.3f}</span></div>
      <div class="row"><span class="label">ATR(14) / RVOL</span>
        <span class="val">${pick['atr']} ({pick['atr_pct']}%) / {pick['rvol']}x</span></div>
      <div class="row"><span class="label">Earnings</span>
        <span class="val {earn_class}">{pick['earnings_flag']}</span></div>

      <div class="section">
        <div class="section-title">Contract</div>
        <div class="contract-symbol">{c['contractSymbol']}</div>
        <div class="row"><span class="label">Strike / Expiry / DTE</span>
          <span class="val">${c['strike']} / {c['expiry']} / {c['days_to_expiry']}d</span></div>
        <div class="row"><span class="label">Mid / Bid / Ask</span>
          <span class="val">${c['mid']} / ${c['bid']} / ${c['ask']}</span></div>
        <div class="row"><span class="label">Delta / IV / OI / Vol</span>
          <span class="val">{c['delta']} / {round(c['impliedVolatility']*100, 1)}% / {c['openInterest']} / {c['volume']}</span></div>
        <div class="row"><span class="label">Cost per contract</span>
          <span class="val good">${c['cost_per_ct']}</span></div>
      </div>

      <div class="section">
        <div class="section-title">Trade Plan</div>
        <div class="row"><span class="label">Max entry (mid x 1.05)</span>
          <span class="val">${c['entry_max_premium']}</span></div>
        <div class="row"><span class="label">Break-even at expiry</span>
          <span class="val">${c['break_even_stock']} ({c['stock_move_needed_pct']:+.2f}% move)</span></div>
        <div class="row"><span class="label">Target 1 (+50%)</span>
          <span class="val good">${c['target_1_premium']} -> +${c['profit_target_1_$']}</span></div>
        <div class="row"><span class="label">Target 2 (+100%)</span>
          <span class="val good">${c['target_2_premium']} -> +${c['profit_target_2_$']}</span></div>
        <div class="row"><span class="label">Stop (-40%)</span>
          <span class="val bad">${c['stop_premium']} -> -${c['risk_$_per_ct']}</span></div>
        <div class="row"><span class="label">Reward:Risk (T1)</span>
          <span class="val">{c['reward_risk']}:1</span></div>
        <div class="row"><span class="label">Time stop</span>
          <span class="val">{c['time_stop_date']} ({config.TIME_STOP_DAYS}d)</span></div>
      </div>

      <div class="chart">{_tradingview_iframe(pick['ticker'])}</div>

      <div class="buttons">
        <a class="btn" href="{tv_link}" target="_blank">Options chain on TradingView</a>
        <a class="btn" href="{chart_link}" target="_blank">Full chart</a>
      </div>
    </div>
    """


def _score_components_row(pick: Dict) -> str:
    c = pick["contract"]
    return (
        f"<div class='row'><span class='label'>Score breakdown</span>"
        f"<span class='val'>T{pick['score_trend']} / M{pick['score_momentum']} / "
        f"V{pick['score_volume']} / S{pick['score_sentiment']} / "
        f"L{c.get('score_liquidity', 0)} / B{c.get('score_budget_fit', 0)}</span></div>"
    )


def build_html(picks: List[Dict]) -> str:
    """Return the full HTML string for the swing scanner report."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    body_parts = [_html_head()]
    body_parts.append(
        f"<h1>Swing Options Scanner</h1>"
        f"<div class='sub'>Generated {now}  |  "
        f"Budget: ${config.BUDGET_USD} USD (~${round(config.BUDGET_USD/config.CAD_TO_USD_RATE,0):.0f} CAD)  |  "
        f"DTE: {config.DTE_MIN}-{config.DTE_MAX}d  |  "
        f"Delta: {config.DELTA_MIN}-{config.DELTA_MAX}  |  "
        f"Auto-refresh every 5 min</div>"
    )
    body_parts.append(
        "<div class='banner'><b>Not financial advice.</b> "
        "Options quotes are ~15 min delayed (CBOE). "
        "Verify live prices in your broker before placing any trade. "
        "Options can go to zero &mdash; only risk what you can afford to lose.</div>"
    )

    if not picks:
        body_parts.append(
            "<div class='empty'>No qualifying swing setups found.<br>"
            "Try relaxing filters in <code>config.py</code> or scanning again later.</div>"
        )
    else:
        body_parts.append("<div class='grid'>")
        for p in picks:
            body_parts.append(_pick_card(p))
        body_parts.append("</div>")

    body_parts.append(
        "<div class='disclaimer'>Data sources: CBOE delayed options quotes, "
        "Yahoo Finance (yfinance) for underlying bars &amp; earnings, "
        "Alpha Vantage NEWS_SENTIMENT (optional). "
        "This is a research tool, not a trading system. Always do your own research.</div>"
    )
    body_parts.append("</body></html>")
    return "".join(body_parts)


def write_html(picks: List[Dict]) -> Path:
    html = build_html(picks)
    _HTML_PATH.write_text(html, encoding="utf-8")
    return _HTML_PATH


def write_json(picks: List[Dict]) -> Path:
    payload = {
        "generated_at": datetime.now().isoformat(),
        "budget_usd":   config.BUDGET_USD,
        "max_contract_cost": config.MAX_CONTRACT_COST,
        "dte_range":    [config.DTE_MIN, config.DTE_MAX],
        "delta_range":  [config.DELTA_MIN, config.DELTA_MAX],
        "count":        len(picks),
        "picks":        picks,
    }
    _JSON_PATH.write_text(json.dumps(payload, indent=2, default=str))
    return _JSON_PATH


def write_all(picks: List[Dict]) -> None:
    """Console + HTML + JSON."""
    print_console(picks)
    html_path = write_html(picks)
    json_path = write_json(picks)
    print(f"  [report] HTML: {html_path}")
    print(f"  [report] JSON: {json_path}")
