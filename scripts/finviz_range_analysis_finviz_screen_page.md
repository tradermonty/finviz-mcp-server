# Finviz カスタム範囲・レンジ指定 詳細解析

HTMLファイル: `finviz_screen_page.html`

このドキュメントは、Finvizでカスタム範囲（手入力レンジ）を指定した際のURLパターンを詳細に解析した結果です。

## 🎯 カスタム範囲対応フィルター一覧

検出されたカスタム範囲対応フィルター数: **20個**

### Analyst Recommendation (アナリスト推奨) - `an_recom`

### Market Cap (時価総額) - `cap`
#### 📊 レンジ指定例

| 範囲 | URLパラメーター | 説明 | 完全URL例 |
|---|---|---|---|
| `1to10` | `cap_1to10` | Market Cap: $1B to $10B | `https://finviz.com/screener.ashx?v=111&f=cap_1to10` |
| `10to50` | `cap_10to50` | Market Cap: $10B to $50B | `https://finviz.com/screener.ashx?v=111&f=cap_10to50` |
| `2to20` | `cap_2to20` | Market Cap: $2B to $20B | `https://finviz.com/screener.ashx?v=111&f=cap_2to20` |

- **データ型**: currency
- **単位**: USD (Billions)
- **フォーマット**: Market Cap: ${min}B to ${max}B

### Earnings Date (決算日) - `earningsdate`

### Exchange (取引所) - `exch`

### Dividend Yield (配当利回り) - `fa_div`
#### 📊 レンジ指定例

| 範囲 | URLパラメーター | 説明 | 完全URL例 |
|---|---|---|---|
| `2to5` | `fa_div_2to5` | Dividend: 2% to 5% | `https://finviz.com/screener.ashx?v=111&f=fa_div_2to5` |
| `5to10` | `fa_div_5to10` | Dividend: 5% to 10% | `https://finviz.com/screener.ashx?v=111&f=fa_div_5to10` |
| `1to3` | `fa_div_1to3` | Dividend: 1% to 3% | `https://finviz.com/screener.ashx?v=111&f=fa_div_1to3` |

- **データ型**: percentage
- **単位**: %
- **フォーマット**: Dividend: {min}% to {max}%

### Country (国) - `geo`

### Index (指数) - `idx`

### Industry (業界) - `ind`

### IPO Date (IPO日) - `ipodate`

### Sector (セクター) - `sec`

### Average Volume (平均出来高) - `sh_avgvol`
#### 📊 レンジ指定例

| 範囲 | URLパラメーター | 説明 | 完全URL例 |
|---|---|---|---|
| `100to500` | `sh_avgvol_100to500` | Volume: 100K to 500K | `https://finviz.com/screener.ashx?v=111&f=sh_avgvol_100to500` |
| `500to1000` | `sh_avgvol_500to1000` | Volume: 500K to 1000K | `https://finviz.com/screener.ashx?v=111&f=sh_avgvol_500to1000` |
| `1000to5000` | `sh_avgvol_1000to5000` | Volume: 1000K to 5000K | `https://finviz.com/screener.ashx?v=111&f=sh_avgvol_1000to5000` |

- **データ型**: volume
- **単位**: K shares
- **フォーマット**: Volume: {min}K to {max}K

### Current Volume (当日出来高) - `sh_curvol`

### Float (浮動株数) - `sh_float`

### Option/Short (オプション/ショート) - `sh_opt`

### Shares Outstanding (発行済株式数) - `sh_outstanding`

### Price (株価) - `sh_price`
#### 📊 レンジ指定例

| 範囲 | URLパラメーター | 説明 | 完全URL例 |
|---|---|---|---|
| `10to50` | `sh_price_10to50` | Price: $10 to $50 | `https://finviz.com/screener.ashx?v=111&f=sh_price_10to50` |
| `5to20` | `sh_price_5to20` | Price: $5 to $20 | `https://finviz.com/screener.ashx?v=111&f=sh_price_5to20` |
| `1to10` | `sh_price_1to10` | Price: $1 to $10 | `https://finviz.com/screener.ashx?v=111&f=sh_price_1to10` |

- **データ型**: currency
- **単位**: USD
- **フォーマット**: Price: ${min} to ${max}

### Relative Volume (相対出来高) - `sh_relvol`
#### 📊 レンジ指定例

| 範囲 | URLパラメーター | 説明 | 完全URL例 |
|---|---|---|---|
| `1to3` | `sh_relvol_1to3` | Rel Volume: 1x to 3x | `https://finviz.com/screener.ashx?v=111&f=sh_relvol_1to3` |
| `2to5` | `sh_relvol_2to5` | Rel Volume: 2x to 5x | `https://finviz.com/screener.ashx?v=111&f=sh_relvol_2to5` |
| `0.5to2` | `sh_relvol_0.5to2` | Rel Volume: 0.5x to 2x | `https://finviz.com/screener.ashx?v=111&f=sh_relvol_0.5to2` |

