"""
EDGAR API Client for SEC filings document content retrieval

This module provides functionality to retrieve SEC filing document content
using the official EDGAR API instead of web scraping.
"""

import html as html_module
import logging
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from sec_edgar_api import EdgarClient

from ..utils.exceptions import EdgarAPIError
from ..utils.validators import normalize_ticker, validate_ticker
from .sec_filings import matches_any_form

logger = logging.getLogger(__name__)

# SEC's published guidance for automated access is a maximum of ~10 requests per
# second per client (https://www.sec.gov/os/accessing-edgar-data). Every raw
# ``requests.Session`` call in this module sleeps at least this long before
# firing, which is the single place that policy is encoded. (``sec_edgar_api``
# rate-limits its own ``data.sec.gov`` calls internally.)
SEC_MIN_REQUEST_INTERVAL_SECONDS = 0.11

COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"

# Markup wrappers that carry no readable prose in an inline-XBRL filing: the
# ``ix:header``/``ix:hidden`` blocks at the top of a modern 10-K are hundreds of
# fact URIs, and script/style are code.
_NON_TEXT_TAGS = ("script", "style", "ix:header", "ix:hidden")

_WHITESPACE_RUN = re.compile(r"[ \t ]+")
_BLANK_LINES = re.compile(r"\n{3,}")
_TAG_RE = re.compile(r"<[^>]+>")
_SCRIPT_STYLE_RE = re.compile(r"<(script|style)\b.*?</\1>", re.IGNORECASE | re.DOTALL)
_BLOCK_BREAK_RE = re.compile(
    r"</?(p|div|br|tr|li|h[1-6]|table|section)\b[^>]*>", re.IGNORECASE
)

TRUNCATION_MARKER = "\n\n[Content truncated due to length limit]"


def _collapse_whitespace(text: str) -> str:
    text = _WHITESPACE_RUN.sub(" ", text)
    text = "\n".join(line.strip() for line in text.split("\n"))
    return _BLANK_LINES.sub("\n\n", text).strip()


def html_to_text(html: str) -> str:
    """Convert filing markup to readable text.

    A modern 10-K is inline XBRL: ~1.5 MB of markup for ~200 KB of prose, with
    the first tens of thousands of characters being ``<head>``/CSS/hidden XBRL
    facts. Returning ``response.text`` verbatim therefore returned no readable
    content at all within any sane length limit.

    Uses BeautifulSoup (a declared dependency) with the stdlib ``html.parser``;
    falls back to a regex tag-strip + entity unescape if bs4 is unavailable so
    the tool degrades instead of failing.
    """
    if not html:
        return ""

    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        for tag_name in _NON_TEXT_TAGS:
            for tag in soup.find_all(tag_name):
                tag.decompose()
        # Inline-XBRL hides its fact block with display:none rather than a
        # dedicated tag in some filers' documents.
        for tag in soup.find_all(style=True):
            style = str(tag.get("style", "")).replace(" ", "").lower()
            if "display:none" in style:
                tag.decompose()
        text = soup.get_text(separator="\n")
    except Exception as e:  # pragma: no cover - only when bs4 is missing/broken
        logger.warning(f"Falling back to regex HTML stripping: {e}")
        text = _SCRIPT_STYLE_RE.sub(" ", html)
        text = _BLOCK_BREAK_RE.sub("\n", text)
        text = _TAG_RE.sub(" ", text)
        text = html_module.unescape(text)

    return _collapse_whitespace(text)


def _looks_like_html(document_name: str, content_type_header: str, body: str) -> bool:
    """Decide whether a fetched filing document needs HTML→text conversion."""
    name = (document_name or "").lower()
    if name.endswith((".txt", ".json", ".csv")):
        return False
    if name.endswith((".htm", ".html", ".xhtml", ".xml")):
        return True
    header = (content_type_header or "").lower()
    if "html" in header or "xml" in header:
        return True
    return "<html" in body[:2000].lower()


