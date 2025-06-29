# Finviz MCP Server セットアップガイド

## 1. 環境確認

Pythonがインストールされていることを確認:
```bash
python3 --version
```

## 2. 依存関係のインストール

```bash
pip3 install -r requirements.txt
```

## 3. 環境設定（オプション）

Finviz Elite APIキーを持っている場合:
```bash
cp .env.example .env
# .envファイルを編集してAPIキーを追加
```

## 4. 基本テストの実行

```bash
python3 test_basic.py
```

## 5. サーバーの起動

### 方法1: 直接起動
```bash
python3 run_server.py
```

### 方法2: モジュールとして起動
```bash
python3 -m src.server
```

## 6. MCP クライアントとの接続

サーバーが起動したら、MCP対応のクライアント（Claude Desktop等）から接続できます。

### Claude Desktop での設定例

`claude_desktop_config.json` に以下を追加:

```json
{
  "mcpServers": {
    "finviz": {
      "command": "python3",
      "args": ["/path/to/finviz-mcp-server/run_server.py"],
      "env": {}
    }
  }
}
```

## 7. 利用可能なツール

### 基本的なスクリーニング
- `earnings_screener`: 決算発表予定銘柄
- `volume_surge_screener`: 出来高急増銘柄
- `get_stock_fundamentals`: 個別銘柄データ
- `get_multiple_stocks_fundamentals`: 複数銘柄一括取得

### 高度なスクリーニング（設計書に基づく）
- `earnings_premarket_screener`: 寄り付き前決算
- `earnings_afterhours_screener`: 引け後決算
- `earnings_trading_screener`: 決算トレード対象

## 8. 使用例

### 決算スクリーニング
```
earnings_screener(
    earnings_date="today_after",
    market_cap="large", 
    min_price=10,
    sectors=["Technology"]
)
```

### 出来高急増銘柄
```
volume_surge_screener(
    min_relative_volume=2.0,
    min_price_change=5.0,
    market_cap="mid"
)
```

### 個別銘柄データ
```
get_stock_fundamentals(ticker="AAPL")
```

## 9. トラブルシューティング

### 依存関係エラー
```bash
pip3 install --upgrade pip
pip3 install -r requirements.txt
```

### 環境変数の問題
.envファイルが正しく設置されているか確認

### レート制限エラー
Finviz Elite APIキーを設定するか、リクエスト間隔を調整

## 10. ログとデバッグ

ログレベルを変更するには、環境変数を設定:
```bash
export LOG_LEVEL=DEBUG
python3 run_server.py
```

## 注意事項

1. このツールは教育・研究目的のものです
2. 投資判断は自己責任で行ってください
3. Finvizの利用規約を遵守してください
4. 過度なリクエストを避け、適切な間隔でAPIを使用してください 