#!/usr/bin/env python3
"""
Financial parameters and ratios testing based on Finviz documentation.
Tests P/E ratios, financial health metrics, profitability ratios, and ownership parameters.
"""

import pytest
import asyncio
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, patch
import logging

from src.server import server
from src.finviz_client.screener import FinvizScreener
from src.finviz_client.base import FinvizClient

logger = logging.getLogger(__name__)


class TestFinancialRatioParameters:
    """Test financial ratio parameters not covered in original tests."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup mock results for financial ratio tests."""
        self.mock_results = {
            "stocks": [
                {
                    "ticker": "AAPL",
                    "company": "Apple Inc.",
                    "pe_ratio": 25.5,
                    "peg_ratio": 1.2,
                    "price_book": 8.5,
                    "debt_equity": 0.8,
                    "roe": 22.5,
                    "roa": 12.3,
                    "gross_margin": 42.5,
                    "operating_margin": 28.1,
                    "net_margin": 23.4,
                    "insider_ownership": 15.2,
                    "institutional_ownership": 65.8,
                    "float_shares": 15800000000,
                    "shares_outstanding": 16200000000,
                }
            ],
            "total_count": 1,
            "execution_time": 1.5,
        }

    # ===========================================
    # P/E RATIO TESTING
    # ===========================================

    @pytest.mark.asyncio
    async def test_pe_ratio_ranges(self):
        """Test P/E ratio ranges for value vs growth stock identification."""
        pe_ratio_tests = [
            # Value stocks (low P/E)
            {"pe_ratio": "low", "pe_max": 15},
            {"pe_ratio": "value", "pe_max": 12},
            {"pe_ratio": "deep_value", "pe_max": 10},
            
            # Growth stocks (high P/E)
            {"pe_ratio": "growth", "pe_min": 25},
            {"pe_ratio": "high_growth", "pe_min": 30},
            {"pe_ratio": "momentum", "pe_min": 40},
            
            # Reasonable ranges
            {"pe_ratio": "reasonable", "pe_min": 10, "pe_max": 25},
            {"pe_ratio": "moderate", "pe_min": 15, "pe_max": 30},
            
            # Custom ranges
            {"pe_ratio": "frange", "pe_min": 8, "pe_max": 20},
            {"pe_ratio": "frange", "pe_min": 20, "pe_max": 50},
        ]
        
        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            for pe_test in pe_ratio_tests:
                params = {
                    "earnings_date": "today_after",
                    **pe_test
                }
                
                result = await server.call_tool("earnings_screener", params)
                assert result is not None

    # ===========================================
    # PEG RATIO TESTING
    # ===========================================

    @pytest.mark.asyncio
    async def test_peg_ratio_analysis(self):
        """Test PEG ratio for growth vs value analysis."""
        peg_ratio_tests = [
            # Undervalued growth (PEG < 1)
            {"peg_ratio": "undervalued", "peg_max": 1.0},
            {"peg_ratio": "bargain", "peg_max": 0.8},
            {"peg_ratio": "deep_value", "peg_max": 0.5},
            
            # Fairly valued (PEG ~ 1)
            {"peg_ratio": "fair", "peg_min": 0.8, "peg_max": 1.2},
            
            # Overvalued growth (PEG > 1)  
            {"peg_ratio": "overvalued", "peg_min": 1.5},
            {"peg_ratio": "expensive", "peg_min": 2.0},
            
            # Custom ranges
            {"peg_ratio": "frange", "peg_min": 0.5, "peg_max": 1.5},
        ]
        
        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            for peg_test in peg_ratio_tests:
                params = {
                    "earnings_date": "today_after",
                    **peg_test
                }
                
                result = await server.call_tool("earnings_screener", params)
                assert result is not None

    # ===========================================
    # PRICE-TO-BOOK RATIO TESTING
    # ===========================================

    @pytest.mark.asyncio
    async def test_price_book_ratios(self):
        """Test Price-to-Book ratios for asset-based valuation."""
        price_book_tests = [
            # Value stocks (low P/B)
            {"price_book": "undervalued", "pb_max": 1.0},
            {"price_book": "asset_play", "pb_max": 0.8},
            {"price_book": "net_net", "pb_max": 0.5},
            
            # Growth stocks (high P/B)
            {"price_book": "growth", "pb_min": 3.0},
            {"price_book": "premium", "pb_min": 5.0},
            {"price_book": "expensive", "pb_min": 10.0},
            
            # Reasonable ranges
            {"price_book": "reasonable", "pb_min": 1.0, "pb_max": 3.0},
            {"price_book": "moderate", "pb_min": 1.5, "pb_max": 4.0},
        ]
        
        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            for pb_test in price_book_tests:
                params = {
                    "earnings_date": "today_after",
                    **pb_test
                }
                
                result = await server.call_tool("earnings_screener", params)
                assert result is not None

    # ===========================================
    # DEBT-TO-EQUITY RATIO TESTING
    # ===========================================

    @pytest.mark.asyncio
    async def test_debt_equity_ratios(self):
        """Test Debt-to-Equity ratios for financial health assessment."""
        debt_equity_tests = [
            # Low debt (financially strong)
            {"debt_equity": "low", "de_max": 0.3},
            {"debt_equity": "conservative", "de_max": 0.5},
            {"debt_equity": "safe", "de_max": 1.0},
            
            # High debt (leveraged)
            {"debt_equity": "leveraged", "de_min": 1.0},
            {"debt_equity": "high_leverage", "de_min": 2.0},
            {"debt_equity": "risky", "de_min": 3.0},
            
            # No debt
            {"debt_equity": "debt_free", "de_max": 0.1},
            
            # Custom ranges
            {"debt_equity": "frange", "de_min": 0.2, "de_max": 1.5},
        ]
        
        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            for de_test in debt_equity_tests:
                params = {
                    "earnings_date": "today_after",
                    **de_test
                }
                
                result = await server.call_tool("earnings_screener", params)
                assert result is not None

    # ===========================================
    # PROFITABILITY METRICS TESTING
    # ===========================================

    @pytest.mark.asyncio
    async def test_roe_analysis(self):
        """Test Return on Equity (ROE) for profitability assessment."""
        roe_tests = [
            # High profitability
            {"roe": "excellent", "roe_min": 20.0},
            {"roe": "high", "roe_min": 15.0},
            {"roe": "good", "roe_min": 12.0},
            
            # Average profitability
            {"roe": "average", "roe_min": 8.0, "roe_max": 15.0},
            {"roe": "moderate", "roe_min": 5.0, "roe_max": 12.0},
            
            # Poor profitability
            {"roe": "poor", "roe_max": 5.0},
            {"roe": "negative", "roe_max": 0.0},
            
            # Custom ranges
            {"roe": "frange", "roe_min": 10.0, "roe_max": 25.0},
        ]
        
        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            for roe_test in roe_tests:
                params = {
                    "earnings_date": "today_after",
                    **roe_test
                }
                
                result = await server.call_tool("earnings_screener", params)
                assert result is not None

    @pytest.mark.asyncio
    async def test_roa_analysis(self):
        """Test Return on Assets (ROA) for efficiency assessment."""
        roa_tests = [
            # High efficiency
            {"roa": "excellent", "roa_min": 10.0},
            {"roa": "high", "roa_min": 7.0},
            {"roa": "good", "roa_min": 5.0},
            
            # Average efficiency
            {"roa": "average", "roa_min": 2.0, "roa_max": 7.0},
            {"roa": "moderate", "roa_min": 1.0, "roa_max": 5.0},
            
            # Poor efficiency
            {"roa": "poor", "roa_max": 2.0},
            {"roa": "negative", "roa_max": 0.0},
        ]
        
        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            for roa_test in roa_tests:
                params = {
                    "earnings_date": "today_after",
                    **roa_test
                }
                
                result = await server.call_tool("earnings_screener", params)
                assert result is not None

    # ===========================================
    # MARGIN ANALYSIS TESTING
    # ===========================================

    @pytest.mark.asyncio
    async def test_profit_margins(self):
        """Test various profit margin metrics."""
        margin_tests = [
            # Gross Margin
            {"gross_margin": "high", "gm_min": 40.0},
            {"gross_margin": "excellent", "gm_min": 50.0},
            {"gross_margin": "moderate", "gm_min": 20.0, "gm_max": 40.0},
            {"gross_margin": "low", "gm_max": 20.0},
            
            # Operating Margin
            {"operating_margin": "high", "om_min": 20.0},
            {"operating_margin": "excellent", "om_min": 30.0},
            {"operating_margin": "moderate", "om_min": 10.0, "om_max": 20.0},
            {"operating_margin": "low", "om_max": 10.0},
            
            # Net Margin
            {"net_margin": "high", "nm_min": 15.0},
            {"net_margin": "excellent", "nm_min": 20.0},
            {"net_margin": "moderate", "nm_min": 5.0, "nm_max": 15.0},
            {"net_margin": "low", "nm_max": 5.0},
        ]
        
        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            for margin_test in margin_tests:
                params = {
                    "earnings_date": "today_after",
                    **margin_test
                }
                
                result = await server.call_tool("earnings_screener", params)
                assert result is not None


