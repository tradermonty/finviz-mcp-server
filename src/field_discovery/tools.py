"""
Field Discovery MCP Tools
Implements field discovery and introspection capabilities for the Finviz MCP Server
"""

# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------
# 1. Prefer the official TextContent from the `mcp` package so that results
#    returned by these tools are serialisable by the FastMCP server.
# 2. During unit-testing (where the `mcp` dependency may be absent) gracefully
#    fall back to a minimal stub that exposes the same public interface used
#    in the assertions (``type`` and ``text`` attributes).
# ---------------------------------------------------------------------------

import difflib
from typing import List, Optional

try:
    # The canonical TextContent with JSON-serialisation helpers
    from mcp.types import TextContent  # type: ignore
except Exception:  # pragma: no cover – testing environments without mcp
    # Lightweight fallback used in test context only
    class TextContent:  # pylint: disable=too-few-public-methods
        """Minimal stub replicating the parts of ``mcp.types.TextContent``
        that are referenced in tests (``type`` and ``text`` attributes)."""

        def __init__(self, type: str, text: str):  # noqa: A002  (shadow built-in)
            self.type = type
            self.text = text


# Import-isolated fallback mapping, used only when this module is loaded
# without its package (a bare unit-test import). It is a small slice of the
# *real* mapping — same names, same verified csv_names, same verified column
# ids — never synthesized filler, so anything derived from it stays truthful
# even though it is incomplete. A previous version invented 128 entries with
# csv_names ("EPS Q/Q", "Dividend %") that do not exist in any Finviz export.
_FALLBACK_FIELD_MAPPING = {
    "ticker": {"csv_name": "Ticker", "column_id": 1},
    "company": {"csv_name": "Company", "column_id": 2},
    "sector": {"csv_name": "Sector", "column_id": 3},
    "industry": {"csv_name": "Industry", "column_id": 4},
    "country": {"csv_name": "Country", "column_id": 5},
    "market_cap": {"csv_name": "Market Cap", "column_id": 6},
    "pe_ratio": {"csv_name": "P/E", "column_id": 7},
    "pb_ratio": {"csv_name": "P/B", "column_id": 11},
    "dividend_yield": {"csv_name": "Dividend Yield", "column_id": 14},
    "eps_growth_this_y": {"csv_name": "EPS Growth This Year", "column_id": 17},
    "eps_growth_qtr": {
        "csv_name": "EPS Growth Quarter Over Quarter",
        "column_id": 22,
    },
    "sales_growth_qtr": {
        "csv_name": "Sales Growth Quarter Over Quarter",
        "column_id": 23,
    },
    "performance_1w": {"csv_name": "Performance (Week)", "column_id": 42},
    "performance_1m": {"csv_name": "Performance (Month)", "column_id": 43},
}

# Import field mapping from constants
try:
    from ..constants import FINVIZ_COMPREHENSIVE_FIELD_MAPPING
except ImportError:
    try:
        from constants import FINVIZ_COMPREHENSIVE_FIELD_MAPPING
    except ImportError:
        FINVIZ_COMPREHENSIVE_FIELD_MAPPING = dict(_FALLBACK_FIELD_MAPPING)


# The accepted-name set used by the real request path. ``validate_fields``
# must agree with it exactly — otherwise the discovery tool tells users that
# requests which actually work are invalid (aliases like ``net_margin``,
# result keys like ``p_e``/``eps_ttm``, derived keys like ``week_52_high``).
try:
    from ..utils.validators import (
        get_valid_data_field_names,
        resolve_canonical_field_name,
    )
except ImportError:  # pragma: no cover – import-isolated test context
    try:
        from utils.validators import (
            get_valid_data_field_names,
            resolve_canonical_field_name,
        )
    except ImportError:

        def get_valid_data_field_names() -> set:
            """Degraded fallback: mapping names only."""
            return set(FINVIZ_COMPREHENSIVE_FIELD_MAPPING.keys())

        def resolve_canonical_field_name(field: str) -> Optional[str]:
            """Degraded fallback: mapping names only."""
            return field if field in FINVIZ_COMPREHENSIVE_FIELD_MAPPING else None


