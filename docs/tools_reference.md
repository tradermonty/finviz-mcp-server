# Finviz MCP Server - Tools Reference

## 🔍 スクリーニングツール

### `earnings_screener`
決算発表予定銘柄の基本スクリーニング

**パラメータ:**
- `earnings_date` (必須): 決算発表日 (`today_after`, `tomorrow_before`, `this_week`, `within_2_weeks`)
- `market_cap`: 時価総額フィルタ (`small`, `mid`, `large`, `mega`, `smallover`, `midover`, `largeover`, ...)
- `min_price`: 最低株価
- `max_price`: 最高株価
- `min_volume`: 最低出来高（**当日**出来高。`sh_curvol_*` に変換）
- `sectors`: 対象セクター

（`premarket_price_change` / `afterhours_price_change` は廃止: Finvizに対応する
フィルタが存在しない。時間外の値動きで絞るには `earnings_afterhours_screener`）

### `volume_surge_screener`
出来高急増を伴う上昇銘柄のスクリーニング

**パラメータ:** なし（条件は固定:
`cap_smallover, ind_stocksonly, sh_avgvol_o100, sh_price_o10, sh_relvol_o1.5, ta_change_u2, ta_sma200_pa`）

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

**パラメータ:** なし（条件は固定）

### `dividend_growth_screener`
配当成長銘柄のスクリーニング

**パラメータ:**
- `market_cap`: 時価総額フィルタ (デフォルト: `midover`)
- `min_dividend_yield` (デフォルト: 2.0), `max_dividend_yield`: 配当利回り範囲
- `min_payout_ratio`, `max_payout_ratio`: 配当性向の範囲
- `min_roe`: 最低ROE
- `max_debt_equity`: 最高負債比率
- `max_pb_ratio` (デフォルト: 5.0), `max_pe_ratio` (デフォルト: 30.0)
- `eps_growth_5y_positive`, `eps_growth_qoq_positive`, `eps_growth_yoy_positive`,
  `sales_growth_5y_positive`, `sales_growth_qoq_positive`: 成長率プラス条件（すべてデフォルト: True）
- `country`: 国フィルタ (デフォルト: `USA`)
- `stocks_only`: ETF等を除外 (デフォルト: True)
- `sort_by` (デフォルト: `dividend_yield`), `sort_order` (デフォルト: `desc`)
- `max_results`: 最大取得件数 (デフォルト: 100)
- （`min_dividend_growth` は廃止: Finvizに配当成長率のフィルタトークンが無い）

### `etf_screener`
ETF戦略用スクリーニング

**パラメータ:**
- `asset_class`: 資産クラス (`equity`, `bond`, `commodity`, `crypto`, ...)
- `min_aum`: 最低運用資産額（クライアント側で適用）
- `max_expense_ratio`: 最高経費率（クライアント側で適用）
- `min_price`, `min_avg_volume`, `sort_by`, `sort_order`, `max_results`
- （`strategy_type` は廃止: Finvizにも取得データにも対応する概念が無い）

## 📈 決算関連スクリーニング

### `earnings_premarket_screener`
寄り付き前決算発表で上昇している銘柄

**パラメータ:** なし（条件は固定。表示される条件ブロックは実際に送るフィルタと一致する）

### `earnings_afterhours_screener`
引け後決算発表で時間外取引上昇銘柄

**パラメータ:** なし（条件は固定。件数上限60はURL側で固定）

### `earnings_trading_screener`
決算トレード対象銘柄（予想上方修正・サプライズ重視）

**パラメータ:** なし（条件は固定）

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
- `earnings_period`: 決算発表期間 (デフォルト: `next_week`。他に `next_5_days`,
  `this_week`, `this_month`, `next_2_weeks`, `next_month`)
- `market_cap`: 時価総額フィルタ (デフォルト: `smallover`)
- `min_price`: 最低株価 (デフォルト: $10)
- `min_avg_volume`: 最低平均出来高（株数、または `o500` 形式。デフォルト: `o500`）
- `target_sectors`: 対象セクター（8セクター）
- `max_results`: 最大取得件数 (デフォルト: 100、**ソート後**に適用)
- `sort_by`: ソート基準 (`earnings_date`, `market_cap`, `target_price_upside`, `volatility`, `ticker`)
- `sort_order`: ソート順序 (デフォルト: `asc`)
- `include_chart_view`: 週足チャートビューを含める (デフォルト: True)
- `earnings_calendar_format`: 決算カレンダー形式で出力 (デフォルト: False)
- `custom_date_range`: Finviz形式の日付範囲 (`MM-DD-YYYYxMM-DD-YYYY`)
- `start_date` / `end_date`: 日付範囲 (`YYYY-MM-DD`、2つで1組)

