# 🔍 Finviz Elite フィルター解析ツール群

Finvizの詳細フィルター項目を包括的に解析するためのPythonツール群です。Elite版の高度なスクリーニング機能を詳細に調査し、ドキュメント化することができます。

## 📋 目次

- [🚀 クイックスタート](#-クイックスタート)
- [🛠️ ツール一覧](#️-ツール一覧)
- [💡 使用例](#-使用例)
- [📊 解析結果](#-解析結果)
- [⚙️ 設定とカスタマイズ](#️-設定とカスタマイズ)
- [🔧 トラブルシューティング](#-トラブルシューティング)

## 🚀 クイックスタート

### 最も簡単な方法（推奨）

```bash
# scriptsディレクトリに移動
cd scripts

# HTMLファイル解析（高速・推奨）
python quick_html_analyze.py

# カスタム範囲解析（レンジ指定URL）
python quick_range_analyze.py
```

### 手動でのファイル指定

```bash
# 特定のHTMLファイルを解析
python finviz_html_analyzer.py ../docs/finviz_screen_page.html

# カスタム範囲パターン解析
python finviz_range_analyzer.py ../docs/finviz_screen_page.html
```

## 🛠️ ツール一覧

### 📄 HTMLファイル解析（推奨）

| ツール | 説明 | 特徴 |
|--------|------|------|
| `finviz_html_analyzer.py` | 保存されたHTMLファイルの解析エンジン | ⚡ 高速、🔒ログイン不要 |
| `quick_html_analyze.py` | HTMLファイル解析の簡単実行ラッパー | 🎯 ワンクリック実行 |

### 🎯 カスタム範囲解析（NEW!）

| ツール | 説明 | 特徴 |
|--------|------|------|
| `finviz_range_analyzer.py` | カスタム範囲指定時のURL解析 | 📈 レンジ指定、🔗 URL生成 |
| `quick_range_analyze.py` | カスタム範囲解析の簡単実行 | 💡 実用的な例示 |

### 🌐 Elite版ライブ解析（上級者用）

| ツール | 説明 | 特徴 |
|--------|------|------|
| `finviz_elite_analyzer.py` | Seleniumを使用したライブ解析 | 🔄 リアルタイム、🔐 要ログイン |
| `quick_analyze.py` | Elite版の簡単実行ラッパー | 🚀 自動化対応 |

## 💡 使用例

### 基本的なフィルター解析

```bash
# HTMLファイルから全フィルターを解析
python quick_html_analyze.py

# 出力: finviz_filters_analysis_finviz_screen_page.md (75+ フィルター)
# 出力: finviz_filters_analysis_finviz_screen_page.json (詳細データ)
```

### カスタム範囲指定の解析

```bash
# レンジ指定URLパターンを解析
python quick_range_analyze.py

# 出力例:
# - sh_price_10to50 → 株価 $10-$50
# - cap_1to10 → 時価総額 $1B-$10B
# - fa_pe_10to20 → PER 10-20倍
# - fa_div_3to7 → 配当利回り 3-7%
```

### 特定の出力形式

```bash
# Markdownのみ出力
python finviz_html_analyzer.py --format markdown

# JSONのみ出力
python finviz_range_analyzer.py --format json
```

## 📊 解析結果

### 📋 基本フィルター解析結果

- **75+種類のフィルター項目**を自動検出
- **数千のオプション値**を詳細に抽出
- **8つの主要カテゴリー**に自動分類：
  - 📈 基本情報系（取引所、指数、セクター等）
  - 💰 株価・時価総額系
  - 📊 財務・収益性系
  - 🔄 出来高・取引系
  - 📅 日付・イベント系
  - 🎯 テクニカル分析系
  - 👥 アナリスト・推奨系
  - ⚙️ その他・特殊系

### 🎯 カスタム範囲解析結果（NEW!）

- **レンジ対応フィルター**の特定
- **URLパターン構造**の詳細解析
- **実践的な使用例**とベストプラクティス
- **20+種類の既知パターン**：
  - 💵 価格範囲: `sh_price_10to50`
  - 📊 時価総額: `cap_1to10`
  - 📈 PER範囲: `fa_pe_10to20`
  - 💎 配当利回り: `fa_div_3to7`
  - 📉 ベータ値: `ta_beta_0.5to1.5`

### 📁 出力ファイル形式

#### Markdown形式（ドキュメント用）
- `finviz_filters_analysis_*.md` - 基本フィルター解析
- `finviz_range_analysis_*.md` - カスタム範囲解析

#### JSON形式（プログラム用）
- `finviz_filters_analysis_*.json` - 構造化データ
- `finviz_range_analysis_*.json` - 範囲パターンデータ

## ⚙️ 設定とカスタマイズ

### 🎛️ 解析パラメーター

```python
# フィルター除外設定
EXCLUDE_FILTERS = ['generic_filter', 'test_*']

# 出力制限
MAX_OPTIONS_PER_FILTER = 1000

# 既知の範囲パターン追加
CUSTOM_RANGE_PATTERNS = {
    'my_filter': {
        'type': 'percentage',
        'unit': '%',
        'examples': ['5to20', '10to30']
    }
}
```

### 🔧 出力カスタマイズ

```bash
# 特定のカテゴリーのみ解析
python finviz_html_analyzer.py --categories "basic,financial"

# 詳細度レベル指定
python finviz_range_analyzer.py --detail-level high
```

## 🔧 トラブルシューティング

### よくある問題と解決方法

#### 1. HTMLファイルが見つからない

```bash
❌ finviz_screen_page.html が見つかりません

✅ 解決方法:
- docs/finviz_screen_page.html が存在することを確認
- パスを明示的に指定: python quick_html_analyze.py ../docs/finviz_screen_page.html
```

#### 2. 解析結果が空

```bash
❌ フィルターが検出されませんでした

✅ 解決方法:
- HTMLファイルが正しいFinvizページか確認
- ファイルサイズが適切か確認（通常100KB+）
- エンコーディング問題の可能性 → UTF-8で保存し直す
```

#### 3. ImportError

```bash
❌ ImportError: No module named 'bs4'

✅ 解決方法:
pip install -r requirements.txt
```

### 📞 サポート

問題が解決しない場合：

1. **ログファイル確認**: `finviz_analyzer.log`
2. **詳細モード実行**: `--verbose` フラグを追加
3. **依存関係確認**: `pip list | grep -E "(beautifulsoup4|lxml|selenium)"`

## 🎯 実践的な活用例

### URLパターンの実用例

```bash
# 複合条件の例
https://finviz.com/screener.ashx?v=111&f=sec_technology,cap_1to10,fa_pe_10to25,sh_price_20to100

# 分解すると:
# sec_technology → テクノロジーセクター
# cap_1to10 → 時価総額 $1B-$10B
# fa_pe_10to25 → PER 10-25倍
# sh_price_20to100 → 株価 $20-$100
```

### 解析結果の活用方法

1. **MCP サーバー開発**: JSON出力をスクリーニング機能の実装に活用
2. **投資戦略**: 範囲指定でポートフォリオ候補を絞り込み
3. **API開発**: URLパターンを自動生成するツールの開発

---

## 📈 パフォーマンス

- **HTMLファイル解析**: ~2-5秒（75+ フィルター）
- **カスタム範囲解析**: ~1-3秒（20+ パターン）
- **出力ファイルサイズ**: 50-200KB（Markdown）、20-100KB（JSON）

---

**💡 Tips**: 初回実行時は `quick_html_analyze.py` と `quick_range_analyze.py` を両方実行することをお勧めします。包括的な解析結果が得られます。 