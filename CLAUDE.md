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

## 現在の市場状態（最終更新: 2026-08-04）
- **REDFORD REPORTS-1767（8/4 11:55）: IBD推奨市場エクスポージャーが0-20%→20-40%に引き上げ**。トレンド評価はまだMarket in Correction継続（ナスダック・S&P500は3連騰も出来高不足でフォロースルーデイ未確定）。原油急落・米国債利回り低下（トランプ氏のイラン攻撃中止・対話再開表明を受け）、ダウは過去最高値更新。S&P500構成銘柄のQ2利益成長率は2021年Q2以来の高水準（86%が予想上回り）。PLTR決算好調で時間外+15%。エントリー突破銘柄はFBK/CSW/VVXの3銘柄のみとまだ少ないが、接近銘柄は13銘柄に急増中。フォロースルーデイは早ければ翌日にも発生の可能性、との見立て
- REDFORD REPORTS-1766（8/4 8:11）: トレンド評価Market in Correction継続・売抜日カウントなし、**推奨ポジション現物株20-40%/キャッシュ60-80%に引き上げ**（前回0-20%/80-100%から）、Put/Call Ratio 0.91（前日値と同じ）
- **REDFORD REPORTS-1766（8/4 10:31）: TGTX（TG Therapeutics）を売り推奨、ウォッチリストから除外**。Q2決算が予想を大幅未達で株価11%急落、50日移動平均線を大幅割れし売りシグナル発動。カップウィズハンドル突破後の上昇分をほぼ全て失う往復ビンタ型シグナルも発現（redford_watchlist.jsonのstatusを"removed_sell_signal"に更新済み）
- REDFORD REPORTS-1764/1765（8/3 10:41-10:42、Watch listを作成しよう第29回・第30回）: CARE（Carter Bankshares、地域銀行、IBD総合評価99・RS97、カップウィズハンドルのハンドル形成中）、JOBY（Joby Aviation、ACHRと同時紹介、目標株価13.90ドルで94%上昇余地）を新規紹介。トレンド評価そのものの更新はなし
- REDFORD REPORTS-1763（8/3、Watch list活用と銘柄選択のポイント）: トレンド評価・売抜日・Put/Callの数値更新なし。フォロースルーデイ発現前に先行して動くリーディング株の見分け方（エントリー突破/接近銘柄数の急増、下落率が小さい銘柄を優先）を解説する戦略記事で、正式なトレンド上方修正は依然未宣言。市場ステータスはREPORTS-1762時点から変化なし
- Minervini（8/2 0:37、8/4時点でも最新のまま更新なし）: 直近投稿（9〜17時間前）は投資チャンピオンシップ実績画像・ライブアート引用・IBD動画リツイート・ワークショップ告知など宣伝/ライフスタイル系のみでトレードアクションなし、スキップ
- REDFORDウォッチリストは第1回〜第30回・43銘柄まで拡充（redford_watchlist.json）
- REDFORD REPORTS-1756（8/1 8:00）: トレンド評価**Market in Correction**（継続・定義上売抜日カウントなし）、Put/Call Ratio 0.91（前日1.05から改善）、推奨ポジション現物株0-20%/キャッシュ80-100%
- REDFORD REPORTS-1762（8/2 11:47、Watch listを作成しよう第28回）: **「新規強気相場への準備を始めよう」**。7/30・31の主要指数反発を受け、『試しの第一日目』から4〜7日後に現れうる『フォロースルーデイ』出現に備える段階。正式なトレンド上方修正はまだ宣言していない。新規ウォッチ銘柄: GE（エントリーゾーン）、NMM（エントリーポイント80.97ドル）、VIK（エントリーポイント105.76ドル）、NTAP（カップ型ベース形成中）。フォロースルーデイ確認後も上昇相場形成の失敗確率25%のため、段階的ポジション構築を推奨
- **Minervini（8/2 0:37）も同じ姿勢**: 7/31の反発は「崩れなかった点で励み」だがポジションに大きな変化なし。数銘柄ロング継続、$SPYショートヘッジ継続（ストップ比較的タイト）。フォロー・スルー・デイと$SPYの高値奪還を待つ姿勢。10年債5%超えブレイクアウトを警戒（歴史的に弱い9月と重なるリスク）
- → **REDFORDとMinervini両者が「FTD待ち」で足並み一致**。正式な強気転換はまだだが、市場の空気が7/25時点の「現金化を急げ」から明確に軟化
- **IBD推奨の現物株保有比率は8/4に20-40%へ引き上げ**（現金60-80%、REPORTS-1766/1767で確認）
- **Minervini実トレード状況（7/27-30）**: ロング保有 PACS/CSX/HXL/ADM/MRK/**LLY**/HSBC/JNJ（大半が含み益、多くはストップを損益分岐点以上に設定）。7/27に$SPYへ部分的ショートヘッジを追加（755.00上にタイトストップ）。決算前の利益クッション不足銘柄は一部売却（銘柄非公表）
- LLYはMinerviniの実保有継続が確認され、引き続き4層確証（REDFORD医療強+Minervini実保有+スクリーナー+Checker）の最優先監視銘柄
- 推奨ポジション: **キャッシュ優先（60-80%、8/4にIBD推奨引き上げを反映）を継続、フォロースルーデイの出現に備えてウォッチリスト（GE/NMM/VIK/NTAP + LLY + Checker検証済み銘柄、TGTXは8/4売り推奨で除外）を準備**。正式なFTD確認・トレンド上方修正までは新規個別株購入は見送り

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
