# Verified Finviz ground truth (captured live 2026-07-31)

Everything below was verified against the live Elite API with this repo's key.
Fixtures in this directory are raw captures. **Trust this file over any comment
or mapping in the code** — stale hardcoded mappings are the #1 bug class here.

## Endpoints

- Stock screener/export: `https://elite.finviz.com/export.ashx` — params `v`, `f`
  (comma-joined filter tokens), `c` (comma-joined column ids), `ft=4`, `auth`.
  **The `ar` param is IGNORED by this endpoint** (probe: ar=10 returned 39+ rows) —
  result limiting must happen client-side, AFTER sorting (use `o=` for server-side
  sort: e.g. `o=-perf1w`, `o=-epsqoq`, `o=ticker`).
- Groups: `https://elite.finviz.com/grp_export.ashx` — `g` in
  {sector, industry, country, capitalization}, optional `sg=<sector_code>` with
  g=industry. **`v=152` without `c=` returns the account's saved custom layout —
  NOT stable** (two probes on different sessions returned different column sets).
  Always pass `v=152&c=<explicit ids>`. Fixed views also exist (v=110 overview,
  v=140 performance — see groups_sector_v140_performance.csv).
- News: `https://elite.finviz.com/news_export.ashx` — `v=1` market/general news
  (columns: Title,Source,Date,Url,Category; Category values like "Market"),
  `v=3` per-stock headlines (adds `Ticker` column), `v=3&t=TICKER[,T2]` filters
  by ticker. **`sec=` and `filter=` params are IGNORED** (byte-identical
  responses probed). Dates are `YYYY-MM-DD HH:MM:SS` in **US/Eastern**.
- SEC filings: `https://elite.finviz.com/export/latest-filings` — `t=TICKER`,
  `o=-filingDate` (camelCase). Columns: `Filing Date,Report Date,Form,
  Description,Filing,Document`. Dates are `M/D/YYYY` (e.g. `7/30/2026`).
  Form values are bare (`4`, `8-K`, `10-K`, `SC 13G/A`...). AAPL export ≈ 1,060
  rows in one response.
- Fundamentals (already fixed on this branch): `export.ashx?v=152&t=TICKER&c=...`.

## Stock export column ids (v=151 and v=152 share these; verified id -> header)

0 No. | 1 Ticker | 2 Company | 3 Sector | 4 Industry | 5 Country | 6 Market Cap
7 P/E | 8 Forward P/E | 9 PEG | 10 P/S | 11 P/B | 12 P/Cash | 13 P/Free Cash Flow
14 Dividend Yield | 15 Payout Ratio | 16 EPS (ttm) | 17 EPS Growth This Year
18 EPS Growth Next Year | 19 EPS Growth Past 5 Years | 20 EPS Growth Next 5 Years
21 Sales Growth Past 5 Years | 22 EPS Growth Quarter Over Quarter
23 Sales Growth Quarter Over Quarter | 24 Shares Outstanding | 25 Shares Float
26 Insider Ownership | 27 Insider Transactions | 28 Institutional Ownership
29 Institutional Transactions | 30 Short Float | 31 Short Ratio
32 Return on Assets | 33 Return on Equity | 34 Return on Invested Capital
35 Current Ratio | 36 Quick Ratio | 37 LT Debt/Equity | 38 Total Debt/Equity
39 Gross Margin | 40 Operating Margin | 41 Profit Margin | 42 Performance (Week)
43 Performance (Month) | 44 Performance (Quarter) | 45 Performance (Half Year)
46 Performance (Year) | 47 Performance (YTD) | 48 Beta | 49 Average True Range
50 Volatility (Week) | 51 Volatility (Month) | 52 20-Day Simple Moving Average
53 50-Day Simple Moving Average | 54 200-Day Simple Moving Average | 55 50-Day High
56 50-Day Low | 57 52-Week High | 58 52-Week Low | 59 Relative Strength Index (14)
60 Change from Open | 61 Gap | 62 Analyst Recom | 63 Average Volume
64 Relative Volume | 65 Price | 66 Change | 67 Volume | 68 Earnings Date
69 Target Price | 70 IPO Date | 71 After-Hours Close | 72 After-Hours Change
73 Book/sh | 74 Cash/sh | 75 Dividend | 76 Employees | 77 EPS Next Q | 78 Income
79 Index | 80 Optionable | 81 Prev Close | 82 Sales | 83 Shortable
84 Short Interest | 85 Float % | 86 Open | 87 High | 88 Low | 89 Trades
90-99 Performance (1 Minute .. 4 Hours) | 100 Asset Type | 101 ETF Type
102 Region | 103 Single Category | 104 Sector/Theme | 105 Tags
106 Active/Passive | 107 Net Expense Ratio | 108 Total Holdings
109 Assets Under Management | 110 Net Asset Value | 111 Net Asset Value %
112-119 Net Flows (1M/%/3M/%/YTD/%/1Y/%) | 120 Return 1 Year | 121 Return 3 Year
122 Return 5 Year | 123 Return 10 Year | 124 Return Since Inception
125 All-Time High | 126 All-Time Low | 127 EPS Surprise | 128 Revenue Surprise
129 Exchange | 130 Dividend TTM | 131 Dividend Ex Date | 132 EPS Year Over Year TTM
133 Sales Year Over Year TTM | 134 52-Week Range | 135 News Time | 136 News URL
137 News Title | 138 Performance (3 Years) | 139 Performance (5 Years)
140 Performance (10 Years) | 141 After-Hours Volume | 142 EPS Growth Past 3 Years
143 Sales Growth Past 3 Years | 144 Enterprise Value | 145 EV/EBITDA | 146 EV/Sales
147 Dividend Growth 1 Year | 148 Dividend Growth 3 Years | 149 Dividend Growth 5 Years

