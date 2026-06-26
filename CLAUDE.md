# CANSLIM / SMART スクリーナー プロジェクト

## 概要
NYSE/NASDAQ の米国株を CANSLIM + SMART + Minervini Trend Template で自動スクリーニングするWebアプリ。

## ファイル構成
- `index.html` — メインUI（ダークテーマ・3タブ切替: CANSLIM/SMART/両方適用）
- `run_full_screen.py` — 1519銘柄フルスクリーニング（S&P500+400+600）
- `canslim_screener.py` — 70銘柄スクリーニング（旧版・速い）
- `fix_a_condition.py` — A条件（年次EPS3年）をyfinanceで補正
- `update_html.py` — screening_results.json → index.html に反映
- `run_screener.bat` — ワンクリック実行（Windows）
- `deploy_github.bat` — GitHub Pages デプロイ
- `sp500_tickers.json` — 1519銘柄リスト（S&P500+400+600）

## データソース
- **Yahoo Finance (yfinance)**: 価格・ファンダメンタル・機関保有（無制限）
- **Alpha Vantage**: 四半期EPS精密値（AV_API_KEY: UMKP1E9TFZV1VNM6、25回/日）
- **FMP MCP**: 一部銘柄の決算データ（FMP_API_KEY: N1HukTVqzFwhSl1tpI13CVJh5cp0I29b）

## スクリーニング実行方法
```bash
# フルスクリーニング（約30分）
python run_full_screen.py

# A条件補正
python fix_a_condition.py

# HTML更新
python update_html.py

# サーバー起動 → http://localhost:5174
python -m http.server 5174 --directory . --bind 0.0.0.0
```

## CANSLIM条件
- C: 四半期EPS成長 ≥25% YoY
- A: 年次EPS 3年連続 ≥25%（yfinance income_stmt で計算）
- N: 52週高値の15%以内
- S: 四半期売上成長 ≥25%
- L: IBD RS Rating ≥70（加重12ヶ月リターンのパーセンタイル）
- I: 機関保有率・50MA位置でAccum/Dist/Neutral判定
- M: IBD公式Confirmed Uptrend（手動入力）またはSPY自動判定

## SMART条件
- S: 売上成長 ≥25%
- M: 営業利益率 25〜65%
- A: EPS加速 ≥30%
- R: ROE ≥20%
- T: Stage2（price>200MA）かつ除外シグナルなし

## 現在の市場状態（最終更新: 2026-06-03）
- IBD: Confirmed Uptrend
- 売抜け日: S&P500=3日 / Nasdaq=3日
- FTD: 2026-05-08確認済み
- 推奨ポジション: 80〜100%

## 除外シグナル
- 除外①: 株価が200日MAの2倍以上（クライマックストップリスク）
- 除外②③: 市場がBearish/Distribution（IBD確認で上書き可）

## GitHub Pages
- リポジトリ: https://github.com/[ユーザー名]/canslim-screener
- URL: https://[ユーザー名].github.io/canslim-screener/
- デプロイ: `deploy_github.bat`

## ngrok（スマホアクセス用）
```
ngrok http 5174 --response-header-add "ngrok-skip-browser-warning:true"
```

## REDFORD自動収集（手動トリガー）
ユーザーが「REDFORD確認して」と言ったら以下を実行:
1. Chrome拡張（mcp__Claude_in_Chrome__）でアクセス
   - browser: deviceId e4ff71ad-9007-4d58-ac38-e0b3e4c41f25（Browser 1）
   - URL: https://x.com/3b4w4aRedford
   - ユーザーは @sannzamenai でログイン済み・REDFORDフォロー中
2. 最新の「REDFORD REPORTS-XXXX」を get_page_text で取得
   - スクロールして固定ポスト下の最新レポートを読む
3. 抽出項目:
   - トレンド評価（Confirmed Uptrend / Uptrend Under Pressure / Market in Correction）
   - 売抜け日（S&P500=X / Nasdaq=X）
   - Put/Call Ratio
   - エントリーポイント突破銘柄・リーディング銘柄
4. screening_results.json の market を更新:
   - Confirmed Uptrend → status="bullish", M全通過
   - Uptrend Under Pressure → status="caution", M全て—
   - Market in Correction → status="bearish", M全て—
   - distributionDdays = Nasdaqの売抜日（厳しい方）
5. python update_html.py → GitHub push
6. REDFORDのセクター情報とスクリーナーを照合して投資戦略を提示

## REDFORD レポート保存先
取得したレポートは redford_reports/REPORTS-XXXX_YYYY-MM-DD.txt に保存（履歴蓄積）

## Put/Call Ratio 判定基準（REDFORD/IBD）
- 0.7以下: 強気
- 0.7-0.79: やや強気
- 0.8-0.89: 中立〜弱気
- 0.9以上: 下落リスクかなり高い
- 1.0以上: 「これじゃダメじゃん」レベル（最大警戒）

## 売抜け日（Distribution Days）基準
- 6〜7回でマーケット下落に向かう
- Confirmed Uptrend: DD 0-5
- Under Pressure: DD 5-8 + 株価軟調
- Market in Correction: DD 6超 + 主要指数MA割れ
