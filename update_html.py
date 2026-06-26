"""
update_html.py — screening_results.json → index.html の loadData() を自動更新
Usage: python update_html.py
"""
import json, re, pathlib

ROOT      = pathlib.Path(__file__).parent
JSON_FILE = ROOT / "screening_results.json"
HTML_FILE = ROOT / "index.html"

def normalize(obj):
    """numpy bool_ などを Python ネイティブ型に変換"""
    if isinstance(obj, dict):  return {k: normalize(v) for k, v in obj.items()}
    if isinstance(obj, list):  return [normalize(v) for v in obj]
    if type(obj).__name__ in ('bool_', 'bool8'): return bool(obj)
    if type(obj).__name__ in ('int64','int32'):  return int(obj)
    if type(obj).__name__ in ('float64','float32') and str(obj) not in ('nan','inf'): return float(obj)
    return obj

def main():
    if not JSON_FILE.exists():
        print("ERROR: screening_results.json not found. Run canslim_screener.py first.")
        return

    with open(JSON_FILE, encoding="utf-8") as f:
        data = normalize(json.load(f))

    # REDFORD履歴を埋め込み
    hist_file = ROOT / "redford_history.json"
    if hist_file.exists():
        try:
            data["redfordHistory"] = json.loads(hist_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    js_block = (
        f"// ── Auto-updated: {data['meta']['updatedAt']} ──\n"
        f"loadData({json.dumps(data, ensure_ascii=False, indent=2)});"
    )

    html = HTML_FILE.read_text(encoding="utf-8")

    # すべての既存 loadData({...}); ブロックを削除（複数混入対策）
    # script タグ外の loadData( を対象にする
    html_clean = re.sub(
        r'//[^\n]*Auto-updated[^\n]*\n|//[^\n]*INIT[^\n]*\n',
        '', html
    )
    # 関数定義でない loadData({ を含むブロックを全削除
    html_clean = re.sub(
        r'(?<!function )loadData\(\{[\s\S]*?\}\);',
        '', html_clean
    )

    # </script> の直前（最後の </script>）にデータを挿入
    # HTMLの最後の </script></body></html> の前に挿入
    INSERT_MARKER = "</script>\n\n</body>\n</html>"
    if INSERT_MARKER in html_clean:
        new_html = html_clean.replace(
            INSERT_MARKER,
            f"\n{js_block}\n" + INSERT_MARKER
        )
    else:
        # フォールバック: </body> の直前
        new_html = html_clean.replace(
            "</body>",
            f"<script>\n{js_block}\n</script>\n</body>"
        )

    HTML_FILE.write_text(new_html, encoding="utf-8")

    meta   = data.get("meta", {})
    stocks = data.get("stocks", [])
    c4plus = sum(1 for s in stocks if s.get("score",0) >= 4)
    sm3plus= sum(1 for s in stocks if s.get("smart_score",0) >= 3)
    rs80   = [s["ticker"] for s in stocks if (s.get("rsScore") or 0) >= 80]

    print(f"OK  index.html updated")
    print(f"    Screened    : {meta.get('screened')} stocks")
    print(f"    CANSLIM 4+  : {c4plus} stocks")
    print(f"    SMART 3+    : {sm3plus} stocks")
    print(f"    IBD RS 80+  : {', '.join(rs80)}")
    print(f"    Updated     : {meta.get('updatedAt')}")

if __name__ == "__main__":
    main()
