import sys, json, yfinance as yf, numpy as np
from datetime import datetime, timezone

# Windowsコンソール(cp932)でも特殊文字で落ちないようUTF-8出力に固定
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

with open("screening_results.json", encoding="utf-8") as f:
    data = json.load(f)

THRESH_A = 25.0

def calc_a(tk):
    try:
        inc = yf.Ticker(tk).income_stmt
        if inc is None or inc.empty:
            return False, []
        eps_vals = []
        for row in ["Diluted EPS","Basic EPS","EPS"]:
            if row in inc.index:
                eps_vals = [float(v) for v in inc.loc[row].values
                            if v is not None and not np.isnan(float(v))]
                break
        if len(eps_vals) < 4:
            return False, []
        growths, a_pass = [], True
        for i in range(3):
            cur, prv = eps_vals[i], eps_vals[i+1]
            if prv < 0 and cur > 0:
                growths.append(999); continue
            if prv <= 0:
                a_pass = False; growths.append(None); continue
            g = (cur - prv) / abs(prv) * 100
            growths.append(round(g,1))
            if g < THRESH_A: a_pass = False
        return a_pass, growths
    except:
        return False, []

print(f"{'銘柄':<6}  旧A  新A  3年成長率")
print("-"*55)
changed = 0
for s in data["stocks"]:
    tk = s["ticker"]
    old_a = bool(s.get("A", False))
    new_a, growths = calc_a(tk)
    g_str = " / ".join([
        f"{g:+.0f}%" if g and g!=999 else ("黒転" if g==999 else "--")
        for g in growths
    ]) if growths else "--"
    mark = "★" if new_a != old_a else " "
    print(f"{mark}{tk:<6}  {'ok' if old_a else '--'}  {'ok' if new_a else '--'}  [{g_str}]")
    if new_a != old_a: changed += 1
    s["A"] = bool(new_a)
    s["score"] = int(sum([bool(s.get(k)) for k in ["C","A","S","N","L","Ipass","M"]]))
    s["combined_score"] = s["score"] + s.get("smart_score", 0)

print(f"\nA条件変化: {changed}件")
data["meta"]["updatedAt"] = datetime.now(timezone.utc).isoformat()
with open("screening_results.json","w",encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print("保存完了")
