"""
minervini_history.py — Mark Minervini (@markminervini) の投稿を2軸で蓄積
  ① アクションログ: 売買銘柄（added/sold/trimmed $TICKER）→ 売買シグナル
  ② 知識ベース: トレード哲学・教訓 → SKILL.md的な知恵の蓄積

使い方:
  python minervini_history.py actions   # 銘柄アクション履歴を表示
  python minervini_history.py wisdom    # 蓄積した知恵を表示
（追加は通常 Claude が Chrome 取得 → add_post() 経由で行う）
"""
import json, re, sys, datetime, pathlib

ROOT     = pathlib.Path(__file__).parent
POST_DIR = ROOT / "minervini_posts"
ACTIONS  = ROOT / "minervini_actions.json"
WISDOM   = ROOT / "minervini_wisdom.md"
POST_DIR.mkdir(exist_ok=True)

# 売買アクションの検出パターン（日本語訳・英語両対応）
ACTION_PATTERNS = [
    (r"(追加しました|added|adding|bought|buying|started)", "buy"),
    (r"(売却しました|売りました|sold|selling|trimmed|trimming|reduced)", "sell"),
    (r"(全部売|exited|closed|stopped out)", "exit"),
]

def extract_tickers(text):
    """$TICKER 形式のティッカーを抽出"""
    return list(dict.fromkeys(re.findall(r"\$([A-Z]{1,5})\b", text)))

def detect_action(text):
    for pat, act in ACTION_PATTERNS:
        if re.search(pat, text, re.IGNORECASE):
            return act
    return None

def add_post(text, date=None, post_id=None):
    """投稿を解析し、アクション/知恵に振り分けて保存"""
    date = date or datetime.date.today().isoformat()
    post_id = post_id or datetime.datetime.now().strftime("%H%M%S")

    # 原文保存
    fname = POST_DIR / f"{date}_{post_id}.txt"
    fname.write_text(text, encoding="utf-8")

    tickers = extract_tickers(text)
    action  = detect_action(text)

    result = {"type": None}

    # ① 銘柄アクション（ティッカー＋売買動詞あり）
    if tickers and action:
        actions = load_actions()
        for tk in tickers:
            entry = {"date": date, "ticker": tk, "action": action,
                     "text": text[:200], "post_id": post_id}
            # 重複除去（同日同銘柄同アクション）
            actions = [a for a in actions
                       if not (a["date"]==date and a["ticker"]==tk and a["action"]==action)]
            actions.append(entry)
        actions.sort(key=lambda x: x["date"])
        ACTIONS.write_text(json.dumps(actions, ensure_ascii=False, indent=2), encoding="utf-8")
        result = {"type": "action", "tickers": tickers, "action": action}

    # ② 知恵・哲学（ティッカーアクションでない投稿で、宣伝でないもの）
    elif not _is_promo(text):
        _append_wisdom(date, text)
        result = {"type": "wisdom"}
    else:
        result = {"type": "promo（スキップ）"}

    return result

def _is_promo(text):
    """宣伝投稿の判定（Private Access等の勧誘）"""
    promo = ["minervini.com", "Private Access", "本日参加", "join today",
             "メンバーシップ", "subscribe"]
    return sum(1 for p in promo if p.lower() in text.lower()) >= 2

def _append_wisdom(date, text):
    """知恵をmarkdownに追記"""
    if not WISDOM.exists():
        WISDOM.write_text("# Mark Minervini トレード知識ベース\n\n"
                          "Minerviniの哲学・教訓を蓄積。Checker/SKILLの判断材料。\n\n",
                          encoding="utf-8")
    body = WISDOM.read_text(encoding="utf-8")
    # 重複チェック（同じ冒頭40字があればスキップ）
    snippet = text[:40]
    if snippet in body:
        return
    entry = f"## {date}\n{text.strip()}\n\n"
    WISDOM.write_text(body + entry, encoding="utf-8")

def load_actions():
    if ACTIONS.exists():
        return json.loads(ACTIONS.read_text(encoding="utf-8"))
    return []

def show_actions():
    actions = load_actions()
    if not actions:
        print("アクション履歴なし"); return
    print("="*60)
    print("  Mark Minervini 売買アクション履歴")
    print("="*60)
    print(f"{'日付':<12} {'動作':<6} {'銘柄':<6}")
    print("-"*60)
    icon = {"buy":"🟢買い","sell":"🔴売り","exit":"❌手仕舞"}
    for a in actions:
        print(f"{a['date']:<12} {icon.get(a['action'],a['action']):<6} ${a['ticker']}")
    # 現在の推定保有（buy-sell相殺）
    print("\n  --- 推定アクティブ銘柄（直近buy未売却）---")
    held = {}
    for a in actions:
        if a["action"]=="buy": held[a["ticker"]] = a["date"]
        elif a["action"] in ("sell","exit"): held.pop(a["ticker"], None)
    for tk, dt in held.items():
        print(f"  🟢 ${tk}（{dt}に追加）")

def show_wisdom():
    if WISDOM.exists():
        print(WISDOM.read_text(encoding="utf-8"))
    else:
        print("知識ベースなし")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "actions"
    if cmd == "actions": show_actions()
    elif cmd == "wisdom": show_wisdom()
