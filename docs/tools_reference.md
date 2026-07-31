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

### `earnings_winners_screener`
決算勝ち組銘柄のスクリーニング（週間パフォーマンス・EPSサプライズ・売上サプライズを含む詳細一覧）

**パラメータ:**
- `earnings_period`: 決算発表期間 (デフォルト: `this_week`)
- `market_cap`: 時価総額フィルタ (デフォルト: `smallover`)
- `min_price`: 最低株価 (デフォルト: $10)
- `min_avg_volume`: 最低平均出来高 (デフォルト: o500 = 500,000以上)
- `min_eps_growth_qoq`: 最低EPS前四半期比成長率(%) (デフォルト: 10%)
- `min_eps_revision`: 最低EPS予想改訂率(%) (デフォルト: 5%)
- `min_sales_growth_qoq`: 最低売上前四半期比成長率(%) (デフォルト: 5%)
- `min_weekly_performance`: 週次パフォーマンスフィルタ (デフォルト: 5to-1w)
- `sma200_filter`: 200日移動平均線上のフィルタ (デフォルト: True)
- `target_sectors`: 対象セクター (デフォルト: 主要6セクター)
- `max_results`: 最大取得件数 (デフォルト: 50)
- `sort_by`: ソート基準 (`performance_1w`, `eps_growth_qoq`, `eps_surprise`, `price_change`, `volume`)
- `sort_order`: ソート順序 (`asc`, `desc`)

### `upcoming_earnings_screener`
来週決算予定銘柄のスクリーニング（決算トレンド事前準備用）

**パラメータ:**
- `earnings_period`: 決算発表期間 (デフォルト: `next_week`)
- `market_cap`: 時価総額フィルタ (デフォルト: `smallover`)
- `min_price`: 最低株価 (デフォルト: $10)
- `min_avg_volume`: 最低平均出来高 (デフォルト: 500,000)
- `target_sectors`: 対象セクター（8セクター）
- `max_results`: 最大取得件数 (デフォルト: 100)
- `sort_by`: ソート基準 (`earnings_date`, `market_cap`, `target_price_upside`, `volatility`)
- `include_chart_view`: 週足チャートビューを含める (デフォルト: True)
- `earnings_calendar_format`: 決算カレンダー形式で出力 (デフォルト: False)

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

日時はすべてFinvizの提供どおり **US/Eastern (ET)** で表示されます。

### `get_stock_news`
銘柄関連ニュースの取得（`news_export.ashx?v=3`）

**パラメータ:**
- `tickers` (必須): 銘柄ティッカー（カンマ区切り可）
- `days_back`: 過去何日分のニュース (デフォルト: 7、ET基準)

各記事にはCSVの `Ticker` 列そのままの銘柄が付きます（複数銘柄の記事はカンマ連結）。
`news_type` は廃止しました: Finvizは `filter=` を無視し、v=3の `Category` は
常に `Stock` なので、正直にフィルタできる軸が存在しません。

### `get_market_news`
市場全体のニュースを取得（`news_export.ashx?v=1`）

**パラメータ:**
- `days_back`: 過去何日分のニュース (デフォルト: 3、ET基準)
- `max_items`: 最大取得件数 (デフォルト: 20)
- `category`: `Category` 列に対する**クライアント側**フィルタ。有効値は
  `Market` / `Blog` のみ（大文字小文字不問）。それ以外はエラー（黙って0件にしない）。
  省略時は全件。

いずれのニュースツールも `days_back` の境界は**含む**（ちょうど N 日前のアイテムは残る）。
日付が空/解釈不能な行は落としますが、件数はWARNINGログに1回まとめて記録されます。

### `get_sector_news`
特定セクターのニュースを取得

Finvizにセクター別ニュースフィードは存在しません（`sec=` は無視される）。
本ツールはまずセクター構成銘柄を時価総額降順で取得し（上位40銘柄）、
その銘柄群のニュースをv=3で取得します（リクエストは計2回）。
各記事は実際のティッカー付きで表示されます。未知のセクター名はエラーになります。

**パラメータ:**
- `sector` (必須): セクター名またはFinvizコード（例 `Technology` / `technology`）
- `days_back`: 過去何日分のニュース (デフォルト: 5、ET基準)
- `max_items`: 最大取得件数 (デフォルト: 15)

## 🏭 セクター・業界分析

### `get_sector_performance`
セクター別パフォーマンス分析

**パラメータ:**
- `sectors`: 対象セクターのリスト（大文字小文字は区別しない。省略時は全セクター）

### `get_industry_performance`
業界別パフォーマンス分析

**パラメータ:**
- `industries`: 対象業界のリスト（大文字小文字は区別しない。省略時は全業界）

### `get_country_performance`
国別市場パフォーマンス分析

**パラメータ:**
- `countries`: 対象国のリスト（大文字小文字は区別しない。省略時は全国）

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
テクニカル分析ベースのスクリーニング

**パラメータ:**
- `rsi_min`, `rsi_max`: RSI範囲
- `price_vs_sma20`, `price_vs_sma50`, `price_vs_sma200`: 移動平均線との関係 (`above`, `below`)
- `min_price`: 最低株価
- `min_volume`: 最低出来高
- `sectors`: 対象セクター
- `max_results`: 最大取得件数 (デフォルト: 50)

## 🔧 ユーティリティ

### `get_capitalization_performance`
時価総額別パフォーマンス分析

**パラメータ:** なし

### `get_sector_specific_industry_performance`
特定セクター内の業界別パフォーマンス分析

**パラメータ:**
- `sector` (必須): セクター名

## 📋 使用例

### 基本的なスクリーニング
```python
# 決算発表予定銘柄を検索
earnings_screener(
    earnings_date="today_after",
    market_cap="large",
    min_price=50
)

# 出来高急増銘柄を検索
volume_surge_screener(
    min_relative_volume=3.0,
    min_price_change=5.0
)
```

### 決算関連分析
```python
# 決算勝ち組銘柄を分析
earnings_winners_screener(
    earnings_period="this_week",
    sort_by="eps_surprise"
)

# 来週決算予定を確認
upcoming_earnings_screener(
    earnings_period="next_week",
    include_chart_view=True
)
```

### ファンダメンタル分析
```python
# 個別銘柄の詳細データ
get_stock_fundamentals(ticker="AAPL")

# 複数銘柄の比較
get_multiple_stocks_fundamentals(
    tickers=["AAPL", "MSFT", "GOOGL"]
)
``` 