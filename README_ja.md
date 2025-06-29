# Finviz MCP Server

[English](README.md) | **日本語**

**Finviz MCP Server**は、Finvizのスクリーニング機能を利用して株式データを取得し、分析を行うためのMCP（Model Context Protocol）サーバーです。

## 🚀 新機能：完全なカラム対応（128カラム）

**2024年版：Finvizの全128カラムに完全対応！**

### 📊 サポートされるデータフィールド

提供されたFinvizカラムリストに完全対応：

#### 基本情報・市場データ
- No., Ticker, Company, Index, Sector, Industry, Country
- Market Cap, P/E, Forward P/E, PEG, P/S, P/B, P/Cash, P/Free Cash Flow
- Book/sh, Cash/sh, Dividend, Dividend Yield, Payout Ratio

#### 収益性・成長指標
- EPS (ttm), EPS Next Q, EPS Growth (This/Next/Past 5 Years)
- Sales Growth (Past 5 Years, Quarter Over Quarter)
- Return on Assets, Return on Equity, Return on Invested Capital
- Gross/Operating/Profit Margin

#### 技術指標・パフォーマンス
- **短時間パフォーマンス**: 1分〜4時間
- **長期パフォーマンス**: 週次〜10年、設定来
- Beta, Average True Range, Volatility (Week/Month)
- 移動平均線（20/50/200日）、52週高値・安値

#### 株式・取引情報
- Shares Outstanding/Float, Float %, Insider/Institutional Ownership
- Short Float/Ratio/Interest, Optionable, Shortable
- Volume, Average Volume, Relative Volume, Trades
- Target Price, Analyst Recommendation

#### 詳細OHLC・時間外取引
- Prev Close, Open, High, Low, Change from Open
- After-Hours Close/Change, Gap

#### ETF専用フィールド
- Asset Type, ETF Type, Sector/Theme, Region, Active/Passive
- Net Expense Ratio, Total Holdings, Assets Under Management
- Net Asset Value, Net Flows (1M/3M/YTD/1Y)
- All-Time High/Low, Return Since Inception

## 🔧 機能一覧

### 📈 スクリーニング機能

1. **決算発表予定銘柄スクリーニング**
   ```python
   # 今日の決算発表予定銘柄
   finviz_earnings_screener(earnings_date="today_after")
   ```

2. **出来高急増銘柄スクリーニング**
   ```python
   # デフォルト条件適用：スモール以上、出来高1.5倍以上、価格2%以上上昇等
   finviz_volume_surge_screener()
   
   # 追加条件でカスタマイズ
   finviz_volume_surge_screener(
       min_relative_volume=3.0,
       min_price_change=5.0,
       sectors=["Technology", "Healthcare"]
   )
   
   # デフォルト条件:
   # - 時価総額: スモール以上 ($300M+)
   # - 株式のみ: ETF除外
   # - 平均出来高: 100,000以上
   # - 株価: $10以上
   # - 相対出来高: 1.5倍以上
   # - 価格変動: 2%以上上昇
   # - 200日移動平均線上
   # - 価格変動降順ソート
   ```

3. **上昇トレンド銘柄スクリーニング**
   ```python
   # デフォルト条件適用：スモール以上、100K出来高以上、株価10以上等
   finviz_uptrend_screener()
   
   # 追加条件でカスタマイズ
   finviz_uptrend_screener(
       trend_type="strong_uptrend",
       sma_period="200",
       sectors=["Technology", "Healthcare"]
   )
   
   # デフォルト条件:
   # - 時価総額: スモール以上 ($300M+)
   # - 平均出来高: 100,000以上
   # - 株価: $10以上
   # - 52週高値から30%以内
   # - 4週パフォーマンス上昇
   # - 20日・200日移動平均線上
   # - 50日移動平均線が200日移動平均線上
   # - EPS成長率（年次）降順ソート
   ```

