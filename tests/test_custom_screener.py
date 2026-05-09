#!/usr/bin/env python3
"""
Unit tests for the custom_screener tool and its supporting validation /
client functions.
"""

from unittest.mock import patch

import pandas as pd
import pytest

from src.finviz_client.base import FinvizClient
from src.utils.validators import (
    validate_and_normalize_raw_filters,
    validate_raw_sort_order,
    validate_signal,
)

# ---------------------------------------------------------------------------
# validate_and_normalize_raw_filters
# ---------------------------------------------------------------------------


class TestValidateAndNormalizeRawFilters:

    def test_basic_valid(self):
        errors, normalized = validate_and_normalize_raw_filters("cap_small,fa_div_o3")
        assert errors == []
        assert normalized == "cap_small,fa_div_o3"

    def test_whitespace_normalization(self):
        errors, normalized = validate_and_normalize_raw_filters("cap_small, fa_div_o3")
        assert errors == []
        assert normalized == "cap_small,fa_div_o3"

    def test_extra_whitespace(self):
        errors, normalized = validate_and_normalize_raw_filters(
            "  cap_small ,  fa_div_o3  "
        )
        assert errors == []
        assert normalized == "cap_small,fa_div_o3"

    def test_pipe_allowed(self):
        errors, normalized = validate_and_normalize_raw_filters(
            "earningsdate_yesterdayafter|todaybefore"
        )
        assert errors == []
        assert normalized == "earningsdate_yesterdayafter|todaybefore"

    def test_single_token(self):
        errors, normalized = validate_and_normalize_raw_filters("cap_large")
        assert errors == []
        assert normalized == "cap_large"

    def test_dots_and_hyphens(self):
        errors, normalized = validate_and_normalize_raw_filters("ta_sma20-50.cross")
        assert errors == []
        assert normalized == "ta_sma20-50.cross"

    def test_injection_rejected(self):
        errors, _ = validate_and_normalize_raw_filters("<script>alert(1)</script>")
        assert len(errors) > 0

    def test_sql_injection_rejected(self):
        errors, _ = validate_and_normalize_raw_filters("cap_small; DROP TABLE stocks")
        assert len(errors) > 0

    def test_uppercase_rejected(self):
        errors, _ = validate_and_normalize_raw_filters("CAP_LARGE")
        assert len(errors) > 0

    def test_empty_string(self):
        errors, normalized = validate_and_normalize_raw_filters("")
        assert len(errors) > 0
        assert normalized == ""

    def test_only_commas(self):
        errors, normalized = validate_and_normalize_raw_filters(",,,")
        assert len(errors) > 0
        assert normalized == ""

    def test_spaces_and_commas(self):
        errors, normalized = validate_and_normalize_raw_filters(" , , ")
        assert len(errors) > 0
        assert normalized == ""

    def test_too_many_tokens(self):
        tokens = ",".join([f"f{i}" for i in range(31)])
        errors, _ = validate_and_normalize_raw_filters(tokens)
        assert len(errors) > 0
        assert "30" in errors[0]

    def test_exactly_30_tokens(self):
        tokens = ",".join([f"f{i}" for i in range(30)])
        errors, normalized = validate_and_normalize_raw_filters(tokens)
        assert errors == []
        assert len(normalized.split(",")) == 30

    def test_none_input(self):
        errors, _ = validate_and_normalize_raw_filters(None)
        assert len(errors) > 0

    def test_non_string_input(self):
        errors, _ = validate_and_normalize_raw_filters(123)
        assert len(errors) > 0


# ---------------------------------------------------------------------------
# validate_raw_sort_order
# ---------------------------------------------------------------------------


class TestValidateRawSortOrder:

    def test_ascending(self):
        assert validate_raw_sort_order("marketcap") == []

    def test_descending(self):
        assert validate_raw_sort_order("-marketcap") == []

    def test_with_underscore(self):
        assert validate_raw_sort_order("-eps_surprise") == []

    def test_invalid_chars(self):
        errors = validate_raw_sort_order("market cap")
        assert len(errors) > 0

    def test_empty(self):
        errors = validate_raw_sort_order("")
        assert len(errors) > 0

    def test_none(self):
        errors = validate_raw_sort_order(None)
        assert len(errors) > 0

    def test_uppercase_rejected(self):
        errors = validate_raw_sort_order("-MarketCap")
        assert len(errors) > 0


