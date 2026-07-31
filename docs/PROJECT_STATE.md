# Project state & working memory

Durable project knowledge that is not derivable from the code or git history.
Agents and humans: write project memories HERE (not in machine-local memory
stores) so they travel with the repo. Keep entries short, dated, and prune
what stops being true.

## Current status (2026-07-31)

- Branch `fix/fundamentals-profitability-display` → **PR #2** (open):
  full-server data-integrity repair. 84 audit findings resolved across 8
  phases; finding-by-finding ledger in `AUDIT_FINDINGS.md` (repo root).
- Offline suite: 671 passed. Live: every tool verified against the real API
  at least once, including in-session intraday checks.
- After merge: any long-running MCP server process must be restarted to pick
  up code changes — a running stdio server keeps pre-change modules in
  memory even with an editable install.

## Where truth lives

- **`tests/fixtures/GROUND_TRUTH.md`** is the canonical reference for Finviz
  reality: verified column ids/headers (stock + groups exports), units,
  filter-token grammar, endpoint quirks, house rules. Trust it over any code
  comment; update it whenever a probe verifies something new.
- Tool parameter reference: `docs/tools_reference.md`. Behavior gotchas per
  tool: the catalog section of `CLAUDE.md`.

## Working agreements (learned the hard way — see AUDIT_FINDINGS.md)

1. **Never trust a hardcoded Finviz mapping; probe first.** Finviz silently
   ignores unknown `f=` filter tokens and unknown params (`ar=`, `sec=`,
   `filter=`), so "the query worked" proves nothing. The #1 bug class here
   was header/token drift.
2. **A parameter that can't be honored honestly gets removed, not faked.**
3. **Failures raise (`FinvizAPIError`/`EdgarAPIError`); only a header-only
   CSV is a legitimate empty result.** Never `[]`-as-"no results".
4. **0/0.0 are values** — `is not None`, never truthiness.
5. **Every fix lands with an offline test that fails on the pre-fix code.**
6. **Mocks hide signature drift**: `get_edgar_company_concept` was dead in
   production while mocked tests were green (`concept=` vs the library's
   `tag=`). Pin third-party signatures with real-signature stubs and finish
   big efforts with a live sweep.
7. Large repairs: per-phase coder subagent → independent reviewer → same
   coder fixes → orchestrator final pass → one commit per phase. Every
   phase's review caught real defects.

## Environment

- `.env` at repo root: `FINVIZ_API_KEY` (Elite, required for everything);
  `EDGAR_USER_AGENT` (required by the 5 EDGAR tools; NOT yet set here).
- Offline suite command + gates (black/isort, line 88): see CLAUDE.md
  Testing section. Live e2e opt-in: `--run-e2e`.
- Live probes: be gentle — ≥1s between Finviz calls, ~1/s to SEC.

## Known residuals (deliberate; ledger has details)

- D15: dead `FinvizScreener.get_relative_volume_stocks` +
  `_build_relative_volume_filters` latent KeyError (unreachable).
- B11 partial: `earnings_timing` renders "unknown" — no CSV column carries
  BMO/AMC timing.
- B21 partial: three zero-truthiness sites at `server.py:2789/2792/2800`.
- `README_ja.md` still says 128 columns (actual: 150).
- Cosmetics: unlabeled $M in three screener row formats; `Volume: ...0`
  trailing decimal in get_relative_volume_stocks; trading criteria echoes
  raw `0_to_negative_4w` spelling.
- Accepted limitations: ETF screener downloads the full ETF universe (no
  server-side AUM/expense tokens exist; filters are client-side and labeled);
  `get_sector_specific_industry_performance` passes unknown sectors through
  lowercased (Finviz then ignores `sg=` and returns all industries).

## Domain notes worth keeping

- `earnings_afterhours_screener` only ever has results on the same US/Eastern
  day, ~16:00 ET onward (needs `ah_change` data), rolling over at midnight;
  next morning those reporters belong to `earnings_trading_screener`
  (`earningsdate_yesterdayafter|todaybefore`). Friday AMC reporters are rare.
- Finviz `earnings_date` is the next scheduled report when announced,
  otherwise the most recent past report — never assume forward-looking.
- Finviz switched ownership-form spelling to `SCHEDULE 13G/D` in 2025;
  `form_matches` normalizes both spellings. Watch for similar renames.
