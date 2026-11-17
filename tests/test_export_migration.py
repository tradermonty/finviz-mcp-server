"""Offline product routing and CSV contracts for the December export migration."""

import csv
import io
from unittest.mock import Mock

import pandas as pd
import pytest
import requests

from src.finviz_client.base import FinvizClient, FinvizDataError
from src.finviz_client.screener import FinvizScreener

STOCK_HEADERS = ["Ticker", "Company", "Price", "Sector", "Industry"]
ETF_HEADERS = [
    "Ticker",
    "Company",
    "Price",
    "Security Type",
    "Assets Under Management",
    "Net Expense Ratio",
]
STOCK_ROW = ["AAPL", "Synthetic Stock", "100", "Technology", "Software"]
ETF_ROW = [
    "SPY",
    "Synthetic Fund",
    "500",
    "Exchange Traded Fund",
    "1000000000",
    "0.09%",
]


def csv_response(headers, rows=()):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(rows)
    response = requests.Response()
    response.status_code = 200
    response._content = output.getvalue().encode()
    response.encoding = "utf-8"
    return response


@pytest.fixture
def client(monkeypatch):
    client = FinvizScreener(api_key="synthetic-export-key")
    client.rate_limit_delay = 0
    monkeypatch.setattr("src.finviz_client.base.time.sleep", lambda _: None)
    return client


def test_stock_request_preserves_filters_and_sort(client):
    client.session.get = Mock(return_value=csv_response(STOCK_HEADERS, [STOCK_ROW]))
    expected = client._convert_filters_to_finviz(client._build_volume_surge_filters())
    assert client.volume_surge_screener()[0].ticker == "AAPL"
    request = client.session.get.call_args
    assert request.args[0] == "https://elite.finviz.com/export/screener"
    params = request.kwargs["params"]
    assert params["type"] == "stocks"
    assert params["f"] == expected["f"]
    assert params["o"] == expected["o"]
    assert params["c"] == client.SCREENER_COLUMNS


def test_etf_request_ranking_and_thresholds(client):
    smaller = ["SMALL", "Small Fund", "50", "Exchange Traded Fund", "100", "0.02%"]
    client.session.get = Mock(
        return_value=csv_response(ETF_HEADERS, [smaller, ETF_ROW])
    )
    result = client.etf_screener()
    assert [r.ticker for r in result] == ["SPY", "SMALL"]
    assert result[0].aum == 1000000000
    assert result[0].net_expense_ratio == 0.09
    assert client.session.get.call_args.kwargs["params"]["type"] == "etf"
    assert client.session.get.call_args.kwargs["params"]["c"] == client.ETF_COLUMNS
    assert [
        r.ticker for r in client.etf_screener(sort_by="expense_ratio", sort_order="asc")
    ] == ["SMALL", "SPY"]
    assert [r.ticker for r in client.etf_screener(min_aum=1000)] == ["SPY"]
    assert [r.ticker for r in client.etf_screener(max_expense_ratio=0.03)] == ["SMALL"]


@pytest.mark.parametrize(
    "product,headers,row",
    [("stocks", STOCK_HEADERS, STOCK_ROW), ("etf", ETF_HEADERS, ETF_ROW)],
)
def test_reordered_columns_and_valid_empty(client, product, headers, row):
    client.session.get = Mock(return_value=csv_response(headers[::-1], [row[::-1]]))
    assert client.screen_stocks({"instrument_type": product})[0].ticker == row[0]
    client.session.get.return_value = csv_response(headers)
    assert client.screen_stocks({"instrument_type": product}) == []


@pytest.mark.parametrize(
    "headers,rows",
    [
        (STOCK_HEADERS, [STOCK_ROW]),
        (ETF_HEADERS[:-1], [ETF_ROW[:-1]]),
        (ETF_HEADERS + ["Ticker"], [ETF_ROW + ["SPY"]]),
        (ETF_HEADERS, [ETF_ROW[:3] + ["Common Stock"] + ETF_ROW[4:]]),
    ],
)
def test_wrong_product_or_missing_etf_columns_fails(client, headers, rows):
    client.session.get = Mock(return_value=csv_response(headers, rows))
    with pytest.raises(FinvizDataError):
        client.etf_screener()


