"""
call_flow.py — Analyze today's call-side options flow for SPY and QQQ.

Uses the CBOE delayed-quotes endpoint (via cboe_client) which gives us:
  - volume       (today's contracts traded)
  - open_interest
  - bid / ask / last / mid
  - IV + greeks

Since CBOE (like all free feeds) does NOT split buys vs. sells, we infer
"most-bought" activity from three complementary views:

    1. Top by Volume        - raw contract activity (in the DTE window)
    2. Top by Vol/OI ratio  - fresh positioning vs. existing OI (opening flow proxy)
    3. Top by $ Premium     - volume * mid * 100 (where the capital went)

Plus:
    - Expected weekly move (from ATM straddle × 0.85 on the nearest Friday >= 5 DTE)
    - Expiry-level rollup showing where flow is stacked (INCLUDES 0DTE for reference)

By default, 0DTE is EXCLUDED from the ranking tables (min-dte=1) so you see
where multi-day positioning is happening. The expiry rollup still shows
0DTE so you can gauge the full picture.

Runnable standalone:
    python call_flow.py                       # SPY + QQQ, min-dte=1, max-dte=30
    python call_flow.py --tickers SPY         # SPY only
    python call_flow.py --min-dte 5           # skip current-week noise
    python call_flow.py --dte 14              # limit to 14 days
    python call_flow.py --min-dte 5 --dte 14  # pure 1-2 week bucket
    python call_flow.py --top 15              # show top-15 per view
"""
from __future__ import annotations
import argparse
import re
import sys
from datetime import date
from typing import Dict, List, Optional

import cboe_client


# OCC symbol parser
_OCC_RE = re.compile(r"^([A-Z]+)(\d{2})(\d{2})(\d{2})([CP])(\d{8})$")

# Expected-move multiplier applied to the ATM straddle price.
# Trader-desk convention (Optionslam, SpotGamma). Rigorous 1-sigma value is
# sqrt(2/pi) ~= 0.7979; 0.85 is the widely quoted rule of thumb.
_EM_MULT = 0.85


def _parse_occ(occ: str) -> Optional[Dict]:
    m = _OCC_RE.match(occ)
    if not m:
        return None
    _, yy, mm, dd, right, strike_raw = m.groups()
    try:
        exp = date(2000 + int(yy), int(mm), int(dd))
        return {
            "expiry":      exp,
            "expiry_str":  exp.strftime("%Y-%m-%d"),
            "right":       right,
            "strike":      int(strike_raw) / 1000.0,
        }
    except Exception:
        return None


# =============================================================
# Expected Move
# =============================================================
def _pick_weekly_expiry(available: List[date], min_dte: int = 5) -> Optional[date]:
    """Pick the nearest Friday >= min_dte days from today.
    Falls back to nearest expiry >= min_dte if no Friday found."""
    today = date.today()
    available = sorted(set(available))
    fridays = [d for d in available
               if (d - today).days >= min_dte and d.weekday() == 4]
    if fridays:
        return fridays[0]
    ge = [d for d in available if (d - today).days >= min_dte]
    return ge[0] if ge else None


def _compute_expected_move(opts: List[Dict], spot: float) -> Optional[Dict]:
    """Compute expected move using ATM straddle * 0.85 on the nearest weekly Friday."""
    if not opts or spot <= 0:
        return None

    parsed_map = []
    for o in opts:
        p = _parse_occ(o.get("option", ""))
        if p:
            parsed_map.append((o, p))
    if not parsed_map:
        return None

    exp_date = _pick_weekly_expiry([p["expiry"] for _o, p in parsed_map], min_dte=5)
    if exp_date is None:
        return None

    calls = [(o, p) for (o, p) in parsed_map
             if p["expiry"] == exp_date and p["right"] == "C"]
    puts = [(o, p) for (o, p) in parsed_map
            if p["expiry"] == exp_date and p["right"] == "P"]
    if not calls or not puts:
        return None

    call_strikes = {p["strike"]: o for (o, p) in calls}
    put_strikes = {p["strike"]: o for (o, p) in puts}
    common = sorted(set(call_strikes.keys()) & set(put_strikes.keys()),
                    key=lambda s: abs(s - spot))
    if not common:
        return None
    atm_strike = common[0]

    def _mid(o):
        try:
            bid = float(o.get("bid", 0) or 0)
            ask = float(o.get("ask", 0) or 0)
            last = float(o.get("last_trade_price", 0) or 0)
            if bid > 0 and ask > 0:
                return (bid + ask) / 2.0
            return last or 0.0
        except Exception:
            return 0.0

    call_mid = _mid(call_strikes[atm_strike])
    put_mid = _mid(put_strikes[atm_strike])
    if call_mid <= 0 or put_mid <= 0:
        return None

    straddle = call_mid + put_mid
    em_dollars = straddle * _EM_MULT
    em_pct = (em_dollars / spot) * 100.0
    dte = (exp_date - date.today()).days

    return {
        "expiry":     exp_date.strftime("%Y-%m-%d"),
        "dte":        dte,
        "atm_strike": round(atm_strike, 2),
        "call_mid":   round(call_mid, 2),
        "put_mid":    round(put_mid, 2),
        "straddle":   round(straddle, 2),
        "em_dollars": round(em_dollars, 2),
        "em_pct":     round(em_pct, 2),
        "range_low":  round(spot - em_dollars, 2),
        "range_high": round(spot + em_dollars, 2),
        "multiplier": _EM_MULT,
    }


