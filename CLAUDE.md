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
- `redford_watchlist.json` — REDFORDの「Watch listを作成しよう」等で紹介した銘柄の記録。トレンドがConfirmed Uptrendに転換した際のリーダー銘柄候補。REDFORD確認時にウォッチリスト系の投稿（個別銘柄解説）があれば追記する

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

## 現在の市場状態（最終更新: 2026-08-08）
- **REDFORD REPORTS-1782（8/8 7:45）: トレンド評価がMarket in CorrectionからUp trend under pressure（下落リスクのある上昇相場・利確/売却段階の位置づけ）に転換継続**。推奨ポジションは現物株60-80%/キャッシュ20-40%までさらに引き上げ。Put/Call Ratio 0.86（前日値0.88から改善）。エントリー突破銘柄: CRSR/GRDN/WTW。接近銘柄8件
- **重要: 正式な「フォロースルーデイ」自体は8/5のREPORTS-1773で不成立と判定された**（ナスダック+2.59%だったが出来高が伴わず）。それでもIBDのシステム全体としては8/5のREPORTS-1770時点でトレンド評価をUp trend under pressureへ切り替え、以降ポジション推奨を段階的に引き上げ続けている（8/4:20-40% → 8/5-6:40-60% → 8/7-8:60-80%）。「FTD不成立」と「トレンド格上げ」が同時に起きている点は要注意（REDFORD本人も偽のFTDパターンへの警戒を表明）
- REDFORD REPORTS-1779（8/7 9:56）: Watch list推奨済みのATIが決算受けて+8.93%急騰。Q2売上+10.6%・営業利益+36.6%・営業利益率17.4%(前年14.1%)、EPS1.09ドル(前年0.70ドル)。総合評価96・RS98
- **REDFORD REPORTS-1780（8/7 14:31、Watch listを作成しよう第30回）: DELLを新規ウォッチ銘柄として紹介**。NVDA/MSFT/AMDとのパートナーシップが追い風、2026年度予想は売上+51%・EPS+79%、RS99。エントリーポイント469.47を8/4に突破後、8/6-7と続落5.41%安も21日移動平均線で支持。アナリスト目標株価470.78ドル(+7.57%、最高550ドル)。redford_watchlist.jsonに追加済み
- REDFORD REPORTS-1781（8/7 23:42）: PLTR決算好調で+8.5%急騰。BofAが「買い」格上げ・目標株価255ドル（コンセンサス197ドルに対し51%上昇余地）
- REDFORD REPORTS-1774/1775（8/6）: トレンド評価Up trend under pressure継続、推奨ポジション40-60%、Put/Call 0.88→0.80。エントリー突破銘柄TVTX/LNVGY/YOU
- **Minervini（8/4-8/5）: $SPYショートヘッジを解消（半分が前日、残り半分が翌朝ストップアウト、損失は一桁台前半の低め）、同日ロング側で銘柄を新規追加開始**。「トレード可能なラリーが来るかもしれない」としつつ、9月にかけての季節的・循環的逆風（特に10年債利回りが5%を確実に超える場合）への警戒は継続。REDFORDの8/5トレンド格上げと時期的に完全一致
- Minervini（8/7 23:42）: キャシー・ウッド/Skillzの事例を引いた需給の教訓を投稿（大口投資家の買い増しも供給過多の下落を止める保証にはならない、という警鐘）。トレードアクションの新規開示なし。LLYなど既存保有銘柄への直近の言及は見つからず、変更報告もないため保有継続とみなす
- REDFORDウォッチリストは39銘柄（redford_watchlist.json、DELL追加済み。TGTXは8/4売り推奨で除外済み）
- **IBD推奨の現物株保有比率は8/4の20-40%から8/8時点で60-80%まで段階的に引き上げ**。ただしステータス区分は依然「Up trend under pressure」＝利確・売却段階の位置づけであり、「Confirmed Uptrend」（無条件で買ってよい局面）への格上げ宣言はまだ出ていない点に注意
- LLYはMinerviniの実保有が7/27時点で確認済み（直近の売却報告なし）。引き続き4層確証（REDFORD医療強+Minervini実保有+スクリーナー+Checker）の最優先監視銘柄
- 推奨ポジション: **REDFORD/Minervini双方が防御姿勢からロング積み増しへ転換したことを反映し、現物株60-80%レンジでの段階的な買い場探しを検討してよい局面。ただし「Confirmed Uptrend」未宣言・FTD技術的不成立という留保もあるため、一括投資でなく分割での慎重なエントリーを推奨**。ウォッチ候補: DELL（新規）、LLY（最優先）、ATI（決算好調で確証強化）、GE/NMM/VIK/NTAP（8/2以来継続）

