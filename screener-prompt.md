# CANSLIM スクリーニング実行プロンプト

Claude Code 再起動後にこのプロンプトを使ってスクリーニングを実行してください。

## 接続確認
```
FMP MCPツールを使ってSPYの直近60日の株価・出来高データを取得してください。
```

## フルスクリーニング実行
```
FMP MCPツールを使ってCANSLIMスクリーニングを実行してください。

手順:
1. screenerツールで時価総額500M超・出来高300K超・US市場の銘柄を200件取得
2. 各銘柄の四半期EPS・売上データでC条件（YoY 25%超）とS条件を判定
3. 年次EPSデータでA条件（3年連続25%超）を判定
4. 株価データで N条件（52週高値の15%以内）と L条件（SPY比RS > 70）を判定
5. 機関投資家データでI条件（Accumulation/Distribution/Neutral）を判定
6. SPYデータでM条件（bullish/caution/bearish）を算出
7. 7点満点でスコア化し上位25件をMarkdownテーブルで出力
8. C:\Users\user\canslim-screener\index.html の loadData() 関数に渡すJSONも生成

出力フォーマット:
| 銘柄 | スコア | C | A | S | N | L | I | M | EPS成長 | 売上成長 |
```

## HTMLへの反映
スクリーニング完了後、以下のJSONを index.html の <script> 末尾に追加:
```js
loadData({
  market: {
    status: "bullish", // or "caution" / "bearish"
    spyPrice: 000.00,
    spyChange: 0.0,
    ma60: 000.00,
    aboveMa60: true,
    distributionDays: 0,
    hiLoRatio: 1.0,
    hiLoDesc: "Strong breadth",
    followThrough: true,
    followThroughDate: "2026-05-XX"
  },
  stocks: [
    // ... 上位25件
  ],
  updatedAt: "2026-05-30T00:00:00Z"
});
```
