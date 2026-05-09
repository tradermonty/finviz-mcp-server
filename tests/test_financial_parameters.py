#!/usr/bin/env python3
"""
Financial parameters and ratios testing based on Finviz documentation.

The high-level earnings wrapper does not accept arbitrary financial-ratio
arguments. These tests therefore exercise the raw Finviz filter contract via
``custom_screener`` and assert that every documented financial filter is
forwarded to ``screen_stocks_raw`` without falling through to live API calls.
"""

import logging
from unittest.mock import patch

import pytest

from src.server import server
from tests import factories

logger = logging.getLogger(__name__)


def _content_list(result):
    return result[0] if isinstance(result, tuple) else result


def _first_text(result) -> str:
    content = _content_list(result)
    first_item = content[0] if isinstance(content, list) else content
    return first_item.text if hasattr(first_item, "text") else str(first_item)


def _make_financial_stock(index: int = 0):
    return factories.make_stock_data(
        ticker=f"F{index:03d}",
        company_name=f"Financial Test {index}",
        sector="Technology",
        industry="Software",
        price=100.0 + index,
        target_price=120.0 + index,
        pe_ratio=25.5,
        peg=1.2,
        pb_ratio=8.5,
        debt_to_equity=0.8,
        roe=22.5,
        roa=12.3,
        gross_margin=42.5,
        operating_margin=28.1,
        profit_margin=23.4,
        insider_ownership=15.2,
        institutional_ownership=65.8,
        float_percentage=85.5,
        shares_outstanding=1_620_000_000,
        shares_float=1_580_000_000,
        short_interest=12.5,
        shortable=True,
        optionable=True,
    )


def _make_stock_results(count: int = 2):
    return [_make_financial_stock(i) for i in range(count)]


class CustomFilterAssertions:
    """Reusable assertions for financial raw-filter coverage."""

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


class TestFinancialRatioParameters(CustomFilterAssertions):
    """Test financial ratio parameters not covered in original tests."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup model-shaped mock results for financial ratio tests."""
        self.mock_results = _make_stock_results()

    # ===========================================
    # P/E RATIO TESTING
    # ===========================================

    @pytest.mark.asyncio
    async def test_pe_ratio_ranges(self):
        """Test P/E ratio ranges for value vs growth stock identification."""
        pe_filters = [
            "fa_pe_low",
            "fa_pe_u15",
            "fa_pe_u10",
            "fa_pe_o25",
            "fa_pe_o30",
            "fa_pe_o40",
            "fa_pe_10to20",
            "fa_pe_15to25",
            "fa_pe_8to20",
            "fa_pe_20to50",
        ]

        await self.assert_custom_filters(pe_filters)

    # ===========================================
    # PEG RATIO TESTING
    # ===========================================

    @pytest.mark.asyncio
    async def test_peg_ratio_analysis(self):
        """Test PEG ratio for growth vs value analysis."""
        peg_filters = [
            "fa_peg_low",
            "fa_peg_u1",
            "fa_peg_u0.5",
            "fa_peg_0.8to1.2",
            "fa_peg_o1.5",
            "fa_peg_o2",
            "fa_peg_0.5to1.5",
        ]

        await self.assert_custom_filters(peg_filters)

    # ===========================================
    # PRICE-TO-BOOK RATIO TESTING
    # ===========================================

    @pytest.mark.asyncio
    async def test_price_book_ratios(self):
        """Test Price-to-Book ratios for asset-based valuation."""
        price_book_filters = [
            "fa_pb_low",
            "fa_pb_u1",
            "fa_pb_u0.5",
            "fa_pb_o3",
            "fa_pb_o5",
            "fa_pb_o10",
            "fa_pb_1to3",
            "fa_pb_1.5to4",
        ]

        await self.assert_custom_filters(price_book_filters)

    # ===========================================
    # DEBT-TO-EQUITY RATIO TESTING
    # ===========================================

    @pytest.mark.asyncio
    async def test_debt_equity_ratios(self):
        """Test Debt-to-Equity ratios for financial health assessment."""
        debt_equity_filters = [
            "fa_debteq_low",
            "fa_debteq_u0.3",
            "fa_debteq_u0.5",
            "fa_debteq_u1",
            "fa_debteq_o1",
            "fa_debteq_o2",
            "fa_debteq_o3",
            "fa_debteq_0.2to1.5",
        ]

        await self.assert_custom_filters(debt_equity_filters)

    # ===========================================
    # PROFITABILITY METRICS TESTING
    # ===========================================

    @pytest.mark.asyncio
    async def test_roe_analysis(self):
        """Test Return on Equity (ROE) for profitability assessment."""
        roe_filters = [
            "fa_roe_o20",
            "fa_roe_o15",
            "fa_roe_o10",
            "fa_roe_8to15",
            "fa_roe_5to12",
            "fa_roe_u5",
            "fa_roe_u0",
            "fa_roe_10to25",
        ]

        await self.assert_custom_filters(roe_filters)

    @pytest.mark.asyncio
    async def test_roa_analysis(self):
        """Test Return on Assets (ROA) for efficiency assessment."""
        roa_filters = [
            "fa_roa_o10",
            "fa_roa_o7",
            "fa_roa_o5",
            "fa_roa_2to7",
            "fa_roa_1to5",
            "fa_roa_u2",
            "fa_roa_u0",
        ]

        await self.assert_custom_filters(roa_filters)

    # ===========================================
    # MARGIN ANALYSIS TESTING
    # ===========================================

    @pytest.mark.asyncio
    async def test_profit_margins(self):
        """Test various profit margin metrics."""
        margin_filters = [
            "fa_grossmargin_o40",
            "fa_grossmargin_o50",
            "fa_grossmargin_20to40",
            "fa_grossmargin_u20",
            "fa_opermargin_o20",
            "fa_opermargin_o30",
            "fa_opermargin_10to20",
            "fa_opermargin_u10",
            "fa_netmargin_o15",
            "fa_netmargin_o20",
            "fa_netmargin_5to15",
            "fa_netmargin_u5",
        ]

        await self.assert_custom_filters(margin_filters)


