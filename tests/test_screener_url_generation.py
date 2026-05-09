"""
Regression tests for issue #5: malformed Finviz URLs from special-path screeners.

Verifies that _convert_filters_to_finviz produces well-formed `f=` parameters
for screeners that use the special-path branches in base.py:
- volume_surge_screener
- earnings_premarket_screener
- earnings_afterhours_screener
- earnings_trading_screener
"""

import pytest

from src.finviz_client.screener import FinvizScreener

VALID_PREFIXES = (
    "cap_",
    "sh_",
    "ta_",
    "fa_",
    "ind_",
    "earningsdate_",
    "sec_",
    "geo_",
    "ah_",
)


@pytest.fixture
def screener():
    return FinvizScreener(api_key="dummy-key-for-url-generation-test")


def _filter_tokens(f_param: str) -> list:
    return [p for p in f_param.split(",") if p]


def _has_no_comma_concat(tokens: list) -> bool:
    """Detect tokens that don't start with a known Finviz prefix — sign of comma-less concat."""
    return any(not tok.startswith(VALID_PREFIXES) for tok in tokens)


def _has_duplicates(tokens: list) -> list:
    seen = set()
    dups = []
    for t in tokens:
        if t in seen:
            dups.append(t)
        seen.add(t)
    return dups


class TestVolumeSurgeURL:
    def test_no_comma_concat(self, screener):
        filters = screener._build_volume_surge_filters()
        params = screener._convert_filters_to_finviz(filters)
        tokens = _filter_tokens(params["f"])
        assert not _has_no_comma_concat(
            tokens
        ), f"Found token without valid prefix in {tokens}"

    def test_no_duplicates(self, screener):
        filters = screener._build_volume_surge_filters()
        params = screener._convert_filters_to_finviz(filters)
        tokens = _filter_tokens(params["f"])
        assert not _has_duplicates(
            tokens
        ), f"Duplicate filter tokens: {_has_duplicates(tokens)}"

    def test_required_filters_present(self, screener):
        filters = screener._build_volume_surge_filters()
        params = screener._convert_filters_to_finviz(filters)
        f = params["f"]
        for required in (
            "cap_smallover",
            "sh_price_o10",
            "ta_change_u2",
            "sh_relvol_o1.5",
        ):
            assert required in f, f"Missing required filter: {required}"


class TestEarningsAfterhoursURL:
    def test_no_comma_concat(self, screener):
        filters = screener._build_earnings_afterhours_filters()
        params = screener._convert_filters_to_finviz(filters)
        tokens = _filter_tokens(params["f"])
        assert not _has_no_comma_concat(
            tokens
        ), f"Found token without valid prefix in {tokens}"

    def test_no_duplicates(self, screener):
        filters = screener._build_earnings_afterhours_filters()
        params = screener._convert_filters_to_finviz(filters)
        tokens = _filter_tokens(params["f"])
        assert not _has_duplicates(
            tokens
        ), f"Duplicate filter tokens: {_has_duplicates(tokens)}"

    def test_required_filters_present(self, screener):
        filters = screener._build_earnings_afterhours_filters()
        params = screener._convert_filters_to_finviz(filters)
        f = params["f"]
        for required in (
            "cap_largeover",
            "sh_price_o30",
            "ah_change_u2",
            "earningsdate_todayafter",
        ):
            assert required in f, f"Missing required filter: {required}"

    def test_runtime_params_set(self, screener):
        filters = screener._build_earnings_afterhours_filters()
        params = screener._convert_filters_to_finviz(filters)
        assert params.get("ft") == "4"
        assert params.get("o") == "-afterchange"
        assert params.get("ar") == "60"


