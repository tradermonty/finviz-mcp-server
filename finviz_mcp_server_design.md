# Finviz MCP Server 設計書

## 1. 概要

このドキュメントは、既存のFinvizスクリプト群を基に、MCP (Model Context Protocol) 経由でFinviz機能を呼び出せるサーバーの設計を定義します。

## 2. 現在の利用状況分析

### 2.1 利用パターン分類

コードベース分析により、以下の主要な利用パターンを特定しました：

1. **短期トレーディング戦略** (10ファイル)
2. **中長期投資戦略** (2ファイル)  
3. **スクリーニング・分析** (7ファイル)
4. **ニュース・センチメント分析** (1ファイル)
5. **ユーティリティ・ツール** (2ファイル)

### 2.2 主要機能

- **スクリーニング**: 複雑なフィルタ条件での銘柄検索
- **ファンダメンタルデータ**: 個別銘柄の詳細情報
- **ニュースデータ**: 銘柄関連ニュースの取得
- **セクター/業界分析**: 市場セグメント別パフォーマンス
- **テクニカル指標**: 価格・出来高・トレンド情報

## 3. MCP Server アーキテクチャ

### 3.1 全体構成

```
finviz-mcp-server/
├── src/
│   ├── server.py                 # MCPサーバーメイン
│   ├── tools/                    # MCPツール定義
│   │   ├── __init__.py
│   │   ├── screening.py          # スクリーニング関連ツール
│   │   ├── fundamentals.py       # ファンダメンタル関連ツール
│   │   ├── news.py              # ニュース関連ツール
│   │   ├── sector_analysis.py   # セクター分析ツール
│   │   └── technical.py         # テクニカル分析ツール
│   ├── finviz_client/           # Finviz API クライント
│   │   ├── __init__.py
│   │   ├── base.py              # 基本APIクライアント
│   │   ├── screener.py          # スクリーニング機能
│   │   ├── fundamentals.py      # ファンダメンタル機能
│   │   └── news.py              # ニュース機能
│   └── utils/
│       ├── __init__.py
│       ├── validators.py        # 入力検証
│       └── formatters.py        # 出力フォーマット
├── tests/
├── requirements.txt
└── README.md
```

### 3.2 MCP Tools 定義

## 4. MCPツール仕様

### 4.1 スクリーニングツール

#### 4.1.1 earnings_screener
```json
{
  "name": "earnings_screener",
  "description": "決算発表予定銘柄のスクリーニング",
  "inputSchema": {
    "type": "object",
    "properties": {
      "earnings_date": {
        "type": "string",
        "enum": ["today_after", "tomorrow_before", "this_week", "within_2_weeks"],
        "description": "決算発表日の指定"
      },
      "market_cap": {
        "type": "string",
        "enum": ["small", "mid", "large", "mega"],
        "description": "時価総額フィルタ"
      },
      "min_price": {"type": "number", "description": "最低株価"},
      "max_price": {"type": "number", "description": "最高株価"},
      "min_volume": {"type": "number", "description": "最低出来高"},
      "sectors": {
        "type": "array",
        "items": {"type": "string"},
        "description": "対象セクター"
      },
      "premarket_price_change": {
        "type": "object",
        "properties": {
          "enabled": {"type": "boolean", "description": "寄り付き前価格変動フィルタを有効にするか"},
          "min_change_percent": {"type": "number", "description": "最低価格変動率(%)"},
          "max_change_percent": {"type": "number", "description": "最高価格変動率(%)"}
        },
        "description": "寄り付き前の通常株価変動フィルタ（決算発表が寄り付き前の場合）"
      },
      "afterhours_price_change": {
        "type": "object",
        "properties": {
          "enabled": {"type": "boolean", "description": "時間外価格変動フィルタを有効にするか"},
          "min_change_percent": {"type": "number", "description": "最低価格変動率(%)"},
          "max_change_percent": {"type": "number", "description": "最高価格変動率(%)"}
        },
        "description": "時間外取引での価格変動フィルタ（決算発表が引け後の場合）"
      }
    },
    "required": ["earnings_date"]
  }
}
```

#### 4.1.2 trend_reversion_screener
```json
{
  "name": "trend_reversion_screener",
  "description": "トレンド反転候補銘柄のスクリーニング",
  "inputSchema": {
    "type": "object",
    "properties": {
      "market_cap": {
        "type": "string",
        "enum": ["mid_large", "large", "mega"],
        "description": "時価総額フィルタ"
      },
      "eps_growth_qoq": {"type": "number", "description": "EPS成長率(QoQ) 最低値"},
      "revenue_growth_qoq": {"type": "number", "description": "売上成長率(QoQ) 最低値"},
      "rsi_max": {"type": "number", "description": "RSI上限値"},
      "sectors": {
        "type": "array",
        "items": {"type": "string"},
        "description": "対象セクター"
      },
      "exclude_sectors": {
        "type": "array",
        "items": {"type": "string"},
        "description": "除外セクター"
      }
    }
  }
}
```

#### 4.1.3 uptrend_screener
```json
{
  "name": "uptrend_screener",
  "description": "上昇トレンド銘柄のスクリーニング",
  "inputSchema": {
    "type": "object",
    "properties": {
      "trend_type": {
        "type": "string",
        "enum": ["strong_uptrend", "breakout", "momentum"],
        "description": "トレンドタイプ"
      },
      "sma_period": {
        "type": "string",
        "enum": ["20", "50", "200"],
        "description": "移動平均期間"
      },
      "relative_volume": {"type": "number", "description": "相対出来高最低値"},
      "price_change": {"type": "number", "description": "価格変化率最低値"}
    }
  }
}
```

#### 4.1.4 dividend_growth_screener
```json
{
  "name": "dividend_growth_screener",
  "description": "配当成長銘柄のスクリーニング",
  "inputSchema": {
    "type": "object",
    "properties": {
      "min_dividend_yield": {"type": "number", "description": "最低配当利回り"},
      "max_dividend_yield": {"type": "number", "description": "最高配当利回り"},
      "min_dividend_growth": {"type": "number", "description": "最低配当成長率"},
      "min_payout_ratio": {"type": "number", "description": "最低配当性向"},
      "max_payout_ratio": {"type": "number", "description": "最高配当性向"},
      "min_roe": {"type": "number", "description": "最低ROE"},
      "max_debt_equity": {"type": "number", "description": "最高負債比率"}
    }
  }
}
```

#### 4.1.5 etf_screener
```json
{
  "name": "etf_screener",
  "description": "ETF戦略用スクリーニング",
  "inputSchema": {
    "type": "object",
    "properties": {
      "strategy_type": {
        "type": "string",
        "enum": ["long", "short"],
        "description": "戦略タイプ"
      },
      "asset_class": {
        "type": "string",
        "enum": ["equity", "bond", "commodity", "currency"],
        "description": "資産クラス"
      },
      "min_aum": {"type": "number", "description": "最低運用資産額"},
      "max_expense_ratio": {"type": "number", "description": "最高経費率"}
    }
  }
}
```

#### 4.1.6 volume_surge_screener
```json
{
  "name": "volume_surge_screener",
  "description": "出来高急増を伴う上昇銘柄のスクリーニング",
  "inputSchema": {
    "type": "object",
    "properties": {
      "market_cap": {
        "type": "string",
        "enum": ["small", "mid", "large", "mega", "smallover"],
        "default": "smallover",
        "description": "時価総額フィルタ"
      },
      "min_price": {
        "type": "number", 
        "default": 10,
        "description": "最低株価"
      },
      "min_avg_volume": {
        "type": "number",
        "default": 100000,
        "description": "最低平均出来高"
      },
      "min_relative_volume": {
        "type": "number",
        "default": 1.5,
        "description": "最低相対出来高倍率"
      },
      "min_price_change": {
        "type": "number",
        "default": 2.0,
        "description": "最低価格変動率(%)"
      },
      "sma_filter": {
        "type": "string",
        "enum": ["above_sma20", "above_sma50", "above_sma200", "none"],
        "default": "above_sma200",
        "description": "移動平均線フィルタ"
      },
      "stocks_only": {
        "type": "boolean",
        "default": true,
        "description": "株式のみ（ETF除外）"
      },
      "max_results": {
        "type": "number",
        "default": 50,
        "description": "最大取得件数"
      },
      "sort_by": {
        "type": "string",
        "enum": ["price_change", "relative_volume", "volume", "price"],
        "default": "price_change",
        "description": "ソート基準"
      },
      "sectors": {
        "type": "array",
        "items": {"type": "string"},
        "description": "対象セクター"
      },
      "exclude_sectors": {
        "type": "array",
        "items": {"type": "string"},
        "description": "除外セクター"
      }
    }
  }
}
```

