"""
redford_history.py — REDFORDレポートの履歴蓄積・トレンド推移管理
使い方:
  python redford_history.py add      # 新規レポートを対話追加（通常はClaude経由）
  python redford_history.py trend    # トレンド推移を表示
  python redford_history.py json     # history.json を更新（HTMLグラフ用）
"""
import json, re, sys, datetime, pathlib

ROOT    = pathlib.Path(__file__).parent
REP_DIR = ROOT / "redford_reports"
HIST    = ROOT / "redford_history.json"
REP_DIR.mkdir(exist_ok=True)

# トレンド評価のスコア化（可視化用）
TREND_SCORE = {
    "confirmed":   3,   # Confirmed Uptrend
    "pressure":    2,   # Uptrend Under Pressure
    "correction":  1,   # Market in Correction
    "uncertain":   0,   # Trend Uncertain
}
TREND_LABEL = {
    3:"Confirmed Uptrend", 2:"Uptrend Under Pressure",
    1:"Market in Correction", 0:"Trend Uncertain"
}

def parse_report(text):
    """REDFORDレポートテキストから主要指標を抽出"""
    d = {}
    # レポート番号
    m = re.search(r"REPORTS?-(\d+)", text)
    d["report_no"] = m.group(1) if m else "?"
    # 日付
    m = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", text)
    if m:
        d["date"] = f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    else:
        d["date"] = datetime.date.today().isoformat()
    # トレンド評価
    t = text.lower()
    if "confirmed" in t and "up" in t:
        d["trend"] = "confirmed"
    elif "under pressure" in t or "under" in t:
        d["trend"] = "pressure"
    elif "correction" in t:
        d["trend"] = "correction"
    else:
        d["trend"] = "uncertain"
    d["trend_score"] = TREND_SCORE[d["trend"]]
    d["trend_label"] = TREND_LABEL[d["trend_score"]]
    # 売抜け日
    m = re.search(r"S&P\s*500\s*[=:：]\s*(\d+)", text)
    d["dd_sp500"] = int(m.group(1)) if m else None
    m = re.search(r"Nasdaq\s*[=:：]\s*(\d+)", text)
    d["dd_nasdaq"] = int(m.group(1)) if m else None
    # Put/Call
    m = re.search(r"Put\s*Call\s*Ratio\s*[=:：]\s*([\d.]+)", text)
    d["put_call"] = float(m.group(1)) if m else None
    # 推奨ポジション
    m = re.search(r"現物株\s*([\d]+)%?\s*[~〜-]\s*([\d]+)%", text)
    if m:
        d["equity_low"]  = int(m.group(1))
        d["equity_high"] = int(m.group(2))
    return d

def add_report(text):
    """レポートを保存し履歴に追加"""
    d = parse_report(text)
    # テキスト保存
    fname = REP_DIR / f"REPORTS-{d['report_no']}_{d['date']}.txt"
    fname.write_text(text, encoding="utf-8")
    # 履歴JSON更新
    history = load_history()
    # 同じレポート番号があれば更新、なければ追加
    history = [h for h in history if h.get("report_no") != d["report_no"]]
    history.append(d)
    history.sort(key=lambda x: (x.get("date",""), x.get("report_no","")))
    HIST.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"保存: {fname.name}")
    print(f"  トレンド: {d['trend_label']}")
    print(f"  売抜日: SP500={d['dd_sp500']} / Nasdaq={d['dd_nasdaq']}")
    print(f"  Put/Call: {d['put_call']}")
    return d

def load_history():
    if HIST.exists():
        return json.loads(HIST.read_text(encoding="utf-8"))
    return []

def show_trend():
    history = load_history()
    if not history:
        print("履歴がありません")
        return
    print("="*78)
    print("  REDFORD トレンド推移履歴")
    print("="*78)
    print(f"{'日付':<12} {'No':>5} {'トレンド':<22} {'SP500':>5} {'NQ':>4} {'P/C':>5} 推奨株%")
    print("-"*78)
    for h in history:
        pc = h.get("put_call")
        pc_mark = ""
        if pc is not None:
            if pc >= 1.0: pc_mark="❌"
            elif pc >= 0.9: pc_mark="⚠"
            elif pc <= 0.7: pc_mark="○"
        eq = f"{h.get('equity_low','?')}-{h.get('equity_high','?')}%" if h.get('equity_low') else "—"
        tr_icon = {"confirmed":"🟢","pressure":"🟡","correction":"🔴","uncertain":"⚪"}.get(h["trend"],"")
        print(f"{h['date']:<12} {h['report_no']:>5} {tr_icon}{h['trend_label']:<20} "
              f"{str(h.get('dd_sp500','-')):>5} {str(h.get('dd_nasdaq','-')):>4} "
              f"{str(pc)+pc_mark if pc else '-':>6} {eq}")
    # 変化サマリー
    if len(history) >= 2:
        prev, cur = history[-2], history[-1]
        print("\n--- 直近の変化 ---")
        if cur["trend_score"] < prev["trend_score"]:
            print(f"  ⚠️ トレンド悪化: {prev['trend_label']} → {cur['trend_label']}")
        elif cur["trend_score"] > prev["trend_score"]:
            print(f"  ✅ トレンド改善: {prev['trend_label']} → {cur['trend_label']}")
        else:
            print(f"  → トレンド維持: {cur['trend_label']}")
        if cur.get("put_call") and prev.get("put_call"):
            diff = cur["put_call"] - prev["put_call"]
            print(f"  Put/Call: {prev['put_call']} → {cur['put_call']} ({diff:+.2f})")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "trend"
    if cmd == "add":
        text = sys.stdin.read()
        add_report(text)
    elif cmd == "trend":
        show_trend()
    elif cmd == "json":
        show_trend()
