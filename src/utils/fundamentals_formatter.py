"""Complete, declarative rendering for fundamentals result dicts.

The fundamentals tools historically rendered a hand-picked subset of the
result dict: every key not named in a display bucket was fetched, counted in
"Data Coverage", echoed in "All Available Fields" — and never shown. That
made whole families invisible (after-hours quotes, intraday performance, the
entire ETF profile) while the coverage line reported near-perfect numbers.

This module is the single source of truth for how a fundamentals dict is
displayed:

* ``SECTIONS`` assigns every known result key a section, a label and a
  format. A completeness test pins that every key the client can produce is
  either listed here or deliberately skipped.
* ``format_fundamentals`` renders all non-null values, and appends a
  catch-all "Other Fields" section for any key this spec doesn't know yet —
  a new Finviz column can never be silently dropped.
* When the caller explicitly requested fields (``data_fields``), keys that
  came back null are rendered as ``N/A (no data from Finviz)`` instead of
  vanishing, and the coverage line counts *rendered values*, not accepted
  field names.
"""

from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

# Keys that are rendered in the report header rather than as data lines.
HEADER_KEYS = {"ticker", "no"}

# Format kinds:
#   text            value as-is
#   num             2-decimal float (falls back to str)
#   signed          +/- prefixed 2-decimal float (percent-like)
#   price           $ prefixed 2-decimal float
#   int             thousands-separated integer
#   millions_money  value stored in $ millions -> $x.xxT/B/M
#   millions_shares value stored in millions of shares -> x.xxB/M
#   money_raw       value stored in raw dollars -> $x.xxT/B/M
SECTIONS: List[Tuple[str, List[Tuple[str, str, str]]]] = [
    (
        "📋 Basic Information",
        [
            ("Company", "company", "text"),
            ("Sector", "sector", "text"),
            ("Industry", "industry", "text"),
            ("Country", "country", "text"),
            ("Exchange", "exchange", "text"),
            ("Index", "index", "text"),
            ("Market Cap", "market_cap", "millions_money"),
            ("Employees", "employees", "int"),
            ("IPO Date", "ipo_date", "text"),
        ],
    ),
    (
        "💲 Price & Trading",
        [
            ("Price", "price", "price"),
            ("Prev Close", "prev_close", "price"),
            ("Open", "open", "price"),
            ("High", "high", "price"),
            ("Low", "low", "price"),
            ("1D Change (%)", "change", "signed"),
            ("Change from Open (%)", "change_from_open", "signed"),
            ("Gap (%)", "gap", "signed"),
            ("52W Range", "52_week_range", "text"),
            ("Volume", "volume", "int"),
            ("Avg Volume", "average_volume", "int"),
            ("Relative Volume", "relative_volume", "num"),
            ("Trades", "trades", "int"),
            ("Optionable", "optionable", "text"),
            ("Shortable", "shortable", "text"),
        ],
    ),
    (
        "🌙 After-Hours",
        [
            ("AH Close", "after_hours_close", "price"),
            ("AH Change (%)", "after_hours_change", "signed"),
            ("AH Volume", "after_hours_volume", "int"),
        ],
    ),
    (
        "🎯 Analyst & Price Target",
        [
            ("Target Price", "target_price", "price"),
            ("Analyst Recom", "analyst_recom", "num"),
        ],
    ),
    (
        "💰 Valuation Metrics",
        [
            ("P/E Ratio", "p_e", "num"),
            ("Forward P/E", "forward_p_e", "num"),
            ("PEG", "peg", "num"),
            ("P/S Ratio", "p_s", "num"),
            ("P/B Ratio", "p_b", "num"),
            ("P/C Ratio", "p_cash", "num"),
            ("P/FCF", "p_free_cash_flow", "num"),
            ("EV/EBITDA", "ev_ebitda", "num"),
            ("EV/Sales", "ev_sales", "num"),
            ("EPS (ttm)", "eps_ttm", "num"),
        ],
    ),
    (
        "🏢 Company Financials",
        [
            ("Income", "income", "millions_money"),
            ("Sales", "sales", "millions_money"),
            ("Enterprise Value", "enterprise_value", "millions_money"),
            ("Book/sh", "book_sh", "price"),
            ("Cash/sh", "cash_sh", "price"),
        ],
    ),
    (
        "🏦 Financial Health",
        [
            ("Quick Ratio", "quick_ratio", "num"),
            ("Current Ratio", "current_ratio", "num"),
            ("Debt/Equity", "total_debt_equity", "num"),
            ("LT Debt/Equity", "lt_debt_equity", "num"),
        ],
    ),
    (
        "💵 Profitability",
        [
            ("Gross Margin (%)", "gross_margin", "num"),
            ("Operating Margin (%)", "operating_margin", "num"),
            ("Profit Margin (%)", "profit_margin", "num"),
        ],
    ),
    (
        "💹 Returns (ROE/ROA/ROIC)",
        [
            ("ROE (%)", "return_on_equity", "num"),
            ("ROA (%)", "return_on_assets", "num"),
            ("ROIC (%)", "return_on_invested_capital", "num"),
        ],
    ),
    (
        "🌱 Growth",
        [
            ("EPS Next Q ($)", "eps_next_q", "num"),
            ("EPS Growth This Y (%)", "eps_growth_this_year", "signed"),
            ("EPS Growth Next Y (%)", "eps_growth_next_year", "signed"),
            ("EPS Growth Past 3Y (%)", "eps_growth_past_3_years", "signed"),
            ("EPS Growth Past 5Y (%)", "eps_growth_past_5_years", "signed"),
            ("EPS Growth Next 5Y (%)", "eps_growth_next_5_years", "signed"),
            ("EPS Growth QoQ (%)", "eps_growth_quarter_over_quarter", "signed"),
            ("EPS YoY TTM (%)", "eps_year_over_year_ttm", "signed"),
            ("Sales Growth Past 3Y (%)", "sales_growth_past_3_years", "signed"),
            ("Sales Growth Past 5Y (%)", "sales_growth_past_5_years", "signed"),
            ("Sales Growth QoQ (%)", "sales_growth_quarter_over_quarter", "signed"),
            ("Sales YoY TTM (%)", "sales_year_over_year_ttm", "signed"),
        ],
    ),
    (
        "📊 Earnings",
        [
            # Finviz reports the next scheduled earnings date when one is
            # announced, otherwise the most recent report date.
            ("Earnings Date", "earnings_date", "text"),
            ("EPS Surprise (%)", "eps_surprise", "signed"),
            ("Revenue Surprise (%)", "revenue_surprise", "signed"),
        ],
    ),
    (
        "💸 Dividends",
        [
            ("Dividend", "dividend", "price"),
            ("Dividend TTM", "dividend_ttm", "price"),
            ("Dividend Yield (%)", "dividend_yield", "num"),
            ("Ex-Date", "dividend_ex_date", "text"),
            ("Payout (%)", "payout_ratio", "num"),
            ("Div Growth 1Y (%)", "dividend_growth_1_year", "signed"),
            ("Div Growth 3Y (%)", "dividend_growth_3_years", "signed"),
            ("Div Growth 5Y (%)", "dividend_growth_5_years", "signed"),
        ],
    ),
    (
        "👥 Ownership & Short Interest",
        [
            ("Insider Own (%)", "insider_ownership", "num"),
            ("Insider Trans (%)", "insider_transactions", "signed"),
            ("Inst Own (%)", "institutional_ownership", "num"),
            ("Inst Trans (%)", "institutional_transactions", "signed"),
            ("Short Float (%)", "short_float", "num"),
            ("Short Ratio", "short_ratio", "num"),
            ("Short Interest", "short_interest", "millions_shares"),
            ("Shs Outstanding", "shares_outstanding", "millions_shares"),
            ("Shs Float", "shares_float", "millions_shares"),
            ("Float (%)", "float_percent", "num"),
        ],
    ),
    (
        "⚡ Intraday Performance",
        [
            ("1 Min (%)", "performance_1_minute", "signed"),
            ("2 Min (%)", "performance_2_minutes", "signed"),
            ("3 Min (%)", "performance_3_minutes", "signed"),
            ("5 Min (%)", "performance_5_minutes", "signed"),
            ("10 Min (%)", "performance_10_minutes", "signed"),
            ("15 Min (%)", "performance_15_minutes", "signed"),
            ("30 Min (%)", "performance_30_minutes", "signed"),
            ("1 Hour (%)", "performance_1_hour", "signed"),
            ("2 Hours (%)", "performance_2_hours", "signed"),
            ("4 Hours (%)", "performance_4_hours", "signed"),
        ],
    ),
    (
        "📈 Performance",
        [
            ("1 Week (%)", "performance_week", "signed"),
            ("1 Month (%)", "performance_month", "signed"),
            ("3 Months (%)", "performance_quarter", "signed"),
            ("6 Months (%)", "performance_half_year", "signed"),
            ("YTD (%)", "performance_ytd", "signed"),
            ("1 Year (%)", "performance_year", "signed"),
            ("3 Years (%)", "performance_3_years", "signed"),
            ("5 Years (%)", "performance_5_years", "signed"),
            ("10 Years (%)", "performance_10_years", "signed"),
        ],
    ),
    (
        "🔧 Technical Indicators",
        [
            ("RSI (14)", "relative_strength_index_14", "num"),
            ("Beta", "beta", "num"),
            ("ATR", "average_true_range", "num"),
            ("Volatility W (%)", "volatility_week", "num"),
            ("Volatility M (%)", "volatility_month", "num"),
            ("20D SMA (%)", "20_day_simple_moving_average", "signed"),
            ("50D SMA (%)", "50_day_simple_moving_average", "signed"),
            ("200D SMA (%)", "200_day_simple_moving_average", "signed"),
            ("50D High Dist (%)", "50_day_high", "signed"),
            ("50D Low Dist (%)", "50_day_low", "signed"),
            ("52W High Dist (%)", "52_week_high", "signed"),
            ("52W Low Dist (%)", "52_week_low", "signed"),
            ("52W High", "week_52_high", "price"),
            ("52W Low", "week_52_low", "price"),
            ("ATH Dist (%)", "all_time_high", "signed"),
            ("ATL Dist (%)", "all_time_low", "signed"),
        ],
    ),
    (
        "🗂️ ETF Profile",
        [
            ("Asset Type", "asset_type", "text"),
            ("ETF Type", "etf_type", "text"),
            ("Category", "single_category", "text"),
            ("Sector/Theme", "sector_theme", "text"),
            ("Region", "region", "text"),
            ("Active/Passive", "active_passive", "text"),
            ("Tags", "tags", "text"),
            ("Net Expense Ratio (%)", "net_expense_ratio", "num"),
            ("Total Holdings", "total_holdings", "int"),
            ("AUM", "assets_under_management", "money_raw"),
            ("NAV", "net_asset_value", "price"),
            ("NAV Change (%)", "net_asset_value_percent", "signed"),
        ],
    ),
    (
        "💧 ETF Fund Flows",
        [
            ("Flows 1M", "net_flows_1_month", "money_raw"),
            ("Flows 1M (%)", "net_flows_percent_1_month", "signed"),
            ("Flows 3M", "net_flows_3_month", "money_raw"),
            ("Flows 3M (%)", "net_flows_percent_3_month", "signed"),
            ("Flows YTD", "net_flows_ytd", "money_raw"),
            ("Flows YTD (%)", "net_flows_percent_ytd", "signed"),
            ("Flows 1Y", "net_flows_1_year", "money_raw"),
            ("Flows 1Y (%)", "net_flows_percent_1_year", "signed"),
        ],
    ),
    (
        "🏆 ETF Annualized Returns",
        [
            ("Return 1Y (%)", "return_1_year", "signed"),
            ("Return 3Y (%)", "return_3_year", "signed"),
            ("Return 5Y (%)", "return_5_year", "signed"),
            ("Return 10Y (%)", "return_10_year", "signed"),
            ("Since Inception (%)", "return_since_inception", "signed"),
        ],
    ),
    (
        "📰 Latest News",
        [
            ("Time", "news_time", "text"),
            ("Title", "news_title", "text"),
            ("URL", "news_url", "text"),
        ],
    ),
]

