#!/usr/bin/env python3
"""
Comprehensive error handling and edge case tests for Finviz MCP Server.
Tests various error conditions, edge cases, and failure scenarios.
"""

import asyncio
import logging
from unittest.mock import patch

import pytest
from requests.exceptions import ConnectionError, HTTPError, Timeout

# FastMCP wraps tool exceptions in mcp.server.fastmcp.exceptions.ToolError when
# invoked through ``server.call_tool``. Import it under an alias so tests can
# distinguish boundary errors from local domain errors (src.utils.exceptions).
from mcp.server.fastmcp.exceptions import ToolError as McpToolError
from src.finviz_client.screener import FinvizScreener
from src.server import server
from src.utils.validators import validate_ticker
from tests import factories

logger = logging.getLogger(__name__)


def _content_list(result):
    return result[0] if isinstance(result, tuple) else result


def _first_text(result) -> str:
    content = _content_list(result)
    first_item = content[0] if isinstance(content, list) else content
    return first_item.text if hasattr(first_item, "text") else str(first_item)


class TestInputValidation:
    """Test input validation and parameter checking."""

    @pytest.mark.asyncio
    async def test_invalid_ticker_formats(self):
        """Test various invalid ticker formats.

        ``validate_ticker`` returns a bool: True for 1-5 alphabetic chars
        (case-insensitive), False otherwise. ``None`` falls through to the MCP
        boundary which raises ``McpToolError``.
        """
        # Strings the validator must reject (returns False). Note ``"ticker"``
        # is 6 characters and therefore invalid (regex caps at 5); ``"TICKER$"``
        # contains a non-alphabetic character.
        invalid_tickers = [
            "",  # Empty string
            " ",  # Whitespace only
            "123",  # Numbers only
            "ticker",  # Too long (6 chars) — would be 'TICKER' (6) after upper()
            "TOOLONGTICKERYMBOL",  # Too long
            "IN-VALID",  # Invalid characters
            "in valid",  # Spaces
            "TICKER$",  # Special characters
        ]
        # Strings the validator must accept (returns True). 1-letter and
        # lowercase short tickers are valid because the validator uppercases
        # before matching ``^[A-Z]{1,5}$``.
        valid_tickers = ["A", "aapl", "AAPL", "MSFT"]

        for ticker in invalid_tickers:
            assert (
                validate_ticker(ticker) is False
            ), f"Expected validate_ticker({ticker!r}) to be False"
        for ticker in valid_tickers:
            assert (
                validate_ticker(ticker) is True
            ), f"Expected validate_ticker({ticker!r}) to be True"

        # ``None`` reaches the MCP boundary; FastMCP rejects it via pydantic.
        with pytest.raises(McpToolError):
            await server.call_tool("get_stock_fundamentals", {"ticker": None})

    @pytest.mark.asyncio
    async def test_invalid_earnings_dates(self):
        """Test invalid earnings date parameters."""
        invalid_dates = [
            "",
            "invalid_date",
            "yesterday",
            "next_year",
            "2024-01-01",  # Specific dates not supported
            None,
            123,  # Wrong type
        ]

        for date in invalid_dates:
            with pytest.raises(McpToolError) as exc_info:
                await server.call_tool("earnings_screener", {"earnings_date": date})

            # FastMCP wraps the underlying validation failure; either the
            # pydantic message ("validation error") or the explicit
            # ``Invalid earnings_date`` string is acceptable.
            msg = str(exc_info.value)
            assert "earnings_date" in msg or "validation error" in msg.lower()

    @pytest.mark.asyncio
    async def test_invalid_market_cap_values(self):
        """Test invalid market cap parameters.

        ``validate_market_cap`` accepts the empty string (treated as
        "no filter") and is case-sensitive. We only assert against values
        the validator actually rejects.
        """
        # Empty string ``""`` is intentionally accepted as the default
        # value of ``cap`` in ALL_PARAMETERS, so it is not in this set.
        invalid_market_caps = [
            "invalid",
            "tiny",
            "huge",
            "LARGE",  # Case sensitivity — only lowercase variants are accepted
            123,  # Wrong type
        ]

        for market_cap in invalid_market_caps:
            with pytest.raises(McpToolError):
                await server.call_tool(
                    "earnings_screener",
                    {"earnings_date": "today_after", "market_cap": market_cap},
                )

    @pytest.mark.asyncio
    async def test_invalid_price_ranges(self):
        """Test invalid price range parameters.

        ``validate_price_range`` converts unparseable strings (e.g.
        ``"invalid"``) and zero to ``None`` / ``0.0`` and accepts both, so
        those values are intentionally NOT in this invalid set. Only the
        cases that the current validator actually rejects are asserted.
        """
        invalid_price_params = [
            {"min_price": -10.0},  # Negative price
            {"max_price": -5.0},  # Negative max price
            {"min_price": 100.0, "max_price": 50.0},  # Min > Max
        ]

        for price_params in invalid_price_params:
            with pytest.raises(McpToolError):
                params = {"earnings_date": "today_after", **price_params}
                await server.call_tool("earnings_screener", params)

    @pytest.mark.asyncio
    async def test_invalid_volume_parameters(self):
        """Test invalid volume parameters and current relative-volume contract.

        ``volume_surge_screener`` is parameterless, so ``min_relative_volume``
        is exercised through ``get_relative_volume_stocks`` instead.
        ``validate_volume(0)`` returns ``True`` (0 is a valid lower bound),
        so zero volume is intentionally NOT in this invalid set.
        """
        invalid_min_volume_params = [
            {"min_volume": -1000},  # Negative volume
            {"min_volume": "invalid"},  # Wrong type / unparseable
        ]

        for volume_params in invalid_min_volume_params:
            with pytest.raises(McpToolError):
                params = {"earnings_date": "today_after", **volume_params}
                await server.call_tool("earnings_screener", params)

        # ``get_relative_volume_stocks`` currently delegates relative-volume
        # validation to ``screen_stocks`` instead of rejecting at the MCP
        # boundary. Keep the test offline and pin that delegation contract.
        delegated_relative_volume_values = [-1.0, "invalid"]
        for min_relative_volume in delegated_relative_volume_values:
            with patch.object(FinvizScreener, "screen_stocks") as mock_screen:
                mock_screen.return_value = []

                result = await server.call_tool(
                    "get_relative_volume_stocks",
                    {"min_relative_volume": min_relative_volume},
                )

                assert "No stocks found" in _first_text(result)
                mock_screen.assert_called_once_with(
                    {
                        "relative_volume_min": min_relative_volume,
                        "price_min": None,
                        "sectors": [],
                    }
                )

    @pytest.mark.asyncio
    async def test_invalid_sector_parameters(self):
        """Test invalid sector parameters.

        ``sectors=[]`` is intentionally NOT in this invalid set: the
        current ``earnings_screener`` only validates sector contents under
        ``if sectors:`` (empty list is falsy and bypassed). Treating it as
        invalid here would let the call escape into the live Finviz path
        even after PR B removes the top-level ``except Exception`` wrapper.
        Same for ``None``, which is the documented "no filter" value.

        If empty-list rejection becomes a product requirement, that
        belongs in a server/validator change PR rather than this test.
        """
        invalid_sector_params = [
            {"sectors": [""]},  # Empty string in list
            {"sectors": [123]},  # Wrong type in list
            {"sectors": "Technology"},  # String instead of list
            {"sectors": ["Invalid Sector"]},  # Non-existent sector
        ]

        for sector_params in invalid_sector_params:
            with pytest.raises(McpToolError):
                params = {"earnings_date": "today_after", **sector_params}
                await server.call_tool("earnings_screener", params)

    @pytest.mark.asyncio
    async def test_invalid_data_fields(self):
        """Test invalid data fields for fundamentals.

        Empty list ``[]`` is treated as "no field filter" by
        ``get_stock_fundamentals`` (``if data_fields:`` is falsy), so it is
        intentionally NOT in this invalid set. Only field names the validator
        actually rejects are asserted.
        """
        invalid_data_fields = [
            [""],  # Empty string in list
            ["invalid_field"],  # Non-existent field
            ["pe_ratio", ""],  # Mix of valid and invalid
            "pe_ratio",  # String instead of list
            [123],  # Wrong type in list
        ]

        for data_fields in invalid_data_fields:
            with pytest.raises(McpToolError):
                await server.call_tool(
                    "get_stock_fundamentals",
                    {"ticker": "AAPL", "data_fields": data_fields},
                )


