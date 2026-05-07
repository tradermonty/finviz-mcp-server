"""Unit-contract tests for the FinViz CSV row parser.

These tests pin the *unit conventions* that the rest of the codebase
relies on. They are deliberately offline (no API key, no network) so
they run in every default ``pytest`` invocation and CI.

Why this exists
---------------

``StockData.market_cap`` is stored in **millions of dollars** and
``StockData.avg_volume`` / ``StockData.volume`` are stored in
**thousands of shares** because the FinViz Elite CSV export ships those
columns in those compact units. Display formatting and screener
invariant tests both depend on this.

Live invariant tests cannot detect a unit drift on their own — a
wrong-unit value scaled by 1,000 will still satisfy a threshold also
scaled by 1,000 — so this file locks the contract at the parser layer
with synthetic CSV input.

If you change the parser unit convention intentionally, update both
this file *and* every consumer (display formatting, screener invariant
helpers in ``test_e2e_screener_invariants.py``) in the same commit.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.finviz_client.base import FinvizClient


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
        "Volume": 1234.56,            # FinViz CSV unit: thousands of shares
        "Average Volume": 5678.90,    # FinViz CSV unit: thousands of shares
        "Market Cap": 196090.0,       # FinViz CSV unit: millions of dollars
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
    """``avg_volume`` and ``volume`` must remain in *thousands* of shares."""

    def test_avg_volume_stored_as_csv_value_in_thousands(self, parser):
        # FTNT-style: ~6.15M shares avg. FinViz CSV reports 6148.17.
        row = _row(**{"Average Volume": 6148.17})
        stock = parser._parse_stock_data_from_csv(row)
        assert stock.avg_volume == pytest.approx(6148.17), (
            "avg_volume should be stored in thousands of shares (FinViz "
            "CSV unit), not absolute share counts."
        )
        # An absolute-shares regression would scale this by 1,000 to
        # ~6_148_170. Hard ceiling under the thousands-unit contract:
        assert stock.avg_volume < 1e7, (
            f"avg_volume={stock.avg_volume} looks like absolute shares, "
            "not thousands. Parser unit contract violated."
        )

    def test_volume_stored_as_csv_value_in_thousands(self, parser):
        row = _row(Volume=1234.56)
        stock = parser._parse_stock_data_from_csv(row)
        assert stock.volume == pytest.approx(1234.56), (
            "volume should be stored in thousands of shares (FinViz "
            "CSV unit), not absolute share counts."
        )

    def test_documented_filter_thresholds_are_in_thousands(self, parser):
        """Cross-check the threshold convention used by invariant tests.

        ``avg_volume_at_least_shares(100_000)`` in the invariant suite
        compares against 100 (because 100K shares = 100 thousand units
        when the CSV unit is thousands). Verify a 100K-share row maps
        to exactly 100.
        """
        row = _row(**{"Average Volume": 100.0})  # 100 thousand = 100K shares
        stock = parser._parse_stock_data_from_csv(row)
        assert stock.avg_volume == pytest.approx(100.0)


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
