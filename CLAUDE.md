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
- **Alpha Vantage**: 四半期EPS精密値（環境変数 AV_API_KEY で指定、25回/日）
- **FMP MCP**: 一部銘柄の決算データ（環境変数 FMP_API_KEY で指定）

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

## 現在の市場状態（最終更新: 2026-09-04）
- **【最重要】REDFORD REPORTS-1920（9/3 7:26）: Up trend under pressure継続、売り抜け日S&P500=3/Nasdaq=4は変化なし。ただしPut/Call Ratioが0.84→0.95に急悪化し「下落リスクがかなり高い」ゾーンに突入**（⚠️マーク付き、REDFORD自身も警戒を明示）。**推奨ポジションは60-80%→40-60%に再び引き下げ**（9/1の一時的な引き上げから逆戻り）。エントリー突破銘柄なし、接近銘柄も8→0に激減し新規の押し目候補が完全に枯渇。9/4朝時点でこれより新しい市場トレンドレポートは未投稿（最新はSNOW決算速報のみ）
- REDFORD REPORTS-1924（9/4 6:18、単独）: **SNOW（スノーフレーク）決算速報**。Q2好決算（EPS・売上高とも予想超、通期売上ガイダンス上方修正）を受け前日比16.55%急騰、356.47ドル。純増顧客692社（+32%）、AI支援コーディングツール需要拡大。アナリスト30名が買い推奨維持、平均目標株価285→431.90ドルに大幅引き上げ。ユーザーは保有していないが、AI関連セクターのセンチメント指標として参考
- REDFORD REPORTS-1909（9/1 7:35）: Up trend under pressure継続だが、売り抜け日カウントS&P500=3/Nasdaq=4に悪化（8/27時点は2/3）。一方で推奨ポジションは現物株60-80%・キャッシュ20-40%に引き上げ（8/27時点は40-60%）——8月月間の指数堅調を踏まえた判断とみられたが、9/3のREPORTS-1920で早くも40-60%に逆戻りしており、この引き上げは短命だった。Put/Call Ratio 0.84（前日0.73から悪化）。エントリー突破銘柄SLB（ベースカウント2）・UBS（ベースカウント1）、接近銘柄8銘柄
- REDFORD REPORTS-1910（9/1 8:12、単独）: **「NYSEは最悪の9月を迎える」と題し9月アノマリーを再警告**。中東紛争再燃（ホルムズ海峡機雷配備のイラン発射台2基への米攻撃、イランの報復、トランプ大統領の報復示唆）を受け8月最終取引日に2日連続下落。ただし8月月間は堅調（ダウ+1.3%・5ヶ月連続高、S&P500+2.6%、Nasdaq+3.9%）。9月アノマリー（過去100年で9月上昇は7回のみ、9月第3週が最も危険）を改めて解説し、10月以降は「年末高アノマリー」への反発を期待。キャッシュレベルは毎朝のトレンドレポート推奨に厳密に従うよう呼びかけ
- **Minervini（8/31 21:50、22時間前）: S&P 500サイクルコンポジット分析で9月警戒をREDFORDと独立に表明**。8月中旬〜10月初旬が歴史的に最も脆弱な時期と指摘。①歴史的に弱い9月期、②金利上昇の可能性（イールドカーブ短期部分は既に上昇）、③原油底入れ・エネルギーセクターの循環的追い風、の「3つの力の収束」に注目し「リスクを厳しく管理すべき」と主張。REDFORD REPORTS-1910と方向性が完全一致し、9/1のエントリー突破銘柄SLB（石油サービス）や8/22の資源・エネルギー株ローテーション（ERO・HBM・TECK・CNQ・DHT・SSRM・COP）とも符合——**エネルギーセクターへの注目が複数ソースで独立に浮上している点は要注視**。詳細はminervini_wisdom.md参照
- REDFORD REPORTS-1887（8/27 8:00）: Up trend under pressure継続、8/21から変化なし。売り抜け日カウントS&P500=2/Nasdaq=3で変化なし（8/21から6日連続横ばい）。推奨ポジションも現物株40-60%・キャッシュ40-60%を維持。Put/Call Ratio 0.83（前日0.91から改善も、依然「中立〜弱気」ゾーン）。エントリー突破銘柄は本日該当なし、接近銘柄10銘柄
- REDFORD REPORTS-1888（8/27、単独・戦略解説）: **9月アノマリー（中間選挙年の季節性下落）への対処法を提示**。9月第3週〜10月第1週がパフォーマンス最悪期になる傾向があるため、①その直前までに50日移動平均線を割り込んだ銘柄は売却しキャッシュを増加、②10月第2〜3週にRSI90以上・IBD総合評価95以上の銘柄を厳選して買い戻す、という2段階の計画を提示。ユーザーの現在のキャッシュ比率（40-60%）は既にこの戦略に沿っている
- REDFORD REPORTS-1885（8/27 5:55）: **NVDA Q2決算速報**。営業利益637億ドル（前年比2.2倍、5四半期連続最高）、売上高962億ドル（同2.1倍、13四半期連続最高）と好業績も、株価は決算後約1%下落（sell the news）。売掛金630億ドルへの回収リスクに言及。ユーザーは保有していないが、AI関連セクター全体のセンチメントに影響しうる
- REDFORD REPORTS-1862（8/22 8:30）: Up trend under pressure継続、8/21から横ばい。売り抜け日カウントS&P500=2/Nasdaq=3で変化なし。推奨ポジションも現物株40-60%・キャッシュ40-60%を維持。Put/Call Ratio 0.78（前日0.82から改善、「やや強気」ゾーンに回復）。エントリー突破銘柄が資源・エネルギー株に集中（ERO・HBM・TECK・CNQ・DHT・SSRM・COP）——セクターローテーションの兆し
- REDFORD REPORTS-1860（8/21 8:30）: Up trend under pressureが継続、さらに悪化していた局面。売り抜け日カウントがS&P500=2/Nasdaq=3に増加（8/20時点は2/2）。推奨ポジションを現物株40-60%・キャッシュ40-60%へ引き下げ（8/20までは60-80%）。エントリー突破銘柄FCX（ベースカウント3）・EOG（ベースカウント1）
- REDFORD REPORTS-1849（8/19 7:45）: トレンド評価が「Confirmed up trend」から「Up trend under pressure（利確・売却段階）」に格下げ。8/14に宣言された「Confirmed up trend」は8/18を最後に終了し、8/19から「利確段階」に移行
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
- **Minervini（9/4頃、直近投稿）: 「最高のセットアップが機能しないとき、最悪のセットアップに行くのではなく…現金に行くのです」と発信**。REDFORD REPORTS-1920のPut/Call急悪化・推奨ポジション再引き下げと同時期で、規律・キャッシュ重視のメッセージが両ソースで一致。同時に取引ルール2箇条（強制的な取引はしない／大きな損失は出さない）を再確認。また$SPCXが「タイトなピボット形成後に上昇へブレイクアウト」と言及（$149.74、+6.42%）——8/20から継続ウォッチしていた銘柄で初のブレイクアウト確認。詳細はminervini_wisdom.md参照
- Minervini（8/28-9/1）: サイクル分析（上記【最重要】欄参照）以外は格言・Masterclass宣伝（11/7-8・14-16開催）が中心で、新規の個別銘柄売買開示なし
- Minervini（8/25-8/27）: 引き続き格言・マインドセット系投稿中心（「ファンダメンタルが失敗するとき、チャートが語る」等）で、新規の銘柄売買開示なし。8/26のライブショーで$SPCXチャートのアナロジーに言及したのみ（詳細な売買判断ではない）
- Minervini（8/10-8/17）: マインドセット本の宣伝・トレード心理学の一般論・格言引用が中心で、新規の銘柄売買開示なし。LLY等の保有継続に変更報告なし
- Minervini（8/20未明）: テック株ローテーション警告（上記【最重要】欄参照）。$SPCXを例に「急速な戻りが供給に押し戻される」パターンを指摘、実売買の開示ではないが市場全体への警戒シグナル
- Minervini（8/4-8/5）: $SPYショートヘッジを解消しロング転換。REDFORDの上昇トレンド転換とタイミングが完全一致
- REDFORDウォッチリストは49銘柄（redford_watchlist.json）。TGTXは8/4売り推奨で除外済み、DDOGは本人実売却を注記。8/18にCRDO・ETONを追加
- **IBD推奨の現物株保有比率は8/4の20-40%→8/8の60-80%→8/14のConfirmed Uptrend宣言後は80-100%まで引き上げ→8/19のUp trend under pressure格下げで60-80%→8/21にさらに40-60%まで引き下げ→9/1に60-80%へ一時引き上げ→9/3に40-60%へ再び引き下げ（Put/Call Ratio 0.95まで急悪化、要警戒）**
- LLYはMinerviniの実保有が7/27時点で確認済み（直近の売却報告なし）。引き続き4層確証（REDFORD医療強+Minervini実保有+スクリーナー+Checker）の最優先監視銘柄。8/20にREDFORDのエントリー・ポイント突破銘柄としても登場
- 推奨ポジション: **9/4時点でUp trend under pressure継続中、Put/Call Ratioが0.95まで急悪化し「下落リスクがかなり高い」ゾーンに突入。REDFORDの推奨現物株比率も9/1の一時引き上げ(60-80%)から9/3に40-60%へ逆戻りし、エントリー接近銘柄もゼロに枯渇——新規買いは完全に見送るべき局面**。REDFORD・Minervini双方が独立に9月アノマリー（季節性下落）と規律・キャッシュ重視を発信しており足並みが揃っている。中東地政学リスク（イラン関連）・金利上昇・9月第3週の下落リスクに要警戒。既存ポジション（LPG・TQQQ等）は損切りライン厳守を最優先。エネルギーセクター（SLB等の突破銘柄、原油底入れ）は複数ソースで独立に浮上しており注視継続。ウォッチ候補: LLY（最優先・4層確証、8/20エントリー突破）、DELL・PLTR（REDFORD本人実買付）、MU・SNDK（50日線待ち）、CRDO・ETON（8/18新規・急騰中）、FCX・EOG（8/21新規エントリー突破）、SLB・UBS（9/1エントリー突破）、SNOW（9/4決算急騰・保有なし）、$SPCX（Minerviniウォッチ・ブレイクアウト確認）、GE/NMM/VIK/NTAP