# =============================================================
# Core analysis
# =============================================================
def analyze_ticker(ticker: str, dte_max: int = 30, dte_min: int = 1,
                   top_n: int = 10, min_oi_for_ratio: int = 100) -> Optional[Dict]:
    """Analyze call-side flow for one ticker.

    dte_min: minimum DTE for ranking tables (default 1 = skip 0DTE).
             expiry_summary always includes 0DTE for reference.
    dte_max: maximum days-to-expiry.
    """
    payload = cboe_client.fetch_raw(ticker)
    if not payload:
        return None

    data = payload.get("data", {}) or {}
    spot = float(data.get("current_price", 0) or 0)
    opts = data.get("options", []) or []
    if not opts or spot <= 0:
        return None

    expected_move = _compute_expected_move(opts, spot)

    today = date.today()
    rows: List[Dict] = []      # filtered rows (dte_min..dte_max) — used for ranking
    all_rows: List[Dict] = []  # 0..dte_max — used for expiry summary

    for o in opts:
        parsed = _parse_occ(o.get("option", ""))
        if not parsed or parsed["right"] != "C":
            continue
        dte = (parsed["expiry"] - today).days
        if dte < 0 or dte > dte_max:
            continue

        try:
            bid = float(o.get("bid", 0) or 0)
            ask = float(o.get("ask", 0) or 0)
            last = float(o.get("last_trade_price", 0) or 0)
            mid = (bid + ask) / 2.0 if (bid > 0 and ask > 0) else (last or 0.0)
            vol = int(o.get("volume", 0) or 0)
            oi = int(o.get("open_interest", 0) or 0)
            iv = float(o.get("iv", 0) or 0)
            delta = float(o.get("delta", 0) or 0)
        except Exception:
            continue

        if vol <= 0:
            continue

        vol_oi = (vol / oi) if oi > 0 else float("inf")
        dollar_premium = vol * mid * 100.0
        moneyness_pct = ((parsed["strike"] - spot) / spot) * 100.0 if spot > 0 else 0.0

        row = {
            "symbol": o.get("option", ""),
            "strike": round(parsed["strike"], 2),
            "expiry": parsed["expiry_str"],
            "dte": dte,
            "bid": round(bid, 2),
            "ask": round(ask, 2),
            "mid": round(mid, 2),
            "volume": vol,
            "open_interest": oi,
            "vol_oi": round(vol_oi, 2) if vol_oi != float("inf") else 999.99,
            "dollar_premium": round(dollar_premium, 0),
            "iv": round(iv, 4),
            "delta": round(delta, 3),
            "moneyness_pct": round(moneyness_pct, 2),
        }
        all_rows.append(row)
        if dte >= dte_min:
            rows.append(row)

    if not all_rows:
        return {
            "ticker": ticker,
            "spot": spot,
            "dte_min": dte_min,
            "dte_max": dte_max,
            "expected_move": expected_move,
            "rows": [],
            "top_volume": [],
            "top_vol_oi": [],
            "top_premium": [],
            "expiry_summary": [],
            "totals": {"volume": 0, "dollar_premium": 0.0, "contracts": 0},
        }

    # Rankings — from filtered rows
    top_volume = sorted(rows, key=lambda r: r["volume"], reverse=True)[:top_n]
    voi_pool = [r for r in rows if r["open_interest"] >= min_oi_for_ratio]
    top_vol_oi = sorted(voi_pool, key=lambda r: r["vol_oi"], reverse=True)[:top_n]
    top_premium = sorted(rows, key=lambda r: r["dollar_premium"], reverse=True)[:top_n]

    # Expiry summary — from ALL rows (includes 0DTE for reference)
    by_exp: Dict[str, Dict] = {}
    for r in all_rows:
        b = by_exp.setdefault(r["expiry"], {
            "expiry": r["expiry"], "dte": r["dte"],
            "volume": 0, "dollar_premium": 0.0, "contracts": 0,
        })
        b["volume"] += r["volume"]
        b["dollar_premium"] += r["dollar_premium"]
        b["contracts"] += 1
    expiry_summary = sorted(by_exp.values(), key=lambda b: b["dte"])

    # Totals — only from FILTERED rows so numbers match the tables
    totals = {
        "volume": sum(r["volume"] for r in rows),
        "dollar_premium": round(sum(r["dollar_premium"] for r in rows), 0),
        "contracts": len(rows),
    }
    totals_all = {
        "volume": sum(r["volume"] for r in all_rows),
        "dollar_premium": round(sum(r["dollar_premium"] for r in all_rows), 0),
        "contracts": len(all_rows),
    }

    return {
        "ticker": ticker,
        "spot": round(spot, 2),
        "dte_min": dte_min,
        "dte_max": dte_max,
        "expected_move": expected_move,
        "rows": rows,
        "top_volume": top_volume,
        "top_vol_oi": top_vol_oi,
        "top_premium": top_premium,
        "expiry_summary": expiry_summary,
        "totals": totals,
        "totals_all": totals_all,
    }


