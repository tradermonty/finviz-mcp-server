"""
Custom exceptions for Finviz MCP Server
"""


class ToolError(Exception):
    """Base exception for tool-related errors."""


class ValidationError(ToolError):
    """Exception raised for input validation errors."""


class NetworkError(ToolError):
    """Exception raised for network-related errors."""


class FinvizAPIError(ToolError):
    """Raised when a Finviz request fails at the request level.

    Covers everything that makes a response unusable rather than empty:
    transport failures (HTTP status, connection, timeout), a missing API
    key, an HTML body where CSV was requested (auth / Elite subscription
    problems), and unparseable payloads.

    A genuinely empty result set (CSV header with zero rows) is NOT an
    error — it returns an empty DataFrame / list, so callers can tell
    "no matches" apart from "the request failed"
    (tests/fixtures/GROUND_TRUTH.md house rule 3).
    """


class DataError(ToolError):
    """Exception raised for data processing errors."""


class EdgarAPIError(ToolError):
    """Raised when a SEC EDGAR request fails at the request level.

    Same contract as :class:`FinvizAPIError`: transport failures, an
    unusable payload, or an API error are reported as errors. "SEC knows
    no such ticker" and "this company filed nothing matching" are empty
    results, not errors (GROUND_TRUTH.md house rule 3).
    """
