# Finviz MCP Server - Tools Reference

## 🔍 スクリーニングツール

### `earnings_screener`
決算発表予定銘柄の基本スクリーニング

**パラメータ:**
- `earnings_date` (必須): 決算発表日 (`today_after`, `tomorrow_before`, `this_week`, `within_2_weeks`)
- `market_cap`: 時価総額フィルタ (`small`, `mid`, `large`, `mega`)
- `min_price`: 最低株価
- `min_volume`: 最低出来高
- `sectors`: 対象セクター

### `volume_surge_screener`
出来高急増を伴う上昇銘柄のスクリーニング

**パラメータ:**
- `market_cap`: 時価総額フィルタ (デフォルト: `smallover`)
- `min_price`: 最低株価 (デフォルト: 10)
- `min_relative_volume`: 最低相対出来高倍率 (デフォルト: 1.5)
- `min_price_change`: 最低価格変動率 (デフォルト: 2.0%)
- `sma_filter`: 移動平均線フィルタ (デフォルト: `above_sma200`)

### `trend_reversion_screener`
トレンド反転候補銘柄のスクリーニング

**パラメータ:**
- `market_cap`: 時価総額フィルタ (デフォルト: `mid_large`)
- `eps_growth_qoq`: EPS成長率(QoQ)最低値
- `revenue_growth_qoq`: 売上成長率(QoQ)最低値
- `rsi_max`: RSI上限値
- `sectors`, `exclude_sectors`: セクターフィルタ

### `uptrend_screener`
上昇トレンド銘柄のスクリーニング

**パラメータ:**
- `trend_type`: トレンドタイプ (`strong_uptrend`, `breakout`, `momentum`)
- `sma_period`: 移動平均期間 (`20`, `50`, `200`)
- `relative_volume`: 相対出来高最低値
- `price_change`: 価格変化率最低値

### `dividend_growth_screener`
配当成長銘柄のスクリーニング

**パラメータ:**
- `min_dividend_yield`, `max_dividend_yield`: 配当利回り範囲
- `min_dividend_growth`: 最低配当成長率
- `min_roe`: 最低ROE
- `max_debt_equity`: 最高負債比率

### `etf_screener`
ETF戦略用スクリーニング

**パラメータ:**
- `strategy_type`: 戦略タイプ (`long`, `short`)
- `asset_class`: 資産クラス (`equity`, `bond`, `commodity`, `currency`)
- `min_aum`: 最低運用資産額
- `max_expense_ratio`: 最高経費率

## 📈 決算関連スクリーニング

### `earnings_premarket_screener`
寄り付き前決算発表で上昇している銘柄

**パラメータ:**
- `earnings_timing`: 決算発表タイミング (デフォルト: `today_before`)
- `min_price_change`: 最低価格変動率 (デフォルト: 2.0%)
- `include_premarket_data`: 寄り付き前取引データを含める
- `max_results`: 最大取得件数 (デフォルト: 60)

### `earnings_afterhours_screener`
引け後決算発表で時間外取引上昇銘柄

**パラメータ:**
- `earnings_timing`: 決算発表タイミング (デフォルト: `today_after`)
- `min_afterhours_change`: 最低時間外価格変動率 (デフォルト: 2.0%)
- `include_afterhours_data`: 時間外取引データを含める
- `max_results`: 最大取得件数 (デフォルト: 60)

### `earnings_trading_screener`
決算トレード対象銘柄（予想上方修正・サプライズ重視）

**パラメータ:**
- `earnings_window`: 決算発表期間 (デフォルト: `yesterday_after_today_before`)
- `earnings_revision`: 決算予想修正フィルタ (デフォルト: `eps_revenue_positive`)
- `price_trend`: 価格トレンドフィルタ (デフォルト: `positive_change`)
- `sort_by`: ソート基準 (デフォルト: `eps_surprise`)

### `earnings_positive_surprise_screener`
今週決算発表でポジティブサプライズ銘柄

**パラメータ:**
- `earnings_period`: 決算発表期間 (デフォルト: `this_week`)
- `min_avg_volume`: 最低平均出来高 (デフォルト: 500,000)
- `sort_by`: ソート基準 (デフォルト: `eps_qoq_growth`)
- `include_chart_view`: 週足チャートビューを含める

## 📊 ファンダメンタル分析

### `get_stock_fundamentals`
個別銘柄のファンダメンタルデータ取得

**パラメータ:**
- `ticker` (必須): 銘柄ティッカー
- `data_fields`: 取得データフィールドのリスト

