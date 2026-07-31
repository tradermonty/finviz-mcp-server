"""Phase 4 — news tool correctness (AUDIT_FINDINGS.md C2-C10).

Everything here is offline and pinned to the raw ``news_export.ashx`` captures
in ``tests/fixtures``:

* ``news_v1_market.csv``    — v=1 market feed (no Ticker column)
* ``news_v3_aapl.csv``      — v=3, single ticker
* ``news_v3_aapl_msft.csv`` — v=3, two tickers (real per-row attribution)
"""

from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from src.finviz_client.base import SECTOR_CODES, resolve_sector_code
from src.finviz_client.news import EASTERN, FinvizNewsClient, _cell

FIXTURES = Path(__file__).parent / "fixtures"

MARKET_CSV = FIXTURES / "news_v1_market.csv"
AAPL_CSV = FIXTURES / "news_v3_aapl.csv"
TWO_TICKER_CSV = FIXTURES / "news_v3_aapl_msft.csv"

# Cutoff far in the past so date filtering never hides a fixture row.
ANCIENT = datetime(2000, 1, 1, tzinfo=EASTERN)


def client() -> FinvizNewsClient:
    return FinvizNewsClient(api_key="test-key")


def fetch_returning(df: pd.DataFrame):
    """Patch the CSV fetch so a client call consumes ``df``."""
    return patch.object(FinvizNewsClient, "_fetch_csv_from_url", return_value=df)


# ---------------------------------------------------------------------------
# C4 — market news uses the v=1 feed
# ---------------------------------------------------------------------------


def test_market_news_requests_the_v1_feed():
    df = pd.read_csv(MARKET_CSV)
    with patch.object(
        FinvizNewsClient, "_fetch_csv_from_url", return_value=df
    ) as fetch:
        client().get_market_news(days_back=36500)

    (_url, params), _kwargs = fetch.call_args
    assert params["v"] == "1"
    assert "sec" not in params and "filter" not in params


def test_market_news_parses_the_v1_fixture():
    df = pd.read_csv(MARKET_CSV)
    assert "Ticker" not in df.columns  # header sanity for the v=1 feed

    with fetch_returning(df):
        news = client().get_market_news(days_back=36500, max_items=200)

    assert len(news) == len(df)
    for item in news:
        assert item.title and item.source and item.url.startswith("http")
        assert item.category in {"Market", "Blog"}
        # C7: v=1 has no Ticker column, so nothing is invented.
        assert item.ticker is None
        # C6: every timestamp is tz-aware Eastern.
        assert item.date.tzinfo is not None
        assert item.date.utcoffset() == item.date.astimezone(EASTERN).utcoffset()


def test_market_news_renders_no_nan_strings():
    df = pd.read_csv(MARKET_CSV)
    with fetch_returning(df):
        news = client().get_market_news(days_back=36500, max_items=200)

    for item in news:
        for value in (item.title, item.source, item.url, item.category):
            assert "nan" != (value or "").lower()


# ---------------------------------------------------------------------------
# C10 — NaN cells never render as the string "nan"
# ---------------------------------------------------------------------------


def test_nan_cells_become_empty_not_the_string_nan():
    row = pd.Series(
        {
            "Title": "A headline",
            "Source": float("nan"),
            "Date": "2026-07-31 04:07:58",
            "Url": float("nan"),
            "Category": float("nan"),
        }
    )
    item = client()._parse_news_from_csv(row, ANCIENT)

    assert item is not None
    assert item.source == ""
    assert item.url == ""
    assert item.category == ""
    assert _cell(row, "Source") == ""
    assert _cell(row, "Missing") == ""


def test_row_without_a_title_is_skipped():
    row = pd.Series(
        {
            "Title": float("nan"),
            "Source": "Reuters",
            "Date": "2026-07-31 04:07:58",
            "Url": "https://example.test/a",
            "Category": "Market",
        }
    )
    assert client()._parse_news_from_csv(row, ANCIENT) is None


