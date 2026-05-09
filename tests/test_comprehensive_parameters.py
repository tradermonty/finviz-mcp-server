#!/usr/bin/env python3
"""
Comprehensive parameter validation tests based on finviz_screening_parameters.md.

These tests intentionally split coverage between the high-level MCP tools and
the raw ``custom_screener`` tool:

* high-level tools only receive arguments that are in their current signature;
* broad Finviz filter-token coverage goes through ``custom_screener`` so stale
  arguments cannot be silently dropped by FastMCP.
"""

import logging
from unittest.mock import patch

import pytest

from src.finviz_client.screener import FinvizScreener
from src.server import server
from tests import factories

logger = logging.getLogger(__name__)


def _content_list(result):
    return result[0] if isinstance(result, tuple) else result


def _first_text(result) -> str:
    content = _content_list(result)
    first_item = content[0] if isinstance(content, list) else content
    return first_item.text if hasattr(first_item, "text") else str(first_item)


def _make_parameter_stock(index: int = 0):
    return factories.make_stock_data(
        ticker=f"C{index:03d}",
        company_name=f"Comprehensive Test {index}",
        sector="Technology",
        industry="Software",
        price=150.0 + index,
        volume=1_000_000 + index * 100_000,
        market_cap=3_000_000.0 + index * 100.0,
        pe_ratio=25.0 + index,
        eps=6.0 + index * 0.5,
        dividend_yield=0.5 + index * 0.1,
        rsi=45.0 + index,
        beta=1.2 + index * 0.1,
        performance_1w=5.0,
        performance_1m=-2.0,
        performance_ytd=10.0,
        performance_1y=20.0,
        sma_20=150.0,
        sma_50=145.0,
        sma_200=140.0,
    )


def _make_stock_results(count: int = 2):
    return [_make_parameter_stock(i) for i in range(count)]


class CustomFilterAssertions:
    """Reusable assertions for raw Finviz filter-token coverage."""

    mock_results = None

    async def assert_custom_filters(self, filter_codes: list[str]) -> None:
        with patch("src.server.finviz_client") as mock_client:
            mock_client.screen_stocks_raw.return_value = self.mock_results

            for filter_code in filter_codes:
                result = await server.call_tool(
                    "custom_screener", {"filters": filter_code}
                )
                assert "Custom Screener Results" in _first_text(result)

            observed_filters = [
                call.kwargs["filters"]
                for call in mock_client.screen_stocks_raw.call_args_list
            ]
            assert observed_filters == filter_codes


