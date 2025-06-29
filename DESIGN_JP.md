# Finviz MCP Server 設計書

## 1. 概要

Finviz MCP ServerはFinvizのAPI経由で株式スクリーニング、ニュース、セクター分析、およびSECファイリング情報を提供するMCP（Model Context Protocol）サーバーです。

## 2. アーキテクチャ

### 2.1 システム構成
```
finviz-mcp-server/
├── src/
│   ├── server.py              # MCPサーバーメイン
│   ├── models.py             # データモデル定義
│   ├── utils.py              # ユーティリティ関数
│   └── finviz_client/        # Finvizクライアント群
│       ├── __init__.py
│       ├── base.py           # 基底クライアント
│       ├── screener.py       # スクリーニング機能
│       ├── news.py           # ニュース機能
│       ├── sector_analysis.py # セクター分析
│       └── sec_filings.py    # SECファイリング（新機能）
├── requirements.txt
└── README_ja.md
```

### 2.2 クライアント構成

#### 2.2.1 基底クライアント (`base.py`)
- HTTP通信の基盤機能
- エラーハンドリング
- レート制限対応
- 認証管理

#### 2.2.2 スクリーニングクライアント (`screener.py`)
- 決算発表予定銘柄
- 出来高急増銘柄
- 上昇トレンド銘柄
- 配当成長銘柄
- テクニカル分析ベース

#### 2.2.3 ニュースクライアント (`news.py`)
- 銘柄関連ニュース
- 市場全体ニュース
- セクター別ニュース

#### 2.2.4 セクター分析クライアント (`sector_analysis.py`)
- セクター・業界・国別パフォーマンス
- 時価総額別分析
- セクター内業界別詳細分析

#### 2.2.5 SECファイリングクライアント (`sec_filings.py`) 【新機能】
- 全SECファイリング取得
- 主要フォーム（10-K、10-Q、8-K）
- インサイダー取引情報（フォーム3、4、5）
- ファイリング統計・概要

## 3. データモデル

### 3.1 基本データモデル

#### 3.1.1 StockData
```python
@dataclass
class StockData:
    ticker: str
    company_name: str
    sector: str
    industry: str
    market_cap: Optional[float]
    price: Optional[float]
    # ... 他の基本フィールド
```

#### 3.1.2 SECFilingData 【新機能】
```python
@dataclass
class SECFilingData:
    ticker: str
    filing_date: str
    report_date: str
    form: str
    description: str
    filing_url: str
    document_url: str
```

### 3.2 特化データモデル

#### 3.2.1 VolumeSurgeData
出来高急増銘柄用のデータ構造

#### 3.2.2 DividendGrowthData
配当成長銘柄用のデータ構造

#### 3.2.3 EarningsData
決算関連データ構造

#### 3.2.4 NewsData
ニュースデータ構造

## 4. API仕様

### 4.1 Finviz API エンドポイント

#### 4.1.1 スクリーニング系
- **基本スクリーニング**: `https://elite.finviz.com/export.ashx`
- **決算スクリーニング**: `https://elite.finviz.com/export.ashv`

#### 4.1.2 ニュース系
- **銘柄ニュース**: `https://finviz.com/quote.ashx?t={ticker}`
- **市場ニュース**: `https://finviz.com/news.ashx`

#### 4.1.3 セクター分析系
- **パフォーマンス**: `https://elite.finviz.com/grp_export.ashx`

#### 4.1.4 SECファイリング系 【新機能】
- **ファイリング**: `https://elite.finviz.com/export/latest-filings`

### 4.2 パラメータ仕様

#### 4.2.1 SECファイリング パラメータ
- `t`: 銘柄ティッカー
- `o`: ソート順序 (`-filingDate` for 降順)
- `auth`: 認証キー

#### 4.2.2 レスポンス形式
CSV形式で以下のカラム：
- Filing Date
- Report Date  
- Form
- Description
- Filing (URL)
- Document (URL)

## 5. 機能詳細

### 5.1 SECファイリング機能 【新機能】

#### 5.1.1 全ファイリング取得 (`get_sec_filings`)
**機能**: 指定銘柄の全SECファイリングを取得
**パラメータ**:
- `ticker`: 銘柄ティッカー
- `form_types`: フォームタイプフィルタ（オプション）
- `days_back`: 取得期間（日数）
- `max_results`: 最大取得件数
- `sort_by`: ソート基準
- `sort_order`: ソート順序

