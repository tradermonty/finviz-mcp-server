"""Phase 5: every advertised screener filter must actually reach Finviz.

Two invariants are pinned here, both learned the hard way:

1. **Token-level wiring.** Finviz silently ignores unknown ``f=`` tokens, so a
   filter is only real if the exact token string lands in the request params.
   Every token asserted below was verified against the live Elite API and is
   recorded in ``tests/fixtures/GROUND_TRUTH.md``.
2. **Sort before truncate.** ``ar`` is ignored by the export endpoint, so the
   client receives every matching row; slicing before sorting turns "top N by
   X" into "N arbitrary rows re-sorted".
"""

from unittest.mock import patch

import pandas as pd
import pytest

from src.finviz_client.base import FinvizClient
from src.finviz_client.screener import FinvizScreener, parse_earnings_datetime
from src.models import MARKET_CAP_FILTERS, StockData


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def captured_params(call_fn):
    """Run ``call_fn`` with the HTTP layer patched; return the request params."""
    seen = {}

    def fake_fetch(self, url, params):
        seen.update(params)
        seen["__url__"] = url
        return pd.DataFrame()

    with patch.object(FinvizClient, "_fetch_csv_from_url", fake_fetch):
        call_fn()
    return seen


def tokens_for(**filters):
    """Return the ``f=`` tokens a filter dict produces."""
    client = FinvizClient(api_key="test-key")
    return client._convert_filters_to_finviz(filters).get("f", "").split(",")


def stock(ticker, **kwargs):
    return StockData(
        ticker=ticker,
        company_name=f"{ticker} Inc",
        sector="Technology",
        industry="Software",
        **kwargs,
    )


# ---------------------------------------------------------------------------
# B1 - current volume: sh_curvol_*, thousands units
# ---------------------------------------------------------------------------
def test_volume_min_emits_sh_curvol_in_thousands():
    """``sh_volume_*`` does not exist; ``sh_curvol_*`` counts thousands.

    Probe: ``cap_mega,sh_curvol_o20000`` returned 0 rows while the mega
    universe (73 rows) had a max raw Volume of 4,022,258 - i.e. the token is
    honored and 20000 means 20M shares, not 20K.
    """
    tokens = tokens_for(volume_min=650_000)
    assert "sh_curvol_o650" in tokens
    assert not any(t.startswith("sh_volume") for t in tokens)


def test_volume_range_and_max_use_verified_range_grammar():
    assert "sh_curvol_100to500" in tokens_for(volume_min=100_000, volume_max=500_000)
    # A bare maximum is expressed with the same verified range grammar,
    # anchored at zero, rather than an unverified "u" spelling.
    assert "sh_curvol_0to500" in tokens_for(volume_max=500_000)


def test_avg_volume_keeps_the_exact_threshold_not_a_preset_bucket():
    """B20: 650,000 used to be floored to ``o500`` (= a looser filter)."""
    assert "sh_avgvol_o650" in tokens_for(avg_volume_min=650_000)
    assert "sh_avgvol_o500" not in tokens_for(avg_volume_min=650_000)


def test_sub_thousand_precision_rounds_so_the_filter_never_loosens():
    client = FinvizClient(api_key="k")
    assert client._shares_to_finviz_thousands(120_500, "min") == 121  # up
    assert client._shares_to_finviz_thousands(120_500, "max") == 120  # down


# ---------------------------------------------------------------------------
# B2 - dividend growth: every advertised criterion becomes a token
# ---------------------------------------------------------------------------
def test_dividend_growth_defaults_reach_finviz():
    screener = FinvizScreener(api_key="k")
    filters = screener._build_dividend_growth_filters()
    tokens = screener._convert_filters_to_finviz(filters)["f"].split(",")

    for expected in (
        "cap_midover",
        "fa_div_2to",
        "fa_pe_u30",
        "fa_pb_u5",
        "fa_eps5years_pos",
        "fa_epsqoq_pos",
        "fa_epsyoy_pos",
        "fa_sales5years_pos",
        "fa_salesqoq_pos",
        "geo_usa",
        "ind_stocksonly",
    ):
        assert expected in tokens, f"{expected} missing from {tokens}"