#### 4.1.7 earnings_premarket_screener
```json
{
  "name": "earnings_premarket_screener",
  "description": "寄り付き前決算発表で上昇している銘柄のスクリーニング",
  "inputSchema": {
    "type": "object",
    "properties": {
      "earnings_timing": {
        "type": "string",
        "enum": ["today_before", "yesterday_before", "this_week_before"],
        "default": "today_before",
        "description": "決算発表タイミング"
      },
      "market_cap": {
        "type": "string",
        "enum": ["small", "mid", "large", "mega", "smallover"],
        "default": "smallover",
        "description": "時価総額フィルタ"
      },
      "min_price": {
        "type": "number",
        "default": 10,
        "description": "最低株価"
      },
      "min_avg_volume": {
        "type": "number",
        "default": 100000,
        "description": "最低平均出来高"
      },
      "min_price_change": {
        "type": "number",
        "default": 2.0,
        "description": "最低価格変動率(%)"
      },
      "max_price_change": {
        "type": "number",
        "description": "最高価格変動率(%)"
      },
      "include_premarket_data": {
        "type": "boolean",
        "default": true,
        "description": "寄り付き前取引データを含める"
      },
      "data_fields": {
        "type": "array",
        "items": {
          "type": "string",
          "enum": [
            "ticker", "company", "sector", "industry", "country", 
            "market_cap", "pe_ratio", "price", "change", "change_percent",
            "volume", "avg_volume", "relative_volume", "float", "outstanding",
            "insider_own", "institutional_own", "short_interest", "target_price",
            "52w_high", "52w_low", "rsi", "gap", "analyst_recom"
          ]
        },
        "default": [
          "ticker", "company", "sector", "price", "change", "change_percent",
          "volume", "relative_volume", "market_cap", "pe_ratio", "target_price"
        ],
        "description": "取得するデータフィールド"
      },
      "max_results": {
        "type": "number",
        "default": 60,
        "description": "最大取得件数"
      },
      "sort_by": {
        "type": "string",
        "enum": ["change_percent", "change_abs", "volume", "relative_volume", "market_cap"],
        "default": "change_percent",
        "description": "ソート基準"
      },
      "sort_order": {
        "type": "string",
        "enum": ["desc", "asc"],
        "default": "desc",
        "description": "ソート順序"
      },
      "sectors": {
        "type": "array",
        "items": {"type": "string"},
        "description": "対象セクター"
      },
      "exclude_sectors": {
        "type": "array",
        "items": {"type": "string"},
        "description": "除外セクター"
      }
    }
  }
}
```

#### 4.1.8 earnings_afterhours_screener
```json
{
  "name": "earnings_afterhours_screener",
  "description": "引け後決算発表で時間外取引上昇銘柄のスクリーニング",
  "inputSchema": {
    "type": "object",
    "properties": {
      "earnings_timing": {
        "type": "string",
        "enum": ["today_after", "yesterday_after", "this_week_after"],
        "default": "today_after",
        "description": "決算発表タイミング"
      },
      "market_cap": {
        "type": "string",
        "enum": ["small", "mid", "large", "mega", "smallover"],
        "default": "smallover",
        "description": "時価総額フィルタ"
      },
      "min_price": {
        "type": "number",
        "default": 10,
        "description": "最低株価"
      },
      "min_avg_volume": {
        "type": "number",
        "default": 100000,
        "description": "最低平均出来高"
      },
      "min_afterhours_change": {
        "type": "number",
        "default": 2.0,
        "description": "最低時間外価格変動率(%)"
      },
      "max_afterhours_change": {
        "type": "number",
        "description": "最高時間外価格変動率(%)"
      },
      "include_afterhours_data": {
        "type": "boolean",
        "default": true,
        "description": "時間外取引データを含める"
      },
      "data_fields": {
        "type": "array",
        "items": {
          "type": "string",
          "enum": [
            "ticker", "company", "sector", "industry", "country", 
            "market_cap", "pe_ratio", "price", "change", "change_percent",
            "afterhours_change", "afterhours_change_percent", "afterhours_price",
            "volume", "avg_volume", "relative_volume", "float", "outstanding",
            "insider_own", "institutional_own", "short_interest", "target_price",
            "52w_high", "52w_low", "rsi", "gap", "analyst_recom"
          ]
        },
        "default": [
          "ticker", "company", "sector", "price", "afterhours_change", "afterhours_change_percent",
          "volume", "relative_volume", "market_cap", "pe_ratio", "target_price"
        ],
        "description": "取得するデータフィールド"
      },
      "max_results": {
        "type": "number",
        "default": 60,
        "description": "最大取得件数"
      },
      "sort_by": {
        "type": "string",
        "enum": ["afterhours_change_percent", "afterhours_change_abs", "change_percent", "volume", "relative_volume", "market_cap"],
        "default": "afterhours_change_percent",
        "description": "ソート基準"
      },
      "sort_order": {
        "type": "string",
        "enum": ["desc", "asc"],
        "default": "desc",
        "description": "ソート順序"
      },
      "sectors": {
        "type": "array",
        "items": {"type": "string"},
        "description": "対象セクター"
      },
      "exclude_sectors": {
        "type": "array",
        "items": {"type": "string"},
        "description": "除外セクター"
      }
    }
  }
}
```

