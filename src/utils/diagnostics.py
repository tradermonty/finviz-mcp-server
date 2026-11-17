"""Shareable request diagnostics: credentials belong only in outbound requests."""

import logging
import os
import re
from typing import Any, Iterable
from urllib.parse import quote, quote_plus

_SENSITIVE = re.compile(r"^(?:auth|api[_-]?key|token|access_token)$", re.I)
_QUERY_SECRET = re.compile(
    r"(\b(?:auth|api[_-]?key|token|access_token)(?:=|%3d))([^&\s\"'<>]+)",
    re.I,
)


def sanitize_diagnostics(value: Any, secrets: Iterable[str] = ()) -> str:
    """Redact known values (including encoded forms) and credential parameters."""
    if isinstance(value, dict):
        value = {
            key: "[REDACTED]" if _SENSITIVE.match(str(key)) else val
            for key, val in value.items()
        }
    text = str(value)
    for secret in (*secrets, os.getenv("FINVIZ_API_KEY", "")):
        if not secret:
            continue
        for variant in sorted(
            {secret, quote(secret, safe=""), quote_plus(secret)}, key=len, reverse=True
        ):
            text = text.replace(variant, "[REDACTED]")
    return _QUERY_SECRET.sub(r"\1[REDACTED]", text)


class RequestLogFilter(logging.Filter):
    """Prevent urllib3 DEBUG request targets from exposing auth query values."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = sanitize_diagnostics(record.getMessage())
        record.args = ()
        return True


# Filter at the emitting logger, so custom/root handlers are protected too.
logging.getLogger("urllib3.connectionpool").addFilter(RequestLogFilter())
