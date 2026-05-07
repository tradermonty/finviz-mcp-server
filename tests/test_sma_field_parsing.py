"""
Regression tests for issue #18: SMA boolean / absolute price parsing.

In Finviz Elite screener CSV view (v=151):

- The columns ``20-Day Simple Moving Average`` / ``50-Day Simple Moving Average`` /
  ``200-Day Simple Moving Average`` return relative percentages from current
  price, not absolute SMA prices.
- The columns ``SMA20`` / ``SMA50`` / ``SMA200`` (which the previous parser
  used to trigger boolean computation) **do not exist** in this view.

Previous behavior:
  - ``above_sma_20`` / ``above_sma_50`` / ``above_sma_200`` were always
    ``None`` (the boolean trigger column never matched).
  - ``sma_20`` / ``sma_50`` / ``sma_200`` silently held the percent literal
    instead of an absolute price.

These tests pin the new behavior:

- ``sma_20_relative`` / ``sma_50_relative`` / ``sma_200_relative`` carry the
  percent values (positive = price above SMA).
- ``above_sma_*`` booleans derive from the sign of the relative percent.
- ``sma_*`` absolute prices are computed from price + relative percent.
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


class TestRelativeSmaMapping:
    def test_relatives_pick_up_percent_values(self, client):
        row = _make_row({
            "20-Day Simple Moving Average": "53.24%",
            "50-Day Simple Moving Average": "63.22%",
            "200-Day Simple Moving Average": "64.58%",
        })
        stock = client._parse_stock_data_from_csv(row)
        assert stock.sma_20_relative == pytest.approx(53.24)
        assert stock.sma_50_relative == pytest.approx(63.22)
        assert stock.sma_200_relative == pytest.approx(64.58)


class TestAboveSmaBooleans:
    def test_positive_relative_means_above(self, client):
        row = _make_row({
            "20-Day Simple Moving Average": "5.00%",
            "50-Day Simple Moving Average": "10.50%",
            "200-Day Simple Moving Average": "0.10%",
        })
        stock = client._parse_stock_data_from_csv(row)
        assert stock.above_sma_20 is True
        assert stock.above_sma_50 is True
        assert stock.above_sma_200 is True

    def test_negative_relative_means_below(self, client):
        row = _make_row({
            "20-Day Simple Moving Average": "-2.50%",
            "50-Day Simple Moving Average": "-7.30%",
            "200-Day Simple Moving Average": "-0.10%",
        })
        stock = client._parse_stock_data_from_csv(row)
        assert stock.above_sma_20 is False
        assert stock.above_sma_50 is False
        assert stock.above_sma_200 is False

    def test_missing_relative_leaves_boolean_none(self, client):
        row = _make_row({
            "20-Day Simple Moving Average": "-",
            "50-Day Simple Moving Average": "-",
            "200-Day Simple Moving Average": "-",
        })
        stock = client._parse_stock_data_from_csv(row)
        assert stock.above_sma_20 is None
        assert stock.above_sma_50 is None
        assert stock.above_sma_200 is None


class TestAbsoluteSmaComputation:
    def test_absolute_sma_is_price_not_percent(self, client):
        row = _make_row({
            "20-Day Simple Moving Average": "53.24%",
            "50-Day Simple Moving Average": "63.22%",
            "200-Day Simple Moving Average": "64.58%",
        })
        stock = client._parse_stock_data_from_csv(row)

        # Pre-fix bug: sma_20 stored 53.24 (the percent). After fix it must be
        # an absolute SMA price reconstructed from price + relative percent.
        # 148.06 / (1 + 53.24/100) ≈ 96.62
        assert stock.sma_20 == pytest.approx(96.62, rel=0.01)
        assert stock.sma_50 == pytest.approx(90.71, rel=0.01)
        assert stock.sma_200 == pytest.approx(89.96, rel=0.01)

        # Sanity: the reconstructed price is below current price (since
        # relatives are positive) and clearly different from the percent literal.
        assert stock.sma_20 < stock.price
        assert abs(stock.sma_20 - 53.24) > 10

    def test_missing_price_skips_absolute(self, client):
        row = _make_row({
            "Price": None,
            "20-Day Simple Moving Average": "5.00%",
        })
        stock = client._parse_stock_data_from_csv(row)
        # boolean still derivable from the relative
        assert stock.above_sma_20 is True
        # absolute stays None when price is unknown
        assert stock.sma_20 is None