#### 4.1.9 earnings_trading_screener
```json
{
  "name": "earnings_trading_screener",
  "description": "決算トレード対象銘柄のスクリーニング（予想上方修正・下落後回復・サプライズ重視）",
  "inputSchema": {
    "type": "object",
    "properties": {
      "earnings_window": {
        "type": "string",
        "enum": ["yesterday_after_today_before", "today_before_after", "this_week", "custom"],
        "default": "yesterday_after_today_before",
        "description": "決算発表期間（昨日引け後・今日寄り付き前）"
      },
      "market_cap": {
        "type": "string",
        "enum": ["small", "mid", "large", "mega", "smallover"],
        "default": "smallover",
        "description": "時価総額フィルタ"
      },
      "min_price": {
        "type": "number",
        "default": 10,
        "description": "最低株価"
      },
      "min_avg_volume": {
        "type": "number",
        "default": 200000,
        "description": "最低平均出来高"
      },
      "earnings_revision": {
        "type": "string",
        "enum": ["eps_revenue_positive", "eps_positive", "revenue_positive", "any_positive"],
        "default": "eps_revenue_positive",
        "description": "決算予想修正フィルタ"
      },
      "price_trend": {
        "type": "string",
        "enum": ["positive_change", "recovery_from_decline", "any_upward"],
        "default": "positive_change",
        "description": "価格トレンドフィルタ"
      },
      "performance_filter": {
        "type": "object",
        "properties": {
          "recent_decline_recovery": {
            "type": "boolean",
            "default": true,
            "description": "最近の下落からの回復を重視"
          },
          "max_4week_decline": {
            "type": "number",
            "default": -4.0,
            "description": "過去4週間の最大下落率(%)"
          }
        },
        "description": "パフォーマンスフィルタ設定"
      },
      "volatility_filter": {
        "type": "object",
        "properties": {
          "min_volatility": {
            "type": "number",
            "default": 1.0,
            "description": "最低ボラティリティ倍率"
          },
          "max_volatility": {
            "type": "number",
            "description": "最高ボラティリティ倍率"
          }
        },
        "description": "ボラティリティフィルタ設定"
      },
      "data_fields": {
        "type": "array",
        "items": {
          "type": "string",
          "enum": [
            "ticker", "company", "sector", "industry", "market_cap", "price",
            "change", "change_percent", "volume", "avg_volume", "relative_volume",
            "eps_surprise", "revenue_surprise", "eps_estimate", "revenue_estimate",
            "pe_ratio", "target_price", "analyst_recom", "volatility",
            "performance_4w", "performance_1m", "rsi", "beta",
            "float", "outstanding", "insider_own", "institutional_own"
          ]
        },
        "default": [
          "ticker", "company", "sector", "price", "change", "change_percent",
          "eps_surprise", "revenue_surprise", "volume", "relative_volume",
          "market_cap", "volatility", "performance_4w", "target_price"
        ],
        "description": "取得するデータフィールド"
      },
      "max_results": {
        "type": "number",
        "default": 60,
        "description": "最大取得件数"
      },
      "sort_by": {
        "type": "string",
        "enum": ["eps_surprise", "revenue_surprise", "combined_surprise", "change_percent", "volatility", "volume"],
        "default": "eps_surprise",
        "description": "ソート基準"
      },
      "sort_order": {
        "type": "string",
        "enum": ["desc", "asc"],
        "default": "desc",
        "description": "ソート順序"
      },
      "sectors": {
        "type": "array",
        "items": {"type": "string"},
        "description": "対象セクター"
      },
      "exclude_sectors": {
        "type": "array",
        "items": {"type": "string"},
        "description": "除外セクター"
      }
    }
  }
}
```

#### 4.1.10 earnings_positive_surprise_screener
```json
{
  "name": "earnings_positive_surprise_screener",
  "description": "今週決算発表でポジティブサプライズがあって上昇している銘柄のスクリーニング",
  "inputSchema": {
    "type": "object",
    "properties": {
      "earnings_period": {
        "type": "string",
        "enum": ["this_week", "last_week", "this_month", "custom"],
        "default": "this_week",
        "description": "決算発表期間"
      },
      "market_cap": {
        "type": "string",
        "enum": ["small", "mid", "large", "mega", "smallover"],
        "default": "smallover",
        "description": "時価総額フィルタ"
      },
      "min_price": {
        "type": "number",
        "default": 10,
        "description": "最低株価"
      },
      "min_avg_volume": {
        "type": "number",
        "default": 500000,
        "description": "最低平均出来高"
      },
      "growth_criteria": {
        "type": "object",
        "properties": {
          "min_eps_qoq_growth": {
            "type": "number",
            "default": 10.0,
            "description": "最低EPS四半期成長率(%)"
          },
          "min_sales_qoq_growth": {
            "type": "number",
            "default": 5.0,
            "description": "最低売上四半期成長率(%)"
          },
          "min_eps_revision": {
            "type": "number",
            "default": 5.0,
            "description": "最低EPS予想上方修正率(%)"
          }
        },
        "description": "成長性フィルタ条件"
      },
      "performance_criteria": {
        "type": "object",
        "properties": {
          "min_weekly_performance": {
            "type": "number",
            "default": -1.0,
            "description": "最低週間パフォーマンス(%)"
          },
          "max_weekly_performance": {
            "type": "number",
            "default": 5.0,
            "description": "最高週間パフォーマンス(%)"
          },
          "above_sma200": {
            "type": "boolean",
            "default": true,
            "description": "200日移動平均線より上"
          }
        },
        "description": "パフォーマンス基準"
      },
      "target_sectors": {
        "type": "array",
        "items": {
          "type": "string",
          "enum": [
            "technology", "industrials", "healthcare", "communication_services",
            "consumer_cyclical", "financial", "consumer_defensive", "basic_materials",
            "real_estate", "utilities", "energy"
          ]
        },
        "default": [
          "technology", "industrials", "healthcare", "communication_services",
          "consumer_cyclical", "financial"
        ],
        "description": "対象セクター"
      },
      "data_fields": {
        "type": "array",
        "items": {
          "type": "string",
          "enum": [
            "ticker", "company", "sector", "industry", "country", "market_cap",
            "price", "change", "change_percent", "volume", "avg_volume", "relative_volume",
            "earnings_date", "eps_qoq_growth", "sales_qoq_growth", "eps_revision",
            "eps_surprise", "revenue_surprise", "eps_estimate", "revenue_estimate",
            "pe_ratio", "forward_pe", "peg", "target_price", "analyst_recom",
            "performance_1w", "performance_1m", "sma_200_relative", "rsi",
            "beta", "volatility", "float", "outstanding", "insider_own", "institutional_own"
          ]
        },
        "default": [
          "ticker", "company", "sector", "price", "change", "change_percent",
          "earnings_date", "eps_qoq_growth", "sales_qoq_growth", "eps_revision",
          "eps_surprise", "revenue_surprise", "volume", "relative_volume",
          "performance_1w", "target_price", "analyst_recom"
        ],
        "description": "取得するデータフィールド"
      },
      "max_results": {
        "type": "number",
        "default": 50,
        "description": "最大取得件数"
      },
      "sort_by": {
        "type": "string",
        "enum": [
          "eps_qoq_growth", "sales_qoq_growth", "eps_revision", "eps_surprise",
          "combined_surprise", "performance_1w", "change_percent", "relative_volume"
        ],
        "default": "eps_qoq_growth",
        "description": "ソート基準"
      },
      "sort_order": {
        "type": "string",
        "enum": ["desc", "asc"],
        "default": "desc",
        "description": "ソート順序"
      },
      "include_chart_view": {
        "type": "boolean",
        "default": true,
        "description": "週足チャートビューを含める"
      }
    }
  }
}
```

