"""E2E invariant tests for fixed-criteria screeners.

Each fixed-criteria screener documents a set of filters (e.g., "Market Cap:
Large+ ($10B+), Price: $30+, Volume: 100K+, ..."). These tests call the
real Finviz API and assert that **every result actually satisfies those
criteria**. They catch bugs that mocked tests cannot, such as:

  - Incorrect Finviz filter codes silently returning the wrong universe
  - Field name / unit drift in StockData (e.g., market_cap millions vs.
    absolute, fixed in commit 2835440)
  - Sort or limit logic mistakes
  - Finviz API behavior changes

Conventions
-----------
* Marked with ``@pytest.mark.e2e`` and ``@pytest.mark.e2e_invariant``.
* Skipped by default; run with ``--run-e2e`` or ``-m e2e_invariant``.
  See ``tests/conftest.py`` and ``tests/E2E_TESTING.md`` for details.
* If a screener returns 0 results, the test is skipped with a warning.
* StockData unit conventions (FinViz CSV) — ``market_cap`` is in
  *millions* of dollars, ``avg_volume``/``volume`` are in *thousands*
  of shares. Unit *regressions* are protected by the parser-level tests
  in ``test_parser_unit_contracts.py``; this suite verifies the live
  API matches expectations within those units.

Required vs. optional invariants
--------------------------------
* ``optional=False`` (default): a missing/None field on any stock is a
  ``[MISSING-REQUIRED]`` violation; the test fails. Use this for fields
  the documented filter directly constrains.
* ``optional=True``: missing values do not fail per-stock, but if
  **every** result is missing the field the invariant is reported
  ``[UNVERIFIABLE]`` and the test fails — silently passing a filter we
  claimed to verify is the worst outcome.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Sequence

import pytest

from src.models import StockData

pytestmark = [pytest.mark.e2e, pytest.mark.e2e_invariant]

# FinViz CSV unit conventions (verified by parser unit-contract tests).
MILLIONS_PER_BILLION: float = 1_000.0
SHARES_PER_THOUSAND: float = 1_000.0

# Below this we skip rather than fail; some screeners (e.g. earnings
# premarket outside session hours) legitimately return 0 results.
MIN_RESULTS_FOR_HARD_FAIL: int = 1


# ---------------------------------------------------------------------------
# Invariant framework
# ---------------------------------------------------------------------------


@dataclass
class Invariant:
    name: str
    description: str
    check: Callable[[StockData], bool]
    field_getter: Callable[[StockData], object]
    # When False (default), a missing/None value is a violation.
    # When True, single missing values are tolerated but the invariant
    # fails if *every* result is missing the field.
    optional: bool = False


@dataclass
class InvariantViolation:
    ticker: str
    invariant: str
    description: str
    actual_value: object


@dataclass
class InvariantReport:
    screener: str
    total_results: int
    violations: List[InvariantViolation] = field(default_factory=list)
    missing_required: List[InvariantViolation] = field(default_factory=list)
    optional_coverage: dict[str, tuple[int, int]] = field(default_factory=dict)
    unverifiable: List[str] = field(default_factory=list)

    @property
    def has_failures(self) -> bool:
        return bool(self.violations or self.missing_required or self.unverifiable)

    def format(self) -> str:
        lines = [
            f"Screener '{self.screener}' returned {self.total_results} stocks.",
            f"  Invariant violations:    {len(self.violations)}",
            f"  Missing required fields: {len(self.missing_required)}",
            f"  Unverifiable invariants: {len(self.unverifiable)}",
        ]
        for v in self.violations[:20]:
            lines.append(
                f"  [VIOLATION] {v.ticker}: {v.invariant} "
                f"(expected {v.description}, got {v.actual_value!r})"
            )
        if len(self.violations) > 20:
            lines.append(f"  ... and {len(self.violations) - 20} more violations")
        for m in self.missing_required[:10]:
            lines.append(
                f"  [MISSING-REQUIRED] {m.ticker}: {m.invariant} field is None "
                f"(documented filter {m.description})"
            )
        if len(self.missing_required) > 10:
            lines.append(
                f"  ... and {len(self.missing_required) - 10} more missing fields"
            )
        for inv_name in self.unverifiable:
            lines.append(
                f"  [UNVERIFIABLE] {inv_name}: every result was missing this "
                "field, so the documented filter could not be verified."
            )
        if self.optional_coverage:
            lines.append("  Optional invariant coverage (verified/total):")
            for name, (verified, total) in self.optional_coverage.items():
                lines.append(f"    {name}: {verified}/{total}")
        return "\n".join(lines)


def _is_missing(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    return False


def assert_invariants(
    screener_name: str,
    results: Sequence[StockData],
    invariants: Sequence[Invariant],
) -> None:
    if len(results) < MIN_RESULTS_FOR_HARD_FAIL:
        pytest.skip(
            f"Screener '{screener_name}' returned 0 results. "
            "This may be legitimate (e.g., no earnings reported in this "
            "window) or may indicate the filter is over-restrictive. "
            "Re-run during regular US market hours to verify."
        )

    report = InvariantReport(screener=screener_name, total_results=len(results))
    verified_count: dict[str, int] = {inv.name: 0 for inv in invariants}

    for stock in results:
        for inv in invariants:
            value = inv.field_getter(stock)
            if _is_missing(value):
                if not inv.optional:
                    report.missing_required.append(
                        InvariantViolation(
                            ticker=stock.ticker or "<no-ticker>",
                            invariant=inv.name,
                            description=inv.description,
                            actual_value=None,
                        )
                    )
                continue
            verified_count[inv.name] += 1
            if not inv.check(stock):
                report.violations.append(
                    InvariantViolation(
                        ticker=stock.ticker or "<no-ticker>",
                        invariant=inv.name,
                        description=inv.description,
                        actual_value=value,
                    )
                )

    # An optional invariant with zero verifications is the worst kind
    # of silent pass: we claimed to check a documented filter and never
    # actually evaluated it.
    for inv in invariants:
        if inv.optional:
            verified = verified_count[inv.name]
            report.optional_coverage[inv.name] = (verified, len(results))
            if verified == 0:
                report.unverifiable.append(inv.name)

    if report.has_failures:
        pytest.fail(report.format(), pytrace=False)


# ---------------------------------------------------------------------------
# Common invariant builders
# ---------------------------------------------------------------------------


def price_at_least(min_price: float) -> Invariant:
    return Invariant(
        name=f"price >= ${min_price}",
        description=f">= ${min_price}",
        check=lambda s: s.price is not None and s.price >= min_price,
        field_getter=lambda s: s.price,
    )


def market_cap_at_least_billions(min_billions: float) -> Invariant:
    threshold = min_billions * MILLIONS_PER_BILLION
    return Invariant(
        name=f"market_cap >= ${min_billions}B",
        description=f">= ${min_billions}B (i.e. >= {threshold:.0f}M units)",
        check=lambda s: s.market_cap is not None and s.market_cap >= threshold,
        field_getter=lambda s: s.market_cap,
    )


def market_cap_at_least_millions(min_millions: float) -> Invariant:
    return Invariant(
        name=f"market_cap >= ${min_millions}M",
        description=f">= ${min_millions}M",
        check=lambda s: s.market_cap is not None and s.market_cap >= min_millions,
        field_getter=lambda s: s.market_cap,
    )


def avg_volume_at_least_shares(min_shares: int) -> Invariant:
    """Assert avg daily volume >= ``min_shares`` shares.

    StockData.avg_volume is in thousands of shares (FinViz CSV unit), so
    we divide the threshold by 1,000 internally. Unit regressions are
    caught by ``test_parser_unit_contracts.py``.
    """
    threshold_thousands = min_shares / SHARES_PER_THOUSAND
    return Invariant(
        name=f"avg_volume >= {min_shares:,} shares",
        description=f">= {min_shares:,} shares (i.e. >= {threshold_thousands:g}K units)",
        check=lambda s: s.avg_volume is not None
        and s.avg_volume >= threshold_thousands,
        field_getter=lambda s: s.avg_volume,
    )


def relative_volume_at_least(min_rel_vol: float) -> Invariant:
    return Invariant(
        name=f"relative_volume >= {min_rel_vol}",
        description=f">= {min_rel_vol}",
        check=lambda s: s.relative_volume is not None
        and s.relative_volume >= min_rel_vol,
        field_getter=lambda s: s.relative_volume,
    )


def _coalesce_change(s: StockData) -> Optional[float]:
    """Pick price_change_percent if populated, else fall back to price_change.

    Uses ``is not None`` so a real ``0.0`` is not silently treated as
    missing (which would mask a stock violating a >=2% filter).
    """
    if s.price_change_percent is not None:
        return s.price_change_percent
    return s.price_change


def price_change_at_least_percent(min_change: float) -> Invariant:
    return Invariant(
        name=f"price_change >= {min_change}%",
        description=f">= {min_change}% (today)",
        check=lambda s: (
            (v := _coalesce_change(s)) is not None and v >= min_change
        ),
        field_getter=_coalesce_change,
    )


def _coalesce_afterhours(s: StockData) -> Optional[float]:
    if s.afterhours_change_percent is not None:
        return s.afterhours_change_percent
    return s.afterhours_change


def afterhours_change_at_least_percent(min_change: float) -> Invariant:
    return Invariant(
        name=f"afterhours_change >= {min_change}%",
        description=f">= {min_change}% after-hours",
        check=lambda s: (
            (v := _coalesce_afterhours(s)) is not None and v >= min_change
        ),
        field_getter=_coalesce_afterhours,
        # Finviz Elite CSV may legitimately omit afterhours_change for
        # stocks without after-hours activity. optional=True tolerates
        # individual missing rows but the framework still fails if
        # every row is missing the field.
        optional=True,
    )


def above_sma_200() -> Invariant:
    """Assert ``StockData.above_sma_200`` is True.

    Uses only the explicit boolean. We do NOT fall back to
    ``price > sma_200`` because the ``sma_200`` field semantics in
    FinViz CSV (actual price vs. percent distance) are ambiguous, and
    AGL/HIMX have been observed with ``sma_200`` values inconsistent
    with the SMA-price interpretation.
    """
    return Invariant(
        name="above_sma_200 == True",
        description="StockData.above_sma_200 should be True",
        check=lambda s: s.above_sma_200 is True,
        field_getter=lambda s: s.above_sma_200,
        # Optional per-stock; framework still fails if all rows missing.
        optional=True,
    )


def above_sma_20() -> Invariant:
    return Invariant(
        name="above_sma_20 == True",
        description="StockData.above_sma_20 should be True",
        check=lambda s: s.above_sma_20 is True,
        field_getter=lambda s: s.above_sma_20,
        optional=True,
    )


# ---------------------------------------------------------------------------
# Per-screener invariant tests
# ---------------------------------------------------------------------------


class TestVolumeSurgeScreenerInvariants:
    """volume_surge_screener fixed criteria (src/finviz_client/screener.py:36):

    f=cap_smallover,ind_stocksonly,sh_avgvol_o100,sh_price_o10,
      sh_relvol_o1.5,ta_change_u2,ta_sma200_pa
    """

    def test_results_satisfy_documented_filters(self, screener) -> None:
        results = screener.volume_surge_screener()
        # NOTE: ta_sma200_pa (price above SMA200) is NOT verified locally
        # because the parser does not reliably populate
        # ``StockData.above_sma_200`` for this CSV view (it is only set
        # when both ``price`` and ``sma_200`` parse as truthy, and the
        # screener view often omits the SMA column). The filter token
        # IS in the request URL, so we trust Finviz's server-side
        # filter execution. Re-enable ``above_sma_200()`` here once the
        # parser/CSV view is changed to expose the SMA columns.
        assert_invariants(
            "volume_surge_screener",
            results,
            invariants=[
                market_cap_at_least_millions(300),    # cap_smallover = $300M+
                avg_volume_at_least_shares(100_000),  # sh_avgvol_o100
                price_at_least(10.0),                 # sh_price_o10
                relative_volume_at_least(1.5),        # sh_relvol_o1.5
                price_change_at_least_percent(2.0),   # ta_change_u2
                # above_sma_200(),                    # ta_sma200_pa — see note
            ],
        )

    def test_results_sorted_by_price_change_desc(self, screener) -> None:
        results = screener.volume_surge_screener()
        if len(results) < 2:
            pytest.skip("Not enough results to verify sort order.")
        present = [c for c in (_coalesce_change(r) for r in results) if c is not None]
        if len(present) < 2:
            pytest.skip("Insufficient populated price_change values to sort-check.")
        for a, b in zip(present, present[1:]):
            assert a + 1e-6 >= b, (
                f"Results not sorted by price change desc: {present[:5]}..."
            )


class TestUptrendScreenerInvariants:
    """uptrend_screener fixed criteria (src/finviz_client/screener.py:65):

    f=cap_microover,sh_avgvol_o100,sh_price_o10,ta_highlow52w_a30h,
      ta_perf2_4wup,ta_sma20_pa,ta_sma200_pa,ta_sma50_sa200
    """

    def test_results_satisfy_documented_filters(self, screener) -> None:
        results = screener.uptrend_screener()
        # NOTE: ta_sma20_pa, ta_sma200_pa, and ta_sma50_sa200 are NOT
        # verified locally — see the comment in TestVolumeSurgeScreener-
        # Invariants for the parser limitation. The filter tokens are
        # in the request URL; trust Finviz's server-side execution.
        assert_invariants(
            "uptrend_screener",
            results,
            invariants=[
                market_cap_at_least_millions(50),     # cap_microover = $50M+
                avg_volume_at_least_shares(100_000),  # sh_avgvol_o100
                price_at_least(10.0),                 # sh_price_o10
                # above_sma_20(),                     # ta_sma20_pa — see note
                # above_sma_200(),                    # ta_sma200_pa — see note
                # ta_perf2_4wup: 4-week perf positive. StockData has
                # performance_1m (~ 4 weeks), not performance_4w.
                Invariant(
                    name="performance_1m > 0",
                    description="1-month (~4w) performance positive",
                    check=lambda s: s.performance_1m is not None
                    and s.performance_1m > 0,
                    field_getter=lambda s: s.performance_1m,
                    optional=True,
                ),
            ],
        )


class TestEarningsPremarketScreenerInvariants:
    """earnings_premarket_screener (src/finviz_client/screener.py:155):

    f=cap_largeover,earningsdate_todaybefore,sh_avgvol_o100,
      sh_price_o30,ta_change_u2
    """

    def test_results_satisfy_documented_filters(self, screener) -> None:
        results = screener.earnings_premarket_screener()
        assert_invariants(
            "earnings_premarket_screener",
            results,
            invariants=[
                market_cap_at_least_billions(10),     # cap_largeover = $10B+
                avg_volume_at_least_shares(100_000),  # sh_avgvol_o100
                price_at_least(30.0),                 # sh_price_o30
                price_change_at_least_percent(2.0),   # ta_change_u2
            ],
        )


class TestEarningsAfterhoursScreenerInvariants:
    """earnings_afterhours_screener (src/finviz_client/screener.py:173):

    f=ah_change_u2,cap_largeover,earningsdate_todayafter,
      sh_avgvol_o100,sh_price_o30
    """

    def test_results_satisfy_documented_filters(self, screener) -> None:
        results = screener.earnings_afterhours_screener()
        assert_invariants(
            "earnings_afterhours_screener",
            results,
            invariants=[
                market_cap_at_least_billions(10),         # cap_largeover = $10B+
                avg_volume_at_least_shares(100_000),       # sh_avgvol_o100
                price_at_least(30.0),                      # sh_price_o30
                afterhours_change_at_least_percent(2.0),   # ah_change_u2
            ],
        )

    def test_max_60_results(self, screener) -> None:
        results = screener.earnings_afterhours_screener()
        assert len(results) <= 60, (
            f"earnings_afterhours_screener documented max is 60 results, "
            f"got {len(results)}"
        )


class TestEarningsTradingScreenerInvariants:
    """earnings_trading_screener (src/finviz_client/screener.py:192):

    f=cap_largeover,earningsdate_yesterdayafter|todaybefore,fa_epsrev_ep,
      fa_netmargin_3to,sh_avgvol_o200,sh_price_o30,ta_change_u,
      ta_perf_0to-4w
    """

    def test_results_satisfy_documented_filters(self, screener) -> None:
        results = screener.earnings_trading_screener()
        assert_invariants(
            "earnings_trading_screener",
            results,
            invariants=[
                market_cap_at_least_billions(10),     # cap_largeover = $10B+
                avg_volume_at_least_shares(200_000),  # sh_avgvol_o200
                price_at_least(30.0),                 # sh_price_o30
                Invariant(
                    name="profit_margin >= 3%",
                    description=">= 3% (fa_netmargin_3to)",
                    check=lambda s: s.profit_margin is not None
                    and s.profit_margin >= 3.0,
                    field_getter=lambda s: s.profit_margin,
                    optional=True,
                ),
            ],
        )

    def test_max_60_results(self, screener) -> None:
        results = screener.earnings_trading_screener()
        assert len(results) <= 60, (
            f"earnings_trading_screener documented max is 60 results, "
            f"got {len(results)}"
        )


# ---------------------------------------------------------------------------
# Cross-cutting invariants (run on a representative screener)
# ---------------------------------------------------------------------------


class TestStockDataIntegrity:
    """Sanity checks that apply to any screener result set."""

    def test_every_result_has_ticker(self, screener) -> None:
        results = screener.volume_surge_screener()
        if not results:
            pytest.skip("No results to check.")
        missing = [i for i, s in enumerate(results) if not s.ticker]
        assert not missing, (
            f"{len(missing)} stocks have empty/None ticker (positions {missing[:5]})"
        )

    def test_no_duplicate_tickers(self, screener) -> None:
        results = screener.volume_surge_screener()
        if not results:
            pytest.skip("No results to check.")
        tickers = [s.ticker for s in results]
        seen: set[str] = set()
        dupes: list[str] = []
        for t in tickers:
            if t in seen:
                dupes.append(t)
            seen.add(t)
        assert not dupes, f"Duplicate tickers in results: {dupes}"
