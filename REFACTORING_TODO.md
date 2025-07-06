# Finviz MCP Server リファクタリング TODO

## 📋 概要

このドキュメントは、Finviz MCP Serverの包括的なリファクタリング計画を記載します。現在のコードベースは機能的には優秀ですが、保守性、拡張性、テスタビリティの向上を目的とした段階的な改善が必要です。

**コードベース規模**: 約9,729行（ソース）+ 4,149行（テスト）+ 8,155行（ドキュメント）

---

## 🚨 緊急度の高い問題（High Priority）

### 1. **巨大メソッドの分割**
**ファイル**: `src/finviz_client/base.py`
**対象**: `_convert_filters_to_finviz`メソッド（500行超）

#### 問題
- 1つのメソッドで全フィルタータイプ（価格、出来高、PE比、RSI等）を処理
- 複雑度が非常に高く、テストが困難
- 新しいフィルタ追加時の影響範囲が広い

#### 解決策
```python
# 現在の巨大メソッドを以下に分割:
class FinvizFilterBuilder:
    def _convert_price_filters(self, filters: Dict) -> str:
        """価格関連フィルタの変換"""
        pass
    
    def _convert_volume_filters(self, filters: Dict) -> str:
        """出来高関連フィルタの変換"""
        pass
    
    def _convert_financial_ratio_filters(self, filters: Dict) -> str:
        """財務比率フィルタの変換（PE, PB, PS等）"""
        pass
    
    def _convert_technical_filters(self, filters: Dict) -> str:
        """テクニカル指標フィルタの変換（RSI, SMA等）"""
        pass
    
    def _convert_sector_filters(self, filters: Dict) -> str:
        """セクター/業界フィルタの変換"""
        pass
    
    def _convert_earnings_filters(self, filters: Dict) -> str:
        """決算関連フィルタの変換"""
        pass
```

#### タスク
- [ ] FilterBuilderクラスの設計と実装
- [ ] 既存メソッドの分割
- [ ] 単体テストの作成
- [ ] 既存機能の動作確認

---

### 2. **重複コードの排除**
**ファイル**: `src/finviz_client/base.py`
**対象**: レンジフィルター処理の重複

#### 問題
- 価格、出来高、PE比、配当利回り等で同一パターンが繰り返し（約200行の重複）
- 同じロジックの微細な差異がバグの原因となる可能性

#### 解決策
```python
def _build_range_filter(self, 
                       filter_prefix: str, 
                       min_val: Optional[Union[int, float, str]], 
                       max_val: Optional[Union[int, float, str]],
                       safe_conversion_func: Callable) -> str:
    """
    共通のレンジフィルタ構築ロジック
    
    Args:
        filter_prefix: フィルタープレフィックス（例: 'sh_price_', 'fa_pe_'）
        min_val: 最小値
        max_val: 最大値
        safe_conversion_func: 値変換関数
    
    Returns:
        Finviz形式のフィルター文字列
    """
    if min_val is None and max_val is None:
        return ""
    
    min_converted = safe_conversion_func(min_val) if min_val is not None else None
    max_converted = safe_conversion_func(max_val) if max_val is not None else None
    
    # Finvizプリセット形式の処理
    if min_converted and min_converted.startswith(('o', 'u')):
        return f'{filter_prefix}{min_converted},'
    elif max_converted and max_converted.startswith(('o', 'u')):
        return f'{filter_prefix}{max_converted},'
    
    # レンジ指定の処理
    if min_converted and max_converted:
        return f'{filter_prefix}{min_converted}to{max_converted},'
    elif min_converted:
        return f'{filter_prefix}{min_converted}to,'
    elif max_converted:
        return f'{filter_prefix}to{max_converted},'
    
    return ""
```

#### タスク
- [ ] 共通レンジフィルタメソッドの実装
- [ ] 各フィルタタイプでの適用
- [ ] リグレッションテストの実行
- [ ] コード行数の削減確認（目標: 200行削減）

---

### 3. **ハードコードされた設定の集約**
**ファイル**: 複数ファイルに散在
**対象**: Finvizパラメータの直書き

