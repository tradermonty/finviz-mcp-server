import pytest
from unittest.mock import patch

# Import the tool and TextContent
from src.server import get_moving_average_position, TextContent


# ----------------------------- Fixtures & Mocks -----------------------------

def _mock_fundamentals(_ticker):
    """Return deterministic fundamentals for testing."""
    return {
        "price": 110.0,
        "20_day_simple_moving_average": 100.0,
        "50_day_simple_moving_average": 105.0,
        "200_day_simple_moving_average": 120.0,
    }


# ---------------------------------- Tests -----------------------------------

def test_returns_text_content_list():
    """Function should return a single TextContent object inside a list."""
    with patch("src.server.finviz_client.get_stock_fundamentals", side_effect=_mock_fundamentals):
        result = get_moving_average_position("AAPL")

    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], TextContent)


def test_output_contains_expected_values():
    """Output text should contain SMA values and correct percentage differences."""
    with patch("src.server.finviz_client.get_stock_fundamentals", side_effect=_mock_fundamentals):
        result = get_moving_average_position("AAPL")

    text = result[0].text

    # Basic headers
    assert "Moving Average Position" in text
    assert "20-Day SMA" in text
    assert "50-Day SMA" in text
    assert "200-Day SMA" in text

    # Percentage calculations: 110 vs 100 = +10%; 110 vs 105 ≈ +4.76%; 110 vs 120 ≈ -8.33%
    assert "+10.00% above" in text
    assert "+4.76% above" in text
    assert "-8.33% below" in text 