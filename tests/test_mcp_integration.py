#!/usr/bin/env python3
"""
Integration tests for MCP server functionality.
Tests the actual MCP protocol integration and server behavior.
"""

import asyncio
import json
import logging
from unittest.mock import patch

import pytest

from mcp.server.fastmcp import FastMCP

# FastMCP wraps tool exceptions in mcp.server.fastmcp.exceptions.ToolError
# when invoked through ``server.call_tool``.
from mcp.server.fastmcp.exceptions import ToolError as McpToolError
from mcp.types import TextContent
from src.finviz_client.base import FinvizClient
from src.finviz_client.news import FinvizNewsClient
from src.finviz_client.screener import FinvizScreener
from src.finviz_client.sector_analysis import FinvizSectorAnalysisClient
from src.server import server
from tests import factories

logger = logging.getLogger(__name__)


def _content_list(result):
    return result[0] if isinstance(result, tuple) else result


def _first_text(result) -> str:
    content = _content_list(result)
    first_item = content[0] if isinstance(content, list) else content
    return first_item.text if hasattr(first_item, "text") else str(first_item)


def _make_upcoming_earnings_stock():
    stock = factories.make_stock_data(
        earnings_date="2026-05-14",
        earnings_timing="Before Market",
    )
    stock.current_price = stock.price
    stock.target_price_upside = 16.7
    return stock


class TestMCPServerIntegration:
    """Test MCP server protocol integration."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup method for each test."""
        self.mock_results = [factories.make_stock_data()]

    @pytest.mark.asyncio
    async def test_server_initialization(self):
        """Test that the MCP server initializes correctly."""
        assert server is not None
        assert isinstance(server, FastMCP)
        assert server.name == "Finviz MCP Server"

    @pytest.mark.asyncio
    async def test_tool_registration(self):
        """Test that the documented core tools are registered with the MCP server.

        ``server.list_tools()`` is async on current FastMCP. The repository now
        exposes additional surface area (SEC filings, EDGAR, field-discovery,
        sector/industry helpers) so the assertion is "must include" — adding
        new tools should not break this test.
        """
        expected_tools = [
            "earnings_screener",
            "volume_surge_screener",
            "get_stock_fundamentals",
            "get_multiple_stocks_fundamentals",
            "trend_reversion_screener",
            "uptrend_screener",
            "dividend_growth_screener",
            "etf_screener",
            "earnings_premarket_screener",
            "earnings_afterhours_screener",
            "earnings_trading_screener",
            "get_stock_news",
            "get_market_news",
            "get_sector_news",
            "get_sector_performance",
            "get_industry_performance",
            "get_country_performance",
            "get_market_overview",
            "get_relative_volume_stocks",
            "technical_analysis_screener",
            "upcoming_earnings_screener",
            "custom_screener",
        ]

        tools = await server.list_tools()
        registered_tool_names = {tool.name for tool in tools}

        missing = [t for t in expected_tools if t not in registered_tool_names]
        assert not missing, f"Expected tools not registered: {missing}"

    @pytest.mark.asyncio
    async def test_tool_metadata(self):
        """Test that tools have proper metadata."""
        tools = await server.list_tools()

        for tool in tools:
            # Each tool should have a name
            assert tool.name is not None
            assert len(tool.name) > 0

            # Each tool should have a description
            assert tool.description is not None
            assert len(tool.description) > 0

            # Tools should have input schema
            assert tool.inputSchema is not None

    @pytest.mark.asyncio
    async def test_mcp_protocol_compliance(self):
        """Test MCP protocol compliance."""
        # Test that server responds to standard MCP methods

        # Test list_tools
        tools = await server.list_tools()
        assert isinstance(tools, list)
        assert len(tools) > 0

        # Test that tools return proper TextContent.
        # FastMCP's ``call_tool`` now returns ``(content_list, structured)``
        # where ``content_list`` is the iterable of ``TextContent``/dicts
        # callers want to render and ``structured`` is the JSON-shaped
        # response. We accept either legacy bare-list or the new tuple shape.
        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            result = await server.call_tool(
                "earnings_screener", {"earnings_date": "today_after"}
            )

            assert result is not None
            content = _content_list(result)
            if isinstance(content, list):
                for item in content:
                    assert isinstance(item, (TextContent, dict))
            else:
                assert isinstance(content, (TextContent, dict))

    @pytest.mark.asyncio
    async def test_parameter_validation_integration(self):
        """Test parameter validation through MCP interface.

        ``min_price="invalid"`` is intentionally NOT exercised here:
        ``validate_price_range`` coerces unparseable strings to ``None``
        and accepts the result, so the call would proceed into the live
        screener path. Use a value the validator actually rejects (an
        explicitly negative bound) to assert the boundary error.
        """
        # Missing required parameter — pydantic at the FastMCP boundary
        # will raise McpToolError before any client call happens.
        with pytest.raises(McpToolError):
            await server.call_tool("earnings_screener", {})

        # Invalid bound — validate_price_range rejects negatives and
        # raises ValueError inside the tool.
        with pytest.raises(McpToolError):
            await server.call_tool(
                "earnings_screener",
                {
                    "earnings_date": "today_after",
                    "min_price": -1.0,
                },
            )

    @pytest.mark.asyncio
    async def test_tool_execution_flow(self):
        """Test the complete tool execution flow."""
        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            # Execute tool and verify the flow
            result = await server.call_tool(
                "earnings_screener",
                {
                    "earnings_date": "today_after",
                    "market_cap": "large",
                    "min_price": 10.0,
                },
            )

            # Verify screener was called with correct parameters
            mock_screener.assert_called_once()
            call_args = mock_screener.call_args  # noqa: F841

            # Verify result is properly formatted
            assert result is not None
            assert "Earnings Screening Results" in _first_text(result)


