"""Unit-contract tests for the FinViz CSV row parser.

These tests pin the *unit conventions* that the rest of the codebase
relies on. They are deliberately offline (no API key, no network) so
they run in every default ``pytest`` invocation and CI.

Why this exists
---------------

``StockData.market_cap`` is stored in **millions of dollars** (the
FinViz CSV unit). Volume units were historically inconsistent: FinViz
ships "Volume" in raw shares but "Average Volume" in *thousands* of
shares, and the parser used to store both verbatim — so
``volume / avg_volume`` was off by 1,000x and displays mislabeled avg
volume by three orders of magnitude. The parser now normalizes
``avg_volume`` to **absolute shares**, so both volume fields share one
unit. Display formatting and screener invariant tests depend on this.

Live invariant tests cannot detect a unit drift on their own — a
wrong-unit value scaled by 1,000 will still satisfy a threshold also
scaled by 1,000 — so this file locks the contract at the parser layer
with synthetic CSV input.

If you change the parser unit convention intentionally, update both
this file *and* every consumer (display formatting, screener invariant
helpers in ``test_e2e_screener_invariants.py``) in the same commit.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from src.finviz_client.base import FinvizClient
from src.finviz_client.screener import FinvizScreener

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def parser() -> FinvizClient:
    # No API key needed — _parse_stock_data_from_csv is pure: it takes
    # a row and produces a StockData. We never call any network method.
    return FinvizClient(api_key="not-used-for-parser-tests")


def _row(**overrides: object) -> pd.Series:
    """Construct a minimal CSV row resembling FinViz Elite's export format."""
    base = {
        "Ticker": "TEST",
        "Company": "Test Co.",
        "Sector": "Technology",
        "Industry": "Software",
        "Country": "USA",
        "Price": 100.0,
        "Change": 1.5,
        "Volume": 1234560,  # FinViz CSV unit: raw shares
        "Average Volume": 5678.90,  # FinViz CSV unit: thousands of shares
        "Market Cap": 196090.0,  # FinViz CSV unit: millions of dollars
        "Relative Volume": 1.75,
        "P/E": 25.5,
    }
    base.update(overrides)
    return pd.Series(base)


# ---------------------------------------------------------------------------
# Market cap unit contract
# ---------------------------------------------------------------------------


class TestMarketCapUnitContract:
    """``StockData.market_cap`` must remain in *millions* of dollars."""

    def test_market_cap_stored_as_csv_value_in_millions(self, parser):
        # AT&T-style: ~$196B. FinViz CSV reports this as 196090 (millions).
        row = _row(**{"Market Cap": 196090.0})
        stock = parser._parse_stock_data_from_csv(row)
        assert stock.market_cap == pytest.approx(196090.0), (
            "market_cap should be stored in millions (FinViz CSV unit), "
            "not absolute dollars. Did commit 2835440 get reverted?"
        )

    def test_megacap_market_cap_stays_in_millions(self, parser):
        # 3T-class (Apple-ish): 3,000,000 (in millions == $3T).
        row = _row(**{"Market Cap": 3_000_000.0})
        stock = parser._parse_stock_data_from_csv(row)
        assert stock.market_cap == pytest.approx(3_000_000.0)
        # An absolute-dollars regression would surface as 3e12, far
        # larger than any plausible millions-unit value. Hard ceiling:
        assert stock.market_cap < 1e9, (
            f"market_cap={stock.market_cap} looks like absolute dollars, "
            "not millions. Parser unit contract violated."
        )

    def test_small_cap_market_cap_in_millions(self, parser):
        # $300M boundary used by cap_smallover.
        row = _row(**{"Market Cap": 300.0})
        stock = parser._parse_stock_data_from_csv(row)
        assert stock.market_cap == pytest.approx(300.0)


# ---------------------------------------------------------------------------
# Volume unit contract
# ---------------------------------------------------------------------------


