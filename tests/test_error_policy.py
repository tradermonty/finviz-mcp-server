"""Request-level failure policy: failures must look like failures.

GROUND_TRUTH.md house rule 3 — "Failures must be reported as failures, never
``[]``-as-'no results'". Every client used to convert *any* exception into an
empty list / empty DataFrame, so a bad API key, an HTML login page or a dead
network read out as "No stocks found" / "No news found" / "No SEC filings
found" — indistinguishable from a genuinely empty result set.

The policy pinned here:

* missing API key, transport failure (connection/timeout/HTTP status),
  HTML-instead-of-CSV and unparseable payloads raise ``FinvizAPIError``;
* a header-only CSV (zero data rows) is a legitimate empty result and comes
  back as an empty list, no exception.

Also pins B8: nothing may be written to stdout, which is the MCP stdio
JSON-RPC channel.
"""

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import requests

from src.finviz_client.news import FinvizNewsClient
from src.finviz_client.screener import FinvizScreener
from src.finviz_client.sec_filings import FinvizSECFilingsClient
from src.finviz_client.sector_analysis import FinvizSectorAnalysisClient
from src.utils.exceptions import FinvizAPIError
from tests import factories

REPO_ROOT = Path(__file__).resolve().parents[1]

HTML_BODY = (
    "<!DOCTYPE html>\n<html><head><title>Finviz</title></head>"
    "<body>Please log in</body></html>"
)

# Header-only captures: the real column headers (GROUND_TRUTH.md) with zero
# data rows — what Finviz returns when a query legitimately matches nothing.
STOCK_HEADER_ONLY = "No.,Ticker,Company,Sector,Industry,Country,Market Cap,Price\n"
GROUPS_HEADER_ONLY = "No.,Name,Market Cap,P/E,Performance (Week),Change,Volume\n"
NEWS_HEADER_ONLY = "Title,Source,Date,Url,Category\n"
SEC_HEADER_ONLY = "Filing Date,Report Date,Form,Description,Filing,Document\n"


class _FakeResponse:
    """Minimal stand-in for ``requests.Response`` (only what clients touch)."""

    def __init__(self, text: str) -> None:
        self.text = text
        self.status_code = 200

    def raise_for_status(self) -> None:
        return None


@pytest.fixture(autouse=True)
def _no_sleeping(monkeypatch):
    """Keep retry/rate-limit sleeps out of the test runtime."""
    monkeypatch.setattr("src.finviz_client.base.time.sleep", lambda *_: None)


# --------------------------------------------------------------------------
# One entry per client path, exercised through its public method.
# --------------------------------------------------------------------------


def _screener_stocks(client):
    return client.screen_stocks({"market_cap": "large"})


def _groups(client):
    return client.get_sector_performance()


def _news(client):
    return client.get_stock_news("AAPL")


def _sec_filings(client):
    return client.get_sec_filings("AAPL")


CLIENT_PATHS = [
    pytest.param(FinvizScreener, _screener_stocks, STOCK_HEADER_ONLY, id="screener"),
    pytest.param(FinvizSectorAnalysisClient, _groups, GROUPS_HEADER_ONLY, id="groups"),
    pytest.param(FinvizNewsClient, _news, NEWS_HEADER_ONLY, id="news"),
    pytest.param(
        FinvizSECFilingsClient, _sec_filings, SEC_HEADER_ONLY, id="sec_filings"
    ),
]


def _client(cls):
    return cls(api_key="test-key")


@pytest.mark.parametrize("cls,call,_header", CLIENT_PATHS)
def test_connection_error_raises_instead_of_returning_empty(cls, call, _header):
    """A dead network must not read as "nothing matched"."""
    client = _client(cls)

    with patch.object(
        client.session,
        "get",
        side_effect=requests.exceptions.ConnectionError("no route"),
    ):
        with pytest.raises(FinvizAPIError) as exc_info:
            call(client)

    message = str(exc_info.value)
    assert "no route" in message, message
    assert "finviz.com" in message, message


@pytest.mark.parametrize("cls,call,_header", CLIENT_PATHS)
def test_html_response_raises_with_actionable_message(cls, call, _header):
    """HTML where CSV was requested means auth/subscription, not empty."""
    client = _client(cls)

    with patch.object(client.session, "get", return_value=_FakeResponse(HTML_BODY)):
        with pytest.raises(FinvizAPIError) as exc_info:
            call(client)

    message = str(exc_info.value)
    assert "HTML instead of CSV" in message, message
    assert "FINVIZ_API_KEY" in message, message