class TestOwnershipParameters(CustomFilterAssertions):
    """Test ownership structure parameters from Finviz documentation."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup for ownership tests."""
        self.mock_results = _make_stock_results()

    @pytest.mark.asyncio
    async def test_insider_ownership_ranges(self):
        """Test insider ownership percentage ranges."""
        insider_ownership_filters = [
            "sh_insiderown_o20",
            "sh_insiderown_o30",
            "sh_insiderown_o50",
            "sh_insiderown_u5",
            "sh_insiderown_u2",
            "sh_insiderown_5to20",
            "sh_insiderown_10to25",
            "sh_insiderown_15to40",
        ]

        await self.assert_custom_filters(insider_ownership_filters)

    @pytest.mark.asyncio
    async def test_institutional_ownership_ranges(self):
        """Test institutional ownership percentage ranges."""
        institutional_filters = [
            "sh_instown_o70",
            "sh_instown_o80",
            "sh_instown_o90",
            "sh_instown_u30",
            "sh_instown_u20",
            "sh_instown_u40",
            "sh_instown_40to70",
            "sh_instown_50to80",
        ]

        await self.assert_custom_filters(institutional_filters)

    @pytest.mark.asyncio
    async def test_float_size_categories(self):
        """Test float size categories from documentation."""
        float_filters = [
            "sh_float_u50",
            "sh_float_u20",
            "sh_float_u10",
            "sh_float_o500",
            "sh_float_o1000",
            "sh_float_o5000",
            "sh_float_50to500",
            "sh_float_u50p",
            "sh_float_o90p",
            "sh_float_70p95p",
        ]

        await self.assert_custom_filters(float_filters)

    @pytest.mark.asyncio
    async def test_shares_outstanding_ranges(self):
        """Test shares outstanding ranges from documentation."""
        shares_outstanding_filters = [
            "sh_outstanding_u1",
            "sh_outstanding_u5",
            "sh_outstanding_u10",
            "sh_outstanding_u50",
            "sh_outstanding_u100",
            "sh_outstanding_o100",
            "sh_outstanding_o500",
            "sh_outstanding_o1000",
            "sh_outstanding_o5000",
            "sh_outstanding_100to1000",
        ]

        await self.assert_custom_filters(shares_outstanding_filters)


class TestShortInterestParameters(CustomFilterAssertions):
    """Test short interest and option parameters from documentation."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup for short interest tests."""
        self.mock_results = _make_stock_results()

    @pytest.mark.asyncio
    async def test_short_interest_ranges(self):
        """Test short interest percentage ranges from documentation."""
        short_interest_filters = [
            "sh_short_low",
            "sh_short_u2",
            "sh_short_high",
            "sh_short_o20",
            "sh_short_o30",
            "sh_short_o40",
            "sh_short_5to20",
            "sh_short_u5",
            "sh_short_u10",
            "sh_short_u15",
            "sh_short_o10",
            "sh_short_8to25",
        ]

        await self.assert_custom_filters(short_interest_filters)

    @pytest.mark.asyncio
    async def test_option_short_availability(self):
        """Test option and short availability parameters."""
        option_short_filters = [
            "sh_opt_option",
            "sh_opt_notoption",
            "sh_opt_short",
            "sh_opt_notshort",
            "sh_opt_optionshort",
            "sh_opt_optionnotshort",
            "sh_opt_notoptionshort",
            "sh_opt_notoptionnotshort",
            "sh_opt_shortsalerestricted",
            "sh_opt_notshortsalerestricted",
            "sh_opt_halted",
            "sh_opt_nothalted",
        ]

        await self.assert_custom_filters(option_short_filters)

    @pytest.mark.asyncio
    async def test_short_availability_thresholds(self):
        """Test short availability thresholds by share count and dollar value."""
        short_availability_filters = [
            "sh_opt_so10k",
            "sh_opt_so100k",
            "sh_opt_so1m",
            "sh_opt_so10m",
            "sh_opt_uo1m",
            "sh_opt_uo10m",
            "sh_opt_uo100m",
            "sh_opt_uo1b",
        ]

        await self.assert_custom_filters(short_availability_filters)


class TestTargetPriceParameters(CustomFilterAssertions):
    """Test target price parameters from documentation."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup for target price tests."""
        self.mock_results = _make_stock_results()

    @pytest.mark.asyncio
    async def test_target_price_ranges(self):
        """Test target price percentage ranges from documentation."""
        target_price_filters = [
            "targetprice_a50",
            "targetprice_a40",
            "targetprice_a30",
            "targetprice_a20",
            "targetprice_a10",
            "targetprice_a5",
            "targetprice_above",
            "targetprice_below",
            "targetprice_b5",
            "targetprice_b10",
            "targetprice_b20",
            "targetprice_b30",
            "targetprice_b40",
            "targetprice_b50",
            "targetprice_modal",
        ]

        await self.assert_custom_filters(target_price_filters)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
