#!/usr/bin/env python3
"""Convenience runner for the screener invariant E2E suite.

Equivalent to::

    pytest --run-e2e -m e2e_invariant tests/test_e2e_screener_invariants.py

with a clear warning if the API key is missing.

Usage::

    python3 scripts/run_e2e_invariants.py
    python3 scripts/run_e2e_invariants.py -k uptrend
    python3 scripts/run_e2e_invariants.py -x

Requires ``FINVIZ_API_KEY`` set in the environment or .env.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv


def main() -> int:
    project_root = Path(__file__).resolve().parent.parent
    load_dotenv(project_root / ".env")

    if not os.environ.get("FINVIZ_API_KEY"):
        print(
            "WARNING: FINVIZ_API_KEY is not set. All live tests will skip.",
            file=sys.stderr,
        )

    args = [
        "--run-e2e",                # bypass conftest auto-skip
        "-m", "e2e_invariant",      # only this suite
        "-v",
        "--tb=short",
        "--color=yes",
        str(project_root / "tests" / "test_e2e_screener_invariants.py"),
        *sys.argv[1:],
    ]
    return pytest.main(args)


if __name__ == "__main__":
    sys.exit(main())