## ユーザーの現在保有ポジション（最終更新: 2026-09-02）
- S&P500投信: 約¥1,180万（コア・売らない）
- VOO: 9株 平均$500.47（コア・売らない）
- QQQ: 1株 @$689.72（2026-07-31購入、月足ルール実行）
- 円預金: 約¥60万
- **ATI: 2026-08-20に3株@$213.27で全株売却（損切りライン$212.76到達のため）**。購入単価$231.26、実現損益-$53.97（-7.78%）。8%ルール通りの規律的な損切り
- **TQQQ: 2026-09-02に6株@$69.03で全株売却**。購入単価$74.74（2026-08-10購入）、実現損益-$34.26（-7.64%）。売却翌日9/3のREDFORD REPORTS-1920でPut/Call Ratio 0.95急悪化・推奨ポジション再引き下げが発表されており、結果的に良いタイミングでの損切りとなった
- **LPG: 30株 @$48.88（2026-08-18購入、REDFORDエントリー突破銘柄+CANSLIM6/7+SMART5/5+Checker検証済み）**。損切りライン$44.97（-8%）。購入翌日8/19に市場がUp trend under pressureへ格下げ・Minerviniがテック株ローテーション警告を発信しているため、通常より注意深く監視が必要。8/20の再スクリーニングでCheckerが検証済み→要注意(4/6)に変化
- 楽天証券+Webull 購入余力: 約$1,106.59（2026-09-02時点。TQQQ売却代金$414.18を加算）
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