# ---------------------------------------------------------------------------
# validate_signal
# ---------------------------------------------------------------------------


class TestValidateSignal:

    def test_valid(self):
        assert validate_signal("ta_topgainers") == []

    def test_valid_simple(self):
        assert validate_signal("ta_oversold") == []

    def test_invalid_with_hyphen(self):
        errors = validate_signal("ta-topgainers")
        assert len(errors) > 0

    def test_invalid_with_special_chars(self):
        errors = validate_signal("ta_top;gainers")
        assert len(errors) > 0

    def test_empty(self):
        errors = validate_signal("")
        assert len(errors) > 0

    def test_none(self):
        errors = validate_signal(None)
        assert len(errors) > 0


# ---------------------------------------------------------------------------
# screen_stocks_raw — max_results double-limit
# ---------------------------------------------------------------------------


class TestScreenStocksRaw:

    def test_max_results_applies_head(self):
        """Verify that screen_stocks_raw applies df.head() with clamped max_results."""
        client = FinvizClient(api_key="test_key")

        # Build a fake DataFrame with 100 rows
        fake_df = pd.DataFrame(
            {
                "Ticker": [f"T{i}" for i in range(100)],
                "Company": [f"Company {i}" for i in range(100)],
                "Sector": ["Technology"] * 100,
                "Industry": ["Software"] * 100,
                "Country": ["USA"] * 100,
                "Market Cap": [1000000000] * 100,
                "P/E": [20.0] * 100,
                "Price": [100.0] * 100,
                "Change": [1.0] * 100,
                "Volume": [500000] * 100,
            }
        )

        with patch.object(
            client, "_fetch_csv_from_url", return_value=fake_df
        ) as mock_fetch:
            results = client.screen_stocks_raw(
                filters="cap_large",
                max_results=10,
            )
            mock_fetch.assert_called_once()
            # Should return at most 10 stocks
            assert len(results) <= 10

    def test_max_results_clamped_to_500(self):
        """Verify max_results > 500 is clamped."""
        client = FinvizClient(api_key="test_key")
        fake_df = pd.DataFrame(
            {
                "Ticker": ["AAPL"],
                "Company": ["Apple"],
                "Sector": ["Technology"],
                "Industry": ["Consumer Electronics"],
                "Country": ["USA"],
                "Market Cap": [3000000000000],
                "P/E": [30.0],
                "Price": [200.0],
                "Change": [0.5],
                "Volume": [80000000],
            }
        )

        with patch.object(
            client, "_fetch_csv_from_url", return_value=fake_df
        ) as mock_fetch:
            client.screen_stocks_raw(filters="cap_mega", max_results=9999)
            call_params = mock_fetch.call_args[0][1]
            # ar parameter should be clamped to 500
            assert call_params["ar"] == "500"

    def test_max_results_zero_clamped_to_1(self):
        """Verify max_results=0 is clamped to 1."""
        client = FinvizClient(api_key="test_key")
        fake_df = pd.DataFrame(
            {
                "Ticker": ["AAPL"],
                "Company": ["Apple"],
                "Sector": ["Technology"],
                "Industry": ["Consumer Electronics"],
                "Country": ["USA"],
                "Market Cap": [3000000000000],
                "P/E": [30.0],
                "Price": [200.0],
                "Change": [0.5],
                "Volume": [80000000],
            }
        )

        with patch.object(
            client, "_fetch_csv_from_url", return_value=fake_df
        ) as mock_fetch:
            client.screen_stocks_raw(filters="cap_mega", max_results=0)
            call_params = mock_fetch.call_args[0][1]
            assert call_params["ar"] == "1"

    def test_no_max_results(self):
        """When max_results is None, ar param should not be set."""
        client = FinvizClient(api_key="test_key")
        empty_df = pd.DataFrame()

        with patch.object(
            client, "_fetch_csv_from_url", return_value=empty_df
        ) as mock_fetch:
            client.screen_stocks_raw(filters="cap_large", max_results=None)
            call_params = mock_fetch.call_args[0][1]
            assert "ar" not in call_params

    def test_signal_and_order_params(self):
        """Verify signal and order are passed correctly."""
        client = FinvizClient(api_key="test_key")
        empty_df = pd.DataFrame()

        with patch.object(client, "_fetch_csv_from_url", return_value=empty_df):
            client.screen_stocks_raw(
                filters="cap_large",
                signal="ta_topgainers",
                order="-marketcap",
            )
            call_params = client._fetch_csv_from_url.call_args[0][1]
            assert call_params["s"] == "ta_topgainers"
            assert call_params["o"] == "-marketcap"


