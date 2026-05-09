#!/usr/bin/env python3
"""
Comprehensive parameter combination tests for all Finviz MCP Server functions.
Tests various parameter combinations to ensure robustness.
"""

import logging
from itertools import combinations, product
from unittest.mock import patch

import pytest

from src.finviz_client.base import FinvizClient
from src.finviz_client.news import FinvizNewsClient
from src.finviz_client.screener import FinvizScreener
from src.finviz_client.sector_analysis import FinvizSectorAnalysisClient
from src.server import server
from tests import factories

logger = logging.getLogger(__name__)


def _make_parameter_stock(index: int = 0):
    ticker = f"S{index:04d}"
    stock = factories.make_stock_data(
        ticker=ticker,
        company_name=f"Test Company {index}",
        sector="Technology",
        industry="Software",
        price=100.0 + index,
        volume=1_000_000 + index * 100_000,
        market_cap=1_000.0 + index * 100.0,
        pe_ratio=20.0 + index,
        eps=5.0 + index * 0.5,
        dividend_yield=1.0 + index * 0.1,
        rsi=50.0 + index,
        beta=1.0 + index * 0.1,
        eps_qoq_growth=6.0 + index,
        sales_qoq_growth=4.0 + index,
        premarket_change_percent=2.0 + index,
        afterhours_change_percent=2.5 + index,
        earnings_date="2026-05-14",
        earnings_timing="Before Market",
    )
    stock.current_price = stock.price
    stock.target_price_upside = 12.5 + index
    return stock


def _make_stock_results(count: int = 5):
    return [_make_parameter_stock(i) for i in range(count)]


