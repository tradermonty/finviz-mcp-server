"""Tests for ``get_moving_average_position``.

Finviz's ``*-Day Simple Moving Average`` columns are the **percent distance
of the price from the SMA** (tests/fixtures/GROUND_TRUTH.md "Units"), and the
fundamentals parser hands them over as bare floats. These tests were
previously written against the old (broken) reading in which those numbers
were treated as absolute SMA dollar prices — that path produced nonsense such
as "20-Day SMA: $2.80 → +11808.21% above" on live data, so the old
expectations are gone on purpose.
"""

from unittest.mock import patch

from src.server import (
    TextContent,
    _sma_absolute_from_pct,
    _sma_position,
    get_moving_average_position,
)

# ----------------------------- Fixtures & Mocks -----------------------------


def _mock_fundamentals(_ticker):
    """Deterministic fundamentals: SMA fields are percent distances."""
    return {
        "price": 100.0,
        # price is 2.8 % above the 20-day SMA
        "20_day_simple_moving_average": 2.8,
        # price sits exactly on the 50-day SMA
        "50_day_simple_moving_average": 0.0,
        # price is 20 % below the 200-day SMA
        "200_day_simple_moving_average": -20.0,
    }


# ------------------------- Unit tests: derivation logic ----------------------


def test_absolute_sma_derived_from_percent_distance():
    """SMA = price / (1 + pct/100)."""
    assert _sma_absolute_from_pct(100.0, 2.8) == 100.0 / 1.028
    assert round(_sma_absolute_from_pct(100.0, 2.8), 2) == 97.28
    assert _sma_absolute_from_pct(100.0, 0.0) == 100.0
    assert _sma_absolute_from_pct(100.0, -20.0) == 125.0


def test_absolute_sma_missing_inputs_and_degenerate_ratio():
    assert _sma_absolute_from_pct(None, 2.8) is None
    assert _sma_absolute_from_pct(100.0, None) is None
    # pct == -100 would divide by zero
    assert _sma_absolute_from_pct(100.0, -100.0) is None


def test_position_uses_greater_or_equal_convention():
    """0.00 % counts as *above* (repo convention, commit 5be5d8c)."""
    assert _sma_position(2.8) == "above"
    assert _sma_position(0.0) == "above"
    assert _sma_position(-0.01) == "below"
    assert _sma_position(None) is None


# ---------------------------------- Tool tests -------------------------------


def test_returns_text_content_list():
    """Function should return a single TextContent object inside a list."""
    with patch(
        "src.server.finviz_client.get_stock_fundamentals",
        side_effect=_mock_fundamentals,
    ):
        result = get_moving_average_position("AAPL")

    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], TextContent)


def test_output_renders_percent_distance_and_derived_sma():
    with patch(
        "src.server.finviz_client.get_stock_fundamentals",
        side_effect=_mock_fundamentals,
    ):
        text = get_moving_average_position("AAPL")[0].text

    assert "Moving Average Position" in text
    assert "Current Price" in text
    assert "$100.00" in text

    # Percent distances are rendered as reported, with the sign of the value
    assert "+2.80% vs the SMA (above)" in text
    assert "+0.00% vs the SMA (above)" in text
    assert "-20.00% vs the SMA (below)" in text

    # Absolute SMAs are derived, not read off as dollars
    assert "$97.28" in text  # 100 / 1.028
    assert "$125.00" in text  # 100 / 0.8
    assert "derived from price" in text


def test_missing_price_reports_unavailable_instead_of_garbage():
    def _no_price(_ticker):
        return {"20_day_simple_moving_average": 2.8}

    with patch(
        "src.server.finviz_client.get_stock_fundamentals", side_effect=_no_price
    ):
        text = get_moving_average_position("AAPL")[0].text

    assert "N/A (current price unavailable)" in text
    assert "+2.80% vs the SMA (above)" in text
    # SMA fields absent entirely => plain N/A, no fabricated numbers
    assert "200-Day SMA           : N/A" in text


def test_degenerate_ratio_is_plain_na_not_a_price_complaint():
    """pct == -100 makes the derivation degenerate even though price exists."""

    def _degenerate(_ticker):
        return {"price": 100.0, "20_day_simple_moving_average": -100.0}

    with patch(
        "src.server.finviz_client.get_stock_fundamentals", side_effect=_degenerate
    ):
        text = get_moving_average_position("AAPL")[0].text

    assert "20-Day SMA            : N/A" in text
    # The price IS available here, so that message must not appear at all
    assert "current price unavailable" not in text
    assert "-100.00% vs the SMA (below)" in text


def test_period_lookup_does_not_confuse_sma20_with_sma200():
    """A key search on "sma20" must not match an "sma200" key."""

    def _only_200(_ticker):
        return {"price": 100.0, "sma200": 25.0}

    with patch(
        "src.server.finviz_client.get_stock_fundamentals", side_effect=_only_200
    ):
        text = get_moving_average_position("AAPL")[0].text

    twenty_day = text.split("20-Day SMA", 1)[1].split("50-Day SMA", 1)[0]
    assert "N/A" in twenty_day
    assert "25.00%" not in twenty_day
    # The 200-day row still resolves from the same key
    two_hundred = text.split("200-Day SMA", 1)[1]
    assert "+25.00% vs the SMA (above)" in two_hundred
    assert "$80.00" in two_hundred  # 100 / 1.25