4. **配当成長銘柄スクリーニング**
   ```python
   # デフォルト条件適用：ミッド以上、配当利回り2%以上、成長率プラス等
   finviz_dividend_growth_screener()
   
   # 追加条件でカスタマイズ
   finviz_dividend_growth_screener(
       min_dividend_yield=3.0,
       min_roe=15.0,
       max_pe_ratio=20.0
   )
   
   # デフォルト条件:
   # - 時価総額: ミッド以上 ($2B+)
   # - 配当利回り: 2%以上
   # - EPS 5年成長率: プラス
   # - EPS QoQ成長率: プラス
   # - EPS YoY成長率: プラス
   # - PBR: 5以下
   # - PER: 30以下
   # - 売上5年成長率: プラス
   # - 売上QoQ成長率: プラス
   # - 地域: アメリカ
   # - 株式のみ
   # - 200日移動平均でソート
   ```

5. **ETF戦略スクリーニング**
   ```python
   # 株式ETF、経費率0.5%以下
   finviz_etf_screener(
       asset_class="equity",
       max_expense_ratio=0.5
   )
   ```

### 📊 決算関連特化機能

6. **寄り付き前決算上昇銘柄**
   ```python
   # デフォルト条件適用：スモール以上、寄り付き前決算、価格2%以上上昇等
   finviz_earnings_premarket_screener()
   
   # 追加条件でカスタマイズ
   finviz_earnings_premarket_screener(
       earnings_timing="today_before",
       min_price_change=3.0,
       sectors=["Technology", "Healthcare"]
   )
   
   # デフォルト条件:
   # - 時価総額: スモール以上 ($300M+)
   # - 決算発表: 今日の寄り付き前
   # - 平均出来高: 100,000以上
   # - 株価: $10以上
   # - 価格変動: 2%以上上昇
   # - 株式のみ
   # - 価格変動降順ソート
   # - 最大結果件数: 60件
   ```

7. **時間外決算上昇銘柄**
   ```python
   # デフォルト条件適用：スモール以上、引け後決算、時間外2%以上上昇等
   finviz_earnings_afterhours_screener()
   
   # 追加条件でカスタマイズ
   finviz_earnings_afterhours_screener(
       earnings_timing="today_after",
       min_afterhours_change=3.0,
       sectors=["Technology", "Healthcare"]
   )
   
   # デフォルト条件:
   # - 時間外取引変動: 2%以上上昇
   # - 時価総額: スモール以上 ($300M+)
   # - 決算発表: 今日の引け後
   # - 平均出来高: 100,000以上
   # - 株価: $10以上
   # - 株式のみ
   # - 時間外変動降順ソート
   # - 最大結果件数: 60件
   ```

8. **決算トレード対象銘柄**
   ```python
   # デフォルト条件適用：スモール以上、昨日引け後・今日寄り付き前決算、EPS上方修正等
   finviz_earnings_trading_screener()
   
   # 追加条件でカスタマイズ
   finviz_earnings_trading_screener(
       earnings_window="yesterday_after_today_before",
       earnings_revision="eps_revenue_positive",
       min_volatility=1.5,
       sectors=["Technology", "Healthcare"]
   )
   
   # デフォルト条件:
   # - 時価総額: スモール以上 ($300M+)
   # - 決算発表: 昨日の引け後または今日の寄り付き前
   # - EPS予想: 上方修正
   # - 平均出来高: 200,000以上
   # - 株価: $10以上
   # - 価格変動: 上昇トレンド
   # - 4週パフォーマンス: 0%から下落（下落後回復候補）
   # - ボラティリティ: 1倍以上
   # - 株式のみ: ETF除外
   # - ソート: EPSサプライズ降順
   # - 最大結果件数: 60件
   ```

### 📄 SECファイリング情報

9. **SECファイリング取得**
   ```python
   # 指定銘柄の全SECファイリング
   get_sec_filings(ticker="MSFT", days_back=30)
   
   # 特定フォームのみ取得
   get_sec_filings(
       ticker="MSFT",
       form_types=["10-K", "10-Q", "8-K"],
       days_back=90
   )
   ```

10. **主要SECファイリング**
    ```python
    # 10-K、10-Q、8-K等の主要フォーム
    get_major_sec_filings(ticker="MSFT", days_back=90)
    ```

11. **インサイダー取引情報**
    ```python
    # フォーム3、4、5のインサイダー情報
    get_insider_sec_filings(ticker="MSFT", days_back=30)
    ```