#### 4.1.11 upcoming_earnings_screener
```json
{
  "name": "upcoming_earnings_screener",
  "description": "来週決算予定銘柄のスクリーニング（決算トレード事前準備用）",
  "inputSchema": {
    "type": "object",
    "properties": {
      "earnings_period": {
        "type": "string",
        "enum": ["next_week", "next_2_weeks", "next_month", "custom_range"],
        "default": "next_week",
        "description": "決算発表期間"
      },
      "market_cap": {
        "type": "string",
        "enum": ["small", "mid", "large", "mega", "smallover"],
        "default": "smallover",
        "description": "時価総額フィルタ"
      },
      "min_price": {
        "type": "number",
        "default": 10,
        "description": "最低株価"
      },
      "min_avg_volume": {
        "type": "number",
        "default": 500000,
        "description": "最低平均出来高"
      },
      "target_sectors": {
        "type": "array",
        "items": {
          "type": "string",
          "enum": [
            "technology", "industrials", "healthcare", "communication_services",
            "consumer_cyclical", "financial", "consumer_defensive", "basic_materials",
            "real_estate", "utilities", "energy"
          ]
        },
        "default": [
          "technology", "industrials", "healthcare", "communication_services",
          "consumer_cyclical", "financial", "consumer_defensive", "basic_materials"
        ],
        "description": "対象セクター（8セクター）"
      },
      "pre_earnings_analysis": {
        "type": "object",
        "properties": {
          "include_estimates": {
            "type": "boolean",
            "default": true,
            "description": "EPS・売上予想を含める"
          },
          "include_revisions": {
            "type": "boolean",
            "default": true,
            "description": "予想修正状況を含める"
          },
          "include_historical_surprise": {
            "type": "boolean",
            "default": true,
            "description": "過去のサプライズ履歴を含める"
          },
          "include_options_activity": {
            "type": "boolean",
            "default": false,
            "description": "オプション活動を含める"
          }
        },
        "description": "決算前分析項目"
      },
      "risk_assessment": {
        "type": "object",
        "properties": {
          "include_volatility": {
            "type": "boolean",
            "default": true,
            "description": "ボラティリティ指標を含める"
          },
          "include_short_interest": {
            "type": "boolean",
            "default": true,
            "description": "空売り比率を含める"
          },
          "include_analyst_changes": {
            "type": "boolean",
            "default": true,
            "description": "最近のアナリスト変更を含める"
          }
        },
        "description": "リスク評価項目"
      },
      "data_fields": {
        "type": "array",
        "items": {
          "type": "string",
          "enum": [
            "ticker", "company", "sector", "industry", "country", "market_cap",
            "price", "change", "change_percent", "volume", "avg_volume", "relative_volume",
            "earnings_date", "earnings_timing", "eps_estimate", "revenue_estimate",
            "eps_estimate_revision", "revenue_estimate_revision", "analyst_count",
            "pe_ratio", "forward_pe", "peg", "target_price", "analyst_recom",
            "performance_1w", "performance_1m", "performance_3m", "sma_200_relative",
            "rsi", "beta", "volatility", "short_interest", "short_ratio",
            "float", "outstanding", "insider_own", "institutional_own",
            "historical_eps_surprise", "historical_revenue_surprise"
          ]
        },
        "default": [
          "ticker", "company", "sector", "industry", "earnings_date", "earnings_timing",
          "eps_estimate", "revenue_estimate", "eps_estimate_revision", "analyst_count",
          "price", "market_cap", "pe_ratio", "target_price", "analyst_recom",
          "volatility", "short_interest", "avg_volume"
        ],
        "description": "取得するデータフィールド"
      },
      "max_results": {
        "type": "number",
        "default": 100,
        "description": "最大取得件数"
      },
      "sort_by": {
        "type": "string",
        "enum": [
          "earnings_date", "market_cap", "eps_estimate_revision", "analyst_recom",
          "volatility", "short_interest", "target_price_upside", "ticker"
        ],
        "default": "earnings_date",
        "description": "ソート基準"
      },
      "sort_order": {
        "type": "string",
        "enum": ["asc", "desc"],
        "default": "asc",
        "description": "ソート順序"
      },
      "include_chart_view": {
        "type": "boolean",
        "default": true,
        "description": "週足チャートビューを含める"
      },
      "earnings_calendar_format": {
        "type": "boolean",
        "default": false,
        "description": "決算カレンダー形式で出力"
      }
    }
  }
}
```

### 4.2 ファンダメンタルデータツール

#### 4.2.1 get_stock_fundamentals
```json
{
  "name": "get_stock_fundamentals",
  "description": "個別銘柄のファンダメンタルデータ取得",
  "inputSchema": {
    "type": "object",
    "properties": {
      "ticker": {"type": "string", "description": "銘柄ティッカー"},
      "data_fields": {
        "type": "array",
        "items": {"type": "string"},
        "description": "取得データフィールド"
      }
    },
    "required": ["ticker"]
  }
}
```

#### 4.2.2 get_multiple_stocks_fundamentals
```json
{
  "name": "get_multiple_stocks_fundamentals",
  "description": "複数銘柄のファンダメンタルデータ一括取得",
  "inputSchema": {
    "type": "object",
    "properties": {
      "tickers": {
        "type": "array",
        "items": {"type": "string"},
        "description": "銘柄ティッカーリスト"
      },
      "data_fields": {
        "type": "array",
        "items": {"type": "string"},
        "description": "取得データフィールド"
      }
    },
    "required": ["tickers"]
  }
}
```

### 4.3 ニュースツール

#### 4.3.1 get_stock_news
```json
{
  "name": "get_stock_news",
  "description": "銘柄関連ニュースの取得",
  "inputSchema": {
    "type": "object",
    "properties": {
      "ticker": {"type": "string", "description": "銘柄ティッカー"},
      "days_back": {"type": "number", "description": "過去何日分のニュース"},
      "news_type": {
        "type": "string",
        "enum": ["all", "earnings", "analyst", "insider", "general"],
        "description": "ニュースタイプ"
      }
    },
    "required": ["ticker"]
  }
}
```

### 4.4 セクター・業界分析ツール

#### 4.4.1 get_sector_performance
```json
{
  "name": "get_sector_performance",
  "description": "セクター別パフォーマンス分析",
  "inputSchema": {
    "type": "object",
    "properties": {
      "timeframe": {
        "type": "string",
        "enum": ["1d", "1w", "1m", "3m", "6m", "1y"],
        "description": "分析期間"
      },
      "sectors": {
        "type": "array",
        "items": {"type": "string"},
        "description": "対象セクター"
      }
    }
  }
}
```

#### 4.4.2 get_industry_performance
```json
{
  "name": "get_industry_performance",
  "description": "業界別パフォーマンス分析",
  "inputSchema": {
    "type": "object",
    "properties": {
      "timeframe": {
        "type": "string",
        "enum": ["1d", "1w", "1m", "3m", "6m", "1y"],
        "description": "分析期間"
      },
      "industries": {
        "type": "array",
        "items": {"type": "string"},
        "description": "対象業界"
      }
    }
  }
}
```

#### 4.4.3 get_country_performance
```json
{
  "name": "get_country_performance",
  "description": "国別市場パフォーマンス分析",
  "inputSchema": {
    "type": "object",
    "properties": {
      "timeframe": {
        "type": "string",
        "enum": ["1d", "1w", "1m", "3m", "6m", "1y"],
        "description": "分析期間"
      },
      "countries": {
        "type": "array",
        "items": {"type": "string"},
        "description": "対象国"
      }
    }
  }
}
```

### 4.5 テクニカル分析ツール

#### 4.5.1 get_relative_volume_stocks
```json
{
  "name": "get_relative_volume_stocks",
  "description": "相対出来高異常銘柄の検出",
  "inputSchema": {
    "type": "object",
    "properties": {
      "min_relative_volume": {"type": "number", "description": "最低相対出来高"},
      "min_price": {"type": "number", "description": "最低株価"},
      "sectors": {
        "type": "array",
        "items": {"type": "string"},
        "description": "対象セクター"
      }
    },
    "required": ["min_relative_volume"]
  }
}
```

## 5. データモデル

### 5.1 共通データ構造

