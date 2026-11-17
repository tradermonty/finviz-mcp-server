"""Authentication failures must survive client fallbacks and reach MCP users."""

import inspect
from unittest.mock import Mock

import pytest
import requests

from mcp.server.fastmcp.exceptions import ToolError as McpToolError
from src import server
from src.finviz_client.base import FinvizAuthenticationError, FinvizClient
from src.finviz_client.news import FinvizNewsClient
from src.finviz_client.screener import FinvizScreener
from src.finviz_client.sec_filings import FinvizSECFilingsClient
from src.finviz_client.sector_analysis import FinvizSectorAnalysisClient


def response(text, status=200):
    result = requests.Response()
    result.status_code = status
    result._content = text.encode()
    result.encoding = "utf-8"
    return result


# Exercise the real client paths, not mocks of high-level methods.
CLIENT_CALLS = [
    (FinvizClient, "get_stock_data", ("AAPL",)),
    (FinvizClient, "screen_stocks", ({},)),
    (FinvizClient, "screen_stocks_raw", ("cap_large",)),
    (FinvizClient, "get_stock_fundamentals", ("AAPL",)),
    (FinvizClient, "get_multiple_stocks_fundamentals", (["AAPL", "MSFT"],)),
    (FinvizScreener, "volume_surge_screener", ()),
    (FinvizScreener, "upcoming_earnings_screener", ()),
    (FinvizScreener, "earnings_winners_screener", ()),
    (FinvizNewsClient, "get_stock_news", ("AAPL",)),
    (FinvizNewsClient, "get_market_news", ()),
    (FinvizNewsClient, "get_sector_news", ("Technology",)),
    (FinvizSectorAnalysisClient, "get_sector_performance", ()),
    (FinvizSectorAnalysisClient, "get_industry_performance", ()),
    (FinvizSectorAnalysisClient, "get_country_performance", ()),
    (
        FinvizSectorAnalysisClient,
        "get_sector_specific_industry_performance",
        ("Technology",),
    ),
    (FinvizSectorAnalysisClient, "get_capitalization_performance", ()),
    (FinvizSECFilingsClient, "get_sec_filings", ("AAPL",)),
    (FinvizSECFilingsClient, "get_filing_summary", ("AAPL",)),
]


@pytest.mark.parametrize("client_type,method,args", CLIENT_CALLS)
@pytest.mark.parametrize("failure", ["missing", "html", "401", "403"])
def test_client_auth_errors_reach_caller(
    monkeypatch, client_type, method, args, failure
):
    monkeypatch.delenv("FINVIZ_API_KEY", raising=False)
    key = None if failure == "missing" else "secret-test-key"
    client = client_type(api_key=key)
    client.rate_limit_delay = 0
    client.session.get = Mock(
        return_value=response(
            "  <!DoCtYpE hTmL><html>Login</html>",
            int(failure) if failure.isdigit() else 200,
        )
    )
    with pytest.raises(FinvizAuthenticationError) as exc:
        getattr(client, method)(*args)
    assert "FINVIZ_API_KEY" in str(exc.value)
    assert "secret-test-key" not in str(exc.value)
    if failure == "missing":
        assert "required" in str(exc.value)
        client.session.get.assert_not_called()
    else:
        assert "required" not in str(exc.value)
        assert client.session.get.call_count == 1


@pytest.mark.parametrize(
    "body",
    [
        "<!DOCTYPE html>Login",
        "\ufeff \n<HTML>Login</HTML>",
        " \n<!doctype HTML>Login",
    ],
)
@pytest.mark.parametrize("fetch", ["filters", "url"])
def test_both_csv_helpers_reject_html(monkeypatch, body, fetch):
    client = FinvizClient(api_key="test-key")
    monkeypatch.setattr(client, "_make_request", Mock(return_value=response(body)))
    with pytest.raises(FinvizAuthenticationError, match="HTML instead of CSV"):
        if fetch == "filters":
            client._fetch_csv_data({})
        else:
            client._fetch_csv_from_url(client.NEWS_EXPORT_URL)


@pytest.mark.parametrize("fetch", ["filters", "url"])
def test_valid_empty_csv_is_still_no_results(monkeypatch, fetch, caplog):
    client = FinvizClient(api_key="secret-test-key")
    request = Mock(return_value=response("Ticker,Company\n"))
    monkeypatch.setattr(client, "_make_request", request)
    with caplog.at_level("INFO"):
        result = (
            client._fetch_csv_data({})
            if fetch == "filters"
            else client._fetch_csv_from_url(client.EXPORT_URL)
        )
    assert result.empty
    assert list(result.columns) == ["Ticker", "Company"]
    assert "secret-test-key" not in caplog.text
    assert request.call_args.args[1]["auth"] == "secret-test-key"


def test_environment_key_resolved_at_request_time(monkeypatch):
    monkeypatch.delenv("FINVIZ_API_KEY", raising=False)
    client = FinvizClient()
    monkeypatch.setenv("FINVIZ_API_KEY", "later-key")
    request = Mock(return_value=response("Ticker\nAAPL\n"))
    monkeypatch.setattr(client, "_make_request", request)
    assert client._fetch_csv_from_url(client.EXPORT_URL).iloc[0]["Ticker"] == "AAPL"
    assert request.call_args.args[1]["auth"] == "later-key"


@pytest.mark.parametrize(
    "tool,args",
    [
        (server.volume_surge_screener, ()),
        (server.get_relative_volume_stocks, (1.2,)),
        (server.get_stock_fundamentals, ("AAPL",)),
        (server.get_multiple_stocks_fundamentals, (["AAPL", "MSFT"],)),
        (server.get_stock_news, ("AAPL",)),
        (server.get_market_news, ()),
        (server.get_sector_performance, ()),
        (server.get_sec_filings, ("AAPL",)),
        (server.get_market_overview, ()),
        (server.earnings_winners_screener, ()),
        (server.upcoming_earnings_screener, ()),
    ],
)
@pytest.mark.parametrize("key", [None, "rejected-test-key"])
async def test_mcp_tools_report_actionable_auth_errors(monkeypatch, tool, args, key):
    monkeypatch.delenv("FINVIZ_API_KEY", raising=False)
    clients = {
        "finviz_client": FinvizClient,
        "finviz_screener": FinvizScreener,
        "finviz_news": FinvizNewsClient,
        "finviz_sector": FinvizSectorAnalysisClient,
        "finviz_sec": FinvizSECFilingsClient,
    }
    for name, cls in clients.items():
        client = cls(api_key=key)
        client.rate_limit_delay = 0
        client.session.get = Mock(return_value=response("<html>Login</html>"))
        monkeypatch.setattr(server, name, client)
    arguments = dict(inspect.signature(tool).bind(*args).arguments)
    with pytest.raises(McpToolError) as exc:
        await server.server.call_tool(tool.__name__, arguments)
    text = str(exc.value)
    assert "FINVIZ_API_KEY" in text
    assert "No stocks found" not in text
    assert "No data found" not in text
    assert "rejected-test-key" not in text