def test_dividend_growth_optional_criteria_reach_finviz():
    screener = FinvizScreener(api_key="k")
    filters = screener._build_dividend_growth_filters(
        min_roe=15, max_debt_equity=0.5, min_payout_ratio=30, max_payout_ratio=80
    )
    tokens = screener._convert_filters_to_finviz(filters)["f"].split(",")
    assert "fa_roe_o15" in tokens
    assert "fa_debteq_u0.5" in tokens
    # Both payout bounds collapse into ONE token: two tokens for the same
    # Finviz key make Finviz drop one of them silently (review item 1).
    assert "fa_payoutratio_30to80" in tokens
    assert "fa_payoutratio_o30" not in tokens
    assert "fa_payoutratio_u80" not in tokens


def test_unverified_country_is_rejected_rather_than_silently_dropped():
    with pytest.raises(ValueError, match="country"):
        tokens_for(country="Japan")


# ---------------------------------------------------------------------------
# B3 - ETF universe server-side, the rest client-side
# ---------------------------------------------------------------------------
def test_etf_screener_restricts_the_universe_server_side():
    screener = FinvizScreener(api_key="k")
    filters = screener._build_etf_filters()
    assert "ind_exchangetradedfund" in screener._convert_filters_to_finviz(filters)["f"]


def test_etf_aum_and_expense_filters_are_applied_client_side():
    """``etf_netexpense_*``/``etf_aum_*`` were probe-confirmed no-ops."""
    rows = [
        stock("CHEAP", aum=5_000_000_000.0, net_expense_ratio=0.05),
        stock("PRICEY", aum=5_000_000_000.0, net_expense_ratio=0.95),
        stock("TINY", aum=1_000_000.0, net_expense_ratio=0.03),
        stock("UNKNOWN"),
    ]
    kept = FinvizScreener._apply_etf_client_filters(
        rows, min_aum=1_000_000_000, max_expense_ratio=0.2
    )
    assert [s.ticker for s in kept] == ["CHEAP"]


def test_etf_asset_class_matches_the_real_asset_type_vocabulary():
    """The column says "Equities (Stocks)"/"Bonds", not "equity"/"bond"."""
    rows = [
        stock("EQ", asset_type="Equities (Stocks)"),
        stock("BOND", asset_type="Bonds"),
        stock("GOLD", asset_type="Commodities & Metals"),
    ]
    for requested, expected in (
        ("equity", "EQ"),
        ("stocks", "EQ"),
        ("bond", "BOND"),
        ("commodity", "GOLD"),
    ):
        kept = FinvizScreener._apply_etf_client_filters(rows, asset_class=requested)
        assert [s.ticker for s in kept] == [expected], requested


# ---------------------------------------------------------------------------
# B4 - upcoming earnings volume key unification
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("key", ["min_avg_volume", "avg_volume_min", "average_volume"])
def test_upcoming_earnings_reads_the_volume_threshold_under_any_spelling(key):
    screener = FinvizScreener(api_key="k")
    filters = screener._build_upcoming_earnings_filters(**{key: 650_000})
    tokens = screener._convert_filters_to_finviz(filters)["f"].split(",")
    assert "sh_avgvol_o650" in tokens, f"{key} was dropped; default 500K applied"


# ---------------------------------------------------------------------------
# B5 - trend reversion
# ---------------------------------------------------------------------------
def test_mid_large_resolves_to_a_real_cap_token():
    screener = FinvizScreener(api_key="k")
    filters = screener._build_trend_reversion_filters(market_cap="mid_large")
    tokens = screener._convert_filters_to_finviz(filters)["f"].split(",")
    assert "cap_midover" in tokens
    assert "cap_mid_large" not in tokens


def test_revenue_growth_qoq_reaches_finviz():
    screener = FinvizScreener(api_key="k")
    filters = screener._build_trend_reversion_filters(revenue_growth_qoq=5)
    assert "fa_salesqoq_o5" in screener._convert_filters_to_finviz(filters)["f"]


def test_exclude_sectors_is_applied_client_side():
    """Finviz has no negation syntax, so the rows are filtered here."""
    rows = [stock("KEEP"), stock("DROP")]
    rows[1].sector = "Energy"
    screener = FinvizScreener(api_key="k")
    with patch.object(FinvizScreener, "screen_stocks", return_value=rows):
        kept = screener.trend_reversion_screener(exclude_sectors=["Energy"])
    assert [s.ticker for s in kept] == ["KEEP"]


def test_unknown_market_cap_raises_instead_of_emitting_a_dead_token():
    with pytest.raises(ValueError, match="market_cap"):
        tokens_for(market_cap="mega_huge")


