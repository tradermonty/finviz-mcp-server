"""Shared pytest fixtures, marker registration, and live-test gating.

The ``e2e`` marker covers two related categories of tests that we want
opt-in by default:

* **Live API tests** — call real Finviz / SEC EDGAR endpoints
  (``test_e2e_screener_invariants.py``, ``test_volume_surge_screener.py``,
  ``test_edgar_api.py``, ...).
* **Slow integration tests** — extended async/MCP server suites that,
  while sometimes mocked at the screener layer, are by team convention
  excluded from quick CI cycles (``test_e2e_screeners.py``,
  ``test_comprehensive_e2e_real_calls.py``, ...).

Both share the same opt-in semantics: skipped unless the user passes
``--run-e2e`` or selects ``-m e2e`` / ``-m e2e_invariant``.

Two complementary marking mechanisms
------------------------------------

1. **Explicit module-level marker** (preferred): files declare
   ``pytestmark = [pytest.mark.e2e]`` at the top. This survives all
   hook ordering and works correctly with ``pytest -m e2e``.

2. **Filename-based auto-marking** (defensive fallback): files whose
   basename contains one of ``LIVE_TEST_FILENAME_PATTERNS`` are tagged
   ``e2e`` automatically. The hook is registered with
   ``tryfirst=True`` so the auto-mark applies *before* pytest's own
   ``-m`` filter runs, making auto-marked files visible to ``-m e2e``
   selection.

The pattern list is intentionally narrow: only files that are known
to either hit the live API or to be slow integration suites. Pure
offline regression tests (``test_screener_url_generation.py``,
``test_moving_average_position.py``, ``test_basic.py``,
``test_parser_unit_contracts.py``, etc.) are NOT in the pattern list
and run by default.

What is NOT solved here
-----------------------

Module-level import errors (e.g. ``ModuleNotFoundError: mcp``) cannot
be prevented by any collection-time hook — they happen during import,
before this hook runs. Such files should be fixed in dependency
management (see PR #8 for the pyproject.toml runtime-deps work).
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional

import pytest
from dotenv import load_dotenv

# Filename substrings that indicate a test file is opt-in (live API or
# slow integration). Matched against the basename. Verified entries
# only — offline regression files (test_screener_url_generation,
# test_moving_average_position, test_market_overview, test_basic,
# test_parser_unit_contracts) are intentionally absent from this list
# so they keep running in the default suite.
LIVE_TEST_FILENAME_PATTERNS: tuple[str, ...] = (
    # Slow integration / e2e suites (mocked at screener layer but
    # heavy MCP server round-trips):
    "test_e2e_",
    "test_comprehensive_e2e",
    "test_live_",
    # Live API suites (verified to instantiate FinvizClient/Screener
    # or EdgarAPIClient and call real endpoints):
    "test_edgar_api",
    "test_volume_surge_screener",
    "test_uptrend_screener",
    "test_comprehensive_finviz_parameters",
    "test_analysis",
)

# Detect "e2e" / "e2e_invariant" / etc. used as a positive marker
# selection while excluding "not e2e" forms.
_E2E_TARGET_RE = re.compile(r"\be2e\w*\b")


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-e2e",
        action="store_true",
        default=False,
        help=(
            "Run end-to-end tests that hit the live Finviz / SEC APIs. "
            "Without this flag (and without -m e2e), e2e-marked tests "
            "are skipped so the default `pytest` run is CI-safe."
        ),
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "e2e: end-to-end test that hits a live external API. "
        "Skipped by default; pass --run-e2e or `-m e2e` to enable.",
    )
    config.addinivalue_line(
        "markers",
        "e2e_invariant: e2e test that verifies screener results satisfy "
        "documented filter invariants.",
    )


def _expression_opts_into_e2e(markexpr: str) -> bool:
    """True iff a -m expression positively targets e2e tests."""
    if not markexpr:
        return False
    expr = markexpr.strip()
    if "not e2e" in expr:
        return False
    return bool(_E2E_TARGET_RE.search(expr))


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Auto-mark live tests by filename, then auto-skip unless opted in.

    Registered ``tryfirst=True`` so the marker is added before pytest's
    built-in ``-m`` filter runs. Without this, ``pytest -m e2e`` would
    deselect auto-marked items because the marker did not yet exist
    when pytest's filter ran.
    """
    for item in items:
        try:
            basename = Path(str(item.fspath)).name
        except Exception:
            continue
        if any(p in basename for p in LIVE_TEST_FILENAME_PATTERNS):
            item.add_marker(pytest.mark.e2e)

    if config.getoption("--run-e2e"):
        return
    markexpr = config.getoption("markexpr") or ""
    if _expression_opts_into_e2e(markexpr):
        return

    skip_marker = pytest.mark.skip(
        reason=(
            "e2e test skipped by default. "
            "Run with `--run-e2e`, `-m e2e`, or `-m e2e_invariant`."
        )
    )
    for item in items:
        if "e2e" in item.keywords:
            item.add_marker(skip_marker)


@pytest.fixture(scope="session", autouse=True)
def _load_env() -> None:
    load_dotenv()


@pytest.fixture(scope="session")
def finviz_api_key() -> Optional[str]:
    return os.environ.get("FINVIZ_API_KEY")


@pytest.fixture(scope="session")
def require_api_key(finviz_api_key: Optional[str]) -> str:
    """Skip cleanly when the live API key is not configured."""
    if not finviz_api_key:
        pytest.skip(
            "FINVIZ_API_KEY is not set; skipping live Finviz E2E test. "
            "Set FINVIZ_API_KEY in .env to enable."
        )
    return finviz_api_key


@pytest.fixture(scope="session")
def screener(require_api_key: str):
    from src.finviz_client.screener import FinvizScreener

    return FinvizScreener(api_key=require_api_key)