class EdgarAPIClient:
    """EDGAR API client for retrieving SEC filing document content"""

    def __init__(self, user_agent: str):
        """
        Initialize EDGAR API client

        Args:
            user_agent: User agent string for SEC API requests. **Required** —
                SEC rejects/blocks anonymous or placeholder agents, and the old
                example.com default silently sent a fake contact address on
                every request. The server passes ``EDGAR_USER_AGENT``.

        Raises:
            ValueError: if no user agent is supplied.
        """
        if not user_agent or not str(user_agent).strip():
            raise ValueError(
                "EdgarAPIClient requires an explicit user_agent identifying you "
                "to SEC (e.g. 'Your Name your.email@example.com'). "
                "See https://www.sec.gov/os/accessing-edgar-data"
            )

        self.client = EdgarClient(user_agent=user_agent)
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
            }
        )
        # ticker -> CIK, built once per client instance (see _ticker_cik_map).
        self._cik_cache: Optional[Dict[str, str]] = None

    def _sec_get(self, url: str, timeout: int = 30) -> requests.Response:
        """GET an sec.gov URL, honoring SEC's ~10 req/s guidance."""
        time.sleep(SEC_MIN_REQUEST_INTERVAL_SECONDS)
        return self.session.get(url, timeout=timeout)

    def _ticker_cik_map(self) -> Dict[str, str]:
        """Return (and memoize) the ticker → zero-padded CIK map.

        ``company_tickers.json`` is ~800 KB and used to be re-downloaded on
        *every* lookup — ten times for a ten-filing batch. It is downloaded at
        most once per client instance; the ticker universe does not move within
        a session.
        """
        if self._cik_cache is not None:
            return self._cik_cache

        response = self._sec_get(COMPANY_TICKERS_URL, timeout=30)
        response.raise_for_status()
        data = response.json()

        mapping: Dict[str, str] = {}
        for entry in data.values():
            symbol = str(entry.get("ticker", "")).upper()
            if not symbol:
                continue
            mapping[symbol] = str(entry.get("cik_str", "")).zfill(10)

        self._cik_cache = mapping
        logger.info(f"Cached {len(mapping)} ticker→CIK entries from SEC")
        return mapping

    def _get_cik_from_ticker(self, ticker: str) -> Optional[str]:
        """Get CIK from ticker using SEC company tickers JSON (cached).

        EDGAR spells class shares with a hyphen (``BRK-B``), so a dotted
        ``BRK.B`` is normalized before lookup.

        Returns None only when the ticker genuinely is not in SEC's list.
        A failed *download* raises :class:`EdgarAPIError` — "SEC is
        unreachable" must not read as "unknown ticker"
        (GROUND_TRUTH.md house rule 3).
        """
        symbol = normalize_ticker(ticker)
        try:
            mapping = self._ticker_cik_map()
        except Exception as e:
            raise EdgarAPIError(
                f"Could not download SEC's ticker→CIK map "
                f"({COMPANY_TICKERS_URL}): {e}"
            ) from e

        cik = mapping.get(symbol)
        if cik:
            logger.debug(f"Found CIK {cik} for ticker {symbol}")
            return cik

        logger.warning(f"CIK not found for ticker {ticker}")
        return None

    def get_company_filings(
        self,
        ticker: str,
        form_types: Optional[List[str]] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        max_count: int = 50,
        include_full_history: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Get company filings using EDGAR API

        Filters are applied to the **whole** submissions list and ``max_count``
        caps the result afterwards. (The previous order — cap first, filter
        after — meant ``form_types=['10-K']`` scanned only the newest 50
        submissions, which for an active filer are almost all Form 4s, and
        reported "No EDGAR filings found".)

        Args:
            ticker: Stock ticker symbol
            form_types: List of form types to filter (e.g., ['10-K', '10-Q'])
            date_from: Start date (YYYY-MM-DD format)
            date_to: End date (YYYY-MM-DD format)
            max_count: Maximum number of filings to return (0 or less = all)
            include_full_history: When False (default) only the submissions API's
                ``recent`` page is used — up to 1,000 filings, which for AAPL
                reaches back to 2015 (probed 2026-07-31: 1,002 entries, oldest
                2015-05-29) and covers every realistic query. Set True to have
                ``sec_edgar_api`` follow the pagination files and download the
                filer's entire history (many extra requests and megabytes).

        Returns:
            List of filing dictionaries with metadata
        """
        if not validate_ticker(ticker):
            raise ValueError(f"Invalid ticker: {ticker}")

        logger.info(f"Fetching filings for {ticker} via EDGAR API")

        # Get CIK from ticker. A download failure raises (see
        # _get_cik_from_ticker); None means SEC does not know this ticker.
        cik = self._get_cik_from_ticker(ticker)
        if not cik:
            logger.error(f"Could not find CIK for ticker {ticker}")
            return []

        # Get submissions data. A transport/API failure here is a failure,
        # not "no filings" — it propagates (GROUND_TRUTH.md house rule 3).
        try:
            submissions = self.client.get_submissions(
                cik=cik, handle_pagination=include_full_history
            )
        except Exception as e:
            raise EdgarAPIError(
                f"EDGAR submissions request for {ticker} (CIK {cik}) failed: {e}"
            ) from e

        if not submissions or "filings" not in submissions:
            logger.warning(f"No submissions found for {ticker} (CIK: {cik})")
            return []

        recent_filings = submissions["filings"]["recent"]

        # Extract filing data
        filings = []
        forms = recent_filings.get("form", [])
        filing_dates = recent_filings.get("filingDate", [])
        report_dates = recent_filings.get("reportDate", [])
        accession_numbers = recent_filings.get("accessionNumber", [])
        primary_documents = recent_filings.get("primaryDocument", [])
        descriptions = recent_filings.get("primaryDocDescription", [])

        skipped_rows = 0
        for i in range(len(forms)):
            if max_count and max_count > 0 and len(filings) >= max_count:
                break

            # Per-row tolerance: one malformed submission entry must not kill
            # the whole listing (but a failed request already raised above).
            try:
                form = forms[i]
                filing_date = filing_dates[i] if i < len(filing_dates) else ""
                report_date = report_dates[i] if i < len(report_dates) else ""
                accession = accession_numbers[i] if i < len(accession_numbers) else ""
                primary_doc = primary_documents[i] if i < len(primary_documents) else ""
                description = descriptions[i] if i < len(descriptions) else ""

                # Filter by form types if specified (amendments included:
                # '10-K' also matches '10-K/A' — see sec_filings.form_matches)
                if form_types and not matches_any_form(form, form_types):
                    continue

                # Filter by date range if specified
                if date_from and filing_date < date_from:
                    continue
                if date_to and filing_date > date_to:
                    continue

                # Construct document URL
                accession_clean = accession.replace("-", "")
                document_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_clean}/{primary_doc}"
                filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_clean}/{accession}-index.html"

                filing_data = {
                    "ticker": ticker,
                    "cik": cik,
                    "form": form,
                    "filing_date": filing_date,
                    "report_date": report_date,
                    "accession_number": accession,
                    "primary_document": primary_doc,
                    "description": description,
                    "document_url": document_url,
                    "filing_url": filing_url,
                }

                filings.append(filing_data)
            except Exception as e:  # pragma: no cover - defensive
                skipped_rows += 1
                logger.warning(f"Skipping malformed submission row {i}: {e}")

        if skipped_rows:
            logger.warning(
                f"Skipped {skipped_rows} malformed submission row(s) for {ticker}"
            )

        logger.info(f"Retrieved {len(filings)} filings for {ticker}")
        return filings

    def get_filing_document_content(
        self,
        ticker: str,
        accession_number: str,
        primary_document: str,
        max_length: int = 50000,
    ) -> Dict[str, Any]:
        """
        Get SEC filing document content via EDGAR API, converted to text.

        HTML/inline-XBRL documents are converted to readable text *before*
        truncation, so ``max_length`` bounds prose rather than markup. Plain
        ``.txt`` filings are passed through unchanged.

        Truncation happens **here and only here**; the returned metadata
        reports both the full converted length and the returned length so
        callers never have to re-slice (which used to chop the marker off).

        Args:
            ticker: Stock ticker symbol
            accession_number: SEC accession number (with dashes)
            primary_document: Primary document filename
            max_length: Maximum content length to return (0 or less = no limit)

        Returns:
            Dictionary with document content and metadata. Metadata keys:
            ``content_type`` ("html"/"text"), ``full_content_length``
            (characters after conversion, before truncation),
            ``content_length`` (characters actually returned),
            ``truncated`` (bool), ``raw_content_length`` (bytes of markup).
        """
        try:
            logger.info(
                f"Fetching document content for {ticker}: {accession_number}/{primary_document}"
            )

            # Get CIK from ticker
            cik = self._get_cik_from_ticker(ticker)

            if not cik:
                return {
                    "content": "",
                    "metadata": {},
                    "status": "error",
                    "error": f"Could not find CIK for ticker {ticker}",
                }

            # Construct document URL
            accession_clean = accession_number.replace("-", "")
            document_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_clean}/{primary_document}"

            # Fetch document content (_sec_get honors SEC's ~10 req/s guidance)
            response = self._sec_get(document_url, timeout=30)
            response.raise_for_status()

            raw = response.text
            is_html = _looks_like_html(
                primary_document, response.headers.get("Content-Type", ""), raw
            )
            content = html_to_text(raw) if is_html else raw
            full_length = len(content)

            # Apply length limit — once, after conversion.
            truncated = bool(max_length and max_length > 0 and full_length > max_length)
            if truncated:
                content = content[:max_length] + TRUNCATION_MARKER

            metadata = {
                "ticker": ticker,
                "cik": cik,
                "accession_number": accession_number,
                "primary_document": primary_document,
                "document_url": document_url,
                "content_type": "html" if is_html else "text",
                "raw_content_length": len(raw),
                "full_content_length": full_length,
                "content_length": len(content),
                "truncated": truncated,
                "retrieved_at": datetime.now().isoformat(),
            }

            logger.info(
                "Retrieved %s document: %d raw chars -> %d text chars "
                "(returned %d, truncated=%s)",
                metadata["content_type"],
                len(raw),
                full_length,
                len(content),
                truncated,
            )

            return {
                "content": content,
                "metadata": metadata,
                "status": "success",
                "url": document_url,
            }

        except requests.RequestException as e:
            logger.error(f"Network error fetching document: {e}")
            return {
                "content": "",
                "metadata": {},
                "status": "error",
                "error": f"Network error: {str(e)}",
            }
        except Exception as e:
            logger.error(f"Error fetching document content: {e}")
            return {"content": "", "metadata": {}, "status": "error", "error": str(e)}

    def get_multiple_filing_contents(
        self, filings_data: List[Dict[str, str]], max_length: int = 5000
    ) -> List[Dict[str, Any]]:
        """
        Get content for multiple SEC filings

        The CIK lookup is served from the per-instance cache, so N filings cost
        one ``company_tickers.json`` download in total. Each document fetch
        still sleeps ``SEC_MIN_REQUEST_INTERVAL_SECONDS`` (SEC ~10 req/s).

        Args:
            filings_data: List of filing data dictionaries with keys:
                         ticker, accession_number, primary_document
            max_length: Maximum content length per document. Defaults to 5,000
                characters of *converted text* — enough for the batch tool to
                render every fetched character rather than downloading 20,000
                and showing 500.

        Returns:
            List of content dictionaries
        """
        results = []

        for i, filing_data in enumerate(filings_data):
            logger.info(f"Processing filing {i+1}/{len(filings_data)}")

            ticker = filing_data.get("ticker")
            accession = filing_data.get("accession_number")
            primary_doc = filing_data.get("primary_document")

            if not all([ticker, accession, primary_doc]):
                results.append(
                    {
                        "content": "",
                        "metadata": filing_data,
                        "status": "error",
                        "error": "Missing required filing data fields",
                    }
                )
                continue

            content = self.get_filing_document_content(
                ticker=ticker,
                accession_number=accession,
                primary_document=primary_doc,
                max_length=max_length,
            )

            results.append(content)

        return results

    def get_company_concept(
        self, ticker: str, concept: str, taxonomy: str = "us-gaap"
    ) -> Dict[str, Any]:
        """
        Get company concept data (financial metrics) via EDGAR API

        Args:
            ticker: Stock ticker symbol
            concept: XBRL concept (e.g., 'Assets', 'Revenues')
            taxonomy: Taxonomy ('us-gaap', 'dei', 'invest')

        Returns:
            Company concept data dictionary
        """
        try:
            logger.info(f"Fetching concept {concept} for {ticker}")

            # Get CIK from ticker
            cik = self._get_cik_from_ticker(ticker)

            if not cik:
                return {"error": f"Could not find CIK for ticker {ticker}"}

            # Get concept data
            concept_data = self.client.get_company_concept(
                cik=cik, taxonomy=taxonomy, concept=concept
            )

            return concept_data

        except Exception as e:
            logger.error(f"Error fetching concept {concept} for {ticker}: {e}")
            return {"error": str(e)}