- **データ型**: numeric
- **単位**: multiplier
- **フォーマット**: Rel Volume: {min}x to {max}x

### Short Float (ショート比率) - `sh_short`

### Trades (取引回数) - `sh_trades`

### Target Price (目標株価) - `targetprice`

## 🔗 URLパターン構造解析

### 基本構造
```
https://finviz.com/screener.ashx?v=111&f=[filter1],[filter2],[filter3]
```

### カスタム範囲のパターン
| フィルター | パターン | 例 |
|---|---|---|
| `sh_price` | `sh_price_{min}to{max}` | `sh_price_10to50` |
| `cap` | `cap_{min}to{max}` | `cap_1to10` |
| `sh_avgvol` | `sh_avgvol_{min}to{max}` | `sh_avgvol_100to500` |
| `fa_pe` | `fa_pe_{min}to{max}` | `fa_pe_5to20` |
| `fa_div` | `fa_div_{min}to{max}` | `fa_div_2to5` |
| `sh_relvol` | `sh_relvol_{min}to{max}` | `sh_relvol_1to3` |
| `ta_perf` | `ta_perf_{min}to{max}` | `ta_perf_5to20` |
| `fa_pb` | `fa_pb_{min}to{max}` | `fa_pb_1to5` |
| `fa_ps` | `fa_ps_{min}to{max}` | `fa_ps_1to10` |
| `fa_roe` | `fa_roe_{min}to{max}` | `fa_roe_10to30` |
| `fa_roa` | `fa_roa_{min}to{max}` | `fa_roa_5to20` |
| `fa_roi` | `fa_roi_{min}to{max}` | `fa_roi_10to30` |
| `fa_curratio` | `fa_curratio_{min}to{max}` | `fa_curratio_1to5` |
| `fa_quickratio` | `fa_quickratio_{min}to{max}` | `fa_quickratio_0.5to3` |
| `fa_debteq` | `fa_debteq_{min}to{max}` | `fa_debteq_0to1` |
| `fa_ltdebteq` | `fa_ltdebteq_{min}to{max}` | `fa_ltdebteq_0to0.5` |
| `fa_grossmargin` | `fa_grossmargin_{min}to{max}` | `fa_grossmargin_20to60` |
| `fa_opermargin` | `fa_opermargin_{min}to{max}` | `fa_opermargin_5to30` |
| `fa_profitmargin` | `fa_profitmargin_{min}to{max}` | `fa_profitmargin_5to30` |
| `ta_beta` | `ta_beta_{min}to{max}` | `ta_beta_0.5to1.5` |
| `ta_volatility` | `ta_volatility_{min}to{max}` | `ta_volatility_5to15` |

## 💡 実践的な使用例

### 1. 価格範囲 $10-$50の銘柄
**URL**: `https://finviz.com/screener.ashx?v=111&f=sh_price_10to50`

**説明**: 株価が$10から$50の範囲にある銘柄

### 2. 時価総額 $1B-$10Bの中型株
**URL**: `https://finviz.com/screener.ashx?v=111&f=cap_1to10`

**説明**: 時価総額が$1Bから$10Bの中型株

### 3. PER 10-20倍の割安株
**URL**: `https://finviz.com/screener.ashx?v=111&f=fa_pe_10to20`

**説明**: PERが10倍から20倍の適正評価銘柄

### 4. 配当利回り 3-7%の高配当株
**URL**: `https://finviz.com/screener.ashx?v=111&f=fa_div_3to7`

**説明**: 配当利回りが3%から7%の高配当銘柄

### 5. 複合条件: テクノロジー × 中型株 × 適正PER
**URL**: `https://finviz.com/screener.ashx?v=111&f=sec_technology,cap_1to10,fa_pe_10to25`

**説明**: テクノロジーセクターの中型株でPER10-25倍

## 🎯 レンジ指定のベストプラクティス

### 📈 数値の指定方法
- **整数**: `10to50` (10から50)
- **小数**: `1.5to3.5` (1.5から3.5)
- **負数**: `-10to10` (-10%から+10%)

### 💰 通貨・単位の考慮
- **株価**: ドル単位 `sh_price_10to50` ($10-$50)
- **時価総額**: 10億ドル単位 `cap_1to10` ($1B-$10B)
- **出来高**: 千株単位 `sh_avgvol_100to500` (100K-500K)

### ⚠️ 注意点
- 最小値は最大値より小さく設定
- 極端な値は結果が0件になる可能性
- 一部のフィルターは特定の範囲のみ有効

