"""
scorer.py — Score day-trade candidates.

Pipeline per ticker:
  1. yfinance 5-min bars → RSI, MACD, RVOL, VWAP, ATR
  2. yfinance options chain → call/put volume bias
  3. AV NEWS_SENTIMENT score (pre-fetched, passed in)
  4. Weight all signals → LONG / SHORT / SKIP
  5. Entry, stop (1xATR), target (2xATR)
"""
from __future__ import annotations
import warnings
warnings.filterwarnings("ignore")
from typing import Dict, List
import config
from indicators import safe, calc_rsi, calc_macd, calc_vwap, calc_atr


def _fetch_intraday(ticker: str) -> Dict:
    try:
        import yfinance as yf
        df = yf.Ticker(ticker).history(period="1d", interval="5m")
        if df.empty or len(df) < 5:
            return {}
        closes  = [safe(v) for v in df["Close"].tolist()]
        volumes = [safe(v) for v in df["Volume"].tolist()]
        highs   = [safe(v) for v in df["High"].tolist()]
        lows    = [safe(v) for v in df["Low"].tolist()]
        price   = closes[-1]
        if price <= 0:
            return {}
        rsi = calc_rsi(closes, 14)
        _, _, macd_hist = calc_macd(closes)
        vwap = calc_vwap(highs, lows, closes, volumes)
        atr  = calc_atr(highs, lows, closes, 14)
        avg_bar_vol = sum(volumes[:-1]) / max(len(volumes) - 1, 1)
        rvol = safe(volumes[-1]) / avg_bar_vol if avg_bar_vol > 0 else 1.0
        open_price = safe(df["Open"].iloc[0])
        gap_pct = (price - open_price) / open_price * 100 if open_price > 0 else 0.0
        return {
            "price":       round(price, 2),
            "open":        round(open_price, 2),
            "rsi":         round(rsi, 1),
            "macd_hist":   round(macd_hist, 4),
            "macd_rising": macd_hist > 0,
            "vwap":        round(vwap, 2),
            "above_vwap":  price > vwap,
            "rvol":        round(rvol, 2),
            "atr":         round(atr, 4),
            "atr_pct":     round(atr / price * 100, 2) if price > 0 else 0.0,
            "gap_pct":     round(gap_pct, 2),
        }
    except Exception as e:
        print(f"  [Scorer] intraday {ticker}: {e}")
        return {}


def _fetch_options_bias(ticker: str) -> Dict:
    try:
        import yfinance as yf
        t = yf.Ticker(ticker)
        exps = t.options
        if not exps:
            return {"cp_ratio": 1.0, "options_bias": "neutral", "call_vol": 0, "put_vol": 0}
        chain = t.option_chain(exps[0])
        call_vol = int(chain.calls["volume"].fillna(0).sum())
        put_vol  = int(chain.puts["volume"].fillna(0).sum())
        if call_vol + put_vol == 0:
            return {"cp_ratio": 1.0, "options_bias": "neutral", "call_vol": 0, "put_vol": 0}
        cp_ratio = call_vol / put_vol if put_vol > 0 else 5.0
        bias = "bullish" if cp_ratio >= 1.5 else ("bearish" if cp_ratio <= 0.67 else "neutral")
        return {"cp_ratio": round(cp_ratio, 2), "options_bias": bias,
                "call_vol": call_vol, "put_vol": put_vol}
    except Exception:
        return {"cp_ratio": 1.0, "options_bias": "neutral", "call_vol": 0, "put_vol": 0}