class TestOwnershipParameters:
    """Test ownership structure parameters from Finviz documentation."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup for ownership tests."""
        self.mock_results = {
            "stocks": [
                {
                    "ticker": "TEST",
                    "insider_ownership": 15.2,
                    "institutional_ownership": 65.8,
                    "float_percentage": 85.5,
                    "shares_outstanding": 1000000000,
                }
            ],
            "total_count": 1,
            "execution_time": 1.0
        }

    @pytest.mark.asyncio
    async def test_insider_ownership_ranges(self):
        """Test insider ownership percentage ranges."""
        insider_ownership_tests = [
            # High insider ownership (aligned interests)
            {"insider_ownership": "high", "insider_min": 20.0},
            {"insider_ownership": "very_high", "insider_min": 30.0},
            {"insider_ownership": "controlled", "insider_min": 50.0},
            
            # Low insider ownership
            {"insider_ownership": "low", "insider_max": 5.0},
            {"insider_ownership": "minimal", "insider_max": 2.0},
            
            # Moderate insider ownership
            {"insider_ownership": "moderate", "insider_min": 5.0, "insider_max": 20.0},
            {"insider_ownership": "balanced", "insider_min": 10.0, "insider_max": 25.0},
            
            # Custom ranges
            {"insider_ownership": "frange", "insider_min": 15.0, "insider_max": 40.0},
        ]
        
        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            for insider_test in insider_ownership_tests:
                params = {
                    "earnings_date": "today_after",
                    **insider_test
                }
                
                result = await server.call_tool("earnings_screener", params)
                assert result is not None

    @pytest.mark.asyncio
    async def test_institutional_ownership_ranges(self):
        """Test institutional ownership percentage ranges."""
        institutional_tests = [
            # High institutional ownership (established companies)
            {"institutional_ownership": "high", "institutional_min": 70.0},
            {"institutional_ownership": "very_high", "institutional_min": 80.0},
            {"institutional_ownership": "dominated", "institutional_min": 90.0},
            
            # Low institutional ownership (retail favorites)
            {"institutional_ownership": "low", "institutional_max": 30.0},
            {"institutional_ownership": "minimal", "institutional_max": 20.0},
            {"institutional_ownership": "retail", "institutional_max": 40.0},
            
            # Moderate institutional ownership
            {"institutional_ownership": "moderate", "institutional_min": 40.0, "institutional_max": 70.0},
            {"institutional_ownership": "balanced", "institutional_min": 50.0, "institutional_max": 80.0},
        ]
        
        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            for institutional_test in institutional_tests:
                params = {
                    "earnings_date": "today_after",
                    **institutional_test
                }
                
                result = await server.call_tool("earnings_screener", params)
                assert result is not None

    @pytest.mark.asyncio
    async def test_float_size_categories(self):
        """Test float size categories from documentation."""
        float_tests = [
            # Small float (easier to move)
            {"float": "small", "float_max": 50000000},      # Under 50M
            {"float": "very_small", "float_max": 20000000}, # Under 20M
            {"float": "tiny", "float_max": 10000000},       # Under 10M
            
            # Large float (stable)
            {"float": "large", "float_min": 500000000},     # Over 500M
            {"float": "very_large", "float_min": 1000000000}, # Over 1B
            {"float": "massive", "float_min": 5000000000},  # Over 5B
            
            # Medium float
            {"float": "medium", "float_min": 50000000, "float_max": 500000000},
            
            # Float percentage tests
            {"float_percentage": "low", "float_pct_max": 50.0},    # Under 50%
            {"float_percentage": "high", "float_pct_min": 90.0},   # Over 90%
            {"float_percentage": "normal", "float_pct_min": 70.0, "float_pct_max": 95.0},
        ]
        
        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            for float_test in float_tests:
                params = {
                    "earnings_date": "today_after",
                    **float_test
                }
                
                result = await server.call_tool("earnings_screener", params)
                assert result is not None

    @pytest.mark.asyncio
    async def test_shares_outstanding_ranges(self):
        """Test shares outstanding ranges from documentation."""
        shares_outstanding_tests = [
            # Low share count
            {"shares_outstanding": "u1"},    # Under 1M
            {"shares_outstanding": "u5"},    # Under 5M  
            {"shares_outstanding": "u10"},   # Under 10M
            {"shares_outstanding": "u50"},   # Under 50M
            {"shares_outstanding": "u100"},  # Under 100M
            
            # High share count
            {"shares_outstanding": "o100"},  # Over 100M
            {"shares_outstanding": "o500"},  # Over 500M
            {"shares_outstanding": "o1000"}, # Over 1B
            {"shares_outstanding": "o5000"}, # Over 5B
            
            # Custom ranges
            {"shares_outstanding": "frange", "shares_min": 100000000, "shares_max": 1000000000},
        ]
        
        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            for shares_test in shares_outstanding_tests:
                params = {
                    "earnings_date": "today_after",
                    **shares_test
                }
                
                result = await server.call_tool("earnings_screener", params)
                assert result is not None