# ---------------------------------------------------------------------------
# custom_screener tool — output formatting & integration
# ---------------------------------------------------------------------------


class TestCustomScreenerTool:

    @pytest.fixture
    def mock_stock(self):
        """Build a minimal StockData-like object with correct attribute names."""
        from src.models import StockData

        return StockData(
            ticker="AAPL",
            company_name="Apple Inc.",
            sector="Technology",
            industry="Consumer Electronics",
            price=195.50,
            price_change=-1.25,
            volume=54000000,
            market_cap=3000000,  # FinViz CSV returns market cap in millions ($3T)
            pe_ratio=30.5,
            relative_volume=1.12,
            dividend_yield=0.55,
            eps_surprise=4.20,
        )

    @pytest.mark.asyncio
    async def test_output_contains_correct_values(self, mock_stock):
        """Verify that the formatted output uses correct StockData attributes."""
        from src.server import server

        with patch("src.server.finviz_client") as mock_client:
            mock_client.screen_stocks_raw.return_value = [mock_stock]

            result = await server.call_tool(
                "custom_screener",
                {
                    "filters": "cap_large,fa_div_o3",
                },
            )

            text = result[0][0].text
            # Core values must appear — not "N/A"
            assert "Apple Inc." in text
            assert "$195.50" in text
            assert "-1.25%" in text
            assert "30.5" in text
            assert "Div Yield: 0.55%" in text
            assert "EPS Surprise: +4.20%" in text
            # Should NOT show N/A for fields we populated
            # (ticker line and company are on the same line)
            assert "AAPL | Apple Inc." in text

    @pytest.mark.asyncio
    async def test_output_no_stocks(self):
        """When no stocks match, a clear message is returned."""
        from src.server import server

        with patch("src.server.finviz_client") as mock_client:
            mock_client.screen_stocks_raw.return_value = []

            result = await server.call_tool(
                "custom_screener",
                {
                    "filters": "cap_nano",
                },
            )

            text = result[0][0].text
            assert "No stocks found" in text

    @pytest.mark.asyncio
    async def test_zero_values_not_shown_as_na(self, mock_stock):
        """Ensure price_change=0 and pe_ratio=0 render as 0, not N/A."""
        from src.models import StockData
        from src.server import server

        stock = StockData(
            ticker="FLAT",
            company_name="Flat Corp",
            sector="Industrials",
            industry="Misc",
            price=10.0,
            price_change=0.0,
            pe_ratio=0.0,
            volume=100,
            market_cap=500000,
        )

        with patch("src.server.finviz_client") as mock_client:
            mock_client.screen_stocks_raw.return_value = [stock]

            result = await server.call_tool(
                "custom_screener",
                {
                    "filters": "cap_small",
                },
            )

            text = result[0][0].text
            assert "+0.00%" in text  # price_change == 0
            assert "P/E: 0.0" in text  # pe_ratio == 0

    @pytest.mark.asyncio
    async def test_invalid_max_results_returns_error(self):
        """max_results outside 1-500 should return an explicit error."""
        from src.server import server

        result = await server.call_tool(
            "custom_screener",
            {
                "filters": "cap_large",
                "max_results": 0,
            },
        )
        text = result[0][0].text
        assert "Invalid max_results" in text

        result2 = await server.call_tool(
            "custom_screener",
            {
                "filters": "cap_large",
                "max_results": 501,
            },
        )
        text2 = result2[0][0].text
        assert "Invalid max_results" in text2

    @pytest.mark.asyncio
    async def test_filter_validation_error(self):
        """Invalid filter tokens return a clear validation error."""
        from src.server import server

        result = await server.call_tool(
            "custom_screener",
            {
                "filters": "<script>alert(1)</script>",
            },
        )
        text = result[0][0].text
        assert "Filter validation error" in text


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
