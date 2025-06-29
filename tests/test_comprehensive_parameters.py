#!/usr/bin/env python3
"""
Comprehensive parameter validation tests based on finviz_screening_parameters.md
Tests all documented Finviz parameters and their combinations.
"""

import pytest
import asyncio
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, patch
import logging

from src.server import server
from src.finviz_client.screener import FinvizScreener
from src.finviz_client.base import FinvizClient
from src.finviz_client.news import FinvizNewsClient
from src.finviz_client.sector_analysis import FinvizSectorAnalysisClient

logger = logging.getLogger(__name__)


class TestComprehensiveParameters:
    """Test comprehensive parameter coverage based on Finviz documentation."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup mock results for all tests."""
        self.mock_results = {
            "stocks": [
                {
                    "ticker": "AAPL",
                    "company": "Apple Inc.",
                    "sector": "Technology", 
                    "industry": "Consumer Electronics",
                    "exchange": "NASDAQ",
                    "country": "USA",
                    "price": 150.0,
                    "volume": 50000000,
                    "market_cap": 2400000000000,
                    "pe_ratio": 25.5,
                    "eps": 6.0,
                    "dividend_yield": 0.5,
                    "beta": 1.2,
                    "rsi": 55.0,
                    "analyst_recommendation": "Buy",
                }
            ],
            "total_count": 1,
            "execution_time": 1.5,
        }

    # ===========================================
    # EXCHANGE PARAMETERS
    # ===========================================

    @pytest.mark.asyncio
    async def test_exchange_parameters(self):
        """Test all documented exchange parameters."""
        exchanges = ["", "amex", "cboe", "nasd", "nyse", "modal"]
        
        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            for exchange in exchanges:
                params = {
                    "earnings_date": "today_after",
                    "exchange": exchange
                }
                if exchange == "":
                    params.pop("exchange")  # Remove empty exchange
                
                result = await server.call_tool("earnings_screener", params)
                assert result is not None

    # ===========================================
    # INDEX MEMBERSHIP PARAMETERS
    # ===========================================

    @pytest.mark.asyncio
    async def test_index_parameters(self):
        """Test all documented index membership parameters."""
        indices = ["", "sp500", "ndx", "dji", "rut", "modal"]
        
        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            for index in indices:
                params = {
                    "earnings_date": "today_after",
                    "index": index
                }
                if index == "":
                    params.pop("index")  # Remove empty index
                
                result = await server.call_tool("earnings_screener", params)
                assert result is not None

    # ===========================================
    # COMPREHENSIVE SECTOR TESTING
    # ===========================================

    @pytest.mark.asyncio
    async def test_all_documented_sectors(self):
        """Test all sectors documented in the Finviz parameters."""
        sectors = [
            "basicmaterials", "communicationservices", "consumercyclical",
            "consumerdefensive", "energy", "financial", "healthcare", 
            "industrials", "realestate", "technology", "utilities"
        ]
        
        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            for sector in sectors:
                params = {
                    "earnings_date": "today_after",
                    "sectors": [sector]
                }
                
                result = await server.call_tool("earnings_screener", params)
                assert result is not None

    # ===========================================
    # COMPREHENSIVE INDUSTRY TESTING  
    # ===========================================

    @pytest.mark.asyncio
    async def test_key_industries(self):
        """Test key industries from the comprehensive industry list."""
        key_industries = [
            "biotechnology", "semiconductors", "softwareapplication",
            "softwareinfrastructure", "oilgasep", "banksdiversified",
            "banksregional", "pharmaceuticalretailers", "airlines",
            "utilitiesregulatedelectric", "realestate", "gold",
            "silver", "solar", "gambling", "restaurants"
        ]
        
        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            for industry in key_industries:
                params = {
                    "earnings_date": "today_after",
                    "industry": industry
                }
                
                result = await server.call_tool("earnings_screener", params)
                assert result is not None

    # ===========================================
    # COUNTRY/GEOGRAPHIC PARAMETERS
    # ===========================================

    @pytest.mark.asyncio
    async def test_geographic_parameters(self):
        """Test geographic/country parameters."""
        countries = [
            "usa", "notusa", "asia", "europe", "latinamerica", "bric",
            "china", "japan", "germany", "unitedkingdom", "canada",
            "australia", "india", "brazil", "singapore", "hongkong"
        ]
        
        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            for country in countries:
                params = {
                    "earnings_date": "today_after",
                    "country": country
                }
                
                result = await server.call_tool("earnings_screener", params)
                assert result is not None

    # ===========================================
    # MARKET CAP GRANULAR TESTING
    # ===========================================

    @pytest.mark.asyncio
    async def test_all_market_cap_categories(self):
        """Test all documented market cap categories."""
        market_caps = [
            "mega", "large", "mid", "small", "micro", "nano",
            "largeover", "midover", "smallover", "microover",
            "largeunder", "midunder", "smallunder", "microunder"
        ]
        
        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            for market_cap in market_caps:
                params = {
                    "earnings_date": "today_after",
                    "market_cap": market_cap
                }
                
                result = await server.call_tool("earnings_screener", params)
                assert result is not None

    # ===========================================
    # PRICE RANGE GRANULAR TESTING
    # ===========================================

    @pytest.mark.asyncio
    async def test_documented_price_ranges(self):
        """Test all documented price range categories."""
        price_ranges = [
            # Under ranges
            {"price_filter": "u1"}, {"price_filter": "u2"}, {"price_filter": "u5"},
            {"price_filter": "u10"}, {"price_filter": "u20"}, {"price_filter": "u50"},
            
            # Over ranges  
            {"price_filter": "o1"}, {"price_filter": "o5"}, {"price_filter": "o10"},
            {"price_filter": "o20"}, {"price_filter": "o50"}, {"price_filter": "o100"},
            
            # Specific ranges
            {"price_filter": "1to5"}, {"price_filter": "5to10"}, 
            {"price_filter": "10to20"}, {"price_filter": "50to100"},
        ]
        
        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            for price_range in price_ranges:
                params = {
                    "earnings_date": "today_after",
                    **price_range
                }
                
                result = await server.call_tool("earnings_screener", params)
                assert result is not None

    # ===========================================
    # DIVIDEND YIELD TESTING
    # ===========================================

    @pytest.mark.asyncio
    async def test_dividend_yield_categories(self):
        """Test dividend yield categories from documentation."""
        dividend_yields = [
            {"dividend_filter": "none"},      # 0%
            {"dividend_filter": "pos"},       # >0%
            {"dividend_filter": "high"},      # >5%
            {"dividend_filter": "veryhigh"},  # >10%
            {"dividend_filter": "o1"},        # Over 1%
            {"dividend_filter": "o3"},        # Over 3%
            {"dividend_filter": "o5"},        # Over 5%
            {"dividend_filter": "o8"},        # Over 8%
        ]
        
        with patch.object(FinvizScreener, "dividend_growth_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            for dividend_yield in dividend_yields:
                params = {
                    "min_dividend_yield": 1.0,  # Basic requirement
                    **dividend_yield
                }
                
                result = await server.call_tool("dividend_growth_screener", params)
                assert result is not None

    # ===========================================
    # VOLUME PARAMETERS TESTING
    # ===========================================

    @pytest.mark.asyncio
    async def test_volume_parameters(self):
        """Test average volume and relative volume parameters."""
        volume_tests = [
            # Average volume
            {"avg_volume": "u50"},    # Under 50K
            {"avg_volume": "u500"},   # Under 500K
            {"avg_volume": "u1000"},  # Under 1M
            {"avg_volume": "o100"},   # Over 100K
            {"avg_volume": "o1000"},  # Over 1M
            {"avg_volume": "o2000"},  # Over 2M
            
            # Relative volume
            {"rel_volume": "o10"},    # Over 10x
            {"rel_volume": "o5"},     # Over 5x
            {"rel_volume": "o2"},     # Over 2x
            {"rel_volume": "o1.5"},   # Over 1.5x
            {"rel_volume": "u1"},     # Under 1x
        ]
        
        with patch.object(FinvizScreener, "volume_surge_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            for volume_test in volume_tests:
                params = {
                    "market_cap": "large",
                    **volume_test
                }
                
                result = await server.call_tool("volume_surge_screener", params)
                assert result is not None

    # ===========================================
    # ANALYST RECOMMENDATION TESTING
    # ===========================================

    @pytest.mark.asyncio
    async def test_analyst_recommendations(self):
        """Test all analyst recommendation categories."""
        recommendations = [
            "strongbuy", "buybetter", "buy", "holdbetter", 
            "hold", "holdworse", "sell", "sellworse", "strongsell"
        ]
        
        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            for recommendation in recommendations:
                params = {
                    "earnings_date": "today_after",
                    "analyst_recommendation": recommendation
                }
                
                result = await server.call_tool("earnings_screener", params)
                assert result is not None

    # ===========================================
    # DATE PARAMETERS TESTING
    # ===========================================

    @pytest.mark.asyncio
    async def test_comprehensive_date_parameters(self):
        """Test all documented date parameters."""
        earnings_dates = [
            "today", "todaybefore", "todayafter",
            "tomorrow", "tomorrowbefore", "tomorrowafter", 
            "yesterday", "yesterdaybefore", "yesterdayafter",
            "nextdays5", "prevdays5", "thisweek", "nextweek",
            "prevweek", "thismonth"
        ]
        
        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            for earnings_date in earnings_dates:
                params = {"earnings_date": earnings_date}
                
                result = await server.call_tool("earnings_screener", params)
                assert result is not None

    @pytest.mark.asyncio
    async def test_ipo_date_parameters(self):
        """Test IPO date parameters."""
        ipo_dates = [
            "today", "yesterday", "prevweek", "prevmonth", 
            "prevquarter", "prevyear", "prev2yrs", "prev3yrs",
            "prev5yrs", "more1", "more5", "more10", "more25"
        ]
        
        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            for ipo_date in ipo_dates:
                params = {
                    "earnings_date": "today_after",
                    "ipo_date": ipo_date
                }
                
                result = await server.call_tool("earnings_screener", params)
                assert result is not None


class TestCustomRangeParameters:
    """Test custom range (frange) and modal parameters."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup for custom range tests."""
        self.mock_results = {
            "stocks": [],
            "total_count": 0,
            "execution_time": 0.5
        }

    @pytest.mark.asyncio
    async def test_custom_market_cap_ranges(self):
        """Test custom market cap ranges (frange)."""
        custom_market_cap_ranges = [
            {"market_cap": "frange", "cap_min": 1000, "cap_max": 50000},   # Custom mid-cap
            {"market_cap": "frange", "cap_min": 50000, "cap_max": 200000}, # Custom large-cap
            {"market_cap": "frange", "cap_min": 100, "cap_max": 2000},     # Custom small-cap
        ]
        
        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            for market_cap_range in custom_market_cap_ranges:
                params = {
                    "earnings_date": "today_after",
                    **market_cap_range
                }
                
                result = await server.call_tool("earnings_screener", params)
                assert result is not None

    @pytest.mark.asyncio
    async def test_custom_price_ranges(self):
        """Test custom price ranges (frange)."""
        custom_price_ranges = [
            {"price": "frange", "price_min": 10, "price_max": 100},
            {"price": "frange", "price_min": 0.1, "price_max": 5},
            {"price": "frange", "price_min": 100, "price_max": 1000},
        ]
        
        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            for price_range in custom_price_ranges:
                params = {
                    "earnings_date": "today_after",
                    **price_range
                }
                
                result = await server.call_tool("earnings_screener", params)
                assert result is not None

    @pytest.mark.asyncio
    async def test_custom_dividend_yield_ranges(self):
        """Test custom dividend yield ranges."""
        custom_dividend_ranges = [
            {"dividend_yield": "frange", "div_min": 2.0, "div_max": 8.0},
            {"dividend_yield": "frange", "div_min": 0.5, "div_max": 3.0},
            {"dividend_yield": "frange", "div_min": 5.0, "div_max": 15.0},
        ]
        
        with patch.object(FinvizScreener, "dividend_growth_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            for dividend_range in custom_dividend_ranges:
                params = {
                    "min_dividend_yield": 1.0,  # Basic requirement
                    **dividend_range
                }
                
                result = await server.call_tool("dividend_growth_screener", params)
                assert result is not None

    @pytest.mark.asyncio
    async def test_modal_parameters(self):
        """Test modal (custom) parameters."""
        modal_tests = [
            {"exchange": "modal", "custom_exchange": "london"},
            {"sector": "modal", "custom_sector": "emerging_tech"},
            {"analyst_recommendation": "modal", "custom_recommendation": "strong_buy_plus"},
        ]
        
        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            for modal_test in modal_tests:
                params = {
                    "earnings_date": "today_after",
                    **modal_test
                }
                
                result = await server.call_tool("earnings_screener", params)
                assert result is not None


class TestTechnicalAnalysisParameters:
    """Test technical analysis parameters missing from original tests."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup for technical analysis tests."""
        self.mock_results = {
            "stocks": [
                {
                    "ticker": "TEST",
                    "rsi": 45.0,
                    "beta": 1.5,
                    "performance_1w": 5.2,
                    "performance_1m": -2.1,
                    "sma20": 150.0,
                    "sma50": 145.0,
                    "sma200": 140.0,
                    "price": 152.0,
                }
            ],
            "total_count": 1,
            "execution_time": 1.0
        }

    @pytest.mark.asyncio
    async def test_rsi_ranges(self):
        """Test RSI range parameters."""
        rsi_tests = [
            {"rsi": "oversold", "rsi_max": 30},      # Oversold
            {"rsi": "overbought", "rsi_min": 70},    # Overbought  
            {"rsi": "neutral", "rsi_min": 40, "rsi_max": 60},  # Neutral
            {"rsi": "extreme_oversold", "rsi_max": 20},         # Extremely oversold
            {"rsi": "extreme_overbought", "rsi_min": 80},       # Extremely overbought
        ]
        
        with patch.object(FinvizScreener, "technical_analysis_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            for rsi_test in rsi_tests:
                technical_criteria = {
                    "rsi_range": {k: v for k, v in rsi_test.items() if k.startswith("rsi_")},
                    "sma_position": "above_sma50"
                }
                params = {"technical_criteria": technical_criteria}
                
                result = await server.call_tool("technical_analysis_screener", params)
                assert result is not None

    @pytest.mark.asyncio
    async def test_moving_average_positions(self):
        """Test moving average position parameters."""
        sma_positions = [
            "above_sma20", "above_sma50", "above_sma200",
            "below_sma20", "below_sma50", "below_sma200",
            "cross_above_sma20", "cross_below_sma20",
            "cross_above_sma50", "cross_below_sma50"
        ]
        
        with patch.object(FinvizScreener, "technical_analysis_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            for sma_position in sma_positions:
                technical_criteria = {
                    "sma_position": sma_position,
                    "volume_criteria": {"min_relative_volume": 1.0}
                }
                params = {"technical_criteria": technical_criteria}
                
                result = await server.call_tool("technical_analysis_screener", params)
                assert result is not None

    @pytest.mark.asyncio
    async def test_performance_ranges(self):
        """Test performance range parameters."""
        performance_tests = [
            {"performance_1w": "positive"},  # 1 week positive
            {"performance_1w": "negative"},  # 1 week negative  
            {"performance_1m": "o5"},        # 1 month over 5%
            {"performance_1m": "u-5"},       # 1 month under -5%
            {"performance_ytd": "o10"},      # YTD over 10%
            {"performance_1y": "o20"},       # 1 year over 20%
        ]
        
        with patch.object(FinvizScreener, "technical_analysis_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            for performance_test in performance_tests:
                technical_criteria = {
                    "performance_criteria": performance_test,
                    "sma_position": "above_sma50"
                }
                params = {"technical_criteria": technical_criteria}
                
                result = await server.call_tool("technical_analysis_screener", params)
                assert result is not None

    @pytest.mark.asyncio
    async def test_beta_ranges(self):
        """Test beta range parameters."""
        beta_tests = [
            {"beta": "high", "beta_min": 2.0},      # High beta (volatile)
            {"beta": "low", "beta_max": 1.0},       # Low beta (stable)
            {"beta": "negative", "beta_max": 0},    # Negative beta
            {"beta": "normal", "beta_min": 0.8, "beta_max": 1.2},  # Normal beta
        ]
        
        with patch.object(FinvizScreener, "technical_analysis_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            for beta_test in beta_tests:
                technical_criteria = {
                    "beta_range": {k: v for k, v in beta_test.items() if k.startswith("beta_")},
                    "sma_position": "above_sma50"
                }
                params = {"technical_criteria": technical_criteria}
                
                result = await server.call_tool("technical_analysis_screener", params)
                assert result is not None


class TestComplexParameterCombinations:
    """Test complex multi-parameter combinations from documentation."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup for complex combination tests."""
        self.mock_results = {
            "stocks": [],
            "total_count": 0,
            "execution_time": 2.0
        }

    @pytest.mark.asyncio
    async def test_complex_multi_parameter_scenarios(self):
        """Test complex scenarios combining multiple parameter categories."""
        complex_scenarios = [
            {
                "earnings_date": "today_after",
                "exchange": "nasdaq",
                "index": "ndx", 
                "sector": "technology",
                "industry": "semiconductors",
                "country": "usa",
                "market_cap": "large",
                "price_range": "o50",
                "dividend_yield": "none",
                "analyst_recommendation": "buy"
            },
            {
                "earnings_date": "nextweek",
                "exchange": "nyse",
                "sector": "healthcare", 
                "industry": "biotechnology",
                "market_cap": "mid",
                "price_range": "10to50",
                "dividend_yield": "pos",
                "volume_filter": "o1000"
            },
            {
                "earnings_date": "thismonth",
                "sector": "financial",
                "industry": "banksdiversified", 
                "country": "usa",
                "market_cap": "largeover",
                "dividend_yield": "high",
                "analyst_recommendation": "holdbetter"
            }
        ]
        
        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            for scenario in complex_scenarios:
                result = await server.call_tool("earnings_screener", scenario)
                assert result is not None

    @pytest.mark.asyncio
    async def test_contradictory_parameter_combinations(self):
        """Test handling of contradictory parameter combinations."""
        contradictory_combinations = [
            # Small cap but S&P 500 member (contradiction)
            {
                "earnings_date": "today_after",
                "market_cap": "nano",
                "index": "sp500"
            },
            # High dividend tech stock (unusual)
            {
                "earnings_date": "today_after", 
                "sector": "technology",
                "dividend_yield": "veryhigh"
            },
            # Foreign stock on US exchange (contradiction)
            {
                "earnings_date": "today_after",
                "country": "china",
                "exchange": "nyse"
            }
        ]
        
        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            for combination in contradictory_combinations:
                # Should handle gracefully, possibly returning empty results
                result = await server.call_tool("earnings_screener", combination)
                assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])