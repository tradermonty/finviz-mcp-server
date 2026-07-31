"""Phase 5: what a screener prints must be what a screener ran.

Every criteria block is now derived from the filter dict that is actually
sent (plus the literal ``f=`` token string), so these tests assert the real
values show up and the old hand-written text cannot come back.
"""

from unittest.mock import patch

import pytest

from src import server
from src.models import StockData


def stock(ticker="AAA", **kwargs):
    base = dict(
        company_name=f"{ticker} Inc",
        sector="Technology",
        industry="Software",
        price=100.0,
        price_change=1.5,
    )
    base.update(kwargs)
    return StockData(ticker=ticker, **base)


def run(tool, rows, **kwargs):
    with patch("src.server.finviz_screener.screen_stocks", return_value=list(rows)):
        return tool(**kwargs)[0].text


# ---------------------------------------------------------------------------
# B12 - earnings_screener printed another tool's criteria
# ---------------------------------------------------------------------------
def test_earnings_screener_prints_the_criteria_it_actually_applied():
    text = run(
        server.earnings_screener,
        [stock()],
        earnings_date="this_week",
        min_price=25,
        min_volume=650_000,
    )

    assert "Min price: $25" in text
    assert "Min volume (today): 650,000 shares" in text
    assert "sh_curvol_o650" in text  # the literal query, not a description
    # ...and none of earnings_trading's fixed criteria, which used to be
    # printed verbatim by this tool.
    assert "EPS Revision: Positive" not in text
    assert "4-Week Performance: 0% to negative" not in text
    assert "Volatility: 1x and above" not in text


def test_finviz_volume_tokens_are_spelled_out_in_share_counts():
    rows = [stock("AAA", earnings_date="8/12/2026 8:30:00 AM")]
    text = run(server.upcoming_earnings_screener, rows, min_avg_volume="o500")
    assert "at least 500,000 shares (o500)" in text


# ---------------------------------------------------------------------------
# B14 - premarket/afterhours advertised the wrong price/cap
# ---------------------------------------------------------------------------
def test_premarket_criteria_show_the_real_price_and_cap():
    text = run(server.earnings_premarket_screener, [stock()])

    assert "$30" in text
    assert "largeover" in text
    assert "Min Price: $10.00" not in text
    assert "(Small+)" not in text
    assert "sh_price_o30" in text


def test_afterhours_criteria_show_the_real_price_and_cap():
    text = run(
        server.earnings_afterhours_screener, [stock(afterhours_change_percent=3)]
    )

    assert "$30" in text
    assert "largeover" in text
    assert "Min Price: $10.00" not in text
    assert "(Small+)" not in text


# ---------------------------------------------------------------------------
# B2 - dividend growth's "Default Criteria" block was fiction
# ---------------------------------------------------------------------------
def test_dividend_growth_block_tracks_overridden_parameters():
    text = run(
        server.dividend_growth_screener,
        [stock(dividend_yield=3.0)],
        max_pe_ratio=12,
        min_dividend_yield=4.0,
    )

    assert "Max P/E: 12" in text
    assert "Min dividend yield (%): 4.0" in text
    assert "fa_pe_u12" in text
    assert "fa_div_4to" in text
    # The old block hard-coded these regardless of the request.
    assert "P/E Ratio: ≤30" not in text
    assert "Dividend Yield: 2%+" not in text


# ---------------------------------------------------------------------------
# B27 - the rich earnings-trading formatter was dead code
# ---------------------------------------------------------------------------
def test_earnings_trading_uses_the_detailed_formatter():
    rows = [
        stock(
            "AAA",
            eps_surprise=5.0,
            revenue_surprise=2.0,
            performance_1w=3.0,
            volatility=2.5,
            volume=1_000_000,
        ),
    ]
    text = run(server.earnings_trading_screener, rows)

    assert "| Ticker | Company | Sector |" in text  # the detailed table
    assert "EPS Surprise" in text
    assert "AAA" in text


# ---------------------------------------------------------------------------
# B26 - "+" was hardcoded, so negatives rendered as "+-3.2%"
# ---------------------------------------------------------------------------
def test_negative_values_keep_their_own_sign():
    rows = [stock("DOWN", performance_1w=-3.2, eps_surprise=-1.5)]
    text = run(
        server.earnings_winners_screener, rows, min_avg_volume="o500", max_results=5
    )

    assert "+-" not in text
    assert "-3.2%" in text


