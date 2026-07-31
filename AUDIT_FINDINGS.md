# Full-server audit — 2026-07-31

## Resolution status (2026-07-31)

Seven repair phases landed on this branch:

| Phase | Commit | Scope |
|---|---|---|
| 1 | `480d1e4` | Shared `StockData` CSV parser — 24 dead column mappings, zero-drop (A) |
| 2 | `dcd0539` | Always-empty paths: groups parsers, moving average, news `Url` (D2-D4, D1, C1) |
| 3 | `d5b7b6a` | Error policy — real exceptions instead of "no results"; API key out of output (B9, C5, E2, B25) |
| 4 | `a95e444` | News tools — real feeds, real attribution, ET dates (C2-C4, C6-C10) |
| 5 | `7702fe7` | Screener filters wired/removed; sort before truncate; honest criteria blocks (B1-B8, B10-B24, B26-B28, D5-D14) |
| 6 | `93df60c` | SEC/EDGAR — dates, filters, content conversion, units, tickers (E1-E16) |
| 7 | *(pending)* | Field discovery + docs (F1-F5) |

**Every HIGH finding is resolved**, verified against the current code (not against
commit messages). The honest exceptions are below. Three new findings (**F3-F5**)
were discovered during the phase-7 sweep and its review, and fixed in the same phase.

### Fixed by a different approach than the finding suggested

- **A4** — `performance_2y` mapping *deleted* rather than remapped (no 2-year column
  exists; the attribute is now permanently `None`). `performance_3y/5y/10y` added.
- **B2** — `min_dividend_growth` / `dividend_growth_min` **removed** from the API, not
  wired: Finviz has no dividend-growth filter token. Everything else in B2 was wired.
- **B3** — ETF `min_aum` / `max_expense_ratio` / `asset_class` applied **client-side**
  on fetched rows; the ETF universe is still downloaded whole.
- **B13** — `premarket_price_change` / `afterhours_price_change` removed from the
  signature (no Finviz filter exists for them).
- **B17** — `pre_earnings_analysis` / `risk_assessment` / `data_fields` removed from
  `upcoming_earnings_screener` rather than implemented.
- **B27** — `_format_earnings_trading_list` was **wired in** (called by
  `earnings_trading_screener`), not deleted — the opposite of what the LOW finding
  implied, but it is the better output.
- **C3** — `news_type` removed from the client and the tool signature; Finviz ignores
  `filter=` and the v=3 `Category` is always `Stock`, so no honest filter axis exists.
- **E17** — still fixed `time.sleep`, now centralized in `_sec_get()` with the SEC
  rate guidance in one constant. No token bucket.

### Knowingly NOT fixed

- **D15** — `FinvizScreener.get_relative_volume_stocks` (screener.py:392) and
  `_build_relative_volume_filters` (latent `KeyError` at screener.py:1294) are still
  present and still dead: the MCP tool calls `screen_stocks()` directly. Only the
  count-reporting half of the finding was fixed. Unreachable, so no user impact.
- **B11 (partial)** — `earnings_timing` is still hardcoded `"unknown"`
  (screener.py:1196) and printed as such. No CSV column carries it; the honest options
  are to keep the placeholder or drop the line. Volatility and analyst_recommendation
  are genuinely fixed.
- **B21 (partial)** — three residual zero-truthiness sites in `server.py`:
  `if stock.pe_ratio:` (2800) and the `or`-chained
  `if stock.eps_qoq_growth or stock.eps_growth_qtr:` / sales pair (2789, 2792). A
  legitimate 0 still renders as absent there.

### Phase 8 — live verification sweep (2026-07-31)

One live call per repaired tool, judged against its original finding:
29 PASS, 5 PARTIAL, 1 FAIL. The failures/partials became six fixes, all
landed with regression tests in `tests/test_phase8_verification_fixes.py`:

- **G1 (HIGH)** `get_edgar_company_concept` was dead on every call: the code
  passed `concept=` where sec-edgar-api's parameter is `tag=`. The offline
  tests mocked the client, so only the live sweep could catch it. Fixed;
  pinned with a real-signature stub plus a test that diffs the stub against
  the installed library's signature.
- **G2 (MED)** `technical_analysis_screener` printed derived *dollar* SMAs
  with a percent sign (`SMA 200: +56.09%`) — same class as D1. SMA lines now
  label both units (`$97.28 (+2.80% vs price)`); the Phase 5 test that had
  pinned the mislabeled rendering (its synthetic data put percentages in the
  dollar attribute) was corrected.
