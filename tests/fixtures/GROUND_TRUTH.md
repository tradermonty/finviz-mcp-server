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
  (columns: Title,Source,Date,Url,Category), `v=3` per-stock headlines (adds
  `Ticker` column), `v=3&t=TICKER[,T2]` filters by ticker. **`sec=` and
  `filter=` params are IGNORED** (byte-identical responses probed). Dates are
  `YYYY-MM-DD HH:MM:SS` in **US/Eastern**.
  - `Category` is a real column with a *tiny* taxonomy (probed 2026-07-31):
    **v=1 → exactly `Market` (90 rows) and `Blog` (90 rows), 180 rows total;
    v=3 → `Stock` for 100/100 rows.** There is no earnings/analyst/insider
    taxonomy anywhere in this feed, so a "news type" filter cannot be honored;
    the only honest client-side filter is v=1 `Category` ∈ {Market, Blog}.
  - `v=3&t=AAPL,MSFT` returns **one** merged feed (100 rows) whose `Ticker`
    cells are per-row and real: `AAPL` 69, `MSFT` 27, `AAPL,MSFT` 3,
    `MSFT,AAPL` 1 — i.e. multi-name items comma-join their tickers, and the
    order is not normalized. Never overwrite this with the requested tickers.
  - No sector feed exists. To get sector news honestly: resolve constituents
    with one `export.ashx` call (`f=sec_<code>&c=1,2,6&o=-marketcap`; probe:
    `sec_technology` → 793 rows, NVDA/AAPL/MSFT/TSM… descending), slice
    client-side, then one `v=3&t=<joined>` news call. Two requests total.
    Probed end-to-end: a **40-ticker `t=`** is accepted and returns correctly
    attributed rows (incl. `INTC,MU,NVDA,AMD,SKHY,SNDK,WDC` on one item).
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
- `sh_volume_*` DOES NOT EXIST (probe-confirmed no-op). Current volume is
  `sh_curvol_*`, average volume `sh_avgvol_*`; **both count thousands of
  shares**.
- Custom perf range grammar: `ta_perf_5to-1w` = weekly performance **>= 5%**
  (probe: returned +5.02%..+29.53%). I.e. `<N>to-<tf>` means ">= N over tf".
  Consequently `ta_perf_0to-4w` = "4-week performance >= 0%" — it is NOT a
  "declined then recovering" filter.
- Sector codes for f=sec_/sg=: lowercase concatenated (`technology`,
  `basicmaterials`, `consumercyclical`, ...). There is no exclusion syntax —
  exclude client-side or enumerate included sectors.
- **One token per filter key.** Sending two tokens for the same key
  (`fa_payoutratio_o10,fa_payoutratio_u80`) does NOT intersect them: Finviz
  keeps one and drops the other silently (verified: the minimum was dropped).
  Both bounds must collapse into one range token (`fa_payoutratio_10to80`).
  `_convert_filters_to_finviz` now refuses to emit a duplicate key at all.
- Grammar per key: `_o<N>` = at least N, `_u<N>` = at most N,
  `_<A>to<B>` = range, `_<A>to` = at least A. Volume keys count thousands.
- Finviz calendars are **US/Eastern**. Any window built from "today"
  (`earningsdate_<start>x<end>`) must use the Eastern date.

### Phase 5 probe log (2026-07-31, 15 requests, ≥1s apart)

Every token below was checked by fetching the columns it claims to constrain
and confirming the returned rows honor it (an ignored token leaves violating
rows in the result). "IGNORED" = the query returned the unfiltered universe.