@pytest.mark.parametrize("cls,call,header", CLIENT_PATHS)
def test_header_only_csv_is_a_clean_empty_result(cls, call, header):
    """Zero data rows is a real answer: empty list, no exception."""
    client = _client(cls)

    with patch.object(client.session, "get", return_value=_FakeResponse(header)):
        assert call(client) == []


@pytest.mark.parametrize("cls,call,_header", CLIENT_PATHS)
def test_missing_api_key_raises_before_any_request(cls, call, _header, monkeypatch):
    """Without a key the export cannot work — say so, don't return []."""
    monkeypatch.delenv("FINVIZ_API_KEY", raising=False)
    client = cls(api_key=None)

    with patch.object(client.session, "get") as mock_get:
        with pytest.raises(FinvizAPIError) as exc_info:
            call(client)

    assert "FINVIZ_API_KEY" in str(exc_info.value)
    mock_get.assert_not_called()


def test_http_status_error_raises():
    """``raise_for_status`` failures (401/403/500...) propagate as API errors."""
    client = _client(FinvizScreener)

    class _ErrorResponse(_FakeResponse):
        def raise_for_status(self):
            raise requests.exceptions.HTTPError("401 Client Error: Unauthorized")

    with patch.object(client.session, "get", return_value=_ErrorResponse("")):
        with pytest.raises(FinvizAPIError) as exc_info:
            client.screen_stocks({})

    assert "401" in str(exc_info.value)


def test_bom_prefixed_html_is_still_rejected():
    """A UTF-8 BOM must not smuggle an error page past the CSV check.

    ``str.strip()`` does not remove ``\\ufeff``, so a BOM-prefixed login
    page used to reach ``pd.read_csv`` and parse into a bogus one-column
    DataFrame — the swallow-to-empty bug wearing a hat.
    """
    client = _client(FinvizScreener)
    body = "﻿" + HTML_BODY

    with patch.object(client.session, "get", return_value=_FakeResponse(body)):
        with pytest.raises(FinvizAPIError) as exc_info:
            client.screen_stocks({})

    assert "HTML instead of CSV" in str(exc_info.value)


def test_empty_body_raises_rather_than_looking_empty():
    """A zero-byte body is not a CSV — a real empty result still has headers."""
    client = _client(FinvizScreener)

    with patch.object(client.session, "get", return_value=_FakeResponse("")):
        with pytest.raises(FinvizAPIError) as exc_info:
            client.screen_stocks({})

    assert "empty response body" in str(exc_info.value)


# --------------------------------------------------------------------------
# The Elite key travels as ``auth=`` in the query string, so it leaks through
# anything that echoes a request URL — requests' own exception text included.
# --------------------------------------------------------------------------

SECRET_KEY = "SECRETKEY123"

# What requests actually puts in the message: the full URL, key and all.
LEAKY_HTTP_ERROR = (
    "401 Client Error: Unauthorized for url: "
    f"https://elite.finviz.com/export.ashx?v=151&f=cap_large&auth={SECRET_KEY}"
)


def test_api_key_is_redacted_from_the_raised_error():
    client = FinvizScreener(api_key=SECRET_KEY)

    with patch.object(
        client.session,
        "get",
        side_effect=requests.exceptions.HTTPError(LEAKY_HTTP_ERROR),
    ):
        with pytest.raises(FinvizAPIError) as exc_info:
            client.screen_stocks({})

    message = str(exc_info.value)
    assert SECRET_KEY not in message, message
    assert "auth=***" in message, message
    # The rest of the diagnostic survives redaction.
    assert "401" in message


@pytest.mark.asyncio
async def test_api_key_is_redacted_at_the_mcp_boundary():
    """FastMCP relays the message to the caller, so redaction must hold there."""
    from mcp.server.fastmcp.exceptions import ToolError as McpToolError
    from src import server as server_module

    with (
        patch.object(server_module.finviz_screener, "api_key", SECRET_KEY),
        patch.object(
            server_module.finviz_screener.session,
            "get",
            side_effect=requests.exceptions.HTTPError(LEAKY_HTTP_ERROR),
        ),
    ):
        with pytest.raises(McpToolError) as exc_info:
            await server_module.server.call_tool(
                "earnings_screener", {"earnings_date": "today_after"}
            )

    message = str(exc_info.value)
    assert SECRET_KEY not in message, message
    assert "auth=***" in message, message


