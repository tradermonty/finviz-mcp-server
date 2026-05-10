# finviz-mcp-server 活用ガイド：日々のスクリーニングを効率化する

> **メタディスクリプション**: finviz-mcp-server を使って Finviz の株式スクリーニングを Claude から自然言語で操作するための実践ガイド。セットアップから決算トレード、配当成長株、セクター分析まで、ツールの使い方とプロンプト例を網羅。

> ⚠️ **免責事項**: 本記事は教育目的の活用ガイドです。投資助言ではなく、特定の運用成果や利益を保証するものではありません。記載のスクリーニング条件・閾値は一般的な目安であり、最終的な投資判断はご自身の責任で行ってください。

## なぜ finviz-mcp-server を使うのか

**従来のスクリーニング作業の課題**:

- Finviz の Web 画面と分析ツールを行き来する手間
- 条件変更のたびにフィルタを設定し直す煩雑さ
- スクリーニング結果と外部のニュース／ファンダ情報を突き合わせる作業
- 同じ操作を毎日繰り返す非効率

**finviz-mcp-server が提供する価値**:

- Claude などの AI アシスタントから自然言語で Finviz のスクリーニングを実行
- 20 種類以上のスクリーニングツール（決算、配当、テクニカル、セクター 等）を関数として呼び出し可能
- 結果に対してその場で深掘り質問・追加分析が可能
- Model Context Protocol (MCP) 経由で再現性のあるワークフローを構築

