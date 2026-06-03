"""
CANSLIM Screener — 3-Source Integration (v2)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Data Sources & Roles:
  Yahoo Finance (yfinance)  → Price, 52w High/Low, MA50/200, Volume,
                               Revenue Growth (S), Earnings Growth (C fallback),
                               Institutional Holders % (I), SPY history (M)
  Alpha Vantage             → Annual EPS history 4 years (A condition, precise)
                               Quarterly EPS YoY (C condition, precise)
  FMP REST API              → Backup for price data if yfinance fails

API call budget (free tiers):
  yfinance  : unlimited (unofficial)
  AV        : 25 calls/day, 5 calls/min
  FMP       : 250 calls/day

Usage:
  python canslim_screener.py [--c 25] [--a 25] [--s 25] [--l 70] [--top 25]
"""

import sys, time, json, re, argparse, datetime
from pathlib import Path
from typing import Optional

try:
    import yfinance as yf
    import pandas as pd
except ImportError:
    sys.exit("Run: pip install yfinance pandas")

try:
    import requests
except ImportError:
    sys.exit("Run: pip install requests")

# ── API keys ──────────────────────────────────────────────────────────────────
import os
FMP_KEY = os.getenv("FMP_API_KEY", "N1HukTVqzFwhSl1tpI13CVJh5cp0I29b")
AV_KEY  = os.getenv("AV_API_KEY",  "UMKP1E9TFZV1VNM6")
AV_BASE = "https://www.alphavantage.co/query"
FMP_BASE = "https://financialmodelingprep.com/stable"

# ── Thresholds ────────────────────────────────────────────────────────────────
THRESH = dict(C=25.0, A=25.0, S=25.0, L=70, N=15.0)

# ── Helpers ───────────────────────────────────────────────────────────────────
def safe_float(v, default=None):
    try: return float(v)
    except: return default

def pct(v):
    return f"{v:+.1f}%" if v is not None else "—"

def av(function, **params):
    params.update({"function": function, "apikey": AV_KEY})
    try:
        r = requests.get(AV_BASE, params=params, timeout=15)
        if r.ok:
            d = r.json()
            if "Note" in d:
                print("[AV] Rate limit (5/min). Waiting 15s…"); time.sleep(15)
                return None
            if "Information" in d:
                print("[AV] Daily limit reached."); return None
            return d
    except Exception as e:
        print(f"[AV] Error: {e}")
    return None

def fmp(endpoint, **params):
    params["apikey"] = FMP_KEY
    try:
        r = requests.get(f"{FMP_BASE}/{endpoint}", params=params, timeout=10)
        if r.ok and r.status_code != 429:
            return r.json()
    except Exception:
        pass
    return None