class TestEarningsTradingURL:
    def test_no_comma_concat(self, screener):
        filters = screener._build_earnings_trading_filters()
        params = screener._convert_filters_to_finviz(filters)
        tokens = _filter_tokens(params["f"])
        assert not _has_no_comma_concat(
            tokens
        ), f"Found token without valid prefix in {tokens}"

    def test_no_duplicates(self, screener):
        filters = screener._build_earnings_trading_filters()
        params = screener._convert_filters_to_finviz(filters)
        tokens = _filter_tokens(params["f"])
        assert not _has_duplicates(
            tokens
        ), f"Duplicate filter tokens: {_has_duplicates(tokens)}"

    def test_required_filters_present(self, screener):
        filters = screener._build_earnings_trading_filters()
        params = screener._convert_filters_to_finviz(filters)
        f = params["f"]
        for required in (
            "cap_largeover",
            "sh_price_o30",
            "fa_netmargin_3to",
            "fa_epsrev_ep",
            "sh_avgvol_o200",
            "ta_change_u",
            "ta_perf_0to-4w",
            "earningsdate_yesterdayafter|todaybefore",
        ):
            assert required in f, f"Missing required filter: {required}"

    def test_runtime_params_set(self, screener):
        filters = screener._build_earnings_trading_filters()
        params = screener._convert_filters_to_finviz(filters)
        assert params.get("ft") == "4"
        assert params.get("o") == "-epssurprise"
        assert params.get("ar") == "60"

    def test_no_invalid_concat_token(self, screener):
        """Regression for the specific bug: ta_perf_0to-4wearningsdate_..."""
        filters = screener._build_earnings_trading_filters()
        params = screener._convert_filters_to_finviz(filters)
        f = params["f"]
        assert "ta_perf_0to-4wearningsdate" not in f
        assert "sh_price_o30earningsdate" not in f
        assert "ta_sma200_pata_change" not in f


class TestEarningsPremarketURL:
    def test_required_filters_present(self, screener):
        filters = screener._build_earnings_premarket_filters()
        params = screener._convert_filters_to_finviz(filters)
        f = params["f"]
        for required in (
            "cap_largeover",
            "sh_price_o30",
            "sh_avgvol_o100",
            "earningsdate_todaybefore",
        ):
            assert required in f, f"Missing required filter: {required}"

    def test_no_invalid_concat_token(self, screener):
        filters = screener._build_earnings_premarket_filters()
        params = screener._convert_filters_to_finviz(filters)
        f = params["f"]
        # The specific malformed tokens from the bug
        assert "sh_price_o30earningsdate" not in f
        assert "ta_perf" not in f or "ta_perf_0to-4wearningsdate" not in f

    def test_no_duplicate_change_filter(self, screener):
        """
        Regression: premarket previously generated both ta_change_2to and
        ta_change_u2 because two separate handlers processed price_change_min.
        After unifying to one handler, only ta_change_u2 should appear.
        """
        filters = screener._build_earnings_premarket_filters()
        params = screener._convert_filters_to_finviz(filters)
        tokens = _filter_tokens(params["f"])
        change_tokens = [t for t in tokens if t.startswith("ta_change_")]
        assert change_tokens == [
            "ta_change_u2"
        ], f"Expected single canonical change filter ta_change_u2, got {change_tokens}"


class TestPriceChangeMinPresetGuard:
    """
    Regression for review feedback: _safe_numeric_conversion strips o/u prefixes,
    so the preset guard must inspect the RAW input, not the converted value.
    """

    def test_preset_o5_input(self, screener):
        filters = {"price_change_min": "o5"}
        params = screener._convert_filters_to_finviz(filters)
        tokens = _filter_tokens(params.get("f", ""))
        change_tokens = [t for t in tokens if t.startswith("ta_change_")]
        # Preset must be passed through unchanged, with no duplicate
        assert change_tokens == ["ta_change_o5"], change_tokens

    def test_preset_u2_input(self, screener):
        filters = {"price_change_min": "u2"}
        params = screener._convert_filters_to_finviz(filters)
        tokens = _filter_tokens(params.get("f", ""))
        change_tokens = [t for t in tokens if t.startswith("ta_change_")]
        assert change_tokens == ["ta_change_u2"], change_tokens

    def test_numeric_input(self, screener):
        filters = {"price_change_min": 2.0}
        params = screener._convert_filters_to_finviz(filters)
        tokens = _filter_tokens(params.get("f", ""))
        change_tokens = [t for t in tokens if t.startswith("ta_change_")]
        assert change_tokens == ["ta_change_u2"], change_tokens

    def test_range_min_max(self, screener):
        filters = {"price_change_min": 2, "price_change_max": 10}
        params = screener._convert_filters_to_finviz(filters)
        tokens = _filter_tokens(params.get("f", ""))
        change_tokens = [t for t in tokens if t.startswith("ta_change_")]
        assert change_tokens == ["ta_change_2to10"], change_tokens