12. **SECファイリング概要**
    ```python
    # 期間別ファイリング統計
    get_sec_filing_summary(ticker="MSFT", days_back=90)
    ```

### 🎯 高度な分析機能

9. **個別銘柄詳細分析**
   ```python
   # 全128フィールドを取得
   finviz_get_stock_fundamentals(
       ticker="AAPL",
       data_fields=["all"]  # 全フィールド取得
   )
   ```

10. **複数銘柄一括分析**
    ```python
    finviz_get_multiple_stocks_fundamentals(
        tickers=["AAPL", "GOOGL", "MSFT"],
        data_fields=["pe_ratio", "eps_growth_next_y", "target_price"]
    )
    ```

### 📰 ニュース・市場分析

11. **銘柄関連ニュース**
    ```python
    finviz_get_stock_news(ticker="TSLA", days_back=7)
    ```

12. **セクター・業界パフォーマンス**
    ```python
    # 基本セクター・業界・国別パフォーマンス
    finviz_get_sector_performance()
    finviz_get_industry_performance()
    finviz_get_country_performance()
    
    # 特定セクター内の業界別パフォーマンス（新機能）
    finviz_get_sector_specific_industry_performance(
        sector="technology"
    )
    
    # 時価総額別パフォーマンス（新機能）
    finviz_get_capitalization_performance()
    
    # 利用可能なセクター:
    # - basicmaterials (基本素材)
    # - communicationservices (通信サービス)
    # - consumercyclical (消費者サイクリカル) 
    # - consumerdefensive (消費者ディフェンシブ)
    # - energy (エネルギー)
    # - financial (金融)
    # - healthcare (ヘルスケア)
    # - industrials (工業)
    # - realestate (不動産)
    # - technology (テクノロジー)
    # - utilities (公益事業)
    
    # 注意: Finviz APIの制限により、期間別パフォーマンスではなく
    # 現在時点のスナップショット情報（Market Cap、P/E、Change等）を取得
    ```

## 🔍 使用例

### 包括的な銘柄分析

```python
# 高成長テック株の包括的分析
results = finviz_volume_surge_screener(
    sectors=["Technology"],
    min_price_change=5.0,
    min_relative_volume=2.0,
    min_eps_growth_next_y=20.0
)

# 各銘柄の詳細データを取得（128フィールド対応）
for stock in results[:5]:  # 上位5銘柄
    details = finviz_get_stock_fundamentals(
        ticker=stock['ticker'],
        data_fields=[
            "forward_pe", "peg", "roic", "eps_growth_next_5y",
            "target_price", "analyst_recommendation",
            "volatility_week", "rsi", "performance_ytd"
        ]
    )
    print(f"{stock['ticker']}: {details}")
```

### 決算シーズン戦略

```python
# 来週決算予定の注目銘柄
upcoming = finviz_upcoming_earnings_screener(
    earnings_period="next_week",
    min_avg_volume=1000000,
    target_sectors=["Technology", "Healthcare"]
)


```

### SECファイリング分析

```python
# 主要企業のSECファイリング分析
major_filings = get_major_sec_filings(
    ticker="AAPL",
    days_back=90
)

# インサイダー取引の監視
insider_activity = get_insider_sec_filings(
    ticker="TSLA", 
    days_back=30
)

# 決算関連ファイリングの確認
earnings_filings = get_sec_filings(
    ticker="MSFT",
    form_types=["10-Q", "8-K"],
    days_back=60
)

# ファイリング概要で全体把握
filing_summary = get_sec_filing_summary(
    ticker="GOOGL",
    days_back=120
)
```

## 🆕 新機能：拡張されたセクター・業界分析

### セクター・業界パフォーマンス分析の全オプション対応

HTMLセレクトタグから抽出されたFinvizの全パフォーマンス分析オプションに対応：

#### 1. 基本分析
- **セクター全体** (`get_sector_performance`)
- **業界全体** (`get_industry_performance`) 
- **国別** (`get_country_performance`)
- **時価総額別** (`get_capitalization_performance`) ← **新機能**

