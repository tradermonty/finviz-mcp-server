"""
Regression tests for issue #17: 52-Week High / Low column collision.

Finviz Elite screener CSV view (v=151) returns "52-Week High" / "52-Week Low"
as percentage distances from current price, not absolute prices. Previously
the parser mapped both ``week_52_high`` (intended as price) and
``high_52w_relative`` (intended as percent) to the same column, leaving
``week_52_high`` populated with the percent value and producing collisions.

These tests pin the new behavior:

- ``high_52w_relative`` / ``low_52w_relative`` carry the percent.
- ``week_52_high`` / ``week_52_low`` are computed from price + percent so
  they remain absolute prices.
"""

import pandas as pd
import pytest

from src.finviz_client.base import FinvizClient


def _make_row(extra: dict) -> pd.Series:
    base = {
        "Ticker": "AAON",
        "Company": "AAON Inc",
        "Sector": "Industrials",
        "Industry": "Building Products & Equipment",
        "Country": "USA",
        "Market Cap": "12B",
        "Price": 148.06,
        "Change": "1.50%",
        "Volume": 500000,
    }
    base.update(extra)
    return pd.Series(base)


@pytest.fixture
def client():
    return FinvizClient(api_key="dummy-key")


class TestRelativePercentMapping:
    def test_high_relative_picks_up_percent_value(self, client):
        row = _make_row({"52-Week High": "27.59%", "52-Week Low": "138.81%"})
        stock = client._parse_stock_data_from_csv(row)
        assert stock.high_52w_relative == pytest.approx(27.59)
        assert stock.low_52w_relative == pytest.approx(138.81)

    def test_absolute_prices_are_computed_not_percent(self, client):
        row = _make_row({"52-Week High": "27.59%", "52-Week Low": "138.81%"})
        stock = client._parse_stock_data_from_csv(row)

        # Pre-fix bug: week_52_high stored 27.59 (the percent). After fix it
        # must be an actual price reconstructed from price + relative.
        assert stock.week_52_high is not None
        assert stock.week_52_high > stock.price, (
            f"week_52_high {stock.week_52_high} should exceed current price "
            f"{stock.price}, not equal the percent literal."
        )
        # 148.06 * (1 + 27.59/100) ≈ 188.91
        assert stock.week_52_high == pytest.approx(188.91, rel=0.01)

        # Same for low: price / (1 + low%) ≈ 148.06 / 2.3881 ≈ 62.0
        assert stock.week_52_low is not None
        assert stock.week_52_low < stock.price
        assert stock.week_52_low == pytest.approx(62.0, rel=0.05)


class TestEdgeCases:
    def test_missing_price_skips_absolute_computation(self, client):
        row = _make_row({"Price": None, "52-Week High": "27.59%"})
        stock = client._parse_stock_data_from_csv(row)
        # high_52w_relative still parsed from the percent column
        assert stock.high_52w_relative == pytest.approx(27.59)
        # absolute prices stay None when price is unknown
        assert stock.week_52_high is None
        assert stock.week_52_low is None

    def test_dash_value_stays_none(self, client):
        row = _make_row({"52-Week High": "-", "52-Week Low": "-"})
        stock = client._parse_stock_data_from_csv(row)
        assert stock.high_52w_relative is None
        assert stock.low_52w_relative is None
        assert stock.week_52_high is None
        assert stock.week_52_low is None