def analyze(tickers: List[str], dte_max: int = 30, dte_min: int = 1,
            top_n: int = 10) -> Dict[str, Dict]:
    """Analyze call flow for multiple tickers. Returns { ticker: result }."""
    out: Dict[str, Dict] = {}
    for t in tickers:
        try:
            r = analyze_ticker(t, dte_max=dte_max, dte_min=dte_min, top_n=top_n)
            if r is not None:
                out[t] = r
                em = r.get("expected_move")
                em_str = ""
                if em:
                    em_str = ("  EM " + em["expiry"] + " +/-$" +
                              "{:.2f}".format(em["em_dollars"]) +
                              " ({:.2f}%)".format(em["em_pct"]))
                print("  [flow] " + t +
                      " spot $" + "{:.2f}".format(r["spot"]) +
                      "  strikes: " + str(r["totals"]["contracts"]) +
                      "  vol: " + "{:,}".format(r["totals"]["volume"]) +
                      em_str)
            else:
                print("  [flow] " + t + " no data")
        except Exception as e:
            print("  [flow] " + t + " error: " + str(e))
    return out


# =============================================================
# Standalone console output
# =============================================================
def _fmt_row(r: Dict) -> str:
    voi = r["vol_oi"]
    voi_str = ">99" if voi >= 100 else "{:.2f}".format(voi)
    return (
        "  $" + "{:>7.2f}".format(r["strike"]) +
        " " + r["expiry"] +
        " (" + "{:>2d}".format(r["dte"]) + "d)" +
        " " + "{:>+6.2f}%".format(r["moneyness_pct"]) +
        "  mid $" + "{:>5.2f}".format(r["mid"]) +
        "  vol " + "{:>7,}".format(r["volume"]) +
        "  OI " + "{:>7,}".format(r["open_interest"]) +
        "  V/OI " + "{:>6}".format(voi_str) +
        "  $prem " + "${:>11,.0f}".format(r["dollar_premium"]) +
        "  d" + "{:>4.2f}".format(r["delta"])
    )


def _fmt_em_line(em: Optional[Dict], spot: float) -> str:
    if not em:
        return "  Expected move: (unavailable)"
    return (
        "  Expected weekly move (exp " + em["expiry"] +
        ", " + str(em["dte"]) + "d): +/-$" +
        "{:.2f}".format(em["em_dollars"]) +
        " (+/-{:.2f}%)".format(em["em_pct"]) +
        "   Range: $" + "{:.2f}".format(em["range_low"]) +
        " - $" + "{:.2f}".format(em["range_high"]) +
        "   ATM straddle $" + "{:.2f}".format(em["straddle"]) +
        " x " + "{:.2f}".format(em["multiplier"])
    )


