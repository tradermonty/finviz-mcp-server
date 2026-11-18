# Finviz stock/ETF export migration (#67)

The screener export uses `https://elite.finviz.com/export/screener` with
explicit `type=stocks` or `type=etf`. Quote, group, news and SEC exports are
separate endpoints and are unchanged. Credentials are supplied only in outbound
request parameters (see #68 / PR #69).

## Routing contract

- Generic `screen_stocks`, raw `custom_screener`, and named stock screeners are
  stock-only by default. Stock filters, signals and sort parameters are preserved.
  Raw custom screens that explicitly ask for the legacy ETF industry are rejected
  with an instruction to use `etf_screener`.
- `etf_screener` explicitly uses the ETF product. Finviz also includes closed-end
  funds in this product; the ETF tool excludes them before ranking and limits.
- Single- and multi-ticker fundamentals query stocks first, then the ETF product
  for unresolved symbols. Results are combined by ticker in requested order. This
  preserves a known ETF in a mixed request such as `SPY,AAPL`. Unknown symbols use
  the existing no-data behavior. A provider response containing an unrequested
  ticker is an error. Fund fundamentals may include closed-end funds even though
  they are excluded from the ETF screening tool.
- Browser links use `/screener/stocks` and contain no credentials; browser links
  and authenticated CSV requests serve distinct purposes.

## Columns and response checks

All screener requests pin `c=` instead of relying on saved custom-view settings.
Stock screens retain IDs 0..128 and fundamentals retain their prior extended
selection; ETF requests select IDs 0..149 (including product-specific AUM,
expense ratio and classification columns). Unsupported columns from the other
product are absent in the new exports. Callers must not assume stock valuation
or earnings fields exist for ETFs, or ETF flows exist for stocks.

The parser requires Ticker, Company and Price; stocks also require Sector and
Industry, and ETFs require Security Type, Assets Under Management and Net Expense
Ratio. It checks raw CSV headers before pandas can rename duplicates. Duplicate
headers/tickers, missing tickers, inconsistent row widths, malformed CSV and
wrong-product security types raise an explicit data error. Header order does not
matter. Header-only valid CSV remains a valid empty result.

AUM is returned in dollars and Net Expense Ratio in percentage points, as verified
on SPY. Both fields populate the ranking model; zero remains zero. ETF AUM and
expense thresholds apply before ranking, and expense sorting respects ascending
and descending order. Individual ETFs missing ranking values are excluded with a
warning containing the count and missing field, rather than ranked as zero.
Fundamentals can still return other available fields for those symbols.

## Pre-cutover live evidence (2026-11-16 Pacific)

Source: [FINVIZ stock/ETF split announcement](https://finviz.com/blog/stock-screener-and-etf-screener-now-separate-tools-and-more-powerful/)
and [upstream migration ticket #799](https://github.com/tradermonty/claude-trading-skills/issues/799),
which records the announced December 7, 2026 export cutover.

Compared the legacy `export.ashx` with the new export, using the configured Elite
account. No authenticated URL, key or account setting is recorded in the evidence.

- Volume-surge stock filters: 28 old and 28 new tickers; identical sets and all
  shared field values. Stock export omits ETF-only columns.
- AAPL: 1 old and 1 new ticker; identical shared values.
- SPY with the legacy ETF industry filter: 1 old and 1 new ticker; identical shared
  values. New ETF export adds Security Type and omits stock-only columns.
- Actual mixed fundamentals: `SPY,AAPL` returned in that order with positive prices.
- Actual ETF screener: top three VOO, IVV, SPY; AUM and expense populated.

The provider's ETF universe contained 6,144 securities: 5,810 Exchange Traded Funds
and 334 closed-end funds. Ten ETFs had missing ranking values. This observation
motivated the type and data-gap handling above. These counts are a snapshot, not
hardcoded expectations.

Detailed field/set differences: [live comparison JSON](finviz-export-live-comparison-2026-11-16.json).
This establishes pre-cutover compatibility; it does not establish provider
behavior after December 7. Repeat a live smoke check after that cutover.