- **G3 (LOW/MED)** three additional zero-truthiness sites in the earnings
  premarket/afterhours/trading top-5 detail blocks (beyond the B21 residual
  list): a real 0.0 change rendered `Change: N/A`. Fixed to `is not None`.
- **G4 (LOW)** mojibake in all CSV-derived text: Finviz sends no charset
  header, so requests decoded UTF-8 as ISO-8859-1 (`â€™`). Responses now
  decode as UTF-8.
- **G5 (LOW)** `trend_reversion_screener` printed no criteria block while
  every sibling does; it now derives one from its real filter dict.
- **G6 (env)** the live e2e `sma_50 > sma_200` invariant failed on a
  2-decimal rounding tie (TAK 16.28/16.28); the invariant now tolerates
  equality at 2 dp since Finviz applies the strict filter server-side.

Still open after the sweep (cosmetic): unlabeled $M market-cap values in
three screener row formats; `Volume: ...0` trailing decimal in
get_relative_volume_stocks; `Timing: unknown` placeholder (B11);
the trading criteria echoing `0_to_negative_4w` raw parameter spelling.

### Documentation

`CLAUDE.md`, `README.md` and `docs/tools_reference.md` were re-walked against the
current tool signatures in phase 7. `README_ja.md` still advertises 128 columns
(actual: 150) and was **not** updated.

---

Scope: all MCP tools except `get_stock_fundamentals` / `get_multiple_stocks_fundamentals`
(fixed on this branch, commits 9624684 / 865a369) and the field-discovery internals fixed
with them. Method: four parallel end-to-end code audits (screeners, news, market/sector,
SEC/EDGAR) plus a direct audit of the shared `StockData` CSV parser and field-discovery
tools. All HIGH findings are **confirmed** — by live API probes where behavior was in
question, otherwise by code-path proof. Verified live-CSV header list and probe evidence
are cited inline by the audits; line numbers refer to this branch.

## Verdict by tool

| Tool | Verdict |
|---|---|
| get_industry_performance | **Broken — always returns empty** |
| get_country_performance | **Broken — always returns empty** |
| get_sector_specific_industry_performance | **Broken — always returns empty** |
| get_moving_average_position | **Broken — wrong numbers on every call** |
| get_sector_news | **Broken — returns general news labeled as sector news** |
| get_market_news | Wrong feed (per-stock headlines, not market news) |
| get_stock_news | Works, but URLs always empty; news_type filter is a no-op |
| get_sector_performance | Works, but ignores its `sectors` parameter |
| etf_screener | Filters do nothing; downloads whole universe |
| dividend_growth_screener | ~10 advertised criteria never applied; prints false criteria block; corrupts stdio |
| trend_reversion_screener | 3 of 6 filters do nothing; growth fields always N/A |
| technical_analysis_screener | "below SMA" options and min_volume silently dropped |
| earnings_screener | min_volume no-op; prints another tool's criteria; volatility always N/A |
| earnings_winners_screener | Sort is a no-op + truncation bias ⇒ arbitrary 50 tickers |
| upcoming_earnings_screener | min_avg_volume ignored; date sort lexicographic; period labels wrong |
| earnings_premarket/afterhours_screener | Work, but printed criteria mislabel actual filters |
| earnings_trading_screener | Works-ish; 4W filter described backwards; rich formatter dead code |
| volume_surge_screener / uptrend_screener / custom_screener | Mostly work (shared zero/N-A and error-masking issues apply) |
| get_relative_volume_stocks | Works; count message lies after truncation |
| get_capitalization_performance | Works; unlabeled $M; dividend_yield fetched, never shown |
| get_market_overview | Works; avg stats biased; "+-" sign bug |
| SEC filings tools (4) | `days_back` is a no-op (dates never parse); errors ⇒ "no filings" |
| EDGAR tools (5) | Form filters applied after 50-row cap; raw XBRL HTML as "content"; USD applied to share counts |
| Field discovery (5) | `validate_fields` disagrees with real validator; suggests nonexistent field |

## Recurring root-cause classes

1. **Mapping drift (the fundamentals bug, everywhere else).** The `StockData` parser maps
   24 fields to CSV headers that don't exist (`"EPS Q/Q"`, `"EPS growth this Y"`, `"Recom"`,
   `"Category"`, `"Earnings Time"`, `"Volatility"`, estimate/actual/revision columns) —
   those attributes are **always None**, nulling screener output columns and making
   sorts no-ops. Same drift broke the groups parsers (`Industry`/`Country` vs actual
   `Name` header; `"1D %"`-style headers vs actual `Performance (Week)`), the news CSV
   (`URL` vs `Url`), and SEC date parsing (`%m/%d/%y` vs actual `M/D/YYYY`).