# ═══════════════════════════════════════════════════════════════════════════════
# M CONDITION — SPY via yfinance (primary) / FMP (fallback)
# ═══════════════════════════════════════════════════════════════════════════════
def calc_m_condition():
    print("\n[M] Fetching SPY data via yfinance …")
    try:
        spy_hist = yf.download("SPY", period="4mo", progress=False, auto_adjust=True)
        if spy_hist.empty:
            raise ValueError("empty")

        closes  = spy_hist["Close"].values.flatten().tolist()
        volumes = spy_hist["Volume"].values.flatten().tolist()
        highs   = spy_hist["High"].values.flatten().tolist()
        dates   = [str(d.date()) for d in spy_hist.index]
        n       = len(closes)

        ma60       = sum(closes[-60:]) / min(60, n)
        cur        = closes[-1]
        prev       = closes[-2]
        above_ma60 = cur > ma60
        day_chg    = (cur - prev) / prev * 100

        dist_days = sum(
            1 for i in range(max(1, n - 25), n)
            if closes[i] < closes[i-1] and volumes[i] > volumes[i-1]
        )
        hi5   = max(highs[-5:])
        hi20p = max(highs[-25:-5]) if n >= 25 else max(highs[:-5] or [hi5])
        hi_lo = round(hi5 / hi20p, 3) if hi20p else 1.0
        hi_lo_desc = "新値圏（5d高値 > 直近20d高値）" if hi5 > hi20p else "直近20d高値を下回る"

        avg_vol20 = sum(volumes[-20:]) / 20
        ft, ft_date = False, ""
        for i in range(max(1, n - 10), n):
            dp = (closes[i] - closes[i-1]) / closes[i-1] * 100
            if dp >= 1.7 and volumes[i] > avg_vol20:
                ft, ft_date = True, dates[i]

        if dist_days <= 3 and above_ma60 and hi_lo >= 1.0:
            status = "bullish"
        elif dist_days >= 6 or not above_ma60:
            status = "bearish"
        else:
            status = "caution"

        # SPY performance vs 200d MA (for L/RS calculation)
        avg200 = sum(closes[-200:]) / min(200, n)
        spy_perf = (cur / avg200 - 1) * 100

        print(f"  SPY ${cur:.2f}  MA60 ${ma60:.2f}  DistDays {dist_days}  "
              f"Hi/Lo {hi_lo}  FT {ft}  → {status.upper()}")

        return dict(
            status=status, pass_=(status == "bullish"), spy_perf=spy_perf,
            spyPrice=round(cur, 2), spyChange=round(day_chg, 2),
            ma60=round(ma60, 2), aboveMa60=above_ma60,
            distributionDays=dist_days, hiLoRatio=hi_lo, hiLoDesc=hi_lo_desc,
            followThrough=ft, followThroughDate=ft_date,
        )
    except Exception as e:
        print(f"  WARNING: SPY fetch failed ({e}). Defaulting to caution.")
        return dict(status="caution", pass_=False, spy_perf=11.0,
                    spyPrice=None, spyChange=None, ma60=None, aboveMa60=False,
                    distributionDays=None, hiLoRatio=None, hiLoDesc="—",
                    followThrough=False, followThroughDate="")

# ═══════════════════════════════════════════════════════════════════════════════
# STOCK UNIVERSE
# ═══════════════════════════════════════════════════════════════════════════════
def get_universe():
    tickers = [
        # AI / Semiconductors
        "NVDA","AMD","AVGO","QCOM","AMAT","LRCX","KLAC","MRVL","ARM","SMCI","INTC",
        # Mega-cap tech
        "MSFT","AAPL","GOOGL","AMZN","META","TSLA","ORCL",
        # Software / Cloud / AI-infra
        "NOW","CRM","PLTR","APP","NET","ZS","CRWD","DDOG","SNOW","TTD",
        "HUBS","BILL","GTLB","MDB","VEEV","WDAY","ADSK",
        # Fintech / Finance
        "V","MA","GS","JPM","COIN","PYPL","NU","AFRM",
        # Consumer
        "COST","ONON","DECK","ELF","LULU","CELH","MNST",
        # Healthcare / Biotech
        "LLY","VRTX","REGN","ISRG","DXCM","ABBV",
        # Industrial / Security
        "AXON","FTNT","PANW","CYBR",
        # Travel / Leisure
        "UBER","ABNB","BKNG","RCL","CCL",
        # Growth / Emerging
        "MELI","SHOP","NFLX","SPOT","DUOL","RBLX",
    ]
    return list(dict.fromkeys(tickers))