# Common typos mapped to their corrections. Every *target* must itself be an
# accepted field name (``get_valid_data_field_names``) — a suggestion pointing
# at a field that does not exist is worse than no suggestion at all. The old
# table suggested ``sales_growth_this_y``, which exists nowhere.
_COMMON_CORRECTIONS = {
    "eps_yoy": "eps_growth_this_y",
    "sales_qtr_over_qtr": "sales_growth_qtr",
    "sales_growth_yoy": "sales_yoy_ttm",
    "div_yield": "dividend_yield",
    "market_capitalication": "market_cap",
    "pe": "pe_ratio",
    "pb": "pb_ratio",
    "ps": "ps_ratio",
}


# Ordered category definitions keyed by inclusive column_id range. These
# ranges mirror the section structure of FINVIZ_COMPREHENSIVE_FIELD_MAPPING, so
# each category's members are computed from the mapping itself rather than a
# hand-maintained sample list. This guarantees every field is listed exactly
# once and the output can never drift from the mapping.
_FIELD_CATEGORY_RANGES = [
    (0, 6, "📊", "Basic Information & Size"),
    (7, 15, "💰", "Valuation & Dividends"),
    (16, 23, "📈", "EPS, Sales & Growth"),
    (24, 31, "📋", "Shares, Ownership & Short Interest"),
    (32, 41, "🏦", "Returns, Solvency & Margins"),
    (42, 51, "🚀", "Performance & Volatility"),
    (52, 59, "🔧", "Technical Indicators"),
    (60, 69, "🎯", "Trading, Volume & Targets"),
    (70, 89, "💲", "Company Info, Quote & After-Hours"),
    (90, 99, "⚡", "Intraday Performance"),
    (100, 111, "🏢", "ETF Profile"),
    (112, 124, "💧", "ETF Flows & Returns"),
    (125, 137, "🧩", "Extremes, Surprises, Dividends Detail & News"),
    (138, 149, "🌱", "Long-Term Performance, Growth & Enterprise Value"),
]


# Short, user-facing aliases for the derived category names. Values must be
# names produced by ``_grouped_fields``; membership itself is never listed
# here. The previous hand-maintained whitelist named 11 fields that exist
# nowhere (``sma20``, ``expense_ratio``, ``float`` …) while omitting the real
# ones, so ``search_fields('sma', category='technical')`` found nothing.
_CATEGORY_ALIASES = {
    "basic": "Basic Information & Size",
    "size": "Basic Information & Size",
    "valuation": "Valuation & Dividends",
    "dividends": "Valuation & Dividends",
    "growth": "EPS, Sales & Growth",
    "earnings": "EPS, Sales & Growth",
    "ownership": "Shares, Ownership & Short Interest",
    "shares": "Shares, Ownership & Short Interest",
    "fundamental": "Returns, Solvency & Margins",
    "margins": "Returns, Solvency & Margins",
    "performance": "Performance & Volatility",
    "volatility": "Performance & Volatility",
    "technical": "Technical Indicators",
    "trading": "Trading, Volume & Targets",
    "volume": "Trading, Volume & Targets",
    "company": "Company Info, Quote & After-Hours",
    "quote": "Company Info, Quote & After-Hours",
    "intraday": "Intraday Performance",
    "etf": "ETF Profile",
    "etf_flows": "ETF Flows & Returns",
    "flows": "ETF Flows & Returns",
    "news": "Extremes, Surprises, Dividends Detail & News",
    "extremes": "Extremes, Surprises, Dividends Detail & News",
    "surprises": "Extremes, Surprises, Dividends Detail & News",
    "long_term": "Long-Term Performance, Growth & Enterprise Value",
    "enterprise_value": "Long-Term Performance, Growth & Enterprise Value",
}