# ---------------------------------------------------------------------------
# B6 - price below SMA
# ---------------------------------------------------------------------------
def test_sma_below_emits_pb_tokens():
    tokens = tokens_for(sma20_below=True, sma50_below=True, sma200_below=True)
    assert "ta_sma20_pb" in tokens
    assert "ta_sma50_pb" in tokens
    assert "ta_sma200_pb" in tokens


# ---------------------------------------------------------------------------
# B22 - market cap table is the converter's table
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("code", ["largeover", "microover", "midover", "smallover"])
def test_market_cap_table_covers_every_code_the_converter_accepts(code):
    assert code in MARKET_CAP_FILTERS
    assert f"cap_{code}" in tokens_for(market_cap=code)


# ---------------------------------------------------------------------------
# Column list + sort tokens
# ---------------------------------------------------------------------------
def test_screener_requests_every_verified_column():
    params = FinvizClient(api_key="k")._convert_filters_to_finviz({})
    assert params["c"] == ",".join(str(i) for i in range(150))


def test_multi_year_performance_columns_are_parsed_for_both_instrument_types():
    """Columns 138-140 (stocks) only arrive now that ``c=`` runs to 149."""
    client = FinvizClient(api_key="k")

    equity = client._parse_stock_data_from_csv(
        pd.Series(
            {
                "Ticker": "AAA",
                "Company": "AAA Inc",
                "Performance (3 Years)": "42.50%",
                "Performance (5 Years)": "80.00%",
                "Performance (10 Years)": "150.00%",
            }
        )
    )
    assert equity.performance_3y == 42.5
    assert equity.performance_5y == 80.0
    assert equity.performance_10y == 150.0

    etf = client._parse_stock_data_from_csv(
        pd.Series({"Ticker": "SPY", "Company": "SPDR", "Return 3 Year": "30.00%"})
    )
    assert etf.performance_3y == 30.0


def test_earnings_date_sort_uses_the_verified_server_side_token():
    params = FinvizClient(api_key="k")._convert_filters_to_finviz(
        {"sort_by": "earnings_date", "sort_order": "asc"}
    )
    assert params["o"] == "earningsdate"


# ---------------------------------------------------------------------------
# B7 / B16 / B18 - sort before truncate
# ---------------------------------------------------------------------------
def test_fetch_does_not_truncate_before_the_client_sorts():
    """``max_results`` must not slice the CSV in Finviz's own order."""
    frame = pd.DataFrame({"Ticker": ["AAA", "BBB", "CCC"], "Price": [1.0, 2.0, 3.0]})
    with patch.object(FinvizClient, "_make_request", return_value=object()):
        with patch.object(
            FinvizClient, "_csv_response_to_dataframe", return_value=frame
        ):
            out = FinvizClient(api_key="k")._fetch_csv_data({"max_results": 1})
    assert len(out) == 3


def test_earnings_winners_sorts_then_slices():
    rows = [
        stock("LOW", performance_1w=1.0),
        stock("HIGH", performance_1w=9.0),
        stock("MID", performance_1w=5.0),
    ]
    screener = FinvizScreener(api_key="k")
    with patch.object(FinvizScreener, "screen_stocks", return_value=list(rows)) as sc:
        out = screener.earnings_winners_screener(max_results=2)

    assert [s.ticker for s in out] == ["HIGH", "MID"]
    # ... and the request itself carried no server-side row cap
    assert "max_results" not in sc.call_args[0][0]


def test_earnings_winners_supports_the_advertised_eps_surprise_sort():
    rows = [
        stock("A", eps_surprise=1.0),
        stock("B", eps_surprise=12.0),
        stock("C"),  # missing datum sorts last, never as 0
    ]
    screener = FinvizScreener(api_key="k")
    with patch.object(FinvizScreener, "screen_stocks", return_value=list(rows)):
        out = screener.earnings_winners_screener(sort_by="eps_surprise")
    assert [s.ticker for s in out] == ["B", "A", "C"]


def test_dividend_growth_sorts_then_slices():
    rows = [
        stock("LOW", dividend_yield=1.0),
        stock("HIGH", dividend_yield=8.0),
        stock("MID", dividend_yield=4.0),
    ]
    screener = FinvizScreener(api_key="k")
    with patch.object(FinvizScreener, "screen_stocks", return_value=list(rows)):
        out = screener.dividend_growth_screener(max_results=2)
    assert [s.ticker for s in out] == ["HIGH", "MID"]