class TestVolumeUnitContract:
    """``avg_volume`` and ``volume`` must both be in *absolute shares*.

    FinViz ships "Volume" raw and "Average Volume" in thousands; the
    parser normalizes avg_volume so the two agree (bug report Class 5:
    the same response carried volume=29,861,730 raw next to
    average_volume=41,261.6 thousands, unlabeled and 1000x apart).
    """

    def test_avg_volume_normalized_to_absolute_shares(self, parser):
        # FTNT-style: ~6.15M shares avg. FinViz CSV reports 6148.17
        # (thousands); the parser must store 6,148,170 shares.
        row = _row(**{"Average Volume": 6148.17})
        stock = parser._parse_stock_data_from_csv(row)
        assert stock.avg_volume == pytest.approx(6_148_170), (
            "avg_volume should be normalized to absolute shares "
            "(CSV thousands x 1000)."
        )

    def test_volume_stored_as_csv_value_in_raw_shares(self, parser):
        row = _row(Volume=1234560)
        stock = parser._parse_stock_data_from_csv(row)
        assert stock.volume == pytest.approx(1234560), (
            "volume is shipped raw by FinViz and must be stored as-is."
        )

    def test_volume_and_avg_volume_share_one_unit(self, parser):
        """volume / avg_volume must be a sane relative-volume ratio.

        MRVL live values: Volume=29,861,730 raw, Average Volume=41,261.6
        (thousands). The CSV's own Relative Volume for that day was 0.72;
        the ratio of the two parsed fields must reproduce it.
        """
        row = _row(
            Volume=29_861_730, **{"Average Volume": 41_261.6}
        )
        stock = parser._parse_stock_data_from_csv(row)
        assert stock.volume / stock.avg_volume == pytest.approx(0.7237, abs=1e-3)

    def test_documented_filter_thresholds_are_in_shares(self, parser):
        """Cross-check the threshold convention used by invariant tests.

        ``avg_volume_at_least_shares(100_000)`` in the invariant suite
        compares directly against shares. A 100K-share row (CSV value
        100.0 thousands) must map to exactly 100,000.
        """
        row = _row(**{"Average Volume": 100.0})  # 100 thousand = 100K shares
        stock = parser._parse_stock_data_from_csv(row)
        assert stock.avg_volume == pytest.approx(100_000)


# ---------------------------------------------------------------------------
# Other parser sanity (non-numeric)
# ---------------------------------------------------------------------------


class TestParserBasics:
    def test_ticker_and_company_strings_round_trip(self, parser):
        row = _row(Ticker="MSFT", Company="Microsoft Corporation")
        stock = parser._parse_stock_data_from_csv(row)
        assert stock.ticker == "MSFT"
        assert stock.company_name == "Microsoft Corporation"

    def test_relative_volume_is_a_ratio_not_a_percent(self, parser):
        # 1.75 means 1.75x average, NOT 175%. Pin it.
        row = _row(**{"Relative Volume": 1.75})
        stock = parser._parse_stock_data_from_csv(row)
        assert stock.relative_volume == pytest.approx(1.75)


# ---------------------------------------------------------------------------
# Issue #19 — eps_revision is unfetchable via Finviz Elite CSV export
# ---------------------------------------------------------------------------


class TestEpsRevisionUnfetchable:
    """Regression tests that pin issue #19 in both directions.

    The Finviz Elite CSV export does not expose ``EPS Revision`` under
    any known view (v=151, v=152 both verified). The mapping in
    ``base.py`` is kept as a no-op so the day Finviz adds the column,
    the parser will pick it up automatically. These tests:

    1. ``test_eps_revision_none_when_column_absent`` — pins the
       current behavior. A CSV row WITHOUT an "EPS Revision" column
       must produce ``StockData.eps_revision is None``. If somebody
       silently changes the parser to default to 0 or skip the field,
       this test catches it.
    2. ``test_eps_revision_picked_up_when_column_present`` — pins the
       *forward path*. The day Finviz adds an "EPS Revision" column
       to its CSV view (or we switch to a view that already has it),
       the existing mapping in base.py must populate the field. This
       test demonstrates that the wiring is intact.
    """

    def test_eps_revision_none_when_column_absent(self, parser):
        # _row() does NOT include "EPS Revision" — matches today's
        # production CSV behavior under v=151 / v=152.
        row = _row()
        assert "EPS Revision" not in row.index, (
            "Test fixture invariant: _row() should not include "
            "'EPS Revision' so we can pin the production-CSV behavior."
        )
        stock = parser._parse_stock_data_from_csv(row)
        assert stock.eps_revision is None, (
            "When the CSV row has no 'EPS Revision' column, "
            "StockData.eps_revision must be None (issue #19)."
        )

    def test_eps_revision_picked_up_when_column_present(self, parser):
        # If Finviz ever adds the column, the existing field mapping
        # at src/finviz_client/base.py:1284 should populate it without
        # any further code change.
        row = _row(**{"EPS Revision": 12.5})
        stock = parser._parse_stock_data_from_csv(row)
        assert stock.eps_revision == pytest.approx(12.5), (
            "When the CSV row includes 'EPS Revision', the existing "
            "field mapping must pick it up. If this regresses, the "
            "mapping in base.py needs investigation."
        )


