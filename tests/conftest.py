"""Shared pytest fixtures, marker registration, and live-test gating.

Three kinds of tests live in this directory:

1. Pure unit tests (e.g. ``test_basic.py``, ``test_parser_unit_contracts.py``)
   — fast, offline, CI-safe.
2. Mocked screener tests (e.g. ``test_e2e_screeners.py``) — they patch
   client objects and don't hit the network. Despite the "e2e" name,
   they don't touch the live API.
3. Live tests that hit the real Finviz / SEC EDGAR APIs (e.g.
   ``test_e2e_screener_invariants.py``, ``test_screener_url_generation.py``,
   ``test_comprehensive_e2e_real_calls.py``).

The default ``pytest`` invocation must skip category 3 reliably for CI
to be safe even if a contributor forgets to add a marker. We do this in
two layers:

* **Auto-marking by filename pattern** — every test file whose name
  matches a known live-test pattern is automatically tagged
  ``pytest.mark.e2e``. This is defensive against a contributor adding a
  new live test without marking it.
* **Auto-skip unless opted in** — ``e2e``-tagged tests are skipped by
  default. Users opt in with ``--run-e2e`` (run all) or ``-m e2e`` /
  ``-m e2e_invariant`` (positive marker selection).

To mark a file that does NOT match the filename heuristic, add
``pytestmark = [pytest.mark.e2e]`` at module top-level.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional

import pytest
from dotenv import load_dotenv

# Filename substrings that indicate a test file hits the live network.
# Matched against the basename. Keep this list explicit; broad patterns
# risk auto-skipping mocked tests that only borrow a similar filename.
LIVE_TEST_FILENAME_PATTERNS: tuple[str, ...] = (
    "test_e2e_",
    "test_comprehensive_e2e",
    "test_live_",
    "test_edgar_api",
    "test_screener_url_generation",
    "test_volume_surge_screener",
    "test_uptrend_screener",
    "test_comprehensive_finviz_parameters",
    "test_analysis",
    "test_market_overview",
    "test_mcp_integration",
    "test_moving_average_position",
    "test_relative_volume_stocks",
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


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Auto-mark live tests by filename, then auto-skip unless opted in."""
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
