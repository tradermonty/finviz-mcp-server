"""Fixture-pinned tests for the Finviz groups (sector/industry/country/cap) path.

Everything here is offline: fixtures in ``tests/fixtures/`` are raw captures of
``grp_export.ashx`` responses (see ``GROUND_TRUTH.md``). The parsers used to
read column names that do not exist in any groups export (``Industry``,
``Country``, ``"1D %"``, ``"1W %"`` ...), so every group tool returned an empty
list; these tests pin the real headers.
"""

import os
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from src.finviz_client.sector_analysis import FinvizSectorAnalysisClient

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> pd.DataFrame:
    return pd.read_csv(FIXTURES / name)


@pytest.fixture
def client():
    return FinvizSectorAnalysisClient(api_key=os.getenv("FINVIZ_API_KEY", "test-key"))


# --------------------------------------------------------------------------
# Request shape
# --------------------------------------------------------------------------


def test_groups_request_always_pins_explicit_columns(client):
    """v=152 without c= returns the account's saved layout (unstable)."""
    params = client._groups_params("sector")

    assert params["g"] == "sector"
    assert params["v"] == "152"
    # Verified groups column ids from GROUND_TRUTH.md
    assert params["c"] == "0,1,2,3,4,10,15,16,17,18,19,20,21,22,23,24,25,26"


def test_sector_specific_request_sends_sg_code(client):
    with patch.object(
        client, "_fetch_csv_from_url", return_value=pd.DataFrame()
    ) as mock_fetch:
        client.get_sector_specific_industry_performance("basic_materials")

    params = mock_fetch.call_args[0][1]
    assert params["g"] == "industry"
    assert params["sg"] == "basicmaterials"
    assert params["c"] == client.GROUPS_COLUMN_IDS


# --------------------------------------------------------------------------
# Sector parsing (verified 29-column capture)
# --------------------------------------------------------------------------


def test_sector_parser_reads_every_row_of_the_verified_capture(client):
    df = _load("groups_sector_allcols.csv")
    rows = [client._parse_group_row(row) for _, row in df.iterrows()]

    assert len(rows) == len(df)
    assert all(r is not None for r in rows)

    for row in rows:
        assert row["name"]
        # Performance columns must actually be found, not silently defaulted
        for key in (
            "change",
            "performance_1w",
            "performance_1m",
            "performance_3m",
            "performance_6m",
            "performance_1y",
            "performance_ytd",
        ):
            assert row[key] is not None, key
            assert isinstance(row[key], float)
        # Market cap stays in millions of USD (as exported)
        assert row["market_cap"] is not None
        assert row["market_cap"] > 1_000  # i.e. >$1B, so clearly not raw dollars


def test_sector_parser_matches_known_fixture_values(client):
    df = _load("groups_sector_allcols.csv")
    rows = [client._parse_group_row(row) for _, row in df.iterrows()]
    by_name = {r["name"]: r for r in rows}

    basic = by_name["Basic Materials"]
    # Raw fixture row:
    # 1,"Basic Materials",2775035.58,21.12,13.82,...,2.02%,...,1.47%,0.94%,
    # -4.93%,-7.84%,33.79%,9.27%,2.02,645321.58,0.01,-0.09%,365150.00,285,...
    assert basic["market_cap"] == pytest.approx(2775035.58)  # $M
    assert basic["pe_ratio"] == pytest.approx(21.12)
    assert basic["forward_pe"] == pytest.approx(13.82)
    assert basic["dividend_yield"] == pytest.approx(2.02)
    assert basic["performance_1w"] == pytest.approx(1.47)
    assert basic["performance_1m"] == pytest.approx(0.94)
    assert basic["performance_3m"] == pytest.approx(-4.93)
    assert basic["performance_6m"] == pytest.approx(-7.84)
    assert basic["performance_1y"] == pytest.approx(33.79)
    assert basic["performance_ytd"] == pytest.approx(9.27)
    assert basic["analyst_recom"] == pytest.approx(2.02)
    assert basic["change"] == pytest.approx(-0.09)  # 1-day change, bare float
    assert basic["relative_volume"] == pytest.approx(0.01)
    assert basic["volume"] == pytest.approx(365150.0)
    assert basic["stock_count"] == 285
    # Average Volume is exported in thousands -> normalized to shares
    assert basic["avg_volume"] == pytest.approx(645321.58 * 1000)


def test_percent_values_lose_the_percent_sign_but_keep_zero(client):
    # 0.0 is a legitimate value, not "missing"
    assert client._parse_percent("0.00%") == 0.0
    assert client._parse_percent("-0.09%") == pytest.approx(-0.09)
    assert client._parse_percent("-") is None
    assert client._parse_percent("") is None
    assert client._parse_percent(None) is None
    assert client._parse_number("1,234.5") == pytest.approx(1234.5)
    assert client._parse_int("285") == 285
    assert client._parse_int("-") is None