#### 問題
- URLパラメータ、カラムインデックス等が複数箇所にハードコード
- 設定変更時の影響範囲が広い
- Finviz API仕様変更への対応が困難

#### 解決策
```python
# src/config/finviz_config.py
class FinvizConfig:
    """Finviz API設定の集約クラス"""
    
    # API基本設定
    BASE_URL = "https://elite.finviz.com"
    EXPORT_URL = f"{BASE_URL}/export.ashx"
    QUOTE_EXPORT_URL = f"{BASE_URL}/quote_export.ashx"
    NEWS_EXPORT_URL = f"{BASE_URL}/news_export.ashx"
    
    # デフォルトパラメータ
    DEFAULT_VIEW = '151'  # 決算情報を含むビュー
    DEFAULT_SORT = '-ticker'
    
    # カラムインデックス（用途別）
    BASIC_COLUMNS = "0,1,2,3,4,5,6,7,8,9,10"
    EARNINGS_COLUMNS = "0,1,2,79,3,4,5,129,6,7,8,9,10,11,12,13"
    ALL_COLUMNS = "0,1,2,79,3,4,5,129,6,7,8,9,10,11,12,13,73,74,75,14..."
    
    # レート制限設定
    RATE_LIMIT_DELAY = 1.0
    MAX_RETRIES = 3
    REQUEST_TIMEOUT = 30
    
    # バッチサイズ制限
    MAX_RESULTS_PER_REQUEST = 1000
    BATCH_SIZE = 5
```

#### タスク
- [ ] 設定クラスの作成
- [ ] ハードコードされた値の特定と移行
- [ ] 環境変数サポートの追加
- [ ] 設定の動的読み込み機能

---

## 🔶 中程度の問題（Medium Priority）

### 4. **クラス責任の分離**
**ファイル**: `src/finviz_client/base.py`
**対象**: `FinvizClient`クラスの肥大化

#### 問題
- HTTP通信、CSV解析、データ変換、フィルタ変換を全て1つのクラスで担当
- 単一責任原則に違反
- テストの際のモック化が困難

#### 解決策
```python
# src/finviz_client/http_client.py
class FinvizHttpClient:
    """HTTP通信専門クラス"""
    def __init__(self, api_key: Optional[str] = None):
        pass
    
    def fetch_csv(self, params: Dict) -> requests.Response:
        """CSV データの取得"""
        pass
    
    def fetch_with_retry(self, url: str, params: Dict) -> requests.Response:
        """リトライ機能付きHTTPリクエスト"""
        pass

# src/finviz_client/data_parser.py
class FinvizDataParser:
    """データ解析専門クラス"""
    def parse_csv_to_stocks(self, csv_content: str) -> List[StockData]:
        """CSV から StockData リストへの変換"""
        pass
    
    def parse_single_stock(self, row: pd.Series) -> StockData:
        """単一行から StockData への変換"""
        pass

# src/finviz_client/filter_builder.py
class FinvizFilterBuilder:
    """フィルタ構築専門クラス"""
    def build_filters(self, filters: Dict) -> Dict[str, str]:
        """内部フィルタから Finviz パラメータへの変換"""
        pass
```

#### タスク
- [ ] 責任分離の設計
- [ ] 新クラスの実装
- [ ] 既存コードのリファクタリング
- [ ] インターフェースの統一
- [ ] 依存性注入の実装

---

### 5. **エラーハンドリングの標準化**
**ファイル**: `src/server.py`
**対象**: 各toolメソッドの例外処理

#### 問題
- 20+のtoolメソッドで同じパターンの例外処理が重複
- エラーメッセージの一貫性不足
- ログ出力の標準化が不十分