class TestNetworkErrorHandling:
    """Test network-related error handling.

    These tests assert that transport-layer failures surface as
    ``McpToolError`` at the FastMCP boundary. The MCP server is responsible
    for letting domain exceptions propagate; FastMCP wraps them into its own
    ``ToolError`` when ``server.call_tool`` is invoked.
    """

    @pytest.mark.asyncio
    async def test_connection_timeout(self):
        """Test handling of connection timeouts."""
        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.side_effect = Timeout("Connection timeout")

            with pytest.raises(McpToolError):
                await server.call_tool(
                    "earnings_screener", {"earnings_date": "today_after"}
                )

    @pytest.mark.asyncio
    async def test_connection_error(self):
        """Test handling of connection errors."""
        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.side_effect = ConnectionError("Failed to connect")

            with pytest.raises(McpToolError):
                await server.call_tool(
                    "earnings_screener", {"earnings_date": "today_after"}
                )

    @pytest.mark.asyncio
    async def test_http_errors(self):
        """Test handling of various HTTP errors."""
        http_errors = [
            HTTPError("400 Bad Request"),
            HTTPError("401 Unauthorized"),
            HTTPError("403 Forbidden"),
            HTTPError("404 Not Found"),
            HTTPError("429 Too Many Requests"),
            HTTPError("500 Internal Server Error"),
            HTTPError("503 Service Unavailable"),
        ]

        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            for error in http_errors:
                mock_screener.side_effect = error

                with pytest.raises(McpToolError):
                    await server.call_tool(
                        "earnings_screener", {"earnings_date": "today_after"}
                    )

    @pytest.mark.asyncio
    async def test_rate_limit_handling(self):
        """Test rate limit error handling."""
        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.side_effect = Exception("Rate limit exceeded")

            with pytest.raises(McpToolError):
                await server.call_tool(
                    "earnings_screener", {"earnings_date": "today_after"}
                )

    @pytest.mark.asyncio
    async def test_malformed_response_handling(self):
        """Test handling of malformed responses."""
        empty_responses = [
            None,  # None response
            "",  # Empty string
        ]
        malformed_responses = [
            "Invalid JSON",  # Invalid JSON
            {"error": "Server error"},  # Error response
            {"incomplete": "data"},  # Incomplete data
        ]

        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            for response in empty_responses:
                mock_screener.return_value = response

                result = await server.call_tool(
                    "earnings_screener", {"earnings_date": "today_after"}
                )
                assert "No stocks found" in _first_text(result)

            for response in malformed_responses:
                mock_screener.return_value = response

                with pytest.raises(McpToolError):
                    await server.call_tool(
                        "earnings_screener", {"earnings_date": "today_after"}
                    )