# ═══════════════════════════════════════════════════════════════════════════════
# YAHOO FINANCE — price + fundamentals + institutional
# ═══════════════════════════════════════════════════════════════════════════════
def get_yf_data(ticker: str) -> Optional[dict]:
    try:
        t    = yf.Ticker(ticker)
        info = t.info or {}
        if not info.get("regularMarketPrice") and not info.get("currentPrice"):
            return None

        price   = safe_float(info.get("currentPrice") or info.get("regularMarketPrice"))
        mkt_cap = safe_float(info.get("marketCap"), 0)
        if not price or mkt_cap < 500_000_000:
            return None

        # Revenue / earnings growth from YF (TTM / quarterly)
        rev_growth = safe_float(info.get("revenueGrowth"))         # TTM YoY decimal
        earn_q_g   = safe_float(info.get("earningsQuarterlyGrowth"))  # latest Q YoY decimal

        if rev_growth  is not None: rev_growth  *= 100
        if earn_q_g    is not None: earn_q_g    *= 100

        # Institutional holders
        inst_pct = safe_float(info.get("heldPercentInstitutions"))

        # SMART extra fields
        op_margin = safe_float(info.get("operatingMargins"))  # M condition
        roe       = safe_float(info.get("returnOnEquity"))    # R condition
        if op_margin is not None: op_margin *= 100
        if roe       is not None: roe       *= 100

        avg200 = safe_float(info.get("twoHundredDayAverage"))
        avg50  = safe_float(info.get("fiftyDayAverage"))

        return dict(
            name    = info.get("longName") or info.get("shortName") or ticker,
            exchange= info.get("exchange",""),
            price   = price,
            yearHigh= safe_float(info.get("fiftyTwoWeekHigh")),
            yearLow = safe_float(info.get("fiftyTwoWeekLow")),
            avg50   = avg50,
            avg200  = avg200,
            volume  = safe_float(info.get("regularMarketVolume"), 0),
            mktCap  = mkt_cap,
            revGrowth   = rev_growth,
            earnQGrowth = earn_q_g,
            instPct     = inst_pct,
            opMargin    = op_margin,   # SMART M
            roe         = roe,         # SMART R
            sector      = info.get("sector",""),
            industry    = info.get("industry",""),
        )
    except Exception:
        return None

# ═══════════════════════════════════════════════════════════════════════════════
# ALPHA VANTAGE EARNINGS — precise A (annual) + C (quarterly) conditions
# ═══════════════════════════════════════════════════════════════════════════════
def get_av_annual_eps(ticker: str) -> tuple:
    """Returns (quarterly_eps_growth, a_pass)."""
    data = av("EARNINGS", symbol=ticker)
    if not data:
        return None, False

    # ── A condition: 3 consecutive fiscal years of EPS growth ≥ THRESH["A"] ──
    annual = sorted(data.get("annualEarnings", []),
                    key=lambda x: x.get("fiscalDateEnding",""), reverse=True)
    # Filter to annual records only (skip partial years by checking date gap)
    annual_eps = []
    last_date  = None
    for rec in annual:
        try:
            d = datetime.date.fromisoformat(rec["fiscalDateEnding"])
        except ValueError:
            continue
        if last_date is None or abs((last_date - d).days) > 180:
            eps = safe_float(rec.get("reportedEPS"))
            if eps is not None:
                annual_eps.append((d, eps))
                last_date = d
        if len(annual_eps) >= 5:
            break

    a_pass = False
    if len(annual_eps) >= 4:
        consistent = True
        for i in range(3):
            cur_e, prv_e = annual_eps[i][1], annual_eps[i+1][1]
            if prv_e == 0 or prv_e < 0:
                consistent = False; break
            if (cur_e - prv_e) / abs(prv_e) * 100 < THRESH["A"]:
                consistent = False; break
        a_pass = consistent

    # ── C condition: latest quarter YoY EPS growth ─────────────────────────
    quarterly = sorted(data.get("quarterlyEarnings",[]),
                       key=lambda x: x.get("fiscalDateEnding",""), reverse=True)
    q_growth = None
    if len(quarterly) >= 5:
        latest = safe_float(quarterly[0].get("reportedEPS"))
        yoy    = safe_float(quarterly[4].get("reportedEPS"))  # same Q, prior year
        if latest is not None and yoy is not None and yoy != 0 and yoy > 0:
            q_growth = (latest - yoy) / abs(yoy) * 100

    return q_growth, a_pass

