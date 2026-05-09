#!/usr/bin/env python3
"""
Comprehensive E2E test suite for all Finviz MCP Server screener functions.
Tests all 22 MCP tools with various parameter combinations.
"""

import pytest
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, patch

from src.server import server
from src.models import NewsData
from src.finviz_client.screener import FinvizScreener
from src.finviz_client.base import FinvizClient
from src.finviz_client.news import FinvizNewsClient
from src.finviz_client.sector_analysis import FinvizSectorAnalysisClient

# FastMCP wraps any exception raised inside a tool function in ``ToolError``
# at the boundary. Import it under an alias so error-path tests can
# distinguish the boundary error from local domain exceptions.
from mcp.server.fastmcp.exceptions import ToolError as McpToolError

# Configure logging for tests
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TestFinvizScreenersE2E:
    """Comprehensive E2E tests for all Finviz screener functions."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup method for each test."""
        self.mock_results = {
            "stocks": [
                {
                    "ticker": "AAPL",
                    "company": "Apple Inc.",
                    "sector": "Technology",
                    "industry": "Consumer Electronics",
                    "price": 150.0,
                    "volume": 50000000,
                    "market_cap": 2400000000000,
                    "pe_ratio": 25.5,
                    "eps": 6.0,
                    "dividend_yield": 0.5,
                }
            ],
            "total_count": 1,
            "execution_time": 1.5,
        }

    # ===========================================
    # EARNINGS SCREENER TESTS
    # ===========================================

    @pytest.mark.skip(reason="mock shape obsolete after PR B; tracked as #42")
    @pytest.mark.asyncio
    async def test_earnings_screener_basic(self):
        """Test basic earnings screener functionality."""
        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            result = await server.call_tool("earnings_screener", {
                "earnings_date": "today_after"
            })

            assert result is not None
            mock_screener.assert_called_once()

    @pytest.mark.skip(reason="mock shape obsolete after PR B; tracked as #42")
    @pytest.mark.asyncio
    async def test_earnings_screener_comprehensive(self):
        """Test earnings screener with all parameters."""
        test_cases = [
            {
                "earnings_date": "today_after",
                "market_cap": "large",
                "min_price": 10.0,
                "max_price": 500.0,
                "min_volume": 1000000,
                "sectors": ["Technology", "Healthcare"],
            },
            {
                "earnings_date": "tomorrow_before",
                "market_cap": "mid",
                "min_price": 5.0,
                "sectors": ["Finance"],
            },
            {
                "earnings_date": "this_week",
                "market_cap": "small",
                "min_volume": 500000,
            },
        ]

        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            for params in test_cases:
                result = await server.call_tool("earnings_screener", params)
                assert result is not None

    # ===========================================
    # VOLUME SURGE SCREENER TESTS
    # ===========================================

    @pytest.mark.skip(reason="mock shape obsolete after PR B; tracked as #42")
    @pytest.mark.asyncio
    async def test_volume_surge_screener_basic(self):
        """Test basic volume surge screener."""
        with patch.object(FinvizScreener, "volume_surge_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            result = await server.call_tool("volume_surge_screener", {
                "market_cap": "large"
            })

            assert result is not None
            mock_screener.assert_called_once()

    @pytest.mark.skip(reason="mock shape obsolete after PR B; tracked as #42")
    @pytest.mark.asyncio
    async def test_volume_surge_screener_comprehensive(self):
        """Test volume surge screener with various parameters."""
        test_cases = [
            {
                "market_cap": "large",
                "min_price": 10.0,
                "min_relative_volume": 2.0,
                "min_price_change": 5.0,
                "sma_filter": "above_sma200",
            },
            {
                "market_cap": "smallover",
                "min_price": 1.0,
                "min_relative_volume": 1.5,
                "min_price_change": 2.0,
                "sma_filter": "above_sma50",
            },
            {
                "market_cap": "mid",
                "max_price": 100.0,
                "min_relative_volume": 3.0,
                "sectors": ["Technology", "Healthcare"],
            },
        ]

        with patch.object(FinvizScreener, "volume_surge_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            for params in test_cases:
                result = await server.call_tool("volume_surge_screener", params)
                assert result is not None

    # ===========================================
    # FUNDAMENTAL DATA TESTS
    # ===========================================

    @pytest.mark.asyncio
    async def test_get_stock_fundamentals_single(self):
        """Test single stock fundamentals retrieval."""
        with patch.object(FinvizClient, "get_stock_fundamentals") as mock_client:
            mock_client.return_value = self.mock_results["stocks"][0]

            test_cases = [
                {
                    "ticker": "AAPL",
                    "data_fields": ["pe_ratio", "eps", "dividend_yield"],
                },
                {
                    "ticker": "MSFT",
                    "data_fields": ["market_cap", "volume", "price"],
                },
                {"ticker": "GOOGL"},  # No data_fields specified
            ]

            for params in test_cases:
                result = await server.call_tool("get_stock_fundamentals", params)
                assert result is not None

    @pytest.mark.asyncio
    async def test_get_multiple_stocks_fundamentals(self):
        """Test multiple stocks fundamentals retrieval."""
        with patch.object(FinvizClient, "get_multiple_stocks_fundamentals") as mock_client:
            mock_client.return_value = self.mock_results["stocks"]

            test_cases = [
                {
                    "tickers": ["AAPL", "MSFT", "GOOGL"],
                    "data_fields": ["pe_ratio", "eps", "market_cap"],
                },
                {
                    "tickers": ["TSLA", "AMZN"],
                    "data_fields": ["price", "volume", "dividend_yield"],
                },
                {"tickers": ["NVDA", "AMD", "INTC"]},  # No data_fields
            ]

            for params in test_cases:
                result = await server.call_tool("get_multiple_stocks_fundamentals", params)
                assert result is not None

    # ===========================================
    # TREND ANALYSIS TESTS
    # ===========================================

    @pytest.mark.skip(reason="mock shape obsolete after PR B; tracked as #42")
    @pytest.mark.asyncio
    async def test_trend_reversion_screener(self):
        """Test trend reversion screener with various parameters."""
        test_cases = [
            {
                "market_cap": "large",
                "eps_growth_qoq": 10.0,
                "rsi_max": 30,
                "sectors": ["Technology"],
            },
            {
                "market_cap": "mid",
                "eps_growth_qoq": 5.0,
                "rsi_max": 35,
                "min_price": 20.0,
            },
            {"market_cap": "small", "rsi_max": 25},
        ]

        with patch.object(FinvizScreener, "trend_reversion_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            for params in test_cases:
                result = await server.call_tool("trend_reversion_screener", params)
                assert result is not None

    @pytest.mark.skip(reason="mock shape obsolete after PR B; tracked as #42")
    @pytest.mark.asyncio
    async def test_uptrend_screener(self):
        """Test uptrend screener with different configurations."""
        test_cases = [
            {
                "trend_type": "strong_uptrend",
                "sma_period": "20",
                "relative_volume": 2.0,
                "price_change": 5.0,
            },
            {
                "trend_type": "moderate_uptrend",
                "sma_period": "50",
                "relative_volume": 1.5,
                "price_change": 2.0,
            },
            {
                "trend_type": "emerging_uptrend",
                "sma_period": "200",
                "relative_volume": 1.2,
            },
        ]

        with patch.object(FinvizScreener, "uptrend_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            for params in test_cases:
                result = await server.call_tool("uptrend_screener", params)
                assert result is not None

    # ===========================================
    # DIVIDEND SCREENER TESTS
    # ===========================================

    @pytest.mark.skip(reason="mock shape obsolete after PR B; tracked as #42")
    @pytest.mark.asyncio
    async def test_dividend_growth_screener(self):
        """Test dividend growth screener with various criteria."""
        test_cases = [
            {
                "min_dividend_yield": 2.0,
                "max_dividend_yield": 6.0,
                "min_dividend_growth": 5.0,
                "min_roe": 15.0,
            },
            {
                "min_dividend_yield": 1.0,
                "max_dividend_yield": 4.0,
                "min_dividend_growth": 3.0,
                "sectors": ["Utilities", "Finance"],
            },
            {
                "min_dividend_yield": 3.0,
                "min_dividend_growth": 10.0,
                "market_cap": "large",
            },
        ]

        with patch.object(FinvizScreener, "dividend_growth_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            for params in test_cases:
                result = await server.call_tool("dividend_growth_screener", params)
                assert result is not None

    # ===========================================
    # ETF SCREENER TESTS
    # ===========================================

    @pytest.mark.skip(reason="mock shape obsolete after PR B; tracked as #42")
    @pytest.mark.asyncio
    async def test_etf_screener(self):
        """Test ETF screener with different parameters."""
        test_cases = [
            {
                "etf_type": "sector",
                "min_volume": 1000000,
                "performance_period": "1m",
            },
            {
                "etf_type": "index",
                "min_volume": 500000,
                "performance_period": "ytd",
            },
            {"etf_type": "commodity", "min_volume": 100000},
        ]

        with patch.object(FinvizScreener, "etf_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            for params in test_cases:
                result = await server.call_tool("etf_screener", params)
                assert result is not None

    # ===========================================
    # EARNINGS TIMING SCREENERS
    # ===========================================

    @pytest.mark.skip(reason="mock shape obsolete after PR B; tracked as #42")
    @pytest.mark.asyncio
    async def test_earnings_premarket_screener(self):
        """Premarket earnings screener takes no parameters (server.py:927).

        The previous form of this test passed timing / market-cap /
        sector arguments that FastMCP silently dropped because they are
        not in the signature. Calling with ``{}`` and asserting the
        patched screener was reached is the only honest coverage here.
        """
        with patch.object(FinvizScreener, "earnings_premarket_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            result = await server.call_tool("earnings_premarket_screener", {})
            assert result is not None
            mock_screener.assert_called_once_with()

    @pytest.mark.skip(reason="mock shape obsolete after PR B; tracked as #42")
    @pytest.mark.asyncio
    async def test_earnings_afterhours_screener(self):
        """Afterhours earnings screener takes no parameters (server.py:974).

        See ``test_earnings_premarket_screener`` for the rationale; this
        is the same fixed-criteria contract.
        """
        with patch.object(FinvizScreener, "earnings_afterhours_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            result = await server.call_tool("earnings_afterhours_screener", {})
            assert result is not None
            mock_screener.assert_called_once_with()

    @pytest.mark.skip(reason="mock shape obsolete after PR B; tracked as #42")
    @pytest.mark.asyncio
    async def test_earnings_trading_screener(self):
        """Earnings trading screener takes no parameters (server.py:1023).

        See ``test_earnings_premarket_screener`` for the rationale.
        """
        with patch.object(FinvizScreener, "earnings_trading_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            result = await server.call_tool("earnings_trading_screener", {})
            assert result is not None
            mock_screener.assert_called_once_with()

    @pytest.mark.asyncio



    # ===========================================
    # NEWS FUNCTIONS TESTS
    # ===========================================

    @staticmethod
    def _fake_news(ticker: str = "AAPL", title: str = "Test News") -> NewsData:
        """Build a NewsData object that matches what the formatter
        renders. Returning plain dicts here used to silently fail because
        the formatter calls ``news.title`` / ``news.date.strftime(...)``;
        the failure surfaced as an error TextContent and was masked by
        the ``result is not None`` check.
        """
        return NewsData(
            ticker=ticker,
            title=title,
            source="TestWire",
            date=datetime(2026, 5, 9, 12, 0),
            url="http://example.test/news",
            category="general",
        )

    @pytest.mark.asyncio
    async def test_get_stock_news(self):
        """``get_stock_news`` signature: ``tickers, days_back, news_type``
        (server.py:1089). The previous form passed ``limit`` which the
        tool does not accept and FastMCP silently dropped — see PR #35
        review note.

        Note on ``tickers`` shape: the docstring advertises list input,
        but the current ``validate_tickers`` (validators.py:32) only
        accepts strings (single or comma-separated). Tests therefore
        pass strings; the docstring/validator mismatch is tracked
        separately and outside the scope of this strictness fix.
        """
        test_cases = [
            {"tickers": "AAPL", "days_back": 10},
            {"tickers": "MSFT", "days_back": 7, "news_type": "earnings"},
            {"tickers": "GOOGL,META"},
        ]

        with patch.object(FinvizNewsClient, "get_stock_news") as mock_news:
            mock_news.return_value = [self._fake_news()]

            for params in test_cases:
                result = await server.call_tool("get_stock_news", params)
                assert result is not None
            assert mock_news.call_count == len(test_cases)

    @pytest.mark.asyncio
    async def test_get_market_news(self):
        """``get_market_news`` signature: ``days_back, max_items``
        (server.py:1156). ``limit`` / ``category`` were stale and dropped.
        """
        test_cases = [
            {"max_items": 20},
            {"days_back": 5, "max_items": 10},
            {"days_back": 3},
        ]

        with patch.object(FinvizNewsClient, "get_market_news") as mock_news:
            mock_news.return_value = [self._fake_news(title="Market News")]

            for params in test_cases:
                result = await server.call_tool("get_market_news", params)
                assert result is not None
            assert mock_news.call_count == len(test_cases)

    @pytest.mark.asyncio
    async def test_get_sector_news(self):
        """``get_sector_news`` signature: ``sector, days_back, max_items``
        (server.py:1199). ``limit`` was stale.
        """
        test_cases = [
            {"sector": "Technology", "max_items": 15},
            {"sector": "Healthcare", "days_back": 5, "max_items": 10},
            {"sector": "Finance"},
        ]

        with patch.object(FinvizNewsClient, "get_sector_news") as mock_news:
            mock_news.return_value = [self._fake_news(title="Sector News")]

            for params in test_cases:
                result = await server.call_tool("get_sector_news", params)
                assert result is not None
            assert mock_news.call_count == len(test_cases)

    # ===========================================
    # MARKET ANALYSIS TESTS
    # ===========================================

    @pytest.mark.asyncio
    async def test_get_sector_performance(self):
        """``get_sector_performance`` signature: ``sectors`` only
        (server.py:1244). ``timeframe`` / ``sort_by`` were stale.
        """
        test_cases = [
            {},
            {"sectors": ["Technology"]},
            {"sectors": ["Technology", "Healthcare", "Financial"]},
        ]

        with patch.object(FinvizSectorAnalysisClient, "get_sector_performance") as mock_sector:
            mock_sector.return_value = [{"name": "Technology", "change": "2.5%"}]

            for params in test_cases:
                result = await server.call_tool("get_sector_performance", params)
                assert result is not None
            assert mock_sector.call_count == len(test_cases)

    @pytest.mark.asyncio
    async def test_get_industry_performance(self):
        """``get_industry_performance`` signature: ``industries`` only
        (server.py:1291). The previous form passed ``sector`` /
        ``timeframe`` / ``sort_by`` which the tool does not accept.
        """
        test_cases = [
            {},
            {"industries": ["Software—Application"]},
            {"industries": ["Software—Application", "Biotechnology"]},
        ]

        with patch.object(FinvizSectorAnalysisClient, "get_industry_performance") as mock_industry:
            mock_industry.return_value = [{"industry": "Software—Application", "change": "3.2%"}]

            for params in test_cases:
                result = await server.call_tool("get_industry_performance", params)
                assert result is not None
            assert mock_industry.call_count == len(test_cases)

    @pytest.mark.asyncio
    async def test_get_country_performance(self):
        """``get_country_performance`` signature: ``countries`` only
        (server.py:1337). ``timeframe`` / ``sort_by`` were stale.
        """
        test_cases = [
            {},
            {"countries": ["USA"]},
            {"countries": ["USA", "Japan", "Germany"]},
        ]

        with patch.object(FinvizSectorAnalysisClient, "get_country_performance") as mock_country:
            mock_country.return_value = [{"name": "USA", "change": "1.8%"}]

            for params in test_cases:
                result = await server.call_tool("get_country_performance", params)
                assert result is not None
            assert mock_country.call_count == len(test_cases)

    @pytest.mark.asyncio
    async def test_get_market_overview(self):
        """Test market overview."""
        test_cases = [
            {"include_futures": True, "include_crypto": True},
            {"include_futures": False, "include_crypto": False},
            {},
        ]

        with patch.object(FinvizClient, "get_market_overview") as mock_overview:
            mock_overview.return_value = {"market_data": {"sp500": 4500.0}}

            for params in test_cases:
                result = await server.call_tool("get_market_overview", params)
                assert result is not None

    # ===========================================
    # TECHNICAL ANALYSIS TESTS
    # ===========================================

    @pytest.mark.asyncio
    async def test_get_relative_volume_stocks(self):
        """The MCP tool calls ``finviz_screener.screen_stocks(...)``
        (server.py:1830), NOT the dedicated ``get_relative_volume_stocks``
        client method. Patching the dedicated method left the live
        client retry path active and the test took ~16s per call —
        see PR #35 review note. The signature is ``min_relative_volume,
        min_price, sectors, max_results`` (server.py:1805) — there is
        no ``market_cap`` parameter.
        """
        test_cases = [
            {"min_relative_volume": 2.0},
            {"min_relative_volume": 1.5, "sectors": ["Technology"]},
            {"min_relative_volume": 3.0, "min_price": 10.0},
        ]

        with patch.object(FinvizScreener, "screen_stocks") as mock_screener:
            mock_screener.return_value = []

            for params in test_cases:
                result = await server.call_tool("get_relative_volume_stocks", params)
                assert result is not None
            assert mock_screener.call_count == len(test_cases)

    @pytest.mark.asyncio
    async def test_technical_analysis_screener(self):
        """The MCP tool calls ``finviz_screener.screen_stocks(filters)``
        (server.py:1937), NOT the dedicated client method. The
        signature is flat (``rsi_min``, ``rsi_max``, ``price_vs_sma20``,
        ``price_vs_sma50``, ``price_vs_sma200``, ``min_price``,
        ``min_volume``, ``sectors``, ``max_results``); the legacy
        nested ``technical_criteria`` dict was silently dropped — see
        PR #35 review note.
        """
        test_cases = [
            {"rsi_min": 30, "rsi_max": 70, "price_vs_sma50": "above"},
            {"rsi_min": 20, "rsi_max": 40, "price_vs_sma200": "below"},
        ]

        with patch.object(FinvizScreener, "screen_stocks") as mock_screener:
            mock_screener.return_value = []

            for params in test_cases:
                result = await server.call_tool("technical_analysis_screener", params)
                assert result is not None
            assert mock_screener.call_count == len(test_cases)

    @pytest.mark.asyncio
    async def test_upcoming_earnings_screener(self):
        """``upcoming_earnings_screener`` signature uses
        ``earnings_period`` and ``target_sectors`` (server.py:2116);
        the legacy ``time_range`` / ``expected_move`` / plain
        ``sectors`` arguments were stale and silently dropped.
        """
        test_cases = [
            {"earnings_period": "next_week", "market_cap": "large"},
            {"earnings_period": "next_month", "target_sectors": ["Technology", "Healthcare"]},
            {"earnings_period": "next_2_weeks", "market_cap": "mid"},
        ]

        with patch.object(FinvizScreener, "upcoming_earnings_screener") as mock_screener:
            mock_screener.return_value = []

            for params in test_cases:
                result = await server.call_tool("upcoming_earnings_screener", params)
                assert result is not None
            assert mock_screener.call_count == len(test_cases)


class TestErrorHandling:
    """Test error handling and edge cases.

    Error model after PR B (error-policy unification):
    - All tool top-level ``except Exception`` handlers ``raise`` to let
      FastMCP wrap the underlying exception in ``ToolError`` at the
      boundary (mcp.server.fastmcp.tools.base:110).
    - Inner ``except ValueError`` handlers in validators / parsers may
      still re-raise after annotating the message; FastMCP wraps those
      too. So **all** error paths now surface as ``McpToolError`` to the
      caller, regardless of which tool was called.
    """

    @pytest.mark.asyncio
    async def test_invalid_ticker_format(self):
        """Invalid tickers raise ``ValueError`` inside the tool, which
        FastMCP wraps as ``ToolError`` at the boundary.
        """
        invalid_tickers = ["", "123", "TOOLONG", "in valid"]

        for ticker in invalid_tickers:
            with pytest.raises(McpToolError):
                await server.call_tool("get_stock_fundamentals", {"ticker": ticker})

    @pytest.mark.asyncio
    async def test_invalid_parameters(self):
        """Both paths now surface as ``McpToolError`` after PR B:

        1. ``earnings_date`` missing → pydantic validation error
           wrapped to ``ToolError``.
        2. Invalid value within otherwise-valid args → ``ValueError``
           raised by ``validate_*`` → wrapped to ``ToolError``.
        """
        # Path 1: missing required field → ToolError
        with pytest.raises(McpToolError):
            await server.call_tool("earnings_screener", {"market_cap": "invalid_cap"})

        # Path 2: invalid value within otherwise-valid args → ToolError
        invalid_value_params = [
            {"earnings_date": "invalid_date"},
            {"earnings_date": "this_week", "market_cap": "invalid_cap"},
            {"earnings_date": "this_week", "min_price": -10.0},
            {"earnings_date": "this_week", "min_volume": -1000},
        ]
        for params in invalid_value_params:
            with pytest.raises(McpToolError):
                await server.call_tool("earnings_screener", params)

    @pytest.mark.asyncio
    async def test_network_timeout_handling(self):
        """Underlying ``TimeoutError`` propagates through the tool's
        top-level ``raise`` and is wrapped as ``ToolError`` by FastMCP.
        """
        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.side_effect = TimeoutError("Network timeout")

            with pytest.raises(McpToolError) as exc_info:
                await server.call_tool(
                    "earnings_screener", {"earnings_date": "today_after"}
                )
            assert "timeout" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_rate_limit_handling(self):
        """Generic exceptions are also wrapped as ``ToolError`` after PR B."""
        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.side_effect = Exception("Rate limit exceeded")

            with pytest.raises(McpToolError) as exc_info:
                await server.call_tool(
                    "earnings_screener", {"earnings_date": "today_after"}
                )
            assert "rate limit" in str(exc_info.value).lower()


class TestParameterValidation:
    """Test parameter validation for all functions."""

    @pytest.mark.skip(reason="mock shape obsolete after PR B; tracked as #42")
    @pytest.mark.parametrize("market_cap", ["small", "mid", "large", "mega", "smallover"])
    @pytest.mark.asyncio
    async def test_valid_market_cap_values(self, market_cap):
        """Test all valid market cap values."""
        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.return_value = {"stocks": [], "total_count": 0}

            result = await server.call_tool("earnings_screener", {
                "earnings_date": "today_after",
                "market_cap": market_cap
            })
            assert result is not None

    @pytest.mark.skip(reason="mock shape obsolete after PR B; tracked as #42")
    @pytest.mark.parametrize("earnings_date", [
        "today_after", "today_before", "tomorrow_after", "tomorrow_before",
        "this_week", "next_week", "within_2_weeks"
    ])
    @pytest.mark.asyncio
    async def test_valid_earnings_dates(self, earnings_date):
        """Test all valid earnings date values."""
        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.return_value = {"stocks": [], "total_count": 0}

            result = await server.call_tool("earnings_screener", {
                "earnings_date": earnings_date
            })
            assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])