#### 解決策
```python
# src/utils/decorators.py
def finviz_tool_error_handler(log_context: str = ""):
    """Finviz tool用エラーハンドリングデコレータ"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                logger.info(f"Starting {func.__name__} {log_context}")
                result = func(*args, **kwargs)
                logger.info(f"Completed {func.__name__} successfully")
                return result
            except ValueError as e:
                error_msg = f"Validation error in {func.__name__}: {str(e)}"
                logger.error(error_msg)
                return [TextContent(type="text", text=f"Error: {str(e)}")]
            except Exception as e:
                error_msg = f"Unexpected error in {func.__name__}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        return wrapper
    return decorator

# 使用例
@server.tool()
@finviz_tool_error_handler("earnings screening")
def earnings_screener(earnings_date: str, ...) -> List[TextContent]:
    # バリデーションとビジネスロジックのみに集中
    pass
```

#### タスク
- [ ] エラーハンドリングデコレータの実装
- [ ] 全toolメソッドへの適用
- [ ] ログレベルの標準化
- [ ] エラーメッセージテンプレートの作成

---

### 6. **型安全性の向上**
**ファイル**: 複数ファイル
**対象**: `Optional[Union[int, float, str]]`の過度な使用

#### 問題
- Union型の乱用により型チェックの恩恵が薄い
- IDE支援が不十分
- ランタイムエラーの可能性

#### 解決策
```python
# src/types/finviz_types.py
from typing import Union, Literal, NewType
from dataclasses import dataclass

# より具体的な型定義
FinvizPresetValue = Literal['o5', 'o10', 'o50', 'u5', 'u10', 'u50']
NumericValue = Union[int, float]
PriceValue = Union[NumericValue, FinvizPresetValue]
VolumeValue = Union[NumericValue, FinvizPresetValue, str]  # レンジ指定対応

# カスタム型
TickerSymbol = NewType('TickerSymbol', str)
FinvizFilter = NewType('FinvizFilter', str)

@dataclass
class PriceRange:
    """価格範囲の型安全な表現"""
    min_price: Optional[PriceValue] = None
    max_price: Optional[PriceValue] = None
    
    def __post_init__(self):
        # バリデーションロジック
        pass

@dataclass
class VolumeRange:
    """出来高範囲の型安全な表現"""
    min_volume: Optional[VolumeValue] = None
    max_volume: Optional[VolumeValue] = None
```

#### タスク
- [ ] カスタム型の定義
- [ ] 既存コードの段階的移行
- [ ] バリデーション機能の統合
- [ ] 型チェックツールの導入

---

### 7. **CSV解析の重複実装統一**
**ファイル**: `src/finviz_client/base.py`
**対象**: `get_stock_fundamentals`と`get_multiple_stocks_fundamentals`

#### 問題
- 同様のCSV→StockData変換ロジックが重複
- 約300行のコード重複
- 保守性の悪化

#### 解決策
```python
# src/finviz_client/csv_processor.py
class FinvizCSVProcessor:
    """CSV処理の統一クラス"""
    
    def __init__(self, field_mapping: Dict[str, str]):
        self.field_mapping = field_mapping
    
    def process_csv_response(self, 
                           csv_content: str, 
                           data_fields: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """CSV レスポンスの統一処理"""
        df = pd.read_csv(StringIO(csv_content))
        return [self._process_row(row, data_fields) for _, row in df.iterrows()]
    
    def _process_row(self, row: pd.Series, data_fields: Optional[List[str]]) -> Dict[str, Any]:
        """単一行の処理"""
        result = {}
        for col in row.index:
            if pd.notna(row[col]) and row[col] != '-':
                field_name = self._normalize_field_name(col)
                converted_value = self._convert_field_value(col, row[col])
                result[field_name] = converted_value
        
        if data_fields:
            return self._filter_fields(result, data_fields)
        return result
```

#### タスク
- [ ] CSV処理クラスの実装
- [ ] 既存メソッドのリファクタリング
- [ ] フィールドマッピングの統一
- [ ] パフォーマンステストの実行

---

## 🔷 低優先度の問題（Low Priority）

### 8. **命名規則の統一**
**ファイル**: 複数ファイル
**対象**: 日英混在の命名

#### 問題
- 一部のコメントとメソッド名で日本語が混在
- 国際化への対応不足

#### 解決策
- 英語での統一または多言語対応パターンの導入
- ドキュメント文字列の国際化