# ---------------------------------------------------------------------------
# Verified column headers (tests/fixtures/GROUND_TRUTH.md)
# ---------------------------------------------------------------------------


class TestVerifiedColumnHeaders:
    """Every mapping below uses a header verified against the live export.

    The parser previously keyed these fields off invented headers ("EPS
    Q/Q", "Sales Q/Q", "Recom", "Category", "EPS growth this Y" with the
    wrong case, bare "Volatility"), so the attributes were always None
    no matter what the CSV contained. The header strings asserted here
    come from GROUND_TRUTH.md's verified id -> header table; treat that
    file, not this test, as the source of truth if Finviz renames a
    column.
    """

    def test_eps_growth_horizons_use_title_case_headers(self, parser):
        row = _row(
            **{
                "EPS Growth This Year": "17.72%",
                "EPS Growth Next Year": "8.10%",
                "EPS Growth Past 5 Years": "12.34%",
                "EPS Growth Next 5 Years": "9.87%",
            }
        )
        stock = parser._parse_stock_data_from_csv(row)
        assert stock.eps_growth_this_y == pytest.approx(17.72)
        assert stock.eps_growth_next_y == pytest.approx(8.10)
        assert stock.eps_growth_past_5y == pytest.approx(12.34)
        assert stock.eps_growth_next_5y == pytest.approx(9.87)

    def test_quarter_over_quarter_growth_and_aliases(self, parser):
        row = _row(
            **{
                "EPS Growth Quarter Over Quarter": "28.85%",
                "Sales Growth Quarter Over Quarter": "16.36%",
            }
        )
        stock = parser._parse_stock_data_from_csv(row)
        # earnings_winners sorts on eps_growth_qtr; server.py prints the
        # *_qoq_growth aliases. Both names must carry the same value.
        assert stock.eps_growth_qtr == pytest.approx(28.85)
        assert stock.eps_qoq_growth == pytest.approx(28.85)
        assert stock.sales_growth_qtr == pytest.approx(16.36)
        assert stock.sales_qoq_growth == pytest.approx(16.36)

    def test_eps_next_q_is_next_quarter_estimate_not_qoq_growth(self, parser):
        # "EPS Next Q" (column id 77) is a dollar EPS estimate. The old
        # mapping pointed at "EPS Q/Q", which is both a phantom header
        # and a different quantity (a growth percentage).
        row = _row(**{"EPS Next Q": 2.0})
        stock = parser._parse_stock_data_from_csv(row)
        assert stock.eps_next_q == pytest.approx(2.0)

    def test_analyst_recommendation_uses_analyst_recom_header(self, parser):
        row = _row(**{"Analyst Recom": 1.98})
        stock = parser._parse_stock_data_from_csv(row)
        assert stock.analyst_recommendation == "1.98"

    def test_single_category_uses_single_category_header(self, parser):
        row = _row(**{"Single Category": "Large Blend"})
        stock = parser._parse_stock_data_from_csv(row)
        assert stock.single_category == "Large Blend"

    def test_net_expense_ratio_is_mapped(self, parser):
        # Column id 107 is in every stock/ETF export but had no mapping
        # at all, so the ETF screener's expense-ratio sort had nothing
        # to sort on.
        row = _row(**{"Net Expense Ratio": "0.09%"})
        stock = parser._parse_stock_data_from_csv(row)
        assert stock.net_expense_ratio == pytest.approx(0.09)

    def test_volatility_reads_the_weekly_column(self, parser):
        # No bare "Volatility" column exists; the generic attribute is
        # fed from "Volatility (Week)" (same choice as
        # models.FINVIZ_FIELD_MAPPING).
        row = _row(**{"Volatility (Week)": "2.30%", "Volatility (Month)": "2.75%"})
        stock = parser._parse_stock_data_from_csv(row)
        assert stock.volatility == pytest.approx(2.30)
        assert stock.volatility_week == pytest.approx(2.30)
        assert stock.volatility_month == pytest.approx(2.75)