def test_api_key_is_redacted_from_logs(caplog):
    """The export params (which carry ``auth``) are logged on every screen."""
    import logging

    client = FinvizScreener(api_key=SECRET_KEY)

    with caplog.at_level(logging.DEBUG, logger="src.finviz_client.base"):
        with patch.object(
            client.session,
            "get",
            side_effect=requests.exceptions.HTTPError(LEAKY_HTTP_ERROR),
        ):
            with pytest.raises(FinvizAPIError):
                client.screen_stocks({})

    assert SECRET_KEY not in caplog.text, caplog.text
    assert "'auth': '***'" in caplog.text


def test_api_key_never_appears_in_tool_output_text(monkeypatch):
    """earnings_winners used to append a "verify on Finviz" export URL with
    ``&auth=<key>`` — a guaranteed key disclosure in tool output (audit B25).
    Pin that no auth token appears in the formatted output."""
    from src.server import _format_earnings_winners_list
    from tests import factories

    monkeypatch.setenv("FINVIZ_API_KEY", SECRET_KEY)
    lines = _format_earnings_winners_list(
        [factories.make_stock_data()], {"earnings_date": "thisweek"}
    )
    text = "\n".join(lines)
    assert SECRET_KEY not in text
    assert "auth=" not in text


# --------------------------------------------------------------------------
# Screener wrappers must not re-swallow what the base client now raises.
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "method", ["earnings_winners_screener", "upcoming_earnings_screener"]
)
def test_screener_wrappers_propagate_api_errors(method):
    client = FinvizScreener(api_key="test-key")

    with patch.object(client.session, "get", return_value=_FakeResponse(HTML_BODY)):
        with pytest.raises(FinvizAPIError):
            getattr(client, method)()


def test_sec_filing_summary_propagates_api_errors():
    """The summary used to return ``{"ticker": ..., "error": ...}``-shaped or
    zeroed data for request failures; it now fails loudly."""
    client = FinvizSECFilingsClient(api_key="test-key")

    with patch.object(client.session, "get", return_value=_FakeResponse(HTML_BODY)):
        with pytest.raises(FinvizAPIError):
            client.get_filing_summary("AAPL")


# --------------------------------------------------------------------------
# The MCP boundary: FastMCP turns the raised error into a tool error, so the
# user sees the cause instead of "No stocks found".
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mcp_boundary_reports_the_failure_not_an_empty_result():
    from mcp.server.fastmcp.exceptions import ToolError as McpToolError
    from src import server as server_module

    # The module-level client is built at import time from the environment,
    # which may have no key in CI; pin one so the request path is reached.
    with (
        patch.object(server_module.finviz_screener, "api_key", "test-key"),
        patch.object(
            server_module.finviz_screener.session,
            "get",
            return_value=_FakeResponse(HTML_BODY),
        ),
    ):
        with pytest.raises(McpToolError) as exc_info:
            await server_module.server.call_tool(
                "earnings_screener", {"earnings_date": "today_after"}
            )

    message = str(exc_info.value)
    assert "HTML instead of CSV" in message, message
    assert "No stocks found" not in message


# --------------------------------------------------------------------------
# B8 — stdout is the MCP stdio JSON-RPC channel.
# --------------------------------------------------------------------------


def test_importing_the_server_writes_nothing_to_stdout():
    result = subprocess.run(
        [sys.executable, "-c", "import src.server"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )

    assert result.stdout == "", f"stdout polluted on import: {result.stdout!r}"


def test_tool_invocation_writes_nothing_to_stdout(capsys):
    """``dividend_growth_screener`` used to ``print("CLAUDE_DEBUG_MARKER: ...")``
    on every call with results, corrupting the JSON-RPC stream."""
    from src import server as server_module

    with patch.object(
        server_module.finviz_screener,
        "dividend_growth_screener",
        return_value=[factories.make_stock_data()],
    ):
        result = server_module.dividend_growth_screener()

    captured = capsys.readouterr()
    assert captured.out == "", f"stdout polluted: {captured.out!r}"
    # Sanity: the tool still produced its normal payload.
    assert "Dividend Growth Screening Results" in result[0].text