#### StockData
```python
@dataclass
class StockData:
    ticker: str
    company_name: str
    sector: str
    industry: str
    country: Optional[str]            # 国
    market_cap: float
    price: float
    volume: int
    avg_volume: int
    relative_volume: Optional[float]  # 相対出来高倍率
    price_change: Optional[float]     # 価格変動率(%)
    price_change_abs: Optional[float] # 価格変動額
    gap: Optional[float]              # ギャップ（前日終値からの変動）
    # 時間外取引データ
    premarket_price: Optional[float]        # 寄り付き前価格
    premarket_change: Optional[float]       # 寄り付き前変動額
    premarket_change_percent: Optional[float] # 寄り付き前変動率(%)
    afterhours_price: Optional[float]       # 時間外価格
    afterhours_change: Optional[float]      # 時間外変動額
    afterhours_change_percent: Optional[float] # 時間外変動率(%)
    # 決算関連データ
    earnings_date: Optional[str]      # 決算発表日
    earnings_timing: Optional[str]    # 決算発表タイミング（before/after）
    eps_surprise: Optional[float]     # EPSサプライズ(%)
    revenue_surprise: Optional[float] # 売上サプライズ(%)
    eps_estimate: Optional[float]     # EPS予想
    revenue_estimate: Optional[float] # 売上予想
    eps_actual: Optional[float]       # EPS実績
    revenue_actual: Optional[float]   # 売上実績
    eps_qoq_growth: Optional[float]   # EPS四半期成長率(%)
    sales_qoq_growth: Optional[float] # 売上四半期成長率(%)
    eps_revision: Optional[float]     # EPS予想上方修正率(%)
    revenue_revision: Optional[float] # 売上予想修正率(%)
    # テクニカル・パフォーマンス指標
    volatility: Optional[float]       # ボラティリティ
    beta: Optional[float]             # ベータ値
    performance_1w: Optional[float]   # 1週間パフォーマンス(%)
    performance_1m: Optional[float]   # 1ヶ月パフォーマンス(%)
    performance_4w: Optional[float]   # 4週間パフォーマンス(%)
    performance_ytd: Optional[float]  # 年初来パフォーマンス(%)
    # 基本指標
    pe_ratio: Optional[float]
    forward_pe: Optional[float]       # フォワードPER
    peg: Optional[float]              # PEGレシオ
    eps: Optional[float]
    dividend_yield: Optional[float]
    rsi: Optional[float]
    sma_20: Optional[float]
    sma_50: Optional[float]
    sma_200: Optional[float]
    above_sma_20: Optional[bool]      # SMA20より上にあるか
    above_sma_50: Optional[bool]      # SMA50より上にあるか  
    above_sma_200: Optional[bool]     # SMA200より上にあるか
    sma_20_relative: Optional[float]  # SMA20との相対位置(%)
    sma_50_relative: Optional[float]  # SMA50との相対位置(%)
    sma_200_relative: Optional[float] # SMA200との相対位置(%)
    target_price: Optional[float]     # アナリスト目標価格
    analyst_recommendation: Optional[str]  # アナリスト推奨
    insider_ownership: Optional[float]     # インサイダー保有率
    institutional_ownership: Optional[float] # 機関投資家保有率
    short_interest: Optional[float]        # 空売り比率
    float_shares: Optional[int]            # 浮動株数
    outstanding_shares: Optional[int]      # 発行済み株式数
    week_52_high: Optional[float]          # 52週高値
    week_52_low: Optional[float]           # 52週安値
    
    def to_dict(self) -> dict:
        return asdict(self)
```

#### NewsData
```python
@dataclass
class NewsData:
    ticker: str
    title: str
    source: str
    date: datetime
    url: str
    category: str
    
    def to_dict(self) -> dict:
        return asdict(self)
```

#### SectorPerformance
```python
@dataclass
class SectorPerformance:
    sector: str
    performance_1d: float
    performance_1w: float
    performance_1m: float
    performance_3m: float
    performance_6m: float
    performance_1y: float
    stock_count: int
    
    def to_dict(self) -> dict:
        return asdict(self)
```

#### EarningsData
```python
@dataclass
class EarningsData:
    ticker: str
    company_name: str
    earnings_date: str
    earnings_timing: str              # "before" or "after"
    # 価格データ
    pre_earnings_price: Optional[float]    # 決算発表前価格
    post_earnings_price: Optional[float]   # 決算発表後価格
    premarket_price: Optional[float]       # 寄り付き前価格
    afterhours_price: Optional[float]      # 時間外価格
    current_price: Optional[float]         # 現在価格
    price_change_percent: Optional[float]  # 価格変動率
    gap_percent: Optional[float]          # ギャップ率
    # 出来高データ
    volume: Optional[int]                 # 出来高
    avg_volume: Optional[int]             # 平均出来高
    relative_volume: Optional[float]      # 相対出来高
    # 決算結果・サプライズ
    eps_surprise: Optional[float]         # EPSサプライズ(%)
    revenue_surprise: Optional[float]     # 売上サプライズ(%)
    eps_estimate: Optional[float]         # EPS予想
    eps_actual: Optional[float]           # EPS実績
    revenue_estimate: Optional[float]     # 売上予想
    revenue_actual: Optional[float]       # 売上実績
    earnings_revision: Optional[str]      # 予想修正状況
    # 市場反応・分析
    market_reaction: Optional[str]        # "positive", "negative", "neutral"
    volatility: Optional[float]           # ボラティリティ
    beta: Optional[float]                 # ベータ値
    performance_4w: Optional[float]       # 過去4週間パフォーマンス
    recovery_from_decline: Optional[bool] # 下落からの回復か
    trading_opportunity_score: Optional[float] # トレード機会スコア(1-10)
    
    def to_dict(self) -> dict:
        return asdict(self)
```

#### UpcomingEarningsData
```python
@dataclass
class UpcomingEarningsData:
    ticker: str
    company_name: str
    sector: str
    industry: str
    earnings_date: str
    earnings_timing: str              # "before" or "after"
    # 基本株価データ
    current_price: Optional[float]    # 現在価格
    market_cap: Optional[float]       # 時価総額
    avg_volume: Optional[int]         # 平均出来高
    # 決算予想データ
    eps_estimate: Optional[float]         # EPS予想
    revenue_estimate: Optional[float]     # 売上予想
    eps_estimate_revision: Optional[float] # EPS予想修正率(%)
    revenue_estimate_revision: Optional[float] # 売上予想修正率(%)
    analyst_count: Optional[int]          # アナリスト数
    estimate_trend: Optional[str]         # 予想トレンド ("improving", "declining", "stable")
    # 過去のサプライズ履歴
    historical_eps_surprise: Optional[List[float]]     # 過去4四半期EPSサプライズ
    historical_revenue_surprise: Optional[List[float]] # 過去4四半期売上サプライズ
    avg_eps_surprise: Optional[float]     # 平均EPSサプライズ
    avg_revenue_surprise: Optional[float] # 平均売上サプライズ
    # 評価・推奨データ
    pe_ratio: Optional[float]             # PER
    forward_pe: Optional[float]           # フォワードPER
    peg: Optional[float]                  # PEGレシオ
    target_price: Optional[float]         # 目標価格
    target_price_upside: Optional[float]  # 目標価格までの上昇余地(%)
    analyst_recommendation: Optional[str]  # アナリスト推奨
    recent_rating_changes: Optional[List[dict]] # 最近の格付け変更
    # リスク評価指標
    volatility: Optional[float]           # ボラティリティ
    beta: Optional[float]                 # ベータ値
    short_interest: Optional[float]       # 空売り比率(%)
    short_ratio: Optional[float]          # 空売り比率（日数）
    insider_ownership: Optional[float]    # インサイダー保有率
    institutional_ownership: Optional[float] # 機関投資家保有率
    # パフォーマンス・テクニカル指標
    performance_1w: Optional[float]       # 1週間パフォーマンス
    performance_1m: Optional[float]       # 1ヶ月パフォーマンス
    performance_3m: Optional[float]       # 3ヶ月パフォーマンス
    sma_200_relative: Optional[float]     # 200日移動平均との相対位置
    rsi: Optional[float]                  # RSI
    # オプション活動（オプション）
    options_volume: Optional[int]         # オプション出来高
    put_call_ratio: Optional[float]       # プット・コール比率
    implied_volatility: Optional[float]   # インプライドボラティリティ
    # 決算前分析スコア
    earnings_potential_score: Optional[float]    # 決算機会スコア(1-10)
    risk_score: Optional[float]                  # リスクスコア(1-10)
    surprise_probability: Optional[float]        # サプライズ確率(%)
    
    def to_dict(self) -> dict:
        return asdict(self)
```

## 6. エラーハンドリング

### 6.1 エラー分類

- **認証エラー**: Finviz API キーの問題
- **レート制限エラー**: API呼び出し頻度制限
- **データ形式エラー**: 不正な入力パラメータ
- **ネットワークエラー**: 接続問題
- **データ不足エラー**: 要求されたデータが存在しない

### 6.2 エラーレスポンス形式

```json
{
  "error": {
    "code": "AUTHENTICATION_ERROR",
    "message": "Invalid API key provided",
    "details": {
      "suggestion": "Please check your FINVIZ_API_KEY environment variable"
    }
  }
}
```

## 7. 設定とデプロイメント

### 7.1 環境変数

