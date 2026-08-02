"""
REDFORDウォッチリスト銘柄の単発スクリーニング（22銘柄）
screening_results.json は上書きせず、watchlist_screen_results.json に別途出力する。
"""
import sys, json, datetime, pathlib, warnings
warnings.filterwarnings("ignore")
import yfinance as yf
from fix_a_condition import calc_a

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

THRESH = dict(C=25, A=25, S=25, L=70, smA=30, smR=20, smMLo=25)

TICKERS = ['VRT','KVYO','QBTS','IONQ','QUBT','LQDA','ASTH','TVTX','DAVE','KNSA',
           'GH','CRWD','SKWD','PANW','FTNT','RBRK','CYBR','EW','GE','NMM','VIK','NTAP']
print(f"対象: {len(TICKERS)} 銘柄（REDFORDウォッチリスト・単発検証）")

# 既存の市場判定を引き継ぐ
prev_mkt = {}
_res = pathlib.Path("screening_results.json")
if _res.exists():
    prev_mkt = json.loads(_res.read_text(encoding="utf-8")).get("market", {})
M_PASS = prev_mkt.get("status") == "bullish"
print(f"市場status={prev_mkt.get('status')}（引き継ぎ） M={'合格' if M_PASS else '不合格'}")

MARKET_EXCL = []
if prev_mkt.get("status") == "bearish":
    MARKET_EXCL.append("除外②市場Correction")
if int(prev_mkt.get("distributionDays") or 0) >= 6:
    MARKET_EXCL.append("除外③売抜け日6回超")

# IBD RS Rating計算用に15ヶ月価格を取得
print("\n[RS] 価格データ取得...")
price_data = yf.download(TICKERS, period="15mo", progress=False, auto_adjust=True)["Close"]

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
        w = (0.40 * q_ret(p, 0, TRADING["Q1"]) +
             0.20 * q_ret(p, TRADING["Q1"], TRADING["Q2"]) +
             0.20 * q_ret(p, TRADING["Q2"], TRADING["Q3"]) +
             0.20 * q_ret(p, TRADING["Q3"], TRADING["Q4"]))
        raw_rs[tk] = float(w)
    except Exception:
        pass

sorted_rs = sorted(raw_rs, key=lambda k: raw_rs[k])
n_rs = len(sorted_rs)
ibd_rs = {tk: int((rank / (n_rs - 1)) * 98 + 1) if n_rs > 1 else 50
          for rank, tk in enumerate(sorted_rs)}
print(f"  IBD RS Rating 計算完了: {len(ibd_rs)} 銘柄")

print(f"\n[Screen] {len(TICKERS)} 銘柄処理中...")
results = []
failed = []
try:
    tks = yf.Tickers(" ".join(TICKERS))
except Exception:
    tks = None

for tk in TICKERS:
    try:
        t = tks.tickers.get(tk) if tks else None
        if not t:
            failed.append(tk); continue
        info = t.info or {}

        price = float(info.get("currentPrice") or info.get("regularMarketPrice") or 0)
        mkt_cap = float(info.get("marketCap") or 0)
        if price <= 0:
            failed.append(tk); continue

        avg50 = float(info.get("fiftyDayAverage") or 0)
        avg200 = float(info.get("twoHundredDayAverage") or 0)
        yh52 = float(info.get("fiftyTwoWeekHigh") or 0)
        inst = float(info.get("heldPercentInstitutions") or 0)
        name = info.get("longName") or info.get("shortName") or tk
        sector = info.get("sector") or ""

        def to_pct(v):
            return round(float(v)*100, 1) if v is not None else None

        rev_g = to_pct(info.get("revenueGrowth"))
        earn_qg = to_pct(info.get("earningsQuarterlyGrowth"))
        om = to_pct(info.get("operatingMargins"))
        roe = to_pct(info.get("returnOnEquity"))

        eps_g = earn_qg
        c_pass = eps_g is not None and eps_g >= THRESH["C"]
        s_pass = rev_g is not None and rev_g >= THRESH["S"]
        from_h = round((yh52 - price) / yh52 * 100, 1) if yh52 > 0 else None
        n_pass = from_h is not None and from_h <= 15
        rs = ibd_rs.get(tk, 50)
        l_pass = rs >= THRESH["L"]
        abv50 = avg50 > 0 and price > avg50
        if inst > 0.50 and abv50 and n_pass:
            i_val = "Accumulation"
        elif inst < 0.25 or not abv50:
            i_val = "Distribution"
        else:
            i_val = "Neutral"
        i_pass = (i_val == "Accumulation")

        a_ok, growths = calc_a(tk)

        score = int(sum([c_pass, bool(a_ok), s_pass, n_pass, l_pass, i_pass, M_PASS]))

        sm_s = s_pass
        sm_m = om is not None and THRESH["smMLo"] <= om <= 65
        sm_a = eps_g is not None and eps_g >= THRESH["smA"]
        sm_r = roe is not None and roe >= THRESH["smR"]
        stage2 = avg200 > 0 and price > avg200
        ratio200 = price / avg200 if avg200 > 0 else 0
        excl = []
        if not stage2: excl.append("Stage2未確認")
        if ratio200 >= 2.0: excl.append("除外①2x200MA")
        sm_t = len(excl) == 0
        sm_sc = int(sum([sm_s, sm_m, sm_a, sm_r, sm_t]))
        comb = score + sm_sc

        excluded = ratio200 >= 2.0
        cs_excl = (["除外①2x200MA"] if excluded else []) + MARKET_EXCL

        results.append(dict(
            ticker=tk, name=name, sector=sector,
            price=round(price, 2), mktCap=mkt_cap,
            score=score, smart_score=sm_sc, combined_score=comb,
            C=c_pass, A=bool(a_ok), S=s_pass, N=n_pass, L=l_pass,
            I=i_val, Ipass=i_pass, M=M_PASS,
            smart_S=sm_s, smart_M=sm_m, smart_A=sm_a,
            smart_R=sm_r, smart_T=sm_t,
            epsGrowth=eps_g, salesGrowth=rev_g,
            opMargin=om, roe=roe, rsScore=rs,
            fromHigh=from_h, instPct=round(inst*100, 1),
            stage2=stage2, avg200=round(avg200, 2), avg50=round(avg50, 2),
            epsAnnual3y=growths,
            smart_excl=excl, excluded=excluded, canslim_excl=cs_excl,
        ))
        print(f"  {tk:<6} Sc={score}/7 Sm={sm_sc}/5  EPS={eps_g}  Sales={rev_g}  RS={rs}  52wH-{from_h}%")
    except Exception as e:
        failed.append(tk)
        print(f"  {tk:<6} 失敗: {e}")

print(f"\n完了: 有効={len(results)}  失敗={len(failed)}  ({failed})")

results.sort(key=lambda x: (x["score"], x.get("epsGrowth") or -9999), reverse=True)

payload = dict(
    generatedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    note="REDFORDウォッチリスト単発検証・screening_results.jsonとは別管理",
    marketStatusInherited=prev_mkt.get("status"),
    stocks=results,
    failed=failed,
)
pathlib.Path("watchlist_screen_results.json").write_text(
    json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
print("\nwatchlist_screen_results.json 保存完了")