#### 2. セクター別業界分析 (`get_sector_specific_industry_performance`) ← **新機能**
特定セクター内の業界別詳細パフォーマンス：

- **基本素材** (basicmaterials)
- **通信サービス** (communicationservices)
- **消費者サイクリカル** (consumercyclical)
- **消費者ディフェンシブ** (consumerdefensive)
- **エネルギー** (energy)
- **金融** (financial)
- **ヘルスケア** (healthcare)
- **工業** (industrials)
- **不動産** (realestate)
- **テクノロジー** (technology)
- **公益事業** (utilities)

#### 3. データ取得について
Finviz APIの実際の構造に合わせ、現在時点のスナップショット情報を取得：
- **Market Cap** (時価総額)
- **P/E Ratio** (PER)
- **Dividend Yield** (配当利回り)
- **Change** (価格変動)
- **Stock Count** (銘柄数)

#### 4. 使用例
```python
# テクノロジーセクター内の業界別パフォーマンス
finviz_get_sector_specific_industry_performance(
    sector="technology"
)

# 時価総額別パフォーマンス（Large Cap, Mid Cap等）
finviz_get_capitalization_performance()
```

## 📋 システム要件

- Python 3.8+
- pandas, requests, beautifulsoup4
- MCol Context Protocol対応環境

## 🛠️ インストール

```bash
git clone https://github.com/your-repo/finviz-mcp-server.git
cd finviz-mcp-server
pip install -r requirements.txt
```

## 🚀 起動方法

```bash
python run_server.py
```

## 📚 詳細ドキュメント

- [設計書](docs/finviz_mcp_server_design.md)
- [スクリーニングパラメータ](docs/finviz_screening_parameters.md)
- [実装完了レポート](docs/IMPLEMENTATION_COMPLETE.md)
- [ツールリファレンス](docs/tools_reference.md)

## 🎯 主な特徴

### ✅ 完全なFinviz対応
- **128カラム完全サポート**：No.からTagsまで全フィールド
- **ETF専用フィールド**：Net Flows、AUM、経費率など
- **短時間パフォーマンス**：分単位から時間単位まで
- **詳細OHLC**：Prev Close、Open、High、Low

### ✅ 高度なスクリーニング
- 15種類の専門的スクリーニング戦略
- 決算トレード特化機能
- セクター・業界分析
- リアルタイム市場データ

### ✅ 柔軟なデータ取得
- 個別銘柄詳細分析
- 複数銘柄一括処理
- カスタムフィールド選択
- 高速CSV export対応

## 🔄 アップデート履歴

### v2.1.0 (2024) - セクター・業界分析修正
- Finviz APIの実際の構造に合わせたパラメータ修正
- 時間枠パラメータの削除（v=152固定値対応）
- 決算トレード対象銘柄のデフォルト条件設定
- セクター・業界・国別・時価総額別分析の統一フォーマット

### v2.0.0 (2024) - 完全カラム対応
- Finviz全128カラムに完全対応
- ETF専用フィールド追加
- 短時間パフォーマンス対応
- 詳細OHLC・時間外取引データ

### v1.0.0 (2024) - 初期リリース
- 基本スクリーニング機能
- 決算分析機能
- ニュース取得機能

## インストール

### 前提条件
- Python 3.11以上
- **Finviz Elite契約**（フル機能の利用に必要）
- Finviz APIキー（オプション、ただしレート制限の向上のため推奨）

> **重要**: このMCPサーバーは、包括的なスクリーニングとデータ機能にアクセスするためにFinviz Eliteの契約が必要です。Finviz Eliteの詳細と契約オプションについては、こちらをご覧ください: https://elite.finviz.com/elite.ashx

### セットアップ

1. **プロジェクトのクローンとセットアップ:**
```bash
# リポジトリをクローン
git clone <repository-url>
cd finviz-mcp-server

# Python 3.11で仮想環境を作成
python3.11 -m venv venv

# 仮想環境をアクティベート
source venv/bin/activate  # macOS/Linux
# または
venv\\Scripts\\activate     # Windows

# 開発モードでパッケージをインストール
pip install -e .
```

