"""
checker.py — 独立検証エージェント（Maker-Checkerパターン）
論文 "Loop Engineering" のChecker原則を実装:
  「生成者（スクリーナー）は最悪の判定者」
  → CANSLIM/SMARTとは独立した観点で各候補を再検証し、
    だましブレイク・偽シグナルを弾く

使い方: python checker.py
  screening_results.json の各銘柄に checker_verdict を付与して上書き
"""
import json, datetime, pathlib, warnings
warnings.filterwarnings("ignore")
import yfinance as yf
import numpy as np

ROOT = pathlib.Path(__file__).parent

# REDFORD堅調セクター（市場下落時の逃避先）
STRONG_SECTORS = ["Healthcare", "Energy", "Financial Services",
                  "Consumer Defensive", "Utilities"]

def verify_stock(s, market_status):
    """1銘柄を独立検証。6つのハードゲートを適用し合否を返す。"""
    tk = s["ticker"]
    try:
        hist = yf.download(tk, period="6mo", progress=False, auto_adjust=True)
        if hist.empty or len(hist) < 50:
            return None
        closes = hist["Close"].values.flatten().astype(float)
        vols   = hist["Volume"].values.flatten().astype(float)
        highs  = hist["High"].values.flatten().astype(float)
        n = len(closes)

        price   = float(closes[-1])
        ma21    = float(closes[-21:].mean())
        ma50    = float(closes[-50:].mean())
        ma200   = float(closes[-200:].mean()) if n >= 200 else float(closes.mean())
        vol5    = float(vols[-5:].mean())
        vol50   = float(vols[-50:].mean())
        hi52    = float(max(highs[-252:])) if n >= 252 else float(max(highs))
        # ATR%（ボラティリティ）
        tr = np.maximum(highs[-14:] - closes[-14:],
                        np.abs(highs[-14:] - np.roll(closes, 1)[-14:]))
        atr_pct = float(np.mean(tr) / price * 100)

        sector  = s.get("sector", "")
        rs      = s.get("rsScore", 50)
        from_h  = (hi52 - price) / hi52 * 100
        from_50 = (price / ma50 - 1) * 100
        ratio200 = price / ma200 if ma200 > 0 else 0
        vol_ratio = vol5 / vol50 if vol50 > 0 else 0

        # ── 6つの独立検証ゲート ────────────────────────────────────
        gates = {}
        # G1 出来高の裏付け（買い集めの実在）: 5日平均 >= 50日平均×0.9
        gates["G1_出来高"] = vol_ratio >= 0.90
        # G2 トレンド健全性: 21MA上 かつ 50MA上（だましでない真の上昇）
        gates["G2_トレンド"] = price > ma21 and price > ma50
        # G3 非クライマックス: 200MAの2倍未満（吹き上げ天井回避）
        gates["G3_非過熱"] = ratio200 < 2.0
        # G4 非過延長: 50MAから+15%以内（ベースから離れすぎていない）
        gates["G4_適正位置"] = from_50 <= 15.0
        # G5 リーダーシップ: 堅調セクター or RS>=85
        gates["G5_主導力"] = sector in STRONG_SECTORS or rs >= 85
        # G6 真の高値圏: 52週高値の8%以内（本物の新高値候補）
        gates["G6_高値圏"] = from_h <= 8.0

        passed = sum(gates.values())

        # ── 判定（市場状況で基準を調整）────────────────────────────
        # Under Pressure / Correction では基準を厳格化
        strict = market_status in ("caution", "bearish")
        if strict:
            # 厳格モード: G5(主導力)必須 + 5ゲート以上で「検証済み」
            if passed >= 5 and gates["G5_主導力"] and gates["G2_トレンド"]:
                verdict = "verified"
            elif passed >= 4:
                verdict = "caution"
            else:
                verdict = "reject"
        else:
            # 通常モード
            if passed >= 5:
                verdict = "verified"
            elif passed >= 3:
                verdict = "caution"
            else:
                verdict = "reject"

        # 失敗ゲートのリスト
        failed = [k.split("_")[1] for k, v in gates.items() if not v]

        return dict(
            verdict=verdict, gates_passed=passed, gates_total=6,
            failed_gates=failed,
            vol_ratio=round(vol_ratio, 2), from_50ma=round(from_50, 1),
            ratio_200=round(ratio200, 2), atr_pct=round(atr_pct, 1),
        )
    except Exception:
        return None

def main():
    f = ROOT / "screening_results.json"
    if not f.exists():
        print("ERROR: screening_results.json がありません")
        return
    data = json.loads(f.read_text(encoding="utf-8"))
    market_status = data.get("market", {}).get("status", "caution")

    print("="*78)
    print(f"  CHECKER 独立検証（市場: {market_status.upper()}）")
    print(f"  {'厳格モード（Under Pressure）' if market_status in ('caution','bearish') else '通常モード'}")
    print("="*78)
    print(f"{'銘柄':<6} {'判定':<10} {'ゲート':>6} {'出来高比':>7} {'50MA比':>7} 失敗ゲート")
    print("-"*78)

    stats = {"verified":0, "caution":0, "reject":0}
    for s in data["stocks"]:
        v = verify_stock(s, market_status)
        if v is None:
            s["checker_verdict"] = "unknown"
            continue
        s["checker_verdict"]    = v["verdict"]
        s["checker_gates"]      = f"{v['gates_passed']}/{v['gates_total']}"
        s["checker_failed"]     = v["failed_gates"]
        s["checker_volRatio"]   = v["vol_ratio"]
        s["checker_atr"]        = v["atr_pct"]
        stats[v["verdict"]] += 1

        icon = {"verified":"✅検証済み","caution":"⚠️要注意","reject":"❌却下"}[v["verdict"]]
        print(f"{s['ticker']:<6} {icon:<10} {v['gates_passed']}/{v['gates_total']:<4} "
              f"{v['vol_ratio']:>6}x {v['from_50ma']:>+6.1f}%  {'/'.join(v['failed_gates']) or '—'}")

    data["meta"]["checkerRun"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    data["meta"]["checkerStats"] = stats
    f.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print("-"*78)
    print(f"  ✅検証済み: {stats['verified']}  ⚠️要注意: {stats['caution']}  ❌却下: {stats['reject']}")
    print(f"\n  論文の原則: 「却下率が低い＝検証が甘い」サイン")
    print(f"  却下率: {stats['reject']/max(1,sum(stats.values()))*100:.0f}%（論文目安40-60%）")

if __name__ == "__main__":
    main()