#### タスク
- [ ] 命名規則ガイドラインの策定
- [ ] 段階的なリネーミング
- [ ] 多言語サポートの検討

---

### 9. **設定管理の改善**
**ファイル**: 複数ファイル
**対象**: 環境変数の散在

#### 問題
- API key取得処理が複数箇所に分散
- 設定の一元管理不足

#### 解決策
```python
# src/config/settings.py
class Settings:
    """アプリケーション設定の一元管理"""
    
    def __init__(self):
        self.api_key = self._get_api_key()
        self.rate_limit = self._get_rate_limit()
        self.log_level = self._get_log_level()
    
    def _get_api_key(self) -> Optional[str]:
        return os.getenv('FINVIZ_API_KEY')
    
    @lru_cache()
    def get_instance() -> 'Settings':
        return Settings()
```

#### タスク
- [ ] 設定管理クラスの実装
- [ ] 環境変数の標準化
- [ ] 設定バリデーションの追加

---

### 10. **テストカバレッジの向上**
**ファイル**: `tests/`
**対象**: 複雑なフィルタロジックのテスト

#### 問題
- `_convert_filters_to_finviz`の分岐が多すぎてテストが困難
- エッジケースのテスト不足

#### 解決策
- リファクタリング後の小さなメソッドに対する単体テスト
- パラメータ組み合わせテストの自動化

#### タスク
- [ ] テストカバレッジの測定
- [ ] 不足テストケースの特定
- [ ] 自動テスト生成の検討

---

## 📅 実装スケジュール

### Phase 1: 基盤整備（2-3週間）
1. **Week 1**: 設定管理とFilterBuilderの実装
2. **Week 2**: 共通レンジフィルタメソッドの実装
3. **Week 3**: エラーハンドリングの標準化

### Phase 2: アーキテクチャ改善（2-3週間）
1. **Week 4-5**: クラス責任の分離
2. **Week 6**: CSV解析の統一

### Phase 3: 品質向上（1-2週間）
1. **Week 7**: 型安全性の向上
2. **Week 8**: テストカバレッジの向上

### Phase 4: 最終調整（1週間）
1. **Week 9**: 命名規則の統一と文書化

---

## 🎯 期待される効果

### 保守性の向上
- **メソッド複雑度**: 500行 → 50行以下に削減
- **コード重複**: 200行の重複コード削除
- **新機能追加時間**: 50%短縮

### テスタビリティの向上
- **単体テストカバレッジ**: 70% → 90%
- **統合テスト効率**: モック化により3倍高速化
- **バグ検出時間**: 早期発見により80%短縮

### 可読性の向上
- **新規開発者の理解時間**: 50%短縮
- **コードレビュー時間**: 30%短縮
- **ドキュメント保守負荷**: 40%削減

### 拡張性の向上
- **新しいフィルタ追加**: 標準化により効率化
- **API変更対応**: 影響範囲の局所化
- **新しいデータソース**: 疎結合により容易な追加

---

## 📊 進捗管理

### チェックリスト
- [ ] Phase 1: 基盤整備完了
- [ ] Phase 2: アーキテクチャ改善完了
- [ ] Phase 3: 品質向上完了
- [ ] Phase 4: 最終調整完了

### 成功指標
- [ ] テストカバレッジ90%達成
- [ ] コード複雑度50%削減
- [ ] 新機能追加時間50%短縮
- [ ] バグ報告件数80%削減

---

## 🤝 貢献ガイドライン

このリファクタリングに参加する際は、以下の原則に従ってください：

1. **段階的な変更**: 一度に大きな変更を行わず、小さな改善を積み重ねる
2. **後方互換性**: 既存のAPIインターフェースを可能な限り維持
3. **テスト駆動**: リファクタリング前後でテストを実行し、機能の正常性を確認
4. **ドキュメント更新**: コード変更に合わせてドキュメントも更新

---

*このドキュメントは進行に合わせて更新されます。最新版を確認してから作業を開始してください。*

## 📝 更新履歴

- **2025-01-01**: 初版作成
- **作成者**: Claude Code Assistant
- **レビュー**: 未実施