class TestMCPToolInterfaces:
    """Test individual MCP tool interfaces."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup mock data for tool interface tests."""
        self.stock_data = {
            "ticker": "AAPL",
            "company": "Apple Inc.",
            "sector": "Technology",
            "price": 150.0,
            "volume": 50000000,
        }

        self.news_data = [factories.make_news_data()]

        self.sector_data = [
            {
                "name": "Technology",
                "market_cap": "$12.3T",
                "pe_ratio": "28.4",
                "dividend_yield": "0.7%",
                "change": "1.2%",
                "stocks": "760",
            }
        ]
        self.industry_data = [
            {
                "industry": "Software - Application",
                "market_cap": "$2.1T",
                "pe_ratio": "34.1",
                "change": "0.8%",
                "stocks": "210",
            }
        ]
        self.country_data = [
            {
                "country": "USA",
                "market_cap": "$55.0T",
                "pe_ratio": "24.2",
                "change": "0.4%",
                "stocks": "4200",
            }
        ]

    @pytest.mark.asyncio
    async def test_stock_fundamentals_interface(self):
        """Test stock fundamentals tool interface."""
        with patch.object(FinvizClient, "get_stock_fundamentals") as mock_client:
            mock_client.return_value = self.stock_data

            # Test single stock
            result = await server.call_tool(
                "get_stock_fundamentals",
                {"ticker": "AAPL", "data_fields": ["price", "volume", "market_cap"]},
            )

            assert result is not None
            mock_client.assert_called_once()

        # Test multiple stocks
        with patch.object(
            FinvizClient, "get_multiple_stocks_fundamentals"
        ) as mock_client:
            mock_client.return_value = [self.stock_data]

            result = await server.call_tool(
                "get_multiple_stocks_fundamentals",
                {"tickers": ["AAPL", "MSFT"], "data_fields": ["price", "volume"]},
            )

            assert result is not None
            mock_client.assert_called_once()

    @pytest.mark.asyncio
    async def test_stock_fundamentals_renders_margin_values(self):
        """Margin values must be rendered, not just listed as field names."""
        with patch.object(FinvizClient, "get_stock_fundamentals") as mock_client:
            mock_client.return_value = {
                "ticker": "AAPL",
                "gross_margin": 47.86,
                "operating_margin": 32.64,
                "profit_margin": 27.15,
            }

            result = await server.call_tool(
                "get_stock_fundamentals",
                {
                    "ticker": "AAPL",
                    "data_fields": [
                        "gross_margin",
                        "operating_margin",
                        "profit_margin",
                    ],
                },
            )

            text = _first_text(result)
            assert "47.86" in text, "gross_margin value not rendered"
            assert "32.64" in text, "operating_margin value not rendered"
            assert "27.15" in text, "profit_margin value not rendered"

    @pytest.mark.asyncio
    async def test_stock_fundamentals_renders_return_values(self):
        """ROE/ROA/ROIC values must be rendered, not just listed as field names."""
        with patch.object(FinvizClient, "get_stock_fundamentals") as mock_client:
            mock_client.return_value = {
                "ticker": "AAPL",
                "return_on_equity": 141.47,
                "return_on_assets": 34.91,
                "return_on_invested_capital": 67.76,
            }

            result = await server.call_tool(
                "get_stock_fundamentals",
                {
                    "ticker": "AAPL",
                    "data_fields": [
                        "return_on_equity",
                        "return_on_assets",
                        "return_on_invested_capital",
                    ],
                },
            )

            text = _first_text(result)
            assert "141.47" in text, "return_on_equity value not rendered"
            assert "34.91" in text, "return_on_assets value not rendered"
            assert "67.76" in text, "return_on_invested_capital value not rendered"

    def test_net_margin_is_valid_data_field(self):
        """net_margin is a Finviz synonym for profit_margin and must validate."""
        from src.utils.validators import validate_data_fields

        assert validate_data_fields(["net_margin"]) == []

    def test_net_margin_resolves_to_profit_margin_value(self):
        """Requesting net_margin returns the Profit Margin column value."""
        import pandas as pd

        client = FinvizClient(api_key="test_key")
        fake_df = pd.DataFrame({"Ticker": ["AAPL"], "Profit Margin": [27.15]})

        with patch.object(client, "_fetch_csv_from_url", return_value=fake_df):
            result = client.get_stock_fundamentals("AAPL", ["net_margin"])

        assert result["net_margin"] == 27.15

    @pytest.mark.asyncio
    async def test_net_margin_value_is_rendered(self):
        """An explicit net_margin request renders under Profit Margin."""
        with patch.object(FinvizClient, "get_stock_fundamentals") as mock_client:
            mock_client.return_value = {"ticker": "AAPL", "net_margin": 27.15}

            result = await server.call_tool(
                "get_stock_fundamentals",
                {"ticker": "AAPL", "data_fields": ["net_margin"]},
            )

            assert "27.15" in _first_text(result)

    @pytest.mark.asyncio
    async def test_multiple_fundamentals_renders_profitability_and_returns(self):
        """Bulk fundamentals must render margin and ROE/ROA/ROIC values."""
        with patch.object(
            FinvizClient, "get_multiple_stocks_fundamentals"
        ) as mock_client:
            mock_client.return_value = [
                {
                    "ticker": "AAPL",
                    "company": "Apple Inc.",
                    "gross_margin": 47.86,
                    "operating_margin": 32.64,
                    "profit_margin": 27.15,
                    "return_on_equity": 141.47,
                    "return_on_assets": 34.91,
                    "return_on_invested_capital": 67.76,
                }
            ]

            result = await server.call_tool(
                "get_multiple_stocks_fundamentals",
                {
                    "tickers": ["AAPL"],
                    "data_fields": [
                        "gross_margin",
                        "operating_margin",
                        "profit_margin",
                        "return_on_equity",
                        "return_on_assets",
                        "return_on_invested_capital",
                    ],
                },
            )

            text = _first_text(result)
            for expected in ["47.86", "32.64", "27.15", "141.47", "34.91", "67.76"]:
                assert expected in text, f"{expected} not rendered in bulk output"

    def test_multiple_fundamentals_net_margin_resolves(self):
        """Bulk path resolves net_margin to the Profit Margin column value."""
        import pandas as pd

        client = FinvizClient(api_key="test_key")
        fake_df = pd.DataFrame({"Ticker": ["AAPL"], "Profit Margin": [27.15]})

        with patch.object(client, "_fetch_csv_from_url", return_value=fake_df):
            results = client.get_multiple_stocks_fundamentals("AAPL".split(), ["net_margin"])

        assert results[0]["net_margin"] == 27.15

    def test_absolute_52w_prices_computed_from_relative(self):
        """week_52_high/low absolute prices are derived from price + relative %."""
        import pandas as pd

        client = FinvizClient(api_key="test_key")
        fake_df = pd.DataFrame(
            {
                "Ticker": ["MSFT"],
                "Price": [386.74],
                "52-Week High": ["-30.37%"],
                "52-Week Low": ["10.75%"],
            }
        )

        with patch.object(client, "_fetch_csv_from_url", return_value=fake_df):
            result = client.get_stock_fundamentals("MSFT")

        assert result["week_52_high"] == pytest.approx(555.42, abs=0.05)
        assert result["week_52_low"] == pytest.approx(349.20, abs=0.05)

    @pytest.mark.asyncio
    async def test_52w_absolute_prices_rendered(self):
        """The Technical section renders absolute 52W high/low, not the relative %."""
        with patch.object(FinvizClient, "get_stock_fundamentals") as mock_client:
            mock_client.return_value = {
                "ticker": "MSFT",
                "week_52_high": 555.42,
                "week_52_low": 349.20,
            }

            result = await server.call_tool(
                "get_stock_fundamentals",
                {"ticker": "MSFT", "data_fields": ["week_52_high", "week_52_low"]},
            )

            text = _first_text(result)
            assert "555.42" in text
            assert "349.20" in text or "349.2" in text

    def test_percent_string_fields_normalized_to_floats(self):
        """A "%"-string field is normalized to a bare float even when its name
        matches no numeric keyword."""
        import pandas as pd

        client = FinvizClient(api_key="test_key")
        fake_df = pd.DataFrame(
            {"Ticker": ["MSFT"], "Insider Ownership": ["1.53%"]}
        )

        with patch.object(client, "_fetch_csv_from_url", return_value=fake_df):
            result = client.get_stock_fundamentals("MSFT")

        assert result["insider_ownership"] == 1.53
        assert isinstance(result["insider_ownership"], float)

    @pytest.mark.asyncio
    async def test_percent_fields_labelled_with_bare_float_values(self):
        """Percentage fields render as "Label (%): <bare float>" (no % on value)."""
        with patch.object(FinvizClient, "get_stock_fundamentals") as mock_client:
            mock_client.return_value = {
                "ticker": "MSFT",
                "gross_margin": 68.31,
                "volatility_week": 3.11,
            }

            result = await server.call_tool(
                "get_stock_fundamentals",
                {"ticker": "MSFT", "data_fields": ["gross_margin", "volatility_week"]},
            )

            text = _first_text(result)
            assert "Gross Margin (%)" in text
            assert "Volatility (%)" in text
            # value is a bare float, the "%" is not appended to the number
            assert "68.31" in text and "68.31%" not in text

    @pytest.mark.asyncio
    async def test_valuation_extras_rendered(self):
        """P/C, P/FCF, EV/EBITDA, EV/Sales render in the Valuation section."""
        with patch.object(FinvizClient, "get_stock_fundamentals") as mock_client:
            mock_client.return_value = {
                "ticker": "MSFT",
                "p_cash": 36.70,
                "p_free_cash_flow": 39.40,
                "ev_ebitda": 15.16,
                "ev_sales": 9.17,
            }

            result = await server.call_tool(
                "get_stock_fundamentals",
                {"ticker": "MSFT", "data_fields": ["p_cash"]},
            )

            text = _first_text(result)
            for expected in ["P/C", "P/FCF", "EV/EBITDA", "EV/Sales", "36.70", "15.16"]:
                assert expected in text, f"{expected} missing from valuation output"

    @pytest.mark.asyncio
    async def test_longterm_performance_rendered(self):
        """3Y/5Y/10Y performance render in the Performance section."""
        with patch.object(FinvizClient, "get_stock_fundamentals") as mock_client:
            mock_client.return_value = {
                "ticker": "MSFT",
                "performance_3_years": 13.32,
                "performance_5_years": 39.29,
                "performance_10_years": 652.71,
            }

            result = await server.call_tool(
                "get_stock_fundamentals",
                {"ticker": "MSFT", "data_fields": ["performance_3_years"]},
            )

            text = _first_text(result)
            for expected in ["3 Years (%)", "5 Years (%)", "10 Years (%)", "652.71"]:
                assert expected in text, f"{expected} missing from performance output"

    @pytest.mark.asyncio
    async def test_financial_health_section_rendered(self):
        """Quick/Current Ratio and Debt/Equity render in a Financial Health section."""
        with patch.object(FinvizClient, "get_stock_fundamentals") as mock_client:
            mock_client.return_value = {
                "ticker": "MSFT",
                "quick_ratio": 1.27,
                "current_ratio": 1.28,
                "total_debt_equity": 0.30,
                "lt_debt_equity": 0.26,
            }

            result = await server.call_tool(
                "get_stock_fundamentals",
                {"ticker": "MSFT", "data_fields": ["quick_ratio"]},
            )

            text = _first_text(result)
            for expected in ["Financial Health", "Quick Ratio", "LT Debt/Equity", "1.27"]:
                assert expected in text, f"{expected} missing from financial health output"

    @pytest.mark.asyncio
    async def test_dividends_section_rendered(self):
        """Dividend amount/TTM/ex-date/payout/growth render in a Dividends section."""
        with patch.object(FinvizClient, "get_stock_fundamentals") as mock_client:
            mock_client.return_value = {
                "ticker": "MSFT",
                "dividend": 3.68,
                "dividend_ttm": 3.56,
                "dividend_ex_date": "8/20/2026",
                "payout_ratio": 24.34,
                "dividend_growth_3_years": 10.21,
                "dividend_growth_5_years": 10.23,
            }

            result = await server.call_tool(
                "get_stock_fundamentals",
                {"ticker": "MSFT", "data_fields": ["dividend_ttm"]},
            )

            text = _first_text(result)
            for expected in ["Dividends", "Payout (%)", "Ex-Date", "8/20/2026", "24.34"]:
                assert expected in text, f"{expected} missing from dividends output"

    @pytest.mark.asyncio
    async def test_news_tools_interface(self):
        """Test news-related tools interface.

        Parameters are aligned to current implementations:
        - ``get_stock_news(tickers, days_back, news_type)``
        - ``get_market_news(days_back, max_items)``
        - ``get_sector_news(sector, days_back, max_items)``

        FastMCP silently ignores unknown extras, so passing the legacy
        ``limit`` / ``category`` keys would false-pass without exercising
        the real signature.
        """
        # Stock news
        with patch.object(FinvizNewsClient, "get_stock_news") as mock_news:
            mock_news.return_value = self.news_data

            result = await server.call_tool(
                "get_stock_news",
                {
                    "tickers": "AAPL",
                    "days_back": 7,
                },
            )

            assert result is not None
            assert "News for AAPL" in _first_text(result)
            mock_news.assert_called_once()

        # Market news
        with patch.object(FinvizNewsClient, "get_market_news") as mock_news:
            mock_news.return_value = self.news_data

            result = await server.call_tool(
                "get_market_news",
                {
                    "days_back": 3,
                    "max_items": 20,
                },
            )

            assert result is not None
            assert "Market News" in _first_text(result)
            mock_news.assert_called_once()

        # Sector news
        with patch.object(FinvizNewsClient, "get_sector_news") as mock_news:
            mock_news.return_value = self.news_data

            result = await server.call_tool(
                "get_sector_news",
                {
                    "sector": "Technology",
                    "days_back": 5,
                    "max_items": 15,
                },
            )

            assert result is not None
            assert "Technology Sector News" in _first_text(result)
            mock_news.assert_called_once()

    @pytest.mark.asyncio
    async def test_sector_analysis_interface(self):
        """Test sector analysis tools interface.

        Parameters aligned to current signatures:
        - ``get_sector_performance(sectors=None)``
        - ``get_industry_performance(industries=None)``
        - ``get_country_performance(countries=None)``
        """
        # Sector performance
        with patch.object(
            FinvizSectorAnalysisClient, "get_sector_performance"
        ) as mock_sector:
            mock_sector.return_value = self.sector_data

            result = await server.call_tool(
                "get_sector_performance",
                {
                    "sectors": ["Technology"],
                },
            )

            assert result is not None
            assert "Sector Performance Analysis" in _first_text(result)
            mock_sector.assert_called_once()

        # Industry performance
        with patch.object(
            FinvizSectorAnalysisClient, "get_industry_performance"
        ) as mock_industry:
            mock_industry.return_value = self.industry_data

            result = await server.call_tool(
                "get_industry_performance",
                {
                    "industries": ["software_application"],
                },
            )

            assert result is not None
            assert "Industry Performance Analysis" in _first_text(result)
            mock_industry.assert_called_once()

        # Country performance
        with patch.object(
            FinvizSectorAnalysisClient, "get_country_performance"
        ) as mock_country:
            mock_country.return_value = self.country_data

            result = await server.call_tool(
                "get_country_performance",
                {
                    "countries": ["usa"],
                },
            )

            assert result is not None
            assert "Country Performance Analysis" in _first_text(result)
            mock_country.assert_called_once()

    @pytest.mark.asyncio
    async def test_screener_tools_interface(self):
        """Test screener tools interface."""
        mock_screener_result = [_make_upcoming_earnings_stock()]

        # ``volume_surge_screener`` is parameterless (fixed criteria) and the
        # other screeners listed here own their own validation; we stick with
        # parameter sets that match the current implementation contracts.
        direct_method_tests = [
            (
                "earnings_screener",
                "earnings_screener",
                {"earnings_date": "today_after"},
            ),
            ("volume_surge_screener", "volume_surge_screener", {}),
            ("trend_reversion_screener", "trend_reversion_screener", {}),
            ("uptrend_screener", "uptrend_screener", {}),
            ("dividend_growth_screener", "dividend_growth_screener", {}),
            ("etf_screener", "etf_screener", {}),
            ("upcoming_earnings_screener", "upcoming_earnings_screener", {}),
        ]

        for tool_name, screener_method, params in direct_method_tests:
            with patch.object(FinvizScreener, screener_method) as mock_screener:
                mock_screener.return_value = mock_screener_result

                result = await server.call_tool(tool_name, params)
                assert result is not None
                mock_screener.assert_called_once()

        for tool_name, params in [
            ("get_relative_volume_stocks", {"min_relative_volume": 1.5}),
            ("technical_analysis_screener", {}),
        ]:
            with patch.object(FinvizScreener, "screen_stocks") as mock_screen:
                mock_screen.return_value = mock_screener_result

                result = await server.call_tool(tool_name, params)
                assert result is not None
                mock_screen.assert_called_once()


