"""Regression tests for the defects found by the Phase 8 live sweep.

The offline suite was green while ``get_edgar_company_concept`` was dead on
every call — the tests mocked ``EdgarAPIClient.client`` so the kwarg mismatch
against the real ``sec_edgar_api`` signature never executed. These tests pin
the sweep's findings in ways mocks can't hide.
"""

from unittest.mock import patch

import pandas as pd
import pytest

from src.finviz_client.base import FinvizClient
from src.finviz_client.edgar_client import EdgarAPIClient
from src.server import _format_sma_line


class _RealSignatureEdgarStub:
    """Stub with sec-edgar-api's REAL parameter names (cik, taxonomy, tag).

    If the client code passes ``concept=`` the call raises TypeError, exactly
    like the installed library — which is how the tool was broken in
    production while mocked tests passed.
    """

    def get_company_concept(self, cik, taxonomy, tag):
        return {"cik": cik, "taxonomy": taxonomy, "tag": tag, "units": {}}


def test_get_company_concept_uses_the_librarys_tag_kwarg():
    client = EdgarAPIClient(user_agent="test test@example.invalid")
    client.client = _RealSignatureEdgarStub()
    with patch.object(client, "_get_cik_from_ticker", return_value="0000320193"):
        result = client.get_company_concept(
            "AAPL", concept="Revenues", taxonomy="us-gaap"
        )
    assert result.get("tag") == "Revenues"
    assert result.get("taxonomy") == "us-gaap"
    assert "error" not in result


def test_stub_signature_matches_installed_library():
    """If sec-edgar-api ever renames the parameter again, fail loudly here."""
    import inspect

    from sec_edgar_api import EdgarClient

    real = list(inspect.signature(EdgarClient.get_company_concept).parameters)
    stub = list(
        inspect.signature(_RealSignatureEdgarStub.get_company_concept).parameters
    )
    assert real == stub


class TestSmaLineUnits:
    """technical_analysis detail blocks rendered derived dollar SMAs with a
    percent sign (SMA 200: +56.09%). The line must label each unit."""

    def test_dollar_and_percent_both_labelled(self):
        line = _format_sma_line("SMA 200", 56.09, -19.62)
        assert "$56.09" in line
        assert "-19.62% vs price" in line
        assert "+56.09%" not in line

    def test_absolute_only(self):
        assert _format_sma_line("SMA 20", 203.12, None) == "SMA 20: $203.12"

    def test_relative_only(self):
        assert _format_sma_line("SMA 20", None, 0.0) == "SMA 20: (+0.00% vs price)"

    def test_missing(self):
        assert _format_sma_line("SMA 50", None, None) == "SMA 50: N/A"


def test_zero_price_change_renders_in_detail_blocks():
    """The premarket/afterhours/trading top-5 detail blocks used
    ``if stock.price and stock.price_change`` — a real 0.0 change (or a
    theoretical 0 price) rendered N/A while the table above showed +0.00%."""
    from src.server import _format_earnings_premarket_list
    from tests import factories

    stock = factories.make_stock_data(price=10.0, price_change=0.0)
    text = "\n".join(_format_earnings_premarket_list([stock], {}))
    assert "Change: +0.00%" in text
    assert "Change: N/A" not in text


def test_csv_responses_decode_as_utf8_without_charset_header():
    """Finviz omits the charset header; requests then falls back to
    ISO-8859-1 and UTF-8 punctuation double-encodes (â€™ mojibake)."""
    import requests

    client = FinvizClient(api_key="test-key")
    resp = requests.Response()
    resp.status_code = 200
    resp._content = 'Title,Source\n"Fund’s Implosion",WSJ\n'.encode("utf-8")
    resp.headers["Content-Type"] = "text/csv"  # no charset
    assert resp.encoding is None or resp.encoding.lower() == "iso-8859-1"
    df = client._csv_response_to_dataframe(resp, "https://example.invalid")
    assert df.iloc[0]["Title"] == "Fund’s Implosion"


def test_trend_reversion_prints_its_criteria_block():
    """Every sibling screener prints a derived criteria block; this one
    printed nothing, so cap_midover/ta_rsi could not be seen by the user."""
    from src.finviz_client.screener import FinvizScreener
    from src.server import trend_reversion_screener
    from tests import factories

    with patch.object(
        FinvizScreener,
        "trend_reversion_screener",
        return_value=[factories.make_stock_data()],
    ):
        text = trend_reversion_screener(market_cap="mid_large", rsi_max=40)[0].text
    assert "cap_midover" in text
    assert "f=" in text