class TestComprehensiveParameters(CustomFilterAssertions):
    """Test comprehensive parameter coverage based on Finviz documentation."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup model-shaped mock results for all tests."""
        self.mock_results = _make_stock_results()

    # ===========================================
    # EXCHANGE PARAMETERS
    # ===========================================

    @pytest.mark.asyncio
    async def test_exchange_parameters(self):
        """Test all documented exchange parameters as raw Finviz filters."""
        exchange_filters = [
            "cap_large",  # no exchange filter selected
            "exch_amex",
            "exch_cboe",
            "exch_nasd",
            "exch_nyse",
            "exch_modal",
        ]

        await self.assert_custom_filters(exchange_filters)

    # ===========================================
    # INDEX MEMBERSHIP PARAMETERS
    # ===========================================

    @pytest.mark.asyncio
    async def test_index_parameters(self):
        """Test all documented index membership parameters."""
        index_filters = [
            "cap_large",  # no index filter selected
            "idx_sp500",
            "idx_ndx",
            "idx_dji",
            "idx_rut",
            "idx_modal",
        ]

        await self.assert_custom_filters(index_filters)

    # ===========================================
    # COMPREHENSIVE SECTOR TESTING
    # ===========================================

    @pytest.mark.asyncio
    async def test_all_documented_sectors(self):
        """Test all sectors documented in the Finviz parameters."""
        sectors = [
            "basicmaterials",
            "communicationservices",
            "consumercyclical",
            "consumerdefensive",
            "energy",
            "financial",
            "healthcare",
            "industrials",
            "realestate",
            "technology",
            "utilities",
        ]

        await self.assert_custom_filters([f"sec_{sector}" for sector in sectors])

    # ===========================================
    # COMPREHENSIVE INDUSTRY TESTING
    # ===========================================

    @pytest.mark.asyncio
    async def test_key_industries(self):
        """Test key industries from the comprehensive industry list."""
        key_industries = [
            "biotechnology",
            "semiconductors",
            "softwareapplication",
            "softwareinfrastructure",
            "oilgasep",
            "banksdiversified",
            "banksregional",
            "pharmaceuticalretailers",
            "airlines",
            "utilitiesregulatedelectric",
            "realestate",
            "gold",
            "silver",
            "solar",
            "gambling",
            "restaurants",
        ]

        await self.assert_custom_filters(
            [f"ind_{industry}" for industry in key_industries]
        )

    # ===========================================
    # COUNTRY/GEOGRAPHIC PARAMETERS
    # ===========================================

    @pytest.mark.asyncio
    async def test_geographic_parameters(self):
        """Test geographic/country parameters."""
        countries = [
            "usa",
            "notusa",
            "asia",
            "europe",
            "latinamerica",
            "bric",
            "china",
            "japan",
            "germany",
            "unitedkingdom",
            "canada",
            "australia",
            "india",
            "brazil",
            "singapore",
            "hongkong",
        ]

        await self.assert_custom_filters([f"geo_{country}" for country in countries])

    # ===========================================
    # MARKET CAP GRANULAR TESTING
    # ===========================================

    @pytest.mark.asyncio
    async def test_all_market_cap_categories(self):
        """Test all documented market cap categories."""
        market_caps = [
            "mega",
            "large",
            "mid",
            "small",
            "micro",
            "nano",
            "largeover",
            "midover",
            "smallover",
            "microover",
            "largeunder",
            "midunder",
            "smallunder",
            "microunder",
        ]

        await self.assert_custom_filters([f"cap_{cap}" for cap in market_caps])

    # ===========================================
    # PRICE RANGE GRANULAR TESTING
    # ===========================================

    @pytest.mark.asyncio
    async def test_documented_price_ranges(self):
        """Test all documented price range categories."""
        price_filters = [
            "sh_price_u1",
            "sh_price_u2",
            "sh_price_u5",
            "sh_price_u10",
            "sh_price_u20",
            "sh_price_u50",
            "sh_price_o1",
            "sh_price_o5",
            "sh_price_o10",
            "sh_price_o20",
            "sh_price_o50",
            "sh_price_o100",
            "sh_price_1to5",
            "sh_price_5to10",
            "sh_price_10to20",
            "sh_price_50to100",
        ]

        await self.assert_custom_filters(price_filters)

    # ===========================================
    # DIVIDEND YIELD TESTING
    # ===========================================

    @pytest.mark.asyncio
    async def test_dividend_yield_categories(self):
        """Test dividend yield categories from documentation."""
        dividend_filters = [
            "fa_div_none",
            "fa_div_pos",
            "fa_div_high",
            "fa_div_veryhigh",
            "fa_div_o1",
            "fa_div_o3",
            "fa_div_o5",
            "fa_div_o8",
        ]

        await self.assert_custom_filters(dividend_filters)

    # ===========================================
    # VOLUME PARAMETERS TESTING
    # ===========================================

    @pytest.mark.asyncio
    async def test_volume_parameters(self):
        """Test average volume and relative volume parameters."""
        volume_filters = [
            "sh_avgvol_u50",
            "sh_avgvol_u500",
            "sh_avgvol_u1000",
            "sh_avgvol_o100",
            "sh_avgvol_o1000",
            "sh_avgvol_o2000",
            "sh_relvol_o10",
            "sh_relvol_o5",
            "sh_relvol_o2",
            "sh_relvol_o1.5",
            "sh_relvol_u1",
        ]

        await self.assert_custom_filters(volume_filters)

    # ===========================================
    # ANALYST RECOMMENDATION TESTING
    # ===========================================

    @pytest.mark.asyncio
    async def test_analyst_recommendations(self):
        """Test all analyst recommendation categories."""
        recommendations = [
            "strongbuy",
            "buybetter",
            "buy",
            "holdbetter",
            "hold",
            "holdworse",
            "sell",
            "sellworse",
            "strongsell",
        ]

        await self.assert_custom_filters(
            [f"an_recom_{recommendation}" for recommendation in recommendations]
        )

    # ===========================================
    # DATE PARAMETERS TESTING
    # ===========================================

    @pytest.mark.asyncio
    async def test_comprehensive_date_parameters(self):
        """Test all documented date parameters."""
        earnings_dates = [
            "today",
            "todaybefore",
            "todayafter",
            "tomorrow",
            "tomorrowbefore",
            "tomorrowafter",
            "yesterday",
            "yesterdaybefore",
            "yesterdayafter",
            "nextdays5",
            "prevdays5",
            "thisweek",
            "nextweek",
            "prevweek",
            "thismonth",
        ]

        await self.assert_custom_filters(
            [f"earningsdate_{earnings_date}" for earnings_date in earnings_dates]
        )

    @pytest.mark.asyncio
    async def test_ipo_date_parameters(self):
        """Test IPO date parameters."""
        ipo_dates = [
            "today",
            "yesterday",
            "prevweek",
            "prevmonth",
            "prevquarter",
            "prevyear",
            "prev2yrs",
            "prev3yrs",
            "prev5yrs",
            "more1",
            "more5",
            "more10",
            "more25",
        ]

        await self.assert_custom_filters(
            [f"ipodate_{ipo_date}" for ipo_date in ipo_dates]
        )