class TestMCPErrorHandling:
    """Test MCP-specific error handling."""

    @pytest.mark.asyncio
    async def test_tool_not_found_error(self):
        """Test handling of non-existent tool calls."""
        with pytest.raises(McpToolError):
            await server.call_tool("non_existent_tool", {})

    @pytest.mark.asyncio
    async def test_malformed_tool_call(self):
        """Test handling of malformed tool calls."""
        # Test with invalid parameters structure (string instead of dict)
        with pytest.raises((McpToolError, ValueError, TypeError)):
            await server.call_tool("earnings_screener", "invalid_params")

    @pytest.mark.asyncio
    async def test_tool_execution_error_propagation(self):
        """Test that tool execution errors are properly propagated."""
        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.side_effect = Exception("Screener error")

            with pytest.raises(McpToolError):
                await server.call_tool(
                    "earnings_screener", {"earnings_date": "today_after"}
                )

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Skipped: server has no cancellable timeout policy.

        ``server.call_tool`` dispatches synchronous screener methods
        directly, so neither an ``async def`` side_effect (yields an
        unawaited coroutine through Mock; emits RuntimeWarning) nor a
        synchronous ``time.sleep`` (blocks the event loop so
        ``asyncio.wait_for`` cannot deliver a TimeoutError) can prove
        timeout behavior with the current implementation. Re-enable
        when the server gains a real cancellable path (e.g.
        ``asyncio.to_thread`` offload or an explicit deadline).
        """
        pytest.skip(
            "Server has no cancellable timeout policy yet. "
            "MCP tools dispatch synchronous screener methods directly, so "
            "asyncio.wait_for cannot interrupt a running call. Re-enable "
            "this assertion when server.call_tool offloads sync work to a "
            "thread (e.g. asyncio.to_thread) or honors an explicit deadline."
        )


class TestMCPDataSerialization:
    """Test data serialization and formatting for MCP responses."""

    @pytest.mark.asyncio
    async def test_response_formatting(self):
        """Test that responses are properly formatted for MCP."""
        mock_result = [factories.make_stock_data()]

        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.return_value = mock_result

            result = await server.call_tool(
                "earnings_screener", {"earnings_date": "today_after"}
            )

            assert result is not None

            # Result should be serializable
            content = _content_list(result)
            for item in content:
                if hasattr(item, "text"):
                    # If it's TextContent, the text should be JSON serializable
                    try:
                        json.loads(item.text)
                    except (json.JSONDecodeError, AttributeError):
                        # If not JSON, should at least be a string
                        assert isinstance(item.text, str)

    @pytest.mark.asyncio
    async def test_special_character_serialization(self):
        """Test serialization of responses with special characters."""
        mock_result = [
            factories.make_stock_data(
                ticker="TEST",
                company_name="Test Company™ & Co.",
                sector="Technology/Software",
            )
        ]

        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.return_value = mock_result

            result = await server.call_tool(
                "earnings_screener", {"earnings_date": "today_after"}
            )

            assert result is not None
            assert "Test Company™ & Co." in _first_text(result)

    @pytest.mark.asyncio
    async def test_large_dataset_serialization(self):
        """Test serialization of large datasets."""
        # Create a large mock dataset
        large_mock_result = [
            factories.make_stock_data(
                ticker=f"S{i:04d}",
                company_name=f"Company {i}",
                price=100.0 + i,
                volume=1_000_000 + i,
            )
            for i in range(500)
        ]

        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.return_value = large_mock_result

            result = await server.call_tool(
                "earnings_screener", {"earnings_date": "today_after"}
            )

            assert result is not None
            assert "500 stocks found" in _first_text(result)


class TestMCPConcurrency:
    """Test MCP server concurrency handling."""

    @pytest.mark.asyncio
    async def test_concurrent_tool_calls(self):
        """Test handling of concurrent tool calls."""
        mock_result = [factories.make_stock_data()]

        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.return_value = mock_result

            # Create multiple concurrent tool calls
            tasks = []
            for i in range(5):
                task = server.call_tool(
                    "earnings_screener", {"earnings_date": "today_after"}
                )
                tasks.append(task)

            # Execute all concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # All should succeed
            for result in results:
                assert not isinstance(result, Exception)
                assert result is not None

    @pytest.mark.asyncio
    async def test_mixed_concurrent_tools(self):
        """Test concurrent calls to different tools."""
        mock_stock_result = [factories.make_stock_data()]
        mock_news_result = [factories.make_news_data()]
        mock_sector_result = [
            {
                "name": "Technology",
                "market_cap": "$12.3T",
                "pe_ratio": "28.4",
                "dividend_yield": "0.7%",
                "change": "1.2%",
                "stocks": "760",
            }
        ]

        with (
            patch.object(FinvizScreener, "earnings_screener") as mock_earnings,
            patch.object(FinvizNewsClient, "get_market_news") as mock_news,
            patch.object(
                FinvizSectorAnalysisClient, "get_sector_performance"
            ) as mock_sector,
        ):

            mock_earnings.return_value = mock_stock_result
            mock_news.return_value = mock_news_result
            mock_sector.return_value = mock_sector_result

            # Create concurrent calls to different tools
            tasks = [
                server.call_tool("earnings_screener", {"earnings_date": "today_after"}),
                server.call_tool("get_market_news", {"max_items": 10}),
                server.call_tool("get_sector_performance", {"sectors": ["Technology"]}),
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # All should succeed
            for result in results:
                assert not isinstance(result, Exception)
                assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
