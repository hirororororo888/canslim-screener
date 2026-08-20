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

## 現在の市場状態（最終更新: 2026-08-20）
- **【最重要】REDFORD REPORTS-1849（8/19 7:45）: トレンド評価が「Confirmed up trend」から「Up trend under pressure（利確・売却段階）」に格下げ**。売り抜け日カウントがS&P500=2/Nasdaq=2に増加（8/18時点は0/1）。推奨ポジションも現物株60-80%・キャッシュ20-40%に引き下げ（8/18までは80-100%）。REDFORD REPORTS-1853（8/20 7:15）でも同トレンド継続を確認、Put/Call Ratio 0.84（中立〜弱気ゾーン）。8/14に宣言された「Confirmed up trend」は8/18を最後に終了し、8/19から「利確段階」に移行した点に注意。新規の全力買いは慎重に判断すべき局面
- Minervini（8/20未明）: **テック株のローテーション（銘柄入れ替え）による混乱を警告**。「急落から急速に切り返した元リーダー銘柄が、テクニカルな時間圧縮と大量の売り圧力（オーバーヘッド供給）の組み合わせで新たな問題に直面している」と指摘。LinkedInの過去事例（2011年上場後6週間で急落→急速に高値近辺まで戻すも供給に押し戻され、本格的な買いは2013年Q1まで待った）を引用し、「最安値でなく、正しい価格（ストップロスに引っかからず即座に上昇するポイント）を待つべき」と説明。REDFORDの格下げと同じ方向性の警戒シグナル
- REDFORD REPORTS-1853（8/20 7:15）: エントリー・ポイント突破銘柄として**LLY（ベースカウント1）**・FANG（ベースカウント2）が新たに登場。ただし市場が利確段階にあるため、通常のConfirmed Uptrend時ほど積極的な新規買いは推奨されない局面
- REDFORD REPORTS-1814（8/14 7:25）: IBD AIシステムがNYSEを正式に「Confirmed up trend（確固たる上昇相場）」に格上げ（CPI・PPI低下でFRB利上げリスク後退が決め手）。ただしこの局面は8/18で終了し、8/19から利確段階に移行済み（上記参照）。「Confirmed up trend」はCANSLIM/IBD流の3区分の中で唯一「株を買って良い」とされる局面（他の2つ、Up trend under pressure=利確段階、Market in correction=絶対に買うな）
- REDFORD REPORTS-1840（8/18 6:15、最新）: トレンド評価Confirmed up trend継続。推奨ポジション現物株80-100%・キャッシュ0-20%を維持。売り抜け日S&P500=0/Nasdaq=1（変化なし）。Put/Call Ratio 0.77（前日0.79、「やや強気」ゾーン継続）。エントリー突破銘柄LPG（ベースカウント3）、接近銘柄9銘柄
- REDFORD REPORTS-1843（8/18 11:25）: **イートン(ETON)が8週間ホールドルールを発動**。Q2決算後2日連続急騰、8/13終値40.80ドル→8/18朝61.73ドル（約51%上昇）。『綺麗なチャートを鑑賞する会』第1位。redford_watchlist.jsonに新規追加
- REDFORD REPORTS-1842（8/18 10:49）: クレド・テクノロジー(CRDO)が8.82%急騰、AIデータセンター接続技術への買い再燃。9/1決算発表を控えたポジション構築が要因と推測。REDFORDが2025年6月(株価72ドル)からテンバガー候補として継続紹介してきた銘柄。redford_watchlist.jsonに新規追加
- REDFORD REPORTS-1820（8/15 8:30）: トレンド評価Confirmed up trend継続。**推奨ポジションを現物株80%~100%・キャッシュ0-20%まで引き上げ**（8/9時点60-80%からさらに上）。売り抜け日S&P500=0/Nasdaq=1。Put/Call Ratio 0.76（前日0.84から改善、「やや強気」ゾーン）。エントリー突破銘柄CVE
- REDFORD REPORTS-1821（8/15 9:04）: **SNDKの購入は「50日移動平均線を明確に上回ってから」を大原則にすべきと注意喚起**。直近その抵抗線に接触しており、下回ったまま購入すると「上昇の騙し」で短期損失のリスクがあるため、焦らず観察を推奨（redford_watchlist.jsonのSNDK欄に注記済み）
- REDFORD（8/14返信、フォロワー@tirunoxさんへ）: 「8週間ホールドルールを発動した銘柄は8月4日・5日に既に仕込みました。現在ETFを除き12銘柄を仕込んでいます」— REDFORD本人がFTD直後の8/4-5に個人で12銘柄のポートフォリオを構築したことが判明。8/7判明済みのPLTR・DELL買付と整合的
- REDFORD REPORTS-1817（8/15、単独）: AMAT決算速報「好業績も株価は下落」。8/13決算プレビュー（REPORTS-1789）通り好業績だったが、材料出尽くしで株価は下落（sell the news）
- REDFORD REPORTS-1816（8/14、単独）: MU（マイクロン）を「割安感の強い」として再度取り上げ、強気継続
- **REDFORD REPORTS-1786（8/9 22:59）: エド・カーソン氏（REDFORD最も信頼する執筆者）が8月4日を正式にフォロースルーデイ(FTD)と確信**（変則的な認定、ナスダック50日平均出来高は下回っていた）。ここから8/14のConfirmed Uptrend宣言まで、位置づけが一段階進んだ形
- REDFORD REPORTS-1790/1789/1788/1787（8/9-10）: MU・AMAT決算プレビュー・ACHR対RKLB決算プレビュー・SNDKを新規紹介。redford_watchlist.jsonに反映済み
- REDFORD REPORTS-1785（8/9、Watch listを作成しよう第31回）: NUE・FCX・AMZN・PWRを新規ウォッチ銘柄として紹介
- **REDFORD本人の実売買（8/7判明）**: PLTR買付・DELL買付・DDOG売付（いずれも8/7）。DDOGは7/21紹介のエントリー278.70から本人資金が抜けた点は留意
- Minervini（8/10-8/17）: マインドセット本の宣伝・トレード心理学の一般論・格言引用が中心で、新規の銘柄売買開示なし。LLY等の保有継続に変更報告なし
- Minervini（8/20未明）: テック株ローテーション警告（上記【最重要】欄参照）。$SPCXを例に「急速な戻りが供給に押し戻される」パターンを指摘、実売買の開示ではないが市場全体への警戒シグナル
- Minervini（8/4-8/5）: $SPYショートヘッジを解消しロング転換。REDFORDの上昇トレンド転換とタイミングが完全一致
- REDFORDウォッチリストは49銘柄（redford_watchlist.json）。TGTXは8/4売り推奨で除外済み、DDOGは本人実売却を注記。8/18にCRDO・ETONを追加
- **IBD推奨の現物株保有比率は8/4の20-40%→8/8の60-80%→8/14のConfirmed Uptrend宣言後は80-100%まで引き上げ→8/19のUp trend under pressure格下げで60-80%に引き下げ**
- LLYはMinerviniの実保有が7/27時点で確認済み（直近の売却報告なし）。引き続き4層確証（REDFORD医療強+Minervini実保有+スクリーナー+Checker）の最優先監視銘柄。8/20にREDFORDのエントリー・ポイント突破銘柄としても登場
- 推奨ポジション: **市場は8/19に「Confirmed up trend」から「Up trend under pressure（利確・売却段階）」へ格下げ。CANSLIM流では新規の全力買いを控え、利益確定や損切りラインの管理を優先すべき局面。IBD推奨も80-100%→60-80%に引き下げ。Minerviniもテック株ローテーションによる「急回復銘柄が売り圧力に押し戻される」リスクを警告しており、方向性が一致**。新規エントリーは通常よりバイポイントに近い位置・出来高確認を厳格にすべき。ウォッチ候補: ATI（ユーザー保有・52週高値更新済み、利確ライン要監視）、LLY（最優先・4層確証、8/20エントリー突破）、DELL・PLTR（REDFORD本人実買付）、MU・SNDK（50日線待ち）、CRDO・ETON（8/18新規・急騰中）、GE/NMM/VIK/NTAP

