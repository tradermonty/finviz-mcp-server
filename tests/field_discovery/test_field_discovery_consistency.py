"""Consistency guarantees for the field-discovery tools.

The discovery tools describe the *same* field vocabulary the request path
accepts. When the two drift, `validate_fields` tells users that requests which
actually work are invalid (audit F1) and suggests fields that do not exist
(audit F2). These tests pin the agreement.
"""

from src.constants import FINVIZ_COMPREHENSIVE_FIELD_MAPPING
from src.field_discovery.metadata import FieldValidator
from src.field_discovery.tools import (
    _CATEGORY_ALIASES,
    _COMMON_CORRECTIONS,
    _FALLBACK_FIELD_MAPPING,
    _grouped_fields,
    describe_field,
    search_fields,
    validate_fields,
)
from src.utils.validators import get_valid_data_field_names, validate_data_fields


def _rendered_related_fields(text: str) -> list:
    """Extract the field names listed under the 'Related Fields' heading."""
    lines = text.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if "Related Fields:" in line)
    except StopIteration:
        return []

    related = []
    for line in lines[start + 1 :]:
        stripped = line.strip()
        if not stripped:
            break
        if stripped.startswith("•"):
            related.append(stripped.lstrip("• ").strip())
    return related


class TestValidateFieldsAgreesWithRequestPath:
    """`validate_fields` must accept exactly what `validate_data_fields` does."""

    def test_accepts_every_name_the_request_path_accepts(self):
        accepted = sorted(get_valid_data_field_names())

        # Sanity: the derived set is more than the public mapping (aliases,
        # normalized CSV result keys, derived keys, and "all").
        assert len(accepted) > len(FINVIZ_COMPREHENSIVE_FIELD_MAPPING)

        content = validate_fields(accepted)[0].text

        assert "INVALID FIELDS" not in content
        assert f"VALID FIELDS ({len(accepted)})" in content

    def test_accepts_aliases_result_keys_and_derived_keys(self):
        # One representative of each class the old implementation rejected.
        samples = [
            "net_margin",  # alias -> profit_margin
            "roi",  # alias -> roic
            "p_e",  # normalized CSV header result key
            "eps_ttm",  # normalized CSV header result key
            "week_52_high",  # derived result key
            "all",  # projection escape hatch
        ]

        assert validate_data_fields(samples) == []

        content = validate_fields(samples)[0].text
        assert "INVALID FIELDS" not in content

    def test_still_rejects_names_the_request_path_rejects(self):
        rejected = ["sales_growth_this_y", "definitely_not_a_field"]

        assert validate_data_fields(rejected) == rejected

        content = validate_fields(rejected)[0].text
        assert "INVALID FIELDS (2)" in content
        assert "✅ VALID FIELDS" not in content


class TestSuggestionTargetsExist:
    """Every typo correction must point at a field that actually validates."""

    def test_tools_correction_targets_validate(self):
        targets = sorted(set(_COMMON_CORRECTIONS.values()))
        assert targets  # guard against an empty table silently passing
        assert validate_data_fields(targets) == []

    def test_metadata_validator_correction_targets_validate(self):
        validator = FieldValidator(get_valid_data_field_names())
        targets = sorted(set(validator.common_corrections.values()))
        assert targets
        assert validate_data_fields(targets) == []

    def test_rendered_suggestions_validate(self):
        typos = sorted(_COMMON_CORRECTIONS)
        content = validate_fields(typos)[0].text

        suggested = [
            line.split("Did you mean:", 1)[1].strip()
            for line in content.splitlines()
            if "Did you mean:" in line
        ]
        assert len(suggested) == len(typos)
        assert validate_data_fields(suggested) == []


class TestDescribeFieldRelatedFields:
    def test_every_related_field_validates(self):
        invalid = {}
        for field_name in FINVIZ_COMPREHENSIVE_FIELD_MAPPING:
            related = _rendered_related_fields(describe_field(field_name)[0].text)
            bad = validate_data_fields(related)
            if bad:
                invalid[field_name] = bad

        assert invalid == {}

    def test_curated_entries_actually_render_related_fields(self):
        # Guard: if the parsing above silently found nothing, the test above
        # would pass vacuously.
        related = _rendered_related_fields(describe_field("pe_ratio")[0].text)
        assert "forward_pe" in related