def test_zero_is_rendered_as_a_value_not_as_missing():
    rows = [stock("FLAT", performance_1w=0.0, eps_surprise=0.0)]
    text = run(server.earnings_winners_screener, rows, max_results=5)
    assert "+0.0%" in text


# ---------------------------------------------------------------------------
# B24 - the false "CSV has no earnings date" note
# ---------------------------------------------------------------------------
def test_upcoming_earnings_does_not_claim_the_csv_lacks_dates():
    rows = [stock("AAA", earnings_date="8/12/2026 8:30:00 AM")]
    text = run(server.upcoming_earnings_screener, rows, max_results=5)

    assert "CSV export does not include earnings date" not in text
    assert "8/12/2026" in text


def test_upcoming_earnings_period_label_matches_the_query():
    rows = [stock("AAA", earnings_date="8/12/2026 8:30:00 AM")]
    text = run(
        server.upcoming_earnings_screener,
        rows,
        earnings_period="next_month",
        max_results=5,
    )
    assert "30 calendar days" in text
    assert "earningsdate_thismonth" not in text


# ---------------------------------------------------------------------------
# B28 - technical analysis sliced the universe silently
# ---------------------------------------------------------------------------
def test_technical_analysis_reports_the_true_match_count():
    rows = [stock("ZZZ"), stock("AAA"), stock("MMM")]
    text = run(server.technical_analysis_screener, rows, max_results=2, rsi_max=30)

    assert "2 of 3 matches shown" in text
    assert "ticker ascending" in text
    assert "ta_rsi_to30" in text


def test_sma_lines_label_dollar_and_percent_units_correctly():
    """StockData.sma_20/50/200 hold *derived dollar SMAs* (see
    _compute_sma_fields); the percent distance is the *_relative twin.
    The Phase 8 live sweep caught this display printing the dollar value
    with a percent sign (SMA 200: +56.09%); each unit must carry its own
    label. Zero readings are values, not N/A."""
    rows = [
        stock(
            "AAA",
            sma_20=97.28,
            sma_20_relative=2.8,
            sma_50=100.0,
            sma_50_relative=0.0,
            sma_200=90.09,
            sma_200_relative=11.0,
            rsi=0.0,
            volume=0,
        )
    ]
    text = run(server.technical_analysis_screener, rows, max_results=5)

    assert "SMA 20: $97.28 (+2.80% vs price)" in text
    assert "SMA 50: $100.00 (+0.00% vs price)" in text  # 0 is a reading
    assert "+97.28%" not in text  # the dollar value never wears a % sign
    assert "RSI: 0.00" in text
    assert "Volume: 0" in text


def test_technical_analysis_below_sma_reaches_finviz():
    seen = {}

    def capture(filters):
        seen.update(filters)
        return [stock("AAA")]

    with patch("src.server.finviz_screener.screen_stocks", side_effect=capture):
        text = server.technical_analysis_screener(price_vs_sma200="below")[0].text

    assert seen.get("sma200_below") is True
    assert "ta_sma200_pb" in text


# ---------------------------------------------------------------------------
# B13 / B17 / B2 / B3 - dead parameters are gone from the tool schemas
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "tool_name,removed",
    [
        ("earnings_screener", ["premarket_price_change", "afterhours_price_change"]),
        (
            "upcoming_earnings_screener",
            ["pre_earnings_analysis", "risk_assessment", "data_fields"],
        ),
        ("dividend_growth_screener", ["min_dividend_growth"]),
        ("etf_screener", ["strategy_type"]),
    ],
)
async def test_unhonorable_parameters_are_no_longer_advertised(tool_name, removed):
    tools = {tool.name: tool for tool in await server.server.list_tools()}
    properties = tools[tool_name].inputSchema.get("properties", {})
    for name in removed:
        assert name not in properties, f"{tool_name} still advertises {name}"


@pytest.mark.asyncio
async def test_etf_tool_still_advertises_what_it_can_honor():
    tools = {tool.name: tool for tool in await server.server.list_tools()}
    properties = tools["etf_screener"].inputSchema.get("properties", {})
    for name in ("min_aum", "max_expense_ratio", "asset_class"):
        assert name in properties
