# Finviz HTML解析 クイックスタートガイド

## 🚀 最速で解析を開始する

### Step 1: HTMLファイルを取得
1. ブラウザで [Finviz Elite Screener](https://elite.finviz.com/screener.ashx) を開く
2. ページ全体を `finviz_screen_page.html` として保存
   - **Chrome**: Ctrl+S → 「Webページ、完全」を選択 → 保存
   - **Firefox**: Ctrl+S → 「Webページ、完全」を選択 → 保存
   - **Safari**: Cmd+S → 「Webアーカイブ」または「ページのソース」を選択 → 保存

### Step 2: 解析実行
```bash
# scriptsディレクトリに移動
cd scripts

# 依存関係インストール（初回のみ）
pip install beautifulsoup4 lxml

# 解析実行
python quick_html_analyze.py
```

### Step 3: 結果確認
解析完了後、以下のファイルが生成されます：
- `finviz_filters_analysis_finviz_screen_page.md` - 読みやすいMarkdown形式
- `finviz_filters_analysis_finviz_screen_page.json` - 構造化データ

## 📊 解析結果の活用

### Markdownファイル
- 各フィルター項目の詳細な説明
- カテゴリー別に整理された一覧
- 実際のURLでの使用方法

### JSONファイル
- プログラムで処理可能なデータ形式
- API開発やスクリプト作成に活用
- フィルター値の自動補完機能に使用可能

## 🔧 トラブルシューティング

### よくある問題

#### 1. "HTMLファイルが見つかりません"
**解決方法:**
- ファイル名が `finviz_screen_page.html` になっているか確認
- scriptsディレクトリまたはその上位ディレクトリに配置されているか確認
- ファイルパスを直接指定: `python quick_html_analyze.py /path/to/your/file.html`

#### 2. "インポートエラー"
**解決方法:**
```bash
pip install beautifulsoup4 lxml requests
```

#### 3. "フィルターが検出されませんでした"
**解決方法:**
- HTMLファイルが完全に保存されているか確認
- Finvizスクリーナーページ（フィルター部分を含む）が保存されているか確認
- ファイルサイズが極端に小さくないか確認（通常100KB以上）

### 手動実行

より詳細な制御が必要な場合：
```bash
# Markdownのみ出力
python finviz_html_analyzer.py finviz_screen_page.html --format markdown

# JSONのみ出力
python finviz_html_analyzer.py finviz_screen_page.html --format json

# 別のHTMLファイルを解析
python finviz_html_analyzer.py my_custom_finviz_page.html
```

## 💡 活用のヒント

### 1. ドキュメント更新
生成されたMarkdownファイルを元に、プロジェクトのパラメーター一覧を更新

### 2. API開発
JSONデータを使用して、Finviz風のスクリーニング機能をAPIとして実装

### 3. 自動化
定期的にHTMLを取得・解析して、新しいパラメーターの追加を監視

### 4. フィルター検証
実装したスクリーニング機能のパラメーター値が正しいか検証

## 📈 次のステップ

1. **パラメーター実装**: 解析結果を元にスクリーニング機能を拡張
2. **ドキュメント更新**: 新しく発見されたパラメーターをドキュメントに追加
3. **自動化**: CI/CDパイプラインに組み込んで定期的な解析を実行 