class TestSearchFieldsCategoryFilter:
    """The category filter must use the categories the other tools display.

    The old hand-maintained whitelist named fields that exist nowhere and
    omitted the real ones, so filtering silently hid legitimate matches
    (audit F3).
    """

    def test_technical_category_finds_the_sma_fields(self):
        content = search_fields("sma", category="technical")[0].text

        for field in ("sma_20", "sma_50", "sma_200"):
            assert field in content
        assert "No matches" not in content

    def test_full_category_name_is_accepted(self):
        by_alias = search_fields("sma", category="technical")[0].text
        by_name = search_fields("sma", category="Technical Indicators")[0].text

        assert by_alias == by_name

    def test_unknown_category_reports_an_error_listing_valid_ones(self):
        content = search_fields("ratio", category="not_a_category")[0].text

        assert "Unknown category" in content
        assert "not_a_category" in content
        # Every derived category name is offered.
        for _, name, _ in _grouped_fields():
            assert name in content
        # It must not masquerade as an empty result set.
        assert "No matches found" not in content

    def test_every_alias_resolves_to_a_category_that_exists(self):
        # An alias for a category _grouped_fields never emits would reproduce
        # the exact silent-empty bug this finding is about.
        derived_names = {name for _, name, _ in _grouped_fields()}
        assert set(_CATEGORY_ALIASES.values()) <= derived_names

    def test_no_alias_yields_an_empty_category(self):
        for alias in _CATEGORY_ALIASES:
            content = search_fields("a", category=alias)[0].text
            assert "Unknown category" not in content, alias

    def test_each_field_belongs_to_exactly_one_category(self):
        seen = {}
        duplicates = []
        for _, name, members in _grouped_fields():
            for field in members:
                if field in seen:
                    duplicates.append((field, seen[field], name))
                seen[field] = name

        assert duplicates == []
        assert set(seen) == set(FINVIZ_COMPREHENSIVE_FIELD_MAPPING)

    def test_searching_a_field_within_its_own_category_finds_it(self):
        missing = []
        for _, name, members in _grouped_fields():
            for field in members:
                content = search_fields(field, category=name)[0].text
                if field not in content:
                    missing.append((field, name))

        assert missing == []


class TestDescribeFieldAcceptsEveryValidName:
    """describe_field must answer for anything validate_fields calls valid."""

    def test_alias_resolves_to_its_canonical_field(self):
        content = describe_field("net_margin")[0].text

        assert "not found" not in content.lower()
        assert "profit_margin" in content
        # The requested spelling is acknowledged, not silently swapped.
        assert "net_margin" in content

    def test_result_key_resolves_to_its_canonical_field(self):
        for requested, canonical in (("p_e", "pe_ratio"), ("eps_ttm", "eps")):
            content = describe_field(requested)[0].text
            assert "not found" not in content.lower(), requested
            assert canonical in content, requested

    def test_derived_key_is_describable(self):
        content = describe_field("week_52_high")[0].text

        assert "not found" not in content.lower()
        assert "week_52_high" in content

    def test_every_accepted_name_is_describable(self):
        undescribable = []
        for name in sorted(get_valid_data_field_names()):
            if name == "all":  # projection escape hatch, not a field
                continue
            if "not found" in describe_field(name)[0].text.lower():
                undescribable.append(name)

        assert undescribable == []

    def test_unknown_name_still_reports_not_found(self):
        content = describe_field("definitely_not_a_field")[0].text
        assert "not found" in content.lower()


class TestDescribeFieldCategory:
    def test_category_matches_the_derived_grouping(self):
        field_categories = {
            field: name for _, name, members in _grouped_fields() for field in members
        }

        mismatched = []
        for field, expected in field_categories.items():
            content = describe_field(field)[0].text
            if f"Category: {expected}" not in content:
                mismatched.append(field)

        assert mismatched == []

    def test_curated_fields_are_not_labelled_other(self):
        for field in ("pe_ratio", "market_cap", "earnings_date", "eps_growth_qtr"):
            assert "Category: Other" not in describe_field(field)[0].text, field


class TestFallbackMapping:
    """The import-isolated fallback must be real fields, not synthesized filler."""

    def test_fallback_is_a_slice_of_the_real_mapping(self):
        for name, info in _FALLBACK_FIELD_MAPPING.items():
            assert name in FINVIZ_COMPREHENSIVE_FIELD_MAPPING, name
            assert info == FINVIZ_COMPREHENSIVE_FIELD_MAPPING[name], name

    def test_fallback_contains_no_synthesized_filler(self):
        assert not [n for n in _FALLBACK_FIELD_MAPPING if n.startswith("test_field_")]
        assert len(_FALLBACK_FIELD_MAPPING) < len(FINVIZ_COMPREHENSIVE_FIELD_MAPPING)
