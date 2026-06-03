"""
S&P500 + Nasdaq-100 フルスクリーニング (516銘柄)
"""
import json, time, datetime, pathlib, warnings
import numpy as np
warnings.filterwarnings("ignore")
import yfinance as yf

THRESH = dict(C=25, A=25, S=25, L=70, smA=30, smR=20, smMLo=25)
TOP_N  = 30
BATCH  = 40

# ── ティッカーリスト ────────────────────────────────────────────────
with open("sp500_tickers.json", encoding="utf-8") as f:
    d = json.load(f)
TICKERS = d["all"]
print(f"対象: {len(TICKERS)} 銘柄")

# ── M条件 (SPY) ──────────────────────────────────────────────────────
print("\n[M] SPY データ取得...")
spy_hist  = yf.download("SPY", period="4mo", progress=False, auto_adjust=True)
spy_cls   = spy_hist["Close"].values.flatten().astype(float)
spy_vol   = spy_hist["Volume"].values.flatten().astype(float)
spy_hi    = spy_hist["High"].values.flatten().astype(float)
n         = len(spy_cls)
ma60      = spy_cls[-60:].mean()
spy_cur   = spy_cls[-1]
dist_days = sum(1 for i in range(max(1,n-25),n)
                if spy_cls[i]<spy_cls[i-1] and spy_vol[i]>spy_vol[i-1])
hi5       = spy_hi[-5:].max()
hi20p     = spy_hi[-25:-5].max()
hi_lo     = round(float(hi5/hi20p), 3)
spy_avg200= spy_cls[-200:].mean() if n>=200 else spy_cls.mean()
spy_perf  = (spy_cur/spy_avg200-1)*100
M_PASS    = True  # IBD Confirmed Uptrend（ユーザー確認済み）
DD_IBD    = 3

mkt = dict(
    status="bullish",
    spyPrice=round(float(spy_cur),2),
    spyChange=round(float((spy_cls[-1]-spy_cls[-2])/spy_cls[-2]*100),2),
    ma60=round(float(ma60),2), aboveMa60=bool(spy_cur>ma60),
    distributionDays=DD_IBD, hiLoRatio=float(hi_lo),
    hiLoDesc="新値圏（52週高値-0.2%）",
    followThrough=True, followThroughDate="2026-05-08"
)
print(f"  SPY ${spy_cur:.2f}  MA60 ${ma60:.2f}  DD(IBD)={DD_IBD}  => Confirmed Uptrend")

# ── IBD RS Rating: 全銘柄の15ヶ月価格を一括DL ─────────────────────
print(f"\n[RS] {len(TICKERS)} 銘柄の価格データ一括取得...")
price_data = yf.download(TICKERS, period="15mo", progress=True, auto_adjust=True)["Close"]
print(f"  取得完了: {len(price_data.columns)} 銘柄")

TRADING = dict(Q1=63, Q2=126, Q3=189, Q4=252)
def q_ret(prices, end_d, start_d):
    n_ = len(prices)
    ei = max(0, n_-1-end_d)
    si = max(0, n_-1-start_d)
    if si >= n_ or prices.iloc[si] == 0:
        return 0.0
    return (float(prices.iloc[ei]) / float(prices.iloc[si]) - 1) * 100

raw_rs = {}
for tk in price_data.columns:
    try:
        p = price_data[tk].dropna()
        if len(p) < 60:
            continue
        w = (0.40 * q_ret(p, 0,               TRADING["Q1"]) +
             0.20 * q_ret(p, TRADING["Q1"],   TRADING["Q2"]) +
             0.20 * q_ret(p, TRADING["Q2"],   TRADING["Q3"]) +
             0.20 * q_ret(p, TRADING["Q3"],   TRADING["Q4"]))
        raw_rs[tk] = float(w)
    except Exception:
        pass

sorted_rs = sorted(raw_rs, key=lambda k: raw_rs[k])
n_rs = len(sorted_rs)
ibd_rs = {}
for rank, tk in enumerate(sorted_rs):
    ibd_rs[tk] = int((rank / (n_rs - 1)) * 98 + 1) if n_rs > 1 else 50
print(f"  IBD RS Rating 計算完了: {len(ibd_rs)} 銘柄")