2. **Advertised-but-unwired parameters.** Filter keys set by screener builders that
   `_convert_filters_to_finviz` never reads (dividend_growth ~10 keys, etf_screener all
   keys, trend_reversion 3 keys, sma*_below, min_volume via nonexistent `sh_volume`
   token, upcoming_earnings min_avg_volume key mismatch, news news_type/sector params,
   earnings premarket/afterhours price-change params). Tools claim filters they never ran.
3. **Errors swallowed into "no results".** Every client returns `[]`/empty DataFrame on
   any exception (bad API key, HTML response, network failure) — server tools then say
   "No stocks/news/filings found", indistinguishable from a true empty result. Several
   server-side `except` fallbacks are unreachable dead code.
4. **Truncation/ordering lies.** `max_results` head() applied to reverse-ticker order
   *before* client-side sorting (earnings_winners, upcoming_earnings, technical_analysis)
   ⇒ "top N by X" is actually "N tickers nearest Z re-sorted". Counts reported after
   truncation ("Found 5 stocks", SEC summary "Total Filings: 100"). Earnings-date sort is
   lexicographic on date strings.
5. **Unit and typing inconsistencies.** Groups market-cap in unlabeled $M vs raw dollars
   elsewhere; EDGAR concept values always formatted as USD (even `shares`/`pure` units);
   SMA percent-distance interpreted as an absolute dollar price (moving-average tool);
   `_convert_volume_to_finviz_format` silently floors thresholds to preset buckets.
6. **Zero-truthiness.** `if stock.price_change:` style checks and parser-level
   `float(value) if value != 0 else None` render legitimate zeros as N/A across
   nearly every screener formatter.
7. **Fabricated/mislabeled output.** Sector news labels general headlines as sector
   news; keyword-guessed "Category" presented as data; earnings_screener prints another
   tool's criteria block; premarket/afterhours print wrong price/cap criteria;
   upcoming_earnings claims the CSV lacks earnings dates while displaying them;
   `performance_2y` silently contains 1-year data; base.py `get_market_overview`
   returns a hardcoded dict (dead code, but API-shaped).

## Complete findings

### A. Shared StockData parser (`src/finviz_client/base.py`) — affects all screeners
- **HIGH** base.py:1480-1496,1560,1636,1638 — 24 dead column mappings (headers that don't
  exist in the export). Always-None fields include `eps_growth_qtr`, `sales_growth_qtr`,
  `eps_qoq_growth`, `sales_qoq_growth`, `eps_next_q` (also semantically wrong header),
  `analyst_recommendation`, `earnings_timing`, `single_category`, `volatility`,
  `eps_growth_this_y/next_y/past_5y/next_5y` (case drift), estimate/actual/revision.
- **HIGH** screener.py:234-235 — earnings_winners default sort keys on always-None
  `eps_growth_qtr` ⇒ silent no-op.
- **MED** base.py:1622 — `float(value) if value != 0 else None`: true zeros become None.
- **MED** base.py:1527 — `performance_2y` mapped to `"Performance (Year)"` ⇒ holds
  1-year data under a 2-year name.

### B. Screener tools (13) — agent-confirmed
1. **HIGH** base.py:794-828 — `volume_min/max` emit nonexistent `sh_volume_*` token
   (real: `sh_curvol_*`); probe: identical row counts with/without. Also raw shares
   passed where Finviz expects thousands. Affects earnings_screener,
   technical_analysis_screener `min_volume`.
2. **HIGH** screener.py:477-521 — dividend_growth_screener: `pe_ratio_max`,
   `pb_ratio_max`, growth-positive flags, `country`, `payout_ratio_*`, `roe_min`,
   `debt_equity_max`, `dividend_growth_min` have no converter handlers; effective query
   is `cap_midover,fa_div_2to`. Printed "Default Criteria" block (server.py:739-753) is
   false; `sma200` sort not in sort_mapping ⇒ order is `-ticker`.
3. **HIGH** screener.py:524-538 — etf_screener: zero filters applied; whole universe
   downloaded; `min_aum`/`max_expense_ratio` ignored; `sort_by="expense_ratio"` no-op
   (field never populated).
