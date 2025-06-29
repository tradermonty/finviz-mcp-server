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
   # 出来高3倍以上、価格5%以上上昇
   finviz_volume_surge_screener(
       min_relative_volume=3.0,
       min_price_change=5.0
   )
   ```

3. **上昇トレンド銘柄スクリーニング**
   ```python
   # 200日移動平均線上の強いトレンド
   finviz_uptrend_screener(
       trend_type="strong_uptrend",
       sma_period="200"
   )
   ```

4. **配当成長銘柄スクリーニング**
   ```python
   # 配当利回り3%以上、ROE15%以上
   finviz_dividend_growth_screener(
       min_dividend_yield=3.0,
       min_roe=15.0
   )
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
   finviz_earnings_premarket_screener(
       earnings_timing="today_before",
       min_price_change=2.0
   )
   ```

7. **時間外決算上昇銘柄**
   ```python
   finviz_earnings_afterhours_screener(
       earnings_timing="today_after",
       min_afterhours_change=3.0
   )
   ```

8. **決算トレード対象銘柄**
   ```python
   finviz_earnings_trading_screener(
       earnings_revision="eps_revenue_positive"
   )
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
    finviz_get_sector_performance(timeframe="1m")
    finviz_get_industry_performance(timeframe="1w")
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

# 決算後のポジティブサプライズ銘柄
surprises = finviz_earnings_positive_surprise_screener(
    earnings_period="this_week",
    min_price=20.0
)
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
- [ツールリファレンス](TOOLS_REFERENCE.md)

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

#### 決算サプライズ好材料
```python
earnings_positive_surprise_screener(
    earnings_period="this_week",
    growth_criteria={
        "min_eps_qoq_growth": 15.0,
        "min_sales_qoq_growth": 8.0
    },
    performance_criteria={
        "above_sma200": True,
        "min_weekly_performance": 0.0
    }
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