def test_server_render_omits_missing_fields_instead_of_printing_nan():
    from src.models import NewsData
    from src.server import _render_news_items

    item = NewsData(
        ticker=None,
        title="A headline",
        source="",
        date=datetime(2026, 7, 31, 4, 7, tzinfo=EASTERN),
        url="",
        category="",
    )
    text = "\n".join(_render_news_items([item], "-" * 10))

    assert "A headline" in text
    assert "nan" not in text.lower()
    assert "Source:" not in text
    assert "URL:" not in text
    assert "Ticker:" not in text


# ---------------------------------------------------------------------------
# C6 — timezone handling and days_back cutoffs
# ---------------------------------------------------------------------------


def _row(date_str: str, title: str = "t", ticker: str = "AAPL") -> pd.Series:
    return pd.Series(
        {
            "Title": title,
            "Source": "Reuters",
            "Date": date_str,
            "Url": "https://example.test/a",
            "Category": "Stock",
            "Ticker": ticker,
        }
    )


def test_days_back_cutoff_uses_eastern_now_regardless_of_local_tz():
    """The window is computed in ET, so a fake ``now`` fully determines it."""
    fake_now = datetime(2026, 7, 31, 12, 0, tzinfo=EASTERN)
    df = pd.DataFrame(
        [
            _row(
                (fake_now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S"), "fresh"
            ),
            _row((fake_now - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S"), "stale"),
        ]
    )

    with patch("src.finviz_client.news._now_et", return_value=fake_now):
        with fetch_returning(df):
            news = client().get_stock_news("AAPL", days_back=1)

    assert [n.title for n in news] == ["fresh"]


def test_cutoff_helper_is_eastern_anchored():
    fake_now = datetime(2026, 7, 31, 12, 0, tzinfo=EASTERN)
    with patch("src.finviz_client.news._now_et", return_value=fake_now):
        cutoff = FinvizNewsClient._cutoff(2)
    assert cutoff == fake_now - timedelta(days=2)
    assert cutoff.tzinfo is not None


def test_naive_cutoff_is_interpreted_as_eastern_and_never_crashes():
    """Aware CSV dates vs a naive cutoff must not raise (C6 regression)."""
    item = client()._parse_news_from_csv(
        _row("2026-07-31 04:07:58"), datetime(2026, 7, 30, 0, 0)
    )
    assert item is not None
    assert item.date.tzinfo is not None


@pytest.mark.parametrize(
    "date_str,expected_offset_hours",
    [
        ("2026-01-15 12:00:00", -5),  # EST
        ("2026-07-15 12:00:00", -4),  # EDT
        ("2026-03-08 03:00:00", -4),  # just after the spring-forward gap
        ("2026-11-01 03:00:00", -5),  # just after the fall-back overlap
    ],
)
def test_dst_boundaries_get_the_right_eastern_offset(date_str, expected_offset_hours):
    parsed = client()._parse_news_date_from_csv(date_str)
    assert parsed is not None
    assert parsed.utcoffset() == timedelta(hours=expected_offset_hours)


def test_server_renders_an_explicit_et_suffix():
    from src.models import NewsData
    from src.server import _render_news_items

    item = NewsData(
        ticker="AAPL",
        title="A headline",
        source="Reuters",
        date=datetime(2026, 7, 31, 4, 7, tzinfo=EASTERN),
        url="https://example.test/a",
        category="Stock",
    )
    text = "\n".join(_render_news_items([item], "-" * 10))
    assert "📅 Date: 2026-07-31 04:07 ET" in text


# ---------------------------------------------------------------------------
# C7 — the real per-row Ticker is kept and rendered
# ---------------------------------------------------------------------------


def test_single_ticker_request_still_uses_the_csv_ticker_not_the_request():
    """A single-ticker request must not stamp its own ticker onto the rows.

    ``t=AAPL`` can still return an item covering several names, so the CSV
    value has to win over the requested one (on HEAD the request was echoed
    onto every row, which this fixture would have hidden).
    """
    df = pd.DataFrame(
        [
            _row("2026-07-31 04:12:27", title="two-name item", ticker="AAPL,MSFT"),
            _row("2026-07-31 04:11:00", title="one-name item", ticker="AAPL"),
        ]
    )
    with fetch_returning(df):
        news = client().get_stock_news("AAPL", days_back=36500)

    assert [n.ticker for n in news] == ["AAPL,MSFT", "AAPL"]


def test_requested_ticker_is_only_a_fallback_for_an_empty_ticker_cell():
    df = pd.DataFrame([_row("2026-07-31 04:12:27", ticker=float("nan"))])
    with fetch_returning(df):
        news = client().get_stock_news("AAPL", days_back=36500)

    assert [n.ticker for n in news] == ["AAPL"]


def test_multi_ticker_request_never_invents_a_fallback_attribution():
    """With several tickers requested there is no honest fallback: None."""
    df = pd.DataFrame([_row("2026-07-31 04:12:27", ticker=float("nan"))])
    with fetch_returning(df):
        news = client().get_stock_news("AAPL,MSFT", days_back=36500)

    assert [n.ticker for n in news] == [None]


def test_multi_ticker_news_attributes_rows_to_their_real_tickers():
    df = pd.read_csv(TWO_TICKER_CSV)
    with fetch_returning(df):
        news = client().get_stock_news("AAPL,MSFT", days_back=36500)

    tickers = {n.ticker for n in news}
    # Real attribution, not the request echoed back on every row.
    assert "AAPL" in tickers and "MSFT" in tickers
    assert tickers == set(df["Ticker"].tolist())
    # Multi-name items keep the comma-joined truth from the feed.
    assert any("," in t for t in tickers)

    for item, (_, row) in zip(news, df.iterrows()):
        assert item.ticker == row["Ticker"]


def test_multi_ticker_request_is_a_single_v3_call():
    df = pd.read_csv(TWO_TICKER_CSV)
    with patch.object(
        FinvizNewsClient, "_fetch_csv_from_url", return_value=df
    ) as fetch:
        client().get_stock_news("AAPL, MSFT", days_back=36500)

    assert fetch.call_count == 1
    (_url, params), _kwargs = fetch.call_args
    assert params == {"v": "3", "t": "AAPL,MSFT"}


def test_server_renders_the_per_item_ticker():
    from src.server import _render_news_items

    df = pd.read_csv(TWO_TICKER_CSV)
    with fetch_returning(df):
        news = client().get_stock_news("AAPL,MSFT", days_back=36500)

    text = "\n".join(_render_news_items(news, "-" * 10))
    assert "📈 Ticker: AAPL" in text
    assert "📈 Ticker: MSFT" in text


# ---------------------------------------------------------------------------
# C8 — the real Category column, never a keyword guess
# ---------------------------------------------------------------------------


def test_category_comes_from_the_csv_not_from_title_keywords():
    item = client()._parse_news_from_csv(
        _row("2026-07-31 04:07:58", title="Revenue soars as earnings beat"), ANCIENT
    )
    assert item is not None
    assert item.category == "Stock"  # the CSV value, not a guessed "earnings"


def test_market_feed_categories_are_the_real_column_values():
    df = pd.read_csv(MARKET_CSV)
    with fetch_returning(df):
        news = client().get_market_news(days_back=36500, max_items=500)

    assert {n.category for n in news} == set(df["Category"].unique())


def test_keyword_categoriser_is_gone():
    assert not hasattr(FinvizNewsClient, "_categorize_news")


# ---------------------------------------------------------------------------
# C9 — dead HTML-era parsers removed
# ---------------------------------------------------------------------------


def test_dead_html_era_helpers_are_gone():
    assert not hasattr(FinvizNewsClient, "_parse_news_date")
    assert not hasattr(FinvizNewsClient, "_extract_news_source")


# ---------------------------------------------------------------------------
# C3 — news_type was a fake filter and is gone; market news gains an honest
#      client-side Category filter (the only real taxonomy in the feed).
# ---------------------------------------------------------------------------


def test_stock_news_takes_no_news_type_argument():
    import inspect

    from src import server

    client_params = inspect.signature(FinvizNewsClient.get_stock_news).parameters
    assert "news_type" not in client_params

    tool = getattr(server.get_stock_news, "fn", server.get_stock_news)
    assert "news_type" not in inspect.signature(tool).parameters


@pytest.mark.asyncio
async def test_news_type_is_absent_from_the_mcp_tool_schema():
    from src import server

    tools = await server.server.list_tools()
    schema = next(t for t in tools if t.name == "get_stock_news").inputSchema
    assert "news_type" not in schema.get("properties", {})


def test_market_news_category_filter_uses_the_real_column():
    df = pd.read_csv(MARKET_CSV)
    with fetch_returning(df):
        blogs = client().get_market_news(
            days_back=36500, max_items=500, category="blog"
        )

    assert blogs
    assert {n.category for n in blogs} == {"Blog"}
    assert len(blogs) == int((df["Category"] == "Blog").sum())


def test_market_news_category_filter_is_client_side_only():
    df = pd.read_csv(MARKET_CSV)
    with patch.object(
        FinvizNewsClient, "_fetch_csv_from_url", return_value=df
    ) as fetch:
        client().get_market_news(days_back=36500, category="Market")

    (_url, params), _kwargs = fetch.call_args
    assert params == {"v": "1"}  # nothing fake is sent to Finviz


def test_unknown_market_news_category_raises_instead_of_returning_nothing():
    """ "Blogs" must not silently look like "no news today"."""
    with patch.object(FinvizNewsClient, "_fetch_csv_from_url") as fetch:
        with pytest.raises(ValueError, match="Unknown market news category"):
            client().get_market_news(category="Blogs")
    fetch.assert_not_called()


@pytest.mark.parametrize("category", ["Market", "market", " BLOG "])
def test_known_market_news_categories_are_accepted_case_insensitively(category):
    df = pd.read_csv(MARKET_CSV)
    with fetch_returning(df):
        news = client().get_market_news(days_back=36500, max_items=5, category=category)
    assert news


def test_declared_market_categories_match_the_fixture():
    df = pd.read_csv(MARKET_CSV)
    assert set(FinvizNewsClient.MARKET_NEWS_CATEGORIES) == set(df["Category"].unique())


# ---------------------------------------------------------------------------
# Drop policy: nothing vanishes silently
# ---------------------------------------------------------------------------


def test_undated_rows_are_dropped_but_counted_in_one_warning(caplog):
    df = pd.DataFrame(
        [
            _row("2026-07-31 04:12:27", title="good"),
            _row("", title="no date"),
            _row("-", title="dash date"),
            _row("not a date at all", title="junk date"),
            _row("2026-07-31 04:00:00", title=float("nan")),
        ]
    )
    with caplog.at_level("WARNING"):
        with fetch_returning(df):
            news = client().get_stock_news("AAPL", days_back=36500)

    assert [n.title for n in news] == ["good"]

    summaries = [
        r for r in caplog.records if "Dropped 4 of 5 news rows" in r.getMessage()
    ]
    assert len(summaries) == 1
    message = summaries[0].getMessage()
    assert "3 with an empty/unparseable Date" in message
    assert "1 with no Title" in message


def test_no_warning_when_every_row_is_usable(caplog):
    df = pd.read_csv(AAPL_CSV)
    with caplog.at_level("WARNING"):
        with fetch_returning(df):
            client().get_stock_news("AAPL", days_back=36500)

    assert not [r for r in caplog.records if "news rows" in r.getMessage()]


# ---------------------------------------------------------------------------
# Cutoff boundary is inclusive (documented behavior)
# ---------------------------------------------------------------------------


def test_item_exactly_days_back_old_is_kept():
    fake_now = datetime(2026, 7, 31, 12, 0, tzinfo=EASTERN)
    exact = fake_now - timedelta(days=2)
    df = pd.DataFrame(
        [
            _row(exact.strftime("%Y-%m-%d %H:%M:%S"), title="exactly on the boundary"),
            _row(
                (exact - timedelta(seconds=1)).strftime("%Y-%m-%d %H:%M:%S"),
                title="one second older",
            ),
        ]
    )

    with patch("src.finviz_client.news._now_et", return_value=fake_now):
        with fetch_returning(df):
            news = client().get_stock_news("AAPL", days_back=2)

    assert [n.title for n in news] == ["exactly on the boundary"]


# ---------------------------------------------------------------------------
# C2 — sector news is built from real constituents
# ---------------------------------------------------------------------------


def test_sector_news_fetches_constituents_then_their_news():
    constituents = pd.DataFrame(
        {
            "Ticker": ["AAPL", "MSFT"],
            "Company": ["Apple Inc", "Microsoft Corp"],
            "Market Cap": [4536924.31, 3326644.34],
        }
    )
    news_df = pd.read_csv(TWO_TICKER_CSV)

    with patch.object(
        FinvizNewsClient, "_fetch_csv_from_url", side_effect=[constituents, news_df]
    ) as fetch:
        news = client().get_sector_news("Technology", days_back=36500, max_items=500)

    # Exactly two requests: constituents, then news.
    assert fetch.call_count == 2
    (_url1, screen_params), _ = fetch.call_args_list[0]
    assert screen_params["f"] == "sec_technology"
    assert screen_params["o"] == "-marketcap"
    (_url2, news_params), _ = fetch.call_args_list[1]
    assert news_params == {"v": "3", "t": "AAPL,MSFT"}
    assert "sec" not in news_params

    # Items carry their real tickers, all from the sector's constituents.
    assert news
    assert {n.ticker for n in news} <= {"AAPL", "MSFT", "AAPL,MSFT", "MSFT,AAPL"}
    assert "AAPL" in {n.ticker for n in news}
    assert "MSFT" in {n.ticker for n in news}


def test_sector_news_caps_the_constituent_list():
    many = pd.DataFrame({"Ticker": [f"T{i}" for i in range(200)]})
    news_df = pd.read_csv(AAPL_CSV)

    with patch.object(
        FinvizNewsClient, "_fetch_csv_from_url", side_effect=[many, news_df]
    ) as fetch:
        client().get_sector_news("technology", days_back=36500)

    (_url, news_params), _ = fetch.call_args_list[1]
    assert len(news_params["t"].split(",")) == FinvizNewsClient.SECTOR_TICKER_LIMIT


def test_unknown_sector_raises_before_any_request():
    with patch.object(FinvizNewsClient, "_fetch_csv_from_url") as fetch:
        with pytest.raises(ValueError, match="Unknown sector"):
            client().get_sector_news("Blockchain")
    fetch.assert_not_called()


def test_empty_constituent_list_raises():
    empty = pd.DataFrame({"Ticker": []})
    with patch.object(FinvizNewsClient, "_fetch_csv_from_url", return_value=empty):
        with pytest.raises(ValueError, match="no constituents"):
            client().get_sector_news("Energy")


def test_sector_news_header_is_not_fabricated_attribution():
    """The header may name the sector only because the items really are its."""
    import asyncio

    from src import server

    constituents = pd.DataFrame({"Ticker": ["AAPL", "MSFT"]})
    news_df = pd.read_csv(TWO_TICKER_CSV)

    with patch.object(
        FinvizNewsClient, "_fetch_csv_from_url", side_effect=[constituents, news_df]
    ):
        result = asyncio.run(
            server.server.call_tool(
                "get_sector_news",
                {"sector": "Technology", "days_back": 36500, "max_items": 5},
            )
        )

    text = result[0][0].text
    assert "Technology Sector News" in text
    assert "constituents by market cap" in text
    assert "📈 Ticker: AAPL" in text or "📈 Ticker: MSFT" in text


# ---------------------------------------------------------------------------
# Centralised sector-code table (no duplicated mapping)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "name,code",
    [
        ("Technology", "technology"),
        ("technology", "technology"),
        ("Consumer Cyclical", "consumercyclical"),
        ("consumer_cyclical", "consumercyclical"),
        ("consumercyclical", "consumercyclical"),
        ("Financial Services", "financial"),
        ("Real Estate", "realestate"),
    ],
)
def test_sector_code_resolution(name, code):
    assert resolve_sector_code(name) == code


def test_unknown_sector_code_resolves_to_none():
    assert resolve_sector_code("Crypto") is None
    assert resolve_sector_code("") is None


def test_client_helper_delegates_to_the_shared_table():
    from src.finviz_client.base import FinvizClient

    for display, code in SECTOR_CODES.items():
        assert FinvizClient(api_key="k")._get_sector_code(display) == code


def test_groups_sg_codes_resolve_through_the_same_table():
    """``sg=`` (groups) and ``f=sec_`` (screener) share one code vocabulary.

    These are exactly the keys the groups client used to carry in its own
    inline map; they must keep resolving to the same tokens now that the map
    is gone.
    """
    legacy_sg_map = {
        "basicmaterials": "basicmaterials",
        "basic_materials": "basicmaterials",
        "communicationservices": "communicationservices",
        "communication_services": "communicationservices",
        "consumercyclical": "consumercyclical",
        "consumer_cyclical": "consumercyclical",
        "consumerdefensive": "consumerdefensive",
        "consumer_defensive": "consumerdefensive",
        "energy": "energy",
        "financial": "financial",
        "healthcare": "healthcare",
        "industrials": "industrials",
        "realestate": "realestate",
        "real_estate": "realestate",
        "technology": "technology",
        "utilities": "utilities",
    }
    for name, code in legacy_sg_map.items():
        assert resolve_sector_code(name) == code


def test_unknown_sg_value_is_still_passed_through_lowercased():
    """Unchanged legacy behavior: Finviz ignores an unknown sg= itself."""
    from src.finviz_client.sector_analysis import FinvizSectorAnalysisClient

    groups = FinvizSectorAnalysisClient(api_key="test-key")
    with patch.object(
        FinvizSectorAnalysisClient, "_fetch_csv_from_url", return_value=pd.DataFrame()
    ) as fetch:
        groups.get_sector_specific_industry_performance("Nonexistent Sector")

    assert fetch.call_args[0][1]["sg"] == "nonexistent sector"


# ---------------------------------------------------------------------------
# Constituent ordering is verified client-side, not taken on trust
# ---------------------------------------------------------------------------


def test_constituents_are_re_sorted_client_side_by_market_cap():
    """``o=-marketcap`` could be silently ignored, so we sort what we got."""
    from src.finviz_client.base import FinvizClient

    scrambled = pd.DataFrame(
        {
            "Ticker": ["SMALL", "HUGE", "MID"],
            "Company": ["Small Co", "Huge Co", "Mid Co"],
            "Market Cap": [100.0, 9000.0, 500.0],
        }
    )
    with patch.object(FinvizClient, "_fetch_csv_from_url", return_value=scrambled):
        tickers = FinvizClient(api_key="k").get_sector_constituent_tickers(
            "Technology", limit=2
        )

    assert tickers == ["HUGE", "MID"]


def test_constituents_with_unparseable_market_cap_sort_last_but_are_kept():
    from src.finviz_client.base import FinvizClient

    df = pd.DataFrame(
        {
            "Ticker": ["NOCAP", "BIG"],
            "Market Cap": ["-", 9000.0],
        }
    )
    with patch.object(FinvizClient, "_fetch_csv_from_url", return_value=df):
        tickers = FinvizClient(api_key="k").get_sector_constituent_tickers("Technology")

    assert tickers == ["BIG", "NOCAP"]


def test_constituents_keep_feed_order_when_market_cap_is_unusable():
    from src.finviz_client.base import FinvizClient

    df = pd.DataFrame({"Ticker": ["A", "B"], "Market Cap": ["-", "-"]})
    with patch.object(FinvizClient, "_fetch_csv_from_url", return_value=df):
        tickers = FinvizClient(api_key="k").get_sector_constituent_tickers("Technology")

    assert tickers == ["A", "B"]


def test_constituent_request_still_asks_for_the_server_side_sort():
    from src.finviz_client.base import FinvizClient

    df = pd.DataFrame({"Ticker": ["A"], "Market Cap": [1.0]})
    with patch.object(FinvizClient, "_fetch_csv_from_url", return_value=df) as fetch:
        FinvizClient(api_key="k").get_sector_constituent_tickers("Technology")

    params = fetch.call_args[0][1]
    assert params["o"] == "-marketcap"
    assert params["c"] == "1,2,6"
