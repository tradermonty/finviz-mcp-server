"""Synthetic credentials must not escape through MCP reports or diagnostics."""

import logging
from unittest.mock import Mock
from urllib.parse import quote, quote_plus

import pytest
import requests

from mcp.server.fastmcp.exceptions import ToolError
from src import server
from src.finviz_client.base import FinvizClient, FinvizRequestError
from src.finviz_client.screener import FinvizScreener
from src.models import StockData
from src.utils.diagnostics import sanitize_diagnostics

SECRET = "synthetic key+/=&secret"
VARIANTS = (SECRET, quote(SECRET, safe=""), quote_plus(SECRET))


def assert_no_secret(text):
    for value in VARIANTS:
        assert value not in text


def test_parameter_redaction_keeps_filters():
    result = sanitize_diagnostics({"auth": SECRET, "f": "cap_large", "o": "ticker"})
    assert_no_secret(result)
    assert "cap_large" in result and "ticker" in result
    for value in VARIANTS:
        assert_no_secret(sanitize_diagnostics(f"redirect?auth={value}&f=cap_large"))
        assert_no_secret(sanitize_diagnostics(f"unstructured {value}", [SECRET]))


async def test_successful_mcp_report_has_no_authenticated_link(
    monkeypatch, caplog, capsys
):
    monkeypatch.setenv("FINVIZ_API_KEY", SECRET)
    client = FinvizScreener(api_key=SECRET)
    monkeypatch.setattr(
        client,
        "earnings_winners_screener",
        Mock(
            return_value=[
                StockData(
                    ticker="TEST",
                    company_name="Synthetic Inc",
                    sector="Technology",
                    industry="Software",
                    price=30.0,
                )
            ]
        ),
    )
    monkeypatch.setattr(server, "finviz_screener", client)
    result = await server.server.call_tool("earnings_winners_screener", {})
    assert_no_secret(str(result) + caplog.text + capsys.readouterr().err)
    report = "\n".join(server._format_earnings_winners_list([], {}))
    assert "auth=" not in report
    assert "screener" in report and "cap_" in report


@pytest.mark.parametrize(
    "kind", [requests.Timeout, requests.ConnectionError, requests.HTTPError]
)
async def test_request_failure_is_safe_at_mcp_boundary(
    monkeypatch, caplog, capsys, kind
):
    monkeypatch.delenv("FINVIZ_API_KEY", raising=False)
    client = FinvizScreener(api_key=SECRET)
    monkeypatch.setattr("src.finviz_client.base.time.sleep", lambda _: None)
    message = f"503 redirect https://elite.finviz.com/export?auth={quote(SECRET, safe='')}&f=cap_large; key {SECRET}"
    monkeypatch.setattr(client.session, "get", Mock(side_effect=kind(message)))
    monkeypatch.setattr(server, "finviz_screener", client)
    with caplog.at_level(logging.DEBUG):
        with pytest.raises(ToolError) as exc:
            await server.server.call_tool("volume_surge_screener", {})
    combined = str(exc.value) + caplog.text + capsys.readouterr().err
    assert_no_secret(combined)
    assert "503" in combined and "cap_large" in combined
    assert "[REDACTED]" in combined


def test_success_diagnostics_and_transport_debug_are_safe(monkeypatch, caplog):
    monkeypatch.setenv("FINVIZ_API_KEY", SECRET)
    client = FinvizClient(api_key=SECRET)
    client.rate_limit_delay = 0
    response = requests.Response()
    response.status_code = 200
    response._content = b"Ticker\nTEST\n"
    monkeypatch.setattr(client.session, "get", Mock(return_value=response))
    with caplog.at_level(logging.DEBUG):
        client._make_request(client.EXPORT_URL, {"auth": SECRET, "f": "cap_large"})
        logging.getLogger("urllib3.connectionpool").debug(
            "GET /export?auth=%s&f=cap_large HTTP/1.1", quote_plus(SECRET)
        )
    assert_no_secret(caplog.text)
    assert "cap_large" in caplog.text
    assert client.session.get.call_args.kwargs["params"]["auth"] == SECRET
