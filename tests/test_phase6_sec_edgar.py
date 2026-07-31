"""Phase 6: the SEC / EDGAR tools must filter, convert, and count honestly.

Findings covered (AUDIT_FINDINGS.md section E):

* E1/E15 — ``M/D/YYYY`` dates never parsed, so ``days_back`` filtered nothing
  and every row logged a warning.
* E3 — EDGAR ``max_count`` applied before the form/date filters.
* E4 — raw inline-XBRL markup returned as "content".
* E5 — ``company_tickers.json`` re-downloaded on every CIK lookup.
* E6 — batch tool fetched 20k chars per document and rendered 500.
* E7 — exact-match form lists (no amendments, 11-K as "insider").
* E8 — only ``filing_date`` converted to the endpoint's camelCase ``o=``.
* E9 — filing summary counted a 100-row slice and called it the period total.
* E10/E11 — every XBRL unit rendered as USD; durations indistinguishable.
* E12 — truncation applied twice, marker chopped, length mis-reported.
* E13 — ticker regex rejected ``BRK.B``.
* E14 — placeholder ``contact@example.com`` User-Agent default.

Fixture: ``tests/fixtures/sec_latest_filings_aapl.csv`` (1,060 rows, all forms,
``M/D/YYYY`` dates spanning 2014-12-29 … 2026-07-30).
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src import server
from src.finviz_client import edgar_client as edgar_module
from src.finviz_client.edgar_client import EdgarAPIClient, html_to_text
from src.finviz_client.sec_filings import (
    FinvizSECFilingsClient,
    form_matches,
    matches_any_form,
)
from src.utils.validators import normalize_ticker, validate_ticker

FIXTURE = Path(__file__).parent / "fixtures" / "sec_latest_filings_aapl.csv"

# The newest filing date in the fixture is 2026-07-30; every windowed
# assertion below pins "now" so the expected counts stay stable.
FIXTURE_NOW = datetime(2026, 7, 31)


@pytest.fixture
def sec_client():
    return FinvizSECFilingsClient(api_key="test-key")


@pytest.fixture
def fixture_csv():
    return FIXTURE.read_text()


@pytest.fixture
def fixture_filings(sec_client, fixture_csv):
    return sec_client._parse_sec_filings_csv(fixture_csv, "AAPL")


class _FakeResponse:
    def __init__(self, text, headers=None):
        self.text = text
        self.status_code = 200
        self.headers = headers or {}

    def raise_for_status(self):
        return None

    def json(self):
        import json

        return json.loads(self.text)


# ---------------------------------------------------------------------------
# E1/E15 — date parsing and the days_back window
# ---------------------------------------------------------------------------


def test_parse_date_reads_the_format_finviz_actually_sends(sec_client):
    # GROUND_TRUTH.md: latest-filings dates are M/D/YYYY, not %m/%d/%y.
    assert sec_client._parse_date("7/30/2026") == datetime(2026, 7, 30)
    assert sec_client._parse_date("12/1/2025") == datetime(2025, 12, 1)
    assert sec_client._parse_date("2026-07-30") == datetime(2026, 7, 30)


def test_parse_date_returns_none_instead_of_now(sec_client):
    # The old fallback returned datetime.now(), which made every unparseable
    # row look like today's filing and pass any window.
    assert sec_client._parse_date("") is None
    assert sec_client._parse_date("not a date") is None
    assert sec_client._parse_date(None) is None


def test_fixture_dates_all_parse(fixture_filings, sec_client):
    assert len(fixture_filings) == 1060
    assert all(sec_client._parse_date(f.filing_date) for f in fixture_filings)


@pytest.mark.parametrize(
    "days_back,expected",
    [(30, 1), (90, 10), (365, 80), (3650, 863)],
)
def test_days_back_actually_filters_the_fixture(
    sec_client, fixture_filings, days_back, expected
):
    kept = sec_client.filter_by_days_back(fixture_filings, days_back, now=FIXTURE_NOW)
    assert len(kept) == expected
    assert len(kept) < len(fixture_filings)


def test_days_back_window_contains_only_in_window_dates(sec_client, fixture_filings):
    kept = sec_client.filter_by_days_back(fixture_filings, 365, now=FIXTURE_NOW)
    cutoff = FIXTURE_NOW.timestamp() - 365 * 86400
    for filing in kept:
        assert sec_client._parse_date(filing.filing_date).timestamp() >= cutoff


def test_unparseable_dates_are_dropped_and_logged_once(sec_client, caplog):
    from src.models import SECFilingData

    def mk(date_str):
        return SECFilingData(
            ticker="AAPL",
            filing_date=date_str,
            report_date=date_str,
            form="8-K",
            description="d",
            filing_url="u",
            document_url="u",
        )

    filings = [mk("7/30/2026"), mk("garbage"), mk(""), mk("7/29/2026")]

    with caplog.at_level("WARNING"):
        kept = sec_client.filter_by_days_back(filings, 30, now=FIXTURE_NOW)

    assert len(kept) == 2  # unparseable rows dropped, not defaulted to now()
    warnings = [r for r in caplog.records if r.levelname == "WARNING"]
    assert len(warnings) == 1  # one aggregate line, not one per row
    assert "2" in warnings[0].getMessage()


def test_days_back_filters_end_to_end(sec_client, fixture_csv):
    with patch.object(
        sec_client.session, "get", return_value=_FakeResponse(fixture_csv)
    ):
        everything = sec_client.get_sec_filings("AAPL", days_back=0, max_results=0)
        windowed = sec_client.get_sec_filings("AAPL", days_back=365, max_results=0)

    assert len(everything) == 1060
    assert 0 < len(windowed) < len(everything)


# ---------------------------------------------------------------------------
# E7 — form matching (amendments in, 424B2 out, 11-K dropped)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "form,wanted,expected",
    [
        ("10-K", "10-K", True),
        ("10-K/A", "10-K", True),  # amendments must match
        ("4", "4", True),
        ("4/A", "4", True),
        ("424B2", "4", False),  # naive startswith would match this
        ("497", "4", False),
        ("SC 13G/A", "SC 13G", True),
        ("8-K/A", "8-K", True),
        ("10-Q", "10-K", False),
    ],
)
def test_form_matches_covers_amendments_without_prefix_collisions(
    form, wanted, expected
):
    assert form_matches(form, wanted) is expected


def test_insider_forms_include_144_and_exclude_11k():
    forms = FinvizSECFilingsClient.INSIDER_FORMS
    assert forms == ["3", "4", "5", "144"]
    # 11-K is an employee benefit plan annual report, not insider activity.
    assert not matches_any_form("11-K", forms)
    assert matches_any_form("144/A", forms)


def test_major_forms_cover_foreign_issuers():
    forms = FinvizSECFilingsClient.MAJOR_FORMS
    assert "20-F" in forms and "6-K" in forms
    assert matches_any_form("10-K/A", forms)
    assert not matches_any_form("4", forms)


def test_form_filter_selects_amendments_from_the_fixture(sec_client, fixture_csv):
    with patch.object(
        sec_client.session, "get", return_value=_FakeResponse(fixture_csv)
    ):
        sc13g = sec_client.get_sec_filings(
            "AAPL", form_types=["SC 13G"], days_back=0, max_results=0
        )
        form4 = sec_client.get_sec_filings(
            "AAPL", form_types=["4"], days_back=0, max_results=0
        )

    # 2 x "SC 13G" + 23 x "SC 13G/A" + the 2025+ "SCHEDULE 13G" spelling
    # (1 x "SCHEDULE 13G" + 2 x "SCHEDULE 13G/A") = 28
    assert len(sc13g) == 28
    # 621 x "4" + 1 x "4/A"; the 52 "424B2" rows must not leak in
    assert len(form4) == 622
    assert not any(f.form.startswith("424") for f in form4)


# ---------------------------------------------------------------------------
# E8 — sort parameter (probed 2026-07-31: -reportDate and -form are honored)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "sort_by,expected",
    [
        ("filing_date", "-filingDate"),
        ("report_date", "-reportDate"),
        ("form", "-form"),
    ],
)
def test_sort_by_is_converted_to_the_camelcase_the_endpoint_honors(
    sec_client, fixture_csv, sort_by, expected
):
    with patch.object(
        sec_client.session, "get", return_value=_FakeResponse(fixture_csv)
    ) as mock_get:
        sec_client.get_sec_filings("AAPL", sort_by=sort_by, days_back=0)

    assert mock_get.call_args.kwargs["params"]["o"] == expected


def test_unsupported_sort_by_is_rejected_instead_of_sent(sec_client):
    with pytest.raises(ValueError, match="sort_by"):
        sec_client.get_sec_filings("AAPL", sort_by="market_cap")


# ---------------------------------------------------------------------------
# E9 — the summary counts every filing in the window
# ---------------------------------------------------------------------------


def test_summary_counts_the_full_filtered_set_not_a_100_row_slice(
    sec_client, fixture_csv
):
    with patch.object(
        sec_client.session, "get", return_value=_FakeResponse(fixture_csv)
    ):
        summary = sec_client.get_filing_summary("AAPL", days_back=0)

    assert summary["total_filings"] == 1060  # used to be capped at 100
    assert sum(summary["forms"].values()) == summary["total_filings"]


def test_summary_tool_percentages_sum_over_the_full_set(sec_client, fixture_csv):
    with patch.object(
        sec_client.session, "get", return_value=_FakeResponse(fixture_csv)
    ):
        with patch("src.server.finviz_sec", sec_client):
            text = server.get_sec_filing_summary("AAPL", days_back=0)[0].text

    assert "Total Filings: 1,060" in text or "Total Filings: 1060" in text
    # 621/1060 = 58.6% — a percentage over the real denominator, not over 100.
    assert "58.6%" in text
    # Display cap is labeled, never presented as the total.
    assert "more form types" in text


# ---------------------------------------------------------------------------
# E13 — ticker regex
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "ticker", ["A", "aapl", "AAPL", "MSFT", "BRK.B", "BRK-B", "BF-B", "BFS-PD"]
)
def test_validate_ticker_accepts_class_share_tickers(ticker):
    assert validate_ticker(ticker) is True


@pytest.mark.parametrize(
    "ticker",
    ["", " ", "123", "TICKER", "TOOLONGTICKERYMBOL", "IN-VALID", "in valid", "AAPL$"],
)
def test_validate_ticker_still_rejects_garbage(ticker):
    assert validate_ticker(ticker) is False


def test_normalize_ticker_matches_edgar_spelling():
    # SEC company_tickers.json and Finviz both spell class shares with "-".
    assert normalize_ticker("brk.b") == "BRK-B"
    assert normalize_ticker("BRK-B") == "BRK-B"


# ---------------------------------------------------------------------------
# E4 — HTML → text conversion
# ---------------------------------------------------------------------------


INLINE_XBRL = """<?xml version='1.0' encoding='ASCII'?>
<html xmlns:ix="http://www.xbrl.org/2013/inlineXBRL">
<head><style>body {font-family: serif;}</style>
<script>var x = 1;</script></head>
<body>
<ix:header><ix:hidden>us-gaap:Assets 12345</ix:hidden></ix:header>
<div style="display:none">HIDDEN FACT BLOCK</div>
<p>Item&nbsp;1. Business</p>
<p>Apple Inc. designs &amp; sells smartphones.</p>
</body></html>"""


def test_html_to_text_strips_markup_and_unescapes_entities():
    text = html_to_text(INLINE_XBRL)

    assert "Item 1. Business" in text
    assert "designs & sells smartphones" in text  # entity unescaped
    assert "font-family" not in text  # style dropped
    assert "var x" not in text  # script dropped
    assert "us-gaap:Assets" not in text  # ix:header/ix:hidden dropped
    assert "HIDDEN FACT BLOCK" not in text  # display:none dropped
    assert "<p>" not in text and "</html>" not in text


def _edgar_client_with_cik(monkeypatch, doc_body, headers=None):
    client = EdgarAPIClient(user_agent="pytest test@example.invalid")
    client._cik_cache = {"AAPL": "0000320193"}
    monkeypatch.setattr(edgar_module.time, "sleep", lambda *_: None)
    client.session.get = MagicMock(return_value=_FakeResponse(doc_body, headers))
    return client


def test_document_content_is_converted_before_truncation(monkeypatch):
    client = _edgar_client_with_cik(monkeypatch, INLINE_XBRL)

    result = client.get_filing_document_content(
        ticker="AAPL",
        accession_number="0000320193-25-000079",
        primary_document="aapl-20250927.htm",
        max_length=20,
    )

    meta = result["metadata"]
    assert meta["content_type"] == "html"
    # Truncation happens once, in the client, and the marker survives.
    assert result["content"].endswith(edgar_module.TRUNCATION_MARKER)
    assert result["content"].startswith("Item 1. Business"[:20])
    assert meta["truncated"] is True
    # Both lengths are reported: full converted text and what was returned.
    assert meta["full_content_length"] > meta["content_length"] - len(
        edgar_module.TRUNCATION_MARKER
    )
    assert meta["content_length"] == len(result["content"])
    assert meta["raw_content_length"] == len(INLINE_XBRL)


def test_plain_text_filings_skip_conversion(monkeypatch):
    body = "<not really html>\nPLAIN TEXT FILING BODY\n"
    client = _edgar_client_with_cik(
        monkeypatch, body, headers={"Content-Type": "text/plain"}
    )

    result = client.get_filing_document_content(
        ticker="AAPL",
        accession_number="0000320193-25-000079",
        primary_document="0000320193-25-000079.txt",
        max_length=0,
    )

    assert result["metadata"]["content_type"] == "text"
    assert result["content"] == body
    assert result["metadata"]["truncated"] is False


def test_filing_content_tool_reports_both_lengths_and_keeps_the_marker(monkeypatch):
    client = _edgar_client_with_cik(monkeypatch, INLINE_XBRL)

    with patch("src.server._get_edgar_client", return_value=client):
        text = server.get_edgar_filing_content(
            ticker="AAPL",
            accession_number="0000320193-25-000079",
            primary_document="aapl-20250927.htm",
            max_length=20,
        )[0].text

    assert "Content truncated due to length limit" in text  # marker not chopped
    assert "Document Length:" in text and "Returned:" in text
    assert "Content Type: html" in text


# ---------------------------------------------------------------------------
# E5 — CIK lookup cache
# ---------------------------------------------------------------------------


COMPANY_TICKERS_JSON = (
    '{"0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},'
    ' "1": {"cik_str": 1067983, "ticker": "BRK-B", "title": "Berkshire"}}'
)


def test_company_tickers_json_is_downloaded_once_per_client(monkeypatch):
    client = EdgarAPIClient(user_agent="pytest test@example.invalid")
    monkeypatch.setattr(edgar_module.time, "sleep", lambda *_: None)
    client.session.get = MagicMock(return_value=_FakeResponse(COMPANY_TICKERS_JSON))

    ciks = [client._get_cik_from_ticker(t) for t in ("AAPL", "AAPL", "BRK-B", "AAPL")]

    assert ciks == ["0000320193", "0000320193", "0001067983", "0000320193"]
    assert client.session.get.call_count == 1  # was one ~800KB download each


def test_batch_of_filings_downloads_the_ticker_map_once(monkeypatch):
    client = EdgarAPIClient(user_agent="pytest test@example.invalid")
    monkeypatch.setattr(edgar_module.time, "sleep", lambda *_: None)

    def fake_get(url, timeout=30):
        if "company_tickers" in url:
            return _FakeResponse(COMPANY_TICKERS_JSON)
        return _FakeResponse("<html><body>DOC BODY</body></html>")

    client.session.get = MagicMock(side_effect=fake_get)

    results = client.get_multiple_filing_contents(
        [
            {
                "ticker": "AAPL",
                "accession_number": f"0000320193-25-00007{i}",
                "primary_document": f"doc{i}.htm",
            }
            for i in range(5)
        ]
    )

    assert len(results) == 5
    ticker_map_calls = [
        c for c in client.session.get.call_args_list if "company_tickers" in c.args[0]
    ]
    assert len(ticker_map_calls) == 1


def test_dotted_ticker_resolves_through_edgars_hyphen_spelling(monkeypatch):
    client = EdgarAPIClient(user_agent="pytest test@example.invalid")
    monkeypatch.setattr(edgar_module.time, "sleep", lambda *_: None)
    client.session.get = MagicMock(return_value=_FakeResponse(COMPANY_TICKERS_JSON))

    assert client._get_cik_from_ticker("BRK.B") == "0001067983"


# ---------------------------------------------------------------------------
# E3 — EDGAR filters run before the cap
# ---------------------------------------------------------------------------


def _synthetic_submissions():
    """60 Form 4s, then a 10-K at index 60 — the shape that used to hide it."""
    forms = ["4"] * 60 + ["10-K"] + ["8-K"] * 10
    n = len(forms)
    return {
        "filings": {
            "recent": {
                "form": forms,
                "filingDate": ["2026-01-15"] * n,
                "reportDate": ["2026-01-01"] * n,
                "accessionNumber": [f"0000320193-26-{i:06d}" for i in range(n)],
                "primaryDocument": [f"doc{i}.htm" for i in range(n)],
                "primaryDocDescription": ["desc"] * n,
            },
            "files": [],
        }
    }


def _edgar_client_with_submissions(monkeypatch, submissions):
    client = EdgarAPIClient(user_agent="pytest test@example.invalid")
    client._cik_cache = {"AAPL": "0000320193"}
    monkeypatch.setattr(edgar_module.time, "sleep", lambda *_: None)
    client.client = MagicMock()
    client.client.get_submissions = MagicMock(return_value=submissions)
    return client


def test_form_filter_is_applied_before_max_count(monkeypatch):
    client = _edgar_client_with_submissions(monkeypatch, _synthetic_submissions())

    filings = client.get_company_filings(
        ticker="AAPL", form_types=["10-K"], max_count=50
    )

    # The 10-K sits at index 60; capping first returned nothing at all.
    assert len(filings) == 1
    assert filings[0]["form"] == "10-K"


def test_max_count_caps_the_filtered_result(monkeypatch):
    client = _edgar_client_with_submissions(monkeypatch, _synthetic_submissions())

    filings = client.get_company_filings(ticker="AAPL", form_types=["4"], max_count=5)

    assert len(filings) == 5
    assert {f["form"] for f in filings} == {"4"}


def test_date_filter_is_applied_before_max_count(monkeypatch):
    submissions = _synthetic_submissions()
    submissions["filings"]["recent"]["filingDate"] = ["2020-01-15"] * 60 + [
        "2026-01-15"
    ] * 11
    client = _edgar_client_with_submissions(monkeypatch, submissions)

    filings = client.get_company_filings(
        ticker="AAPL", date_from="2025-01-01", max_count=50
    )

    assert len(filings) == 11
    assert all(f["filing_date"] >= "2025-01-01" for f in filings)


def test_submissions_history_is_not_paginated_by_default(monkeypatch):
    client = _edgar_client_with_submissions(monkeypatch, _synthetic_submissions())

    client.get_company_filings(ticker="AAPL")
    assert client.client.get_submissions.call_args.kwargs["handle_pagination"] is False

    client.get_company_filings(ticker="AAPL", include_full_history=True)
    assert client.client.get_submissions.call_args.kwargs["handle_pagination"] is True


# ---------------------------------------------------------------------------
# E6 — the batch tool renders what it fetched
# ---------------------------------------------------------------------------


def test_batch_tool_renders_the_fetched_content(monkeypatch):
    body = "<html><body><p>" + ("word " * 300) + "</p></body></html>"
    client = _edgar_client_with_cik(monkeypatch, body)

    with patch("src.server._get_edgar_client", return_value=client):
        text = server.get_multiple_edgar_filing_contents(
            ticker="AAPL",
            filings_data=[
                {
                    "accession_number": "0000320193-25-000079",
                    "primary_document": "doc.htm",
                }
            ],
        )[0].text

    # Old behavior: fetch 20,000 chars, print 500.
    assert text.count("word") > 250
    assert "chars shown" in text


def test_batch_tool_preview_length_is_honored_and_labeled(monkeypatch):
    body = "<html><body><p>" + ("word " * 300) + "</p></body></html>"
    client = _edgar_client_with_cik(monkeypatch, body)

    with patch("src.server._get_edgar_client", return_value=client):
        text = server.get_multiple_edgar_filing_contents(
            ticker="AAPL",
            filings_data=[
                {
                    "accession_number": "0000320193-25-000079",
                    "primary_document": "doc.htm",
                }
            ],
            preview_length=100,
        )[0].text

    assert "more characters" in text
    assert "get_edgar_filing_content" in text


# ---------------------------------------------------------------------------
# E10/E11 — XBRL units and period labeling
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value,unit,expected",
    [
        (3_200_000_000, "USD", "$3.20B"),
        (-3_200_000_000, "USD", "-$3.20B"),  # not "$-3,200,000,000.00"
        (4_500_000, "USD", "$4.50M"),
        (250.0, "USD", "$250.00"),
        (15_204_137_000, "shares", "15,204,137,000"),  # no dollar sign, no "B"
        (-1_000, "shares", "-1,000"),
        (6.6, "USD/shares", "$6.60"),
        (-0.35, "USD/shares", "-$0.35"),
        (0.25, "pure", "0.25"),
        (0, "USD", "$0.00"),
        (0, "shares", "0"),
    ],
)
def test_xbrl_values_are_formatted_per_unit(value, unit, expected):
    assert server._format_xbrl_value(value, unit) == expected


def test_period_buckets_separate_quarterly_from_annual():
    quarterly = {"start": "2025-06-29", "end": "2025-09-27"}
    annual = {"start": "2024-09-29", "end": "2025-09-27"}
    instant = {"end": "2025-09-27"}

    assert "Quarterly" in server._period_bucket(quarterly)
    assert "Annual" in server._period_bucket(annual)
    assert "Instant" in server._period_bucket(instant)


def test_period_description_renders_start_end_and_fiscal_labels():
    described = server._describe_period(
        {
            "start": "2024-09-29",
            "end": "2025-09-27",
            "fy": 2025,
            "fp": "FY",
            "frame": "CY2025",
        }
    )
    assert "2024-09-29" in described and "2025-09-27" in described
    assert "12m" in described
    assert "FY2025 FY" in described
    assert "CY2025" in described

    instant = server._describe_period({"end": "2025-09-27"})
    assert instant.startswith("as of 2025-09-27")


def test_repeated_frames_are_deduped():
    entries = [
        {"start": "2024-09-29", "end": "2025-09-27", "val": 100, "filed": "2025-10-31"},
        {"start": "2024-09-29", "end": "2025-09-27", "val": 100, "filed": "2026-01-30"},
        {"start": "2025-06-29", "end": "2025-09-27", "val": 25, "filed": "2025-10-31"},
    ]

    deduped = server._dedupe_concept_entries(entries)

    assert len(deduped) == 2
    annual = [e for e in deduped if e["val"] == 100][0]
    assert annual["_report_count"] == 2
    assert annual["filed"] == "2026-01-30"  # most recent filing kept


def test_concept_tool_labels_units_and_periods(monkeypatch):
    client = EdgarAPIClient(user_agent="pytest test@example.invalid")
    client.get_company_concept = MagicMock(
        return_value={
            "cik": 320193,
            "entityName": "Apple Inc.",
            "label": None,
            "description": None,
            "units": {
                "shares": [
                    {
                        "end": "2025-09-27",
                        "val": 15_204_137_000,
                        "form": "10-K",
                        "filed": "2025-10-31",
                        "fy": 2025,
                        "fp": "FY",
                    }
                ]
            },
        }
    )

    with patch("src.server._get_edgar_client", return_value=client):
        text = server.get_edgar_company_concept(
            ticker="AAPL", concept="CommonStockSharesOutstanding"
        )[0].text

    assert "15,204,137,000" in text
    assert "$15.20B" not in text  # shares are not dollars
    assert "None" not in text  # null label/description fall back
    assert "Instant" in text


def test_company_facts_tool_falls_back_to_label_for_null_descriptions(monkeypatch):
    client = EdgarAPIClient(user_agent="pytest test@example.invalid")
    client._cik_cache = {"AAPL": "0000320193"}
    client.client = MagicMock()
    client.client.get_company_facts = MagicMock(
        return_value={
            "cik": 320193,
            "entityName": "Apple Inc.",
            "facts": {
                "us-gaap": {
                    "Assets": {"label": "Assets", "description": None},
                    "Liabilities": {"label": None, "description": None},
                }
            },
        }
    )

    with patch("src.server._get_edgar_client", return_value=client):
        text = server.get_edgar_company_facts(ticker="AAPL")[0].text

    assert "Concept: None" not in text
    assert ": None" not in text
    assert "Assets" in text and "Liabilities" in text


# ---------------------------------------------------------------------------
# E14 — no placeholder User-Agent
# ---------------------------------------------------------------------------


def test_edgar_client_requires_an_explicit_user_agent():
    with pytest.raises(TypeError):
        EdgarAPIClient()  # type: ignore[call-arg]

    with pytest.raises(ValueError, match="user_agent"):
        EdgarAPIClient(user_agent="   ")


def test_user_agent_has_no_default_value():
    import inspect

    param = inspect.signature(EdgarAPIClient.__init__).parameters["user_agent"]
    assert param.default is inspect.Parameter.empty


def test_sec_rate_limit_guidance_is_defined_once():
    # SEC publishes ~10 requests/second; the constant is the single knob.
    assert 0 < edgar_module.SEC_MIN_REQUEST_INTERVAL_SECONDS <= 0.2


# ---------------------------------------------------------------------------
# Window labeling: "Last 0 days" is not a window
# ---------------------------------------------------------------------------


def test_sec_filings_tool_labels_the_window_honestly(sec_client, fixture_csv):
    with patch.object(
        sec_client.session, "get", return_value=_FakeResponse(fixture_csv)
    ):
        with patch("src.server.finviz_sec", sec_client):
            unbounded = server.get_sec_filings(
                "AAPL", form_types=["10-K"], days_back=0, max_results=0
            )[0].text
            windowed = server.get_sec_filings("AAPL", days_back=365, max_results=0)[
                0
            ].text

    assert "All available history" in unbounded
    assert "Last 0 days" not in unbounded
    assert "Results: 11 filings" in unbounded  # every 10-K in the fixture
    # The windowed count is relative to the real "now", so pin only that the
    # window is applied and labeled (exact counts are pinned against a fixed
    # reference in test_days_back_actually_filters_the_fixture).
    assert "Last 365 days" in windowed
    windowed_count = int(windowed.split("Results: ")[1].split(" ")[0])
    assert 0 < windowed_count < 1060


def test_error_policy_is_not_regressed(sec_client):
    """E2 (fixed in Phase 3): a failed request must not read as "no filings"."""
    from src.utils.exceptions import FinvizAPIError

    with patch.object(
        sec_client.session,
        "get",
        return_value=_FakeResponse("<html><body>login</body></html>"),
    ):
        with pytest.raises(FinvizAPIError):
            sec_client.get_sec_filings("AAPL")


# ---------------------------------------------------------------------------
# Review fix 1 — Finviz changed the ownership-form spelling mid-history
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "form,wanted,expected",
    [
        ("SCHEDULE 13G", "SC 13G", True),  # 2025+ spelling
        ("SCHEDULE 13G/A", "SC 13G", True),
        ("SC 13G/A", "SCHEDULE 13G", True),  # symmetric
        ("SCHEDULE 13D", "SC 13D", True),
        ("SCHEDULE 13G", "SC 13D", False),
        ("SCHEDULE 14A", "SC 13G", False),
    ],
)
def test_ownership_form_spelling_is_normalized(form, wanted, expected):
    assert form_matches(form, wanted) is expected


def test_major_filings_include_the_2025_plus_ownership_spelling(
    sec_client, fixture_csv
):
    with patch.object(
        sec_client.session, "get", return_value=_FakeResponse(fixture_csv)
    ):
        majors = sec_client.get_sec_filings(
            "AAPL",
            form_types=FinvizSECFilingsClient.MAJOR_FORMS,
            days_back=0,
            max_results=0,
        )

    forms = {f.form for f in majors}
    # The header advertises "SC 13G/D (Ownership)"; the fixture's current-era
    # rows are spelled "SCHEDULE 13G" and used to be filtered out entirely.
    assert "SCHEDULE 13G" in forms
    assert "SCHEDULE 13G/A" in forms
    assert "SC 13G/A" in forms
    schedule_rows = [f for f in majors if f.form.startswith("SCHEDULE")]
    assert len(schedule_rows) == 3


# ---------------------------------------------------------------------------
# Review fix 2 — the widened ticker regex needs normalization at the Finviz
# request layer, not just on the SEC/EDGAR paths
# ---------------------------------------------------------------------------


def test_finviz_requests_normalize_dotted_tickers():
    from src.finviz_client.base import FinvizClient

    client = FinvizClient(api_key="test-key")
    csv_body = "Ticker,Company,Price\nBRK-B,Berkshire Hathaway,500\n"

    with patch.object(
        client.session, "get", return_value=_FakeResponse(csv_body)
    ) as mock_get:
        with patch("src.finviz_client.base.time.sleep", lambda *_: None):
            client.get_stock_fundamentals("BRK.B")

    # Finviz spells class shares BRK-B; "BRK.B" used to reach the API verbatim
    # and come back as "No data found" once the validator started accepting it.
    assert mock_get.call_args.kwargs["params"]["t"] == "BRK-B"


def test_ticker_param_normalization_handles_comma_lists():
    from src.utils.validators import normalize_ticker_param

    assert normalize_ticker_param("brk.b") == "BRK-B"
    assert normalize_ticker_param("brk.b,aapl") == "BRK-B,AAPL"
    assert normalize_ticker_param("AAPL") == "AAPL"


# ---------------------------------------------------------------------------
# Review fix 3 — EDGAR transport failures are failures, not "no filings"
# ---------------------------------------------------------------------------


def test_cik_map_download_failure_raises(monkeypatch):
    import requests as requests_module

    from src.utils.exceptions import EdgarAPIError

    client = EdgarAPIClient(user_agent="pytest test@example.invalid")
    monkeypatch.setattr(edgar_module.time, "sleep", lambda *_: None)
    client.session.get = MagicMock(
        side_effect=requests_module.exceptions.ConnectionError("no route")
    )

    with pytest.raises(EdgarAPIError):
        client.get_company_filings(ticker="AAPL")


def test_submissions_failure_raises_instead_of_empty_list(monkeypatch):
    from src.utils.exceptions import EdgarAPIError

    client = _edgar_client_with_submissions(monkeypatch, _synthetic_submissions())
    client.client.get_submissions = MagicMock(side_effect=RuntimeError("502 from SEC"))

    with pytest.raises(EdgarAPIError, match="submissions"):
        client.get_company_filings(ticker="AAPL")


def test_unknown_ticker_is_an_empty_result_not_an_error(monkeypatch):
    client = EdgarAPIClient(user_agent="pytest test@example.invalid")
    monkeypatch.setattr(edgar_module.time, "sleep", lambda *_: None)
    client.session.get = MagicMock(return_value=_FakeResponse(COMPANY_TICKERS_JSON))

    assert client.get_company_filings(ticker="ZZZZZ") == []


# ---------------------------------------------------------------------------
# Review fix 4 — days_back <= 0 means "no window" everywhere
# ---------------------------------------------------------------------------


def test_edgar_company_filings_treats_zero_days_back_as_unlimited(monkeypatch):
    client = _edgar_client_with_submissions(monkeypatch, _synthetic_submissions())
    captured = {}

    def capture(**kwargs):
        captured.update(kwargs)
        return []

    client.get_company_filings = capture

    with patch("src.server._get_edgar_client", return_value=client):
        text = server.get_edgar_company_filings(ticker="AAPL", days_back=0)[0].text

    assert captured["date_from"] is None  # was "today", i.e. today-only
    assert "All available history" in text


def test_edgar_company_filings_still_applies_a_positive_window(monkeypatch):
    client = _edgar_client_with_submissions(monkeypatch, _synthetic_submissions())
    captured = {}

    def capture(**kwargs):
        captured.update(kwargs)
        return []

    client.get_company_filings = capture

    with patch("src.server._get_edgar_client", return_value=client):
        text = server.get_edgar_company_filings(ticker="AAPL", days_back=365)[0].text

    assert captured["date_from"] is not None
    assert "365 days" in text