def test_generic_and_custom_screens_are_stock_only(client):
    client.session.get = Mock(return_value=csv_response(STOCK_HEADERS, [STOCK_ROW]))
    client.screen_stocks({})
    assert client.session.get.call_args.kwargs["params"]["type"] == "stocks"
    client.screen_stocks_raw("cap_large", order="-volume")
    assert client.session.get.call_args.kwargs["params"]["type"] == "stocks"
    assert client.session.get.call_args.kwargs["params"]["o"] == "-volume"
    with pytest.raises(FinvizDataError, match="stock-only"):
        client.screen_stocks_raw("ind_exchangetradedfund")


def route_mixed(client):
    def get(url, params, **kwargs):
        assert url == client.EXPORT_URL
        assert params["c"]
        if params["type"] == "stocks":
            return csv_response(
                STOCK_HEADERS, [STOCK_ROW] if "AAPL" in params["t"] else []
            )
        assert params["t"] == "SPY"
        return csv_response(ETF_HEADERS, [ETF_ROW])

    client.session.get = Mock(side_effect=get)


def test_single_fundamentals_stock_and_etf(client):
    route_mixed(client)
    assert client.get_stock_fundamentals("AAPL", ["price"])["price"] == 100
    assert client.session.get.call_count == 1
    assert client.get_stock_fundamentals("SPY", ["price"])["price"] == 500
    assert client.session.get.call_count == 3


def test_mixed_fundamentals_preserve_order_and_query_only_unresolved(client):
    route_mixed(client)
    results = client.get_multiple_stocks_fundamentals(
        ["SPY", "AAPL"], ["ticker", "price"]
    )
    assert [r["ticker"] for r in results] == ["SPY", "AAPL"]
    assert [r["price"] for r in results] == [500, 100]
    assert client.session.get.call_count == 2
    assert client.session.get.call_args_list[0].kwargs["params"]["t"] == "SPY,AAPL"
    assert client.session.get.call_args_list[1].kwargs["params"]["t"] == "SPY"


def test_fundamentals_reject_unrequested_symbols(client):
    client.session.get = Mock(return_value=csv_response(STOCK_HEADERS, [STOCK_ROW]))
    with pytest.raises(FinvizDataError, match="unrequested"):
        client.get_stock_fundamentals("MSFT")


def test_other_export_endpoints_are_not_rerouted(client):
    client.session.get = Mock(return_value=csv_response(["Title", "Url"]))
    for url in (
        client.NEWS_EXPORT_URL,
        client.GROUPS_EXPORT_URL,
        client.QUOTE_EXPORT_URL,
    ):
        client._fetch_csv_from_url(url, {})
        request = client.session.get.call_args
        assert request.args[0] == url
        assert "type" not in request.kwargs["params"]


def test_missing_and_duplicate_tickers_fail():
    for rows in ([STOCK_ROW, STOCK_ROW], [[None] + STOCK_ROW[1:]]):
        response = csv_response(STOCK_HEADERS, rows)
        with pytest.raises(FinvizDataError):
            FinvizClient._read_screener_csv(response.text, "stocks")


def test_closed_end_funds_do_not_break_or_enter_etf_ranking(client):
    cef = ["CLOSED", "Synthetic CEF", "30", "Closed-End Fund - Debt", "-", "-"]
    client.session.get = Mock(return_value=csv_response(ETF_HEADERS, [cef, ETF_ROW]))
    assert [r.ticker for r in client.etf_screener()] == ["SPY"]


def test_malformed_csv_row_does_not_become_a_success(client):
    response = csv_response(STOCK_HEADERS, [STOCK_ROW + ["extra value"]])
    client.session.get = Mock(return_value=response)
    with pytest.raises(FinvizDataError, match="malformed"):
        client.screen_stocks({})


def test_missing_etf_values_are_excluded_with_a_warning(client, caplog):
    incomplete = ["GAP", "Missing data", "20", "Exchange Traded Fund", "-", "-"]
    client.session.get = Mock(
        return_value=csv_response(ETF_HEADERS, [incomplete, ETF_ROW])
    )
    assert [r.ticker for r in client.etf_screener()] == ["SPY"]
    assert "missing/invalid" in caplog.text
    assert "excluded from ETF ranking" in caplog.text