def _normalize_category(value: str) -> str:
    """Fold a user-supplied category name for comparison."""
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def _resolve_category(value: str) -> Optional[str]:
    """Map a user-supplied category onto a derived category name.

    Accepts either a short alias (``technical``) or the full derived name
    (``Technical Indicators``), case-insensitively. Returns ``None`` when the
    name is not recognised — callers must report that rather than silently
    returning zero matches.
    """
    normalized = _normalize_category(value)

    if normalized in _CATEGORY_ALIASES:
        return _CATEGORY_ALIASES[normalized]

    for _, name, _ in _grouped_fields():
        if _normalize_category(name) == normalized:
            return name

    return None


def _field_category_map() -> dict:
    """field name -> derived category name, for every mapped field."""
    return {field: name for _, name, members in _grouped_fields() for field in members}


def _grouped_fields() -> List[tuple]:
    """Group every mapped field into an ordered category by column_id.

    Returns a list of ``(icon, name, fields)`` tuples where ``fields`` is the
    list of field names in that category, ordered by column position. Members
    are derived from ``FINVIZ_COMPREHENSIVE_FIELD_MAPPING``, so nothing is
    hand-listed and nothing is truncated.
    """
    # (column_id, field_name) ordered by column position. Fields lacking a
    # column_id sort last so they surface in the "Other" bucket.
    ordered = sorted(
        (info.get("column_id", 10_000), name)
        for name, info in FINVIZ_COMPREHENSIVE_FIELD_MAPPING.items()
    )

    groups: List[tuple] = []
    for lo, hi, icon, name in _FIELD_CATEGORY_RANGES:
        members = [f for (cid, f) in ordered if lo <= cid <= hi]
        groups.append((icon, name, members))

    # Surface anything outside the defined ranges instead of dropping it.
    covered = {f for _, _, members in groups for f in members}
    leftover = [f for (_, f) in ordered if f not in covered]
    if leftover:
        groups.append(("📦", "Other", leftover))

    return groups


def list_available_fields() -> List[TextContent]:
    """
    List all available data fields for stock fundamentals.

    Returns:
        Complete list of field names that can be used with
        get_stock_fundamentals and get_multiple_stocks_fundamentals
    """
    total_count = len(FINVIZ_COMPREHENSIVE_FIELD_MAPPING)

    # Build the output text — every field listed under its category, no
    # truncation.
    output_lines = [f"Available Data Fields ({total_count} total):", ""]

    for icon, name, members in _grouped_fields():
        output_lines.append(f"{icon} {name} ({len(members)} fields):")
        for field in members:
            output_lines.append(f"- {field}")
        output_lines.append("")

    # Add note about usage
    output_lines.extend(
        [
            "Usage:",
            "- Use field names directly in get_stock_fundamentals(ticker, data_fields=[...])",
            "- Use get_field_categories() to see the same fields grouped compactly",
            "- Use describe_field(field_name) for detailed field information",
            "- Use search_fields(keyword) to find specific fields",
        ]
    )

    return [TextContent(type="text", text="\n".join(output_lines))]


def get_field_categories() -> List[TextContent]:
    """
    Get available data fields organized by category.

    Returns:
        Fields grouped by column position in the Finviz export (valuation,
        performance, technical, ETF, etc.), with every field listed once.
    """
    # Build the output text — one line of comma-joined members per category,
    # computed from the mapping so nothing is truncated or stale.
    output_lines = ["Field Categories:", ""]

    for icon, name, members in _grouped_fields():
        output_lines.append(f"{icon} {name.upper()} ({len(members)} fields)")
        if members:
            output_lines.append(f"- {', '.join(members)}")
        output_lines.append("")

    return [TextContent(type="text", text="\n".join(output_lines))]