### `get_multiple_stocks_fundamentals`
複数銘柄のファンダメンタルデータ一括取得

**パラメータ:**
- `tickers` (必須): 銘柄ティッカーのリスト
- `data_fields`: 取得データフィールドのリスト

## 📄 SECファイリング分析

### `get_sec_filings`
指定銘柄のSECファイリングリストを取得

**パラメータ:**
- `ticker` (必須): 銘柄ティッカー
- `form_types`: フォームタイプフィルタ (例: `["10-K", "10-Q", "8-K"]`)
- `days_back`: 過去何日分のファイリング (デフォルト: 30)
- `max_results`: 最大取得件数 (デフォルト: 50)
- `sort_by`: ソート基準 (`filing_date`, `report_date`, `form`)
- `sort_order`: ソート順序 (`asc`, `desc`)

### `get_major_sec_filings`
主要SECファイリング（10-K, 10-Q, 8-K等）を取得

**パラメータ:**
- `ticker` (必須): 銘柄ティッカー
- `days_back`: 過去何日分のファイリング (デフォルト: 90)

### `get_insider_sec_filings`
インサイダー取引関連SECファイリング（フォーム3, 4, 5等）を取得

**パラメータ:**
- `ticker` (必須): 銘柄ティッカー
- `days_back`: 過去何日分のファイリング (デフォルト: 30)

### `get_sec_filing_summary`
指定期間のSECファイリング概要とサマリーを取得

**パラメータ:**
- `ticker` (必須): 銘柄ティッカー
- `days_back`: 過去何日分の概要 (デフォルト: 90)

## 📰 ニュース分析

### `get_stock_news`
銘柄関連ニュースの取得

**パラメータ:**
- `ticker` (必須): 銘柄ティッカー
- `days_back`: 過去何日分のニュース (デフォルト: 7)
- `news_type`: ニュースタイプ (`all`, `earnings`, `analyst`, `insider`, `general`)

### `get_market_news`
市場全体のニュースを取得

**パラメータ:**
- `days_back`: 過去何日分のニュース (デフォルト: 3)
- `max_items`: 最大取得件数 (デフォルト: 20)

### `get_sector_news`
特定セクターのニュースを取得

**パラメータ:**
- `sector` (必須): セクター名
- `days_back`: 過去何日分のニュース (デフォルト: 5)
- `max_items`: 最大取得件数 (デフォルト: 15)

## 🏭 セクター・業界分析

### `get_sector_performance`
セクター別パフォーマンス分析

**パラメータ:**
- `timeframe`: 分析期間 (`1d`, `1w`, `1m`, `3m`, `6m`, `1y`)
- `sectors`: 対象セクターのリスト

### `get_industry_performance`
業界別パフォーマンス分析

**パラメータ:**
- `timeframe`: 分析期間 (`1d`, `1w`, `1m`, `3m`, `6m`, `1y`)
- `industries`: 対象業界のリスト

### `get_country_performance`
国別市場パフォーマンス分析

**パラメータ:**
- `timeframe`: 分析期間 (`1d`, `1w`, `1m`, `3m`, `6m`, `1y`)
- `countries`: 対象国のリスト

### `get_market_overview`
市場全体の概要を取得

**パラメータ:** なし

## 📉 テクニカル分析

### `get_relative_volume_stocks`
相対出来高異常銘柄の検出

**パラメータ:**
- `min_relative_volume` (必須): 最低相対出来高
- `min_price`: 最低株価
- `sectors`: 対象セクター
- `max_results`: 最大取得件数 (デフォルト: 50)

### `technical_analysis_screener`
テクニカル指標ベースのスクリーニング

**パラメータ:**
- `rsi_min`, `rsi_max`: RSI範囲
- `price_vs_sma20`, `price_vs_sma50`, `price_vs_sma200`: 移動平均との関係 (`above`, `below`)
- `min_price`: 最低株価
- `min_volume`: 最低出来高
- `sectors`: 対象セクター

## 💡 使用例

### 基本的な決算スクリーニング
```
earnings_screener(
    earnings_date="today_after",
    market_cap="large",
    min_price=10,
    sectors=["Technology"]
)
```

### 出来高急増銘柄の検出
```
volume_surge_screener(
    min_relative_volume=2.0,
    min_price_change=5.0,
    market_cap="mid"
)
```

### セクター別パフォーマンス
```
get_sector_performance(
    timeframe="1w",
    sectors=["Technology", "Healthcare"]
)
```

