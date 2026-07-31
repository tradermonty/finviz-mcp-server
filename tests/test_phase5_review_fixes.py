"""Phase 5 review follow-ups: one pinning test per numbered fix.

Each test names the failure mode it prevents, because every one of these was
a case of the server describing a filter/order it did not actually run.
"""

from datetime import date
from unittest.mock import patch

import pandas as pd
import pytest

from src.finviz_client.base import (
    EARNINGS_DATE_TOKENS,
    EASTERN,
    FinvizClient,
    eastern_today,
    finviz_date_range,
)
from src.finviz_client.screener import FinvizScreener
from src.models import StockData


def tokens_for(**filters):
    client = FinvizClient(api_key="test-key")
    return client._convert_filters_to_finviz(filters).get("f", "").split(",")


def stock(ticker, **kwargs):
    base = dict(
        company_name=f"{ticker} Inc",
        sector="Technology",
        industry="Software",
    )
    base.update(kwargs)
    return StockData(ticker=ticker, **base)


# ---------------------------------------------------------------------------
# 1. One Finviz key -> one token
# ---------------------------------------------------------------------------
def test_both_payout_bounds_collapse_into_one_range_token():
    """Two tokens for one key => Finviz keeps one and drops the other."""
    tokens = tokens_for(payout_ratio_min=10, payout_ratio_max=80.5)
    assert "fa_payoutratio_10to80.5" in tokens
    assert len([t for t in tokens if t.startswith("fa_payoutratio")]) == 1


@pytest.mark.parametrize(
    "min_key,max_key,expected",
    [
        ("pe_min", "pe_max", "fa_pe_5to30"),
        ("pb_ratio_min", "pb_ratio_max", "fa_pb_5to30"),
        ("roe_min", "roe_max", "fa_roe_5to30"),
        ("debt_equity_min", "debt_equity_max", "fa_debteq_5to30"),
        ("payout_ratio_min", "payout_ratio_max", "fa_payoutratio_5to30"),
        ("dividend_yield_min", "dividend_yield_max", "fa_div_5to30"),
        ("rsi_min", "rsi_max", "ta_rsi_5to30"),
        ("price_min", "price_max", "sh_price_5to30"),
        ("relative_volume_min", "relative_volume_max", "sh_relvol_5to30"),
        ("price_change_min", "price_change_max", "ta_change_5to30"),
    ],
)
def test_every_min_max_pair_produces_a_single_range_token(min_key, max_key, expected):
    tokens = tokens_for(**{min_key: 5, max_key: 30})
    key = expected.rsplit("_", 1)[0]
    assert expected in tokens
    assert len([t for t in tokens if t.rsplit("_", 1)[0] == key]) == 1


def test_volume_min_max_pairs_produce_a_single_token_each():
    tokens = tokens_for(
        volume_min=100_000,
        volume_max=500_000,
        avg_volume_min=1_000,
        avg_volume_max=2_000,
    )
    assert "sh_curvol_100to500" in tokens
    assert "sh_avgvol_1to2" in tokens
    assert len([t for t in tokens if t.startswith("sh_curvol")]) == 1
    assert len([t for t in tokens if t.startswith("sh_avgvol")]) == 1


def test_alias_keys_do_not_produce_a_second_token_for_the_same_key():
    """``pe_ratio_max`` is an alias of ``pe_max`` - one fa_pe token, not two."""
    tokens = tokens_for(pe_max=20, pe_ratio_max=30)
    assert len([t for t in tokens if t.startswith("fa_pe")]) == 1


def test_positive_flag_yields_to_a_numeric_minimum_on_the_same_key():
    tokens = tokens_for(sales_growth_qoq_positive=True, revenue_growth_qoq_min=5)
    assert "fa_salesqoq_o5" in tokens
    assert "fa_salesqoq_pos" not in tokens