def describe_field(field_name: str) -> List[TextContent]:
    """
    Get detailed description and metadata for a specific field.

    Args:
        field_name: The field name to describe. Any name the tools accept
            works: a mapping key (``profit_margin``), an alias
            (``net_margin``, ``roi``) or a CSV result key (``p_e``,
            ``eps_ttm``) — all resolve to the same canonical field.

    Returns:
        Detailed field information including description, data type,
        format, and usage examples
    """
    # Resolve aliases / result keys to the canonical mapping key, using the
    # same tables the request path resolves against. Without this, names that
    # validate_fields reports as VALID were answered with "not found".
    canonical_name = resolve_canonical_field_name(field_name)

    if canonical_name is None:
        # Suggest similar fields
        similar_fields = []
        for existing_field in FINVIZ_COMPREHENSIVE_FIELD_MAPPING.keys():
            if (
                field_name.lower() in existing_field.lower()
                or existing_field.lower() in field_name.lower()
            ):
                similar_fields.append(existing_field)

        output_lines = [
            f"❌ Field '{field_name}' not found",
            "",
            "💡 Similar fields available:",
        ]

        if similar_fields:
            for field in similar_fields[:5]:
                output_lines.append(f"  • {field}")
        else:
            output_lines.append("  • No similar fields found")
            output_lines.append("  • Use search_fields() to find fields by keyword")

        return [TextContent(type="text", text="\n".join(output_lines))]

    requested_name = field_name
    field_name = canonical_name

    # Get field metadata
    field_info = FINVIZ_COMPREHENSIVE_FIELD_MAPPING[field_name]
    csv_name = field_info.get("csv_name", field_name)

    # Define field descriptions and metadata
    field_descriptions = {
        "pe_ratio": {
            "display_name": "Price-to-Earnings Ratio",
            "description": "The ratio of a company's current share price to its per-share earnings. Used to value a company relative to its earnings.",
            "format": "Decimal number (e.g., 15.2, 22.8)",
            "interpretation": {
                "low": "Low P/E (< 15): Potentially undervalued or slow growth",
                "medium": "Medium P/E (15-25): Fairly valued for moderate growth",
                "high": "High P/E (> 25): Growth expectations or overvalued",
            },
            "related_fields": ["forward_pe", "peg", "eps_ttm", "earnings_date"],
        },
        "dividend_yield": {
            "display_name": "Dividend Yield",
            "description": "Annual dividend payment as a percentage of the stock price. Indicates income potential from dividends.",
            "format": "Percentage (e.g., 2.5%, 4.1%)",
            "interpretation": {
                "low": "0-2%: Growth companies, low income",
                "medium": "2-4%: Balanced income and growth",
                "high": "4%+: High income, mature companies",
            },
            "related_fields": ["dividend", "payout_ratio", "dividend_growth_1y"],
        },
        "market_cap": {
            "display_name": "Market Capitalization",
            "description": "Total value of a company's shares in the market. Key metric for company size classification.",
            "format": "Dollar amount (e.g., $50.2B, $1.5T)",
            "interpretation": {
                "small": "< $2B: Small-cap, higher risk/reward",
                "mid": "$2B-$10B: Mid-cap, balanced growth",
                "large": "> $10B: Large-cap, established companies",
            },
            "related_fields": ["shares_outstanding", "price", "shares_float"],
        },
        "earnings_date": {
            "display_name": "Earnings Date",
            "description": (
                "Earnings report date as published by Finviz. This is the "
                "next scheduled report when one has been announced; "
                "otherwise it is the most recent (past) report date. Do "
                "not assume it is always forward-looking — check whether "
                "the date is in the future before scheduling on it."
            ),
            "format": "Date/time (e.g., 5/27/2026 4:30:00 PM)",
            "interpretation": {
                "future": "Date in the future: next confirmed report",
                "past": "Date in the past: last report; next not yet scheduled",
            },
            "related_fields": ["eps_surprise", "revenue_surprise", "eps_next_q"],
        },
        "eps_growth_qtr": {
            "display_name": "EPS Growth Quarter Over Quarter",
            "description": (
                "Quarterly earnings-per-share growth as published by Finviz "
                "in its 'EPS Growth Quarter Over Quarter' column. Shows "
                "short-term earnings momentum. Consult Finviz for the exact "
                "comparison base before using it in a screen."
            ),
            "format": "Percentage (e.g., 15.3%, -5.2%)",
            "interpretation": {
                "positive": "> 0%: Growing earnings, positive momentum",
                "negative": "< 0%: Declining earnings, potential concerns",
                "high": "> 20%: Strong growth, verify sustainability",
            },
            "related_fields": ["eps_ttm", "eps_growth_this_y", "sales_growth_qtr"],
        },
    }

    # Get description or create default
    if field_name in field_descriptions:
        desc = field_descriptions[field_name]
    else:
        # Create basic description for fields without curated copy
        desc = {
            "display_name": csv_name,
            "description": f"Financial data field: {csv_name}",
            "format": "Various formats depending on data type",
            "interpretation": {
                "note": "Refer to Finviz documentation for specific details"
            },
            "related_fields": [],
        }

    # The category comes from the same derived grouping list_available_fields,
    # get_field_categories and search_fields use — never a hand-written label,
    # which used to put 144 of 150 fields in "Other".
    category = _field_category_map().get(field_name, "Other")

    # Build detailed output
    output_lines = [
        f"📊 Field Description: {field_name}",
        "=" * 50,
        "",
        "📋 Basic Info:",
        f"  • Display Name: {desc['display_name']}",
        f"  • Category: {category}",
        f"  • CSV Column: {csv_name}",
    ]

    if requested_name != field_name:
        output_lines.append(
            f"  • Requested As: {requested_name} "
            f"(alias/result key for {field_name})"
        )

    output_lines.append("")
    output_lines.extend(
        [
            "📖 Description:",
            f"  {desc['description']}",
            "",
            "🔧 Format:",
            f"  {desc['format']}",
            "",
        ]
    )

    # Add interpretation section
    if "interpretation" in desc and desc["interpretation"]:
        output_lines.append("💡 Usage Examples:")
        for key, value in desc["interpretation"].items():
            output_lines.append(f"  • {value}")
        output_lines.append("")

    # Add related fields
    if desc.get("related_fields"):
        output_lines.append("🔗 Related Fields:")
        for related in desc["related_fields"]:
            output_lines.append(f"  • {related}")
        output_lines.append("")

    # Add usage note
    output_lines.extend(
        [
            "📝 Usage:",
            f"  get_stock_fundamentals('AAPL', data_fields=['{field_name}'])",
            "",
            "💡 Tip: Use search_fields('{keyword}') to find similar fields",
        ]
    )

    return [TextContent(type="text", text="\n".join(output_lines))]