```bash
FINVIZ_API_KEY=your_finviz_api_key_here
MCP_SERVER_PORT=8080
LOG_LEVEL=INFO
RATE_LIMIT_REQUESTS_PER_MINUTE=100
```

### 7.2 依存関係

```txt
mcp>=0.1.0
requests>=2.31.0
pandas>=2.0.0
python-dotenv>=1.0.0
pydantic>=2.0.0
```

## 8. 使用例

### 8.1 決算スクリーニング

```python
# MCP Client側での使用例

# 基本的な決算スクリーニング
result = await mcp_client.call_tool(
    "earnings_screener",
    {
        "earnings_date": "today_after",
        "market_cap": "large",
        "min_price": 10,
        "min_volume": 1000000,
        "sectors": ["Technology", "Healthcare"]
    }
)

# 引け後決算発表で時間外取引価格上昇銘柄のスクリーニング
result = await mcp_client.call_tool(
    "earnings_screener",
    {
        "earnings_date": "today_after",
        "market_cap": "large",
        "min_price": 10,
        "min_volume": 1000000,
        "sectors": ["Technology", "Healthcare"],
        "afterhours_price_change": {
            "enabled": True,
            "min_change_percent": 2.0,
            "max_change_percent": 15.0
        }
    }
)

# 寄り付き前決算発表で通常取引価格上昇銘柄のスクリーニング
result = await mcp_client.call_tool(
    "earnings_screener",
    {
        "earnings_date": "tomorrow_before",
        "market_cap": "mid",
        "min_price": 5,
        "min_volume": 500000,
        "premarket_price_change": {
            "enabled": True,
            "min_change_percent": 1.0,
            "max_change_percent": 10.0
        }
    }
)
```

### 8.2 出来高急増スクリーニング

```python
# 基本的な出来高急増スクリーニング（URLの条件を再現）
result = await mcp_client.call_tool(
    "volume_surge_screener",
    {
        "market_cap": "smallover",
        "min_price": 10,
        "min_avg_volume": 100000,
        "min_relative_volume": 1.5,
        "min_price_change": 2.0,
        "sma_filter": "above_sma200",
        "stocks_only": True,
        "sort_by": "price_change",
        "max_results": 50
    }
)

# テクノロジーセクターに絞った出来高急増スクリーニング
result = await mcp_client.call_tool(
    "volume_surge_screener",
    {
        "market_cap": "large",
        "min_price": 20,
        "min_relative_volume": 2.0,
        "min_price_change": 3.0,
        "sma_filter": "above_sma50",
        "sectors": ["Technology"],
        "sort_by": "relative_volume",
        "max_results": 25
    }
)

# より厳しい条件での高品質な急騰銘柄スクリーニング
result = await mcp_client.call_tool(
    "volume_surge_screener",
    {
        "market_cap": "mid",
        "min_price": 15,
        "min_avg_volume": 500000,
        "min_relative_volume": 3.0,
        "min_price_change": 5.0,
        "sma_filter": "above_sma20",
        "exclude_sectors": ["Financial", "Real Estate"],
        "sort_by": "price_change",
        "max_results": 20
    }
)
```

### 8.3 寄り付き前決算スクリーニング

```python
# 基本的な寄り付き前決算スクリーニング（URLの条件を再現）
result = await mcp_client.call_tool(
    "earnings_premarket_screener",
    {
        "earnings_timing": "today_before",
        "market_cap": "smallover",
        "min_price": 10,
        "min_avg_volume": 100000,
        "min_price_change": 2.0,
        "include_premarket_data": True,
        "max_results": 60,
        "sort_by": "change_percent",
        "sort_order": "desc"
    }
)

# 大型株に絞った寄り付き前決算スクリーニング
result = await mcp_client.call_tool(
    "earnings_premarket_screener",
    {
        "earnings_timing": "today_before",
        "market_cap": "large",
        "min_price": 25,
        "min_avg_volume": 1000000,
        "min_price_change": 1.5,
        "max_price_change": 20.0,
        "sectors": ["Technology", "Healthcare", "Consumer Discretionary"],
        "data_fields": [
            "ticker", "company", "sector", "price", "change", "change_percent",
            "volume", "relative_volume", "market_cap", "pe_ratio", "target_price",
            "analyst_recom", "gap", "52w_high", "52w_low"
        ],
        "max_results": 30,
        "sort_by": "change_percent"
    }
)

# より詳細なデータを含む寄り付き前決算スクリーニング
result = await mcp_client.call_tool(
    "earnings_premarket_screener",
    {
        "earnings_timing": "today_before",
        "market_cap": "mid",
        "min_price": 15,
        "min_avg_volume": 500000,
        "min_price_change": 3.0,
        "exclude_sectors": ["Financial", "Real Estate"],
        "data_fields": [
            "ticker", "company", "sector", "industry", "country",
            "market_cap", "pe_ratio", "price", "change", "change_percent",
            "volume", "avg_volume", "relative_volume", "float", "outstanding",
            "insider_own", "institutional_own", "short_interest", "target_price",
            "52w_high", "52w_low", "rsi", "gap", "analyst_recom"
        ],
        "max_results": 40,
        "sort_by": "relative_volume",
        "sort_order": "desc"
    }
)
```

### 8.4 引け後決算・時間外取引スクリーニング

```python
# 基本的な引け後決算・時間外上昇スクリーニング（URLの条件を再現）
result = await mcp_client.call_tool(
    "earnings_afterhours_screener",
    {
        "earnings_timing": "today_after",
        "market_cap": "smallover",
        "min_price": 10,
        "min_avg_volume": 100000,
        "min_afterhours_change": 2.0,
        "include_afterhours_data": True,
        "max_results": 60,
        "sort_by": "afterhours_change_percent",
        "sort_order": "desc"
    }
)

# 大型株の引け後決算・時間外上昇スクリーニング
result = await mcp_client.call_tool(
    "earnings_afterhours_screener",
    {
        "earnings_timing": "today_after",
        "market_cap": "large",
        "min_price": 20,
        "min_avg_volume": 1000000,
        "min_afterhours_change": 1.5,
        "max_afterhours_change": 25.0,
        "sectors": ["Technology", "Healthcare", "Consumer Discretionary"],
        "data_fields": [
            "ticker", "company", "sector", "price", "afterhours_change", "afterhours_change_percent",
            "afterhours_price", "volume", "relative_volume", "market_cap", "pe_ratio", 
            "target_price", "analyst_recom", "52w_high", "52w_low"
        ],
        "max_results": 30,
        "sort_by": "afterhours_change_percent"
    }
)

# 時間外取引で異常な上昇を示す銘柄の詳細スクリーニング
result = await mcp_client.call_tool(
    "earnings_afterhours_screener",
    {
        "earnings_timing": "today_after",
        "market_cap": "mid",
        "min_price": 15,
        "min_avg_volume": 250000,
        "min_afterhours_change": 5.0,
        "max_afterhours_change": 50.0,
        "exclude_sectors": ["Financial", "Real Estate", "Utilities"],
        "data_fields": [
            "ticker", "company", "sector", "industry", "country",
            "market_cap", "pe_ratio", "price", "change", "change_percent",
            "afterhours_change", "afterhours_change_percent", "afterhours_price",
            "volume", "avg_volume", "relative_volume", "float", "outstanding",
            "insider_own", "institutional_own", "short_interest", "target_price",
            "52w_high", "52w_low", "rsi", "gap", "analyst_recom"
        ],
        "max_results": 25,
        "sort_by": "afterhours_change_percent",
        "sort_order": "desc"
    }
)
```

### 8.5 決算トレード対象銘柄スクリーニング

