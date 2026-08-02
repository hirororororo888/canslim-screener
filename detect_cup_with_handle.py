"""
カップウィズハンドル（Cup with Handle）パターン検出（単発・screening_results.jsonは触らない）

パターン定義（IBD/CANSLIM流）:
  カップ: 左ピーク→12-50%下落→丸みを帯びた底→右側で左ピーク付近まで回復（7-65週）
  ハンドル: カップ右側高値からさらに5-15%程度の浅い調整（1-5週間）、カップ上半分で推移
  現在値: ハンドル高値付近（ブレイクアウト直前 or 直後）
"""
import sys, json, datetime, pathlib, warnings
warnings.filterwarnings("ignore")
import numpy as np
import yfinance as yf

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TICKERS = ['TGTX','DELL','KRYS','LPG','AUB','ADAM','INSW','VLO','RELY','DINO','GEN','ARW','LLY','AMG','KTB',
           'DDOG','MBIN','VIRT','NTRS','TILE','VCTR','STLD','HWM','APH','CXW','OVV','INCY','LTH','RS','ENVA',
           'WDC','TER','STX','COCO','MPWR','AVGO','CINF','CPAY','SEZL','FTNT','LRCX','RNST','AFL','FBK','MU',
           'KALU','PLTR','GOOG','KNSA','SKWD','LQDA','TVTX','GH','CRWD','PANW','NMM','ASTH','DAVE','NTAP','GE',
           'VIK','VRT','EW','KVYO','IONQ','QUBT','RBRK','QBTS']

def smooth(a, w=5):
    if len(a) < w:
        return a
    kernel = np.ones(w) / w
    pad = np.pad(a, (w//2, w - 1 - w//2), mode="edge")
    return np.convolve(pad, kernel, mode="valid")

def find_cup_handle(close, high, low, vol):
    """直近9ヶ月の値動きからカップ+ハンドルを探す。見つかれば dict、なければ None。

    手順:
      1) 直近5日を除いた区間でグローバル最安値=カップ底候補を探す
      2) その底より前の最高値=左ピーク
      3) 底より後の最高値=右肩(ピボット)。右肩が直近数日以内なら「ハンドル未形成」
      4) 右肩より後（=直近）の値動きをハンドルとして深さ・期間を判定
    """
    n = len(close)
    if n < 80:
        return None
    sm = smooth(close, 5)
    lookback = min(n, 190)
    window = sm[-lookback:]
    m = len(window)
    if m < 60:
        return None

    # カップ底候補: 直近5日を除いた区間の最安値
    search_end = m - 5
    bottom_idx = int(np.argmin(window[:search_end]))
    bottom_val = float(window[bottom_idx])

    # 底が全体の前半5%未満(=左ピークを探す余地がない)なら不可
    if bottom_idx < 15:
        return None

    left_peak_idx = int(np.argmax(window[:bottom_idx]))
    left_peak = float(window[left_peak_idx])

    cup_len_days = bottom_idx - left_peak_idx
    if cup_len_days < 12:
        return None

    depth = (left_peak - bottom_val) / left_peak * 100
    if not (8 <= depth <= 55):
        return None

    # 底より後（現在まで）の最高値 = 右肩・ピボット
    right_region = window[bottom_idx:]
    right_peak_rel = int(np.argmax(right_region))
    right_peak_idx = bottom_idx + right_peak_rel
    right_peak_val = float(right_region[right_peak_rel])

    cup_total_days = right_peak_idx - left_peak_idx
    if not (20 <= cup_total_days <= 260):
        return None

    recovery_pct = right_peak_val / left_peak * 100
    if recovery_pct < 80:
        return None

    cur = float(window[-1])
    days_since_peak = (m - 1) - right_peak_idx

    if days_since_peak <= 3:
        # 右肩＝ほぼ現在値。ハンドルはまだ形成されていないカップ完成直後
        cur_from_peak = (right_peak_val - cur) / right_peak_val * 100
        if cur_from_peak <= 3:
            return dict(stage="カップ完成（ハンドル未形成）", depth=round(depth,1),
                        cup_weeks=round(cup_total_days/5,1), handle_pct=None, handle_weeks=None,
                        cur_price=round(float(close[-1]),2), pivot=round(right_peak_val,2),
                        pct_from_pivot=round(-cur_from_peak,1))
        return None

    if days_since_peak < 4:
        return None

    handle_region = window[right_peak_idx:]
    handle_low = float(handle_region.min())
    handle_pct = (right_peak_val - handle_low) / right_peak_val * 100

    # カップ上半分に収まっているか
    upper_half_thresh = bottom_val + (right_peak_val - bottom_val) * 0.5
    if handle_low < upper_half_thresh:
        return None
    if not (2 <= handle_pct <= 20):
        return None

    cur_from_pivot = (right_peak_val - cur) / right_peak_val * 100
    if not (-3 <= cur_from_pivot <= 18):
        return None

    stage = "ブレイクアウト" if cur >= right_peak_val * 0.99 else "ハンドル形成中"

    return dict(stage=stage, depth=round(depth,1), cup_weeks=round(cup_total_days/5,1),
                handle_pct=round(handle_pct,1), handle_weeks=round(days_since_peak/5,1),
                cur_price=round(float(close[-1]),2), pivot=round(right_peak_val,2),
                pct_from_pivot=round(cur_from_pivot,1))

print(f"対象: {len(TICKERS)} 銘柄のチャートパターン検出")
data = yf.download(TICKERS, period="1y", progress=False, auto_adjust=True, group_by="ticker")

hits = []
for tk in TICKERS:
    try:
        h = data[tk] if len(TICKERS) > 1 else data
        h = h.dropna()
        if len(h) < 80:
            continue
        close = h["Close"].values.flatten().astype(float)
        high  = h["High"].values.flatten().astype(float)
        low   = h["Low"].values.flatten().astype(float)
        vol   = h["Volume"].values.flatten().astype(float)
        r = find_cup_handle(close, high, low, vol)
        if r:
            r["ticker"] = tk
            hits.append(r)
            print(f"  {tk:<6} {r['stage']:<16} 深さ{r['depth']:>5}% カップ{r['cup_weeks']:>4}週 "
                  f"ハンドル{r.get('handle_pct','-')}% ピボット${r['pivot']} 現在値${r['cur_price']} (ピボット比{r['pct_from_pivot']:+}%)")
    except Exception as e:
        pass

print(f"\n該当: {len(hits)} / {len(TICKERS)} 銘柄")

payload = dict(
    generatedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    note="カップウィズハンドル検出・単発（screening_results.jsonとは別管理）",
    universe=len(TICKERS),
    hits=hits,
)
pathlib.Path("cup_with_handle_results.json").write_text(
    json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
print("cup_with_handle_results.json 保存完了")