def search_fields(keyword: str, category: Optional[str] = None) -> List[TextContent]:
    """
    Search for fields matching a keyword or pattern.

    Args:
        keyword: Search term (e.g., "growth", "ratio", "performance")
        category: Optional category filter. Accepts either a short alias —
            basic, valuation, growth (earnings), ownership, fundamental,
            performance, technical, trading, company, intraday, etf,
            etf_flows, news, long_term — or the full category name as
            shown by get_field_categories() (e.g. "Technical Indicators"),
            case-insensitively. Membership matches
            list_available_fields()/get_field_categories() exactly. An
            unrecognised name is reported as an error, never as "no matches".

    Returns:
        Matching fields with descriptions
    """
    # Handle empty search
    if not keyword or not keyword.strip():
        return [
            TextContent(
                type="text",
                text="❌ No search term provided. Please provide a keyword.\n\n💡 Example: search_fields('growth')",
            )
        ]

    keyword_lower = keyword.strip().lower()
    all_fields = list(FINVIZ_COMPREHENSIVE_FIELD_MAPPING.keys())

    # Resolve the category filter against the *derived* categories, so a
    # filter can never exclude a field that list_available_fields shows in
    # that category.
    resolved_category = None
    if category and category.strip():
        resolved_category = _resolve_category(category)
        if resolved_category is None:
            derived_names = [name for _, name, _ in _grouped_fields()]
            output_lines = [
                f"❌ Unknown category '{category}'",
                "",
                "📂 Valid categories (full name — short alias):",
            ]
            aliases_by_name = {}
            for alias, name in _CATEGORY_ALIASES.items():
                aliases_by_name.setdefault(name, []).append(alias)
            for name in derived_names:
                aliases = ", ".join(sorted(aliases_by_name.get(name, []))) or "—"
                output_lines.append(f"  • {name} — {aliases}")
            output_lines.extend(
                [
                    "",
                    "💡 Use get_field_categories() to see the members of each category,",
                    "   or search_fields(keyword) without a category filter.",
                ]
            )
            return [TextContent(type="text", text="\n".join(output_lines))]

    field_categories = _field_category_map()

    # Find matching fields
    matching_fields = []

    # Search in field names
    for field in all_fields:
        if keyword_lower in field.lower():
            matching_fields.append(field)

    # Search in CSV names (display names)
    for field, field_info in FINVIZ_COMPREHENSIVE_FIELD_MAPPING.items():
        csv_name = field_info.get("csv_name", "")
        if keyword_lower in csv_name.lower() and field not in matching_fields:
            matching_fields.append(field)

    # Apply category filter if provided
    if resolved_category:
        matching_fields = [
            f for f in matching_fields if field_categories.get(f) == resolved_category
        ]

    # Build output
    if not matching_fields:
        output_lines = [f"❌ No matches found for '{keyword}'", ""]

        if resolved_category:
            output_lines.append(f"📂 Searched in category: {resolved_category}")
            output_lines.append("")

        output_lines.extend(
            [
                "💡 Suggestions:",
                "  • Try broader keywords (e.g., 'growth', 'ratio', 'performance')",
                "  • Check spelling",
                "  • Use list_available_fields() to see all fields",
                "  • Use get_field_categories() to browse by category",
            ]
        )

        return [TextContent(type="text", text="\n".join(output_lines))]

    # Build results
    output_lines = [
        f"🔍 Search Results for '{keyword_lower}' ({len(matching_fields)} matches):"
    ]

    if resolved_category:
        output_lines.append(f"📂 Category: {resolved_category}")

    output_lines.append("")

    # Group results by their derived category — the same grouping
    # list_available_fields() and get_field_categories() display.
    categorized_results = {}
    for field in matching_fields:
        field_category = field_categories.get(field, "Other")
        categorized_results.setdefault(field_category, []).append(field)

    # Output results by category
    for cat_name, fields in categorized_results.items():
        if (
            len(categorized_results) > 1
        ):  # Only show category headers if multiple categories
            output_lines.append(f"📊 {cat_name}:")

        for field in sorted(fields):
            # Get display name
            field_info = FINVIZ_COMPREHENSIVE_FIELD_MAPPING.get(field, {})
            csv_name = field_info.get("csv_name", field)

            output_lines.append(f"  • {field}")
            if csv_name != field:
                output_lines.append(f"    ↳ Display: {csv_name}")

        if len(categorized_results) > 1:
            output_lines.append("")

    # Add usage note
    output_lines.extend(
        [
            "📝 Usage:",
            "  • describe_field('field_name') - Get detailed info",
            "  • get_stock_fundamentals('AAPL', data_fields=['field_name'])",
            "",
            "💡 Tip: Use category filter like search_fields('ratio', category='valuation')",
        ]
    )

    return [TextContent(type="text", text="\n".join(output_lines))]