```python
# 基本的な決算トレード対象銘柄スクリーニング（URLの条件を再現）
result = await mcp_client.call_tool(
    "earnings_trading_screener",
    {
        "earnings_window": "yesterday_after_today_before",
        "market_cap": "smallover",
        "min_price": 10,
        "min_avg_volume": 200000,
        "earnings_revision": "eps_revenue_positive",
        "price_trend": "positive_change",
        "performance_filter": {
            "recent_decline_recovery": True,
            "max_4week_decline": -4.0
        },
        "volatility_filter": {
            "min_volatility": 1.0
        },
        "max_results": 60,
        "sort_by": "eps_surprise",
        "sort_order": "desc"
    }
)

# 大型株に特化した決算トレードスクリーニング
result = await mcp_client.call_tool(
    "earnings_trading_screener",
    {
        "earnings_window": "yesterday_after_today_before",
        "market_cap": "large",
        "min_price": 25,
        "min_avg_volume": 1000000,
        "earnings_revision": "eps_revenue_positive",
        "price_trend": "recovery_from_decline",
        "performance_filter": {
            "recent_decline_recovery": True,
            "max_4week_decline": -8.0
        },
        "volatility_filter": {
            "min_volatility": 0.8,
            "max_volatility": 3.0
        },
        "sectors": ["Technology", "Healthcare", "Consumer Discretionary"],
        "data_fields": [
            "ticker", "company", "sector", "price", "change", "change_percent",
            "eps_surprise", "revenue_surprise", "eps_estimate", "revenue_estimate",
            "volume", "relative_volume", "market_cap", "pe_ratio", "volatility",
            "performance_4w", "performance_1m", "target_price", "analyst_recom"
        ],
        "max_results": 30,
        "sort_by": "combined_surprise"
    }
)

# 高ボラティリティ決算トレード候補スクリーニング
result = await mcp_client.call_tool(
    "earnings_trading_screener",
    {
        "earnings_window": "today_before_after",
        "market_cap": "mid",
        "min_price": 15,
        "min_avg_volume": 500000,
        "earnings_revision": "any_positive",
        "price_trend": "any_upward",
        "performance_filter": {
            "recent_decline_recovery": True,
            "max_4week_decline": -10.0
        },
        "volatility_filter": {
            "min_volatility": 2.0,
            "max_volatility": 8.0
        },
        "exclude_sectors": ["Financial", "Real Estate", "Utilities"],
        "data_fields": [
            "ticker", "company", "sector", "industry", "market_cap", "price",
            "change", "change_percent", "volume", "avg_volume", "relative_volume",
            "eps_surprise", "revenue_surprise", "eps_estimate", "revenue_estimate",
            "pe_ratio", "target_price", "analyst_recom", "volatility", "beta",
            "performance_4w", "performance_1m", "rsi", "float", "outstanding"
        ],
        "max_results": 40,
        "sort_by": "volatility",
        "sort_order": "desc"
    }
)
```

### 8.6 決算ポジティブサプライズ銘柄スクリーニング

```python
# 基本的な今週決算ポジティブサプライズスクリーニング（URLの条件を再現）
result = await mcp_client.call_tool(
    "earnings_positive_surprise_screener",
    {
        "earnings_period": "this_week",
        "market_cap": "smallover",
        "min_price": 10,
        "min_avg_volume": 500000,
        "growth_criteria": {
            "min_eps_qoq_growth": 10.0,
            "min_sales_qoq_growth": 5.0,
            "min_eps_revision": 5.0
        },
        "performance_criteria": {
            "min_weekly_performance": -1.0,
            "max_weekly_performance": 5.0,
            "above_sma200": True
        },
        "target_sectors": [
            "technology", "industrials", "healthcare", 
            "communication_services", "consumer_cyclical", "financial"
        ],
        "max_results": 50,
        "sort_by": "eps_qoq_growth",
        "include_chart_view": True
    }
)

# 高成長・強いサプライズに特化したスクリーニング
result = await mcp_client.call_tool(
    "earnings_positive_surprise_screener",
    {
        "earnings_period": "this_week",
        "market_cap": "large",
        "min_price": 20,
        "min_avg_volume": 1000000,
        "growth_criteria": {
            "min_eps_qoq_growth": 20.0,
            "min_sales_qoq_growth": 10.0,
            "min_eps_revision": 10.0
        },
        "performance_criteria": {
            "min_weekly_performance": 0.0,
            "max_weekly_performance": 15.0,
            "above_sma200": True
        },
        "target_sectors": ["technology", "healthcare", "communication_services"],
        "data_fields": [
            "ticker", "company", "sector", "price", "change", "change_percent",
            "earnings_date", "eps_qoq_growth", "sales_qoq_growth", "eps_revision",
            "eps_surprise", "revenue_surprise", "eps_estimate", "revenue_estimate",
            "pe_ratio", "forward_pe", "peg", "target_price", "analyst_recom",
            "performance_1w", "performance_1m", "relative_volume", "beta"
        ],
        "max_results": 25,
        "sort_by": "combined_surprise"
    }
)

# 週間パフォーマンス重視のスクリーニング
result = await mcp_client.call_tool(
    "earnings_positive_surprise_screener",
    {
        "earnings_period": "this_week",
        "market_cap": "mid",
        "min_price": 15,
        "min_avg_volume": 250000,
        "growth_criteria": {
            "min_eps_qoq_growth": 15.0,
            "min_sales_qoq_growth": 7.5,
            "min_eps_revision": 7.5
        },
        "performance_criteria": {
            "min_weekly_performance": 2.0,
            "max_weekly_performance": 20.0,
            "above_sma200": True
        },
        "target_sectors": [
            "technology", "industrials", "healthcare", "consumer_cyclical"
        ],
        "data_fields": [
            "ticker", "company", "sector", "industry", "country", "market_cap",
            "price", "change", "change_percent", "volume", "avg_volume", "relative_volume",
            "earnings_date", "eps_qoq_growth", "sales_qoq_growth", "eps_revision",
            "eps_surprise", "revenue_surprise", "performance_1w", "performance_1m",
            "sma_200_relative", "target_price", "analyst_recom", "volatility"
        ],
        "max_results": 30,
        "sort_by": "performance_1w",
        "sort_order": "desc",
        "include_chart_view": True
    }
)
```

### 8.6.1 実際のスクリーニング結果例

提供されたURLのスクリーニング結果から、以下のような銘柄が抽出されています：

```python
# 実際の今週決算ポジティブサプライズ銘柄例
example_results = [
    {
        "ticker": "AVAV",
        "company": "AeroVironment Inc",
        "sector": "Industrials",
        "industry": "Aerospace & Defense", 
        "eps_qoq_growth": 173.98,  # 173.98%のEPS成長
        "sales_qoq_growth": 39.63,  # 39.63%の売上成長
        "market_cap": "12.71B",
        "pe_ratio": 180.17,
        "forward_pe": 65.56,
        "target_price": 249.29,
        "performance_analysis": "極めて高いEPS成長率でポジティブサプライズ"
    },
    {
        "ticker": "CCL", 
        "company": "Carnival Corp",
        "sector": "Consumer Cyclical",
        "industry": "Travel Services",
        "eps_qoq_growth": 474.17,  # 474.17%の驚異的なEPS成長
        "sales_qoq_growth": 9.46,   # 9.46%の売上成長
        "market_cap": "35.36B",
        "pe_ratio": 14.78,
        "forward_pe": 12.01,
        "target_price": 29.49,
        "performance_analysis": "旅行業界回復による大幅EPS改善"
    },
    {
        "ticker": "SNX",
        "company": "TD Synnex Corp", 
        "sector": "Technology",
        "industry": "Electronics & Computer Distribution",
        "eps_qoq_growth": 33.37,   # 33.37%のEPS成長
        "sales_qoq_growth": 7.16,   # 7.16%の売上成長
        "market_cap": "11.31B",
        "pe_ratio": 15.75,
        "forward_pe": 9.93,
        "target_price": 149.00,
        "performance_analysis": "テクノロジー流通での堅実な成長"
    }
]
```

### 8.7 来週決算予定銘柄スクリーニング