#: Every result key the section spec knows how to display.
KNOWN_KEYS: Set[str] = {key for _, fields in SECTIONS for _, key, _ in fields}


def _as_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _fmt_scaled_money(dollars: float) -> str:
    sign = "-" if dollars < 0 else ""
    n = abs(dollars)
    if n >= 1e12:
        return f"{sign}${n / 1e12:.2f}T"
    if n >= 1e9:
        return f"{sign}${n / 1e9:.2f}B"
    if n >= 1e6:
        return f"{sign}${n / 1e6:.2f}M"
    return f"{sign}${n:,.0f}"


def format_value(value: Any, kind: str) -> str:
    """Format one value per its declared kind, degrading to ``str(value)``."""
    if kind == "text":
        return str(value)
    n = _as_float(value)
    if n is None:
        return str(value)
    if kind == "num":
        return f"{n:.2f}"
    if kind == "signed":
        return f"{n:+.2f}"
    if kind == "price":
        return f"${n:.2f}"
    if kind == "int":
        return f"{int(n):,}"
    if kind == "millions_money":
        return _fmt_scaled_money(n * 1e6)
    if kind == "millions_shares":
        return _fmt_scaled_money(n * 1e6).replace("$", "")
    if kind == "money_raw":
        return _fmt_scaled_money(n)
    return str(value)