def _score_signals(tech: Dict, opts: Dict, sentiment: Dict, regime_bias: str) -> Dict:
    price = tech.get("price", 0.0)
    rsi   = tech.get("rsi", 50.0)
    atr   = tech.get("atr", price * 0.01) or price * 0.01
    bull = 0
    bear = 0
    signals = []

    if 30 < rsi < 65:
        bull += 1
        signals.append(f"RSI {rsi:.0f}")
    elif rsi >= 65:
        bear += 1
        signals.append(f"RSI {rsi:.0f} OB")
    elif rsi <= 30:
        bull += 1
        signals.append(f"RSI {rsi:.0f} OS")

    if tech.get("macd_rising"):
        bull += 1; signals.append("MACD+")
    else:
        bear += 1; signals.append("MACD-")

    if tech.get("above_vwap"):
        bull += 1; signals.append("Above VWAP")
    else:
        bear += 1; signals.append("Below VWAP")

    rvol = tech.get("rvol", 1.0)
    if rvol >= config.RVOL_HIGH:
        bull += 1; signals.append(f"RVOL {rvol:.1f}x")

    gap = tech.get("gap_pct", 0.0)
    if gap >= 1.0:
        bull += 1; signals.append(f"Gap+{gap:.1f}%")
    elif gap <= -1.0:
        bear += 1; signals.append(f"Gap{gap:.1f}%")

    ob = opts.get("options_bias", "neutral")
    if ob == "bullish":
        bull += 1; signals.append(f"Calls {opts.get('cp_ratio',1.0):.1f}:1")
    elif ob == "bearish":
        bear += 1; signals.append("Puts>Calls")

    sc = sentiment.get("sentiment_score", 0.5)
    sl = sentiment.get("sentiment_label", "Neutral")
    if sc >= 0.65:
        bull += 1; signals.append(f"Sent {sc:.2f} {sl}")
    elif sc <= 0.35:
        bear += 1; signals.append(f"Sent {sc:.2f} {sl}")

    if regime_bias == "bull":
        bull += 1; signals.append("Bull mkt")
    elif regime_bias == "bear":
        bear += 1; signals.append("Bear mkt")

    if bull >= 3 and bull > bear:
        direction = "LONG"
        stop   = round(price - atr * config.ATR_STOP_MULT, 2)
        target = round(price + atr * config.ATR_TARGET_MULT, 2)
        stop_pct   = round((price - stop)   / price * 100, 1)
        target_pct = round((target - price) / price * 100, 1)
    elif bear >= 3 and bear > bull:
        direction = "SHORT"
        stop   = round(price + atr * config.ATR_STOP_MULT, 2)
        target = round(price - atr * config.ATR_TARGET_MULT, 2)
        stop_pct   = round((stop - price)   / price * 100, 1)
        target_pct = round((price - target) / price * 100, 1)
    else:
        direction = "SKIP"
        stop = target = price
        stop_pct = target_pct = 0.0

    return {
        "direction": direction, "stop": stop, "target": target,
        "stop_pct": stop_pct, "target_pct": target_pct,
        "bull_signals": bull, "bear_signals": bear, "signals": signals,
    }


def score_ticker(ticker: str, sentiment: Dict, regime_bias: str,
                 av_price: float = 0.0) -> Dict:
    tech = _fetch_intraday(ticker)
    if not tech:
        if av_price > config.MIN_PRICE:
            tech = {
                "price": av_price, "open": av_price, "rsi": 50.0,
                "macd_hist": 0.0, "macd_rising": False, "above_vwap": False,
                "rvol": 1.0, "atr": av_price * 0.01, "atr_pct": 1.0,
                "gap_pct": 0.0, "vwap": av_price,
            }
        else:
            return {}

    price = tech.get("price", 0.0)
    if price < config.MIN_PRICE:
        return {}

    opts   = _fetch_options_bias(ticker)
    result = _score_signals(tech, opts, sentiment, regime_bias)
    if result["direction"] == "SKIP":
        return {}

    top_headline = ""
    hls = sentiment.get("top_headlines", [])
    if hls:
        top_headline = hls[0].get("title", "")

    return {
        "ticker":       ticker,
        "direction":    result["direction"],
        "entry":        price,
        "stop":         result["stop"],
        "target":       result["target"],
        "stop_pct":     result["stop_pct"],
        "target_pct":   result["target_pct"],
        "bull_signals": result["bull_signals"],
        "bear_signals": result["bear_signals"],
        "signals":      result["signals"],
        "rsi":          tech.get("rsi", 50.0),
        "macd_hist":    tech.get("macd_hist", 0.0),
        "rvol":         tech.get("rvol", 1.0),
        "above_vwap":   tech.get("above_vwap", False),
        "vwap":         tech.get("vwap", price),
        "atr":          tech.get("atr", 0.0),
        "gap_pct":      tech.get("gap_pct", 0.0),
        "call_vol":     opts.get("call_vol", 0),
        "put_vol":      opts.get("put_vol", 0),
        "cp_ratio":     opts.get("cp_ratio", 1.0),
        "options_bias": opts.get("options_bias", "neutral"),
        "sentiment_score": sentiment.get("sentiment_score", 0.5),
        "sentiment_label": sentiment.get("sentiment_label", "Neutral"),
        "top_headline": top_headline,
        "articles":     sentiment.get("articles", 0),
    }


def build_candidates(av_data: Dict) -> List[Dict]:
    """
    Build scored candidate list from AV TOP_GAINERS_LOSERS data.
    Returns list of {ticker, av_price, av_change_pct, source}.
    """
    candidates = []
    seen = set()

    def _add(items, source):
        for item in items[:config.SCAN_CANDIDATES]:
            t = item.get("ticker", "").strip().upper()
            if not t or t in seen:
                continue
            if "." in t or len(t) > 5:
                continue  # skip ETFs with dots, long symbols
            try:
                price = float(str(item.get("price", "0")).replace(",", ""))
                chg   = float(str(item.get("change_percentage", "0")).replace("%", "").replace(",", ""))
                vol   = int(str(item.get("volume", "0")).replace(",", ""))
            except Exception:
                price, chg, vol = 0.0, 0.0, 0
            if price < config.MIN_PRICE:
                continue
            seen.add(t)
            candidates.append({"ticker": t, "av_price": price,
                                "av_change_pct": chg, "av_volume": vol,
                                "source": source})

    _add(av_data.get("top_gainers", []),          "gainer")
    _add(av_data.get("most_actively_traded", []),  "active")
    _add(av_data.get("top_losers", []),            "loser")
    return candidates