```python
# 基本的な来週決算予定銘柄スクリーニング（URLの条件を再現）
result = await mcp_client.call_tool(
    "upcoming_earnings_screener",
    {
        "earnings_period": "next_week",
        "market_cap": "smallover",
        "min_price": 10,
        "min_avg_volume": 500000,
        "target_sectors": [
            "technology", "industrials", "healthcare", "communication_services",
            "consumer_cyclical", "financial", "consumer_defensive", "basic_materials"
        ],
        "pre_earnings_analysis": {
            "include_estimates": True,
            "include_revisions": True,
            "include_historical_surprise": True,
            "include_options_activity": False
        },
        "risk_assessment": {
            "include_volatility": True,
            "include_short_interest": True,
            "include_analyst_changes": True
        },
        "sort_by": "earnings_date",
        "sort_order": "asc",
        "max_results": 100
    }
)

# 大型株に特化した来週決算予定銘柄スクリーニング
result = await mcp_client.call_tool(
    "upcoming_earnings_screener",
    {
        "earnings_period": "next_week",
        "market_cap": "large",
        "min_price": 25,
        "min_avg_volume": 1000000,
        "target_sectors": ["technology", "healthcare", "financial"],
        "pre_earnings_analysis": {
            "include_estimates": True,
            "include_revisions": True,
            "include_historical_surprise": True,
            "include_options_activity": True
        },
        "risk_assessment": {
            "include_volatility": True,
            "include_short_interest": True,
            "include_analyst_changes": True
        },
        "data_fields": [
            "ticker", "company", "sector", "industry", "earnings_date", "earnings_timing",
            "eps_estimate", "revenue_estimate", "eps_estimate_revision", "analyst_count",
            "target_price", "target_price_upside", "analyst_recom", "pe_ratio", "forward_pe",
            "volatility", "short_interest", "avg_volume", "market_cap",
            "historical_eps_surprise", "historical_revenue_surprise"
        ],
        "sort_by": "target_price_upside",
        "sort_order": "desc",
        "max_results": 50
    }
)

# 決算カレンダー形式での詳細分析
result = await mcp_client.call_tool(
    "upcoming_earnings_screener",
    {
        "earnings_period": "next_week",
        "market_cap": "mid",
        "min_price": 15,
        "min_avg_volume": 250000,
        "target_sectors": [
            "technology", "industrials", "healthcare", "consumer_cyclical"
        ],
        "pre_earnings_analysis": {
            "include_estimates": True,
            "include_revisions": True,
            "include_historical_surprise": True,
            "include_options_activity": True
        },
        "risk_assessment": {
            "include_volatility": True,
            "include_short_interest": True,
            "include_analyst_changes": True
        },
        "data_fields": [
            "ticker", "company", "sector", "industry", "earnings_date", "earnings_timing",
            "eps_estimate", "revenue_estimate", "eps_estimate_revision", "revenue_estimate_revision",
            "analyst_count", "pe_ratio", "forward_pe", "peg", "target_price", "target_price_upside",
            "analyst_recom", "volatility", "beta", "short_interest", "short_ratio",
            "performance_1w", "performance_1m", "performance_3m", "sma_200_relative", "rsi",
            "historical_eps_surprise", "historical_revenue_surprise"
        ],
        "earnings_calendar_format": True,
        "include_chart_view": True,
        "sort_by": "earnings_date",
        "sort_order": "asc",
        "max_results": 75
    }
)
```

### 8.7.1 実際のスクリーニング結果例

提供されたURLのスクリーニング結果から、以下のような来週決算予定銘柄が抽出されています：

```python
# 実際の来週決算予定銘柄例
upcoming_earnings_examples = [
    {
        "ticker": "MSM",
        "company": "MSC Industrial Direct Co., Inc",
        "sector": "Industrials",
        "industry": "Industrial Distribution",
        "earnings_date": "2025-07-01",
        "earnings_timing": "before",
        "market_cap": "4.76B",
        "current_price": 85.50,
        "pe_ratio": 22.50,
        "forward_pe": 21.77,
        "target_price": 82.33,
        "analyst_recom": "2.55",  # Buy=1, Hold=2, Sell=3の平均
        "avg_volume": "528.55K",
        "dividend_yield": 4.05,
        "week_52_range": "68.10 - 90.81",
        "earnings_analysis": "産業流通セクター、安定配当、決算前準備に適した銘柄"
    },
    {
        "ticker": "PRGS",
        "company": "Progress Software Corp",
        "sector": "Technology",
        "industry": "Software - Infrastructure",
        "earnings_date": "2025-06-30",
        "earnings_timing": "after",
        "market_cap": "2.74B",
        "current_price": 63.82,
        "pe_ratio": 49.48,
        "forward_pe": 11.17,
        "peg": 7.58,
        "target_price": 71.71,
        "target_price_upside": 12.4,  # 約12.4%のアップサイド
        "analyst_recom": "1.75",  # 強い買い推奨
        "avg_volume": "568.99K",
        "week_52_range": "50.68 - 70.56",
        "earnings_analysis": "ソフトウェア・インフラ、高いフォワードPE乖離、強い買い推奨"
    },
    {
        "ticker": "STZ",
        "company": "Constellation Brands Inc",
        "sector": "Consumer Defensive",
        "industry": "Beverages - Brewers",
        "earnings_date": "2025-07-01",
        "earnings_timing": "after",
        "market_cap": "28.54B",
        "current_price": 166.50,
        "pe_ratio": None,  # 負のEPSのため計算不可
        "forward_pe": 11.71,
        "target_price": 201.00,
        "target_price_upside": 20.7,  # 約20.7%のアップサイド
        "analyst_recom": "1.96",
        "avg_volume": "2.12M",
        "dividend_yield": 2.57,
        "week_52_range": "159.35 - 264.45",
        "earnings_analysis": "大型酒類銘柄、高いアップサイド期待、S&P500構成銘柄"
    }
]
```

### 8.8 ファンダメンタルデータ取得

```python
result = await mcp_client.call_tool(
    "get_stock_fundamentals",
    {
        "ticker": "AAPL",
        "data_fields": ["pe_ratio", "eps", "revenue_growth", "roe"]
    }
)
```

## 9. パフォーマンス最適化

### 9.1 キャッシュ戦略

- **データキャッシュ**: 頻繁にアクセスされるデータの一時保存
- **レスポンスキャッシュ**: 同一クエリの結果キャッシュ
- **TTL管理**: データ種別に応じた有効期限設定

### 9.2 バッチ処理

- **バッチリクエスト**: 複数銘柄の一括取得
- **並列処理**: 独立したリクエストの並列実行
- **レート制限対応**: API制限に応じたリクエスト調整

## 10. テスト戦略

### 10.1 単体テスト

- 各MCPツールの入力検証
- API呼び出しのモック化
- エラーハンドリングの検証

### 10.2 統合テスト

- 実際のFinviz APIとの連携テスト
- データ整合性の確認
- パフォーマンステスト

## 11. 運用・監視

### 11.1 ログ設定

```python
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        '': {
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': False
        }
    }
})
```

### 11.2 メトリクス収集

- API呼び出し回数
- レスポンス時間
- エラー率
- キャッシュヒット率

## 12. 今後の拡張計画

### 12.1 Phase 1: 基本機能実装
- 主要スクリーニング機能
- ファンダメンタルデータ取得
- 基本的なエラーハンドリング

### 12.2 Phase 2: 高度な機能追加
- ニュース分析機能
- テクニカル分析機能
- パフォーマンス最適化

### 12.3 Phase 3: 運用機能強化
- 詳細な監視・ログ機能
- 自動テスト強化
- ドキュメント整備

## 13. まとめ

このMCP Serverは、既存のFinvizスクリプト群の機能を統合し、MCP経由でアクセス可能な統一されたAPIを提供します。投資判断に必要な様々なデータを効率的に取得し、分析することが可能になります。