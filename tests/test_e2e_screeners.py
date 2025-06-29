#!/usr/bin/env python3
"""
Comprehensive E2E test suite for all Finviz MCP Server screener functions.
Tests all 22 MCP tools with various parameter combinations.
"""

import pytest
import asyncio
import logging
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, patch

from src.server import server
from src.finviz_client.screener import FinvizScreener
from src.finviz_client.base import FinvizClient
from src.finviz_client.news import FinvizNewsClient
from src.finviz_client.sector_analysis import FinvizSectorAnalysisClient

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

    @pytest.mark.asyncio
    async def test_earnings_premarket_screener(self):
        """Test premarket earnings screener."""
        test_cases = [
            {
                "earnings_timing": "today_before",
                "market_cap": "large",
                "min_price": 25.0,
                "min_price_change": 2.0,
                "include_premarket_data": True,
            },
            {
                "earnings_timing": "tomorrow_before",
                "market_cap": "mid",
                "min_price": 10.0,
                "sectors": ["Technology"],
            },
        ]

        with patch.object(FinvizScreener, "earnings_premarket_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            for params in test_cases:
                result = await server.call_tool("earnings_premarket_screener", params)
                assert result is not None

    @pytest.mark.asyncio
    async def test_earnings_afterhours_screener(self):
        """Test afterhours earnings screener."""
        test_cases = [
            {
                "earnings_timing": "today_after",
                "min_afterhours_change": 5.0,
                "market_cap": "mid",
                "include_afterhours_data": True,
            },
            {
                "earnings_timing": "yesterday_after",
                "min_afterhours_change": 3.0,
                "market_cap": "large",
            },
        ]

        with patch.object(FinvizScreener, "earnings_afterhours_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            for params in test_cases:
                result = await server.call_tool("earnings_afterhours_screener", params)
                assert result is not None

    @pytest.mark.asyncio
    async def test_earnings_trading_screener(self):
        """Test earnings trading screener."""
        test_cases = [
            {
                "earnings_period": "this_week",
                "trading_volume_threshold": 2.0,
                "price_momentum": {"min_change": 5.0, "timeframe": "1d"},
            },
            {
                "earnings_period": "next_week",
                "trading_volume_threshold": 1.5,
                "sectors": ["Healthcare", "Technology"],
            },
        ]

        with patch.object(FinvizScreener, "earnings_trading_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            for params in test_cases:
                result = await server.call_tool("earnings_trading_screener", params)
                assert result is not None

    @pytest.mark.asyncio
    async def test_earnings_positive_surprise_screener(self):
        """Test earnings positive surprise screener."""
        test_cases = [
            {
                "earnings_period": "this_week",
                "growth_criteria": {
                    "min_eps_qoq_growth": 15.0,
                    "min_sales_qoq_growth": 8.0,
                },
                "performance_criteria": {
                    "above_sma200": True,
                    "min_weekly_performance": 0.0,
                },
            },
            {
                "earnings_period": "last_week",
                "growth_criteria": {
                    "min_eps_qoq_growth": 10.0,
                    "min_sales_qoq_growth": 5.0,
                },
            },
        ]

        with patch.object(FinvizScreener, "earnings_positive_surprise_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            for params in test_cases:
                result = await server.call_tool("earnings_positive_surprise_screener", params)
                assert result is not None

    # ===========================================
    # NEWS FUNCTIONS TESTS
    # ===========================================

    @pytest.mark.asyncio
    async def test_get_stock_news(self):
        """Test stock news retrieval."""
        test_cases = [
            {"ticker": "AAPL", "limit": 10},
            {"ticker": "MSFT", "limit": 5, "days_back": 7},
            {"ticker": "GOOGL"},
        ]

        with patch.object(FinvizNewsClient, "get_stock_news") as mock_news:
            mock_news.return_value = [{"title": "Test News", "url": "http://test.com"}]

            for params in test_cases:
                result = await server.call_tool("get_stock_news", params)
                assert result is not None

    @pytest.mark.asyncio
    async def test_get_market_news(self):
        """Test market news retrieval."""
        test_cases = [
            {"limit": 20},
            {"limit": 10, "category": "earnings"},
            {"category": "general"},
        ]

        with patch.object(FinvizNewsClient, "get_market_news") as mock_news:
            mock_news.return_value = [{"title": "Market News", "url": "http://test.com"}]

            for params in test_cases:
                result = await server.call_tool("get_market_news", params)
                assert result is not None

    @pytest.mark.asyncio
    async def test_get_sector_news(self):
        """Test sector news retrieval."""
        test_cases = [
            {"sector": "Technology", "limit": 15},
            {"sector": "Healthcare", "limit": 10},
            {"sector": "Finance"},
        ]

        with patch.object(FinvizNewsClient, "get_sector_news") as mock_news:
            mock_news.return_value = [{"title": "Sector News", "url": "http://test.com"}]

            for params in test_cases:
                result = await server.call_tool("get_sector_news", params)
                assert result is not None

    # ===========================================
    # MARKET ANALYSIS TESTS
    # ===========================================

    @pytest.mark.asyncio
    async def test_get_sector_performance(self):
        """Test sector performance analysis."""
        test_cases = [
            {"timeframe": "1d"},
            {"timeframe": "1w", "sort_by": "performance"},
            {"timeframe": "1m", "sort_by": "volume"},
            {"timeframe": "ytd"},
        ]

        with patch.object(FinvizSectorAnalysisClient, "get_sector_performance") as mock_sector:
            mock_sector.return_value = {"sectors": [{"name": "Technology", "performance": 2.5}]}

            for params in test_cases:
                result = await server.call_tool("get_sector_performance", params)
                assert result is not None

    @pytest.mark.asyncio
    async def test_get_industry_performance(self):
        """Test industry performance analysis."""
        test_cases = [
            {"sector": "Technology", "timeframe": "1d"},
            {"sector": "Healthcare", "timeframe": "1w"},
            {"sector": "Finance", "timeframe": "1m", "sort_by": "performance"},
        ]

        with patch.object(FinvizSectorAnalysisClient, "get_industry_performance") as mock_industry:
            mock_industry.return_value = {"industries": [{"name": "Software", "performance": 3.2}]}

            for params in test_cases:
                result = await server.call_tool("get_industry_performance", params)
                assert result is not None

    @pytest.mark.asyncio
    async def test_get_country_performance(self):
        """Test country performance analysis."""
        test_cases = [
            {"timeframe": "1d"},
            {"timeframe": "1w", "sort_by": "performance"},
            {"timeframe": "1m"},
        ]

        with patch.object(FinvizSectorAnalysisClient, "get_country_performance") as mock_country:
            mock_country.return_value = {"countries": [{"name": "USA", "performance": 1.8}]}

            for params in test_cases:
                result = await server.call_tool("get_country_performance", params)
                assert result is not None

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
        """Test relative volume stocks screener."""
        test_cases = [
            {"min_relative_volume": 2.0, "market_cap": "large"},
            {"min_relative_volume": 1.5, "market_cap": "mid", "sectors": ["Technology"]},
            {"min_relative_volume": 3.0, "min_price": 10.0},
        ]

        with patch.object(FinvizScreener, "get_relative_volume_stocks") as mock_screener:
            mock_screener.return_value = self.mock_results

            for params in test_cases:
                result = await server.call_tool("get_relative_volume_stocks", params)
                assert result is not None

    @pytest.mark.asyncio
    async def test_technical_analysis_screener(self):
        """Test technical analysis screener."""
        test_cases = [
            {
                "technical_criteria": {
                    "rsi_range": {"min": 30, "max": 70},
                    "sma_position": "above_sma50",
                    "volume_criteria": {"min_relative_volume": 1.5},
                }
            },
            {
                "technical_criteria": {
                    "rsi_range": {"min": 20, "max": 40},
                    "sma_position": "below_sma200",
                },
                "market_cap": "large",
            },
        ]

        with patch.object(FinvizScreener, "technical_analysis_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            for params in test_cases:
                result = await server.call_tool("technical_analysis_screener", params)
                assert result is not None

    @pytest.mark.asyncio
    async def test_upcoming_earnings_screener(self):
        """Test upcoming earnings screener."""
        test_cases = [
            {
                "time_range": "next_week",
                "market_cap": "large",
                "expected_move": {"min_percentage": 5.0},
            },
            {
                "time_range": "next_month",
                "sectors": ["Technology", "Healthcare"],
                "expected_move": {"min_percentage": 3.0},
            },
            {"time_range": "next_quarter", "market_cap": "mid"},
        ]

        with patch.object(FinvizScreener, "upcoming_earnings_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            for params in test_cases:
                result = await server.call_tool("upcoming_earnings_screener", params)
                assert result is not None


class TestErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_invalid_ticker_format(self):
        """Test handling of invalid ticker formats."""
        invalid_tickers = ["", "123", "TOOLONG", "in valid"]

        for ticker in invalid_tickers:
            with pytest.raises(ValueError):
                await server.call_tool("get_stock_fundamentals", {"ticker": ticker})

    @pytest.mark.asyncio
    async def test_invalid_parameters(self):
        """Test handling of invalid parameters."""
        invalid_params = [
            {"earnings_date": "invalid_date"},
            {"market_cap": "invalid_cap"},
            {"min_price": -10.0},
            {"min_volume": -1000},
        ]

        for params in invalid_params:
            with pytest.raises((ValueError, TypeError)):
                await server.call_tool("earnings_screener", params)

    @pytest.mark.asyncio
    async def test_network_timeout_handling(self):
        """Test network timeout handling."""
        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.side_effect = TimeoutError("Network timeout")

            with pytest.raises(TimeoutError):
                await server.call_tool("earnings_screener", {"earnings_date": "today_after"})

    @pytest.mark.asyncio
    async def test_rate_limit_handling(self):
        """Test rate limit handling."""
        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.side_effect = Exception("Rate limit exceeded")

            with pytest.raises(Exception):
                await server.call_tool("earnings_screener", {"earnings_date": "today_after"})


class TestParameterValidation:
    """Test parameter validation for all functions."""

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