4. **HIGH** server.py:2291-2297 vs screener.py:916 — upcoming_earnings `min_avg_volume`
   stored under keys the builder never reads; default 500K always applies.
5. **HIGH** screener.py:1021-1038 — trend_reversion: default `market_cap="mid_large"`
   emits invalid `cap_mid_large`; `revenue_growth_qoq` and `exclude_sectors` unhandled.
6. **HIGH** server.py:1995-2004 — `sma20/50/200_below` filter keys never read; "below"
   queries return the unfiltered universe under a "Price below SMA" header.
7. **HIGH** base.py:1392-1396 + screener builders — `max_results` head() applied to
   reverse-ticker server order before client-side sort (earnings_winners,
   upcoming_earnings, technical_analysis, dividend_growth `[:100]`): deterministic
   truncation bias. `ar=` param confirmed ignored by export endpoint.
8. **HIGH** server.py:731-733 — bare `print("CLAUDE_DEBUG_MARKER...")` to stdout inside
   dividend_growth_screener: corrupts the MCP stdio channel on every call.
9. **HIGH** base.py:325-327,1414-1416; screener.py:741-743,801-803 — all exceptions
   swallowed to `[]` ⇒ every failure reads as "No stocks found". Server fallbacks at
   server.py:2197-2213, 2345-2362 unreachable.
10. **MED** — consumers of dead QoQ mappings: trend_reversion growth lines always N/A
    (server.py:546-554); earnings_winners QoQ metrics never print (server.py:2517-2524),
    `sort_by="eps_growth_qoq"` no-op.
11. **MED** — phantom headers: volatility (earnings tools' Volatility columns always
    N/A; upcoming_earnings `sort_by="volatility"` no-op), analyst_recommendation,
    earnings_timing always "unknown".
12. **MED** server.py:142-153 — earnings_screener prints earnings_trading's criteria
    block (EPS revision, 200K vol, $10, 4W recovery) — none applied.
13. **MED** server.py:84-85 — `premarket_price_change`/`afterhours_price_change`
    accepted, never read by `_build_earnings_filters`.
14. **MED** server.py:2791-2793, 2953-2955 — premarket/afterhours print "Min Price:
    $10"/"Small+" while actual filters are $30/`largeover`.
15. **MED** server.py:2334-2337 — `next_2_weeks`→`nextdays5` (5 business days);
    `next_month`→`thismonth` (current month). Period labels wrong.
16. **MED** screener.py:1003-1004 — earnings-date sort lexicographic on "M/DD/YYYY"
    strings; default calendar ordering wrong across month boundaries.
17. **MED** server.py:2314-2322 — upcoming_earnings `pre_earnings_analysis`,
    `risk_assessment`, `data_fields` accepted and discarded.
18. **MED** server.py:2143 vs screener.py:778-795 — advertised `sort_by='eps_surprise'`
    not implemented ⇒ reverse-ticker order.
19. **MED** screener.py:619 — `ta_perf_0to-4w` means "4W perf ≥ 0%" (probe-verified
    grammar) but is described as decline-recovery; description inverted.
20. **MED** base.py:136-159 — numeric volume thresholds floored to preset buckets
    (650000→o500, 120000→o100, <50K→o0): filters silently loosened.
21. **MED** — zero-truthiness in every formatter (`if stock.price_change` etc.) plus
    parser zero-drop: legitimate 0 renders as N/A.
22. **MED** models.py:433-442 — `MARKET_CAP_FILTERS` missing `largeover`/`microover`;
    earnings_winners/upcoming_earnings silently drop `market_cap="largeover"`.
23. **MED** validators.py:157-196 vs base.py:1273-1286 — sector validation and sector-
    code mapping disagree both directions ("Financial Services" rejected; accepted
    values like "technology" then silently dropped — no `sec_` token).
24. **LOW** server.py:2377-2380 — false note "CSV export does not include earnings date".
25. **LOW** server.py:2586 — "verification" URL doesn't reproduce the query and embeds
    the API key in tool output.
26. **LOW** server.py:2449-2465 — hardcoded "+" ⇒ "+-3.2%" for negatives.
27. **LOW** server.py:3092-3267 — `_format_earnings_trading_list` dead code.
28. **LOW** server.py:2012-2013 — technical_analysis with sparse filters downloads the
    universe and slices [:50] of reverse-alphabetical order.

### C. News tools (3) — agent-confirmed with live probes
1. **HIGH** news.py:355 — reads `row.get("URL")`, column is `"Url"` ⇒ every article URL
   rendered empty in all three tools.
