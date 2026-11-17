"""Shareable request diagnostics: credentials belong only in outbound requests."""

import logging
import os
import re
from typing import Any, Iterable, Mapping

_SENSITIVE = re.compile(r"^(?:auth|api[_-]?key|token|access_token)$", re.I)
_QUERY_SECRET = re.compile(
    r"(\b(?:auth|api[_-]?key|token|access_token)(?:=|%3d))([^&\s\"'<>]+)",
    re.I,
)


def credential_values(value: Any) -> Iterable[str]:
    """Find credential values before request diagnostics are wrapped or formatted."""
    if isinstance(value, Mapping):
        for key, item in value.items():
            if _SENSITIVE.fullmatch(str(key)):
                yield from _string_values(item)
            else:
                yield from credential_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from credential_values(item)


def _string_values(value: Any) -> Iterable[str]:
    if isinstance(value, Mapping):
        for item in value.values():
            yield from _string_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _string_values(item)
    elif value is not None:
        yield str(value)


def _secret_pattern(secret: str) -> str:
    # Percent escape hex digits are case-insensitive. Each character can be
    # literal or escaped, including normally unreserved letters (e.g. %73).
    parts = []
    for char in secret:
        encoded = ""
        for byte in char.encode("utf-8"):
            digits = f"{byte:02X}"
            encoded += "%" + "".join(
                f"[{d.lower()}{d}]" if d.isalpha() else d for d in digits
            )
        alternatives = [re.escape(char), encoded]
        if char == " ":
            alternatives.append(r"\+")  # application/x-www-form-urlencoded
        parts.append("(?:" + "|".join(alternatives) + ")")
    return "".join(parts)


def sanitize_diagnostics(value: Any, secrets: Iterable[str] = ()) -> str:
    """Recursively redact parameters, then known raw/encoded secrets in text."""
    known = {
        str(secret)
        for secret in (
            *secrets,
            *credential_values(value),
            os.getenv("FINVIZ_API_KEY", ""),
        )
        if secret
    }
    patterns = [
        re.compile(_secret_pattern(s)) for s in sorted(known, key=len, reverse=True)
    ]

    def redact_text(text: str) -> str:
        for pattern in patterns:
            text = pattern.sub("[REDACTED]", text)
        return _QUERY_SECRET.sub(r"\1[REDACTED]", text)

    def redact(item: Any) -> Any:
        if isinstance(item, Mapping):
            return {
                redact_text(str(key)): (
                    "[REDACTED]" if _SENSITIVE.fullmatch(str(key)) else redact(val)
                )
                for key, val in item.items()
            }
        if isinstance(item, list):
            return [redact(val) for val in item]
        if isinstance(item, tuple):
            return tuple(redact(val) for val in item)
        return redact_text(item) if isinstance(item, str) else item

    return redact_text(str(redact(value)))


class RequestLogFilter(logging.Filter):
    """Prevent urllib3 DEBUG request targets from exposing auth query values."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = sanitize_diagnostics(record.getMessage())
        record.args = ()
        return True


# Filter at the emitting logger, so custom/root handlers are protected too.
logging.getLogger("urllib3.connectionpool").addFilter(RequestLogFilter())