# ═══════════════════════════════════════════════════════════════════════════════
# SMART condition scoring
# ═══════════════════════════════════════════════════════════════════════════════
def score_smart(ticker, yf_d, eps_g, mkt_status, dist_days, spy_perf):
    """
    S — Sales Growth >= 25% (YF revGrowth)
    M — Operating Margin 25-65% (sweet spot: not too low, not monopoly)
    A — EPS Acceleration >= 30% (quarterly YoY)
    R — ROE >= 20%
    T — Timing: Stage2 + no exclusion signals + dist_days <= 5
    Returns dict with smart_score (0-5) and individual flags.
    """
    price  = yf_d["price"]
    avg50  = yf_d["avg50"]
    avg200 = yf_d["avg200"]
    yh     = yf_d["yearHigh"]
    om     = yf_d.get("opMargin")
    roe    = yf_d.get("roe")
    vol    = yf_d.get("volume", 0)

    # S
    rev_g  = yf_d.get("revGrowth")
    sm_s   = rev_g is not None and rev_g >= 25.0

    # M — Operating Margin 25-65%
    sm_m   = om is not None and 25.0 <= om <= 65.0

    # A — EPS acceleration >= 30%
    sm_a   = eps_g is not None and eps_g >= 30.0

    # R — ROE >= 20%
    sm_r   = roe is not None and roe >= 20.0

    # T — Timing (multi-check)
    stage2       = bool(avg200 and price > avg200)
    ratio_200    = price / avg200 if avg200 and avg200 > 0 else 0
    from_h       = (yh - price) / yh * 100 if yh and yh > 0 else None

    # Exclusion signals
    t_excl = []
    if mkt_status in ("bearish",):
        t_excl.append("市場Correction")
    if dist_days is not None and dist_days >= 6:
        t_excl.append(f"売抜日{dist_days}回")
    if not stage2:
        t_excl.append("Stage2未確認")
    if ratio_200 >= 2.0:
        t_excl.append("除外①2x200MA")
    if from_h is not None and from_h > 40:
        t_excl.append("高値から乖離大")

    sm_t = len(t_excl) == 0

    smart_score = sum([sm_s, sm_m, sm_a, sm_r, sm_t])

    return dict(
        smart_S=sm_s, smart_M=sm_m, smart_A=sm_a, smart_R=sm_r, smart_T=sm_t,
        smart_score=smart_score,
        opMargin=round(om, 1) if om is not None else None,
        roe=round(roe, 1) if roe is not None else None,
        smart_excl=t_excl,
        stage2=stage2,
    )

# ═══════════════════════════════════════════════════════════════════════════════
# CANSLIM condition scoring
# ═══════════════════════════════════════════════════════════════════════════════
def score_stock(ticker, yf_d, av_q_growth, av_a_pass, spy_perf, m_pass):
    price  = yf_d["price"]
    yh     = yf_d["yearHigh"]
    avg50  = yf_d["avg50"]
    avg200 = yf_d["avg200"]

    # C — quarterly EPS growth (AV precise, else YF fallback)
    eps_g = av_q_growth if av_q_growth is not None else yf_d["earnQGrowth"]
    c_pass = eps_g is not None and eps_g >= THRESH["C"]

    # A — 3 consecutive annual EPS ≥ THRESH["A"] (AV)
    a_pass = av_a_pass

    # S — revenue growth (YF TTM)
    rev_g  = yf_d["revGrowth"]
    s_pass = rev_g is not None and rev_g >= THRESH["S"]

    # N — within THRESH["N"]% of 52-week high
    from_h = round((yh - price) / yh * 100, 1) if (yh and yh > 0) else None
    n_pass = from_h is not None and from_h <= THRESH["N"]

    # L — Relative Strength vs SPY (via 200d MA performance proxy)
    rs = 50
    l_pass = False
    if avg200 and avg200 > 0:
        st_perf = (price / avg200 - 1) * 100
        rs_raw  = st_perf - spy_perf
        rs      = max(0, min(100, round(50 + rs_raw * 0.67)))
        l_pass  = rs >= THRESH["L"]

    # I — Institutional sponsorship
    #   Uses: heldPercentInstitutions (YF), price vs 50dMA, N condition
    inst   = yf_d["instPct"]           # decimal 0-1
    abv50  = avg50 is not None and price > avg50
    if inst is not None:
        if inst > 0.50 and abv50 and n_pass:
            i_val = "Accumulation"
        elif inst < 0.25 or not abv50:
            i_val = "Distribution"
        else:
            i_val = "Neutral"
    else:
        i_val = "Accumulation" if (abv50 and n_pass) else \
                "Distribution" if not abv50 else "Neutral"
    i_pass = (i_val == "Accumulation")

    score = sum([c_pass, a_pass, s_pass, n_pass, l_pass, i_pass, m_pass])

    return dict(
        C=c_pass, A=a_pass, S=s_pass, N=n_pass, L=l_pass,
        I=i_val, Ipass=i_pass, M=m_pass, score=score,
        epsGrowth  = round(eps_g, 1) if eps_g is not None else None,
        salesGrowth= round(rev_g, 1) if rev_g is not None else None,
        rsScore    = rs,
        fromHigh   = from_h,
        instPct    = round(inst * 100, 1) if inst else None,
        avUsed     = av_q_growth is not None,  # True = precise AV data
    )