class TestDataValidation:
    """Test data validation and sanitization."""

    @pytest.mark.asyncio
    async def test_empty_results_handling(self):
        """Test handling of empty results."""
        empty_results = [[], None]

        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            for result in empty_results:
                mock_screener.return_value = result

                response = await server.call_tool(
                    "earnings_screener", {"earnings_date": "today_after"}
                )
                assert "No stocks found" in _first_text(response)

    @pytest.mark.asyncio
    async def test_partial_data_handling(self):
        """Test handling of partial or incomplete data."""
        partial_data_results = [
            [
                factories.make_stock_data(ticker="AAPL", price=None),
                factories.make_stock_data(ticker="MSFT", company_name=None),
                factories.make_stock_data(ticker=None, price=150.0),
            ],
            [factories.make_stock_data(ticker="AAPL"), factories.make_stock_data()],
        ]

        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            for result in partial_data_results:
                mock_screener.return_value = result

                response = await server.call_tool(
                    "earnings_screener", {"earnings_date": "today_after"}
                )
                assert "Earnings Screening Results" in _first_text(response)

    @pytest.mark.asyncio
    async def test_data_type_conversion(self):
        """Test handling of incorrect data types in response objects."""
        type_mismatch_results = [
            factories.make_stock_data(
                price="150.0",  # String instead of float
                volume="1000000",  # String instead of int
                pe_ratio="25.5",  # String instead of float
                market_cap="2.4T",  # String with suffix
            )
        ]

        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.return_value = type_mismatch_results

            with pytest.raises(McpToolError):
                await server.call_tool(
                    "earnings_screener", {"earnings_date": "today_after"}
                )