class TestNonExistentColumnsStayNone:
    """Headers GROUND_TRUTH.md lists as non-existent must not be mapped.

    These mappings were deleted rather than kept as forward-compatible
    no-ops (unlike eps_revision / revenue_revision, which have pinned
    issue-#19 tests). Feeding the invented headers in must therefore
    change nothing — a re-added phantom mapping fails here.
    """

    def test_phantom_headers_do_not_populate_fields(self, parser):
        row = _row(
            **{
                "EPS Q/Q": 11.1,
                "Sales Q/Q": 22.2,
                "Recom": 3.0,
                "Category": "Phantom",
                "Earnings Time": "Before Market",
                "Volatility": 4.4,
                "EPS Estimate": 5.5,
                "EPS Actual": 6.6,
                "Revenue Estimate": 7.7,
                "Revenue Actual": 8.8,
                "EPS this Y": 9.9,
                "EPS next Y": 10.1,
                "EPS past 5Y": 11.2,
                "EPS next 5Y": 12.3,
                "Sales past 5Y": 13.4,
            }
        )
        stock = parser._parse_stock_data_from_csv(row)
        for field in (
            "eps_growth_qtr",
            "sales_growth_qtr",
            "eps_next_q",
            "analyst_recommendation",
            "single_category",
            "earnings_timing",
            "volatility",
            "eps_estimate",
            "eps_actual",
            "revenue_estimate",
            "revenue_actual",
            "eps_this_y",
            "eps_next_y",
            "eps_past_5y",
            "eps_next_5y",
            "sales_past_5y",
        ):
            assert getattr(stock, field) is None, (
                f"{field} was populated from a header that does not exist "
                "in any Finviz export (see GROUND_TRUTH.md)."
            )

    def test_performance_2y_is_not_fed_by_the_one_year_column(self, parser):
        # The export has no 2-year performance column. It used to be
        # mapped to "Performance (Year)", i.e. 1-year data under a
        # 2-year name.
        row = _row(**{"Performance (Year)": "49.11%"})
        stock = parser._parse_stock_data_from_csv(row)
        assert stock.performance_1y == pytest.approx(49.11)
        assert stock.performance_2y is None


# ---------------------------------------------------------------------------
# Zero is a value, not a missing datum
# ---------------------------------------------------------------------------


class TestZerosSurviveParsing:
    """``0``/``0.0`` must round-trip (GROUND_TRUTH.md house rule 4)."""

    def test_numeric_zero_change_is_preserved(self, parser):
        row = _row(Change=0.0)
        stock = parser._parse_stock_data_from_csv(row)
        assert stock.price_change == 0.0, "A flat day is 0.0, not missing data."
        assert stock.price_change_percent == 0.0

    def test_numeric_zero_dividend_is_preserved(self, parser):
        row = _row(Dividend=0.0)
        stock = parser._parse_stock_data_from_csv(row)
        assert stock.dividend == 0.0, "A non-payer's dividend is 0.0, not None."

    def test_string_zero_percent_is_preserved(self, parser):
        row = _row(**{"Performance (Week)": "0.00%"})
        stock = parser._parse_stock_data_from_csv(row)
        assert stock.performance_1w == 0.0

    def test_missing_value_is_still_none(self, parser):
        row = _row(**{"Performance (Week)": float("nan"), "P/E": "-"})
        stock = parser._parse_stock_data_from_csv(row)
        assert stock.performance_1w is None
        assert stock.pe_ratio is None


# ---------------------------------------------------------------------------
# Fixture-pinned: a real v=151 export row
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def dji_first_row() -> pd.Series:
    return pd.read_csv(FIXTURES / "screener_v151_dji.csv").iloc[0]


@pytest.fixture(scope="module")
def stock(parser, dji_first_row):
    return parser._parse_stock_data_from_csv(dji_first_row)


class TestRealExportRow:
    """Parse the first data row of the captured v=151 DJIA export."""

    def test_identity(self, stock):
        assert stock.ticker == "AAPL"

    @pytest.mark.parametrize(
        "field",
        [
            "eps_growth_qtr",
            "sales_growth_qtr",
            "eps_qoq_growth",
            "sales_qoq_growth",
            "analyst_recommendation",
            "eps_growth_this_y",
            "eps_next_q",
            "volatility",
        ],
    )
    def test_previously_dead_fields_populate(self, stock, field):
        assert getattr(stock, field) is not None, (
            f"{field} is None on a real export row — its column mapping "
            "is dead again."
        )

    def test_earnings_date_keeps_the_export_timestamp(self, stock, dji_first_row):
        assert stock.earnings_date == str(dji_first_row["Earnings Date"])

    def test_volume_units_are_absolute_shares(self, stock, dji_first_row):
        # Volume ships raw; Average Volume ships in thousands and is
        # normalized on the way in.
        assert stock.volume == pytest.approx(float(dji_first_row["Volume"]))
        assert stock.avg_volume == pytest.approx(
            float(dji_first_row["Average Volume"]) * 1000
        )


