# Finviz MCP Server

[English](README.md) | **日本語**

Finvizデータを使用した包括的な株式スクリーニングおよびファンダメンタル分析機能を提供するModel Context Protocol (MCP) サーバーです。

## 機能

### 株式スクリーニングツール
- **決算スクリーナー**: 決算発表予定の銘柄を検索
- **出来高急増スクリーナー**: 異常な出来高と価格変動を検出
- **トレンド分析**: 上昇トレンドとモメンタム株を特定
- **配当成長スクリーナー**: 成長性のある配当株を検索
- **ETFスクリーナー**: 上場投資信託をスクリーニング
- **プレマーケット/アフターアワーズ決算**: 時間外取引での決算反応を追跡

### ファンダメンタル分析
- 個別銘柄のファンダメンタルデータ取得
- 複数銘柄の比較
- セクター・業界のパフォーマンス分析
- ニュースとセンチメント追跡

### テクニカル分析
- RSI、ベータ、ボラティリティ指標
- 移動平均分析 (SMA 20/50/200)
- 相対出来高分析
- 52週高値/安値追跡

## インストール

### 前提条件
- Python 3.11以上
- Finviz APIキー（オプション、ただしレート制限の向上のため推奨）

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

- `FINVIZ_API_KEY`: Finviz Elite APIキー（オプション、レート制限を改善）
- `MCP_SERVER_PORT`: サーバーポート（デフォルト: 8080）
- `LOG_LEVEL`: ログレベル（デフォルト: INFO）
- `RATE_LIMIT_REQUESTS_PER_MINUTE`: レート制限（デフォルト: 100）

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

## サポート

問題や機能要求については、GitHubのissue trackerをご利用ください。

## 更新履歴

### v1.0.0
- 初回リリース
- 基本スクリーニングツールの実装
- ファンダメンタルデータ取得
- MCPサーバー統合
- 包括的なエラーハンドリングと検証