class TestParameterCombinations:
    """Test various parameter combinations for all screener functions."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup mock results for all tests."""
        self.mock_stock_results = _make_stock_results(5)

        self.mock_news_results = [
            factories.make_news_data(
                ticker="AAPL",
                title=f"Test News {i}",
                source="TestSource",
                url=f"https://example.test/news/{i}",
            )
            for i in range(3)
        ]

        self.mock_sector_results = [
            {
                "name": "Technology",
                "market_cap": "$12.3T",
                "pe_ratio": "28.4",
                "dividend_yield": "0.7%",
                "change": "2.5%",
                "stocks": "760",
            },
            {
                "name": "Healthcare",
                "market_cap": "$6.8T",
                "pe_ratio": "21.0",
                "dividend_yield": "1.2%",
                "change": "1.8%",
                "stocks": "520",
            },
        ]
        self.mock_industry_results = [
            {
                "industry": "Software - Application",
                "market_cap": "$2.1T",
                "pe_ratio": "34.1",
                "change": "0.8%",
                "stocks": "210",
            }
        ]
        self.mock_country_results = [
            {
                "country": "USA",
                "market_cap": "$55.0T",
                "pe_ratio": "24.2",
                "change": "0.4%",
                "stocks": "4200",
            }
        ]

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
            {"min_price": 5.0, "max_price": 200.0},
        ]
        volume_filters = [None, 1000000, 500000]  # noqa: F841
        sector_filters = [  # noqa: F841
            None,
            ["Technology"],
            ["Healthcare", "Finance"],
            ["Technology", "Healthcare", "Finance"],
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
                    "sectors": ["Technology", "Healthcare"],
                },
                {
                    "earnings_date": "this_week",
                    "market_cap": "mid",
                    "max_price": 150.0,
                    "min_volume": 500000,
                    "sectors": ["Financial"],
                },
                {
                    "earnings_date": "tomorrow_before",
                    "min_price": 10.0,
                    "max_price": 300.0,
                    "sectors": ["Technology"],
                },
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

        market_caps = ["large", "mid", "small", "smallover"]  # noqa: F841
        price_ranges = [  # noqa: F841
            {"min_price": 1.0},
            {"min_price": 10.0},
            {"min_price": 5.0, "max_price": 100.0},
        ]
        volume_filters = [1.5, 2.0, 3.0]  # noqa: F841
        price_changes = [2.0, 5.0, 10.0]  # noqa: F841
        # ``volume_surge_screener`` is a fixed-criteria tool with no
        # arguments. Just exercise that the wrapper invokes the screener
        # method end-to-end through FastMCP. (The market_cap / SMA / price
        # parameters used previously were silently ignored by FastMCP and
        # never reached the implementation.)
        with patch.object(FinvizScreener, "volume_surge_screener") as mock_screener:
            mock_screener.return_value = self.mock_stock_results

            for _ in range(3):  # call multiple times to mimic the prior loop scope
                result = await server.call_tool("volume_surge_screener", {})
                assert result is not None

            assert mock_screener.call_count >= 3

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

        with patch.object(
            FinvizClient, "get_multiple_stocks_fundamentals"
        ) as mock_client:
            mock_client.return_value = self.mock_stock_results

            # Test all combinations of ticker sets and data fields
            for tickers, data_fields in product(ticker_sets, data_field_sets):
                params = {"tickers": tickers}
                if data_fields:
                    params["data_fields"] = data_fields

                result = await server.call_tool(
                    "get_multiple_stocks_fundamentals", params
                )
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
        sector_combinations = [  # noqa: F841
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
                    "rsi_max": rsi_max,
                }

                result = await server.call_tool("trend_reversion_screener", params)
                assert result is not None

        # ``uptrend_screener`` is parameterless (fixed criteria); the
        # previous ``trend_type``/``sma_period``/``relative_volume`` keys
        # were silently dropped by FastMCP and never reached the screener.
        # Just verify the wrapper invokes the screener through FastMCP.
        with patch.object(FinvizScreener, "uptrend_screener") as mock_screener:
            mock_screener.return_value = self.mock_stock_results

            for _ in range(3):
                result = await server.call_tool("uptrend_screener", {})
                assert result is not None
            assert mock_screener.call_count >= 3

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
                params = {
                    **yield_range,
                    "min_dividend_growth": growth_rate,
                    "min_roe": roe_min,
                }

                result = await server.call_tool("dividend_growth_screener", params)
                assert result is not None

            # Test with market cap filters
            for market_cap in market_caps:
                params = {
                    "min_dividend_yield": 2.0,
                    "min_dividend_growth": 5.0,
                    "min_roe": 15.0,
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
        """Test fixed-criteria earnings timing screeners.

        Both ``earnings_premarket_screener`` and ``earnings_afterhours_screener``
        are parameterless (Finviz fixed-filter URLs). The previous
        ``earnings_timing``/``market_cap``/``min_price_change``/
        ``min_afterhours_change`` keys were silently dropped by FastMCP and
        never reached the screener. Test that the wrapper invokes the
        screener through FastMCP without false-passing on bogus args.
        """
        with patch.object(FinvizScreener, "earnings_premarket_screener") as mock_pre:
            mock_pre.return_value = self.mock_stock_results

            for _ in range(3):
                result = await server.call_tool("earnings_premarket_screener", {})
                assert result is not None
            assert mock_pre.call_count >= 3

        with patch.object(FinvizScreener, "earnings_afterhours_screener") as mock_after:
            mock_after.return_value = self.mock_stock_results

            for _ in range(3):
                result = await server.call_tool("earnings_afterhours_screener", {})
                assert result is not None
            assert mock_after.call_count >= 3

    # ===========================================
    # NEWS FUNCTION COMBINATIONS
    # ===========================================

    @pytest.mark.asyncio
    async def test_news_function_combinations(self):
        """Test news functions with various parameter combinations.

        Aligned to current signatures:
        - ``get_stock_news(tickers, days_back, news_type)``
        - ``get_market_news(days_back, max_items)``

        ``limit``/``category`` are not real arguments; FastMCP would silently
        drop them, so we no longer pass them.
        """
        tickers = ["AAPL", "MSFT", "GOOGL", "AMZN"]
        days_back_options = [1, 3, 7]
        news_types = [None, "all", "general"]

        with patch.object(FinvizNewsClient, "get_stock_news") as mock_news:
            mock_news.return_value = self.mock_news_results

            for ticker, days_back in product(tickers, days_back_options):
                params = {"tickers": ticker, "days_back": days_back}
                result = await server.call_tool("get_stock_news", params)
                assert result is not None

            for ticker, news_type in product(tickers[:2], news_types):
                params = {"tickers": ticker, "days_back": 7}
                if news_type:
                    params["news_type"] = news_type
                result = await server.call_tool("get_stock_news", params)
                assert result is not None

        # Market news combinations — current signature is days_back/max_items.
        max_items_options = [10, 20, 50]
        with patch.object(FinvizNewsClient, "get_market_news") as mock_news:
            mock_news.return_value = self.mock_news_results

            for days_back, max_items in product(days_back_options, max_items_options):
                params = {"days_back": days_back, "max_items": max_items}
                result = await server.call_tool("get_market_news", params)
                assert result is not None

    # ===========================================
    # SECTOR ANALYSIS COMBINATIONS
    # ===========================================

    @pytest.mark.asyncio
    async def test_sector_analysis_combinations(self):
        """Test sector analysis tools with parameter combinations.

        Current signatures take list-typed canonical arguments only:
        - ``get_sector_performance(sectors=None)``
        - ``get_industry_performance(industries=None)``
        - ``get_country_performance(countries=None)``

        ``timeframe``/``sort_by``/``sector`` (singular) are not arguments
        and were silently dropped by FastMCP previously.
        """
        sector_groups = [
            None,
            ["Technology"],
            ["Technology", "Healthcare"],
            ["Energy", "Utilities", "Financial"],
        ]
        with patch.object(
            FinvizSectorAnalysisClient, "get_sector_performance"
        ) as mock_sector:
            mock_sector.return_value = self.mock_sector_results

            for sectors in sector_groups:
                params = {} if sectors is None else {"sectors": sectors}
                result = await server.call_tool("get_sector_performance", params)
                assert result is not None

        industry_groups = [
            None,
            ["software_application"],
            ["software_application", "semiconductors"],
        ]
        with patch.object(
            FinvizSectorAnalysisClient, "get_industry_performance"
        ) as mock_industry:
            mock_industry.return_value = self.mock_industry_results

            for industries in industry_groups:
                params = {} if industries is None else {"industries": industries}
                result = await server.call_tool("get_industry_performance", params)
                assert result is not None

        country_groups = [
            None,
            ["usa"],
            ["usa", "japan"],
        ]
        with patch.object(
            FinvizSectorAnalysisClient, "get_country_performance"
        ) as mock_country:
            mock_country.return_value = self.mock_country_results

            for countries in country_groups:
                params = {} if countries is None else {"countries": countries}
                result = await server.call_tool("get_country_performance", params)
                assert result is not None

    # ===========================================
    # TECHNICAL ANALYSIS COMBINATIONS
    # ===========================================

    @pytest.mark.asyncio
    async def test_technical_analysis_combinations(self):
        """Test technical analysis screener with various criteria combinations.

        Implementation calls ``finviz_screener.screen_stocks(filters)`` (see
        ``src/server.py:1937``), so we patch ``screen_stocks`` — patching
        ``technical_analysis_screener`` would not intercept anything and
        would let live API calls through. Args are flat per the current
        signature (``rsi_min``/``rsi_max``/``price_vs_sma20``/...), not the
        legacy nested ``technical_criteria`` dict.
        """
        rsi_ranges = [(20, 40), (30, 70), (60, 80)]
        sma_positions = [
            ("above", None, None),
            (None, "above", None),
            (None, None, "above"),
            ("below", None, None),
        ]
        sectors_options = [None, ["Technology"]]

        with patch.object(FinvizScreener, "screen_stocks") as mock_screen:
            mock_screen.return_value = self.mock_stock_results

            for (rsi_min, rsi_max), (sma20, sma50, sma200) in product(
                rsi_ranges, sma_positions
            ):
                params: dict = {"rsi_min": rsi_min, "rsi_max": rsi_max}
                if sma20:
                    params["price_vs_sma20"] = sma20
                if sma50:
                    params["price_vs_sma50"] = sma50
                if sma200:
                    params["price_vs_sma200"] = sma200
                result = await server.call_tool("technical_analysis_screener", params)
                assert result is not None

            for sectors in sectors_options:
                params = {"rsi_min": 30, "rsi_max": 70, "price_vs_sma50": "above"}
                if sectors:
                    params["sectors"] = sectors
                result = await server.call_tool("technical_analysis_screener", params)
                assert result is not None

    # ===========================================
    # UPCOMING EARNINGS COMBINATIONS
    # ===========================================

    @pytest.mark.asyncio
    async def test_upcoming_earnings_combinations(self):
        """Test upcoming earnings screener with various time ranges and criteria.

        Aligned to the actual signature
        (``earnings_period``/``market_cap``/``min_price``/``min_avg_volume``/
        ``target_sectors``/``pre_earnings_analysis``/...). The legacy
        ``time_range``/``expected_move``/``sectors`` keys were silently
        dropped by FastMCP and never reached the screener.
        """
        earnings_periods = ["next_week", "next_2_weeks", "next_month"]
        market_caps = ["smallover", "midover", "largeover"]
        target_sector_groups = [
            None,
            ["Technology"],
            ["Technology", "Healthcare"],
            ["Energy", "Utilities", "Financial"],
        ]

        with patch.object(
            FinvizScreener, "upcoming_earnings_screener"
        ) as mock_screener:
            mock_screener.return_value = self.mock_stock_results

            for period, market_cap in product(earnings_periods, market_caps):
                params = {"earnings_period": period, "market_cap": market_cap}
                result = await server.call_tool("upcoming_earnings_screener", params)
                assert result is not None

            for period, sectors in product(earnings_periods, target_sector_groups):
                params = {"earnings_period": period}
                if sectors:
                    params["target_sectors"] = sectors
                result = await server.call_tool("upcoming_earnings_screener", params)
                assert result is not None


class TestEdgeCaseParameterCombinations:
    """Test edge cases and boundary conditions for parameter combinations."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup for edge case tests."""
        self.empty_results = []

    @pytest.mark.asyncio
    async def test_minimum_maximum_price_combinations(self):
        """Test minimum and maximum price boundary combinations."""

        price_combinations = [
            {"min_price": 0.01, "max_price": 0.99},  # Penny stocks
            {"min_price": 1.0, "max_price": 5.0},  # Low price
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
        """Test extreme volume parameter combinations.

        ``min_volume`` and ``min_relative_volume`` are not arguments of the
        fixed-criteria ``volume_surge_screener``; they belong to
        ``earnings_screener`` (``min_volume``) and ``get_relative_volume_stocks``
        (``min_relative_volume``). Routed accordingly.
        """
        min_volume_cases = [1, 1000, 100_000_000]
        min_rel_volume_cases = [0.1, 10.0]

        with patch.object(FinvizScreener, "earnings_screener") as mock_earnings:
            mock_earnings.return_value = self.empty_results

            for min_vol in min_volume_cases:
                params = {"earnings_date": "today_after", "min_volume": min_vol}
                result = await server.call_tool("earnings_screener", params)
                assert result is not None

        # ``get_relative_volume_stocks`` calls ``screen_stocks`` internally
        # (src/server.py:1830), so patch that. Patching the same-name
        # screener method does not intercept and would let live calls
        # through.
        with patch.object(FinvizScreener, "screen_stocks") as mock_screen:
            mock_screen.return_value = []

            for min_rel in min_rel_volume_cases:
                result = await server.call_tool(
                    "get_relative_volume_stocks", {"min_relative_volume": min_rel}
                )
                assert result is not None

    @pytest.mark.asyncio
    async def test_extreme_technical_combinations(self):
        """Test extreme technical indicator combinations.

        ``technical_analysis_screener`` calls ``screen_stocks`` internally
        (src/server.py:1937); patch that. Args are flat per the current
        signature.
        """
        extreme_combinations = [
            {"rsi_min": 0, "rsi_max": 10, "price_vs_sma200": "below"},  # Oversold
            {"rsi_min": 90, "rsi_max": 100, "price_vs_sma20": "above"},  # Overbought
            {"rsi_min": 45, "rsi_max": 55, "price_vs_sma50": "above"},  # Neutral
        ]

        with patch.object(FinvizScreener, "screen_stocks") as mock_screen:
            mock_screen.return_value = []

            for params in extreme_combinations:
                result = await server.call_tool("technical_analysis_screener", params)
                assert result is not None

    @pytest.mark.asyncio
    async def test_large_ticker_list_combinations(self):
        """Test performance with large ticker lists.

        ``validate_ticker`` accepts ``^[A-Z]{1,5}$``, so we generate 1- to 5-
        letter alphabetic tickers (base-26) instead of the legacy
        ``TICK000`` shape that the validator now rejects.
        """

        def make_ticker(i: int) -> str:
            # Two-letter alphabetic ticker: AA, AB, ..., DV (covers 0-99).
            high, low = divmod(i, 26)
            return f"{chr(ord('A') + high)}{chr(ord('A') + low)}"

        # Create progressively larger ticker lists
        ticker_lists = [
            [make_ticker(i) for i in range(10)],  # 10 tickers
            [make_ticker(i) for i in range(50)],  # 50 tickers
            [make_ticker(i) for i in range(100)],  # 100 tickers
        ]

        data_field_combinations = [
            None,
            ["pe_ratio"],
            ["pe_ratio", "eps", "market_cap", "dividend_yield", "volume"],
        ]

        with patch.object(
            FinvizClient, "get_multiple_stocks_fundamentals"
        ) as mock_client:
            mock_client.return_value = []

            for tickers, data_fields in product(ticker_lists, data_field_combinations):
                params = {"tickers": tickers}
                if data_fields:
                    params["data_fields"] = data_fields

                result = await server.call_tool(
                    "get_multiple_stocks_fundamentals", params
                )
                assert result is not None

    @pytest.mark.asyncio
    async def test_sector_combinations_exhaustive(self):
        """Test sector combinations against valid sector names.

        Sector names match ``validate_sector`` (Finviz canonical labels);
        ``"Finance"``/``"Consumer Goods"``/``"Industrial"`` are NOT valid
        and have been replaced with ``"Financial"``/``"Consumer Cyclical"``/
        ``"Consumer Defensive"``/``"Industrials"`` accordingly.

        All loops run inside a single ``patch.object`` context so the test
        cannot leak into the live Finviz API (the previous version's pair
        and full-list loops were outside the patch).
        """
        available_sectors = [
            "Technology",
            "Healthcare",
            "Financial",
            "Energy",
            "Utilities",
            "Consumer Cyclical",
            "Consumer Defensive",
            "Industrials",
            "Basic Materials",
            "Real Estate",
        ]

        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.return_value = self.empty_results

            # Single-sector cases
            for sector in available_sectors:
                params = {
                    "earnings_date": "today_after",
                    "sectors": [sector],
                }
                result = await server.call_tool("earnings_screener", params)
                assert result is not None

            # Pair combinations
            for sector_combo in combinations(available_sectors, 2):
                params = {
                    "earnings_date": "today_after",
                    "sectors": list(sector_combo),
                }
                result = await server.call_tool("earnings_screener", params)
                assert result is not None

            # All sectors at once
            params = {
                "earnings_date": "today_after",
                "sectors": available_sectors,
            }
            result = await server.call_tool("earnings_screener", params)
            assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-x"])