# ---------------------------------------------------------------------------
# Downstream contract: sorts that key on the repaired QoQ mapping
# ---------------------------------------------------------------------------


class TestQoQSortsAreNoLongerNoOps:
    """``eps_growth_qtr`` feeds two earnings sorts.

    While the field was mapped to the phantom "EPS Q/Q" header it was
    always None, so ``x.eps_growth_qtr or 0`` collapsed every key to 0
    and the sorts silently preserved the server's (reverse-ticker)
    order. These tests pin that they now order by the real value.
    """

    @staticmethod
    def _stocks(parser):
        rows = [
            _row(Ticker="LOW", **{"EPS Growth Quarter Over Quarter": "5.00%"}),
            _row(Ticker="HIGH", **{"EPS Growth Quarter Over Quarter": "50.00%"}),
            _row(Ticker="MID", **{"EPS Growth Quarter Over Quarter": "20.00%"}),
        ]
        return [parser._parse_stock_data_from_csv(row) for row in rows]

    def test_earnings_positive_surprise_default_sort(self, parser):
        screener = FinvizScreener(api_key="not-used")
        with patch.object(
            FinvizScreener, "screen_stocks", return_value=self._stocks(parser)
        ):
            results = screener.earnings_positive_surprise_screener()
        assert [s.ticker for s in results] == ["HIGH", "MID", "LOW"]

    def test_earnings_winners_eps_growth_qoq_sort(self, parser):
        screener = FinvizScreener(api_key="not-used")
        with patch.object(
            FinvizScreener, "screen_stocks", return_value=self._stocks(parser)
        ):
            results = screener.earnings_winners_screener(sort_by="eps_growth_qoq")
        assert [s.ticker for s in results] == ["HIGH", "MID", "LOW"]


class TestSortsKeepZeroDistinctFromMissing:
    """Sort keys must not fold ``0.0`` into a missing-data sentinel.

    ``x.field or 0`` / ``or -999`` ranks a genuine zero as if the datum
    were absent (and vice versa). The screeners now sort the rows that
    have a value and append the ones that don't, so a 0.00% expense
    ratio outranks an ETF whose ratio Finviz never reported.
    """

    @staticmethod
    def _etfs(parser):
        return [
            parser._parse_stock_data_from_csv(row)
            for row in (
                _row(Ticker="MID", **{"Net Expense Ratio": "0.20%"}),
                _row(Ticker="UNKNOWN"),  # column absent -> None
                _row(Ticker="FREE", **{"Net Expense Ratio": "0.00%"}),
                _row(Ticker="PRICEY", **{"Net Expense Ratio": "0.95%"}),
            )
        ]

    def test_expense_ratio_desc_is_highest_first_with_unknowns_last(self, parser):
        screener = FinvizScreener(api_key="not-used")
        with patch.object(
            FinvizScreener, "screen_stocks", return_value=self._etfs(parser)
        ):
            results = screener.etf_screener(sort_by="expense_ratio")
        # "desc" is the default and must mean descending here, as it does
        # for every other sort in screener.py.
        assert [s.ticker for s in results] == ["PRICEY", "MID", "FREE", "UNKNOWN"]

    def test_expense_ratio_asc_puts_the_zero_first_not_the_unknown(self, parser):
        screener = FinvizScreener(api_key="not-used")
        with patch.object(
            FinvizScreener, "screen_stocks", return_value=self._etfs(parser)
        ):
            results = screener.etf_screener(sort_by="expense_ratio", sort_order="asc")
        assert [s.ticker for s in results] == ["FREE", "MID", "PRICEY", "UNKNOWN"]

    def test_eps_growth_sorts_rank_zero_above_missing(self, parser):
        stocks = [
            parser._parse_stock_data_from_csv(row)
            for row in (
                _row(Ticker="UNKNOWN"),  # column absent -> None
                _row(Ticker="FLAT", **{"EPS Growth Quarter Over Quarter": "0.00%"}),
                _row(Ticker="DOWN", **{"EPS Growth Quarter Over Quarter": "-8.00%"}),
            )
        ]
        screener = FinvizScreener(api_key="not-used")
        with patch.object(FinvizScreener, "screen_stocks", return_value=stocks):
            default_sorted = screener.earnings_positive_surprise_screener()
            winners_sorted = screener.earnings_winners_screener(
                sort_by="eps_growth_qoq"
            )
        for results in (default_sorted, winners_sorted):
            assert [s.ticker for s in results] == ["FLAT", "DOWN", "UNKNOWN"]