def test_a_duplicate_key_is_a_loud_error_not_a_silent_half_filter():
    """market_cap + market_cap_min would send two cap_ tokens."""
    with pytest.raises(ValueError, match="same Finviz key"):
        tokens_for(market_cap="mid", market_cap_min=10)


# ---------------------------------------------------------------------------
# 2. price prefix matching
# ---------------------------------------------------------------------------
def test_price_change_is_not_rendered_as_a_dollar_amount():
    from src.server import _format_filter_value

    assert _format_filter_value("price_min", 30.0) == "$30.0"
    assert _format_filter_value("price_change_min", 2.0) == "2.0"
    assert "$" not in _format_filter_value("price_change_max", 5.0)


# ---------------------------------------------------------------------------
# 3. zero-truthiness in the summary tables
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "tool_name",
    [
        "earnings_premarket_screener",
        "earnings_afterhours_screener",
        "earnings_trading_screener",
    ],
)
def test_summary_tables_render_zero_as_a_value(tool_name):
    from src import server

    rows = [
        stock(
            "FLAT",
            price=10.0,
            price_change=0.0,
            eps_surprise=0.0,
            revenue_surprise=0.0,
            performance_1w=0.0,
            volatility=0.0,
            volume=0,
            premarket_change_percent=0.0,
            afterhours_change_percent=0.0,
        )
    ]
    with patch("src.server.finviz_screener.screen_stocks", return_value=rows):
        text = getattr(server, tool_name)()[0].text

    flat_row = [line for line in text.splitlines() if line.startswith("| FLAT")]
    assert flat_row, text
    assert "N/A" not in flat_row[0], flat_row[0]
    assert "+0.00%" in flat_row[0]


# ---------------------------------------------------------------------------
# 4. within_2_weeks really means two weeks
# ---------------------------------------------------------------------------
def test_within_2_weeks_runs_as_a_fourteen_day_window_not_nextdays5():
    screener = FinvizScreener(api_key="k")
    filters = screener._build_earnings_filters(earnings_date="within_2_weeks")

    resolved = filters["earnings_date"]
    assert "x" in resolved, resolved
    start, end = resolved.split("x")
    span = (
        date(int(end[6:]), int(end[:2]), int(end[3:5]))
        - date(int(start[6:]), int(start[:2]), int(start[3:5]))
    ).days
    assert span == 13  # tomorrow .. +14 days inclusive

    tokens = screener._convert_filters_to_finviz(filters)["f"].split(",")
    assert f"earningsdate_{resolved}" in tokens
    assert "earningsdate_nextdays5" not in tokens


def test_validator_accepts_exactly_the_values_the_converter_understands():
    from src.utils.validators import validate_earnings_date

    for value in EARNINGS_DATE_TOKENS:
        assert validate_earnings_date(value), value
    assert validate_earnings_date("08-03-2026x08-14-2026")
    assert not validate_earnings_date("next_year")
    assert not validate_earnings_date("2024-01-01")
    assert not validate_earnings_date(None)


# ---------------------------------------------------------------------------
# 5. Finviz calendars are US/Eastern
# ---------------------------------------------------------------------------
def test_date_windows_are_built_from_the_eastern_date():
    from datetime import datetime

    assert str(EASTERN) == "America/New_York"
    assert eastern_today() == datetime.now(EASTERN).date()

    # Year boundary: the window must roll over, not clamp.
    fixed = date(2026, 12, 31)
    assert finviz_date_range(14, today=fixed) == "01-01-2027x01-14-2027"


def test_earnings_period_windows_use_the_shared_eastern_helper():
    screener_value = FinvizScreener.earnings_period_to_finviz("next_2_weeks")
    assert screener_value == finviz_date_range(14)


