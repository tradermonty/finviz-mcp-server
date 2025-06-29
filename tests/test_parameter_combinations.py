#!/usr/bin/env python3
"""
Comprehensive parameter combination tests for all Finviz MCP Server functions.
Tests various parameter combinations to ensure robustness.
"""

import pytest
import asyncio
from itertools import product, combinations
from unittest.mock import Mock, patch
import logging

from src.server import server
from src.finviz_client.screener import FinvizScreener
from src.finviz_client.base import FinvizClient
from src.finviz_client.news import FinvizNewsClient
from src.finviz_client.sector_analysis import FinvizSectorAnalysisClient

logger = logging.getLogger(__name__)


class TestParameterCombinations:
    """Test various parameter combinations for all screener functions."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup mock results for all tests."""
        self.mock_stock_results = {
            "stocks": [
                {
                    "ticker": f"TEST{i}",
                    "company": f"Test Company {i}",
                    "sector": "Technology",
                    "industry": "Software",
                    "price": 100.0 + i,
                    "volume": 1000000 + i * 100000,
                    "market_cap": 1000000000 + i * 100000000,
                    "pe_ratio": 20.0 + i,
                    "eps": 5.0 + i * 0.5,
                    "dividend_yield": 1.0 + i * 0.1,
                    "rsi": 50.0 + i,
                    "beta": 1.0 + i * 0.1,
                } for i in range(5)
            ],
            "total_count": 5,
            "execution_time": 1.5,
        }

        self.mock_news_results = [
            {
                "title": f"Test News {i}",
                "url": f"http://test{i}.com",
                "timestamp": f"2024-01-0{i+1}",
                "source": "TestSource",
            } for i in range(3)
        ]

        self.mock_sector_results = {
            "sectors": [
                {"name": "Technology", "performance": 2.5, "volume": 1000000},
                {"name": "Healthcare", "performance": 1.8, "volume": 800000},
                {"name": "Finance", "performance": -0.5, "volume": 1200000},
            ]
        }

    # ===========================================
    # EARNINGS SCREENER PARAMETER COMBINATIONS
    # ===========================================

    @pytest.mark.asyncio
    async def test_earnings_screener_all_combinations(self):
        """Test earnings screener with comprehensive parameter combinations."""
        
        # Define parameter sets
        earnings_dates = ["today_after", "tomorrow_before", "this_week"]
        market_caps = [None, "large", "mid", "small"]
        price_ranges = [
            None,
            {"min_price": 10.0},
            {"max_price": 100.0},
            {"min_price": 5.0, "max_price": 200.0}
        ]
        volume_filters = [None, 1000000, 500000]
        sector_filters = [
            None,
            ["Technology"],
            ["Healthcare", "Finance"],
            ["Technology", "Healthcare", "Finance"]
        ]

        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.return_value = self.mock_stock_results

            # Test combinations of earnings_date and market_cap
            for earnings_date, market_cap in product(earnings_dates, market_caps):
                params = {"earnings_date": earnings_date}
                if market_cap:
                    params["market_cap"] = market_cap

                result = await server.call_tool("earnings_screener", params)
                assert result is not None
                mock_screener.assert_called()

            # Test price range combinations
            for earnings_date, price_range in product(earnings_dates[:2], price_ranges):
                params = {"earnings_date": earnings_date}
                if price_range:
                    params.update(price_range)

                result = await server.call_tool("earnings_screener", params)
                assert result is not None

            # Test complex combinations
            complex_combinations = [
                {
                    "earnings_date": "today_after",
                    "market_cap": "large",
                    "min_price": 20.0,
                    "min_volume": 1000000,
                    "sectors": ["Technology", "Healthcare"]
                },
                {
                    "earnings_date": "this_week",
                    "market_cap": "mid",
                    "max_price": 150.0,
                    "min_volume": 500000,
                    "sectors": ["Finance"]
                },
                {
                    "earnings_date": "tomorrow_before",
                    "min_price": 10.0,
                    "max_price": 300.0,
                    "sectors": ["Technology"]
                }
            ]

            for params in complex_combinations:
                result = await server.call_tool("earnings_screener", params)
                assert result is not None

    # ===========================================
    # VOLUME SURGE SCREENER COMBINATIONS
    # ===========================================

    @pytest.mark.asyncio
    async def test_volume_surge_screener_combinations(self):
        """Test volume surge screener with various parameter combinations."""
        
        market_caps = ["large", "mid", "small", "smallover"]
        price_ranges = [
            {"min_price": 1.0}, {"min_price": 10.0}, {"min_price": 5.0, "max_price": 100.0}
        ]
        volume_filters = [1.5, 2.0, 3.0]
        price_changes = [2.0, 5.0, 10.0]
        sma_filters = [None, "above_sma20", "above_sma50", "above_sma200"]

        with patch.object(FinvizScreener, "volume_surge_screener") as mock_screener:
            mock_screener.return_value = self.mock_stock_results

            # Test all market cap combinations with volume and price filters
            for market_cap, volume_filter, price_change in product(
                market_caps, volume_filters, price_changes[:2]
            ):
                params = {
                    "market_cap": market_cap,
                    "min_relative_volume": volume_filter,
                    "min_price_change": price_change
                }

                result = await server.call_tool("volume_surge_screener", params)
                assert result is not None

            # Test SMA filter combinations
            for market_cap, sma_filter in product(market_caps[:2], sma_filters):
                params = {"market_cap": market_cap}
                if sma_filter:
                    params["sma_filter"] = sma_filter

                result = await server.call_tool("volume_surge_screener", params)
                assert result is not None

    # ===========================================
    # MULTIPLE STOCKS FUNDAMENTALS COMBINATIONS
    # ===========================================

    @pytest.mark.asyncio
    async def test_multiple_stocks_fundamentals_combinations(self):
        """Test multiple stocks fundamentals with various ticker combinations."""
        
        ticker_sets = [
            ["AAPL"],
            ["AAPL", "MSFT"],
            ["AAPL", "MSFT", "GOOGL"],
            ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"],
            ["NVDA", "AMD", "INTC", "QCOM"],
        ]

        data_field_sets = [
            None,
            ["pe_ratio"],
            ["pe_ratio", "eps"],
            ["pe_ratio", "eps", "market_cap"],
            ["pe_ratio", "eps", "market_cap", "dividend_yield", "volume"],
            ["price", "volume", "market_cap", "sector", "industry"],
        ]

        with patch.object(FinvizClient, "get_multiple_stocks_fundamentals") as mock_client:
            mock_client.return_value = self.mock_stock_results["stocks"]

            # Test all combinations of ticker sets and data fields
            for tickers, data_fields in product(ticker_sets, data_field_sets):
                params = {"tickers": tickers}
                if data_fields:
                    params["data_fields"] = data_fields

                result = await server.call_tool("get_multiple_stocks_fundamentals", params)
                assert result is not None
                mock_client.assert_called()

    # ===========================================
    # TREND ANALYSIS COMBINATIONS
    # ===========================================

    @pytest.mark.asyncio
    async def test_trend_analysis_combinations(self):
        """Test trend analysis with various parameter combinations."""
        
        # Trend reversion parameters
        market_caps = ["large", "mid", "small"]
        eps_growths = [5.0, 10.0, 15.0]
        rsi_maxes = [25, 30, 35]
        sector_combinations = [
            None,
            ["Technology"],
            ["Technology", "Healthcare"],
            ["Finance", "Energy"],
        ]

        with patch.object(FinvizScreener, "trend_reversion_screener") as mock_screener:
            mock_screener.return_value = self.mock_stock_results

            for market_cap, eps_growth, rsi_max in product(
                market_caps, eps_growths, rsi_maxes
            ):
                params = {
                    "market_cap": market_cap,
                    "eps_growth_qoq": eps_growth,
                    "rsi_max": rsi_max
                }

                result = await server.call_tool("trend_reversion_screener", params)
                assert result is not None

        # Uptrend screener parameters
        trend_types = ["strong_uptrend", "moderate_uptrend", "emerging_uptrend"]
        sma_periods = ["20", "50", "200"]
        relative_volumes = [1.2, 1.5, 2.0]
        price_changes = [2.0, 5.0, 8.0]

        with patch.object(FinvizScreener, "uptrend_screener") as mock_screener:
            mock_screener.return_value = self.mock_stock_results

            for trend_type, sma_period, rel_vol in product(
                trend_types, sma_periods, relative_volumes
            ):
                params = {
                    "trend_type": trend_type,
                    "sma_period": sma_period,
                    "relative_volume": rel_vol
                }

                result = await server.call_tool("uptrend_screener", params)
                assert result is not None

    # ===========================================
    # DIVIDEND SCREENER COMBINATIONS
    # ===========================================

    @pytest.mark.asyncio
    async def test_dividend_screener_combinations(self):
        """Test dividend screener with various yield and growth combinations."""
        
        yield_ranges = [
            {"min_dividend_yield": 1.0},
            {"min_dividend_yield": 2.0, "max_dividend_yield": 6.0},
            {"min_dividend_yield": 3.0, "max_dividend_yield": 8.0},
            {"max_dividend_yield": 4.0},
        ]

        growth_rates = [3.0, 5.0, 8.0, 10.0]
        roe_minimums = [10.0, 15.0, 20.0]
        market_caps = [None, "large", "mid"]

        with patch.object(FinvizScreener, "dividend_growth_screener") as mock_screener:
            mock_screener.return_value = self.mock_stock_results

            for yield_range, growth_rate, roe_min in product(
                yield_ranges, growth_rates, roe_minimums
            ):
                params = {**yield_range, "min_dividend_growth": growth_rate, "min_roe": roe_min}

                result = await server.call_tool("dividend_growth_screener", params)
                assert result is not None

            # Test with market cap filters
            for market_cap in market_caps:
                params = {
                    "min_dividend_yield": 2.0,
                    "min_dividend_growth": 5.0,
                    "min_roe": 15.0
                }
                if market_cap:
                    params["market_cap"] = market_cap

                result = await server.call_tool("dividend_growth_screener", params)
                assert result is not None

    # ===========================================
    # EARNINGS TIMING SCREENER COMBINATIONS
    # ===========================================

    @pytest.mark.asyncio
    async def test_earnings_timing_combinations(self):
        """Test earnings timing screeners with various combinations."""
        
        # Premarket screener
        timings = ["today_before", "tomorrow_before", "this_week_before"]
        market_caps = ["large", "mid", "small"]
        price_ranges = [
            {"min_price": 10.0},
            {"min_price": 25.0},
            {"min_price": 5.0, "max_price": 100.0}
        ]
        price_changes = [1.0, 2.0, 5.0]

        with patch.object(FinvizScreener, "earnings_premarket_screener") as mock_screener:
            mock_screener.return_value = self.mock_stock_results

            for timing, market_cap, price_change in product(
                timings, market_caps, price_changes
            ):
                params = {
                    "earnings_timing": timing,
                    "market_cap": market_cap,
                    "min_price_change": price_change
                }

                result = await server.call_tool("earnings_premarket_screener", params)
                assert result is not None

        # Afterhours screener
        afterhours_timings = ["today_after", "yesterday_after", "this_week_after"]
        afterhours_changes = [3.0, 5.0, 8.0]

        with patch.object(FinvizScreener, "earnings_afterhours_screener") as mock_screener:
            mock_screener.return_value = self.mock_stock_results

            for timing, change, market_cap in product(
                afterhours_timings, afterhours_changes, market_caps
            ):
                params = {
                    "earnings_timing": timing,
                    "min_afterhours_change": change,
                    "market_cap": market_cap
                }

                result = await server.call_tool("earnings_afterhours_screener", params)
                assert result is not None

    # ===========================================
    # NEWS FUNCTION COMBINATIONS
    # ===========================================

    @pytest.mark.asyncio
    async def test_news_function_combinations(self):
        """Test news functions with various parameter combinations."""
        
        # Stock news combinations
        tickers = ["AAPL", "MSFT", "GOOGL", "AMZN"]
        limits = [5, 10, 15, 20]
        days_back_options = [None, 1, 3, 7]

        with patch.object(FinvizNewsClient, "get_stock_news") as mock_news:
            mock_news.return_value = self.mock_news_results

            for ticker, limit in product(tickers, limits):
                params = {"ticker": ticker, "limit": limit}

                result = await server.call_tool("get_stock_news", params)
                assert result is not None

            # Test with days_back parameter
            for ticker, days_back in product(tickers[:2], days_back_options):
                params = {"ticker": ticker, "limit": 10}
                if days_back:
                    params["days_back"] = days_back

                result = await server.call_tool("get_stock_news", params)
                assert result is not None

        # Market news combinations
        categories = [None, "general", "earnings", "analyst", "insider"]
        
        with patch.object(FinvizNewsClient, "get_market_news") as mock_news:
            mock_news.return_value = self.mock_news_results

            for category, limit in product(categories, limits):
                params = {"limit": limit}
                if category:
                    params["category"] = category

                result = await server.call_tool("get_market_news", params)
                assert result is not None

    # ===========================================
    # SECTOR ANALYSIS COMBINATIONS
    # ===========================================

    @pytest.mark.asyncio
    async def test_sector_analysis_combinations(self):
        """Test sector analysis with various timeframes and sorting options."""
        
        timeframes = ["1d", "1w", "1m", "3m", "6m", "ytd", "1y"]
        sort_options = [None, "performance", "volume", "name"]

        # Sector performance
        with patch.object(FinvizSectorAnalysisClient, "get_sector_performance") as mock_sector:
            mock_sector.return_value = self.mock_sector_results

            for timeframe, sort_by in product(timeframes, sort_options):
                params = {"timeframe": timeframe}
                if sort_by:
                    params["sort_by"] = sort_by

                result = await server.call_tool("get_sector_performance", params)
                assert result is not None

        # Industry performance
        sectors = ["Technology", "Healthcare", "Finance", "Energy"]
        
        with patch.object(FinvizSectorAnalysisClient, "get_industry_performance") as mock_industry:
            mock_industry.return_value = self.mock_sector_results

            for sector, timeframe in product(sectors, timeframes):
                params = {"sector": sector, "timeframe": timeframe}

                result = await server.call_tool("get_industry_performance", params)
                assert result is not None

        # Country performance
        with patch.object(FinvizSectorAnalysisClient, "get_country_performance") as mock_country:
            mock_country.return_value = self.mock_sector_results

            for timeframe in timeframes:
                params = {"timeframe": timeframe}

                result = await server.call_tool("get_country_performance", params)
                assert result is not None

    # ===========================================
    # TECHNICAL ANALYSIS COMBINATIONS
    # ===========================================

    @pytest.mark.asyncio
    async def test_technical_analysis_combinations(self):
        """Test technical analysis screener with various criteria combinations."""
        
        rsi_ranges = [
            {"min": 20, "max": 40},
            {"min": 30, "max": 70},
            {"min": 60, "max": 80},
        ]

        sma_positions = [
            "above_sma20", "above_sma50", "above_sma200",
            "below_sma20", "below_sma50", "below_sma200"
        ]

        volume_criterias = [
            {"min_relative_volume": 1.2},
            {"min_relative_volume": 1.5},
            {"min_relative_volume": 2.0},
        ]

        market_caps = [None, "large", "mid", "small"]

        with patch.object(FinvizScreener, "technical_analysis_screener") as mock_screener:
            mock_screener.return_value = self.mock_stock_results

            for rsi_range, sma_pos, vol_criteria in product(
                rsi_ranges, sma_positions, volume_criterias
            ):
                technical_criteria = {
                    "rsi_range": rsi_range,
                    "sma_position": sma_pos,
                    "volume_criteria": vol_criteria
                }
                params = {"technical_criteria": technical_criteria}

                result = await server.call_tool("technical_analysis_screener", params)
                assert result is not None

            # Test with market cap combinations
            for market_cap in market_caps:
                technical_criteria = {
                    "rsi_range": {"min": 30, "max": 70},
                    "sma_position": "above_sma50",
                    "volume_criteria": {"min_relative_volume": 1.5}
                }
                params = {"technical_criteria": technical_criteria}
                if market_cap:
                    params["market_cap"] = market_cap

                result = await server.call_tool("technical_analysis_screener", params)
                assert result is not None

    # ===========================================
    # UPCOMING EARNINGS COMBINATIONS
    # ===========================================

    @pytest.mark.asyncio
    async def test_upcoming_earnings_combinations(self):
        """Test upcoming earnings screener with various time ranges and criteria."""
        
        time_ranges = ["next_week", "next_month", "next_quarter"]
        market_caps = ["large", "mid", "small"]
        expected_moves = [
            {"min_percentage": 3.0},
            {"min_percentage": 5.0},
            {"min_percentage": 8.0, "max_percentage": 20.0},
        ]

        sectors_combinations = [
            None,
            ["Technology"],
            ["Technology", "Healthcare"],
            ["Finance", "Energy", "Utilities"],
        ]

        with patch.object(FinvizScreener, "upcoming_earnings_screener") as mock_screener:
            mock_screener.return_value = self.mock_stock_results

            for time_range, market_cap, expected_move in product(
                time_ranges, market_caps, expected_moves
            ):
                params = {
                    "time_range": time_range,
                    "market_cap": market_cap,
                    "expected_move": expected_move
                }

                result = await server.call_tool("upcoming_earnings_screener", params)
                assert result is not None

            # Test with sector combinations
            for time_range, sectors in product(time_ranges, sectors_combinations):
                params = {"time_range": time_range}
                if sectors:
                    params["sectors"] = sectors

                result = await server.call_tool("upcoming_earnings_screener", params)
                assert result is not None