#### 5.1.2 主要ファイリング取得 (`get_major_sec_filings`)
**機能**: 10-K、10-Q、8-K等の主要フォームを取得
**対象フォーム**: 
- 10-K (年次報告書)
- 10-Q (四半期報告書)
- 8-K (臨時報告書)
- DEF 14A (委任状説明書)
- SC 13G/D (大量保有報告書)

#### 5.1.3 インサイダー情報取得 (`get_insider_sec_filings`)
**機能**: インサイダー取引関連ファイリングを取得
**対象フォーム**:
- Form 3 (初回保有報告書)
- Form 4 (保有変動報告書)
- Form 5 (年次保有変動報告書)
- 11-K (従業員株式購入制度報告書)

#### 5.1.4 ファイリング概要取得 (`get_sec_filing_summary`)
**機能**: 指定期間のファイリング統計情報を取得
**提供情報**:
- 総ファイリング数
- フォームタイプ別集計
- 最新ファイリング情報
- 期間統計

## EDGAR API機能 (追加)

### SEC公式EDGAR API
- **ドキュメント取得**: `get_edgar_filing_content()` - SECファイリングドキュメント内容取得
- **複数ドキュメント取得**: `get_multiple_edgar_filing_contents()` - 複数ファイリング一括取得
- **ファイリング一覧**: `get_edgar_company_filings()` - 企業のファイリング一覧取得
- **企業ファクト**: `get_edgar_company_facts()` - 企業基本情報と財務概念データ
- **財務概念**: `get_edgar_company_concept()` - 特定の財務概念詳細データ

### 技術的特徴
- SEC公式APIを使用（Webスクレイピングなし）
- レート制限準拠（SEC API規定）
- 構造化データ対応（XBRL財務データ）
- CIK自動解決（ティッカーからCIK変換）
- エラーハンドリング完備

### 5.2 既存機能

#### 5.2.1 スクリーニング機能
- 決算発表予定銘柄スクリーニング
- 出来高急増銘柄スクリーニング
- 上昇トレンド銘柄スクリーニング
- トレンド反転候補スクリーニング
- 配当成長銘柄スクリーニング
- ETF戦略スクリーニング

#### 5.2.2 決算関連特化機能
- 寄り付き前決算上昇銘柄
- 時間外決算上昇銘柄
- 決算トレード対象銘柄
- ポジティブサプライズ銘柄
- 来週決算予定銘柄

#### 5.2.3 ニュース・分析機能
- 銘柄関連ニュース
- 市場ニュース
- セクター別ニュース
- セクター・業界・国別パフォーマンス
- 相対出来高異常銘柄
- テクニカル分析

## 6. エラーハンドリング

### 6.1 共通エラー処理
- HTTP通信エラー
- CSVパースエラー
- データ変換エラー
- 認証エラー

### 6.2 SECファイリング特有のエラー
- ファイリングデータなし
- 日付パースエラー
- フォームタイプ不正
- URL不正

## 7. パフォーマンス考慮事項

### 7.1 レート制限
- Finviz API制限に準拠
- リクエスト間隔調整
- バッチ処理最適化

### 7.2 データキャッシュ
- ファイリングデータの一時キャッシュ
- 重複リクエスト回避
- メモリ使用量管理

## 8. セキュリティ

### 8.1 認証管理
- API키の安全な管理
- 認証情報の暗号化
- アクセス制御

### 8.2 データ保護
- 個人情報の適切な処理
- ログ情報の管理
- 通信の暗号化

## 9. 拡張性

### 9.1 新機能追加
- モジュラー設計による容易な機能追加
- プラグイン機構の検討
- APIバージョン管理

### 9.2 スケーラビリティ
- 負荷分散対応
- データベース統合可能性
- 並列処理対応

## 10. テスト戦略

### 10.1 単体テスト
- 各クライアントクラスのテスト
- データモデルのテスト
- エラーハンドリングのテスト

### 10.2 統合テスト
- API通信テスト
- エンドツーエンドテスト
- パフォーマンステスト

## 11. デプロイメント

### 11.1 環境構成
- 開発環境
- テスト環境
- 本番環境

### 11.2 CI/CD
- 自動テスト実行
- 自動デプロイ
- 品質ゲート

## 12. 監視・運用

### 12.1 ログ管理
- 構造化ログ出力
- ログレベル管理
- エラー通知

### 12.2 パフォーマンス監視
- レスポンス時間監視
- エラー率監視
- リソース使用率監視 