`next_2_weeks` / `next_month` は明示的な日付範囲として送る（以前は5営業日/今月を
送っており表示ラベルと期間が食い違っていた）。`pre_earnings_analysis` /
`risk_assessment` / `data_fields` は受け取っても捨てていたため廃止。

## 📊 ファンダメンタル分析

### `get_stock_fundamentals`
個別銘柄のファンダメンタルデータ取得

**パラメータ:**
- `ticker` (必須): 銘柄ティッカー
- `data_fields`: 取得データフィールドのリスト（省略時は全150カラム）

### `get_multiple_stocks_fundamentals`
複数銘柄のファンダメンタルデータ一括取得

**パラメータ:**
- `tickers` (必須): 銘柄ティッカーのリスト
- `data_fields`: 取得データフィールドのリスト（省略時は全150カラム）

`data_fields` にはマッピング名のほか、別名 (`net_margin`, `roi` 等)、CSVヘッダ由来の
結果キー (`p_e`, `eps_ttm` 等)、派生キー (`week_52_high` 等) も使える。`all` を渡すと
射影せず全件返す。有効性は `validate_fields` で事前確認できる（同じ判定を使う）。

## 📄 SECファイリング分析

### `get_sec_filings`
指定銘柄のSECファイリングリストを取得

**パラメータ:**
- `ticker` (必須): 銘柄ティッカー
- `form_types`: フォームタイプフィルタ (例: `["10-K", "10-Q", "8-K"]`)。訂正版 (`10-K/A`) も一致
- `days_back`: 過去何日分のファイリング (デフォルト: 30、**0以下で期間無制限**)
- `max_results`: 最大取得件数 (デフォルト: 50、**0以下で無制限**)
- `sort_by`: ソート基準 (`filing_date`, `report_date`, `form`)。これ以外はエラー
- `sort_order`: ソート順序 (`asc`, `desc`)

### `get_major_sec_filings`
主要SECファイリング（10-K, 10-Q, 8-K等）を取得

**パラメータ:**
- `ticker` (必須): 銘柄ティッカー
- `days_back`: 過去何日分のファイリング (デフォルト: 90)

### `get_insider_sec_filings`
インサイダー取引関連SECファイリング（フォーム3, 4, 5, 144。訂正版含む）を取得。
従業員給付制度の年次報告である 11-K は対象外。

**パラメータ:**
- `ticker` (必須): 銘柄ティッカー
- `days_back`: 過去何日分のファイリング (デフォルト: 30)

### `get_sec_filing_summary`
指定期間のSECファイリング概要とサマリーを取得。集計は期間全件に対して行い、
表示件数の上限は別途明記する。

**パラメータ:**
- `ticker` (必須): 銘柄ティッカー
- `days_back`: 過去何日分の概要 (デフォルト: 90)

## 🗂 EDGAR (SEC公式API)

いずれも `EDGAR_USER_AGENT` 環境変数（SECが要求する連絡先付きUA）が必須。

### `get_edgar_company_filings`
企業のファイリング一覧をEDGARから取得。フォーム・期間フィルタを先に適用し、
`max_count` は最後に効かせる。

**パラメータ:**
- `ticker` (必須): 銘柄ティッカー
- `form_types`: フォームタイプフィルタ（訂正版も一致）
- `max_count`: 最大取得件数 (デフォルト: 50)
- `days_back`: 過去何日分 (デフォルト: 365。**0以下/None で期間無制限**)
- `include_full_history`: ページネーションを辿って全履歴を取得 (デフォルト: False)

### `get_edgar_company_facts`
企業のXBRLファクトデータを取得

**パラメータ:**
- `ticker` (必須): 銘柄ティッカー

### `get_edgar_company_concept`
特定の財務コンセプトの時系列を取得。単位 (`USD` / `shares` / `pure` 等) に応じて
書式を変え、期間の長さ（四半期/通年）を区別して表示する。

**パラメータ:**
- `ticker` (必須): 銘柄ティッカー
- `concept` (必須): XBRLコンセプト (例: `Assets`, `Revenues`, `NetIncomeLoss`)
- `taxonomy`: タクソノミー (デフォルト: `us-gaap`)

