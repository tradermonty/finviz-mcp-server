"""Regression tests: every fetched fundamentals field must actually render.

Bug report (2026-07): the fundamentals tools accepted field names, counted
them as "covered", echoed them in "All Available Fields" — and never
rendered dozens of them. Confirmed invisible families included the quote
group (open/high/low/gap/after-hours), all ten intraday performance fields,
forward growth estimates, and the *entire* ETF profile (an ETF call rendered
zero ETF-specific values). Meanwhile "Data Coverage" reported near-perfect
numbers because it counted accepted names, not rendered values.

Fixtures ``tests/fixtures/MRVL_raw.json`` (stock) and ``SPMO_raw.json``
(ETF) are real client result dicts captured live on 2026-07-30 — the exact
shapes the display layer receives.

These tests pin the new contract:

1. The section spec knows every key the client can produce (completeness).
2. ``format_fundamentals`` renders every non-null key; coverage counts
   rendered values.
3. Explicitly requested fields that come back null render as an explicit
   N/A instead of vanishing (the "eps_growth_past_5y disappeared" class).
4. The multi-stock compact view renders every non-null key too.
5. Validator/mapping/client resolution can't drift apart.
"""

import json
from pathlib import Path

import pytest

from src.constants import FINVIZ_COMPREHENSIVE_FIELD_MAPPING
from src.finviz_client.base import FinvizClient
from src.utils.fundamentals_formatter import (
    HEADER_KEYS,
    KNOWN_KEYS,
    compact_fundamentals,
    format_fundamentals,
)
from src.utils.validators import validate_data_fields

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / f"{name}_raw.json").read_text())


@pytest.fixture(scope="module")
def mrvl() -> dict:
    return _load("MRVL")


@pytest.fixture(scope="module")
def spmo() -> dict:
    return _load("SPMO")


@pytest.fixture(scope="module")
def client() -> FinvizClient:
    return FinvizClient(api_key="test-key")


# ---------------------------------------------------------------------------
# 1. Spec completeness
# ---------------------------------------------------------------------------


class TestSectionSpecCompleteness:
    def test_every_stock_result_key_has_a_display_slot(self, mrvl):
        unknown = set(mrvl) - KNOWN_KEYS - HEADER_KEYS
        assert not unknown, (
            f"Result keys with no display slot (would only render via the "
            f"catch-all): {sorted(unknown)}. Add them to SECTIONS."
        )

    def test_every_etf_result_key_has_a_display_slot(self, spmo):
        unknown = set(spmo) - KNOWN_KEYS - HEADER_KEYS
        assert not unknown

    def test_mapping_covers_every_verified_csv_column_exactly_once(self):
        ids = sorted(
            info["column_id"] for info in FINVIZ_COMPREHENSIVE_FIELD_MAPPING.values()
        )
        assert ids == list(range(150)), (
            "FINVIZ_COMPREHENSIVE_FIELD_MAPPING must cover column ids 0-149 "
            "exactly once (verified against the live v=152 export)."
        )


# ---------------------------------------------------------------------------
# 2. Full rendering + honest coverage
# ---------------------------------------------------------------------------


class TestEveryNonNullFieldRenders:
    @pytest.mark.parametrize("fixture_name", ["MRVL", "SPMO"])
    def test_rendered_count_equals_non_null_count(self, fixture_name):
        data = _load(fixture_name)
        text = "\n".join(format_fundamentals(data))
        expected = sum(
            1 for k, v in data.items() if v is not None and k not in HEADER_KEYS
        )
        assert f"Data Coverage: {expected}/{len(data)} fields rendered" in text

    def test_previously_invisible_stock_fields_render(self, mrvl):
        """The exact fields the bug report proved were silently dropped."""
        text = "\n".join(format_fundamentals(mrvl))
        assert "AH Close" in text and "$195.31" in text
        assert "AH Volume" in text and "7,252,985" in text
        assert "Open" in text and "$178.38" in text
        assert "Gap (%)" in text and "+9.16" in text
        assert "Optionable" in text
        assert "1 Min (%)" in text  # intraday performance family
        assert "4 Hours (%)" in text
        assert "EPS Growth Next 5Y (%)" in text and "+47.74" in text
        assert "Float (%)" in text and "99.24" in text
        assert "Exchange" in text and "NASD" in text
        assert "Latest News" in text

    def test_etf_profile_renders_for_etf(self, spmo):
        """SPMO previously rendered *zero* ETF-specific values."""
        text = "\n".join(format_fundamentals(spmo))
        assert "Asset Type" in text and "Equities (Stocks)" in text
        assert "ETF Type" in text and "US Equities" in text
        assert "AUM" in text and "$19.96B" in text
        assert "NAV" in text and "$136.31" in text
        assert "Net Expense Ratio (%)" in text and "0.13" in text
        assert "Flows 1M" in text and "$935.57M" in text
        assert "Return 1Y (%)" in text and "+19.26" in text
        assert "Since Inception (%)" in text and "+18.35" in text
        assert "Tags" in text

    def test_volatility_week_and_month_both_render(self, mrvl):
        """volatility_week and volatility_month used to collide on a single
        "Volatility (%)" slot, silently discarding one value."""
        text = "\n".join(format_fundamentals(mrvl))
        assert "Volatility W (%)" in text and "8.10" in text
        assert "Volatility M (%)" in text and "7.17" in text

    def test_relative_and_absolute_52w_both_render(self, mrvl):
        text = "\n".join(format_fundamentals(mrvl))
        assert "52W High Dist (%)" in text and "-44.43" in text
        assert "52W High" in text and "$329.85" in text

    def test_unknown_future_key_falls_into_other_section(self):
        data = {"ticker": "X", "price": 10.0, "brand_new_finviz_column": 42}
        text = "\n".join(format_fundamentals(data))
        assert "📦 Other Fields" in text
        assert "brand_new_finviz_column" in text and "42" in text


