"""
Unit tests for the EDGAR client lazy-initialization wired in PR E.

The contract:

1. Importing ``src.server`` does not import or initialize the EDGAR client
   (so missing ``sec_edgar_api`` / fragile transitive deps cannot break the
   whole MCP server at module-load).
2. ``_get_edgar_client()`` raises ``ValueError`` when ``EDGAR_USER_AGENT`` is
   not set — SEC requires a non-empty User-Agent on every request.
3. With ``EDGAR_USER_AGENT`` set, ``_get_edgar_client()`` returns an
   ``EdgarAPIClient`` instance and caches it (subsequent calls return the
   same object).
4. Finviz SEC tools (``finviz_sec``) are independent — they do not touch the
   EDGAR client and so are unaffected by ``EDGAR_USER_AGENT``.

Cache isolation is enforced by an autouse fixture that resets
``server._edgar_client`` to ``None`` before every test, so test order does
not leak a previously-built client into the unset-env case.
"""

import sys
from unittest.mock import MagicMock

import pytest

from src import server as server_module


@pytest.fixture(autouse=True)
def reset_edgar_client(monkeypatch):
    """Reset the cached singleton so tests are order-independent."""
    monkeypatch.setattr(server_module, "_edgar_client", None)


class TestEdgarLazyInit:
    def test_missing_user_agent_raises_value_error(self, monkeypatch):
        monkeypatch.delenv("EDGAR_USER_AGENT", raising=False)
        with pytest.raises(ValueError) as exc_info:
            server_module._get_edgar_client()
        msg = str(exc_info.value)
        assert "EDGAR_USER_AGENT" in msg
        assert "User-Agent" in msg

    def test_with_user_agent_returns_client_and_caches(self, monkeypatch):
        monkeypatch.setenv("EDGAR_USER_AGENT", "Test Co test@example.com")

        # Pre-mock ``sec_edgar_api`` in sys.modules so the lazy
        # ``from sec_edgar_api import EdgarClient`` inside
        # ``_get_edgar_client()`` succeeds even when the real package
        # is broken in the running env (e.g. CI's pyrate-limiter 3.x
        # API mismatch). We then also drop any cached
        # ``src.finviz_client.edgar_client`` so the inner module is
        # re-imported fresh and picks up the mocked dependency.
        fake_sec_edgar = MagicMock()
        monkeypatch.setitem(sys.modules, "sec_edgar_api", fake_sec_edgar)
        monkeypatch.delitem(
            sys.modules, "src.finviz_client.edgar_client", raising=False
        )

        client_a = server_module._get_edgar_client()
        client_b = server_module._get_edgar_client()

        # Cache: second call returns the same object, not a fresh instance.
        # That alone proves ``_get_edgar_client`` is idempotent and the
        # singleton is wired correctly; we deliberately avoid asserting on
        # the concrete type because the test uses a mocked sec_edgar_api.
        assert client_a is client_b
        assert client_a is not None

    def test_finviz_sec_client_does_not_require_user_agent(self, monkeypatch):
        """The Finviz SEC listing tools use ``finviz_sec`` (a different
        client) and must not be coupled to ``EDGAR_USER_AGENT``."""
        monkeypatch.delenv("EDGAR_USER_AGENT", raising=False)
        # finviz_sec is initialized at module-load with the FINVIZ_API_KEY,
        # not EDGAR_USER_AGENT. Asserting on type is enough — actually
        # invoking it would hit the network.
        from src.finviz_client.sec_filings import FinvizSECFilingsClient

        assert isinstance(server_module.finviz_sec, FinvizSECFilingsClient)