### `get_edgar_filing_content`
ファイリング本文を取得。HTML/インラインXBRLはテキスト変換**後**に `max_length` を適用。

**パラメータ:**
- `ticker` (必須), `accession_number` (必須), `primary_document` (必須)
- `max_length`: 変換後テキストの最大長 (デフォルト: 50,000)

### `get_multiple_edgar_filing_contents`
複数ファイリング本文の一括取得

**パラメータ:**
- `ticker` (必須): 銘柄ティッカー
- `filings_data` (必須): `[{"accession_number": ..., "primary_document": ...}, ...]`
- `max_length`: 各ドキュメントの取得上限 (デフォルト: 5,000)
- `preview_length`: 表示上限。省略時は取得した全文字を表示

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
- `min_volume`: 最低出来高（**当日**出来高、`sh_curvol_*` に変換）
- `sectors`: 対象セクター
- `max_results`: 最大取得件数 (デフォルト: 50)

`below` は `ta_sma*_pb` として実際に送られる。条件を何も指定しない場合は全銘柄が
対象になるため、返すのはティッカー昇順の先頭 `max_results` 件で、一致総数も併記する。

### `get_moving_average_position`
指定銘柄の現在値と20/50/200日移動平均線との位置関係

**パラメータ:**
- `ticker` (必須): 銘柄ティッカー

FinvizのSMA列は「現在値からの乖離率(%)」なので、表示する絶対価格は
現在値と乖離率から算出した派生値。

### `custom_screener`
生のFinvizフィルタトークンを直接指定するスクリーニング

**パラメータ:**
- `filters` (必須): カンマ区切りの生フィルタ (例: `"cap_large,fa_div_o3"`)
- `signal`: Finvizシグナル (例: `ta_topgainers`, `ta_unusualvolume`)
- `order`: ソート順 (例: `-marketcap`、`change`)
- `max_results`: 最大取得件数 (1-500、デフォルト: 50)

出力カラムは固定（指定できない）。

## 🔧 ユーティリティ

### `get_capitalization_performance`
時価総額別パフォーマンス分析

**パラメータ:** なし

### `get_sector_specific_industry_performance`
特定セクター内の業界別パフォーマンス分析

**パラメータ:**
- `sector` (必須): セクター名

## 🧭 フィールド探索

`data_fields` に指定できる名前を調べるツール群（全150カラム）。

### `list_available_fields`
全フィールドをカテゴリ別に列挙（省略なし）。**パラメータ:** なし

### `get_field_categories`
同じフィールドをカテゴリごとに1行でまとめて表示。**パラメータ:** なし

### `describe_field`
1フィールドの詳細（表示名・カテゴリ・CSV列名・解釈・関連フィールド）

**パラメータ:**
- `field_name` (必須): フィールド名。マッピング名・別名 (`net_margin`)・
  結果キー (`p_e`, `eps_ttm`) のいずれでもよく、正規のフィールドに解決して表示する
  （要求した綴りも併記）。カテゴリは他の探索ツールと同じ導出定義を使う。

### `search_fields`
キーワード検索

**パラメータ:**
- `keyword` (必須): 検索語
- `category`: カテゴリ絞り込み。短縮名 (`basic`, `valuation`, `growth`/`earnings`,
  `ownership`, `fundamental`, `performance`, `technical`, `trading`, `company`,
  `intraday`, `etf`, `etf_flows`, `news`, `long_term`) または
  `get_field_categories()` が表示する正式名（例 `Technical Indicators`）。大文字小文字不問。

カテゴリの所属は `list_available_fields` / `get_field_categories` と**同一**の
（列ID範囲から導出した）定義。未知のカテゴリ名は0件ではなくエラーとして返す。

### `validate_fields`
フィールド名の妥当性チェックと訂正候補の提示

**パラメータ:**
- `field_names` (必須): フィールド名のリスト

判定は `get_stock_fundamentals` 等が実際に使う判定と**同一**（別名・結果キー・
派生キー・`all` を含む）。以前はマッピング名しか通さず、実際には動くリクエストを
「無効」と報告していた。

## 📋 使用例

### 基本的なスクリーニング
```python
# 決算発表予定銘柄を検索
earnings_screener(
    earnings_date="today_after",
    market_cap="large",
    min_price=50
)

# 出来高急増銘柄を検索（条件は固定、引数なし）
volume_surge_screener()
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