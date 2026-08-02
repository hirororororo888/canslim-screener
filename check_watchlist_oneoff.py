"""
watchlist_screen_results.json の銘柄をChecker検証（単発・screening_results.jsonは触らない）
"""
import sys, json, datetime, pathlib, warnings
warnings.filterwarnings("ignore")
import yfinance as yf
from checker import verify_stock

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = pathlib.Path(__file__).parent
f = ROOT / "watchlist_screen_results.json"
data = json.loads(f.read_text(encoding="utf-8"))
market_status = data.get("marketStatusInherited", "bearish")

print(f"CHECKER 独立検証（ウォッチリスト単発・市場:{market_status}）")
print("-"*78)

tickers = [s["ticker"] for s in data["stocks"]]
all_hist = yf.download(tickers, period="2y", progress=False, auto_adjust=True, group_by="ticker")

def get_hist(tk):
    try:
        if len(tickers) == 1:
            return all_hist
        return all_hist[tk]
    except Exception:
        return None

stats = {"verified":0, "caution":0, "reject":0}
for s in data["stocks"]:
    v = verify_stock(s, market_status, get_hist(s["ticker"]))
    if v is None:
        s["checker_verdict"] = "unknown"
        continue
    s["checker_verdict"] = v["verdict"]
    s["checker_gates"] = f"{v['gates_passed']}/{v['gates_total']}"
    s["checker_failed"] = v["failed_gates"]
    s["checker_volRatio"] = v["vol_ratio"]
    s["checker_atr"] = v["atr_pct"]
    stats[v["verdict"]] += 1
    icon = {"verified":"検証済み","caution":"要注意","reject":"却下"}[v["verdict"]]
    print(f"{s['ticker']:<6} {icon:<6} {v['gates_passed']}/6  出来高{v['vol_ratio']}x  50MA比{v['from_50ma']:+.1f}%  失敗:{'/'.join(v['failed_gates']) or '—'}")

data["checkerRun"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
data["checkerStats"] = stats
f.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print("-"*78)
print(f"検証済み:{stats['verified']} 要注意:{stats['caution']} 却下:{stats['reject']}")
