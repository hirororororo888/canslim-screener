"""
カップウィズハンドル検出・フルスクリーニング残り銘柄版（単発、screening_results.jsonは触らない）
detect_cup_with_handle.py と同じロジックをremaining_tickers.json(1464銘柄)に適用。
バッチ分割でダウンロードし、進捗を逐次出力・保存する。
"""
import sys, json, datetime, pathlib, warnings, time
warnings.filterwarnings("ignore")
import numpy as np
import yfinance as yf

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BATCH = 150

with open("remaining_tickers.json", encoding="utf-8") as f:
    TICKERS = json.load(f)
print(f"対象: {len(TICKERS)} 銘柄（フルスクリーニング残り・カップウィズハンドル検出）")

def smooth(a, w=5):
    if len(a) < w:
        return a
    kernel = np.ones(w) / w
    pad = np.pad(a, (w//2, w - 1 - w//2), mode="edge")
    return np.convolve(pad, kernel, mode="valid")

def find_cup_handle(close):
    n = len(close)
    if n < 80:
        return None
    sm = smooth(close, 5)
    lookback = min(n, 190)
    window = sm[-lookback:]
    m = len(window)
    if m < 60:
        return None

    search_end = m - 5
    bottom_idx = int(np.argmin(window[:search_end]))
    bottom_val = float(window[bottom_idx])
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

hits = []
failed = []
t0 = time.time()
for bi in range(0, len(TICKERS), BATCH):
    batch = TICKERS[bi:bi+BATCH]
    try:
        data = yf.download(batch, period="1y", progress=False, auto_adjust=True, group_by="ticker", threads=True)
    except Exception as e:
        failed.extend(batch)
        continue

    for tk in batch:
        try:
            h = data[tk] if len(batch) > 1 else data
            h = h.dropna()
            if len(h) < 80:
                continue
            close = h["Close"].values.flatten().astype(float)
            r = find_cup_handle(close)
            if r:
                r["ticker"] = tk
                hits.append(r)
        except Exception:
            failed.append(tk)

    elapsed = time.time() - t0
    done = min(bi+BATCH, len(TICKERS))
    print(f"[{done}/{len(TICKERS)}] 経過{elapsed:.0f}秒  該当{len(hits)}件  失敗{len(failed)}件")

    # 途中経過を都度保存（長時間実行の保険）
    payload = dict(
        generatedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        note="フルスクリーニング残り銘柄のカップウィズハンドル検出・単発",
        universe=len(TICKERS), processed=done,
        hits=sorted(hits, key=lambda x: (x["stage"]!="ブレイクアウト", abs(x.get("pct_from_pivot",99)))),
        failed=failed,
    )
    pathlib.Path("cup_with_handle_full_results.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"\n完了: 該当 {len(hits)} / {len(TICKERS)} 銘柄  失敗 {len(failed)}件  総時間{time.time()-t0:.0f}秒")
print("cup_with_handle_full_results.json 保存完了")