### テクニカル分析
```
technical_analysis_screener(
    rsi_max=30,
    price_vs_sma200="above",
    min_price=20
)
```

### `upcoming_earnings_screener`
来週決算予定銘柄のスクリーニング（決算トレード事前準備用）

**パラメータ:**
- `earnings_period`: 決算発表期間 (デフォルト: `next_week`)
- `market_cap`: 時価総額フィルタ (デフォルト: `smallover`)
- `min_price`: 最低株価 (デフォルト: 10)
- `min_avg_volume`: 最低平均出来高 (デフォルト: 500,000)
- `target_sectors`: 対象セクター（8セクター）
- `pre_earnings_analysis`: 決算前分析項目の設定
- `risk_assessment`: リスク評価項目の設定
- `data_fields`: 取得するデータフィールド
- `max_results`: 最大取得件数 (デフォルト: 100)
- `sort_by`: ソート基準 (デフォルト: `earnings_date`)
- `sort_order`: ソート順序 (デフォルト: `asc`)
- `include_chart_view`: 週足チャートビューを含める
- `earnings_calendar_format`: 決算カレンダー形式で出力

## 📝 注意事項

1. **レート制限**: Finvizの利用規約に従い、適切な間隔でAPIを使用してください
2. **データの信頼性**: 投資判断は自己責任で行ってください
3. **APIキー**: Finviz Elite APIキーを設定すると、より高いレート制限が適用されます
4. **エラーハンドリング**: ネットワークエラーや無効なパラメータは適切にハンドリングされます

## EDGAR API ツール (SEC公式API)

### 📄 get_edgar_filing_content
**EDGAR API経由でSECファイリングドキュメント内容を取得**

**パラメータ:**
- `ticker`: 銘柄ティッカー
- `accession_number`: SEC accession number (ダッシュ付き)
- `primary_document`: プライマリドキュメントファイル名
- `max_length`: 最大コンテンツ長 (デフォルト: 50,000文字)

**使用例:**
```python
get_edgar_filing_content(
    ticker="AAPL",
    accession_number="0000320193-24-000007",
    primary_document="aapl-20231230.htm",
    max_length=100000
)
```

### 📄 get_multiple_edgar_filing_contents
**複数のSECファイリングドキュメント内容を一括取得**

**パラメータ:**
- `ticker`: 銘柄ティッカー
- `filings_data`: ファイリングデータのリスト
- `max_length`: 各ドキュメントの最大コンテンツ長 (デフォルト: 20,000文字)

**使用例:**
```python
get_multiple_edgar_filing_contents(
    ticker="AAPL",
    filings_data=[
        {"accession_number": "0000320193-24-000007", "primary_document": "aapl-20231230.htm"},
        {"accession_number": "0000320193-23-000077", "primary_document": "aapl-20230930.htm"}
    ]
)
```

### 📊 get_edgar_company_filings
**EDGAR API経由で企業のファイリング一覧を取得**

**パラメータ:**
- `ticker`: 銘柄ティッカー
- `form_types`: フォームタイプフィルタ (例: ["10-K", "10-Q", "8-K"])
- `max_count`: 最大取得件数 (デフォルト: 50)
- `days_back`: 過去何日分 (デフォルト: 365日)

**使用例:**
```python
get_edgar_company_filings(
    ticker="AAPL",
    form_types=["10-K", "10-Q"],
    max_count=20,
    days_back=180
)
```

### 🏢 get_edgar_company_facts
**EDGAR API経由で企業の基本情報とファクトデータを取得**

**パラメータ:**
- `ticker`: 銘柄ティッカー

**使用例:**
```python
get_edgar_company_facts(ticker="AAPL")
```

### 📊 get_edgar_company_concept
**EDGAR API経由で企業の特定の財務コンセプトデータを取得**

**パラメータ:**
- `ticker`: 銘柄ティッカー
- `concept`: XBRLコンセプト (例: 'Assets', 'Revenues', 'NetIncomeLoss')
- `taxonomy`: タクソノミー ('us-gaap', 'dei', 'invest')

**使用例:**
```python
get_edgar_company_concept(
    ticker="AAPL",
    concept="Assets",
    taxonomy="us-gaap"
)
```

**よく使用される財務コンセプト:**
- `Assets`: 総資産
- `Revenues`: 売上高
- `NetIncomeLoss`: 純利益
- `StockholdersEquity`: 株主資本
- `CashAndCashEquivalentsAtCarryingValue`: 現金及び現金同等物