## ユーザーの現在保有ポジション（最終更新: 2026-08-20）
- S&P500投信: 約¥1,180万（コア・売らない）
- VOO: 9株 平均$500.47（コア・売らない）
- QQQ: 1株 @$689.72（2026-07-31購入、月足ルール実行）
- 円預金: 約¥60万
- **ATI: 3株 @$231.26（2026-08-10購入、CANSLIM/Checker検証済み銘柄への初エントリー）**。損切りライン$212.76（-8%）
- **TQQQ: 6株 @$74.74（2026-08-10購入、Nasdaq-100の3倍レバレッジETF）**
- **LPG: 30株 @$48.88（2026-08-18購入、REDFORDエントリー突破銘柄+CANSLIM6/7+SMART5/5+Checker検証済み）**。損切りライン$44.97（-8%）。購入翌日8/19に市場がUp trend under pressureへ格下げ・Minerviniがテック株ローテーション警告を発信しているため、通常より注意深く監視が必要
- 楽天証券+Webull 購入余力: 約$52.60（2026-08-18時点。ATI/TQQQ/LPG購入後の残額）
- 生活資金: 50万円（投資対象外、別管理）
- 最優先監視銘柄: LLY（4層確証：REDFORD医療強+Minervini実保有+スクリーナー+Checker✅、CANSLIM6/7に上昇）
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