## ユーザーの現在保有ポジション（最終更新: 2026-08-01）
- S&P500投信: 約¥1,180万（コア・売らない）
- VOO: 9株 平均$500.47（コア・売らない）
- QQQ: 1株 @$689.72（2026-07-31購入、月足ルール実行）
- 円預金: 約¥60万
- 楽天証券+Webull: $2,210（現金待機中）
- 個別株: ゼロ（AMKR・MNST は売却済み）
- 最優先監視銘柄: LLY（4層確証：REDFORD医療強+Minervini実保有+スクリーナー+Checker✅）
- 月足ルール実績: 7月QQQ陰線 → 7/31にQQQ 1株@$689.72を購入

## 除外シグナル
- 除外①: 株価が200日MAの2倍以上（クライマックストップリスク）
- 除外②③: 市場がBearish/Distribution（IBD確認で上書き可）

## GitHub Pages
- リポジトリ: https://github.com/hirororororo888/canslim-screener
- URL: https://hirororororo888.github.io/canslim-screener/
- デプロイ: `deploy_github.bat`
- push方法: git remote set-url origin "https://[PAT]@github.com/hirororororo888/canslim-screener.git"

## ngrok（スマホアクセス用）
```
ngrok http 5174 --response-header-add "ngrok-skip-browser-warning:true"
```

## REDFORD自動収集（手動トリガー）
ユーザーが「REDFORD確認して」または「両方確認」と言ったら以下を実行:
1. Chrome拡張（mcp__claude-in-chrome__）でアクセス（ツール名が小文字に変更）
   - list_connected_browsers → select_browser
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

## ユーザーの指数ETF積立ルール
- 対象ETF: QQQ（2026年6月までVOOだったが、7月分以降QQQに変更）
- メインルール: QQQの月足が陰線（始値>終値）の月末に1株購入（変更: 2026-08-01）
  - 月末（最終営業日）の終値で判定
  - 陰線確定 → QQQを1株購入
  - 陽線 → その月は見送り
- 下落ナンピン補強ルール:
  - 52週高値から-10%でQQQ買い増し（余力の40%）
  - 52週高値から-20%でさらに買い増し（余力の60%）
  - 余力は楽天証券+Webull（2026/6時点で計約$3,344）
- ユーザーが「月足確認」と言ったらSPX月足陰線/陽線を判定
- VOO切替前の実績: VOO 9株を平均$500.47で保有済み（コア）
- その他コア資産: S&P500投信 約¥1,180万、円預金約¥60万

## Checker（独立検証）機能
論文「Loop Engineering」のmaker-checker分離を実装。
- `checker.py`: スクリーニング結果(Maker)をCANSLIM/SMARTとは独立した6ゲートで再検証
- 6つの検証ゲート:
  - G1 出来高: 5日平均 >= 50日平均×0.9（買い集めの実在）
  - G2 トレンド: 21MA上 かつ 50MA上（だましでない真の上昇）
  - G3 非過熱: 200MAの2倍未満（クライマックス回避）
  - G4 適正位置: 50MAから+15%以内（過延長でない）
  - G5 主導力: 堅調セクター or RS>=85
  - G6 高値圏: 52週高値の8%以内
- 判定: verified（5-6通過）/ caution（3-4）/ reject（2以下）
- Under Pressure/Correction時は厳格モード（G5主導力+G2トレンド必須）
- スクリーニング後の標準フロー: run_full_screen.py → fix_a_condition.py → checker.py → update_html.py → git push
- HTMLに「検証」列で✅検証/⚠️注意/❌却下を表示（ホバーで失敗ゲート詳細）

## Mark Minervini自動収集（手動トリガー）
ユーザーが「Minervini確認」と言ったら以下を実行:
1. Chrome拡張でアクセス: https://x.com/markminervini（ログイン済み・フォロー中）
2. 最新投稿を get_page_text で取得（スクロールして固定ポスト下を読む）
3. minervini_history.py の add_post() で2軸に振り分け:
   - 銘柄アクション（added/sold $TICKER）→ minervini_actions.json
   - トレード哲学・教訓 → minervini_wisdom.md（知識ベース）
   - 宣伝（Private Access勧誘）→ スキップ
4. アクション銘柄をスクリーナー/Checkerと照合
   - 例: LLY追加 → 既にCANSLIM/Checker検証済みなら強い確証
5. minervini_posts/ に原文保存（履歴蓄積）
- 投稿種類: REDFORDと違い構造化レポートでなく、売買アクション+哲学が中心
- Minerviniの実際の買い銘柄は、スクリーナー候補の「プロによる確証」として価値大

## 統合トリガー「両方確認」「両者確認」
ユーザーが「両方確認」または「両者確認」と言ったら、REDFORDとMinervini両方を順に取得:
1. REDFORD確認の手順を実行（市場トレンド・売抜日・Put/Call → screening_results.json更新）
2. Minervini確認の手順を実行（銘柄アクション・哲学 → actions.json/wisdom.md更新）
3. 両者を統合した投資判断を提示:
   - REDFORD市場トレンド（買ってよい局面か）
   - Minoviniの実売買銘柄（プロの確証）
   - スクリーナー候補 × Checker検証 との4層照合
   - 複数ソースが一致する銘柄を最優先候補として提示
4. update_html.py → GitHub push
- 「REDFORD確認」「Minervini確認」は個別実行も可能