def test_technical_analysis_orders_by_ticker_and_reports_the_true_total():
    rows = [stock("ZZZ"), stock("AAA"), stock("MMM")]
    screener = FinvizScreener(api_key="k")
    with patch.object(FinvizScreener, "screen_stocks", return_value=list(rows)):
        out, total = screener.technical_analysis_screener(max_results=2)
    assert [s.ticker for s in out] == ["AAA", "MMM"]
    assert total == 3


def test_earnings_dates_sort_chronologically_not_lexicographically():
    """ "5/13/2026" sorts before "5/2/2026" as a string - not as a date."""
    from src.models import UpcomingEarningsData

    def upcoming(ticker, date):
        return UpcomingEarningsData(
            ticker=ticker,
            company_name=ticker,
            sector="Technology",
            industry="Software",
            earnings_date=date,
            earnings_timing="unknown",
        )

    rows = [
        upcoming("LATE", "5/13/2026 4:30:00 PM"),
        upcoming("EARLY", "5/2/2026 8:30:00 AM"),
        upcoming("PRIOR", "12/1/2025 8:30:00 AM"),
    ]
    out = FinvizScreener(api_key="k")._sort_upcoming_earnings_results(
        rows, "earnings_date", "asc"
    )
    assert [s.ticker for s in out] == ["PRIOR", "EARLY", "LATE"]


def test_unparseable_earnings_date_sorts_last_instead_of_crashing():
    assert parse_earnings_datetime("not a date") is None
    assert parse_earnings_datetime("8/12/2026 8:30:00 AM").month == 8


# ---------------------------------------------------------------------------
# B15 - earnings periods map to something real
# ---------------------------------------------------------------------------
def test_period_tokens_that_do_not_exist_are_never_sent():
    """Probes: earningsdate_nextmonth / _nextdays10 returned the full universe."""
    two_weeks = FinvizScreener.earnings_period_to_finviz("next_2_weeks")
    a_month = FinvizScreener.earnings_period_to_finviz("next_month")
    for value in (two_weeks, a_month):
        assert "x" in value, f"{value} is not a date range"
        assert value not in ("nextdays5", "thismonth", "nextmonth", "nextdays10")

    assert FinvizScreener.earnings_period_to_finviz("next_week") == "nextweek"
    with pytest.raises(ValueError, match="earnings_period"):
        FinvizScreener.earnings_period_to_finviz("next_quarter")


def test_period_label_matches_what_actually_runs():
    assert "14 calendar days" in FinvizScreener.describe_earnings_period("next_2_weeks")
    assert "30 calendar days" in FinvizScreener.describe_earnings_period("next_month")


def test_date_range_period_produces_a_verified_earningsdate_token():
    screener = FinvizScreener(api_key="k")
    filters = screener._build_upcoming_earnings_filters(earnings_period="next_month")
    tokens = screener._convert_filters_to_finviz(filters)["f"].split(",")
    ranges = [t for t in tokens if t.startswith("earningsdate_")]
    assert len(ranges) == 1
    assert "x" in ranges[0]


# ---------------------------------------------------------------------------
# B23 - validator and converter agree
# ---------------------------------------------------------------------------
def test_validator_accepts_exactly_what_the_converter_can_resolve():
    from src.finviz_client.base import SECTOR_CODES, resolve_sector_code
    from src.utils.validators import validate_sector

    for name in list(SECTOR_CODES) + list(SECTOR_CODES.values()):
        assert validate_sector(name)
        assert resolve_sector_code(name)
        assert f"sec_{resolve_sector_code(name)}" in tokens_for(sectors=[name])

    assert validate_sector("Financial Services")  # used to be rejected
    assert not validate_sector("Nonexistent Sector")


def test_unknown_sector_raises_instead_of_widening_the_screen():
    with pytest.raises(ValueError, match="[Ss]ector"):
        tokens_for(sectors=["Nonexistent Sector"])


def test_validate_tickers_accepts_the_list_form_it_advertises():
    from src.utils.validators import parse_tickers, validate_tickers

    assert validate_tickers(["AAPL", "MSFT"])
    assert parse_tickers(["AAPL", "MSFT"]) == ["AAPL", "MSFT"]
    assert validate_tickers("AAPL,MSFT")
    assert not validate_tickers([])