2. **環境変数の設定:**
```bash
# サンプル環境ファイルをコピー
cp .env.example .env

# .envファイルを編集してFinviz APIキーを追加
FINVIZ_API_KEY=your_actual_api_key_here
```

3. **インストールのテスト:**
```bash
# サーバーが正しく起動するかテスト（停止するにはCtrl+C）
finviz-mcp-server

# stdio モードでサーバーが起動することを確認
```

## 設定

サーバーは環境変数で設定できます：

- `FINVIZ_API_KEY`: Finviz Elite APIキー（Elite機能に必要、レート制限を改善）
- `MCP_SERVER_PORT`: サーバーポート（デフォルト: 8080）
- `LOG_LEVEL`: ログレベル（デフォルト: INFO）
- `RATE_LIMIT_REQUESTS_PER_MINUTE`: レート制限（デフォルト: 100）

> **注意**: APIキーは技術的にはオプションですが、高度なスクリーニング機能の多くは、Finviz Eliteの契約とAPIキーが適切に機能するために必要です。

## 使用方法

### MCPサーバーの実行

サーバーはstdioベースのMCPサーバーとして動作します：

```bash
# 仮想環境がアクティベートされていることを確認
source venv/bin/activate

# サーバーを実行
finviz-mcp-server
```

### Claude Desktopとの統合

Claude DesktopのMCP設定ファイル（macOSでは `~/Library/Application Support/Claude/claude_desktop_config.json`）にサーバーを追加します：

```json
{
  "mcpServers": {
    "finviz": {
      "command": "/path/to/your/project/venv/bin/finviz-mcp-server",
      "args": [],
      "cwd": "/path/to/your/project/finviz-mcp-server",
      "env": {
        "FINVIZ_API_KEY": "your_api_key_here",
        "LOG_LEVEL": "INFO",
        "RATE_LIMIT_REQUESTS_PER_MINUTE": "100"
      }
    }
  }
}
```

**重要な設定注意事項:**
- `/path/to/your/project/` を実際のプロジェクトパスに置き換えてください
- 仮想環境内の `finviz-mcp-server` 実行可能ファイルの絶対パスを使用してください
- `cwd`（現在の作業ディレクトリ）をプロジェクトルートに設定してください
- `your_api_key_here` を実際のFinviz APIキーに置き換えてください

**代替方法: .envファイルの使用**
`.env`ファイルを使用する場合（セキュリティのため推奨）：

```json
{
  "mcpServers": {
    "finviz": {
      "command": "/path/to/your/project/venv/bin/finviz-mcp-server",
      "args": [],
      "cwd": "/path/to/your/project/finviz-mcp-server"
    }
  }
}
```

`.env`ファイルに必要な環境変数がすべて含まれていることを確認してください。

### MCPツール

#### 決算スクリーナー
```python
# 今日の場後に決算発表予定の銘柄を検索
earnings_screener(
    earnings_date="today_after",
    market_cap="large",
    min_price=10,
    min_volume=1000000,
    sectors=["Technology", "Healthcare"]
)
```

#### 出来高急増スクリーナー
```python
# 高出来高と価格上昇を示す銘柄を検索
volume_surge_screener(
    market_cap="smallover",
    min_price=10,
    min_relative_volume=1.5,
    min_price_change=2.0,
    sma_filter="above_sma200"
)
```

#### 株式ファンダメンタルズ
```python
# 単一銘柄のファンダメンタルデータを取得
get_stock_fundamentals(
    ticker="AAPL",
    data_fields=["pe_ratio", "eps", "dividend_yield", "market_cap"]
)

# 複数銘柄のファンダメンタルデータを取得
get_multiple_stocks_fundamentals(
    tickers=["AAPL", "MSFT", "GOOGL"],
    data_fields=["pe_ratio", "eps", "market_cap"]
)
```

## 高度なスクリーニング例

### 決算ベース戦略

#### プレマーケット決算モメンタム
```python
earnings_premarket_screener(
    earnings_timing="today_before",
    market_cap="large",
    min_price=25,
    min_price_change=2.0,
    include_premarket_data=True
)
```

#### アフターアワーズ決算反応
```python
earnings_afterhours_screener(
    earnings_timing="today_after",
    min_afterhours_change=5.0,
    market_cap="mid",
    include_afterhours_data=True
)
```