# ---------------------------------------------------------------------------
# 3. Explicit data_fields mode — misses must be visible
# ---------------------------------------------------------------------------


class TestExplicitRequestHonesty:
    def test_requested_but_null_field_renders_na(self):
        data = {"ticker": "MRVL", "p_e": 25.0, "eps_growth_past_5_years": None}
        text = "\n".join(
            format_fundamentals(
                data, requested_fields=["pe_ratio", "eps_growth_past_5y"]
            )
        )
        assert "EPS Growth Past 5Y (%)" in text
        assert "N/A (no data from Finviz)" in text
        assert "No data from Finviz for: eps_growth_past_5_years" in text

    def test_null_fields_skipped_in_default_mode(self, mrvl):
        text = "\n".join(format_fundamentals(mrvl))
        assert "N/A (no data from Finviz)" not in text

    def test_explicit_52w_request_carries_absolute_prices(self, client, mrvl):
        """Requesting 52_week_high explicitly used to drop the derived
        absolute price in projection, so nothing rendered."""
        filtered = client._filter_fundamental_fields(mrvl, ["52_week_high"])
        assert filtered["52_week_high"] == pytest.approx(-44.43)
        assert filtered["week_52_high"] == pytest.approx(329.85)
        text = "\n".join(
            format_fundamentals(filtered, requested_fields=["52_week_high"])
        )
        assert "$329.85" in text

    def test_week_52_low_alias_also_carries_absolute(self, client, mrvl):
        filtered = client._filter_fundamental_fields(mrvl, ["week_52_low"])
        assert filtered["week_52_low"] == pytest.approx(61.44)


# ---------------------------------------------------------------------------
# 4. Multi-stock compact view
# ---------------------------------------------------------------------------


class TestCompactViewCompleteness:
    def test_compact_renders_every_non_null_field(self, spmo):
        text = "\n".join(compact_fundamentals(spmo))
        # Previously-invisible ETF family in the bulk view:
        assert "AUM=$19.96B" in text
        assert "Flows YTD=$4.71B" in text
        assert "Return 5Y (%)=+19.13" in text
        assert "AH Close=$145.12" in text
        assert "1 Min (%)=" in text


# ---------------------------------------------------------------------------
# 5. Anti-drift: validator / mapping / client resolution stay in sync
# ---------------------------------------------------------------------------


class TestNoDrift:
    def test_every_public_mapping_name_is_accepted_and_resolvable(
        self, client, mrvl
    ):
        """Every name list_available_fields advertises must (a) pass the
        validator and (b) resolve to a key the client actually returns."""
        names = list(FINVIZ_COMPREHENSIVE_FIELD_MAPPING)
        assert validate_data_fields(names) == []
        result_keys = set(mrvl) | {"week_52_high", "week_52_low"}
        unresolvable = {
            name
            for name in names
            if client._resolve_result_key(name) not in result_keys
        }
        assert not unresolvable, (
            f"Documented fields that resolve to keys the client never "
            f"returns: {sorted(unresolvable)}"
        )

    def test_every_result_key_is_a_valid_request_name(self, mrvl):
        """The raw result keys (what the echo line shows) must round-trip
        as request names — users copy them from the output."""
        assert validate_data_fields(sorted(mrvl)) == []

    def test_bug_report_class2_names_accepted(self, client, mrvl):
        """eps_growth_past_5y and sector_theme: listed by discovery, must
        be accepted and resolve to real columns (null for MRVL is genuine
        Finviz data absence, now surfaced as N/A rather than vanishing)."""
        assert validate_data_fields(["eps_growth_past_5y", "sector_theme"]) == []
        assert client._resolve_result_key("eps_growth_past_5y") in mrvl
        assert client._resolve_result_key("sector_theme") in mrvl

    def test_stock_vs_etf_long_term_performance_split(self, client):
        """performance_3y must hit the stock column (Performance (3 Years)),
        not the ETF-only "Return 3 Year" column it used to point at (null
        for every stock)."""
        assert client._resolve_result_key("performance_3y") == "performance_3_years"
        assert client._resolve_result_key("return_3y") == "return_3_year"
