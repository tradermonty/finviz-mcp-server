# E2E Screener Invariant Tests

Two layered test suites verify that screeners behave correctly:

| Suite | File | Hits API | Default `pytest` |
|-------|------|---------|------------------|
| Parser unit contracts | `tests/test_parser_unit_contracts.py` | No | **Runs** |
| Screener invariant E2E | `tests/test_e2e_screener_invariants.py` | Yes (Finviz Elite) | Skipped |

The parser-level tests pin the FinViz CSV unit conventions
(`market_cap` in millions, `avg_volume`/`volume` in thousands of shares)
using synthetic rows. The E2E suite calls the live API and checks that
every returned stock satisfies the documented filter criteria.

## Why both layers

A unit drift in one direction can mask itself in the other layer alone:

- A parser bug that returns `avg_volume` in absolute shares instead of
  thousands would still pass the live invariant `>= 100K shares` check
  if the threshold is also scaled by 1,000. Only the parser-level
  fixture catches that.
- A wrong Finviz filter code that admits `$5B`-cap stocks into a
  documented `$10B+` screener would pass parser tests trivially. Only
  the live invariant catches that.

Past bugs caught by this layered approach:

| Bug | Commit | Layer that catches it |
|-----|--------|----------------------|
| `market_cap` parsed as millions vs. absolute | `2835440` | parser unit contracts |
| Wrong `StockData` attribute names | `5bb158c` | live invariants |
| Earnings filter too loose ($300M vs $10B) | `558ca61` | live invariants |

## Running

```bash
# Default: parser tests run, E2E auto-skipped (CI-safe)
pytest

# All tests including E2E
pytest --run-e2e

# Only the screener invariant suite
pytest -m e2e_invariant

# Only e2e tests (a wider category — auto-marks any live-test file)
pytest -m e2e

# Convenience runner (sets --run-e2e + selects e2e_invariant)
python3 scripts/run_e2e_invariants.py

# Run a single screener's invariants
pytest -m e2e_invariant -k uptrend
```

The auto-skip is implemented in `tests/conftest.py` via
`pytest_collection_modifyitems`. Files matching known live-test name
patterns are auto-marked `e2e`; you can also add
`pytestmark = [pytest.mark.e2e]` at module top-level for explicit
marking.

## Required vs. optional invariants

Each `Invariant(...)` in `test_e2e_screener_invariants.py` declares
whether the underlying field is required:

- **`optional=False`** (default): a missing/None field on any stock is
  recorded as a `[MISSING-REQUIRED]` violation and the test fails. Use
  this for fields the documented filter directly constrains (price,
  market cap, avg volume).
- **`optional=True`**: a missing field on a *single* stock is tolerated
  silently, but if **every** result is missing the field the invariant
  becomes "unverifiable" and the test fails with `[UNVERIFIABLE]`. This
  prevents the framework from silently passing while not actually
  checking a documented filter. Used for fields Finviz Elite
  occasionally omits (`afterhours_change_percent`, `above_sma_200`).

## Behavior on edge cases

- **No API key** → live tests `skip` cleanly (parser tests still run).
- **0 results** → live tests `skip` with a warning. Some screeners
  (especially earnings-time-of-day ones) can legitimately return 0.
  Re-run during US market hours to confirm.
- **All violations are reported together** in one block, not just the
  first.

## Adding a new screener

1. Locate the fixed filter string in `src/finviz_client/screener.py`
   (`f=...` in the docstring).
2. Add a `class TestXxxScreenerInvariants` to
   `test_e2e_screener_invariants.py`.
3. For each filter token, add an `Invariant(...)` using a helper
   (`price_at_least`, `market_cap_at_least_billions`,
   `avg_volume_at_least_shares`, `relative_volume_at_least`,
   `price_change_at_least_percent`,
   `afterhours_change_at_least_percent`, `above_sma_200`, etc.).
   Custom invariants can be inlined with the `Invariant(...)`
   constructor.
4. Use `optional=True` only when Finviz legitimately omits the field
   (such fields will still hard-fail if 100% of results are missing
   them).
5. If a filter cannot be verified from `StockData` (e.g. sector
   inclusion when the field isn't in the CSV view), document that in
   the test docstring rather than silently skipping it.