def render_console(result: Dict) -> str:
    lines: List[str] = []
    t = result["ticker"]
    dte_min = result.get("dte_min", 1)
    dte_max = result.get("dte_max", 30)
    spot = result.get("spot", 0)

    lines.append("")
    lines.append("=" * 120)
    lines.append("  " + t + " CALL FLOW  (spot $" + "{:.2f}".format(spot) +
                 ", DTE " + str(dte_min) + "-" + str(dte_max) +
                 ", quotes ~15 min delayed)")
    lines.append(_fmt_em_line(result.get("expected_move"), spot))
    excl_note = "  (excludes 0DTE)" if dte_min > 0 else ""
    lines.append("  Filtered totals: " + "{:,}".format(result["totals"]["volume"]) +
                 " calls across " + str(result["totals"]["contracts"]) +
                 " strikes  ·  $" + "{:,.0f}".format(result["totals"]["dollar_premium"]) +
                 " premium" + excl_note)
    lines.append("=" * 120)

    def _section(title, rows):
        lines.append("")
        lines.append("  " + title)
        lines.append("  " + "-" * 116)
        if not rows:
            lines.append("    (no data in this DTE window)")
            return
        for r in rows:
            lines.append(_fmt_row(r))

    _section("TOP BY VOLUME (most-traded calls in window)", result["top_volume"])
    _section("TOP BY VOL/OI RATIO (fresh positioning — opening-flow proxy, OI >= 100)",
             result["top_vol_oi"])
    _section("TOP BY $ PREMIUM (where the capital went)", result["top_premium"])

    lines.append("")
    lines.append("  EXPIRY ROLLUP  (all expiries incl. 0DTE, for reference)")
    lines.append("  " + "-" * 116)
    lines.append("    " + "{:<12}".format("Expiry") +
                 "{:>5}".format("DTE") +
                 "  " + "{:>12}".format("Vol") +
                 "  " + "{:>16}".format("$ Premium") +
                 "  " + "{:>9}".format("Strikes"))
    for b in result["expiry_summary"]:
        marker = " *" if b["dte"] >= dte_min else "  "
        lines.append("  " + marker + "{:<12}".format(b["expiry"]) +
                     "{:>5d}".format(b["dte"]) +
                     "  " + "{:>12,}".format(b["volume"]) +
                     "  " + "${:>15,.0f}".format(b["dollar_premium"]) +
                     "  " + "{:>9,}".format(b["contracts"]))
    lines.append("  (* = included in the top-rank tables above)")

    return "\n".join(lines)


# =============================================================
# CLI
# =============================================================
def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    ap = argparse.ArgumentParser(
        description="Analyze call-side options flow (CBOE delayed, ~15 min)")
    ap.add_argument("--tickers", nargs="+", default=["SPY", "QQQ"],
                    help="Tickers to analyze (default: SPY QQQ)")
    ap.add_argument("--min-dte", type=int, default=1, dest="min_dte",
                    help="Minimum days-to-expiry for ranking tables "
                         "(default: 1 = skip 0DTE)")
    ap.add_argument("--dte", type=int, default=30,
                    help="Max days-to-expiry (default: 30)")
    ap.add_argument("--top", type=int, default=10,
                    help="Rows per ranking table (default: 10)")
    args = ap.parse_args()

    print("=" * 60)
    print("  SPY/QQQ CALL FLOW  ·  DTE " + str(args.min_dte) +
          "-" + str(args.dte) + " days")
    print("  Data: CBOE delayed quotes (~15 min)")
    print("=" * 60)

    results = analyze(args.tickers, dte_max=args.dte, dte_min=args.min_dte,
                      top_n=args.top)
    if not results:
        print("No data returned.")
        return 1

    for t in args.tickers:
        r = results.get(t)
        if r is None:
            print("\n  " + t + ": no data")
            continue
        print(render_console(r))

    print("")
    print("Note: CBOE feed does not split buys vs sells. Vol/OI ratio is the")
    print("best free proxy for 'new opening flow' (calls being bought to open).")
    print("Expected move = ATM straddle x 0.85 for nearest Friday (>=5 DTE).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
