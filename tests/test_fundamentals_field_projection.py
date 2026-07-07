"""Regression tests for fundamentals field projection (data_fields filtering).

Bug report: requesting ``data_fields`` on ``get_stock_fundamentals`` /
``get_multiple_stocks_fundamentals`` produced three failure modes:

* **Silently dropped** — a valid public field name (``pe_ratio``, ``ps_ratio``,
  ``rsi``, ``performance_1y``, ``eps_growth_qtr``) was accepted by the
  validator but never appeared in the output. The client keyed its result
  dict by the *normalized CSV header* (``P/E`` -> ``p_e``) and matched the
  requested name against those keys, so the public name never matched.
* **Retrieved-but-not-rendered / wrong value** — ``sales_growth_qtr`` matched
  the unrelated ``sales`` column via a loose substring fallback, storing the
  Sales dollar figure under a key no display bucket reads.

The fix routes every requested field through
``FINVIZ_COMPREHENSIVE_FIELD_MAPPING[...].csv_name`` to the canonical result
key that the display/formatting layer reads, and drops the substring fallback.

These tests pin that behavior at the pure-projection layer (no network).
"""

import pytest

from src.finviz_client.base import FinvizClient


# A synthetic result dict exactly as the CSV-derived builder produces it:
# keyed by normalized CSV headers. Includes the ``sales`` column that the old
# substring matcher wrongly grabbed for ``sales_growth_qtr``.
SYNTHETIC_RESULT = {
    "market_cap": 50000.0,
    "p_e": 25.0,
    "p_s": 5.0,
    "peg": 1.5,
    "profit_margin": 20.0,
    "sales": 999999.0,  # the wrong-value trap
    "sales_growth_quarter_over_quarter": 12.0,
    "eps_growth_quarter_over_quarter": 15.0,
    "performance_year": 30.0,
    "relative_strength_index_14": 55.0,
    "beta": 1.1,
    "ticker": "AAPL",
}

# The ten fields from the bug report, mapped to the canonical result key the
# display buckets in src/server.py actually read.
REQUESTED_TO_CANONICAL = {
    "market_cap": "market_cap",
    "pe_ratio": "p_e",
    "ps_ratio": "p_s",
    "peg": "peg",
    "profit_margin": "profit_margin",
    "sales_growth_qtr": "sales_growth_quarter_over_quarter",
    "eps_growth_qtr": "eps_growth_quarter_over_quarter",
    "performance_1y": "performance_year",
    "rsi": "relative_strength_index_14",
    "beta": "beta",
}


@pytest.fixture
def client() -> FinvizClient:
    return FinvizClient(api_key="test-key")


@pytest.mark.parametrize("requested,canonical", REQUESTED_TO_CANONICAL.items())
def test_public_field_resolves_to_canonical_key(client, requested, canonical):
    assert client._resolve_result_key(requested) == canonical


def test_all_requested_fields_are_retrieved(client):
    filtered = client._filter_fundamental_fields(
        SYNTHETIC_RESULT, list(REQUESTED_TO_CANONICAL.keys())
    )
    non_null = {k: v for k, v in filtered.items() if v is not None}
    # All ten resolve to a non-null value (previously only four survived).
    assert len(non_null) == 10


def test_values_land_under_the_key_the_display_reads(client):
    filtered = client._filter_fundamental_fields(
        SYNTHETIC_RESULT, list(REQUESTED_TO_CANONICAL.keys())
    )
    for requested, canonical in REQUESTED_TO_CANONICAL.items():
        assert filtered[canonical] == SYNTHETIC_RESULT[canonical], requested


def test_sales_growth_does_not_leak_the_sales_value(client):
    """The loose substring fallback used to store Sales dollars under
    sales_growth_qtr; the resolved key must carry the real growth value."""
    filtered = client._filter_fundamental_fields(
        SYNTHETIC_RESULT, ["sales_growth_qtr"]
    )
    assert filtered["sales_growth_quarter_over_quarter"] == 12.0
    assert 999999.0 not in filtered.values()


def test_missing_field_resolves_to_none_not_wrong_value(client):
    """A requested field with no matching column is an honest None."""
    result = {"beta": 1.1, "ticker": "AAPL"}
    filtered = client._filter_fundamental_fields(result, ["pe_ratio", "beta"])
    assert filtered["p_e"] is None
    assert filtered["beta"] == 1.1


def test_alias_resolves_through_canonical_mapping(client):
    """Legacy aliases still resolve (net_margin -> profit_margin column)."""
    assert client._resolve_result_key("net_margin") == "profit_margin"
    assert client._resolve_result_key("performance_week") == "performance_week"
    assert client._resolve_result_key("roi") == "return_on_invested_capital"


def test_internal_name_passthrough(client):
    """An already-canonical internal name is used as-is."""
    assert client._resolve_result_key("p_e") == "p_e"
    assert client._resolve_result_key("relative_strength_index_14") == (
        "relative_strength_index_14"
    )


def test_bulk_projection_includes_ticker(client):
    filtered = client._filter_fundamental_fields(
        SYNTHETIC_RESULT, ["pe_ratio"], include_ticker=True
    )
    assert filtered["ticker"] == "AAPL"
    assert filtered["p_e"] == 25.0