2. **HIGH** news.py:154-157 — `sec=<sector>` not a real endpoint param (byte-identical
   responses) ⇒ get_sector_news returns general headlines labeled as sector news.
3. **HIGH** news.py:49-57 — `filter=insider` etc. ignored by Finviz (byte-identical)
   ⇒ `news_type` is a no-op presented as a filter.
4. **MED/HIGH** news.py:108,111 — market news uses `v=3` (per-stock feed) instead of
   `v=1` (real market news).
5. **MED** news.py:90-92,135-137,186-188 — all errors ⇒ [] ⇒ "No news found".
6. **MED** news.py:68,119,168,361 — CSV timestamps are US/Eastern compared against
   naive local `datetime.now()` ⇒ days_back window shifted; "future" dates shown.
7. **MED** news.py:72-77 + server.py:1099-1210 — real per-item `Ticker` column
   discarded/overwritten and never rendered ⇒ multi-ticker news unattributable.
8. **LOW/MED** news.py:365 — real `Category` column ignored; keyword-guessed category
   rendered as data.
9. **LOW** news.py:190-292 — dead HTML-era parsers (with latent now()-default bug);
   stray `pass` at :350.
10. **LOW** news.py:353-355 — NaN cells render as literal "nan".

### D. Market & performance tools (8) — agent-confirmed with live probes
1. **HIGH** server.py:4149-4165 — get_moving_average_position: percent branch dead
   (values already floats), so percent-distance treated as absolute SMA dollars.
   Live: "20-Day SMA: $2.80 → +11808.21% above". Every response wrong.
2. **HIGH** sector_analysis.py:351 — industry parser reads `Industry`; header is
   `Name` ⇒ get_industry_performance always empty.
3. **HIGH** sector_analysis.py:385 — same for `Country` ⇒ always empty.
4. **HIGH** sector_analysis.py:240 — sector-specific industries reuse broken parser ⇒
   always empty.
5. **HIGH** server.py:1223 — `get_sector_performance(sectors)` passes the list into the
   client's `timeframe` positional; `sectors` filter never applied.
6. **MED** sector_analysis.py:357-362,391-396 — `"1D %"`-style headers don't exist
   (actual `Performance (Week)` etc.); after fixing 2-4, every perf value would be a
   silent 0.0.
7. **MED** server.py:1288-1295,1331-1338,1398-1405 — formatter/parser key mismatch:
   formatters read keys parsers never emit and vice-versa (invisible fields).
8. **MED** server.py:1243,1445,1661 — market cap rendered in unlabeled $M (groups) vs
   raw dollars elsewhere.
9. **MED** base.py:2184-2226 — `FinvizClient.get_market_overview` returns hardcoded
   synthesized data (currently dead code).
10. **MED** server.py:1894,1949 — "Found {len(results)} stocks" after truncation.
11. **LOW** server.py:4183 — dead percent branch renders exactly-0.00% as "below"
    (contradicts 5be5d8c convention); phrasing inverts referent.
12. **LOW** server.py:1520-1533,1821 — averages divide by full count over non-null
    sums; hardcoded "+" ⇒ "+-1.5%".
13. **LOW** sector_analysis.py:449 — capitalization `dividend_yield` parsed, never shown.
14. **LOW** sector_analysis.py:33 — `v=152` custom view without `c=` list: column set
    depends on account defaults (fragile).
15. **LOW** screener.py:275-295,1046 — dead `get_relative_volume_stocks` with latent
    KeyError.

### E. SEC & EDGAR tools (9) — agent-confirmed with live probe + package inspection
1. **HIGH** sec_filings.py:244-254 — `_parse_date` formats don't match actual
   `M/D/YYYY`; every date falls back to `datetime.now()` ⇒ `days_back` no-op in 4
   tools; summary aggregates the full export (1,060 rows for AAPL) as "Last N days".
2. **HIGH** sec_filings.py:95-97 — blanket except swallows even its own "API key
   required" ValueError ⇒ all failures read "No SEC filings found".
3. **HIGH** edgar_client.py:117-127 — `max_count` cap applied before form/date filters
   (and the SDK downloads the entire paginated history first) ⇒
   `form_types=["10-K"]` returns ~nothing, reported as "No EDGAR filings found".
4. **HIGH** edgar_client.py:207 — no HTML→text conversion: 10-K "content" is markup;
   first 50K chars ≈ head/CSS/XBRL tags.