### テクニカル分析戦略

#### トレンド反転候補
```python
trend_reversion_screener(
    market_cap="large",
    eps_growth_qoq=10.0,
    rsi_max=30,
    sectors=["Technology", "Healthcare"]
)
```

#### 強い上昇トレンド株
```python
uptrend_screener(
    trend_type="strong_uptrend",
    sma_period="20",
    relative_volume=2.0,
    price_change=5.0
)
```

### バリュー投資戦略

#### 配当成長
```python
dividend_growth_screener(
    min_dividend_yield=2.0,
    max_dividend_yield=6.0,
    min_dividend_growth=5.0,
    min_roe=15.0
)
```

## データモデル

### StockData
以下を含む包括的な株式情報：
- 基本情報（ティッカー、会社名、セクター、業界）
- 価格・出来高データ
- テクニカル指標（RSI、ベータ、移動平均）
- ファンダメンタル指標（P/E、EPS、配当利回り）
- 決算データ（サプライズ、予想、成長率）
- パフォーマンス指標（1週間、1ヶ月、年初来）

### スクリーニング結果
以下を含む構造化された結果：
- 使用されたクエリパラメータ
- 一致する銘柄のリスト
- 総数と実行時間
- 読みやすくフォーマットされた出力

## エラーハンドリング

サーバーには包括的なエラーハンドリングが含まれています：
- 全パラメータの入力値検証
- レート制限保護
- 再試行機能付きネットワークエラー回復
- 詳細なエラーメッセージとログ記録

## レート制限

Finvizサーバーへの配慮：
- リクエスト間のデフォルト1秒遅延
- 設定可能なレート制限
- 指数バックオフ付き自動再試行
- より高い制限のためのFinviz Elite APIキーサポート

## ログ記録

設定可能なログレベル：
- DEBUG: 詳細なリクエスト/レスポンス情報
- INFO: 一般的な操作情報（デフォルト）
- WARNING: 重要でない問題
- ERROR: 重大なエラー

## 貢献

1. リポジトリをフォーク
2. 機能ブランチを作成
3. 変更を加える
4. 該当する場合はテストを追加
5. プルリクエストを提出

## ライセンス

このプロジェクトはMITライセンスの下でライセンスされています - 詳細はLICENSEファイルを参照してください。

## 免責事項

このツールは教育および研究目的のためのものです。投資判断を行う前に、常に独自の調査を行ってください。本ソフトウェアの使用によって生じた金銭的損失について、作者は責任を負いません。

**Finviz Elite契約について**: このMCPサーバーは、フル機能を使用するためにFinviz Eliteの契約が必要です。無料のFinvizアカウントでは、スクリーニング機能とデータへのアクセスが制限されています。包括的な株式スクリーニング機能については、https://elite.finviz.com/elite.ashx でFinviz Eliteにご契約ください。

## サポート

問題や機能要求については、GitHubのissue trackerをご利用ください。

## 更新履歴

### v1.0.0
- 初回リリース
- 基本スクリーニングツールの実装
- ファンダメンタルデータ取得
- MCPサーバー統合
- 包括的なエラーハンドリングと検証

## 🔐 セキュリティ設定

### 環境変数の設定

このMCPサーバーはFinviz Elite APIキーが必要です。セキュリティ上の理由から、APIキーは環境変数で設定してください。

#### 方法1: 環境変数でAPIキーを設定

```bash
export FINVIZ_API_KEY="your_actual_api_key_here"
```

#### 方法2: .envファイルでAPIキーを設定

プロジェクトルートに`.env`ファイルを作成：

```bash
# .env
FINVIZ_API_KEY=your_actual_api_key_here
MCP_SERVER_DEBUG=false
```

**⚠️ 重要な注意事項:**
- APIキーは絶対にコードにハードコードしないでください
- `.env`ファイルは`.gitignore`に追加してください
- APIキーを誤ってGitHubにコミットした場合は、すぐにキーを無効化してください

### APIキーの取得

Finviz Elite APIキーは以下から取得できます：
https://elite.finviz.com/