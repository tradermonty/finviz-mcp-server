# Finviz MCP Server - Test Suite

このディレクトリには、Finviz MCP Serverの包括的なテストスイートが含まれています。全22個のMCPツール機能を網羅的にテストし、様々なパラメーター組み合わせ、エラーハンドリング、統合テストを提供します。

## テストファイル構成

### 1. `test_e2e_screeners.py`
**エンドツーエンド (E2E) テスト**
- 全22個のMCPツール機能をテスト
- 基本的な機能動作を検証
- 各スクリーナーの基本パラメーターをテスト

**テスト対象ツール:**
- Earnings Screeners (4種類)
- Volume & Trend Screeners (4種類)  
- Fundamental Data Tools (2種類)
- News Functions (3種類)
- Market Analysis Tools (5種類)
- Technical Analysis Tools (4種類)

### 2. `test_parameter_combinations.py`
**パラメーター組み合わせテスト**
- 様々なパラメーター組み合わせを系統的にテスト
- 境界値テスト
- 大規模データでのパフォーマンステスト
- セクター組み合わせの網羅的テスト

**主要テストケース:**
- 価格範囲の組み合わせ (最小価格、最大価格)
- 出来高フィルターの組み合わせ
- 時価総額 × セクターの組み合わせ
- テクニカル指標の複合条件
- 大量ティッカーリストでのテスト

### 3. `test_error_handling.py`
**エラーハンドリング・エッジケーステスト**
- 入力値検証テスト
- ネットワークエラーハンドリング
- データ検証・サニタイゼーション
- 並行処理とパフォーマンス
- リソース管理

**エラーシナリオ:**
- 無効なティッカー形式
- 不正なパラメーター値
- ネットワーク接続エラー
- HTTPエラー (400, 401, 403, 404, 429, 500, 503)
- レート制限エラー
- 不正なレスポンス形式

### 4. `test_mcp_integration.py`
**MCP統合テスト**
- MCPプロトコル準拠テスト
- サーバー初期化テスト
- ツール登録・メタデータ検証
- データシリアライゼーション
- 並行処理テスト

**統合テスト項目:**
- 全ツールの登録確認
- パラメーター検証統合
- レスポンス形式検証
- 特殊文字・Unicode対応
- 大容量データのシリアライゼーション

## 使用方法

### 1. 基本的なテスト実行

```bash
# 全テストを実行
python run_tests.py all

# 特定のテストカテゴリを実行
python run_tests.py e2e          # E2Eテスト
python run_tests.py params       # パラメーター組み合わせテスト
python run_tests.py errors       # エラーハンドリングテスト
python run_tests.py integration  # MCP統合テスト

# スモークテスト (クイック検証)
python run_tests.py smoke

# パフォーマンステスト
python run_tests.py performance
```

### 2. pytestを直接使用

```bash
# 全テストを実行
pytest tests/ -v

# 特定のテストファイルを実行
pytest tests/test_e2e_screeners.py -v
pytest tests/test_parameter_combinations.py -v
pytest tests/test_error_handling.py -v
pytest tests/test_mcp_integration.py -v

# 特定のテストクラス・メソッドを実行
pytest tests/test_e2e_screeners.py::TestFinvizScreenersE2E::test_earnings_screener_basic -v

# 失敗時に詳細を表示
pytest tests/ -v --tb=long

# 最初の失敗で停止
pytest tests/ -x
```

### 3. カバレッジ付きテスト

```bash
# カバレッジレポート付きテスト
python run_tests.py coverage

# またはpytestで直接
pytest tests/ --cov=src --cov-report=html --cov-report=term
```

### 4. 並行実行

```bash
# 並行実行 (pytest-xdist使用)
pytest tests/ -n auto

# 4プロセスで並行実行
pytest tests/ -n 4
```

## テスト環境セットアップ

### 1. 依存関係のインストール

```bash
# 開発依存関係をインストール
pip install -e .[dev]

# または個別にインストール
pip install pytest pytest-asyncio pytest-cov
```

### 2. 環境変数設定

```bash
# テスト用の環境変数設定 (オプション)
export FINVIZ_API_KEY=your_test_api_key
export LOG_LEVEL=DEBUG
export RATE_LIMIT_REQUESTS_PER_MINUTE=50
```

## テストデータとモック

### モックデータ構造

全テストは実際のFinvizサーバーに接続せず、モックデータを使用します：

```python
mock_stock_data = {
    "ticker": "AAPL",
    "company": "Apple Inc.",
    "sector": "Technology",
    "industry": "Consumer Electronics",
    "price": 150.0,
    "volume": 50000000,
    "market_cap": 2400000000000,
    "pe_ratio": 25.5,
    "eps": 6.0,
    "dividend_yield": 0.5,
}
```

### テストパターン

1. **正常系テスト**: 期待される入力での動作確認
2. **異常系テスト**: 無効な入力でのエラーハンドリング確認
3. **境界値テスト**: 最小・最大値での動作確認
4. **組み合わせテスト**: 複数パラメーターの組み合わせ確認

## CI/CD統合

### GitHub Actions設定例

```yaml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -e .[dev]
      - run: python run_tests.py all
```

## パフォーマンス指標

### テスト実行時間の目安

- **E2Eテスト**: ~30秒 (50+ テストケース)
- **パラメーター組み合わせテスト**: ~45秒 (100+ テストケース)
- **エラーハンドリングテスト**: ~20秒 (60+ テストケース)
- **MCP統合テスト**: ~15秒 (30+ テストケース)
- **全テスト**: ~2分 (240+ テストケース)

### 並行実行での改善

```bash
# 標準実行: ~2分
pytest tests/ -v

# 並行実行: ~30秒
pytest tests/ -n auto -v
```

## トラブルシューティング

### よくある問題

1. **ModuleNotFoundError**
   ```bash
   # プロジェクトルートから実行
   cd /path/to/finviz-mcp-server
   python -m pytest tests/
   ```

2. **Import Error**
   ```bash
   # 開発モードでインストール
   pip install -e .
   ```

3. **テストタイムアウト**
   ```bash
   # タイムアウト時間を延長
   pytest tests/ --timeout=300
   ```

4. **メモリ不足**
   ```bash
   # 並行数を制限
   pytest tests/ -n 2
   ```

## 継続的改善

### テストの追加

新しい機能を追加する際は、対応するテストも追加してください：

1. `test_e2e_screeners.py` - 基本機能テスト
2. `test_parameter_combinations.py` - パラメーター組み合わせテスト
3. `test_error_handling.py` - エラーケーステスト
4. `test_mcp_integration.py` - MCP統合テスト

### テストカバレッジ目標

- **ライン カバレッジ**: 90%以上
- **ブランチ カバレッジ**: 85%以上
- **関数 カバレッジ**: 95%以上

### コードクオリティ

```bash
# コード品質チェック
python run_tests.py lint    # flake8, black
python run_tests.py types   # mypy
```

## 参考資料

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [MCP Protocol Specification](https://spec.modelcontextprotocol.io/)
- [Finviz API Documentation](https://finviz.com/help/technical-analysis)

---

**注意**: このテストスイートは開発・テスト環境での使用を想定しています。本番環境では実際のFinviz APIを使用してください。