# ── 各銘柄スクリーニング ─────────────────────────────────────────────
print(f"\n[Screen] {len(TICKERS)} 銘柄処理中 (batch={BATCH})...")
results  = []
failed   = []
processed = 0

for batch_start in range(0, len(TICKERS), BATCH):
    batch = TICKERS[batch_start : batch_start + BATCH]
    try:
        tks = yf.Tickers(" ".join(batch))
    except Exception:
        failed.extend(batch)
        continue

    for tk in batch:
        try:
            t = tks.tickers.get(tk)
            if not t:
                failed.append(tk)
                continue
            info = t.info or {}

            price   = float(info.get("currentPrice") or info.get("regularMarketPrice") or 0)
            mkt_cap = float(info.get("marketCap") or 0)
            if price <= 0 or mkt_cap < 500_000_000:
                failed.append(tk)
                continue

            avg50   = float(info.get("fiftyDayAverage") or 0)
            avg200  = float(info.get("twoHundredDayAverage") or 0)
            yh52    = float(info.get("fiftyTwoWeekHigh") or 0)
            inst    = float(info.get("heldPercentInstitutions") or 0)
            name    = info.get("longName") or info.get("shortName") or tk
            sector  = info.get("sector") or ""

            def to_pct(v):
                return round(float(v)*100, 1) if v is not None else None

            rev_g  = to_pct(info.get("revenueGrowth"))
            earn_qg= to_pct(info.get("earningsQuarterlyGrowth"))
            om     = to_pct(info.get("operatingMargins"))
            roe    = to_pct(info.get("returnOnEquity"))

            eps_g  = earn_qg
            c_pass = eps_g is not None and eps_g >= THRESH["C"]
            a_pass = False
            s_pass = rev_g is not None and rev_g >= THRESH["S"]
            from_h = round((yh52 - price) / yh52 * 100, 1) if yh52 > 0 else None
            n_pass = from_h is not None and from_h <= 15
            rs     = ibd_rs.get(tk, 50)
            l_pass = rs >= THRESH["L"]
            abv50  = avg50 > 0 and price > avg50
            if inst > 0.50 and abv50 and n_pass:
                i_val = "Accumulation"
            elif inst < 0.25 or not abv50:
                i_val = "Distribution"
            else:
                i_val = "Neutral"
            i_pass = (i_val == "Accumulation")
            score  = int(sum([c_pass, a_pass, s_pass, n_pass, l_pass, i_pass, M_PASS]))

            sm_s   = s_pass
            sm_m   = om is not None and THRESH["smMLo"] <= om <= 65
            sm_a   = eps_g is not None and eps_g >= THRESH["smA"]
            sm_r   = roe is not None and roe >= THRESH["smR"]
            stage2 = avg200 > 0 and price > avg200
            ratio200 = price / avg200 if avg200 > 0 else 0
            excl   = []
            if not stage2:      excl.append("Stage2未確認")
            if ratio200 >= 2.0: excl.append("除外①2x200MA")
            sm_t   = len(excl) == 0
            sm_sc  = int(sum([sm_s, sm_m, sm_a, sm_r, sm_t]))
            comb   = score + sm_sc

            eg = f"{eps_g:+.1f}%" if eps_g is not None else ""
            rg = f"{rev_g:+.1f}%" if rev_g is not None else ""
            fh = f"-{from_h}%" if from_h is not None else ""
            comment = f"EPS {eg} 売上 {rg} RS={rs} 52wH{fh} OM={om}% ROE={roe}%"

            results.append(dict(
                ticker=tk, name=name, sector=sector,
                price=round(price, 2), mktCap=mkt_cap,
                score=score, smart_score=sm_sc, combined_score=comb,
                C=c_pass, A=a_pass, S=s_pass, N=n_pass, L=l_pass,
                I=i_val, Ipass=i_pass, M=M_PASS,
                smart_S=sm_s, smart_M=sm_m, smart_A=sm_a,
                smart_R=sm_r, smart_T=sm_t,
                epsGrowth=eps_g, salesGrowth=rev_g,
                opMargin=om, roe=roe, rsScore=rs,
                fromHigh=from_h, instPct=round(inst*100,1),
                stage2=stage2, avg200=round(avg200,2), avg50=round(avg50,2),
                smart_excl=excl, comment=comment,
            ))
        except Exception:
            failed.append(tk)

    processed += len(batch)
    good = len([r for r in results if r.get("score",0) >= 4])
    print(f"  [{processed:>3}/{len(TICKERS)}]  有効:{len(results):>3}  4点+:{good:>3}  失敗:{len(failed):>3}")