class TestCustomRangeParameters(CustomFilterAssertions):
    """Test custom range (frange) and modal parameters."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup for custom range tests."""
        self.mock_results = _make_stock_results()

    @pytest.mark.asyncio
    async def test_custom_market_cap_ranges(self):
        """Test custom market cap ranges (frange)."""
        custom_market_cap_filters = [
            "cap_frange_1000to50000",
            "cap_frange_50000to200000",
            "cap_frange_100to2000",
        ]

        await self.assert_custom_filters(custom_market_cap_filters)

    @pytest.mark.asyncio
    async def test_custom_price_ranges(self):
        """Test custom price ranges (frange)."""
        custom_price_filters = [
            "sh_price_frange_10to100",
            "sh_price_frange_0.1to5",
            "sh_price_frange_100to1000",
        ]

        await self.assert_custom_filters(custom_price_filters)

    @pytest.mark.asyncio
    async def test_custom_dividend_yield_ranges(self):
        """Test custom dividend yield ranges."""
        custom_dividend_filters = [
            "fa_div_frange_2.0to8.0",
            "fa_div_frange_0.5to3.0",
            "fa_div_frange_5.0to15.0",
        ]

        await self.assert_custom_filters(custom_dividend_filters)

    @pytest.mark.asyncio
    async def test_modal_parameters(self):
        """Test modal (custom) parameters as raw filter tokens."""
        modal_filters = [
            "exch_modal_london",
            "sec_modal_emerging_tech",
            "an_recom_modal_strong_buy_plus",
        ]

        await self.assert_custom_filters(modal_filters)