# ---------------------------------------------------------------------------
# 6. the criteria block is printed once
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "tool_name,marker",
    [
        ("earnings_premarket_screener", "Applied Screening Criteria"),
        ("earnings_afterhours_screener", "Applied Screening Criteria"),
        ("earnings_trading_screener", "適用されたスクリーニング条件"),
    ],
)
def test_criteria_block_appears_exactly_once(tool_name, marker):
    from src import server

    rows = [stock("AAA", price=50.0, price_change=1.0)]
    with patch("src.server.finviz_screener.screen_stocks", return_value=rows):
        text = getattr(server, tool_name)()[0].text

    assert text.count(marker) == 1
    assert text.count("Fixed Filter Criteria:") == 0
    # the real query is still shown, once
    assert text.count("Finviz query: f=") == 1


# ---------------------------------------------------------------------------
# 7. market-cap validation == market-cap resolution
# ---------------------------------------------------------------------------
def test_market_cap_validator_matches_the_converter():
    from src.models import MARKET_CAP_ALIASES, MARKET_CAP_FILTERS
    from src.utils.validators import validate_market_cap

    for code in MARKET_CAP_FILTERS:
        assert validate_market_cap(code)
        assert f"cap_{code}" in tokens_for(market_cap=code)

    for alias, code in MARKET_CAP_ALIASES.items():
        assert validate_market_cap(alias)
        assert f"cap_{code}" in tokens_for(market_cap=alias)

    assert validate_market_cap("")  # "no filter"
    assert validate_market_cap("10to20")
    assert validate_market_cap("LARGE")  # case-insensitive, resolves to cap_large
    # "frange" is the UI's custom-range placeholder: the converter cannot turn
    # it into a token, so the validator must not accept it either.
    assert not validate_market_cap("frange")
    assert not validate_market_cap("huge")


# ---------------------------------------------------------------------------
# 8. custom_screener: no ar=, honest ordering
# ---------------------------------------------------------------------------
def _raw_frame(n=5):
    return pd.DataFrame(
        {
            "Ticker": [f"T{i}" for i in range(n)],
            "Company": [f"Co {i}" for i in range(n)],
            "Sector": ["Technology"] * n,
            "Industry": ["Software"] * n,
            "Price": [10.0 + i for i in range(n)],
            "Market Cap": [100.0 * (n - i) for i in range(n)],
        }
    )


def test_raw_screen_does_not_send_the_ignored_ar_param():
    client = FinvizClient(api_key="k")
    with patch.object(
        client, "_fetch_csv_from_url", return_value=_raw_frame()
    ) as fetch:
        client.screen_stocks_raw(filters="cap_large", max_results=2)
    assert "ar" not in fetch.call_args[0][1]


def test_raw_screen_resorts_a_known_order_before_slicing():
    client = FinvizClient(api_key="k")
    with patch.object(client, "_fetch_csv_from_url", return_value=_raw_frame()):
        rows, total, verified = client.screen_stocks_raw(
            filters="cap_large", order="-marketcap", max_results=2
        )
    assert verified is True
    assert total == 5
    # largest market cap first, and the cut keeps the real top 2
    assert [s.ticker for s in rows] == ["T0", "T1"]


def test_raw_screen_reports_an_unverifiable_order_instead_of_implying_a_ranking():
    client = FinvizClient(api_key="k")
    with patch.object(client, "_fetch_csv_from_url", return_value=_raw_frame()):
        rows, total, verified = client.screen_stocks_raw(
            filters="cap_large", order="-someunknowncolumn", max_results=2
        )
    assert verified is False
    assert total == 5
    assert len(rows) == 2


def test_custom_screener_output_states_how_the_rows_were_chosen():
    from src import server

    rows = [stock(f"T{i}", price=10.0, market_cap=100.0) for i in range(3)]

    with patch(
        "src.server.finviz_client.screen_stocks_raw", return_value=(rows, 42, False)
    ):
        text = server.custom_screener(filters="cap_large", max_results=3)[0].text
    assert "3 of 42 rows" in text
    assert "not a ranking" in text

    with patch(
        "src.server.finviz_client.screen_stocks_raw", return_value=(rows, 42, True)
    ):
        text = server.custom_screener(
            filters="cap_large", order="-marketcap", max_results=3
        )[0].text
    assert "re-sorted client-side" in text