class TestEdgeCaseParameterCombinations:
    """Test edge cases and boundary conditions for parameter combinations."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup for edge case tests."""
        self.empty_results = {"stocks": [], "total_count": 0, "execution_time": 0.5}

    @pytest.mark.asyncio
    async def test_minimum_maximum_price_combinations(self):
        """Test minimum and maximum price boundary combinations."""
        
        price_combinations = [
            {"min_price": 0.01, "max_price": 0.99},  # Penny stocks
            {"min_price": 1.0, "max_price": 5.0},    # Low price
            {"min_price": 1000.0, "max_price": 5000.0},  # High price
            {"min_price": 0.01},  # Only minimum
            {"max_price": 1000000.0},  # Only maximum
        ]

        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.return_value = self.empty_results

            for price_combo in price_combinations:
                params = {"earnings_date": "today_after", **price_combo}
                
                result = await server.call_tool("earnings_screener", params)
                assert result is not None

    @pytest.mark.asyncio
    async def test_extreme_volume_combinations(self):
        """Test extreme volume parameter combinations."""
        
        volume_combinations = [
            {"min_volume": 1},  # Minimum volume
            {"min_volume": 1000},  # Low volume
            {"min_volume": 100000000},  # Very high volume
            {"min_relative_volume": 0.1},  # Low relative volume
            {"min_relative_volume": 10.0},  # High relative volume
        ]

        with patch.object(FinvizScreener, "volume_surge_screener") as mock_screener:
            mock_screener.return_value = self.empty_results

            for vol_combo in volume_combinations:
                params = {"market_cap": "large", **vol_combo}
                
                result = await server.call_tool("volume_surge_screener", params)
                assert result is not None

    @pytest.mark.asyncio
    async def test_extreme_technical_combinations(self):
        """Test extreme technical indicator combinations."""
        
        extreme_technical_combinations = [
            {
                "technical_criteria": {
                    "rsi_range": {"min": 0, "max": 10},  # Extremely oversold
                    "sma_position": "below_sma200",
                    "volume_criteria": {"min_relative_volume": 5.0}
                }
            },
            {
                "technical_criteria": {
                    "rsi_range": {"min": 90, "max": 100},  # Extremely overbought
                    "sma_position": "above_sma20",
                    "volume_criteria": {"min_relative_volume": 0.5}
                }
            },
            {
                "technical_criteria": {
                    "rsi_range": {"min": 45, "max": 55},  # Neutral RSI
                    "sma_position": "above_sma50",
                    "volume_criteria": {"min_relative_volume": 1.0}
                }
            },
        ]

        with patch.object(FinvizScreener, "technical_analysis_screener") as mock_screener:
            mock_screener.return_value = self.empty_results

            for params in extreme_technical_combinations:
                result = await server.call_tool("technical_analysis_screener", params)
                assert result is not None

    @pytest.mark.asyncio
    async def test_large_ticker_list_combinations(self):
        """Test performance with large ticker lists."""
        
        # Create progressively larger ticker lists
        ticker_lists = [
            [f"TICK{i:03d}" for i in range(10)],   # 10 tickers
            [f"TICK{i:03d}" for i in range(50)],   # 50 tickers
            [f"TICK{i:03d}" for i in range(100)],  # 100 tickers
        ]

        data_field_combinations = [
            None,
            ["pe_ratio"],
            ["pe_ratio", "eps", "market_cap", "dividend_yield", "volume"],
        ]

        with patch.object(FinvizClient, "get_multiple_stocks_fundamentals") as mock_client:
            mock_client.return_value = []

            for tickers, data_fields in product(ticker_lists, data_field_combinations):
                params = {"tickers": tickers}
                if data_fields:
                    params["data_fields"] = data_fields

                result = await server.call_tool("get_multiple_stocks_fundamentals", params)
                assert result is not None

    @pytest.mark.asyncio
    async def test_sector_combinations_exhaustive(self):
        """Test all possible sector combinations."""
        
        available_sectors = [
            "Technology", "Healthcare", "Finance", "Energy", "Utilities",
            "Consumer Goods", "Industrial", "Basic Materials", "Real Estate"
        ]

        # Test single sectors
        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.return_value = self.empty_results

            for sector in available_sectors:
                params = {
                    "earnings_date": "today_after",
                    "sectors": [sector]
                }
                
                result = await server.call_tool("earnings_screener", params)
                assert result is not None

        # Test sector combinations (2-3 sectors)
        for sector_combo in combinations(available_sectors, 2):
            params = {
                "earnings_date": "today_after",
                "sectors": list(sector_combo)
            }
            
            result = await server.call_tool("earnings_screener", params)
            assert result is not None

        # Test all sectors
        params = {
            "earnings_date": "today_after",
            "sectors": available_sectors
        }
        
        result = await server.call_tool("earnings_screener", params)
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-x"])