# ═══════════════════════════════════════════════════════════════════════════════
# COMMENT GENERATOR
# ═══════════════════════════════════════════════════════════════════════════════
def make_comment(s):
    parts = []
    src   = "（AV精密）" if s.get("avUsed") else "（YF推定）"
    if s.get("epsGrowth") is not None:
        parts.append(f"EPS成長 {pct(s['epsGrowth'])}{src}")
    if s.get("salesGrowth") is not None:
        parts.append(f"売上成長 {pct(s['salesGrowth'])}")
    if s.get("fromHigh") is not None:
        parts.append(f"52週高値 -{s['fromHigh']}%")
    if s.get("rsScore") is not None:
        parts.append(f"RSスコア {s['rsScore']}")
    if s.get("instPct") is not None:
        parts.append(f"機関保有 {s['instPct']}%")
    passing = [c for c in ["C","A","S","N","L"] if s.get(c)]
    if passing:
        parts.append("通過: " + "/".join(passing))
    if s.get("I") == "Accumulation":
        parts.append("I=機関買い優勢")
    return "。".join(parts) + "。"

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--c",   type=float, default=25)
    parser.add_argument("--a",   type=float, default=25)
    parser.add_argument("--s",   type=float, default=25)
    parser.add_argument("--l",   type=float, default=70)
    parser.add_argument("--top", type=int,   default=25)
    args = parser.parse_args()
    THRESH.update(C=args.c, A=args.a, S=args.s, L=args.l)

    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    print("=" * 72)
    print(f"  CANSLIM SCREENER  v2  ─  {ts}")
    print(f"  Sources: Yahoo Finance + Alpha Vantage + FMP")
    print(f"  Thresholds: C>={THRESH['C']}%  A>={THRESH['A']}%  S>={THRESH['S']}%  L>={THRESH['L']}")
    print("=" * 72)

    # M condition
    mkt = calc_m_condition()
    m_pass   = mkt["pass_"]
    spy_perf = mkt["spy_perf"]

    # Universe
    tickers = get_universe()
    print(f"\n[Screen] {len(tickers)} tickers | AV budget: 25 calls")

    results  = []
    av_calls = 0
    AV_LIMIT = 24

    for i, ticker in enumerate(tickers, 1):
        print(f"  [{i:3d}/{len(tickers)}] {ticker:<6}", end=" ", flush=True)

        # 1. Yahoo Finance
        yf_d = get_yf_data(ticker)
        if yf_d is None:
            print("skip (no data / mktCap<500M)")
            continue

        # 2. Alpha Vantage (budget-aware)
        av_q, av_a = None, False
        if av_calls < AV_LIMIT:
            av_q, av_a = get_av_annual_eps(ticker)
            av_calls  += 1
            time.sleep(12.5)   # 5 calls/min → 12s gap

        # 3. CANSLIM Score
        cond = score_stock(ticker, yf_d, av_q, av_a, spy_perf, m_pass)

        # 4. SMART Score
        eps_g_for_smart = cond.get("epsGrowth")
        smart = score_smart(ticker, yf_d, eps_g_for_smart,
                            mkt["status"], mkt["distributionDays"], spy_perf)

        row = dict(ticker=ticker, name=yf_d["name"],
                   price=round(yf_d["price"], 2),
                   mktCap=yf_d["mktCap"],
                   sector=yf_d["sector"],
                   exchange=yf_d["exchange"],
                   **cond, **smart)
        results.append(row)

        print(f"{cond['score']}/7  "
              f"C={'✓' if cond['C'] else '—'}"
              f"A={'✓' if cond['A'] else '—'}"
              f"S={'✓' if cond['S'] else '—'}"
              f"N={'✓' if cond['N'] else '—'}"
              f"L={'✓' if cond['L'] else '—'}"
              f"I={cond['I'][:5]:<5}  "
              f"eps={pct(cond.get('epsGrowth'))}  "
              f"rev={pct(cond.get('salesGrowth'))}  "
              f"{'[AV]' if cond.get('avUsed') else '[YF]'}")

    # ── Rank ──────────────────────────────────────────────────────────────────
    results.sort(key=lambda x: (x["score"], x.get("epsGrowth") or -999), reverse=True)
    top = results[:args.top]
    for s in top:
        s["comment"] = make_comment(s)

    # ── Markdown table ────────────────────────────────────────────────────────
    print(f"\n{'=' * 90}")
    print(f"  TOP {args.top} CANSLIM  ─  Market: {mkt['status'].upper()}  "
          f"SPY ${mkt['spyPrice']}  DistDays={mkt['distributionDays']}")
    print(f"{'=' * 90}")
    hdr = f"| {'銘柄':<6} | Sc | C | A | S | N | L | {'I':<6} | M | {'EPS%':>7} | {'Rev%':>7} | RS  | 52wH%  | 機関%  |"
    print(hdr)
    print("|" + "-" * (len(hdr)-2) + "|")
    for s in top:
        ip   = f"{s['instPct']}%" if s.get("instPct") else "—"
        fh   = f"-{s['fromHigh']}%" if s.get("fromHigh") is not None else "—"
        print(f"| {s['ticker']:<6} | {s['score']:2}/7"
              f"| {'✓' if s['C'] else '—'} | {'✓' if s['A'] else '—'}"
              f"| {'✓' if s['S'] else '—'} | {'✓' if s['N'] else '—'}"
              f"| {'✓' if s['L'] else '—'} | {s['I'][:6]:<6}"
              f"| {'✓' if s['M'] else '—'} | {pct(s.get('epsGrowth')):>7}"
              f"| {pct(s.get('salesGrowth')):>7} | {s['rsScore']:>3}"
              f"| {fh:>6} | {ip:>6} |")

    # ── Save JSON ─────────────────────────────────────────────────────────────
    payload = dict(
        market=dict(
            status=mkt["status"], spyPrice=mkt["spyPrice"],
            spyChange=mkt["spyChange"], ma60=mkt["ma60"],
            aboveMa60=mkt["aboveMa60"], distributionDays=mkt["distributionDays"],
            hiLoRatio=mkt["hiLoRatio"], hiLoDesc=mkt["hiLoDesc"],
            followThrough=mkt["followThrough"],
            followThroughDate=mkt["followThroughDate"],
        ),
        stocks=top,
        meta=dict(
            updatedAt=datetime.datetime.utcnow().isoformat() + "Z",
            screened=len(results), avCallsUsed=av_calls,
            thresholds=THRESH, top=args.top,
            sources=["YahooFinance", "AlphaVantage", "FMP"],
        ),
    )
    out = Path(__file__).parent / "screening_results.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✓ Saved → {out}")

    # ── Top-5 detail ──────────────────────────────────────────────────────────
    print(f"\n── 上位銘柄コメント {'─'*50}")
    for s in top[:5]:
        print(f"\n【{s['ticker']}】{s['name']}  {s['score']}/7")
        print(f"  {s['comment']}")

    print(f"\n✓ Screened {len(results)} stocks | AV calls: {av_calls}/{AV_LIMIT}")
    return payload


if __name__ == "__main__":
    main()