class TestShortInterestParameters:
    """Test short interest and option parameters from documentation."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup for short interest tests."""
        self.mock_results = {
            "stocks": [
                {
                    "ticker": "TEST",
                    "short_interest": 12.5,
                    "option_available": True,
                    "shortable": True,
                    "short_sale_restricted": False,
                }
            ],
            "total_count": 1,
            "execution_time": 1.0
        }

    @pytest.mark.asyncio
    async def test_short_interest_ranges(self):
        """Test short interest percentage ranges from documentation."""
        short_interest_tests = [
            # Low short interest
            {"short_interest": "low", "short_max": 5.0},
            {"short_interest": "minimal", "short_max": 2.0},
            
            # High short interest (squeeze potential)
            {"short_interest": "high", "short_min": 20.0},
            {"short_interest": "very_high", "short_min": 30.0},
            {"short_interest": "extreme", "short_min": 40.0},
            
            # Moderate short interest
            {"short_interest": "moderate", "short_min": 5.0, "short_max": 20.0},
            
            # Specific ranges from documentation
            {"short_interest": "u5"},   # Under 5%
            {"short_interest": "u10"},  # Under 10%
            {"short_interest": "u15"},  # Under 15%
            {"short_interest": "o10"},  # Over 10%
            {"short_interest": "o20"},  # Over 20%
            {"short_interest": "o30"},  # Over 30%
            
            # Custom ranges
            {"short_interest": "frange", "short_min": 8.0, "short_max": 25.0},
        ]
        
        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            for short_test in short_interest_tests:
                params = {
                    "earnings_date": "today_after",
                    **short_test
                }
                
                result = await server.call_tool("earnings_screener", params)
                assert result is not None

    @pytest.mark.asyncio
    async def test_option_short_availability(self):
        """Test option and short availability parameters."""
        option_short_tests = [
            # Option availability
            {"option_short": "option"},      # Optionable
            {"option_short": "notoption"},   # Not optionable
            
            # Short availability
            {"option_short": "short"},       # Shortable
            {"option_short": "notshort"},    # Not shortable
            
            # Combinations
            {"option_short": "optionshort"},       # Both available
            {"option_short": "optionnotshort"},    # Options only
            {"option_short": "notoptionshort"},    # Short only
            {"option_short": "notoptionnotshort"}, # Neither available
            
            # Special conditions
            {"option_short": "shortsalerestricted"},    # SSR active
            {"option_short": "notshortsalerestricted"}, # No SSR
            {"option_short": "halted"},                 # Trading halted
            {"option_short": "nothalted"},              # Not halted
        ]
        
        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            for option_test in option_short_tests:
                params = {
                    "earnings_date": "today_after",
                    **option_test
                }
                
                result = await server.call_tool("earnings_screener", params)
                assert result is not None

    @pytest.mark.asyncio
    async def test_short_availability_thresholds(self):
        """Test short availability thresholds by share count and dollar value."""
        short_availability_tests = [
            # Share count based availability
            {"short_available_shares": "so10k"},   # Over 10K shares
            {"short_available_shares": "so100k"},  # Over 100K shares
            {"short_available_shares": "so1m"},    # Over 1M shares
            {"short_available_shares": "so10m"},   # Over 10M shares
            
            # Dollar value based availability
            {"short_available_usd": "uo1m"},    # Over $1M available
            {"short_available_usd": "uo10m"},   # Over $10M available
            {"short_available_usd": "uo100m"},  # Over $100M available
            {"short_available_usd": "uo1b"},    # Over $1B available
        ]
        
        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            for short_avail_test in short_availability_tests:
                params = {
                    "earnings_date": "today_after",
                    **short_avail_test
                }
                
                result = await server.call_tool("earnings_screener", params)
                assert result is not None