> 💰 **コスト**: Finviz Elite サブスクリプション（年払いで $24.96/月、月払いで $39.50/月。価格は変更される可能性があるため [公式ページ](https://finviz.com/elite) で要確認）の API キーが必須です。無料アカウントでは動作しません。

---

## セットアップガイド

### 前提条件

| 項目 | 要件 | 確認方法 |
|------|------|----------|
| Python | 3.11 以上 | `python3 --version` |
| Finviz Elite | サブスクリプション必須 | [Finviz Elite](https://finviz.com/elite.ashx) |
| Claude Desktop | 最新版 | [公式サイト](https://claude.ai/download) |

> ⚠️ 現在の finviz-mcp-server は **Finviz Elite API キーが必須** です。無料版では動作しません。

---

### Step 1: プロジェクト環境構築

```bash
# プロジェクトディレクトリ作成
mkdir ~/finviz-trading && cd ~/finviz-trading

# Python 仮想環境作成
python3.11 -m venv venv
source venv/bin/activate  # macOS/Linux
# Windows の場合
venv\Scripts\activate

# finviz-mcp-server インストール
git clone https://github.com/tradermonty/finviz-mcp-server.git
cd finviz-mcp-server
pip install -e .
```

### Step 2: Finviz Elite API キー取得

1. [Finviz Elite](https://finviz.com/elite.ashx) でサブスクリプション契約
2. アカウントにログイン後、Account Settings → API Access
3. Generate New API Key をクリック
4. 生成されたキーをコピー（次の Step で使用）

---

### Step 3: Claude Desktop の MCP 設定

#### 設定ファイルの場所

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

#### 設定ファイル例

```json
{
  "mcpServers": {
    "finviz": {
      "command": "/Users/your-username/finviz-trading/finviz-mcp-server/venv/bin/finviz-mcp-server",
      "args": [],
      "cwd": "/Users/your-username/finviz-trading/finviz-mcp-server",
      "env": {
        "FINVIZ_API_KEY": "your_actual_finviz_elite_api_key_here",
        "LOG_LEVEL": "INFO",
        "RATE_LIMIT_REQUESTS_PER_MINUTE": "100"
      }
    }
  }
}
```

> ⚠️ パスを自分の環境に合わせて修正し、`FINVIZ_API_KEY` に Step 2 で取得したキーを設定してください。

#### Claude Desktop 再起動

1. Claude Desktop を完全終了
2. アプリケーションを再起動
3. 新しいチャットで動作確認

---

### Step 4: 動作確認

Claude Desktop で以下を試します:

```
今日の市場概況を教えて
```

**期待される応答**: 主要指数の状況、セクター別パフォーマンス、VIX 指数の値などが返ってくれば設定完了です。

---

## 1. 朝の市場概況チェック

### Step 1: 市場全体の概況

```python
# 市場全体の概況を取得
market_overview = get_market_overview()
```

**確認項目の例**:

| 指標 | 確認内容 |
|------|----------|
| S&P 500 | 前日比変動率 |
| NASDAQ | テック株動向 |
| VIX | ボラティリティ水準 |

> 💡 一般的に VIX が 30 を超えると「警戒水準」と解釈されます（絶対的な閾値ではなく、過去の分布からの目安）。

### Step 2: セクター別パフォーマンス

```python
# 全セクターのパフォーマンス
sector_performance = get_sector_performance()

# 特定セクターのみ
tech_performance = get_sector_performance(sectors=["Technology"])
```

セクター間の強弱を見ることで、当日の資金フローの傾向を把握できます。

### Step 3: 異常出来高銘柄の検出

```python
# 出来高急増銘柄
volume_surge_stocks = volume_surge_screener()
```

出来高が平均より大きく上回る銘柄は、ニュースイベントやアナリスト評価変更などで注目を集めているケースが多いため、ニュース確認とセットで活用します。

---

### 朝のルーティン用プロンプト例

```
今日の市場概況を整理してください。

1. 市場全体（S&P500、NASDAQ、VIX）の前日比
2. 強いセクター・弱いセクターを各 3 つずつ
3. 相対出来高 2 倍以上で価格が 3% 以上動いている銘柄

各ステップの結果を表形式でまとめてください。
```

---

## 2. 週末の振り返り

### 週次パフォーマンス分析

```python
# セクター・国別・時価総額別パフォーマンス
weekly_sectors = get_sector_performance()
country_performance = get_country_performance()
cap_performance = get_capitalization_performance()
```

### トレンド分析

```python
# 上昇トレンド継続銘柄
uptrend_stocks = uptrend_screener()

# 反転候補
reversal_candidates = trend_reversion_screener()
```

### 週次レビューの観点

1. 主要指数の週間騰落率と VIX の変化
2. セクター別の強弱と週次でのローテーション傾向
3. 週間で大きく動いた個別銘柄、新高値・新安値銘柄
4. 翌週注目すべきイベント（決算、経済指標、FOMC 等）

---

## 3. 決算トレード活用パターン

### 3.1 決算前の準備

#### 来週の決算カレンダー取得

```python
upcoming_earnings = upcoming_earnings_screener(
    earnings_period="next_week",
    market_cap="smallover",        # $300M 以上
    min_price=10,                  # $10 以上
    min_avg_volume="o500"          # 平均出来高 50万株以上
)
```

**選定基準の目安**:

| 項目 | 目安 | 理由 |
|------|------|------|
| 時価総額 | $300M 以上 | 流動性確保 |
| 株価 | $10 以上 | ペニーストック回避 |
| 平均出来高 | 50万株以上 | スリッページ抑制 |

#### テクニカル条件での絞り込み

```python
technical_candidates = technical_analysis_screener(
    rsi_min=30,
    rsi_max=70,
    price_vs_sma20="above",
    min_price=10,
    min_volume=500000
)
```

### 3.2 決算発表日

#### 寄り付き前

```python
premarket_earnings = earnings_premarket_screener()
```

#### 引け後

```python
afterhours_earnings = earnings_afterhours_screener()
```

### 3.3 決算後の勝ち組分析

```python
earnings_winners = earnings_winners_screener(
    earnings_period="this_week",
    market_cap="smallover",
    min_eps_growth_qoq=10,
    min_sales_growth_qoq=5
)
```

---

### 決算トレード用プロンプト例

#### 週末の準備

```
来週の決算戦略を組み立てます。

1. 来週決算予定の銘柄を、時価総額 $500M 以上、平均出来高 100万株以上でスクリーニング
2. その中から RSI 40-60、20日 SMA 上の銘柄を抽出
3. 各銘柄の決算日、予想 EPS、過去 4 四半期のサプライズ率を表で整理
4. セクター分散を考慮したうえで、注目度の高い 5 銘柄を提示

各銘柄の選定理由も簡潔に添えてください。
```

#### 決算発表日朝のチェック

```
寄り付き前に決算発表があった銘柄について：

- プリマーケットで 2% 以上上昇
- 時価総額 $300M 以上
- 平均出来高 50万株以上

各銘柄について以下を整理してください：
1. EPS／売上のサプライズ
2. ガイダンス変更の有無
3. アナリストの初期反応・主要ニュースの要約
4. セクター全体や競合との比較
```

#### 引け後

```
引け後に決算発表があり、アフターアワーズで 3% 以上上昇している銘柄：

- 時価総額 $1B 以上
- EPS または売上でサプライズ

各銘柄について：
1. サプライズの大きさ（予想 vs 実績）
2. ガイダンス上方修正の有無
3. CEO コメントの要旨
4. 翌日寄り付きの戦略案（ギャップアップ予想、エントリー方針、損切り水準）

を整理してください。
```

---

## 4. 配当成長株スクリーニング

### 4.1 配当成長株の抽出

```python
dividend_growers = dividend_growth_screener(
    market_cap="midover",           # $2B 以上
    min_dividend_yield=2.0,         # 利回り 2% 以上
    max_dividend_yield=8.0,         # 高すぎる利回りは除外
    min_dividend_growth=5.0,        # 配当成長率 5% 以上
    max_payout_ratio=70.0,          # 配当性向 70% 以下
    min_roe=12.0,                   # ROE 12% 以上
    max_debt_equity=0.5             # 負債比率 0.5 以下
)
```

**配当株の評価でよく使われる目安**:

| 指標 | 一般的に健全とされる範囲 | 注意が必要な範囲 |
|------|-------------------------|------------------|
| 配当利回り | 3-6% | 10% 以上（持続性に疑義） |
| 配当性向 | 40-60% | 80% 以上 |
| ROE | 12% 以上 | 5% 以下 |
| 負債比率 (D/E) | 0.3 以下 | 0.7 以上 |

> 💡 これらは一般的な目安であり、業種によって適正水準は異なります（例: 公益・REIT は配当性向が高くなる傾向）。

### 4.2 個別銘柄のファンダメンタル分析

```python
# data_fields は内部キー（snake_case）で指定する点に注意
stock_fundamentals = get_stock_fundamentals(
    ticker="VZ",
    data_fields=[
        "dividend_yield",
        "payout_ratio",
        "roe",
        "debt_to_equity",
        "eps_growth_past_5y",
        "sales_growth_past_5y",
    ]
)
```

> ℹ️ `data_fields` は **内部キー（snake_case）** で指定します。利用可能なキーの一覧は `mcp__finviz__list_available_fields` または `mcp__finviz__search_fields` で取得できます。

### 4.3 REIT への絞り込み

`dividend_growth_screener` 自体にはセクター指定機能がないため、REIT に絞り込む場合は次のいずれかで対応します:

- `custom_screener` でセクター条件を含めたカスタムフィルタを作る
- `dividend_growth_screener` の結果を取得後、`get_multiple_stocks_fundamentals` でセクターを取得して post-filter する

```python
# custom_screener は raw な Finviz フィルタ文字列を受け取ります（カンマ区切り）
# 例: REIT セクター・配当利回り 4-12%・時価総額 mid 以上
reit_results = custom_screener(
    filters="sec_realestate,fa_div_o4,fa_div_u12,cap_midover"
)
```

> ℹ️ `custom_screener` の `filters` は dict ではなく **Finviz の raw フィルタ文字列**（例: `"sec_realestate,fa_div_o4"`）です。プレフィックス: `cap_`（時価総額）/ `fa_`（ファンダ）/ `ta_`（テクニカル）/ `sec_`（セクター）/ `ind_`（業種）/ `geo_`（国）/ `sh_`（取引データ）。

---

### 配当株分析プロンプト例

```
配当成長株を以下の条件でスクリーニングしてください：
- 配当利回り 3-7%
- 配当成長率（過去 5 年） 年平均 5% 以上
- 配当性向 70% 以下
- ROE 12% 以上
- 負債比率 (D/E) 0.5 以下
- 時価総額 $2B 以上

結果を配当利回り順で表示し、各銘柄の連続増配年数（取得可能であれば）も添えてください。
```

---

## 5. 高度なスクリーニング戦略

### 5.1 モメンタム戦略

```python
momentum_stocks = technical_analysis_screener(
    rsi_min=60,
    rsi_max=80,
    price_vs_sma20="above",
    price_vs_sma50="above",
    price_vs_sma200="above",
    min_volume=1000000
)
```

### 5.2 反転候補（バリュー寄り）

```python
value_candidates = trend_reversion_screener(
    market_cap="large",
    eps_growth_qoq=5.0,
    revenue_growth_qoq=3.0,
    rsi_max=40
)
```

### 5.3 ETF スクリーニング

```python
sector_etfs = etf_screener(
    strategy_type="long",
    asset_class="equity",
    min_aum=100_000_000,    # $100M 以上
    max_expense_ratio=0.75
)
```

> ℹ️ `etf_screener` は `data_fields` パラメータを取りません。出力フォーマットは固定です。

---

## 6. ポートフォリオ確認

### 6.1 複数銘柄のファンダメンタルス取得

```python
portfolio_stocks = get_multiple_stocks_fundamentals(
    tickers=["AAPL", "MSFT", "GOOGL", "AMZN"],
    data_fields=[
        "sector",
        "beta",
        "volatility_week",
        "market_cap",
    ]
)
```

### 6.2 セクター別パフォーマンス

```python
portfolio_sectors = get_sector_performance(
    sectors=["Technology", "Healthcare", "Financial", "Consumer Defensive"]
)
```

セクター集中度を可視化することで、ポートフォリオのリスク偏在を把握できます。

---

## 7. シナリオ別プロンプト例

### 7.1 デイトレード前のチェック

```
デイトレードに入る前のチェックをします。

1. 市場概況（S&P500、NASDAQ、VIX）
2. 出来高急増銘柄（相対出来高 2 倍以上、価格 3% 以上変動）
3. 強い／弱いセクター TOP3
4. 当日のニュースで注目すべき材料

結果を「今日の戦略メモ」として要約してください。
```

### 7.2 スイングトレード候補の選定

```
来週のスイングトレード候補を選定します。

条件：
- SMA20 > SMA50 > SMA200 のフルアラインメント
- RSI 40-60
- 来週の決算発表なし
- 時価総額 $1B 以上
- 平均出来高 100万株以上

候補をテクニカル・業績・セクター分散の観点で評価し、上位 10 銘柄を提示してください。
```

### 7.3 月次ポートフォリオレビュー

```
月次レビューを実施します。

1. 配当成長株の健全性チェック（利回り 3-8%、配当性向 70% 以下、連続増配 5 年以上）
2. バリュー候補（時価総額 $10B 以上、PER 15 以下、PBR 2 以下、ROE 12% 以上）
3. 当月のセクターローテーション状況

長期投資戦略の調整提案も添えてください。
```

---

## 8. 主要ツール一覧（リファレンス）

| カテゴリ | ツール名 | 用途 |
|---|---|---|
| 市場概況 | `get_market_overview` | 主要指数・VIX・センチメント |
| 市場概況 | `get_sector_performance` | セクター別パフォーマンス |
| 市場概況 | `get_industry_performance` | 業種別パフォーマンス |
| スクリーニング | `volume_surge_screener` | 出来高急増銘柄 |
| スクリーニング | `uptrend_screener` | 上昇トレンド銘柄 |
| スクリーニング | `trend_reversion_screener` | 反転候補銘柄 |
| スクリーニング | `technical_analysis_screener` | テクニカル条件指定 |
| スクリーニング | `dividend_growth_screener` | 配当成長株 |
| スクリーニング | `etf_screener` | ETF |
| スクリーニング | `custom_screener` | 任意条件のカスタム |
| 決算 | `upcoming_earnings_screener` | 決算カレンダー（次週など） |
| 決算 | `earnings_premarket_screener` | 寄り付き前決算反応 |
| 決算 | `earnings_afterhours_screener` | 引け後決算反応 |
| 決算 | `earnings_winners_screener` | 決算後の勝ち組 |
| 決算 | `earnings_trading_screener` | 決算トレード候補 |
| ファンダ | `get_stock_fundamentals` | 個別銘柄の詳細 |
| ファンダ | `get_multiple_stocks_fundamentals` | 複数銘柄一括 |
| ニュース | `get_stock_news` / `get_market_news` / `get_sector_news` | 各種ニュース |
| フィールド | `list_available_fields` / `search_fields` / `describe_field` | data_fields の探索 |

各ツールの引数の詳細は、Claude 上で `この finviz-mcp-server のツール XXX のパラメータを教えて` と聞くか、リポジトリの `src/server.py` を参照してください。

---

## 9. トラブルシューティング

### MCP サーバーが認識されない

```bash
# パスの確認
which finviz-mcp-server

# 実行権限の確認
ls -la /path/to/finviz-mcp-server/venv/bin/finviz-mcp-server

# 手動実行テスト
/path/to/finviz-mcp-server/venv/bin/finviz-mcp-server

# Claude Desktop の設定ファイル確認
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

### コード変更が反映されない

```bash
# Claude Desktop を完全終了 → 30 秒待機 → 再起動

# プロセスが残っていないか確認
ps aux | grep finviz-mcp-server

# 必要なら再インストール
cd /path/to/finviz-mcp-server
pip install -e . --force-reinstall
```

### API キーエラー

`API key required` などが出る場合:

1. Finviz Elite サブスクリプション状況を確認（無料アカウントでは動作しません）
2. API Access ページで生成したキーが有効か確認
3. `claude_desktop_config.json` の `FINVIZ_API_KEY` が正しく設定されているか
4. Claude Desktop を完全再起動

### データが取得できない／動作が遅い

```json
{
  "mcpServers": {
    "finviz": {
      "env": {
        "RATE_LIMIT_REQUESTS_PER_MINUTE": "200",
        "LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

`LOG_LEVEL=DEBUG` にすると、リクエストの詳細がログに出るため原因特定がしやすくなります。

---

## 10. 効果的なプロンプトのコツ

### 改善前

```
株を教えて
```

### 改善後

```
テクノロジーセクターで時価総額 $1B 以上、
RSI 30-70、配当利回り 2% 以上の銘柄を 5 つまで抽出してください。

結果は以下の形式で：
- ティッカー
- 企業名
- 現在株価
- RSI
- 配当利回り
- 選定理由
```

具体的な条件・件数・出力フォーマットを明示すると、再現性のある結果が得やすくなります。

---

## まとめ

finviz-mcp-server は、Finviz の豊富なスクリーニング機能を Claude などの AI アシスタントから自然言語で操作できるようにする MCP サーバーです。本ガイドでは:

- セットアップ手順
- 朝の市場確認・週末レビューのルーティン
- 決算トレード／配当成長株／テクニカル戦略のスクリーニング例
- 主要ツールのリファレンスとプロンプト例

を紹介しました。

ご自身の投資スタイルに合わせて条件を調整し、まずは 1 つの戦略から運用ルーティンに組み込んでみてください。

---

## リソース

- **GitHub Repository**: [tradermonty/finviz-mcp-server](https://github.com/tradermonty/finviz-mcp-server)
- **Finviz Elite**: [finviz.com/elite.ashx](https://finviz.com/elite.ashx)
- **Claude Desktop**: [claude.ai/download](https://claude.ai/download)
- **Updates**: [@monty_investor](https://x.com/monty_investor)

---

## 免責事項

- 本記事は教育目的の活用ガイドです。投資助言ではありません。
- 投資には元本割れのリスクが伴います。投資判断はご自身の責任で行ってください。
- 過去の数値や事例は、将来の成果を保証するものではありません。
- Finviz のデータ利用規約および API レート制限を遵守してください。

---

*最終更新: 2026-05-10 | finviz-mcp-server 対応*
