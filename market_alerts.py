"""
market_alerts.py — 市場全体の通知判定（クラウドルーティンから毎朝実行）

株価データ(yfinance)だけで、IBD流の以下を近似判定し、新しく成立したものだけ
標準出力に「NOTIFY|メッセージ」として出す（通知そのものはルーティン側が行う）。
  - 売り抜け日(Distribution Day)の増減（S&P500 / ナスダック総合）
  - フォロースルーデイ(FTD)候補
  - QQQの200日線割れ/回復
  - QQQ月足ルール（月末に陰線なら1株購入の日）
  - QQQ 52週高値から-10% / -20%（ナンピン補強ルール）
最後に「GATE|buy_allowed=...」で、買い通知を出してよい相場かを返す。
状態は pivot_alerts_state.json の "_market" に保存（同じ通知を繰り返さない）。
使い方: python market_alerts.py [--dry]   (--dry は状態を保存しない)
"""
import json
import sys
import warnings
from pathlib import Path

import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore")
ROOT = Path(__file__).parent
STATE = ROOT / "pivot_alerts_state.json"
RESULTS = ROOT / "screening_results.json"
DRY = "--dry" in sys.argv

INDEXES = {"S&P500": "^GSPC", "ナスダック総合": "^IXIC"}


def load(sym, period="1y"):
    h = yf.Ticker(sym).history(period=period, auto_adjust=False)
    return h.dropna(subset=["Close"])


def distribution_days(h, window=25):
    """直近window営業日で、前日比-0.2%以下かつ出来高が前日より多い日の数。"""
    chg = h["Close"].pct_change()
    vol_up = h["Volume"] > h["Volume"].shift(1)
    dd = (chg <= -0.002) & vol_up
    return int(dd.tail(window).sum())


def follow_through(h, look=15):
    """直近look営業日以内のFTD候補を返す: (日付, 上昇率%) か None。
    直近60日の最安値の翌営業日以降を反発試行とし、4日目以降に+1.25%以上かつ出来高増。
    反発試行中に最安値を割ったら無効。"""
    c, v = h["Close"], h["Volume"]
    seg = c.tail(60)
    low_i = seg.idxmin()
    after = c[c.index > low_i]
    if len(after) < 4:
        return None
    # 反発試行の1日目 = 最安値の後、最初に前日比プラスで引けた日
    day1 = None
    for i, d in enumerate(after.index):
        prev = c.shift(1).loc[d]
        if after.loc[d] > prev:
            day1 = i
            break
    if day1 is None:
        return None
    low_val = c.loc[low_i]
    for j in range(day1 + 3, len(after)):  # 4日目 = day1 + 3
        d = after.index[j]
        if after.iloc[: j + 1].min() < low_val:
            return None  # 最安値割れで無効
        gain = after.iloc[j] / after.iloc[j - 1] - 1
        if gain >= 0.0125 and v.loc[d] > v.shift(1).loc[d]:
            if (len(c) - 1 - c.index.get_loc(d)) <= look:
                return d.strftime("%Y-%m-%d"), round(gain * 100, 2)
    return None


def main():
    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
    ms = state.setdefault("_market", {})
    msgs = []

    # ---- 売り抜け日 / FTD ----
    dd_now = {}
    for name, sym in INDEXES.items():
        h = load(sym)
        n = distribution_days(h)
        dd_now[name] = n
        last = ms.get("dd_level", {}).get(name, 0)
        if n >= 6 and last < 6:
            msgs.append(f"{name}の売り抜け日(直近25日)が{n}に到達。7以上は下落リスク大、新規買いは控える局面です。")
        elif n <= 4 and last >= 6:
            msgs.append(f"{name}の売り抜け日が{n}まで減少。回復の兆し。REDFORDのトレンド格上げを確認してください。")
        ms.setdefault("dd_level", {})[name] = n

        ft = follow_through(h)
        if ft and ft[0] not in ms.get("ftd_seen", []):
            msgs.append(f"{name}でフォロースルーデイ候補({ft[0]}、+{ft[1]}%、出来高増)。"
                        f"REDFORDがConfirmed up trendに格上げしたか確認し、買いを検討する局面です。")
            ms.setdefault("ftd_seen", []).append(ft[0])

    # ---- QQQ ----
    q = load("QQQ", "1y")
    qc = q["Close"]
    last_c = float(qc.iloc[-1])
    ma200 = float(qc.tail(200).mean())
    below = last_c < ma200
    if below and not ms.get("qqq_below200", False):
        msgs.append(f"QQQが200日線(${ma200:.0f})を割りました(${last_c:.2f})。守りを強める局面です。")
    elif (not below) and ms.get("qqq_below200", False):
        msgs.append(f"QQQが200日線(${ma200:.0f})を回復しました(${last_c:.2f})。回復の兆しです。")
    ms["qqq_below200"] = bool(below)

    hi = float(qc.max())
    dd_hi = (1 - last_c / hi) * 100
    for lvl, key in ((10, "nanpin10"), (20, "nanpin20")):
        if dd_hi >= lvl and not ms.get(key, False):
            msgs.append(f"QQQが52週高値から-{lvl}%に到達(${last_c:.2f}、高値${hi:.2f})。"
                        f"ナンピン補強ルール(余力の{40 if lvl==10 else 60}%で買い増し)の対象です。")
            ms[key] = True
        if dd_hi < 5:
            ms[key] = False

    # 月足ルール: 今日が月内の最終営業日で、月足が陰線
    today = qc.index[-1]
    nxt = today + pd.offsets.BDay(1)
    if nxt.month != today.month:
        mkey = today.strftime("%Y-%m")
        month_open = float(q["Open"][q.index.strftime("%Y-%m") == mkey].iloc[0])
        if last_c < month_open and ms.get("month_alert") != mkey:
            msgs.append(f"QQQの{today.month}月足が陰線(始値${month_open:.2f}>終値${last_c:.2f})。"
                        f"月足ルールで1株購入の日です。")
            ms["month_alert"] = mkey

    # ---- 相場ゲート（買い通知を出してよいか）----
    status = "unknown"
    if RESULTS.exists():
        try:
            status = json.loads(RESULTS.read_text(encoding="utf-8"))["market"]["status"]
        except Exception:
            pass
    auto_bad = max(dd_now.values()) >= 6 or below
    allowed = (status == "bullish") and not auto_bad
    reason = f"market.status={status}, 売り抜け日={dd_now}, QQQ200日線{'割れ' if below else '上'}"

    for m in msgs:
        print("NOTIFY|" + m)
    print(f"GATE|buy_allowed={str(allowed).lower()}|{reason}")

    if not DRY and (msgs or True):
        STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