class TestTargetPriceParameters:
    """Test target price parameters from documentation."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup for target price tests."""
        self.mock_results = {
            "stocks": [
                {
                    "ticker": "TEST", 
                    "price": 100.0,
                    "target_price": 120.0,
                    "target_price_percentage": 20.0,
                }
            ],
            "total_count": 1,
            "execution_time": 1.0
        }

    @pytest.mark.asyncio
    async def test_target_price_ranges(self):
        """Test target price percentage ranges from documentation."""
        target_price_tests = [
            # Above current price (upside potential)
            {"target_price": "a50"},   # 50% above price
            {"target_price": "a40"},   # 40% above price  
            {"target_price": "a30"},   # 30% above price
            {"target_price": "a20"},   # 20% above price
            {"target_price": "a10"},   # 10% above price
            {"target_price": "a5"},    # 5% above price
            {"target_price": "above"}, # Any amount above
            
            # Below current price (downside risk)
            {"target_price": "below"}, # Any amount below
            {"target_price": "b5"},    # 5% below price
            {"target_price": "b10"},   # 10% below price
            {"target_price": "b20"},   # 20% below price
            {"target_price": "b30"},   # 30% below price
            {"target_price": "b40"},   # 40% below price
            {"target_price": "b50"},   # 50% below price
            
            # Custom target price ranges
            {"target_price": "modal", "target_custom": "15% above with high confidence"},
        ]
        
        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.return_value = self.mock_results

            for target_test in target_price_tests:
                params = {
                    "earnings_date": "today_after",
                    **target_test
                }
                
                result = await server.call_tool("earnings_screener", params)
                assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])