def validate_fields(field_names: List[str]) -> List[TextContent]:
    """
    Validate a list of field names and suggest corrections.

    Args:
        field_names: List of field names to validate

    Returns:
        Validation results with suggestions for invalid fields
    """
    # Handle empty list
    if not field_names:
        return [
            TextContent(
                type="text",
                text="❌ No fields provided.\n\n💡 Example: validate_fields(['ticker', 'pe_ratio'])",
            )
        ]

    # Accept exactly what the request path accepts (mapping names + aliases +
    # normalized CSV result keys + derived keys), not just the public mapping.
    all_fields = get_valid_data_field_names()
    valid_fields = []
    invalid_fields = []
    suggestions = {}

    common_corrections = _COMMON_CORRECTIONS

    # Validate each field
    for field in field_names:
        if field in all_fields:
            valid_fields.append(field)
        else:
            invalid_fields.append(field)

            # Find suggestions
            suggestion = None

            # Check common corrections first
            if field in common_corrections:
                suggestion = common_corrections[field]
            else:
                # Find similar field names. Sorted so the suggestion is
                # deterministic; substring matches first, then edit-distance
                # matches. A mere length coincidence is not a suggestion —
                # the old heuristic answered "bogus_thing_xyz" with an
                # unrelated field of similar length.
                field_lower = field.lower()
                ordered_fields = sorted(all_fields)
                substring_matches = [
                    existing
                    for existing in ordered_fields
                    if field_lower in existing.lower()
                    or existing.lower() in field_lower
                ]
                # Rank substring hits by similarity, not alphabetically —
                # otherwise the "best match" for `eps_growth_qtr_typo` is
                # whatever generic prefix sorts first (`eps`).
                substring_matches.sort(
                    key=lambda existing: (
                        -difflib.SequenceMatcher(
                            None, field_lower, existing.lower()
                        ).ratio(),
                        existing,
                    )
                )

                similar_fields = substring_matches or difflib.get_close_matches(
                    field_lower, ordered_fields, n=1, cutoff=0.6
                )
                if similar_fields:
                    suggestion = similar_fields[0]  # Take the best match

            if suggestion:
                suggestions[field] = suggestion

    # Build output
    output_lines = [
        f"✅ Field Validation Results ({len(field_names)} fields checked):",
        "",
    ]

    # Valid fields section
    if valid_fields:
        output_lines.extend([f"✅ VALID FIELDS ({len(valid_fields)}):", ""])
        for field in valid_fields:
            field_info = FINVIZ_COMPREHENSIVE_FIELD_MAPPING.get(field, {})
            csv_name = field_info.get("csv_name", field)
            output_lines.append(f"  ✓ {field}")
            if csv_name != field:
                output_lines.append(f"    ↳ Display: {csv_name}")
        output_lines.append("")

    # Invalid fields section
    if invalid_fields:
        output_lines.extend([f"❌ INVALID FIELDS ({len(invalid_fields)}):", ""])
        for field in invalid_fields:
            output_lines.append(f"  ✗ {field}")
            if field in suggestions:
                output_lines.append(f"    → Did you mean: {suggestions[field]}")
            else:
                output_lines.append("    → No suggestions found")
        output_lines.append("")

    # Summary and guidance
    if invalid_fields:
        output_lines.extend(
            [
                "💡 SUGGESTIONS:",
                "  • Double-check field names for typos",
                "  • Use search_fields('keyword') to find correct names",
                "  • Use list_available_fields() to see all options",
                "  • Common patterns:",
                "    - Growth metrics: eps_growth_qtr, sales_growth_qtr",
                "    - Performance: performance_1w, performance_1m",
                "    - Ratios: pe_ratio, pb_ratio, ps_ratio",
                "",
                "📚 Yearly growth fields use '_this_y' suffix",
                "📅 Quarterly growth fields use '_qtr' suffix",
                "",
            ]
        )

    # Usage examples
    if valid_fields:
        sample_field = valid_fields[0]
        output_lines.extend(
            [
                "📝 Usage with valid fields:",
                f"  get_stock_fundamentals('AAPL', data_fields={valid_fields[:3]})",
                "",
                f"💡 Get details: describe_field('{sample_field}')",
            ]
        )

    return [TextContent(type="text", text="\n".join(output_lines))]


def register_field_discovery_tools(server):
    """Register all field discovery tools with the MCP server"""
    server.tool()(list_available_fields)
    server.tool()(get_field_categories)
    server.tool()(describe_field)
    server.tool()(search_fields)
    server.tool()(validate_fields)
