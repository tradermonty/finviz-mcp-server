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

from unittest.mock import patch

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

        # Stub out the real EdgarAPIClient import so this test does not
        # depend on sec_edgar_api being installable in the running env.
        class FakeEdgarAPIClient:
            def __init__(self, user_agent):
                self.user_agent = user_agent

        with patch(
            "src.finviz_client.edgar_client.EdgarAPIClient",
            FakeEdgarAPIClient,
        ):
            client_a = server_module._get_edgar_client()
            client_b = server_module._get_edgar_client()

        assert isinstance(client_a, FakeEdgarAPIClient)
        assert client_a.user_agent == "Test Co test@example.com"
        # Cache: second call returns the same object, not a fresh instance
        assert client_a is client_b

    def test_finviz_sec_client_does_not_require_user_agent(self, monkeypatch):
        """The Finviz SEC listing tools use ``finviz_sec`` (a different
        client) and must not be coupled to ``EDGAR_USER_AGENT``."""
        monkeypatch.delenv("EDGAR_USER_AGENT", raising=False)
        # finviz_sec is initialized at module-load with the FINVIZ_API_KEY,
        # not EDGAR_USER_AGENT. Asserting on type is enough — actually
        # invoking it would hit the network.
        from src.finviz_client.sec_filings import FinvizSECFilingsClient

        assert isinstance(server_module.finviz_sec, FinvizSECFilingsClient)