print(f"\n完了: 有効={len(results)}  失敗={len(failed)}")

# ── ランキング & 表示 ─────────────────────────────────────────────────
results.sort(key=lambda x: (x["score"], x.get("epsGrowth") or -9999), reverse=True)

print(f"\n{'='*85}")
print(f"  CANSLIM Top{TOP_N} — S&P500+NQ100 ({len(results)}銘柄対象)")
print(f"  Market: Confirmed Uptrend | SPY ${spy_cur:.2f} | IBD DD={DD_IBD}")
print(f"{'='*85}")
print(f"{'銘柄':<6} {'Sc':>4}  C  A  S  N  L  {'I':<6}  M  {'EPS%':>7} {'Rev%':>7}  RS  {'52wH':>6}  セクター")
print("-"*90)
for s in results[:TOP_N]:
    i_d = "Accum" if s["I"]=="Accumulation" else "Dist" if s["I"]=="Distribution" else "Neut"
    c_ = lambda k: "ok" if s.get(k) else "--"
    eg = f"{s['epsGrowth']:+.0f}%" if s.get("epsGrowth") is not None else "   —"
    rg = f"{s['salesGrowth']:+.0f}%" if s.get("salesGrowth") is not None else "   —"
    fh = f"-{s['fromHigh']}%" if s.get("fromHigh") is not None else "   —"
    print(f"{s['ticker']:<6} {s['score']:>4}/7"
          f"  {c_('C')}  {c_('A')}  {c_('S')}  {c_('N')}  {c_('L')}  {i_d:<6}"
          f"  {c_('M')}  {eg:>7} {rg:>7}  {s['rsScore']:>3}  {fh:>6}  {s['sector'][:20]}")

# SMART Top20
results_sm = sorted(results, key=lambda x:(x["smart_score"],x.get("epsGrowth") or -9999), reverse=True)
print(f"\n{'='*75}")
print(f"  SMART Top20")
print(f"{'='*75}")
print(f"{'銘柄':<6} {'Sc':>4}  S  M  A  R  T  {'OM%':>6} {'ROE%':>6} {'EPS%':>7}  RS  セクター")
print("-"*75)
for s in results_sm[:20]:
    c_ = lambda k: "ok" if s.get(k) else "--"
    om_  = f"{s['opMargin']:.0f}%" if s.get("opMargin") is not None else "  —"
    roe_ = f"{s['roe']:.0f}%" if s.get("roe") is not None else "  —"
    eg   = f"{s['epsGrowth']:+.0f}%" if s.get("epsGrowth") is not None else "   —"
    print(f"{s['ticker']:<6} {s['smart_score']:>4}/5"
          f"  {c_('smart_S')}  {c_('smart_M')}  {c_('smart_A')}  {c_('smart_R')}  {c_('smart_T')}"
          f"  {om_:>6} {roe_:>6} {eg:>7}  {s['rsScore']:>3}  {s['sector'][:20]}")

# ── 保存 ──────────────────────────────────────────────────────────────
payload = dict(
    market=mkt,
    stocks=results[:TOP_N],
    meta=dict(
        updatedAt=datetime.datetime.utcnow().isoformat()+"Z",
        screened=len(results), failed=len(failed),
        universe="S&P500+Nasdaq100", totalUniverse=len(TICKERS),
        sources=["YahooFinance","FMP"],
        marketNote="IBD Confirmed Uptrend: DD=3, FTD=2026-05-08"
    )
)
pathlib.Path("screening_results.json").write_text(
    json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
pathlib.Path("results_full.json").write_text(
    json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\nscreening_results.json (Top{TOP_N}) 保存完了")
print(f"results_full.json ({len(results)}銘柄) 保存完了")