5. **HIGH** edgar_client.py:43-65 — ~1MB `company_tickers.json` re-downloaded per call
   (10x for a 10-filing batch), uncached, not rate-limited.
6. **MED** server.py:3714-3729 — batch tool fetches 20,000 chars/doc, renders 500.
7. **MED** sec_filings.py:135,158 — exact-match form lists: amendments (10-K/A, 13D/A…)
   excluded; 11-K misclassified as insider; Form 144 missing.
8. **MED** sec_filings.py:44 — only `filing_date` converted to camelCase; other
   sort_by values sent invalid.
9. **MED** sec_filings.py:271,290-297 — summary "Total Filings" capped at 100 but
   presented as period total; percentages wrong.
10. **MED** server.py:4026-4034 — concept values always formatted USD (shares/pure
    get $ and B/M/K); negatives render "$-3,200,000,000.00".
11. **MED** server.py:4013-4040 — quarterly vs annual duration values
    indistinguishable (start never rendered, no frame dedup).
12. **MED** edgar_client.py:210-221 + server.py:3618-3631 — truncation double-applied;
    reported "Content Length" is the clipped size; marker chopped.
13. **MED** validators.py:21 — `^[A-Z]{1,5}$` rejects BRK.B/BF.B/dotted tickers,
    blocking all 9 tools (and screeners' ticker params) for those issuers.
14. **LOW** edgar_client.py:24 — placeholder User-Agent default (latent).
15. **LOW** sec_filings.py:253 — ~1,000 date-parse warnings per call (with E1).
16. **LOW** server.py:3922-3926 — "• Concept: None" for null descriptions; labels
    fetched, never rendered.
17. **LOW** — batch rate-limit posture relies on fixed sleeps for raw-session calls.

### F. Field discovery (5) — direct audit
1. **MED** field_discovery/tools.py:548 — `validate_fields` accepts only the 150 public
   mapping names while the real tools also accept aliases and result keys (`p_e`,
   `net_margin`, `roi`…): tells users valid requests are invalid.
   *Resolved (phase 7): both paths now call `validators.get_valid_data_field_names()`.*
2. **LOW** field_discovery/tools.py:557 — typo table suggests `sales_growth_this_y`,
   which doesn't exist. *Resolved (phase 7): retargeted to `sales_yoy_ttm` in both
   correction tables; a test asserts every suggestion target validates.*
3. **MED** field_discovery/tools.py:411-460 — `search_fields` filtered on a stale
   hand-maintained category whitelist naming 11 fields that exist nowhere (`sma20`,
   `expense_ratio`, `float`…) while omitting the real ones, so a category filter
   silently hid legitimate matches (`search_fields('sma', category='technical')` →
   "No matches found" despite `sma_20/50/200`). *Found during the phase-7 sweep, not
   in the original audit. Resolved (phase 7): membership now derived from the same
   column-id ranges the other discovery tools use; unknown categories return an error
   listing the valid names instead of an empty result.*
4. **MED** field_discovery/tools.py:289 — `describe_field` looked names up in the 150-key
   mapping only, so every alias / CSV result key (`net_margin`, `p_e`, `eps_ttm`, `roi`)
   that `validate_fields` reports VALID was answered "not found". *Found in phase-7
   review. Resolved: names resolve through the shared
   `validators.resolve_canonical_field_name()` (inverse of the client's
   `_resolve_result_key`), and the requested spelling is echoed back.*
5. **LOW** field_discovery/tools.py:399 — `describe_field` printed hand-written category
   labels: 144 of 150 fields said "Other" and the 6 curated ones used ad-hoc names,
   contradicting the categories the other four tools show. *Found in phase-7 review.
   Resolved: category now comes from the same derived grouping.*

## Suggested fix order

1. **Shared parser mappings + zero-drop** (A) — one fix un-breaks columns/sorts in many
   screener tools at once; same technique as the fundamentals fix (verify headers live,
   pin with fixture tests).
2. **Always-empty tools** (D2-D4 header fix; D1 moving-average; C1 `Url`) — one-line-class
   fixes with maximal user impact.
3. **Stdio corruption** (B8 print) and **error swallowing** (B9, C5, E2) — reliability.
4. **Unwired/ignored parameters** (B1-B6, C2-C4, D5) — either wire them or remove/rename
   the advertised knobs; fix false criteria blocks (B12, B14, B24).
5. **Truncation/sort correctness** (B7, B16, D10, E3, E9).
6. **Units/labels** (D8, E10, B19-B20) and remaining MED/LOW cleanup.