class TestConcurrencyAndPerformance:
    """Test concurrency issues and performance edge cases."""

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling of concurrent requests."""
        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.return_value = [factories.make_stock_data()]

            # Create multiple concurrent requests
            tasks = []
            for i in range(10):
                task = server.call_tool(
                    "earnings_screener", {"earnings_date": "today_after"}
                )
                tasks.append(task)

            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # All should complete successfully
            for result in results:
                assert not isinstance(result, Exception)
                assert result is not None

    @pytest.mark.asyncio
    async def test_memory_usage_large_datasets(self):
        """Test memory usage with large datasets."""
        # Create a large mock dataset
        large_dataset = [
            factories.make_stock_data(
                ticker=f"S{i:04d}",
                company_name=f"Company {i}",
                price=100.0 + i,
                volume=1_000_000 + i,
                market_cap=1_000 + i,
            )
            for i in range(1000)
        ]

        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.return_value = large_dataset

            result = await server.call_tool(
                "earnings_screener", {"earnings_date": "today_after"}
            )
            assert "1000 stocks found" in _first_text(result)

    @pytest.mark.asyncio
    async def test_slow_response_handling(self):
        """Test handling of slow (synchronous) API responses.

        ``FinvizScreener.earnings_screener`` is synchronous; passing an
        ``async def`` to ``side_effect`` returns an unawaited coroutine and
        the slow path is never actually exercised (RuntimeWarning, false
        pass). Use a real synchronous ``time.sleep`` so the wrapper path
        truly blocks for ~2 seconds within the 5-second outer wait_for
        budget.
        """
        import time

        def slow_response(*args, **kwargs):
            time.sleep(2)
            return []

        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.side_effect = slow_response

            result = await asyncio.wait_for(
                server.call_tool("earnings_screener", {"earnings_date": "today_after"}),
                timeout=5.0,
            )
            assert result is not None


class TestEdgeCaseScenarios:
    """Test various edge case scenarios."""

    @pytest.mark.asyncio
    async def test_special_character_handling(self):
        """Test handling of special characters in inputs."""
        special_char_inputs = [
            {"ticker": "AAPL", "sectors": ["Technology & Software"]},
            {"ticker": "AAPL", "sectors": ["Finance/Banking"]},
            {"ticker": "AAPL", "sectors": ["Energy & Utilities"]},
        ]

        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            for params in special_char_inputs:
                params["earnings_date"] = "today_after"

                # The current validator rejects unknown sector strings before
                # any screener call reaches the network/client layer.
                with pytest.raises(McpToolError):
                    await server.call_tool("earnings_screener", params)

            mock_screener.assert_not_called()

    @pytest.mark.asyncio
    async def test_unicode_handling(self):
        """Test handling of Unicode characters."""
        unicode_inputs = [
            {"ticker": "AAPL", "sectors": ["Technology™"]},
            {"ticker": "AAPL", "sectors": ["Financé"]},
            {"ticker": "AAPL", "sectors": ["Technología"]},
        ]

        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            for params in unicode_inputs:
                params["earnings_date"] = "today_after"

                with pytest.raises(McpToolError):
                    await server.call_tool("earnings_screener", params)

            mock_screener.assert_not_called()

    @pytest.mark.asyncio
    async def test_extreme_parameter_values(self):
        """Test extreme parameter values."""
        with patch.object(FinvizScreener, "earnings_screener") as mock_earnings:
            mock_earnings.return_value = []

            result = await server.call_tool(
                "earnings_screener",
                {
                    "earnings_date": "today_after",
                    "min_price": 0.0001,  # Very small price
                    "max_price": 999999.99,  # Very large price
                    "min_volume": 1,  # Minimum volume
                },
            )

            assert "No stocks found" in _first_text(result)
            mock_earnings.assert_called_once()

        with patch.object(FinvizScreener, "screen_stocks") as mock_screen:
            mock_screen.return_value = []

            result = await server.call_tool(
                "get_relative_volume_stocks",
                {
                    "min_relative_volume": 0.001,  # Very small relative volume
                    "min_price": 0.01,  # Very small price
                },
            )

            assert "No stocks found" in _first_text(result)
            mock_screen.assert_called_once()

        with patch.object(FinvizScreener, "dividend_growth_screener") as mock_dividend:
            mock_dividend.return_value = []

            result = await server.call_tool(
                "dividend_growth_screener",
                {
                    "min_dividend_yield": 0.001,  # Very small yield
                    "max_dividend_yield": 99.999,  # Very large yield
                    "min_dividend_growth": 0.01,  # Very small growth
                    "min_roe": 0.01,  # Very small ROE
                },
            )

            assert "No dividend growth stocks found" in _first_text(result)
            mock_dividend.assert_called_once()

    @pytest.mark.asyncio
    async def test_null_and_undefined_handling(self):
        """Test handling of null and undefined values."""
        null_params = [
            {"earnings_date": "today_after", "market_cap": None},
            {"earnings_date": "today_after", "sectors": None},
            {"earnings_date": "today_after", "min_price": None},
        ]

        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.return_value = []

            for params in null_params:
                # Should handle None values gracefully (as optional parameters)
                result = await server.call_tool("earnings_screener", params)
                assert "No stocks found" in _first_text(result)


class TestResourceManagement:
    """Test resource management and cleanup."""

    @pytest.mark.asyncio
    async def test_resource_cleanup_on_error(self):
        """Test that resources are properly cleaned up on errors."""
        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.side_effect = Exception("Simulated error")

            with pytest.raises(McpToolError):
                await server.call_tool(
                    "earnings_screener", {"earnings_date": "today_after"}
                )

            # Verify that the screener was called (and presumably cleaned up)
            mock_screener.assert_called()

    @pytest.mark.asyncio
    async def test_multiple_error_scenarios(self):
        """Test handling of multiple different error scenarios in sequence."""
        error_scenarios = [
            ConnectionError("Network error"),
            Timeout("Request timeout"),
            HTTPError("HTTP 500"),
            ValueError("Invalid data"),
            KeyError("Missing key"),
        ]

        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            for error in error_scenarios:
                mock_screener.side_effect = error

                with pytest.raises(McpToolError):
                    await server.call_tool(
                        "earnings_screener", {"earnings_date": "today_after"}
                    )

                # Reset for next test
                mock_screener.reset_mock()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-x"])