| Token / grammar | Verdict | Evidence |
|---|---|---|
| `sh_curvol_o<N>` | **WORKS**, N in thousands | `cap_mega,sh_curvol_o20000` → 0 rows, while cap_mega (73 rows) had max raw Volume 4,022,258 → 20000 means 20M shares, not 20K |
| `sh_curvol_<A>to<B>` | **WORKS**, thousands | `cap_mega,sh_curvol_100to200` → ARM 119,550 / PLTR 163,928 raw shares |
| `sh_avgvol_<A>to` | **WORKS**, thousands | `cap_mega,sh_avgvol_50000to` → exactly the 6 mega caps with Average Volume > 50,000 |
| `sh_avgvol_<A>to<B>` | **WORKS**, thousands | `sh_avgvol_1234to1250` → 24 rows, Average Volume 1234.08–1249.49 |
| arbitrary (non-preset) numeric values | **WORKS** | `o20000`, `1234to1250`, `50000to` are not UI presets and were all honored → no need to floor to buckets |
| `fa_pe_u<N>` | **WORKS** | `fa_pe_u10,fa_pb_u2,fa_roe_o15` → 159 rows, P/E max 9.96 |
| `fa_pb_u<N>` | **WORKS** | same probe, P/B max 1.98 |
| `fa_roe_o<N>` | **WORKS** | same probe, ROE min 15.3% |
| `fa_debteq_u<N>` (decimals ok) | **WORKS** | `cap_midover,fa_debteq_u0.5,...` → Total Debt/Equity max 0.50 |
| `fa_payoutratio_o<N>` | **WORKS** | same probe → Payout Ratio min 71.48% (`_u` is the same key with the verified `u` grammar) |
| `fa_divgrowth1_o5` | **IGNORED** | same probe kept rows with Dividend Growth 1 Year of −58.97% → no dividend-growth filter exists |
| `fa_epsyoy_pos` | **WORKS** | `cap_largeover,geo_usa,fa_*_pos` → 283 rows, EPS Growth This Year min +0.27% |
| `fa_epsqoq_pos` | **WORKS** | same probe, EPS Q/Q min +0.81% |
| `fa_salesqoq_pos` | **WORKS** | same probe, Sales Q/Q min +0.31% |
| `fa_eps5years_pos` | **WORKS** | same probe, EPS past 5Y min +0.09% |
| `fa_sales5years_pos` | **WORKS** | same probe, Sales past 5Y min +0.03% |
| `geo_usa` | **WORKS** | same probe: Country == USA for all 283 rows |
| `ind_exchangetradedfund` | **WORKS** | 5,580 rows, every one with an ETF `Asset Type` (universe is 11,532) |
| `etf_netexpense_u0.2` | **IGNORED** | same probe returned Net Expense Ratio 0.50/0.75/0.95% |
| `etf_aum_o10000` | **IGNORED** | same probe returned AUM as low as $81,491 |
| `ind_stocksonly` | **WORKS** | 1,607 rows, `Asset Type` empty on every one (no ETFs) |
| `ta_sma20_pb` / `ta_sma50_pb` / `ta_sma200_pb` | **WORK** | `cap_mega` + all three → 10 rows, all three SMA distance columns negative |
| `earningsdate_<MM-DD-YYYY>x<MM-DD-YYYY>` | **WORKS** | `08-03-2026x08-14-2026` → 1,607 rows, dates 8/3 08:30 … 8/14 16:30 |
| `earningsdate_nextmonth` | **IGNORED** (does not exist) | 11,532 rows = full universe |
| `earningsdate_nextdays10` | **IGNORED** (does not exist) | 11,532 rows, byte-identical to the above |
| `o=earningsdate` | **WORKS**, real date order | cap_mega → 5/2, 5/2, 5/13 … 8/20 (a lexicographic sort would put 5/13 before 5/2) |
| `o=-perf1w` | **WORKS** | cap_mega → +17.55% … −11.41%, monotonically descending |

Because `ar` is ignored, `o=` is only an optimization: every screener still
sorts client-side on parsed values **before** applying `max_results`.

## Fixture inventory

- `screener_v151_dji.csv` — export.ashx v=151 c=0..128, f=idx_dji (~30 DJIA rows),
  exactly what `screen_stocks` requests today.
- `groups_sector.csv`, `groups_industry.csv`, `groups_country.csv`,
  `groups_capitalization.csv`, `groups_industry_energy.csv` (sg=energy) —
  v=152 with NO c= (account default = 9-column overview; kept as a regression
  fixture for the "unstable custom view" failure mode).
- `groups_sector_allcols.csv` — v=152 c=0..29 (the verified 29-column map above).
- `groups_industry_energy_cols.csv` (g=industry&sg=energy), `groups_country_cols.csv`,
  `groups_capitalization_cols.csv` — captured 2026-07-31 with the explicit column
  list the client now sends (`c=0,1,2,3,4,10,15,16,17,18,19,20,21,22,23,24,25,26`);
  confirms a `c=` subset is honored and that `Name` is the label column for every `g=`.
  Cross-check probe (g=industry&sg=energy vs `f=ind_oilgasdrilling` stock export):
  group `Volume` equals the sum of member stocks' raw `Volume`, and group
  `Average Volume` the sum of their thousands-unit `Average Volume` — i.e. the
  units above hold for groups too.
- `groups_sector_v140_performance.csv` — fixed performance view.
- `news_v1_market.csv`, `news_v3_stocks.csv`, `news_v3_aapl.csv`.
- `news_v3_aapl_msft.csv` — captured 2026-07-31, `v=3&t=AAPL,MSFT` (100 rows).
  Pins real per-row `Ticker` attribution incl. the comma-joined multi-name
  rows. (Written back through pandas, so quoting is normalized vs the raw
  body; field values are unchanged.)
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