def format_fundamentals(
    data: Dict[str, Any],
    requested_fields: Optional[Iterable[str]] = None,
    label_width: int = 24,
) -> List[str]:
    """Render a fundamentals result dict as display lines.

    * Every non-null key is rendered — either in its section or in the
      catch-all "Other Fields" section.
    * With ``requested_fields`` (explicit ``data_fields`` mode), null keys
      are rendered as ``N/A (no data from Finviz)`` so a miss is visible.
      In default (all-fields) mode null keys are skipped to avoid noise.
    * The coverage footer counts values actually rendered, and the field
      echo lists only keys that carry a value.
    """
    explicit = requested_fields is not None
    lines: List[str] = []
    rendered = 0

    def emit(section_lines: List[str], title: str) -> None:
        nonlocal lines
        if section_lines:
            lines.extend([f"{title}:", "-" * 30, *section_lines, ""])

    consumed: Set[str] = set(HEADER_KEYS)
    for title, fields in SECTIONS:
        section_lines: List[str] = []
        for label, key, kind in fields:
            if key not in data:
                continue
            consumed.add(key)
            value = data[key]
            if value is None:
                if explicit:
                    section_lines.append(
                        f"{label:{label_width}}: N/A (no data from Finviz)"
                    )
                continue
            section_lines.append(
                f"{label:{label_width}}: {format_value(value, kind)}"
            )
            rendered += 1
        emit(section_lines, title)

    # Catch-all: keys this spec doesn't know yet must still surface.
    other_lines: List[str] = []
    for key in sorted(set(data) - consumed):
        value = data[key]
        if value is None:
            if explicit:
                other_lines.append(
                    f"{key:{label_width}}: N/A (no data from Finviz)"
                )
            continue
        other_lines.append(f"{key:{label_width}}: {value}")
        rendered += 1
    emit(other_lines, "📦 Other Fields")

    total = len(data)
    populated = sorted(k for k, v in data.items() if v is not None)
    pct = (rendered / total * 100) if total else 0.0
    lines.append(
        f"📋 Data Coverage: {rendered}/{total} fields rendered ({pct:.1f}%)"
    )
    if explicit:
        missing = sorted(
            k for k, v in data.items() if v is None and k not in HEADER_KEYS
        )
        if missing:
            lines.append(
                "⚠️ No data from Finviz for: " + ", ".join(missing)
            )
    lines.append("🔍 Fields with values: " + ", ".join(populated))
    return lines


def compact_fundamentals(
    data: Dict[str, Any],
    skip_keys: Optional[Set[str]] = None,
) -> List[str]:
    """Compact per-section ``label=value`` lines for the multi-stock view.

    Renders the same complete section spec, one line per section, skipping
    null values (and ``skip_keys`` already shown elsewhere).
    """
    skip = HEADER_KEYS | (skip_keys or set())
    lines: List[str] = []
    consumed: Set[str] = set(skip)
    for title, fields in SECTIONS:
        parts = []
        for label, key, kind in fields:
            consumed.add(key)
            if key in skip:
                continue
            value = data.get(key)
            if value is None:
                continue
            parts.append(f"{label}={format_value(value, kind)}")
        if parts:
            lines.append(f"  {title}: " + ", ".join(parts))
    other = [
        f"{key}={data[key]}"
        for key in sorted(set(data) - consumed)
        if data[key] is not None
    ]
    if other:
        lines.append("  📦 Other: " + ", ".join(other))
    return lines