# --------------------------------------------------------------------------
# Industry / country / capitalization parse to non-empty results
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "fixture,expected_name",
    [
        ("groups_industry_energy_cols.csv", "Oil & Gas Drilling"),
        ("groups_country_cols.csv", "Argentina"),
        ("groups_capitalization_cols.csv", "Large"),
    ],
)
def test_non_sector_groups_parse_non_empty(client, fixture, expected_name):
    """The group label column is ``Name`` for every g= value."""
    df = _load(fixture)
    rows = [client._parse_group_row(row) for _, row in df.iterrows()]

    assert rows and all(r is not None for r in rows)
    names = [r["name"] for r in rows]
    assert expected_name in names
    for row in rows:
        assert row["performance_1w"] is not None
        assert row["stock_count"] is not None


def test_industry_client_end_to_end_with_fixture(client):
    df = _load("groups_industry_energy_cols.csv")
    with patch.object(client, "_fetch_csv_from_url", return_value=df):
        rows = client.get_sector_specific_industry_performance("energy")

    assert len(rows) == len(df)
    assert all(r["parent_sector"] == "energy" for r in rows)
    assert rows[0]["name"] == "Oil & Gas Drilling"


def test_country_client_filter_is_case_insensitive(client):
    df = _load("groups_country_cols.csv")
    with patch.object(client, "_fetch_csv_from_url", return_value=df):
        rows = client.get_country_performance(["argentina"])

    assert [r["name"] for r in rows] == ["Argentina"]


# --------------------------------------------------------------------------
# Sector filter (D5): the tool used to pass the list into ``timeframe``
# --------------------------------------------------------------------------


def test_sector_filter_returns_only_requested_sectors(client):
    df = _load("groups_sector_allcols.csv")
    with patch.object(client, "_fetch_csv_from_url", return_value=df):
        rows = client.get_sector_performance(sectors=["Technology", "energy"])

    assert sorted(r["name"] for r in rows) == ["Energy", "Technology"]


def test_sector_filter_none_returns_everything(client):
    df = _load("groups_sector_allcols.csv")
    with patch.object(client, "_fetch_csv_from_url", return_value=df):
        rows = client.get_sector_performance()

    assert len(rows) == len(df)


def test_server_tool_passes_sectors_as_keyword_and_renders_all_fields():
    """The server tool must filter by sector and render every parsed field."""
    from src import server as server_module

    df = _load("groups_sector_allcols.csv")
    client = FinvizSectorAnalysisClient(api_key="test-key")
    with patch.object(client, "_fetch_csv_from_url", return_value=df):
        rows = client.get_sector_performance(sectors=["Technology"])

    with patch.object(
        server_module.finviz_sector, "get_sector_performance", return_value=rows
    ) as mock_sector:
        result = server_module.get_sector_performance(sectors=["Technology"])

    mock_sector.assert_called_once_with(sectors=["Technology"])
    text = result[0].text
    assert "Sector Performance Analysis" in text
    assert "Technology" in text
    # Every parsed field is visible somewhere in the table header
    for header in (
        "Market Cap",
        "P/E",
        "Fwd P/E",
        "Div %",
        "Change",
        "1W",
        "1M",
        "3M",
        "6M",
        "1Y",
        "YTD",
        "Recom",
        "Avg Vol",
        "Rel Vol",
        "Volume",
        "Stocks",
    ):
        assert header in text


def test_market_cap_is_rendered_scaled_and_labeled():
    from src.server import _fmt_group_market_cap

    # groups Market Cap arrives in millions of USD
    assert _fmt_group_market_cap(2775035.58) == "$2.78T"
    assert _fmt_group_market_cap(31548.03) == "$31.55B"
    assert _fmt_group_market_cap(500.0) == "$500.00M"
    assert _fmt_group_market_cap(None) == "N/A"


def test_capitalization_output_includes_dividend_yield():
    from src import server as server_module

    df = _load("groups_capitalization_cols.csv")
    client = FinvizSectorAnalysisClient(api_key="test-key")
    with patch.object(client, "_fetch_csv_from_url", return_value=df):
        rows = client.get_capitalization_performance()

    assert rows[0]["dividend_yield"] is not None

    with patch.object(
        server_module.finviz_sector,
        "get_capitalization_performance",
        return_value=rows,
    ):
        text = server_module.get_capitalization_performance()[0].text

    assert "Div %" in text
    # Dividend yield is a magnitude, so it renders unsigned (no "+" prefix)
    expected = f"{rows[0]['dividend_yield']:.2f}%"
    assert expected in text


def test_percent_columns_sign_only_where_the_sign_means_something():
    from src.server import _fmt_group_value

    # Moves carry a sign
    assert _fmt_group_value("change", -0.09) == "-0.09%"
    assert _fmt_group_value("change", 0.0) == "+0.00%"
    assert _fmt_group_value("performance_1y", 33.79) == "+33.79%"
    # Magnitudes do not
    assert _fmt_group_value("dividend_yield", 2.02) == "2.02%"
    assert _fmt_group_value("dividend_yield", 0.0) == "0.00%"
    assert _fmt_group_value("dividend_yield", None) == "N/A"