Headers that DO NOT exist in any stock export: "EPS Q/Q", "Sales Q/Q", "Recom",
"Category", "Earnings Time", "Volatility" (bare), "EPS growth this Y" (case
matters), "EPS Estimate", "EPS Actual", "Revenue Estimate/Actual/Revision".

## Groups export column ids (g=sector, v=152&c=..., verified 2026-07-31)

0 No. | 1 Name | 2 Market Cap | 3 P/E | 4 Forward P/E | 5 PEG | 6 P/S | 7 P/B
8 P/C | 9 P/Free Cash Flow | 10 Dividend Yield | 11 EPS growth past 5 years
12 EPS growth next 5 years | 13 Sales growth past 5 years | 14 Float Short
15 Performance (Week) | 16 Performance (Month) | 17 Performance (Quarter)
18 Performance (Half Year) | 19 Performance (Year) | 20 Performance (Year To Date)
21 Analyst Recom | 22 Average Volume | 23 Relative Volume | 24 Change | 25 Volume
26 Stocks | 27 LT Debt/Equity | 28 Total Debt/Equity

The group-name column is **`Name`** for every g= (sector/industry/country/cap) —
never "Industry"/"Country"/"Sector". 1-day change is `Change`. There are no
"1D %"/"1W %" style headers. YTD is "Performance (Year To Date)" (differs from
the stock export's "Performance (YTD)").

## Units (verified)

- Stock export: `Market Cap`, `Income`, `Sales`, `Enterprise Value`,
  `Shares Outstanding/Float`, `Short Interest` in **millions**; `Average Volume`
  in **thousands of shares**; `Volume`, `Trades`, `After-Hours Volume` raw.
  (StockData parser now normalizes avg_volume to shares — keep it that way.)
- Groups export: `Market Cap` in **millions of dollars**; `Average Volume` in
  **thousands**; `Volume` raw. Percent columns come with trailing `%`.
- ETF: `Assets Under Management`, `Net Flows *` in **raw dollars**.
- SMA / 50-Day / 52-Week / All-Time High/Low columns are **percent distance
  from current price**, never absolute prices.

## Filter-token grammar (probed)

- `f=` tokens unknown to Finviz are **silently ignored** (probed: row counts
  identical) — never assume a token works because the query succeeded.
- `sh_volume_*` DOES NOT EXIST (probe-confirmed no-op). Current-volume token to
  use/verify is `sh_curvol_*`; avg volume is `sh_avgvol_*` (thousands units:
  `o500` = 500K shares). Custom ranges: `frange` style `X to Y` tokens like
  `sh_avgvol_franges? ` — VERIFY with a probe before relying (Phase 5).
- Custom perf range grammar: `ta_perf_5to-1w` = weekly performance **>= 5%**
  (probe: returned +5.02%..+29.53%). I.e. `<N>to-<tf>` means ">= N over tf".
- SMA below-price tokens: `ta_sma20_pb`, `ta_sma50_pb`, `ta_sma200_pb`
  (pa = price above) — standard Finviz, verify with one probe in Phase 5.
- Sector codes for f=sec_/sg=: lowercase concatenated (`technology`,
  `basicmaterials`, `consumercyclical`, ...). There is no exclusion syntax —
  exclude client-side or enumerate included sectors.

## Fixture inventory

- `screener_v151_dji.csv` — export.ashx v=151 c=0..128, f=idx_dji (~30 DJIA rows),
  exactly what `screen_stocks` requests today.
- `groups_sector.csv`, `groups_industry.csv`, `groups_country.csv`,
  `groups_capitalization.csv`, `groups_industry_energy.csv` (sg=energy) —
  v=152 with NO c= (account default = 9-column overview; kept as a regression
  fixture for the "unstable custom view" failure mode).
- `groups_sector_allcols.csv` — v=152 c=0..29 (the verified 29-column map above).
- `groups_sector_v140_performance.csv` — fixed performance view.
- `news_v1_market.csv`, `news_v3_stocks.csv`, `news_v3_aapl.csv`.
- `sec_latest_filings_aapl.csv` — 1,060 rows, all forms, M/D/YYYY dates.
- `MRVL_raw.json`, `SPMO_raw.json` — parsed fundamentals dicts (stock/ETF),
  used by the already-fixed fundamentals tests.

## House rules for fixes (apply to every phase)

1. Never trust an existing mapping/comment — check this file or probe.
2. A parameter that can't be honored honestly gets removed/renamed, not faked.
3. Failures must be reported as failures — never `[]`-as-"no results".
4. `0`/`0.0` are legitimate values: use `is not None`, never truthiness.
5. Every fix lands with an offline fixture-pinned test.
6. Live probes: max a handful per phase, ≥1s apart.