class TestTechnicalAnalysisParameters(CustomFilterAssertions):
    """Test technical analysis parameters missing from original tests."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup for technical analysis tests."""
        self.mock_results = _make_stock_results()

    @pytest.mark.asyncio
    async def test_rsi_ranges(self):
        """Test current MCP RSI range parameters."""
        rsi_tests = [
            {"rsi_max": 30},  # Oversold
            {"rsi_min": 70},  # Overbought
            {"rsi_min": 40, "rsi_max": 60},  # Neutral
            {"rsi_max": 20},  # Extremely oversold
            {"rsi_min": 80},  # Extremely overbought
        ]

        with patch.object(FinvizScreener, "screen_stocks") as mock_screen:
            mock_screen.return_value = self.mock_results

            for rsi_params in rsi_tests:
                params = {"price_vs_sma50": "above", **rsi_params}

                result = await server.call_tool("technical_analysis_screener", params)
                assert result is not None

            observed_filters = [call.args[0] for call in mock_screen.call_args_list]
            assert observed_filters == [
                {"rsi_max": 30, "sma50_above": True},
                {"rsi_min": 70, "sma50_above": True},
                {"rsi_min": 40, "rsi_max": 60, "sma50_above": True},
                {"rsi_max": 20, "sma50_above": True},
                {"rsi_min": 80, "sma50_above": True},
            ]

    @pytest.mark.asyncio
    async def test_moving_average_positions(self):
        """Test moving-average position parameters and raw crossover filters."""
        supported_positions = [
            ("price_vs_sma20", "above", {"sma20_above": True}),
            ("price_vs_sma50", "above", {"sma50_above": True}),
            ("price_vs_sma200", "above", {"sma200_above": True}),
            ("price_vs_sma20", "below", {"sma20_below": True}),
            ("price_vs_sma50", "below", {"sma50_below": True}),
            ("price_vs_sma200", "below", {"sma200_below": True}),
        ]

        with patch.object(FinvizScreener, "screen_stocks") as mock_screen:
            mock_screen.return_value = self.mock_results

            for arg_name, value, _expected_filters in supported_positions:
                result = await server.call_tool(
                    "technical_analysis_screener", {arg_name: value}
                )
                assert result is not None

            observed_filters = [call.args[0] for call in mock_screen.call_args_list]
            assert observed_filters == [
                expected for _arg_name, _value, expected in supported_positions
            ]

        await self.assert_custom_filters(
            [
                "ta_cross20_above",
                "ta_cross20_below",
                "ta_cross50_above",
                "ta_cross50_below",
            ]
        )

    @pytest.mark.asyncio
    async def test_performance_ranges(self):
        """Test performance range parameters as raw Finviz filters."""
        performance_filters = [
            "ta_perf_1wpos",
            "ta_perf_1wneg",
            "ta_perf_1mo5",
            "ta_perf_1mu-5",
            "ta_perf_ytdo10",
            "ta_perf_1yo20",
        ]

        await self.assert_custom_filters(performance_filters)

    @pytest.mark.asyncio
    async def test_beta_ranges(self):
        """Test beta range parameters as raw Finviz filters."""
        beta_filters = [
            "fa_beta_o2",
            "fa_beta_u1",
            "fa_beta_u0",
            "fa_beta_0.8to1.2",
        ]

        await self.assert_custom_filters(beta_filters)


class TestComplexParameterCombinations(CustomFilterAssertions):
    """Test complex multi-parameter combinations from documentation."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup for complex combination tests."""
        self.mock_results = _make_stock_results()

    @pytest.mark.asyncio
    async def test_complex_multi_parameter_scenarios(self):
        """Test complex scenarios combining multiple parameter categories."""
        complex_scenarios = [
            ",".join(
                [
                    "earningsdate_todayafter",
                    "exch_nasd",
                    "idx_ndx",
                    "sec_technology",
                    "ind_semiconductors",
                    "geo_usa",
                    "cap_large",
                    "sh_price_o50",
                    "fa_div_none",
                    "an_recom_buy",
                ]
            ),
            ",".join(
                [
                    "earningsdate_nextweek",
                    "exch_nyse",
                    "sec_healthcare",
                    "ind_biotechnology",
                    "cap_mid",
                    "sh_price_10to50",
                    "fa_div_pos",
                    "sh_avgvol_o1000",
                ]
            ),
            ",".join(
                [
                    "earningsdate_thismonth",
                    "sec_financial",
                    "ind_banksdiversified",
                    "geo_usa",
                    "cap_largeover",
                    "fa_div_high",
                    "an_recom_holdbetter",
                ]
            ),
        ]

        await self.assert_custom_filters(complex_scenarios)

    @pytest.mark.asyncio
    async def test_contradictory_parameter_combinations(self):
        """Test forwarding of unusual or contradictory raw filter combinations."""
        contradictory_combinations = [
            "earningsdate_todayafter,cap_nano,idx_sp500",
            "earningsdate_todayafter,sec_technology,fa_div_veryhigh",
            "earningsdate_todayafter,geo_china,exch_nyse",
        ]

        await self.assert_custom_filters(contradictory_combinations)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
