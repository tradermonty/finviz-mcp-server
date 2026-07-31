#!/usr/bin/env python3
import logging
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent

from .field_discovery.tools import register_field_discovery_tools
from .finviz_client.base import FinvizClient
from .finviz_client.news import EASTERN, FinvizNewsClient
from .finviz_client.screener import FinvizScreener
from .finviz_client.sec_filings import FinvizSECFilingsClient
from .finviz_client.sector_analysis import FinvizSectorAnalysisClient
from .models import MARKET_CAP_FILTERS, NewsData
from .utils.exceptions import FinvizAPIError
from .utils.formatters import format_large_number
from .utils.fundamentals_formatter import compact_fundamentals, format_fundamentals
from .utils.validators import (
    validate_and_normalize_raw_filters,
    validate_data_fields,
    validate_earnings_date,
    validate_market_cap,
    validate_price_range,
    validate_raw_sort_order,
    validate_sector,
    validate_signal,
    validate_ticker,
    validate_volume,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

server = FastMCP("Finviz MCP Server")

# Initialize Finviz clients
finviz_api_key = os.getenv("FINVIZ_API_KEY")
finviz_client = FinvizClient(api_key=finviz_api_key)
finviz_screener = FinvizScreener(api_key=finviz_api_key)
finviz_news = FinvizNewsClient(api_key=finviz_api_key)
finviz_sector = FinvizSectorAnalysisClient(api_key=finviz_api_key)
finviz_sec = FinvizSECFilingsClient(api_key=finviz_api_key)

# EDGAR API client — lazy-initialized to keep ``import server`` cheap and to
# avoid hard-coupling unrelated tools (Finviz SEC listing tools never touch
# this client). Initialization requires ``EDGAR_USER_AGENT``; SEC requires a
# non-empty User-Agent header on every request.
# See https://www.sec.gov/os/accessing-edgar-data
_edgar_client: Optional[Any] = None


def _format_filter_value(key: str, value: Any) -> str:
    """Render one internal filter value the way a caller would read it."""
    if isinstance(value, bool):
        return "yes" if value else "no"
    if key == "market_cap":
        return f"{MARKET_CAP_FILTERS.get(value, value)} (cap_{value})"
    # Exact keys only: ``startswith("price")`` also caught
    # price_change_min/max and rendered "2.0% change" as "$2.0".
    if key in ("price_min", "price_max"):
        return f"${value}"
    if key.endswith(("volume_min", "volume_max")):
        if isinstance(value, (int, float)):
            return f"{int(value):,} shares"
        # Finviz volume tokens count thousands of shares; spell that out
        # rather than echoing "o500" at the caller.
        token = re.fullmatch(r"([ou])(\d+(?:\.\d+)?)", str(value))
        if token:
            shares = int(float(token.group(2)) * 1000)
            comparator = "at least" if token.group(1) == "o" else "at most"
            return f"{comparator} {shares:,} shares ({value})"
        span = re.fullmatch(r"(\d+(?:\.\d+)?)to(\d+(?:\.\d+)?)", str(value))
        if span:
            low = int(float(span.group(1)) * 1000)
            high = int(float(span.group(2)) * 1000)
            return f"{low:,} - {high:,} shares ({value})"
    if isinstance(value, (list, tuple)):
        return ", ".join(str(item) for item in value)
    if isinstance(value, dict):
        return ", ".join(f"{k}={v}" for k, v in value.items())
    return str(value)


# Internal filter key -> the label a caller sees. Anything not listed still
# gets printed (as "key: value"): a criteria block must never be able to hide
# a filter that actually ran.
_FILTER_LABELS = {
    "market_cap": "Market cap",
    "price_min": "Min price",
    "price_max": "Max price",
    "volume_min": "Min volume (today)",
    "volume_max": "Max volume (today)",
    "avg_volume_min": "Min average volume",
    "avg_volume_max": "Max average volume",
    "relative_volume_min": "Min relative volume",
    "price_change_min": "Min price change (%)",
    "price_change_max": "Max price change (%)",
    "price_change_positive": "Price change positive",
    "afterhours_change_min": "Min after-hours change (%)",
    "rsi_min": "Min RSI",
    "rsi_max": "Max RSI",
    "pe_ratio_max": "Max P/E",
    "pb_ratio_max": "Max P/B",
    "roe_min": "Min ROE (%)",
    "debt_equity_max": "Max total debt/equity",
    "payout_ratio_min": "Min payout ratio (%)",
    "payout_ratio_max": "Max payout ratio (%)",
    "dividend_yield_min": "Min dividend yield (%)",
    "dividend_yield_max": "Max dividend yield (%)",
    "eps_growth_5y_positive": "EPS growth past 5Y positive",
    "eps_growth_qoq_positive": "EPS growth Q/Q positive",
    "eps_growth_yoy_positive": "EPS growth this year positive",
    "sales_growth_5y_positive": "Sales growth past 5Y positive",
    "sales_growth_qoq_positive": "Sales growth Q/Q positive",
    "eps_growth_qoq_min": "Min EPS growth Q/Q (%)",
    "eps_revision_min": "Min EPS revision (%)",
    "sales_growth_qoq_min": "Min sales growth Q/Q (%)",
    "net_margin_min": "Min net margin (%)",
    "weekly_performance": "Weekly performance filter",
    "performance_4w_positive": "4-week performance up",
    "performance_4w_range": "4-week performance range",
    "volatility_min": "Min volatility",
    "near_52w_high": "Within % of 52-week high",
    "sma20_above": "Price above SMA20",
    "sma50_above": "Price above SMA50",
    "sma200_above": "Price above SMA200",
    "sma20_below": "Price below SMA20",
    "sma50_below": "Price below SMA50",
    "sma200_below": "Price below SMA200",
    "sma50_above_sma200": "SMA50 above SMA200",
    "sectors": "Sectors",
    "country": "Country",
    "instrument_type": "Instrument type",
    "earnings_date": "Earnings date",
    "earnings_recent": "Earnings just reported (yesterday PM / today AM)",
    "earnings_revision_positive": "EPS estimate revised up",
    "exclude_etfs": "Exclude ETFs",
}

# Keys that steer the request but are not screening criteria.
_NON_CRITERIA_KEYS = {
    "sort_by",
    "sort_order",
    "max_results",
    "screener_type",
    "stocks_only",
}


def _format_sma_line(
    label: str, absolute: Optional[float], relative: Optional[float]
) -> str:
    """Render an SMA with its real units: derived dollar price + % distance.

    ``StockData.sma_20/50/200`` are absolute prices derived from the CSV's
    percent-distance columns; the distance itself is the ``*_relative`` twin.
    """
    if absolute is None and relative is None:
        return f"{label}: N/A"
    parts = []
    if absolute is not None:
        parts.append(f"${absolute:.2f}")
    if relative is not None:
        parts.append(f"({relative:+.2f}% vs price)")
    return f"{label}: " + " ".join(parts)


def _criteria_block(
    filters: Dict[str, Any],
    client: Optional[FinvizClient] = None,
    extra: Optional[List[str]] = None,
    title: str = "Screening criteria applied:",
) -> List[str]:
    """Render the criteria block straight from the filters that will run.

    Several tools used to print a hand-written block that had drifted from the
    query — earnings_screener printed earnings_trading's criteria, and the
    premarket/afterhours tools advertised "$10 / Small+" while filtering on
    $30 / Large+ (audit B12, B14, B2). Deriving the text from the filter dict
    (and echoing the exact ``f=`` token string) makes that drift impossible.
    """
    lines = [title]
    for key, value in filters.items():
        if key in _NON_CRITERIA_KEYS or value is None or value is False:
            continue
        label = _FILTER_LABELS.get(key, key)
        lines.append(f"- {label}: {_format_filter_value(key, value)}")

    for line in extra or []:
        lines.append(f"- {line}")

    if client is not None:
        try:
            tokens = client._convert_filters_to_finviz(filters).get("f", "")
        except Exception as exc:  # pragma: no cover - defensive only
            logger.warning("Could not render Finviz filter string: %s", exc)
            tokens = ""
        if tokens:
            lines.append(f"- Finviz query: f={tokens}")

    sort_by = filters.get("sort_by")
    if sort_by:
        lines.append(f"- Sort: {sort_by} ({filters.get('sort_order', 'desc')})")

    return lines


def _get_edgar_client() -> Any:
    """Return the lazily-initialized EDGAR API client.

    Imports ``EdgarAPIClient`` on first use so module-load does not pull in
    ``sec_edgar_api`` (which has fragile transitive deps in some environments).
    Raises ``ValueError`` if ``EDGAR_USER_AGENT`` is not set — FastMCP wraps
    that into ``ToolError`` at the boundary, giving callers a clear message.
    """
    global _edgar_client
    if _edgar_client is None:
        user_agent = os.getenv("EDGAR_USER_AGENT")
        if not user_agent:
            raise ValueError(
                "EDGAR_USER_AGENT environment variable is required to use "
                "EDGAR tools. SEC requires a User-Agent header (e.g. "
                "'Your Name your.email@example.com'). "
                "See https://www.sec.gov/os/accessing-edgar-data"
            )
        from .finviz_client.edgar_client import EdgarAPIClient

        _edgar_client = EdgarAPIClient(user_agent=user_agent)
    return _edgar_client


@server.tool()
def earnings_screener(
    earnings_date: str,
    market_cap: Optional[str] = None,
    min_price: Optional[Union[int, float, str]] = None,
    max_price: Optional[Union[int, float, str]] = None,
    min_volume: Optional[Union[int, float, str]] = None,
    sectors: Optional[List[str]] = None,
) -> List[TextContent]:
    """
    決算発表予定銘柄のスクリーニング

    Args:
        earnings_date: 決算発表日の指定 (today_after, tomorrow_before, this_week, within_2_weeks)
        market_cap: 時価総額フィルタ (small, mid, large, mega, smallover, midover, largeover, ...)
        min_price: 最低株価
        max_price: 最高株価
        min_volume: 最低出来高（当日出来高、sh_curvol_* に変換）
        sectors: 対象セクター

    Note:
        ``premarket_price_change`` / ``afterhours_price_change`` は削除した。
        Finvizのスクリーナーには寄り付き前変動のフィルタが存在せず、
        時間外変動 (``ah_change``) も表示専用なので、受け取っても適用でき
        なかった（audit B13）。時間外の値動きで絞るには
        ``earnings_afterhours_screener`` を使う。
    """
    try:
        # Validate parameters
        if not validate_earnings_date(earnings_date):
            raise ValueError(f"Invalid earnings_date: {earnings_date}")

        if market_cap is not None and not validate_market_cap(market_cap):
            raise ValueError(f"Invalid market_cap: {market_cap}")

        if not validate_price_range(min_price, max_price):
            raise ValueError("Invalid price range")

        if min_volume is not None and not validate_volume(min_volume):
            raise ValueError(f"Invalid min_volume: {min_volume}")

        if sectors:
            for sector in sectors:
                if not validate_sector(sector):
                    raise ValueError(f"Invalid sector: {sector}")

        # Prepare parameters
        params = {
            "earnings_date": earnings_date,
            "market_cap": market_cap,
            "min_price": min_price,
            "max_price": max_price,
            "min_volume": min_volume,
            "sectors": sectors or [],
        }

        # 表示用の条件は、実際に走るフィルタから作る（同じビルダーを使う）。
        # 以前はここに earnings_trading_screener の固定条件がハードコードされ
        # ており、実行していない条件を「適用済み」と表示していた（audit B12）。
        applied_filters = finviz_screener._build_earnings_filters(**params)

        results = finviz_screener.earnings_screener(**params)

        if not results:
            return [
                TextContent(type="text", text="No stocks found matching the criteria.")
            ]

        output_lines = (
            [
                f"Earnings Screening Results ({len(results)} stocks found):",
                "=" * 60,
                "",
            ]
            + _criteria_block(applied_filters, client=finviz_screener)
            + [
                "",
                "=" * 60,
                "",
            ]
        )

        for stock in results:
            output_lines.extend(
                [
                    f"Ticker: {stock.ticker}",
                    f"Company: {stock.company_name}",
                    f"Sector: {stock.sector}",
                    (
                        f"Price: ${stock.price:.2f}"
                        if stock.price is not None
                        else "Price: N/A"
                    ),
                    (
                        f"Change: {stock.price_change:.2f}%"
                        if stock.price_change is not None
                        else "Change: N/A"
                    ),
                    (
                        f"EPS Surprise: {stock.eps_surprise:.2f}%"
                        if stock.eps_surprise is not None
                        else "EPS Surprise: N/A"
                    ),
                    (
                        f"Revenue Surprise: {stock.revenue_surprise:.2f}%"
                        if stock.revenue_surprise is not None
                        else "Revenue Surprise: N/A"
                    ),
                    (
                        f"Volatility: {stock.volatility:.2f}"
                        if stock.volatility is not None
                        else "Volatility: N/A"
                    ),
                    (
                        f"1M Performance: {stock.performance_1m:.2f}%"
                        if stock.performance_1m is not None
                        else "1M Performance: N/A"
                    ),
                    "-" * 40,
                    "",
                ]
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except Exception as e:
        logger.error(f"Error in earnings_screener: {str(e)}")
        raise


@server.tool()
def volume_surge_screener() -> List[TextContent]:
    """
    出来高急増を伴う上昇銘柄のスクリーニング（固定条件）

    固定フィルタ条件（変更不可）：
    f=cap_smallover,ind_stocksonly,sh_avgvol_o100,sh_price_o10,sh_relvol_o1.5,ta_change_u2,ta_sma200_pa&ft=4&o=-change

    - 時価総額：スモール以上 ($300M+)
    - 株式のみ：ETF除外
    - 平均出来高：100,000以上
    - 株価：$10以上
    - 相対出来高：1.5倍以上
    - 価格変動：2%以上上昇
    - 200日移動平均線上
    - 価格変動降順ソート
    - 全件取得（制限なし）

    パラメーターなし - 全ての条件は固定されています
    """
    try:
        # 固定条件で実行（パラメーターなし）
        results = finviz_screener.volume_surge_screener()

        if not results:
            return [
                TextContent(
                    type="text",
                    text="No stocks found matching the fixed volume surge criteria.",
                )
            ]

        # 固定条件の表示
        fixed_conditions = [
            "固定フィルタ条件:",
            "- 時価総額: スモール以上 ($300M+)",
            "- 株式のみ: ETF除外",
            "- 平均出来高: 100,000以上",
            "- 株価: $10以上",
            "- 相対出来高: 1.5倍以上",
            "- 価格変動: 2%以上上昇",
            "- 200日移動平均線上",
            "- 価格変動降順ソート",
            "- 全件取得（制限なし）",
        ]

        # 簡潔な出力形式（ティッカーのみ）
        output_lines = (
            [
                f"Volume Surge Screening Results ({len(results)} stocks found):",
                "=" * 60,
                "",
            ]
            + fixed_conditions
            + ["", "Detected Tickers:", "-" * 40, ""]
        )

        # ティッカーを10個ずつ1行に表示
        tickers = [stock.ticker for stock in results]
        for i in range(0, len(tickers), 10):
            line_tickers = tickers[i : i + 10]
            output_lines.append(" | ".join(line_tickers))

        return [TextContent(type="text", text="\n".join(output_lines))]

    except Exception as e:
        logger.error(f"Error in volume_surge_screener: {str(e)}")
        raise


@server.tool()
def get_stock_fundamentals(
    ticker: str, data_fields: Optional[List[str]] = None
) -> List[TextContent]:
    """
    個別銘柄のファンダメンタルデータ取得（全150カラム対応）

    Args:
        ticker: 銘柄ティッカー
        data_fields: 取得データフィールド（指定しない場合は全フィールド）
    """
    try:
        # Validate ticker
        if not validate_ticker(ticker):
            raise ValueError(f"Invalid ticker: {ticker}")

        # Validate data fields
        if data_fields:
            field_errors = validate_data_fields(data_fields)
            if field_errors:
                raise ValueError(f"Invalid data fields: {', '.join(field_errors)}")

        # Get fundamental data
        fundamental_data = finviz_client.get_stock_fundamentals(ticker, data_fields)

        if not fundamental_data:
            return [
                TextContent(type="text", text=f"No data found for ticker: {ticker}")
            ]

        # Normalize to a plain dict; the display layer is dict-driven.
        if isinstance(fundamental_data, dict):
            data_dict = fundamental_data
        elif hasattr(fundamental_data, "to_dict"):
            data_dict = fundamental_data.to_dict()
        else:
            data_dict = vars(fundamental_data)

        output_lines = [f"📊 Fundamental Data for {ticker}:", "=" * 60, ""]
        output_lines.extend(
            format_fundamentals(data_dict, requested_fields=data_fields)
        )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except (ValueError, TypeError) as e:
        logger.error(f"Validation error in get_stock_fundamentals: {str(e)}")
        raise e  # Re-raise validation errors
    except Exception as e:
        logger.error(f"Error in get_stock_fundamentals: {str(e)}")
        raise


@server.tool()
def get_multiple_stocks_fundamentals(
    tickers: List[str], data_fields: Optional[List[str]] = None
) -> List[TextContent]:
    """
    複数銘柄のファンダメンタルデータ一括取得（全150カラム対応）

    Args:
        tickers: 銘柄ティッカーリスト
        data_fields: 取得データフィールド（指定しない場合は全フィールド）
    """
    try:
        if not tickers:
            raise ValueError("No tickers provided")

        # Validate all tickers
        invalid_tickers = [ticker for ticker in tickers if not validate_ticker(ticker)]
        if invalid_tickers:
            raise ValueError(f"Invalid tickers: {', '.join(invalid_tickers)}")

        # Validate data fields
        if data_fields:
            field_errors = validate_data_fields(data_fields)
            if field_errors:
                raise ValueError(f"Invalid data fields: {', '.join(field_errors)}")

        results = finviz_client.get_multiple_stocks_fundamentals(tickers, data_fields)

        if not results:
            return [
                TextContent(
                    type="text", text="No data found for any of the provided tickers."
                )
            ]

        # Format output with enhanced table view
        output_lines = [f"📊 Fundamental Data for {len(results)} stocks:", "=" * 80, ""]

        # Create comparison table for key metrics
        key_metrics = [
            ("Ticker", "ticker"),
            ("Company", "company"),
            ("Sector", "sector"),
            ("Price", "price"),
            ("Market Cap", "market_cap"),  # 実際に取得されるフィールド名
            ("P/E", "p_e"),  # 実際に取得されるフィールド名
            ("Volume", "volume"),
            ("1D Perf", "change"),  # 本日のパフォーマンス
            ("1W Perf", "performance_week"),  # 実際に取得されるフィールド名
            ("EPS Surprise", "eps_surprise"),  # 実際に取得されるフィールド名
        ]

        # Table header
        header = " | ".join([f"{name:12}" for name, _ in key_metrics])
        output_lines.append(header)
        output_lines.append("-" * len(header))

        # Helper function to get value from result (dict or object)
        def get_value(result, field):
            if isinstance(result, dict):
                return result.get(field)
            else:
                return getattr(result, field, None)

        # Table rows
        for result in results:
            row_values = []
            for name, field in key_metrics:
                value = get_value(result, field)
                if value is not None:
                    if field == "price" and isinstance(value, (int, float)):
                        row_values.append(f"${value:.2f}".ljust(12))
                    elif field == "market_cap" and isinstance(value, (int, float)):
                        # 時価総額データは百万ドル単位で格納されているため、百万倍してから変換
                        actual_value = value * 1e6  # 百万ドル単位を実際の金額に変換
                        if actual_value >= 1e12:  # 1兆以上
                            row_values.append(f"${actual_value/1e12:.1f}T".ljust(12))
                        elif actual_value >= 1e9:  # 10億以上
                            row_values.append(f"${actual_value/1e9:.1f}B".ljust(12))
                        elif actual_value >= 1e6:  # 100万以上
                            row_values.append(f"${actual_value/1e6:.1f}M".ljust(12))
                        else:
                            row_values.append(f"${actual_value:,.0f}".ljust(12))
                    elif field in [
                        "p_e",
                        "change",
                        "performance_week",
                        "eps_surprise",
                    ] and isinstance(value, (int, float)):
                        # change / performance_week / eps_surprise are percentages
                        if field in ["change", "performance_week", "eps_surprise"]:
                            row_values.append(f"{value:.2f}%".ljust(12))
                        else:
                            row_values.append(f"{value:.2f}".ljust(12))
                    elif field == "volume" and isinstance(value, (int, float)):
                        if value >= 1e6:
                            row_values.append(f"{value/1e6:.1f}M".ljust(12))
                        elif value >= 1e3:
                            row_values.append(f"{value/1e3:.1f}K".ljust(12))
                        else:
                            row_values.append(f"{value:,.0f}".ljust(12))
                    else:
                        str_value = str(value)
                        if len(str_value) > 12:
                            str_value = str_value[:9] + "..."
                        row_values.append(str_value.ljust(12))
                else:
                    row_values.append("N/A".ljust(12))

            row = " | ".join(row_values)
            output_lines.append(row)

        output_lines.append("")

        # Detailed breakdown for each stock
        output_lines.append("📋 Detailed Data:")
        output_lines.append("=" * 40)

        for i, result in enumerate(results, 1):
            ticker = get_value(result, "ticker") or "Unknown"
            company = get_value(result, "company") or "N/A"
            output_lines.append(f"\n{i}. {ticker} - {company}")
            output_lines.append("-" * 50)

            # Complete per-section breakdown driven by the shared spec —
            # every non-null field renders (ticker/company shown above).
            if isinstance(result, dict):
                result_dict = result
            elif hasattr(result, "to_dict"):
                result_dict = result.to_dict()
            else:
                result_dict = vars(result) if hasattr(result, "__dict__") else {}

            output_lines.extend(
                compact_fundamentals(result_dict, skip_keys={"company"})
            )

            non_null_fields = sum(1 for v in result_dict.values() if v is not None)
            total_fields = len(result_dict)
            pct = non_null_fields / total_fields * 100 if total_fields else 0.0
            output_lines.append(
                f"  📋 Data Coverage: {non_null_fields}/{total_fields} fields ({pct:.1f}%)"
            )

        # Summary
        output_lines.extend(
            [
                "",
                "📊 Summary:",
                f"Total stocks processed: {len(results)}",
                f"Average data coverage: {sum(sum(1 for v in (result if isinstance(result, dict) else result.to_dict() if hasattr(result, 'to_dict') else vars(result) if hasattr(result, '__dict__') else {}).values() if v is not None)/len(result if isinstance(result, dict) else result.to_dict() if hasattr(result, 'to_dict') else vars(result) if hasattr(result, '__dict__') else {'dummy': None}) for result in results)/len(results)*100:.1f}%",
            ]
        )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except (ValueError, TypeError) as e:
        logger.error(f"Validation error in get_multiple_stocks_fundamentals: {str(e)}")
        raise e  # Re-raise validation errors
    except Exception as e:
        logger.error(f"Error in get_multiple_stocks_fundamentals: {str(e)}")
        raise


@server.tool()
def trend_reversion_screener(
    market_cap: Optional[str] = "mid_large",
    eps_growth_qoq: Optional[float] = None,
    revenue_growth_qoq: Optional[float] = None,
    rsi_max: Optional[float] = None,
    sectors: Optional[List[str]] = None,
    exclude_sectors: Optional[List[str]] = None,
) -> List[TextContent]:
    """
    トレンド反転候補銘柄のスクリーニング

    Args:
        market_cap: 時価総額フィルタ (mid_large, large, mega)
        eps_growth_qoq: EPS成長率(QoQ) 最低値
        revenue_growth_qoq: 売上成長率(QoQ) 最低値
        rsi_max: RSI上限値
        sectors: 対象セクター
        exclude_sectors: 除外セクター
    """
    try:
        params = {
            "market_cap": market_cap,
            "eps_growth_qoq": eps_growth_qoq,
            "revenue_growth_qoq": revenue_growth_qoq,
            "rsi_max": rsi_max,
            "sectors": sectors or [],
            "exclude_sectors": exclude_sectors or [],
        }

        results = finviz_screener.trend_reversion_screener(**params)

        # Same derived criteria block as the sibling screeners: built from
        # the filter dict that actually runs, so the text cannot drift.
        applied_filters = finviz_screener._build_trend_reversion_filters(**params)
        criteria_lines = _criteria_block(applied_filters, client=finviz_screener)
        if params["exclude_sectors"]:
            criteria_lines.append(
                "- Excluded sectors (client-side): "
                + ", ".join(params["exclude_sectors"])
            )

        if not results:
            return [
                TextContent(
                    type="text",
                    text="\n".join(
                        ["No trend reversal candidates found.", ""] + criteria_lines
                    ),
                )
            ]

        output_lines = (
            [
                f"Trend Reversal Screening Results ({len(results)} stocks found):",
                "=" * 60,
                "",
            ]
            + criteria_lines
            + ["", "=" * 60, ""]
        )

        for stock in results:
            output_lines.extend(
                [
                    f"Ticker: {stock.ticker}",
                    f"Company: {stock.company_name}",
                    f"Sector: {stock.sector}",
                    (
                        f"Price: ${stock.price:.2f}"
                        if stock.price is not None
                        else "Price: N/A"
                    ),
                    (
                        f"P/E Ratio: {stock.pe_ratio:.2f}"
                        if stock.pe_ratio is not None
                        else "P/E Ratio: N/A"
                    ),
                    f"RSI: {stock.rsi:.2f}" if stock.rsi is not None else "RSI: N/A",
                    (
                        f"EPS Growth: {stock.eps_qoq_growth:.2f}%"
                        if stock.eps_qoq_growth is not None
                        else "EPS Growth: N/A"
                    ),
                    (
                        f"Revenue Growth: {stock.sales_qoq_growth:.2f}%"
                        if stock.sales_qoq_growth is not None
                        else "Revenue Growth: N/A"
                    ),
                    "-" * 40,
                    "",
                ]
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except Exception as e:
        logger.error(f"Error in trend_reversion_screener: {str(e)}")
        raise


@server.tool()
def uptrend_screener() -> List[TextContent]:
    """
    上昇トレンド銘柄のスクリーニング（固定条件）

    固定フィルタ条件：
    - 時価総額：マイクロ以上（$50M+）
    - 平均出来高：100K以上
    - 株価：10以上
    - 52週高値から30%以内
    - 4週パフォーマンス上昇
    - 20日移動平均線上
    - 200日移動平均線上
    - 50日移動平均線が200日移動平均線上
    - 株式のみ
    - EPS成長率（年次）降順ソート

    パラメーターなし - 全ての条件は固定されています
    """
    try:
        # 固定パラメーターで実行
        results = finviz_screener.uptrend_screener()

        if not results:
            return [
                TextContent(
                    type="text",
                    text="No stocks found matching the fixed uptrend criteria.",
                )
            ]

        # 固定条件の表示
        fixed_conditions = [
            "Fixed Filter Criteria:",
            "- Market Cap: Micro+ ($50M+)",
            "- Avg Volume: 100K+",
            "- Price: $10+",
            "- Within 30% of 52W high",
            "- 4W Performance: Up",
            "- Above SMA20",
            "- Above SMA200",
            "- SMA50 above SMA200",
            "- Stocks only",
            "- Sorted by EPS growth YoY desc",
        ]

        # ティッカーのみをコンパクトに表示
        tickers = [stock.ticker for stock in results]

        output_lines = (
            [f"Uptrend Screening Results ({len(results)} stocks found):", "=" * 60, ""]
            + fixed_conditions
            + ["", f"Detected Stocks ({len(tickers)} items):", "-" * 40, ""]
        )

        # ティッカーを1行に10個ずつ表示
        ticker_lines = []
        for i in range(0, len(tickers), 10):
            line_tickers = tickers[i : i + 10]
            ticker_lines.append("  " + " | ".join(line_tickers))

        output_lines.extend(ticker_lines)
        output_lines.append("")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except Exception as e:
        logger.error(f"Error in uptrend_screener: {str(e)}")
        raise


@server.tool()
def dividend_growth_screener(
    market_cap: Optional[str] = "midover",
    min_dividend_yield: Optional[float] = 2.0,
    max_dividend_yield: Optional[float] = None,
    min_payout_ratio: Optional[float] = None,
    max_payout_ratio: Optional[float] = None,
    min_roe: Optional[float] = None,
    max_debt_equity: Optional[float] = None,
    max_pb_ratio: Optional[float] = 5.0,
    max_pe_ratio: Optional[float] = 30.0,
    eps_growth_5y_positive: Optional[bool] = True,
    eps_growth_qoq_positive: Optional[bool] = True,
    eps_growth_yoy_positive: Optional[bool] = True,
    sales_growth_5y_positive: Optional[bool] = True,
    sales_growth_qoq_positive: Optional[bool] = True,
    country: Optional[str] = "USA",
    stocks_only: Optional[bool] = True,
    sort_by: Optional[str] = "dividend_yield",
    sort_order: Optional[str] = "desc",
    max_results: Optional[int] = 100,
) -> List[TextContent]:
    """
    配当成長銘柄のスクリーニング

    デフォルト条件（変更可能、すべて実際にFinvizへ送られる）：
    - 時価総額：ミッド以上 ($2B+, cap_midover)
    - 配当利回り：2%以上 (fa_div_2to)
    - EPS 5年/QoQ/今年 成長率：プラス (fa_eps5years_pos, fa_epsqoq_pos, fa_epsyoy_pos)
    - PBR：5以下 (fa_pb_u5) / PER：30以下 (fa_pe_u30)
    - 売上5年/QoQ 成長率：プラス (fa_sales5years_pos, fa_salesqoq_pos)
    - 地域：アメリカ (geo_usa)
    - 株式のみ (ind_stocksonly)

    Args:
        market_cap: 時価総額フィルタ (デフォルト: midover)
        min_dividend_yield: 最低配当利回り (デフォルト: 2.0)
        max_dividend_yield: 最高配当利回り
        min_payout_ratio: 最低配当性向 (fa_payoutratio_o*)
        max_payout_ratio: 最高配当性向 (fa_payoutratio_u*)
        min_roe: 最低ROE (fa_roe_o*)
        max_debt_equity: 最高負債比率 (fa_debteq_u*)
        max_pb_ratio: 最高PBR (デフォルト: 5.0)
        max_pe_ratio: 最高PER (デフォルト: 30.0)
        eps_growth_5y_positive: EPS 5年成長率プラス (デフォルト: True)
        eps_growth_qoq_positive: EPS QoQ成長率プラス (デフォルト: True)
        eps_growth_yoy_positive: EPS 今年成長率プラス (デフォルト: True)
        sales_growth_5y_positive: 売上5年成長率プラス (デフォルト: True)
        sales_growth_qoq_positive: 売上QoQ成長率プラス (デフォルト: True)
        country: 地域 (デフォルト: USA。geo_usa のみ検証済みで他はエラー)
        stocks_only: 株式のみ (デフォルト: True)
        sort_by: ソート基準 ('dividend_yield', 'market_cap', 'sma200', 'pe_ratio')
        sort_order: ソート順序 (デフォルト: desc)

    Note:
        ``min_dividend_growth`` は削除した。配当成長率に対応するFinvizの
        フィルタトークンが見つからず（``fa_divgrowth1_o5`` はプローブで無視
        された）、CSVの Dividend Growth 列もStockDataに無いためクライアント
        側でも適用できない（audit B2）。
    """
    try:
        params = {
            "market_cap": market_cap,
            "min_dividend_yield": min_dividend_yield,
            "max_dividend_yield": max_dividend_yield,
            "min_payout_ratio": min_payout_ratio,
            "max_payout_ratio": max_payout_ratio,
            "min_roe": min_roe,
            "max_debt_equity": max_debt_equity,
            "max_pb_ratio": max_pb_ratio,
            "max_pe_ratio": max_pe_ratio,
            "eps_growth_5y_positive": eps_growth_5y_positive,
            "eps_growth_qoq_positive": eps_growth_qoq_positive,
            "eps_growth_yoy_positive": eps_growth_yoy_positive,
            "sales_growth_5y_positive": sales_growth_5y_positive,
            "sales_growth_qoq_positive": sales_growth_qoq_positive,
            "country": country,
            "stocks_only": stocks_only,
            "sort_by": sort_by,
            "sort_order": sort_order,
            "max_results": max_results,
        }

        # 表示用の条件は実際に走るフィルタから生成する（audit B2）
        applied_filters = finviz_screener._build_dividend_growth_filters(**params)

        results = finviz_screener.dividend_growth_screener(**params)

        # Debug: log the first few results to check dividend_yield values.
        # Never print(): stdout is the MCP stdio JSON-RPC channel.
        if results:
            logger.debug(
                f"First 3 results dividend yields: {[(stock.ticker, stock.dividend_yield) for stock in results[:3]]}"
            )

        if not results:
            return [TextContent(type="text", text="No dividend growth stocks found.")]

        output_lines = (
            [
                f"Dividend Growth Screening Results ({len(results)} stocks shown):",
                "=" * 60,
                "",
            ]
            + _criteria_block(
                applied_filters,
                client=finviz_screener,
                extra=[f"Sort: {sort_by} ({sort_order}), applied before the cut"],
            )
            + ["", "=" * 60, ""]
        )

        # 件数制限はスクリーナー側でソート後に適用済み
        for stock in results:
            output_lines.extend(
                [
                    f"Ticker: {stock.ticker}",
                    f"Company: {stock.company_name}",
                    f"Sector: {stock.sector}",
                    (
                        f"Price: ${stock.price:.2f}"
                        if stock.price is not None
                        else "Price: N/A"
                    ),
                    (
                        f"Dividend Yield: {stock.dividend_yield:.2f}%"
                        if stock.dividend_yield is not None
                        else "Dividend Yield: N/A"
                    ),
                    (
                        f"P/E Ratio: {stock.pe_ratio:.2f}"
                        if stock.pe_ratio is not None
                        else "P/E Ratio: N/A"
                    ),
                    (
                        f"Market Cap: {stock.market_cap}"
                        if stock.market_cap is not None
                        else "Market Cap: N/A"
                    ),
                    "-" * 40,
                    "",
                ]
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except Exception as e:
        logger.error(f"Error in dividend_growth_screener: {str(e)}")
        raise


@server.tool()
def etf_screener(
    asset_class: Optional[str] = None,
    min_aum: Optional[float] = None,
    max_expense_ratio: Optional[float] = None,
    min_price: Optional[float] = None,
    min_avg_volume: Optional[float] = None,
    sort_by: Optional[str] = "aum",
    sort_order: Optional[str] = "desc",
    max_results: int = 50,
) -> List[TextContent]:
    """
    ETFスクリーニング

    Args:
        asset_class: 資産クラス (equity, bond, commodity, ... / Asset Type 列で照合)
        min_aum: 最低運用資産額（USD）
        max_expense_ratio: 最高経費率（%）
        min_price: 最低価格
        min_avg_volume: 最低平均出来高（株数）
        sort_by: ソート基準 ('aum', 'expense_ratio', 'price', 'volume', 'ticker')
        sort_order: ソート順序 ('asc', 'desc')
        max_results: 最大取得件数

    Note:
        Finvizで効くのはETF universe（``ind_exchangetradedfund``）と価格・
        出来高までで、AUM・経費率・資産クラスのフィルタトークンは実在が確認
        できなかった（``etf_netexpense_u0.2`` / ``etf_aum_o10000`` はどちらも
        無視された）。それらはCSVの実データを使ってクライアント側で適用する
        （audit B3）。``strategy_type`` は Finviz にも CSV にも対応する概念が
        無いため削除した。
    """
    try:
        params = {
            "asset_class": asset_class,
            "min_aum": min_aum,
            "max_expense_ratio": max_expense_ratio,
            "min_price": min_price,
            "min_avg_volume": min_avg_volume,
            "sort_by": sort_by,
            "sort_order": sort_order,
            "max_results": max_results,
        }

        applied_filters = finviz_screener._build_etf_filters(**params)
        client_side = []
        if min_aum is not None:
            client_side.append(f"Min AUM: ${min_aum:,.0f} (client-side)")
        if max_expense_ratio is not None:
            client_side.append(
                f"Max net expense ratio: {max_expense_ratio}% (client-side)"
            )
        if asset_class:
            client_side.append(f"Asset class: {asset_class} (client-side)")

        results = finviz_screener.etf_screener(**params)

        if not results:
            return [TextContent(type="text", text="No ETFs found matching criteria.")]

        output_lines = (
            [
                f"ETF Screening Results ({len(results)} ETFs shown):",
                "=" * 60,
                "",
            ]
            + _criteria_block(
                applied_filters,
                client=finviz_screener,
                extra=client_side
                + [f"Sort: {sort_by} ({sort_order}), applied before the cut"],
            )
            + ["", "=" * 60, ""]
        )

        for stock in results:
            output_lines.extend(
                [
                    f"Ticker: {stock.ticker}",
                    f"Name: {stock.company_name}",
                    (
                        f"Price: ${stock.price:.2f}"
                        if stock.price is not None
                        else "Price: N/A"
                    ),
                    (
                        f"Volume: {stock.volume:,.0f}"
                        if stock.volume is not None
                        else "Volume: N/A"
                    ),
                    (
                        f"Change: {stock.price_change:.2f}%"
                        if stock.price_change is not None
                        else "Change: N/A"
                    ),
                    (
                        f"AUM: {format_large_number(stock.aum)}"
                        if stock.aum is not None
                        else "AUM: N/A"
                    ),
                    (
                        f"Net Expense Ratio: {stock.net_expense_ratio:.2f}%"
                        if stock.net_expense_ratio is not None
                        else "Net Expense Ratio: N/A"
                    ),
                    f"Asset Type: {stock.asset_type or 'N/A'}",
                    f"ETF Type: {stock.etf_type or 'N/A'}",
                    "-" * 40,
                    "",
                ]
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except Exception as e:
        logger.error(f"Error in etf_screener: {str(e)}")
        raise


@server.tool()
def earnings_premarket_screener() -> List[TextContent]:
    """
    寄り付き前決算発表で上昇している銘柄のスクリーニング（固定条件）

    固定フィルタ条件（変更不可）：
    f=cap_largeover,earningsdate_todaybefore,sh_avgvol_o100,sh_price_o30,ta_change_u2&ft=4&o=-change

    - 時価総額：ラージ以上（$10B+）
    - 決算発表：今日の寄り付き前
    - 平均出来高：100K以上
    - 株価：$30以上
    - 価格変動：2%以上上昇
    - 株式のみ
    - 価格変動降順ソート

    パラメーターなし - 全ての条件は固定されています
    """
    try:
        # 固定パラメーターで実行
        results = finviz_screener.earnings_premarket_screener()

        if not results:
            return [
                TextContent(
                    type="text",
                    text="No stocks found matching the fixed premarket earnings criteria.",
                )
            ]

        # 条件表示はフォーマッタ側が実フィルタから描画する（audit B14）。
        # ここで別の条件ブロックを足すと同じ内容が二度出るだけなので出さない。
        applied_filters = finviz_screener._build_earnings_premarket_filters()
        formatted_output = _format_earnings_premarket_list(results, applied_filters)

        return [TextContent(type="text", text="\n".join(formatted_output))]

    except Exception as e:
        logger.error(f"Error in earnings_premarket_screener: {str(e)}")
        raise


@server.tool()
def earnings_afterhours_screener() -> List[TextContent]:
    """
    引け後決算発表で時間外取引上昇銘柄のスクリーニング（固定条件）

    固定フィルタ条件（変更不可）：
    f=ah_change_u2,cap_largeover,earningsdate_todayafter,sh_avgvol_o100,sh_price_o30&ft=4&o=-afterchange&ar=60

    - 時間外変動：2%以上上昇
    - 時価総額：ラージ以上（$10B+）
    - 決算発表：今日の引け後
    - 平均出来高：100K以上
    - 株価：$30以上
    - 株式のみ
    - 時間外変動降順ソート
    - 最大結果：60件

    パラメーターなし - 全ての条件は固定されています
    """
    try:
        # 固定パラメーターで実行
        results = finviz_screener.earnings_afterhours_screener()

        if not results:
            return [
                TextContent(
                    type="text",
                    text="No stocks found matching the fixed afterhours earnings criteria.",
                )
            ]

        # 条件表示はフォーマッタ側が実フィルタから描画する（audit B14）
        applied_filters = finviz_screener._build_earnings_afterhours_filters()
        formatted_output = _format_earnings_afterhours_list(results, applied_filters)

        return [TextContent(type="text", text="\n".join(formatted_output))]

    except Exception as e:
        logger.error(f"Error in earnings_afterhours_screener: {str(e)}")
        raise


@server.tool()
def earnings_trading_screener() -> List[TextContent]:
    """
    決算トレード対象銘柄のスクリーニング（固定条件）

    固定フィルタ条件（変更不可）：
    f=cap_largeover,earningsdate_yesterdayafter|todaybefore,fa_epsrev_ep,fa_netmargin_3to,sh_avgvol_o200,sh_price_o30,ta_change_u,ta_perf_0to-4w&ft=4&o=-epssurprise&ar=60

    - 時価総額：ラージ以上 ($10B+)
    - 決算発表：昨日の引け後または今日の寄り付き前
    - EPS予想：上方修正
    - ネットマージン：3%以上
    - 平均出来高：200,000以上
    - 株価：$30以上
    - 価格変動：上昇トレンド
    - 4週パフォーマンス：0%以上（ta_perf_0to-4w = 4週騰落率が0%以上。
      `<N>to-<tf>` は「tf期間の騰落率がN%以上」を意味する: audit B19）
    - 株式のみ
    - EPSサプライズ降順ソート
    - 最大結果件数：60件

    パラメーターなし - 全ての条件は固定されています
    """
    try:
        # 固定条件で実行（パラメーターなし）
        applied_filters = finviz_screener._build_earnings_trading_filters()
        results = finviz_screener.earnings_trading_screener()

        if not results:
            return [
                TextContent(
                    type="text",
                    text="No stocks found matching the specified earnings trading criteria.",
                )
            ]

        # 詳細フォーマッタを使用。以前はこの関数が丸ごと未使用（dead code）で、
        # ティッカーの羅列だけを返していた（audit B27）。Phase 1でパーサの
        # マッピングを直した結果、この表が使う eps_surprise / revenue_surprise
        # / performance_1w / volatility(=Volatility (Week)) / volume はすべて
        # 実データで埋まるようになったので、削除ではなく接続する。
        output_lines = (
            [
                f"Earnings Trading Screening Results ({len(results)} stocks found):",
                "=" * 60,
                "",
            ]
            # 条件ブロックはフォーマッタ側が実フィルタから描画する（二重表示を避ける）
            + _format_earnings_trading_list(results, applied_filters)
        )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except Exception as e:
        logger.error(f"Error in earnings_trading_screener: {str(e)}")
        raise


def _format_news_datetime(value: datetime) -> str:
    """Render a news timestamp, labelling the zone when we actually know it.

    Finviz news timestamps are US/Eastern (GROUND_TRUTH.md) and the client
    hands back tz-aware values; those get an explicit ``ET`` suffix. A naive
    value carries no zone information, so none is claimed.
    """
    if value.tzinfo is not None:
        return f"{value.astimezone(EASTERN).strftime('%Y-%m-%d %H:%M')} ET"
    return value.strftime("%Y-%m-%d %H:%M")


def _render_news_items(news_list: List[NewsData], separator: str) -> List[str]:
    """Render news items. Only fields the feed actually supplied are shown."""
    lines: List[str] = []
    for news in news_list:
        lines.append(f"📰 {news.title}")
        if news.ticker:
            # Real per-article attribution from the CSV ``Ticker`` column;
            # comma-joined when one item covers several names.
            lines.append(f"📈 Ticker: {news.ticker}")
        if news.source:
            lines.append(f"🏢 Source: {news.source}")
        lines.append(f"📅 Date: {_format_news_datetime(news.date)}")
        if news.category:
            lines.append(f"🏷️ Category: {news.category}")
        if news.url:
            lines.append(f"🔗 URL: {news.url}")
        lines.extend([separator, ""])
    return lines


@server.tool()
def get_stock_news(
    tickers: Union[str, List[str]], days_back: int = 7
) -> List[TextContent]:
    """
    銘柄関連ニュースの取得（news_export v=3）

    Args:
        tickers: 銘柄ティッカー（単一文字列、カンマ区切り文字列、またはリスト）
        days_back: 過去何日分のニュース（US/Eastern基準）

    Note:
        Finviz's news export has no news-type/category taxonomy to filter on
        (``filter=`` is ignored and every row is ``Category=Stock``), so this
        tool takes no news_type argument. Each item is labelled with the
        article's real ticker(s).

        The days_back boundary is inclusive: an item timestamped exactly
        days_back days ago is kept. Rows whose Date cell is empty or
        unparseable are dropped (and counted in one WARNING per call), so a
        feed-format change cannot masquerade as "no news".
    """
    try:
        from .utils.validators import parse_tickers, validate_tickers

        # Validate tickers
        if not validate_tickers(tickers):
            raise ValueError(f"Invalid tickers: {tickers}")

        # Validate days_back
        if days_back <= 0:
            raise ValueError(f"Invalid days_back: {days_back}")

        # Parse tickers for display
        ticker_list = parse_tickers(tickers)
        ticker_display = ", ".join(ticker_list)

        # Get news data
        news_list = finviz_news.get_stock_news(tickers, days_back or 7)

        if not news_list:
            return [
                TextContent(
                    type="text",
                    text=(
                        f"No news for {ticker_display} dated within the last "
                        f"{days_back} days (the feed may still carry older items)."
                    ),
                )
            ]

        output_lines = [
            f"News for {ticker_display} (last {days_back} days):",
            "=" * 50,
            "",
        ]
        output_lines.extend(_render_news_items(news_list, "-" * 40))

        return [TextContent(type="text", text="\n".join(output_lines))]

    except (ValueError, TypeError) as e:
        logger.error(f"Validation error in get_stock_news: {str(e)}")
        raise e  # Re-raise validation errors
    except Exception as e:
        logger.error(f"Error in get_stock_news: {str(e)}")
        raise


@server.tool()
def get_market_news(
    days_back: int = 3, max_items: int = 20, category: Optional[str] = None
) -> List[TextContent]:
    """
    市場全体のニュースを取得（news_export v=1）

    Args:
        days_back: 過去何日分のニュース（US/Eastern基準）
        max_items: 最大取得件数
        category: 実際の ``Category`` 列に対するクライアント側フィルタ。
            "Market"（報道）または "Blog"（ブログ/コラム）のみ有効で、
            それ以外を渡すとエラーになる（黙って0件にしない）。省略時は全件。

    Note:
        The days_back boundary is inclusive: an item timestamped exactly
        days_back days ago is kept. Rows whose Date cell is empty or
        unparseable are dropped (and counted in one WARNING per call), so a
        feed-format change cannot masquerade as "no news".
    """
    try:
        # Get market news
        news_list = finviz_news.get_market_news(
            days_back or 3, max_items or 20, category
        )

        if not news_list:
            scope = f" in category '{category}'" if category else ""
            return [
                TextContent(
                    type="text",
                    text=(
                        f"No market news{scope} dated within the last "
                        f"{days_back} days."
                    ),
                )
            ]

        # Format output
        title = "Market News"
        if category:
            title += f" [{category}]"
        output_lines = [f"{title} (last {days_back} days):", "=" * 50, ""]
        output_lines.extend(_render_news_items(news_list, "-" * 30))

        return [TextContent(type="text", text="\n".join(output_lines))]

    except Exception as e:
        logger.error(f"Error in get_market_news: {str(e)}")
        raise


@server.tool()
def get_sector_news(
    sector: str, days_back: int = 5, max_items: int = 15
) -> List[TextContent]:
    """
    特定セクターのニュースを取得

    Finviz has no sector news feed, so this resolves the sector to its largest
    constituents (one screener export, market-cap ordered) and then fetches
    news for exactly those tickers. Each headline is labelled with its real
    ticker — nothing is attributed to the sector that did not come from one of
    its constituents.

    Args:
        sector: セクター名（例 "Technology"）またはFinvizコード
        days_back: 過去何日分のニュース（US/Eastern基準）
        max_items: 最大取得件数

    Note:
        The days_back boundary is inclusive: an item timestamped exactly
        days_back days ago is kept. Rows whose Date cell is empty or
        unparseable are dropped (and counted in one WARNING per call), so a
        feed-format change cannot masquerade as "no news".
    """
    try:
        # Get sector news
        news_list = finviz_news.get_sector_news(sector, days_back or 5, max_items or 15)

        if not news_list:
            return [
                TextContent(
                    type="text",
                    text=(
                        f"No news for {sector} sector constituents dated within "
                        f"the last {days_back} days."
                    ),
                )
            ]

        # Format output
        output_lines = [
            f"{sector} Sector News (last {days_back} days, "
            f"top {finviz_news.SECTOR_TICKER_LIMIT} constituents by market cap):",
            "=" * 50,
            "",
        ]
        output_lines.extend(_render_news_items(news_list, "-" * 30))

        return [TextContent(type="text", text="\n".join(output_lines))]

    except (ValueError, TypeError) as e:
        logger.error(f"Validation error in get_sector_news: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Error in get_sector_news: {str(e)}")
        raise


# ---------------------------------------------------------------------------
# Groups (sector / industry / country / capitalization) rendering
# ---------------------------------------------------------------------------

# (header, key, width) — every field the groups parser emits is rendered here;
# nothing is fetched-but-hidden.
_GROUP_TABLE_COLUMNS = [
    ("Market Cap", "market_cap", 11),
    ("P/E", "pe_ratio", 7),
    ("Fwd P/E", "forward_pe", 8),
    ("Div %", "dividend_yield", 7),
    ("Change", "change", 8),
    ("1W", "performance_1w", 8),
    ("1M", "performance_1m", 8),
    ("3M", "performance_3m", 8),
    ("6M", "performance_6m", 8),
    ("1Y", "performance_1y", 9),
    ("YTD", "performance_ytd", 9),
    ("Recom", "analyst_recom", 6),
    ("Avg Vol", "avg_volume", 9),
    ("Rel Vol", "relative_volume", 8),
    ("Volume", "volume", 11),
    ("Stocks", "stock_count", 6),
]

# Percent columns whose sign carries meaning (up/down) => rendered signed.
_SIGNED_PERCENT_GROUP_KEYS = {
    "change",
    "performance_1w",
    "performance_1m",
    "performance_3m",
    "performance_6m",
    "performance_1y",
    "performance_ytd",
}

# Percent columns that are magnitudes, not moves => rendered unsigned.
_UNSIGNED_PERCENT_GROUP_KEYS = {"dividend_yield"}


def _fmt_group_market_cap(value: Any) -> str:
    """Format a groups market cap (exported in $M) as a labeled $M/$B/$T."""
    if value is None:
        return "N/A"
    if not isinstance(value, (int, float)):
        return str(value)
    dollars = float(value) * 1e6  # 百万ドル単位 → 実際の金額
    if abs(dollars) >= 1e12:
        return f"${dollars / 1e12:.2f}T"
    if abs(dollars) >= 1e9:
        return f"${dollars / 1e9:.2f}B"
    if abs(dollars) >= 1e6:
        return f"${dollars / 1e6:.2f}M"
    return f"${dollars:,.0f}"


def _fmt_group_shares(value: Any) -> str:
    """Format a share count (already normalized to shares) compactly."""
    if value is None:
        return "N/A"
    if not isinstance(value, (int, float)):
        return str(value)
    shares = float(value)
    if abs(shares) >= 1e9:
        return f"{shares / 1e9:.2f}B"
    if abs(shares) >= 1e6:
        return f"{shares / 1e6:.2f}M"
    if abs(shares) >= 1e3:
        return f"{shares / 1e3:.1f}K"
    return f"{shares:,.0f}"


def _fmt_group_value(key: str, value: Any) -> str:
    """Format one group field for the table (None => N/A, never a fake 0)."""
    if value is None:
        return "N/A"
    if key == "market_cap":
        return _fmt_group_market_cap(value)
    if key in ("avg_volume", "volume"):
        return _fmt_group_shares(value)
    if not isinstance(value, (int, float)):
        return str(value)
    if key in _SIGNED_PERCENT_GROUP_KEYS:
        return f"{float(value):+.2f}%"
    if key in _UNSIGNED_PERCENT_GROUP_KEYS:
        return f"{float(value):.2f}%"
    if key == "stock_count":
        return f"{int(value):,}"
    return f"{float(value):.2f}"


def _format_group_table(
    rows: List[Dict[str, Any]], name_header: str, name_width: int = 30
) -> List[str]:
    """Render group rows as a table covering every parsed field."""
    header = f"{name_header:<{name_width}} " + " ".join(
        f"{title:<{width}}" for title, _, width in _GROUP_TABLE_COLUMNS
    )
    lines = [
        "単位: Market Cap = USD / Avg Vol・Volume = 株数 / その他 % 表記は百分率",
        "",
        header,
        "-" * len(header),
    ]

    for row in rows:
        name = str(row.get("name", "N/A"))
        if len(name) > name_width - 1:
            name = name[: name_width - 4] + "..."
        cells = " ".join(
            f"{_fmt_group_value(key, row.get(key)):<{width}}"
            for _, key, width in _GROUP_TABLE_COLUMNS
        )
        lines.append(f"{name:<{name_width}} {cells}")

    return lines


@server.tool()
def get_sector_performance(sectors: Optional[List[str]] = None) -> List[TextContent]:
    """
    セクター別パフォーマンス分析

    Args:
        sectors: 対象セクター（大文字小文字は区別しない。例: ["Technology"]）
    """
    try:
        # Get sector performance data
        sector_data = finviz_sector.get_sector_performance(sectors=sectors)

        if not sector_data:
            if sectors:
                return [
                    TextContent(
                        type="text",
                        text=(
                            "No sector performance data found for: "
                            f"{', '.join(sectors)}"
                        ),
                    )
                ]
            return [TextContent(type="text", text="No sector performance data found.")]

        # Format output
        output_lines = ["🏢 Sector Performance Analysis:", "=" * 60, ""]
        output_lines.extend(_format_group_table(sector_data, "Sector", 30))
        output_lines.extend(["", f"Showing {len(sector_data)} sector(s)."])

        return [TextContent(type="text", text="\n".join(output_lines))]

    except Exception as e:
        logger.error(f"Error in get_sector_performance: {str(e)}")
        raise


@server.tool()
def get_industry_performance(
    industries: Optional[List[str]] = None,
) -> List[TextContent]:
    """
    業界別パフォーマンス分析

    Args:
        industries: 対象業界（大文字小文字は区別しない。例: ["Semiconductors"]）
    """
    try:
        # Get industry performance data
        industry_data = finviz_sector.get_industry_performance(industries)

        if not industry_data:
            if industries:
                return [
                    TextContent(
                        type="text",
                        text=(
                            "No industry performance data found for: "
                            f"{', '.join(industries)}"
                        ),
                    )
                ]
            return [
                TextContent(type="text", text="No industry performance data found.")
            ]

        # Format output
        output_lines = ["🏭 Industry Performance Analysis:", "=" * 60, ""]
        output_lines.extend(_format_group_table(industry_data, "Industry", 38))
        output_lines.extend(["", f"Showing {len(industry_data)} industry/industries."])

        return [TextContent(type="text", text="\n".join(output_lines))]

    except Exception as e:
        logger.error(f"Error in get_industry_performance: {str(e)}")
        raise


@server.tool()
def get_country_performance(countries: Optional[List[str]] = None) -> List[TextContent]:
    """
    国別市場パフォーマンス分析

    Args:
        countries: 対象国（大文字小文字は区別しない。例: ["USA"]）
    """
    try:
        # Get country performance data
        country_data = finviz_sector.get_country_performance(countries)

        if not country_data:
            if countries:
                return [
                    TextContent(
                        type="text",
                        text=(
                            "No country performance data found for: "
                            f"{', '.join(countries)}"
                        ),
                    )
                ]
            return [TextContent(type="text", text="No country performance data found.")]

        # Format output
        output_lines = ["🌍 Country Performance Analysis:", "=" * 60, ""]
        output_lines.extend(_format_group_table(country_data, "Country", 26))
        output_lines.extend(["", f"Showing {len(country_data)} country/countries."])

        return [TextContent(type="text", text="\n".join(output_lines))]

    except Exception as e:
        logger.error(f"Error in get_country_performance: {str(e)}")
        raise


@server.tool()
def get_sector_specific_industry_performance(sector: str) -> List[TextContent]:
    """
    特定セクター内の業界別パフォーマンス分析

    利用可能なセクター:
    - basicmaterials (Basic Materials)
    - communicationservices (Communication Services)
    - consumercyclical (Consumer Cyclical)
    - consumerdefensive (Consumer Defensive)
    - energy (Energy)
    - financial (Financial)
    - healthcare (Healthcare)
    - industrials (Industrials)
    - realestate (Real Estate)
    - technology (Technology)
    - utilities (Utilities)

    Args:
        sector: セクター名 (上記のセクター名から選択)
    """
    try:
        # Get sector-specific industry performance data
        industry_data = finviz_sector.get_sector_specific_industry_performance(sector)

        if not industry_data:
            return [
                TextContent(
                    type="text",
                    text=f"No industry performance data found for {sector} sector.",
                )
            ]

        # Format output
        sector_display = sector.replace("_", " ").title()
        output_lines = [
            f"🏭 {sector_display} Sector - Industry Performance Analysis:",
            "=" * 70,
            "",
        ]
        output_lines.extend(_format_group_table(industry_data, "Industry", 38))
        output_lines.extend(
            [
                "",
                f"Showing {len(industry_data)} industry/industries "
                f"in the {sector_display} sector.",
            ]
        )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except Exception as e:
        logger.error(f"Error in get_sector_specific_industry_performance: {str(e)}")
        raise


@server.tool()
def get_capitalization_performance() -> List[TextContent]:
    """
    時価総額別パフォーマンス分析
    """
    try:
        # Get capitalization performance data
        cap_data = finviz_sector.get_capitalization_performance()

        if not cap_data:
            return [
                TextContent(
                    type="text", text="No capitalization performance data found."
                )
            ]

        # Format output
        output_lines = ["💼 Capitalization Performance Analysis:", "=" * 70, ""]
        output_lines.extend(_format_group_table(cap_data, "Capitalization", 18))
        output_lines.extend(["", f"Showing {len(cap_data)} capitalization tier(s)."])

        return [TextContent(type="text", text="\n".join(output_lines))]

    except Exception as e:
        logger.error(f"Error in get_capitalization_performance: {str(e)}")
        raise


@server.tool()
def get_market_overview() -> List[TextContent]:
    """
    市場全体の概要を取得（実際のデータ）
    """
    try:
        import pandas as pd

        logger.info("Retrieving real market overview data...")

        # 主要ETFのティッカー（ユーザーが提供したデータと一致）
        major_etfs = ["SPY", "QQQ", "DIA", "IWM", "TLT", "GLD"]

        # 1. 主要ETFの実データを一括取得（Finvizの実フィールド名使用）
        logger.info("Fetching major ETF data using Finviz bulk API...")
        try:
            # 実際のFinvizレスポンスフィールドに対応
            etf_data_bulk = finviz_client.get_multiple_stocks_fundamentals(
                major_etfs,
                data_fields=[
                    "ticker",
                    "company",
                    "price",
                    "change",
                    "volume",
                    "market_cap",
                ],
            )
            logger.info(f"Successfully retrieved data for {len(etf_data_bulk)} ETFs")
        except FinvizAPIError:
            # リクエスト自体の失敗（認証切れ等）は個別取得でも直らない。
            # ゼロ埋めした「概況」を返さず、そのまま失敗として報告する。
            raise
        except Exception as e:
            logger.warning(f"Bulk API failed: {e}, trying individual requests...")
            # フォールバック：個別取得
            etf_data_bulk = []
            for ticker in major_etfs:
                try:
                    data = finviz_client.get_stock_fundamentals(
                        ticker,
                        data_fields=[
                            "ticker",
                            "company",
                            "price",
                            "change",
                            "volume",
                            "market_cap",
                        ],
                    )
                    etf_data_bulk.append(data)
                except Exception as etf_error:
                    logger.warning(f"Failed to get data for {ticker}: {etf_error}")
                    etf_data_bulk.append({"ticker": ticker, "error": str(etf_error)})

        # 2. 市場統計を並列取得
        logger.info("Calculating market statistics...")

        # 出来高急増銘柄数を取得
        try:
            volume_surge_results = finviz_screener.volume_surge_screener()
            volume_surge_count = (
                len(volume_surge_results) if volume_surge_results else 0
            )
            # 統計計算: 欠損値は平均から除外し、母数も実際の件数を使う
            # (0.0 は正当な値なので truthiness ではなく is not None で判定)
            rel_vol_values = [
                stock.relative_volume
                for stock in volume_surge_results
                if getattr(stock, "relative_volume", None) is not None
            ]
            change_values = [
                stock.price_change
                for stock in volume_surge_results
                if getattr(stock, "price_change", None) is not None
            ]
            avg_rel_vol = (
                sum(rel_vol_values) / len(rel_vol_values) if rel_vol_values else None
            )
            avg_change = (
                sum(change_values) / len(change_values) if change_values else None
            )
            rel_vol_sample = len(rel_vol_values)
            change_sample = len(change_values)
        except FinvizAPIError:
            raise
        except Exception as e:
            logger.warning(f"Volume surge calculation failed: {e}")
            volume_surge_count = 0
            avg_rel_vol = None
            avg_change = None
            rel_vol_sample = 0
            change_sample = 0

        # 上昇トレンド銘柄数を取得
        try:
            uptrend_results = finviz_screener.uptrend_screener()
            uptrend_count = len(uptrend_results) if uptrend_results else 0
            # セクター分析
            if uptrend_results:
                sectors_count = {}
                for stock in uptrend_results:
                    sector = getattr(stock, "sector", None)
                    if sector:
                        sectors_count[sector] = sectors_count.get(sector, 0) + 1
                top_sectors = dict(
                    sorted(sectors_count.items(), key=lambda x: x[1], reverse=True)[:3]
                )
            else:
                top_sectors = {}
        except FinvizAPIError:
            raise
        except Exception as e:
            logger.warning(f"Uptrend calculation failed: {e}")
            uptrend_count = 0
            top_sectors = {}

        # 決算関連統計
        try:
            earnings_results = finviz_screener.earnings_screener(
                earnings_date="this_week"
            )
            earnings_count = len(earnings_results) if earnings_results else 0
        except FinvizAPIError:
            raise
        except Exception as e:
            logger.warning(f"Earnings calculation failed: {e}")
            earnings_count = 0

        # ETF名称マッピング（実際のFinvizと一致）
        etf_names = {
            "SPY": "SPDR S&P 500 ETF Trust",
            "QQQ": "Invesco QQQ Trust Series 1",
            "DIA": "SPDR Dow Jones Industrial Average ETF",
            "IWM": "iShares Russell 2000 ETF",
            "TLT": "iShares 20+ Year Treasury Bond ETF",
            "GLD": "SPDR Gold Shares ETF",
        }

        # 出力フォーマット
        output_lines = [
            "🏛️ リアルタイム市場概要",
            "=" * 70,
            f"📅 データ取得時刻: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "📊 データソース: Finviz.com (Live Data)",
            "",
            "📈 主要ETF価格データ:",
            "-" * 50,
        ]

        # ETFデータを辞書に変換（ティッカーをキーとして）
        etf_data_dict = {}

        # 一括取得データをティッカーベースの辞書に変換
        if isinstance(etf_data_bulk, list):
            for data_item in etf_data_bulk:
                if isinstance(data_item, dict):
                    ticker_key = data_item.get("ticker")
                    if ticker_key:
                        etf_data_dict[ticker_key] = data_item
                else:
                    # オブジェクト形式の場合
                    if hasattr(data_item, "ticker"):
                        ticker_key = getattr(data_item, "ticker")
                        if ticker_key:
                            etf_data_dict[ticker_key] = {
                                "ticker": getattr(data_item, "ticker", ""),
                                "company": getattr(data_item, "company", ""),
                                "price": getattr(data_item, "price", None),
                                "change": getattr(data_item, "change", None),
                                "volume": getattr(data_item, "volume", None),
                                "market_cap": getattr(data_item, "market_cap", None),
                            }

        logger.info(f"Converted {len(etf_data_dict)} ETF records to dictionary")

        # ETFデータの表示（ティッカーベースで検索）
        for ticker in major_etfs:
            try:
                # 辞書からティッカーに対応するデータを取得
                etf_data = etf_data_dict.get(ticker)

                if etf_data and not etf_data.get("error"):
                    name = etf_names.get(ticker, ticker)

                    # データの安全な取得
                    def get_safe_data(key, default="N/A"):
                        value = etf_data.get(key, default)
                        return value if value is not None else default

                    price = get_safe_data("price")
                    change = get_safe_data("change")
                    volume = get_safe_data("volume")
                    market_cap = get_safe_data("market_cap")

                    # フォーマット処理
                    if isinstance(price, (int, float)):
                        price_str = f"${price:.2f}"
                    else:
                        price_str = str(price)

                    # 変動率の処理（Finvizからそのまま使用）
                    if isinstance(change, str) and "%" in change:
                        change_str = change  # 既に%付きの場合
                    elif isinstance(change, (int, float)):
                        change_str = f"{change:+.2f}%"
                    else:
                        change_str = str(change)

                    # 出来高のフォーマット
                    if isinstance(volume, (int, float)):
                        volume_str = f"{int(volume):,}"
                    else:
                        volume_str = str(volume)

                    # 時価総額のフォーマット
                    market_cap_str = str(market_cap) if market_cap != "N/A" else "N/A"

                    # 変動方向の絵文字
                    trend_emoji = (
                        "📈"
                        if change_str.startswith("+")
                        else "📉" if change_str.startswith("-") else "📊"
                    )

                    output_lines.extend(
                        [
                            f"🔹 {ticker} ({name})",
                            f"   💰 価格: {price_str}  {trend_emoji} 変動: {change_str}",
                            f"   📦 出来高: {volume_str}  💼 時価総額: {market_cap_str}",
                            "",
                        ]
                    )
                else:
                    # データが取得できない場合、個別取得を試行
                    logger.warning(
                        f"No data found for {ticker} in bulk result, trying individual fetch..."
                    )
                    try:
                        individual_data = finviz_client.get_stock_fundamentals(
                            ticker,
                            data_fields=[
                                "ticker",
                                "company",
                                "price",
                                "change",
                                "volume",
                                "market_cap",
                            ],
                        )
                        if individual_data:
                            # 個別取得データの処理
                            if hasattr(individual_data, "ticker"):
                                etf_data = {
                                    "ticker": getattr(
                                        individual_data, "ticker", ticker
                                    ),
                                    "company": getattr(individual_data, "company", ""),
                                    "price": getattr(individual_data, "price", None),
                                    "change": getattr(individual_data, "change", None),
                                    "volume": getattr(individual_data, "volume", None),
                                    "market_cap": getattr(
                                        individual_data, "market_cap", None
                                    ),
                                }
                                logger.info(
                                    f"Successfully retrieved individual data for {ticker}"
                                )
                            else:
                                etf_data = individual_data
                        else:
                            etf_data = None
                    except Exception as individual_error:
                        logger.warning(
                            f"Individual fetch also failed for {ticker}: {individual_error}"
                        )
                        etf_data = None

                    # 個別取得が成功した場合、データを表示
                    if etf_data and not etf_data.get("error"):
                        name = etf_names.get(ticker, ticker)

                        # データの安全な取得（個別取得版）
                        def get_safe_data_individual(key, default="N/A"):
                            value = etf_data.get(key, default)
                            return value if value is not None else default

                        price = get_safe_data_individual("price")
                        change = get_safe_data_individual("change")
                        volume = get_safe_data_individual("volume")
                        market_cap = get_safe_data_individual("market_cap")

                        # フォーマット処理
                        if isinstance(price, (int, float)):
                            price_str = f"${price:.2f}"
                        else:
                            price_str = str(price)

                        # 変動率の処理
                        if isinstance(change, str) and "%" in change:
                            change_str = change
                        elif isinstance(change, (int, float)):
                            change_str = f"{change:+.2f}%"
                        else:
                            change_str = str(change)

                        # 出来高のフォーマット
                        if isinstance(volume, (int, float)):
                            volume_str = f"{int(volume):,}"
                        else:
                            volume_str = str(volume)

                        # 時価総額のフォーマット
                        market_cap_str = (
                            str(market_cap) if market_cap != "N/A" else "N/A"
                        )

                        # 変動方向の絵文字
                        trend_emoji = (
                            "📈"
                            if change_str.startswith("+")
                            else "📉" if change_str.startswith("-") else "📊"
                        )

                        output_lines.extend(
                            [
                                f"🔹 {ticker} ({name}) [個別取得]",
                                f"   💰 価格: {price_str}  {trend_emoji} 変動: {change_str}",
                                f"   📦 出来高: {volume_str}  💼 時価総額: {market_cap_str}",
                                "",
                            ]
                        )
                    else:
                        # 全ての取得方法が失敗した場合
                        name = etf_names.get(ticker, ticker)
                        error_msg = (
                            etf_data.get("error", "データなし")
                            if etf_data
                            else "データなし"
                        )
                        output_lines.extend(
                            [
                                f"🔹 {ticker} ({name})",
                                f"   ⚠️ Data fetch error: {error_msg}",
                                "",
                            ]
                        )

            except Exception as e:
                logger.warning(f"Failed to process data for {ticker}: {e}")
                output_lines.extend(
                    [
                        f"🔹 {ticker} ({etf_names.get(ticker, ticker)})",
                        f"   ⚠️ Data processing error: {str(e)[:30]}...",
                        "",
                    ]
                )

        # 市場統計の表示
        output_lines.extend(
            [
                "📊 市場活動統計:",
                "-" * 50,
                f"🔥 出来高急増銘柄数: {volume_surge_count}銘柄",
                f"📈 上昇トレンド銘柄数: {uptrend_count}銘柄",
                f"📋 今週決算発表予定: {earnings_count}銘柄",
                "",
            ]
        )

        # 出来高急増銘柄の詳細統計（データのある銘柄のみで平均、件数を明示）
        if volume_surge_count > 0:
            rel_vol_text = (
                f"{avg_rel_vol:.1f}x ({rel_vol_sample}/{volume_surge_count}銘柄)"
                if avg_rel_vol is not None
                else "N/A (データなし)"
            )
            change_text = (
                f"{avg_change:+.1f}% ({change_sample}/{volume_surge_count}銘柄)"
                if avg_change is not None
                else "N/A (データなし)"
            )
            output_lines.extend(
                [
                    "🔥 出来高急増銘柄詳細:",
                    f"   📊 平均相対出来高: {rel_vol_text}",
                    f"   📈 平均価格変動: {change_text}",
                    "",
                ]
            )

        # 上昇トレンド主要セクター
        if top_sectors:
            output_lines.extend(
                [
                    "📈 上昇トレンド主要セクター:",
                ]
            )
            for sector, count in top_sectors.items():
                output_lines.append(f"   🏢 {sector}: {count}銘柄")
            output_lines.append("")

        output_lines.extend(
            [
                "=" * 70,
                "💡 詳細分析には以下の機能をご利用ください:",
                "🔍 get_stock_fundamentals - 個別銘柄詳細データ",
                "🔥 volume_surge_screener - 出来高急増銘柄詳細",
                "📈 uptrend_screener - 上昇トレンド銘柄詳細",
                "🏢 get_sector_performance - セクター別パフォーマンス分析",
                "",
                "🌐 データソース: Finviz Elite (https://elite.finviz.com/)",
                f"⏰ 最終更新: {pd.Timestamp.now().strftime('%H:%M:%S')}",
            ]
        )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except Exception as e:
        logger.error(f"Error in get_market_overview: {str(e)}")
        raise


@server.tool()
def get_relative_volume_stocks(
    min_relative_volume: Any,
    min_price: Optional[Union[int, float, str]] = None,
    sectors: Optional[List[str]] = None,
    max_results: int = 50,
) -> List[TextContent]:
    """
    相対出来高異常銘柄の検出

    Args:
        min_relative_volume: 最低相対出来高
        min_price: 最低株価
        sectors: 対象セクター
        max_results: 最大取得件数
    """
    try:
        # Build screening parameters
        params = {  # noqa: F841
            "min_relative_volume": min_relative_volume,
            "min_price": min_price,
            "sectors": sectors or [],
            "max_results": max_results or 50,
        }

        # Use volume surge screener as the base
        results = finviz_screener.screen_stocks(
            {
                "relative_volume_min": min_relative_volume,
                "price_min": min_price,
                "sectors": sectors or [],
            }
        )

        # Sort by relative volume, then truncate (keep the pre-truncation total
        # so the summary line can stay honest about what was cut).
        results.sort(key=lambda x: x.relative_volume or 0, reverse=True)
        limit = max_results or 50
        total_matches = len(results)
        results = results[:limit]

        if not results:
            return [
                TextContent(
                    type="text",
                    text=f"No stocks found with relative volume >= {min_relative_volume}x.",
                )
            ]

        # Format output
        output_lines = [
            f"High Relative Volume Stocks (>= {min_relative_volume}x):",
            "=" * 60,
            "",
        ]

        # ヘッダー行
        output_lines.extend(
            [
                f"{'Ticker':<8} {'Company':<25} {'Price':<8} {'Change%':<8} {'Volume':<12} {'Rel Vol':<8}",
                "-" * 70,
            ]
        )

        # データ行
        for stock in results:
            company_short = (
                (stock.company_name[:22] + "...")
                if stock.company_name and len(stock.company_name) > 25
                else (stock.company_name or "N/A")
            )
            price_str = f"${stock.price:.2f}" if stock.price is not None else "N/A"
            change_str = (
                f"{stock.price_change:.2f}%"
                if stock.price_change is not None
                else "N/A"
            )
            volume_str = f"{stock.volume:,}" if stock.volume is not None else "N/A"
            rel_volume_str = (
                f"{stock.relative_volume:.2f}x"
                if stock.relative_volume is not None
                else "N/A"
            )

            output_lines.append(
                f"{stock.ticker:<8} "
                f"{company_short:<25} "
                f"{price_str:<8} "
                f"{change_str:<8} "
                f"{volume_str:<12} "
                f"{rel_volume_str:<8}"
            )

        summary = (
            f"Showing {len(results)} of {total_matches} stocks with unusual "
            f"volume activity (max_results={limit})."
        )
        output_lines.extend(["", summary])

        return [TextContent(type="text", text="\n".join(output_lines))]

    except Exception as e:
        logger.error(f"Error in get_relative_volume_stocks: {str(e)}")
        raise


@server.tool()
def technical_analysis_screener(
    rsi_min: Optional[Union[int, float, str]] = None,
    rsi_max: Optional[Union[int, float, str]] = None,
    price_vs_sma20: Optional[str] = None,
    price_vs_sma50: Optional[str] = None,
    price_vs_sma200: Optional[str] = None,
    min_price: Optional[Union[int, float, str]] = None,
    min_volume: Optional[Union[int, float]] = None,
    sectors: Optional[List[str]] = None,
    max_results: int = 50,
) -> List[TextContent]:
    """
    テクニカル分析ベースのスクリーニング

    Args:
        rsi_min: RSI最低値
        rsi_max: RSI最高値
        price_vs_sma20: 20日移動平均との関係 (above, below)
        price_vs_sma50: 50日移動平均との関係 (above, below)
        price_vs_sma200: 200日移動平均との関係 (above, below)
        min_price: 最低株価
        min_volume: 最低出来高（当日出来高、sh_curvol_* に変換）
        sectors: 対象セクター
        max_results: 最大取得件数（ティッカー昇順の先頭N件）

    Note:
        "below" 指定は ``ta_sma*_pb`` として実際に送られる（以前はフィルタ
        キーを読む処理が無く、全銘柄が返っていた: audit B6）。条件を何も
        指定しない場合は全銘柄が対象になるため、返すのはティッカー昇順の
        先頭 ``max_results`` 件で、一致総数も併記する（audit B28）。
    """
    try:
        # Build screening parameters via the screener's own builder so the
        # printed criteria cannot drift from the query.
        params = {
            "rsi_min": rsi_min,
            "rsi_max": rsi_max,
            "price_vs_sma20": price_vs_sma20,
            "price_vs_sma50": price_vs_sma50,
            "price_vs_sma200": price_vs_sma200,
            "min_price": min_price,
            "min_volume": min_volume,
            "sectors": sectors,
            "max_results": max_results,
        }
        params = {key: value for key, value in params.items() if value is not None}

        filters = finviz_screener._build_technical_analysis_filters(**params)
        results, total_matches = finviz_screener.technical_analysis_screener(**params)

        if not results:
            return [
                TextContent(
                    type="text", text="No stocks found matching technical criteria."
                )
            ]

        shown = len(results)
        header = f"Technical Analysis Screening Results ({shown} of {total_matches} matches shown):"
        output_lines = (
            [header]
            + _criteria_block(
                filters,
                client=finviz_screener,
                extra=["Order: ticker ascending (no ranking metric for this screen)"],
                title="Criteria:" if filters else "Criteria: none (all stocks)",
            )
            + [
                "=" * 60,
                "",
            ]
        )

        for stock in results:
            output_lines.extend(
                [
                    f"Ticker: {stock.ticker}",
                    f"Company: {stock.company_name}",
                    f"Sector: {stock.sector}",
                    (
                        f"Price: ${stock.price:.2f}"
                        if stock.price is not None
                        else "Price: N/A"
                    ),
                    f"RSI: {stock.rsi:.2f}" if stock.rsi is not None else "RSI: N/A",
                    # sma_20/50/200 hold *derived dollar prices* (see
                    # _compute_sma_fields); the percent distance from price is
                    # the *_relative twin. Label each with its real unit.
                    _format_sma_line("SMA 20", stock.sma_20, stock.sma_20_relative),
                    _format_sma_line("SMA 50", stock.sma_50, stock.sma_50_relative),
                    _format_sma_line("SMA 200", stock.sma_200, stock.sma_200_relative),
                    (
                        f"Volume: {stock.volume:,.0f}"
                        if stock.volume is not None
                        else "Volume: N/A"
                    ),
                    "-" * 40,
                    "",
                ]
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except Exception as e:
        logger.error(f"Error in technical_analysis_screener: {str(e)}")
        raise


def cli_main():
    """CLI entry point - supports stdio (default) and sse transport for Docker.

    The HTTP/SSE bind defaults to ``127.0.0.1`` (loopback). Override with
    ``MCP_HOST=0.0.0.0`` only when you need the server reachable from
    outside the host (e.g. inside a Docker container with host port
    mapping). See README and Finding #6 in reviews/REVIEW_TRACKING.md.
    """
    transport = os.getenv("MCP_TRANSPORT", "stdio")

    if transport in ("sse", "streamable-http"):
        host = os.getenv("MCP_HOST", "127.0.0.1")
        port = int(os.getenv("MCP_PORT", "8000"))
        if host == "0.0.0.0":  # noqa: S104 - intentional opt-in pattern
            logger.warning(
                "MCP_HOST=0.0.0.0 binds the server to all network "
                "interfaces. For local-only access, use MCP_HOST=127.0.0.1 "
                "(the new default). If you are running in Docker and need "
                "host-side access, keep MCP_HOST=0.0.0.0 inside the "
                "container and restrict exposure via host port mapping "
                "(e.g. -p 127.0.0.1:8000:8000). Public exposure also "
                "requires DNS rebinding protection — see Finding #6 in "
                "reviews/REVIEW_TRACKING.md."
            )
        logger.info(f"Starting MCP server with {transport} transport on {host}:{port}")
        server.run(transport=transport, host=host, port=port)
    else:
        server.run()


@server.tool()
def earnings_winners_screener(
    earnings_period: Optional[str] = "this_week",
    market_cap: Optional[str] = "smallover",
    min_price: Optional[Union[int, float, str]] = 10.0,
    min_avg_volume: Optional[str] = "o500",
    min_eps_growth_qoq: Optional[float] = 10.0,
    min_eps_revision: Optional[float] = 5.0,
    min_sales_growth_qoq: Optional[float] = 5.0,
    min_weekly_performance: Optional[str] = "5to-1w",
    sma200_filter: Optional[bool] = True,
    target_sectors: Optional[List[str]] = None,
    max_results: int = 50,
    sort_by: Optional[str] = "performance_1w",
    sort_order: Optional[str] = "desc",
) -> List[TextContent]:
    """
    決算勝ち組銘柄のスクリーニング - 週間パフォーマンス、EPSサプライズ、売上サプライズを含む詳細一覧

    Finviz URLと同一の条件・データで決算後に上昇した銘柄を検索し、表形式で詳細データを表示します。
    取得データには以下が含まれます：
    - 週間パフォーマンス（Performance Week）
    - EPSサプライズ（EPS Surprise）
    - 売上サプライズ（Revenue Surprise）
    - EPS前四半期比成長率（EPS QoQ Growth）
    - 売上前四半期比成長率（Sales QoQ Growth）
    - 基本的な株価・出来高データ

    Args:
        earnings_period: 決算発表期間 ('this_week', 'yesterday', 'today', 'custom')
        market_cap: 時価総額フィルタ ('small', 'mid', 'large', 'mega', 'smallover')
        min_price: 最低株価 (デフォルト: $10)
        min_avg_volume: 最低平均出来高 (数値または文字列形式、デフォルト: "o500" = 500,000以上)
        min_eps_growth_qoq: 最低EPS前四半期比成長率(%) (デフォルト: 10%)
        min_eps_revision: 最低EPS予想改訂率(%) (デフォルト: 5%)
        min_sales_growth_qoq: 最低売上前四半期比成長率(%) (デフォルト: 5%)
        min_weekly_performance: 週次パフォーマンスフィルタ (デフォルト: 5to-1w)
        sma200_filter: 200日移動平均線上のフィルタ (デフォルト: True)
        target_sectors: 対象セクター (デフォルト: 主要6セクター)
        max_results: 最大取得件数 (デフォルト: 50)
        sort_by: ソート基準 ('performance_1w', 'eps_growth_qoq', 'eps_surprise', 'price_change', 'volume')
        sort_order: ソート順序 ('asc', 'desc')

    Returns:
        決算勝ち組銘柄の詳細一覧（表形式 + 分析データ + Finviz URL）
        - メインテーブル: 銘柄 | 企業名 | セクター | 株価 | 週間パフォーマンス | EPSサプライズ | 売上サプライズ | 決算日
        - 上位5銘柄の詳細分析
        - EPSサプライズ統計
        - セクター別パフォーマンス分析
        - 元データのFinviz URL（CSV export形式）
    """
    try:
        # パラメータの準備
        params = {
            "earnings_period": earnings_period,
            "market_cap": market_cap,
            "min_price": min_price,
            "min_avg_volume": min_avg_volume,
            "min_eps_growth_qoq": min_eps_growth_qoq,
            "min_eps_revision": min_eps_revision,
            "min_sales_growth_qoq": min_sales_growth_qoq,
            "min_weekly_performance": min_weekly_performance,
            "sma200_filter": sma200_filter,
            "max_results": max_results,
            "sort_by": sort_by,
            "sort_order": sort_order,
        }

        # セクター設定
        if target_sectors:
            params["target_sectors"] = target_sectors
        else:
            params["target_sectors"] = [
                "Technology",
                "Industrials",
                "Healthcare",
                "Communication Services",
                "Consumer Cyclical",
                "Financial Services",
            ]

        # earnings_dateパラメータの設定
        if earnings_period == "this_week":
            params["earnings_date"] = "thisweek"
        elif earnings_period == "yesterday":
            params["earnings_date"] = "yesterday"
        elif earnings_period == "today":
            params["earnings_date"] = "today"
        else:
            params["earnings_date"] = "thisweek"  # デフォルト

        logger.info(f"Executing earnings winners screening with params: {params}")

        # スクリーニング実行。
        # 以前はここに earnings_screener へのフォールバックがあったが、
        # (a) 当時のクライアントは例外を [] に潰していたため到達不能で、
        # (b) リクエスト失敗時に別フィルタで再実行すると、ユーザーが求めた
        #     条件とは違う結果を「決算勝ち組」として返してしまう。
        # 失敗はそのまま FinvizAPIError として MCP エラーに変換させる。
        applied_filters = finviz_screener._build_earnings_winners_filters(**params)
        results = finviz_screener.earnings_winners_screener(**params)

        if not results:
            return [
                TextContent(
                    type="text", text="No earnings winners found matching the criteria."
                )
            ]

        # 結果の表示（条件は実際のフィルタから描画する）
        applied_filters = dict(applied_filters)
        applied_filters["sort_by"] = sort_by
        applied_filters["sort_order"] = sort_order
        output_lines = _format_earnings_winners_list(results, applied_filters)

        return [TextContent(type="text", text="\n".join(output_lines))]

    except Exception as e:
        logger.error(f"Error in earnings_winners_screener: {str(e)}")
        raise


@server.tool()
def upcoming_earnings_screener(
    earnings_period: Optional[str] = "next_week",
    market_cap: Optional[str] = "smallover",
    min_price: Optional[Union[int, float, str]] = 10,
    min_avg_volume: Optional[
        str
    ] = "o500",  # Support both numeric and string values - converts internally
    target_sectors: Optional[List[str]] = None,
    max_results: int = 100,
    sort_by: Optional[str] = "earnings_date",
    sort_order: Optional[str] = "asc",
    include_chart_view: Optional[bool] = True,
    earnings_calendar_format: Optional[bool] = False,
    custom_date_range: Optional[
        str
    ] = None,  # 新機能: カスタム日付範囲 (例: "06-30-2025x07-04-2025")
    start_date: Optional[str] = None,  # 新機能: 開始日 (YYYY-MM-DD format)
    end_date: Optional[str] = None,  # 新機能: 終了日 (YYYY-MM-DD format)
) -> List[TextContent]:
    """
    来週決算予定銘柄のスクリーニング（決算トレード事前準備用）

    Args:
        earnings_period: 決算発表期間
            ('next_week', 'next_5_days', 'this_week', 'this_month',
             'next_2_weeks', 'next_month')
        market_cap: 時価総額フィルタ ('small', 'mid', 'large', 'mega', 'smallover', ...)
        min_price: 最低株価
        min_avg_volume: 最低平均出来高（株数、または 'o500' 形式）
        target_sectors: 対象セクター（8セクター）
        max_results: 最大取得件数（ソート後に適用）
        sort_by: ソート基準 ('earnings_date', 'market_cap', 'target_price_upside', 'volatility', 'ticker')
        sort_order: ソート順序 ('asc', 'desc')
        include_chart_view: 週足チャートビューを含める
        earnings_calendar_format: 決算カレンダー形式で出力
        custom_date_range: カスタム日付範囲（Finviz形式: "MM-DD-YYYYxMM-DD-YYYY"）
        start_date: 開始日（YYYY-MM-DD形式、end_dateと組み合わせて使用）
        end_date: 終了日（YYYY-MM-DD形式、start_dateと組み合わせて使用）

    Returns:
        決算予定銘柄のスクリーニング結果

    Note:
        - ``next_2_weeks`` / ``next_month`` は日付範囲
          (``earningsdate_MM-DD-YYYYxMM-DD-YYYY``、検証済み) として実行する。
          以前は ``nextdays5``（5営業日）と ``thismonth``（今月）を送っており、
          表示ラベルと実際の期間が食い違っていた（audit B15）。
          ``earningsdate_nextmonth`` / ``earningsdate_nextdays10`` は
          プローブの結果Finvizに存在しない（全銘柄が返る）。
        - ``pre_earnings_analysis`` / ``risk_assessment`` / ``data_fields`` は
          受け取っても捨てていたので削除した（audit B17）。
    """
    try:
        # パラメータの準備と正規化
        params = {
            "earnings_period": earnings_period,
            "market_cap": market_cap,
            "min_price": min_price,
            "max_results": max_results,
            "sort_by": sort_by,
            "sort_order": sort_order,
        }

        # 出来高パラメータ。以前は avg_volume_min / average_volume という
        # 別名で入れていたが、フィルタ構築側は min_avg_volume しか読まず、
        # 指定は常に捨てられて既定の500Kが適用されていた（audit B4）。
        if min_avg_volume is not None:
            params["min_avg_volume"] = min_avg_volume

        # セクターの正規化 - upcoming_earnings_screenで使用されるパラメータ名に合わせる
        if target_sectors:
            params["target_sectors"] = target_sectors
        else:
            params["target_sectors"] = [
                "Technology",
                "Industrials",
                "Healthcare",
                "Communication Services",
                "Consumer Cyclical",
                "Financial Services",
                "Consumer Defensive",
                "Basic Materials",
            ]

        # earnings_dateパラメータの設定（優先順位順）
        # 1. カスタム日付範囲が指定されている場合
        if custom_date_range:
            params["earnings_date"] = custom_date_range
            period_label = f"custom range {custom_date_range}"
        # 2. 開始日と終了日が両方指定されている場合
        elif start_date and end_date:
            params["earnings_date"] = {"start": start_date, "end": end_date}
            period_label = f"{start_date} .. {end_date}"
        # 3. 期間指定（実在するトークン／日付範囲だけに解決する: audit B15）
        else:
            params["earnings_date"] = FinvizScreener.earnings_period_to_finviz(
                earnings_period
            )
            period_label = FinvizScreener.describe_earnings_period(earnings_period)

        # スクリーニング実行 - 新しいadvanced_screenメソッドを使用
        logger.info(f"Executing upcoming earnings screening with params: {params}")
        logger.info(f"Final earnings_date parameter: {params.get('earnings_date')}")
        # upcoming_earnings_screenメソッドを使用。
        # 旧フォールバック（earnings_screener での再実行）は削除:
        # クライアントが例外を [] に潰していたため到達不能なうえ、
        # 失敗時に別条件の結果を返してしまう。
        applied_filters = finviz_screener._build_upcoming_earnings_filters(**params)
        results = finviz_screener.upcoming_earnings_screener(**params)

        if not results:
            return [TextContent(type="text", text="No upcoming earnings stocks found.")]

        # 結果の表示
        if earnings_calendar_format:
            body = _format_earnings_calendar(results, include_chart_view)
        else:
            body = _format_upcoming_earnings_list(results, include_chart_view)

        output_lines = (
            _criteria_block(
                applied_filters,
                client=finviz_screener,
                extra=[
                    f"Period requested: {period_label}",
                    f"Sort: {sort_by} ({sort_order}), applied before the cut",
                ],
            )
            + ["", "=" * 70, ""]
            + body
        )

        # NOTE: この下には以前「CSV export does not include earnings date」
        # という注意書きが付いていたが、事実に反する（Earnings Date は列68
        # として取得しており、上の一覧にも表示している）ので削除した
        # （audit B24）。
        output_lines.extend(
            [
                "",
                "🔗 Finviz URL with your filters:",
                f"    {_generate_finviz_url(market_cap, params.get('earnings_date', 'nextweek'))}",
            ]
        )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except Exception as e:
        logger.error(f"Error in upcoming_earnings_screener: {str(e)}")
        raise


def _format_earnings_winners_list(results: List, params: Dict[str, Any]) -> List[str]:
    """決算後上昇銘柄をリスト形式でフォーマット"""

    # 安全に数値を取得するヘルパー関数
    def safe_float(value, default=0.0):
        try:
            return float(value) if value is not None else default
        except (ValueError, TypeError):
            return default

    # 条件は実際に走ったフィルタ辞書から描画する（ハードコードした
    # "($300M+)" のような注釈は market_cap を変えると嘘になる）。
    output_lines = (
        [
            "📈 決算勝ち組銘柄一覧 - WeeklyパフォーマンスとEPSサプライズ",
            "",
        ]
        + _criteria_block(params, title="🎯 スクリーニング条件:")
        + [
            "",
            "=" * 120,
            "",
        ]
    )

    # テーブルヘッダー
    output_lines.extend(
        [
            "| 銘柄    | 企業名                              | セクター        | 株価    | 週間パフォーマンス | EPSサプライズ | 売上サプライズ | 決算日      |",
            "|---------|-------------------------------------|-----------------|---------|-------------------|---------------|---------------|-------------|",
        ]
    )

    for stock in results:
        # データの整理
        ticker = stock.ticker or "N/A"
        company = (stock.company_name or "N/A")[:35]  # 35文字に制限
        sector = (stock.sector or "N/A")[:15]  # 15文字に制限
        price = f"${stock.price:.2f}" if stock.price is not None else "N/A"

        # 週間パフォーマンス／サプライズ。符号は値そのものから出す:
        # "+" をハードコードしていたため -3.2% が "+-3.2%" と表示されていた
        # （audit B26）。0.0 も正当な値なので ``is not None`` で判定する。
        weekly_perf = (
            f"{stock.performance_1w:+.1f}%"
            if stock.performance_1w is not None
            else "N/A"
        )

        # EPSサプライズ
        eps_surprise = (
            f"{stock.eps_surprise:+.1f}%" if stock.eps_surprise is not None else "N/A"
        )

        # 売上サプライズ
        revenue_surprise = (
            f"{stock.revenue_surprise:+.1f}%"
            if stock.revenue_surprise is not None
            else "N/A"
        )

        # 決算日
        earnings_date = stock.earnings_date or "N/A"

        # テーブル行を作成
        row = f"| {ticker:<7} | {company:<35} | {sector:<15} | {price:<7} | {weekly_perf:>17} | {eps_surprise:>13} | {revenue_surprise:>13} | {earnings_date:<11} |"
        output_lines.append(row)

    output_lines.extend(["", "=" * 120, "", "🎯 パフォーマンス分析:", ""])

    # 上位パフォーマーの詳細分析（0.0% も「値がある」ので除外しない）
    if results:
        top_performers = sorted(
            [s for s in results if s.performance_1w is not None],
            key=lambda x: x.performance_1w,
            reverse=True,
        )[:5]

        output_lines.append("📈 週間パフォーマンス上位5銘柄:")
        for i, stock in enumerate(top_performers, 1):
            output_lines.extend(
                [
                    "",
                    f"🏆 #{i} **{stock.ticker}** - {stock.company_name}",
                    f"   📊 週間パフォーマンス: **{stock.performance_1w:+.1f}%**",
                    (
                        f"   💰 株価: ${stock.price:.2f}"
                        if stock.price is not None
                        else "   💰 株価: N/A"
                    ),
                    (
                        f"   🎯 EPSサプライズ: {stock.eps_surprise:+.1f}%"
                        if stock.eps_surprise is not None
                        else "   🎯 EPSサプライズ: N/A"
                    ),
                    (
                        f"   📈 売上サプライズ: {stock.revenue_surprise:+.1f}%"
                        if stock.revenue_surprise is not None
                        else "   📈 売上サプライズ: N/A"
                    ),
                    f"   🏢 セクター: {stock.sector}",
                    (
                        f"   📅 決算日: {stock.earnings_date}"
                        if stock.earnings_date
                        else "   📅 決算日: N/A"
                    ),
                ]
            )

            # 追加メトリクス
            metrics = []
            if stock.eps_qoq_growth or stock.eps_growth_qtr:
                eps_growth = safe_float(stock.eps_qoq_growth or stock.eps_growth_qtr)
                metrics.append(f"EPS QoQ: {eps_growth:.1f}%")
            if stock.sales_qoq_growth or stock.sales_growth_qtr:
                sales_growth = safe_float(
                    stock.sales_qoq_growth or stock.sales_growth_qtr
                )
                metrics.append(f"売上QoQ: {sales_growth:.1f}%")
            if stock.volume and stock.avg_volume and safe_float(stock.avg_volume) > 0:
                rel_vol = safe_float(stock.volume) / safe_float(stock.avg_volume)
                metrics.append(f"相対出来高: {rel_vol:.1f}x")
            if stock.pe_ratio:
                metrics.append(f"PER: {safe_float(stock.pe_ratio):.1f}")

            if metrics:
                output_lines.append(f"   📋 財務指標: {' | '.join(metrics)}")

    # サプライズ分析
    surprise_stocks = [
        s for s in results if s.eps_surprise and safe_float(s.eps_surprise) > 0
    ]
    if surprise_stocks:
        avg_eps_surprise = sum(
            safe_float(s.eps_surprise) for s in surprise_stocks
        ) / len(surprise_stocks)
        max_eps_surprise = max(safe_float(s.eps_surprise) for s in surprise_stocks)

        output_lines.extend(
            [
                "",
                "🎯 EPSサプライズ分析:",
                f"   • 平均EPSサプライズ: {avg_eps_surprise:.1f}%",
                f"   • 最大EPSサプライズ: {max_eps_surprise:.1f}%",
                f"   • ポジティブサプライズ銘柄数: {len(surprise_stocks)}件",
            ]
        )

    # セクター分析
    sector_performance = {}
    for stock in results:
        if stock.sector and stock.performance_1w:
            perf_value = safe_float(stock.performance_1w)
            if perf_value != 0:  # 有効な値のみ追加
                if stock.sector not in sector_performance:
                    sector_performance[stock.sector] = []
                sector_performance[stock.sector].append(perf_value)

    if sector_performance:
        output_lines.extend(
            [
                "",
                "🏢 セクター別パフォーマンス:",
            ]
        )

        for sector, performances in sector_performance.items():
            avg_perf = sum(performances) / len(performances)
            count = len(performances)
            output_lines.append(f"   • {sector}: 平均 {avg_perf:.1f}% ({count}銘柄)")

    # NOTE: this used to append a "verify on Finviz" export URL, but it
    # embedded the caller's Elite API key in the tool output (a guaranteed
    # key disclosure, audit B25) and did not reproduce the actual query
    # (hardcoded sort/sectors). Screener URLs must never carry `auth=`.
    output_lines.extend(
        [
            "",
            "💡 これらの銘柄は最近決算を発表し、強いパフォーマンスと良好なファンダメンタル指標を示しています。",
            "   モメンタム取引や詳細分析の対象として検討してください。",
        ]
    )

    return output_lines


def _generate_finviz_url(market_cap: str, earnings_date) -> str:
    """Finviz URLを生成"""
    base_url = "https://elite.finviz.com/screener.ashx?v=311&f="

    # Market cap filter
    cap_filter = f"cap_{market_cap or 'smallover'}"

    # Earnings date filter
    if isinstance(earnings_date, dict):
        # 辞書形式の場合（start/end）
        from .finviz_client.base import FinvizClient

        client = FinvizClient()
        start_formatted = client._format_date_for_finviz(earnings_date["start"])
        end_formatted = client._format_date_for_finviz(earnings_date["end"])
        earnings_filter = f"earningsdate_{start_formatted}x{end_formatted}"
    elif isinstance(earnings_date, str) and "x" in earnings_date:
        # 日付範囲文字列の場合
        earnings_filter = f"earningsdate_{earnings_date}"
    else:
        # 固定期間の場合
        earnings_filter = f"earningsdate_{earnings_date}"

    return f"{base_url}{cap_filter},{earnings_filter}"


def _format_upcoming_earnings_list(
    results: List, include_chart_view: bool = True
) -> List[str]:
    """来週決算予定銘柄をリスト形式でフォーマット"""
    output_lines = [
        f"Upcoming Earnings Screening Results ({len(results)} stocks found):",
        "=" * 70,
        "",
    ]

    for stock in results:
        output_lines.extend(
            [
                f"📈 {stock.ticker} - {stock.company_name}",
                f"   Sector: {stock.sector} | Industry: {stock.industry}",
                f"   Earnings Date: {stock.earnings_date or 'Not available in CSV'} | Timing: {stock.earnings_timing or 'N/A'}",
                (
                    f"   Current Price: ${stock.current_price:.2f}"
                    if stock.current_price is not None
                    else "   Current Price: N/A"
                ),
                (
                    f"   Market Cap: {format_large_number(stock.market_cap * 1e6)}"
                    if stock.market_cap is not None
                    else "   Market Cap: N/A"
                ),
                (
                    f"   PE Ratio: {stock.pe_ratio:.2f}"
                    if stock.pe_ratio is not None
                    else "   PE Ratio: N/A"
                ),
                (
                    f"   Target Price: ${stock.target_price:.2f}"
                    if stock.target_price is not None
                    else "   Target Price: N/A"
                ),
                (
                    f"   Target Upside: {stock.target_price_upside:.1f}%"
                    if stock.target_price_upside is not None
                    else "   Target Upside: N/A"
                ),
                (
                    f"   Analyst Recommendation: {stock.analyst_recommendation}"
                    if stock.analyst_recommendation
                    else "   Analyst Recommendation: N/A"
                ),
                (
                    f"   Volatility: {stock.volatility:.2f}"
                    if stock.volatility is not None
                    else "   Volatility: N/A"
                ),
                (
                    f"   Short Interest: {stock.short_interest:.1f}%"
                    if stock.short_interest is not None
                    else "   Short Interest: N/A"
                ),
                (
                    f"   Avg Volume: {format_large_number(stock.avg_volume)}"
                    if stock.avg_volume is not None
                    else "   Avg Volume: N/A"
                ),
                "",
            ]
        )

        # Additional metrics (if available)
        additional_metrics = []
        if stock.performance_1w is not None:
            additional_metrics.append(
                f"   • 1W Performance: {stock.performance_1w:.1f}%"
            )
        if stock.performance_1m is not None:
            additional_metrics.append(
                f"   • 1M Performance: {stock.performance_1m:.1f}%"
            )
        if stock.rsi is not None:
            additional_metrics.append(f"   • RSI: {stock.rsi:.1f}")

        if additional_metrics:
            output_lines.extend(["   📊 Additional Metrics:", *additional_metrics, ""])

        output_lines.append("-" * 70)
        output_lines.append("")

    return output_lines


def _format_earnings_calendar(
    results: List, include_chart_view: bool = True
) -> List[str]:
    """来週決算予定銘柄をカレンダー形式でフォーマット"""
    output_lines = [
        f"📅 Upcoming Earnings Calendar ({len(results)} stocks)",
        "=" * 70,
        "",
    ]

    # 日付ごとにグループ化
    by_date = {}
    for stock in results:
        date = stock.earnings_date or "Unknown"
        if date not in by_date:
            by_date[date] = []
        by_date[date].append(stock)

    # 日付順でソート
    for date in sorted(by_date.keys()):
        stocks = by_date[date]
        output_lines.extend([f"📅 {date}", "-" * 30, ""])

        for stock in stocks:
            upside_str = (
                f"(+{stock.target_price_upside:.1f}%)"
                if stock.target_price_upside and stock.target_price_upside > 0
                else ""
            )
            output_lines.extend(
                [
                    f"  • {stock.ticker} - {stock.company_name}",
                    (
                        f"    ${stock.current_price:.2f} → ${stock.target_price:.2f} {upside_str}"
                        if stock.current_price and stock.target_price
                        else (
                            f"    Current: ${stock.current_price:.2f}"
                            if stock.current_price is not None
                            else "    Price: N/A"
                        )
                    ),
                    (
                        f"    {stock.sector} | PE: {stock.pe_ratio:.1f}"
                        if stock.pe_ratio is not None
                        else f"    {stock.sector}"
                    ),
                    "",
                ]
            )

        output_lines.append("")

    return output_lines


def _format_earnings_premarket_list(results: List, params: Dict[str, Any]) -> List[str]:
    """寄り付き前決算上昇銘柄の詳細フォーマット"""

    def format_large_number(num):
        # 0 is a real reading (a halted name really did trade 0 shares);
        # only a missing value is "N/A".
        if num is None:
            return "N/A"
        if num >= 1_000_000_000:
            return f"{num/1_000_000_000:.1f}B"
        elif num >= 1_000_000:
            return f"{num/1_000_000:.1f}M"
        elif num >= 1_000:
            return f"{num/1_000:.1f}K"
        else:
            return f"{num:.0f}"

    output_lines = (
        [
            "🔍 Premarket Earnings Screening Results",
            f"📊 Stocks Detected: {len(results)}",
            "=" * 100,
            "",
        ]
        # ハードコードされた条件文（"$10" / "Small+"）は実際のフィルタと
        # 食い違っていた（audit B14）。フィルタ辞書から描画する。
        + _criteria_block(
            params, client=finviz_screener, title="📋 Applied Screening Criteria:"
        )
        + [
            "",
            "=" * 100,
            "",
        ]
    )

    # 詳細な銘柄一覧
    output_lines.extend(
        [
            "📈 Detailed Data:",
            "",
            "| Ticker | Company | Sector | Price | Change | PreMkt | EPS Surprise | Revenue Surprise | Perf 1W | Volume |",
            "|--------|---------|--------|-------|--------|--------|--------------|------------------|---------|--------|",
        ]
    )

    for i, stock in enumerate(results[:10]):  # 上位10銘柄
        price_str = f"${stock.price:.2f}" if stock.price is not None else "N/A"
        change_str = (
            f"{stock.price_change:+.2f}%" if stock.price_change is not None else "N/A"
        )
        premarket_str = (
            f"{stock.premarket_change_percent:+.2f}%"
            if stock.premarket_change_percent is not None
            else "N/A"
        )
        eps_surprise_str = (
            f"{stock.eps_surprise:+.2f}%" if stock.eps_surprise is not None else "N/A"
        )
        revenue_surprise_str = (
            f"{stock.revenue_surprise:+.2f}%"
            if stock.revenue_surprise is not None
            else "N/A"
        )
        perf_1w_str = (
            f"{stock.performance_1w:+.2f}%"
            if stock.performance_1w is not None
            else "N/A"
        )
        volume_str = (
            format_large_number(stock.volume) if stock.volume is not None else "N/A"
        )

        ticker_display = stock.ticker or "N/A"
        company_display = (
            (stock.company_name[:15] + "...")
            if stock.company_name and len(stock.company_name) > 15
            else (stock.company_name or "N/A")
        )
        sector_display = (
            (stock.sector[:12] + "...")
            if stock.sector and len(stock.sector) > 12
            else (stock.sector or "N/A")
        )

        output_lines.append(
            f"| {ticker_display:<6} | {company_display:<15} | {sector_display:<12} | {price_str:<7} | {change_str:<8} | {premarket_str:<8} | {eps_surprise_str:<12} | {revenue_surprise_str:<16} | {perf_1w_str:<7} | {volume_str:<6} |"
        )

    output_lines.extend(["", "=" * 100, "", "🏆 上位5銘柄の詳細分析:", ""])

    # 上位5銘柄の詳細情報
    for i, stock in enumerate(results[:5], 1):
        output_lines.extend(
            [
                f"#{i} 📊 {stock.ticker} - {stock.company_name}",
                (
                    "   📈 Price: "
                    + (f"${stock.price:.2f}" if stock.price is not None else "N/A")
                    + " | Change: "
                    + (
                        f"{stock.price_change:+.2f}%"
                        if stock.price_change is not None
                        else "N/A"
                    )
                ),
                (
                    f"   🔔 Premarket: {stock.premarket_change_percent:.2f}%"
                    if stock.premarket_change_percent is not None
                    else "   🔔 Premarket: N/A"
                ),
                (
                    f"   💼 Sector: {stock.sector} | Volume: {format_large_number(stock.volume)}"
                    if stock.sector and stock.volume
                    else f"   💼 Sector: {stock.sector or 'N/A'} | Volume: {format_large_number(stock.volume) if stock.volume is not None else 'N/A'}"
                ),
                (
                    f"   📊 EPS Surprise: {stock.eps_surprise:.2f}%"
                    if stock.eps_surprise is not None
                    else "   📊 EPS Surprise: N/A"
                ),
                (
                    f"   💰 Revenue Surprise: {stock.revenue_surprise:.2f}%"
                    if stock.revenue_surprise is not None
                    else "   💰 Revenue Surprise: N/A"
                ),
                (
                    f"   📈 Performance 1W: {stock.performance_1w:.2f}%"
                    if stock.performance_1w is not None
                    else "   📈 Performance 1W: N/A"
                ),
                "",
            ]
        )

    # 統計情報
    eps_surprises = [s.eps_surprise for s in results if s.eps_surprise is not None]
    revenue_surprises = [  # noqa: F841
        s.revenue_surprise for s in results if s.revenue_surprise is not None
    ]

    if eps_surprises:
        avg_eps = sum(eps_surprises) / len(eps_surprises)
        max_eps = max(eps_surprises)
        output_lines.extend(
            [
                "📊 EPSサプライズ統計:",
                f"   • 平均: {avg_eps:.2f}%",
                f"   • 最大: {max_eps:.2f}%",
                f"   • サンプル数: {len(eps_surprises)}",
                "",
            ]
        )

    # セクター別分析
    sector_counts = {}
    for stock in results:
        if stock.sector:
            sector_counts[stock.sector] = sector_counts.get(stock.sector, 0) + 1

    if sector_counts:
        output_lines.extend(
            [
                "🏢 セクター別分析:",
                *[
                    f"   • {sector}: {count}銘柄"
                    for sector, count in sorted(
                        sector_counts.items(), key=lambda x: x[1], reverse=True
                    )[:5]
                ],
                "",
            ]
        )

    return output_lines


def _format_earnings_afterhours_list(
    results: List, params: Dict[str, Any]
) -> List[str]:
    """時間外決算上昇銘柄の詳細フォーマット"""

    def format_large_number(num):
        # 0 is a real reading (a halted name really did trade 0 shares);
        # only a missing value is "N/A".
        if num is None:
            return "N/A"
        if num >= 1_000_000_000:
            return f"{num/1_000_000_000:.1f}B"
        elif num >= 1_000_000:
            return f"{num/1_000_000:.1f}M"
        elif num >= 1_000:
            return f"{num/1_000:.1f}K"
        else:
            return f"{num:.0f}"

    output_lines = (
        [
            "🌙 After-Hours Earnings Screening Results",
            f"📊 Stocks Detected: {len(results)}",
            "=" * 100,
            "",
        ]
        # 実際のフィルタから描画（audit B14）
        + _criteria_block(
            params, client=finviz_screener, title="📋 Applied Screening Criteria:"
        )
        + [
            "",
            "=" * 100,
            "",
        ]
    )

    # 詳細な銘柄一覧
    output_lines.extend(
        [
            "📈 Detailed Data:",
            "",
            "| Ticker | Company | Sector | Price | Change | AftHrs | EPS Surprise | Revenue Surprise | Perf 1W | Volume |",
            "|--------|---------|--------|-------|--------|--------|--------------|------------------|---------|--------|",
        ]
    )

    for i, stock in enumerate(results[:10]):  # 上位10銘柄
        price_str = f"${stock.price:.2f}" if stock.price is not None else "N/A"
        change_str = (
            f"{stock.price_change:+.2f}%" if stock.price_change is not None else "N/A"
        )
        afterhours_str = (
            f"{stock.afterhours_change_percent:+.2f}%"
            if stock.afterhours_change_percent is not None
            else "N/A"
        )
        eps_surprise_str = (
            f"{stock.eps_surprise:+.2f}%" if stock.eps_surprise is not None else "N/A"
        )
        revenue_surprise_str = (
            f"{stock.revenue_surprise:+.2f}%"
            if stock.revenue_surprise is not None
            else "N/A"
        )
        perf_1w_str = (
            f"{stock.performance_1w:+.2f}%"
            if stock.performance_1w is not None
            else "N/A"
        )
        volume_str = (
            format_large_number(stock.volume) if stock.volume is not None else "N/A"
        )

        ticker_display = stock.ticker or "N/A"
        company_display = (
            (stock.company_name[:15] + "...")
            if stock.company_name and len(stock.company_name) > 15
            else (stock.company_name or "N/A")
        )
        sector_display = (
            (stock.sector[:12] + "...")
            if stock.sector and len(stock.sector) > 12
            else (stock.sector or "N/A")
        )

        output_lines.append(
            f"| {ticker_display:<6} | {company_display:<15} | {sector_display:<12} | {price_str:<7} | {change_str:<8} | {afterhours_str:<8} | {eps_surprise_str:<12} | {revenue_surprise_str:<16} | {perf_1w_str:<7} | {volume_str:<6} |"
        )

    output_lines.extend(["", "=" * 100, "", "🏆 上位5銘柄の詳細分析:", ""])

    # 上位5銘柄の詳細情報
    for i, stock in enumerate(results[:5], 1):
        output_lines.extend(
            [
                f"#{i} 📊 {stock.ticker} - {stock.company_name}",
                (
                    "   📈 Price: "
                    + (f"${stock.price:.2f}" if stock.price is not None else "N/A")
                    + " | Change: "
                    + (
                        f"{stock.price_change:+.2f}%"
                        if stock.price_change is not None
                        else "N/A"
                    )
                ),
                (
                    f"   🌙 After Hours: {stock.afterhours_change_percent:.2f}%"
                    if stock.afterhours_change_percent is not None
                    else "   🌙 After Hours: N/A"
                ),
                (
                    f"   💼 Sector: {stock.sector} | Volume: {format_large_number(stock.volume)}"
                    if stock.sector and stock.volume
                    else f"   💼 Sector: {stock.sector or 'N/A'} | Volume: {format_large_number(stock.volume) if stock.volume is not None else 'N/A'}"
                ),
                (
                    f"   📊 EPS Surprise: {stock.eps_surprise:.2f}%"
                    if stock.eps_surprise is not None
                    else "   📊 EPS Surprise: N/A"
                ),
                (
                    f"   💰 Revenue Surprise: {stock.revenue_surprise:.2f}%"
                    if stock.revenue_surprise is not None
                    else "   💰 Revenue Surprise: N/A"
                ),
                (
                    f"   📈 Performance 1W: {stock.performance_1w:.2f}%"
                    if stock.performance_1w is not None
                    else "   📈 Performance 1W: N/A"
                ),
                "",
            ]
        )

    # 統計情報
    eps_surprises = [s.eps_surprise for s in results if s.eps_surprise is not None]
    revenue_surprises = [  # noqa: F841
        s.revenue_surprise for s in results if s.revenue_surprise is not None
    ]

    if eps_surprises:
        avg_eps = sum(eps_surprises) / len(eps_surprises)
        max_eps = max(eps_surprises)
        output_lines.extend(
            [
                "📊 EPSサプライズ統計:",
                f"   • 平均: {avg_eps:.2f}%",
                f"   • 最大: {max_eps:.2f}%",
                f"   • サンプル数: {len(eps_surprises)}",
                "",
            ]
        )

    # セクター別分析
    sector_counts = {}
    for stock in results:
        if stock.sector:
            sector_counts[stock.sector] = sector_counts.get(stock.sector, 0) + 1

    if sector_counts:
        output_lines.extend(
            [
                "🏢 セクター別分析:",
                *[
                    f"   • {sector}: {count}銘柄"
                    for sector, count in sorted(
                        sector_counts.items(), key=lambda x: x[1], reverse=True
                    )[:5]
                ],
                "",
            ]
        )

    return output_lines


def _format_earnings_trading_list(results: List, params: Dict[str, Any]) -> List[str]:
    """決算トレード対象銘柄の詳細フォーマット"""

    def format_large_number(num):
        # 0 is a real reading (a halted name really did trade 0 shares);
        # only a missing value is "N/A".
        if num is None:
            return "N/A"
        if num >= 1_000_000_000:
            return f"{num/1_000_000_000:.1f}B"
        elif num >= 1_000_000:
            return f"{num/1_000_000:.1f}M"
        elif num >= 1_000:
            return f"{num/1_000:.1f}K"
        else:
            return f"{num:.0f}"

    output_lines = (
        [
            "🎯 決算トレード対象銘柄スクリーニング結果",
            f"📊 検出銘柄数: {len(results)}",
            "=" * 100,
            "",
        ]
        + _criteria_block(
            params, client=finviz_screener, title="📋 適用されたスクリーニング条件:"
        )
        + [
            "",
            "=" * 100,
            "",
        ]
    )

    # 詳細な銘柄一覧
    output_lines.extend(
        [
            "📈 詳細データ:",
            "",
            "| Ticker | Company | Sector | Price | Change | EPS Surprise | Revenue Surprise | Perf 1W | Volatility | Volume |",
            "|--------|---------|--------|-------|--------|--------------|------------------|---------|------------|--------|",
        ]
    )

    for i, stock in enumerate(results[:10]):  # 上位10銘柄
        price_str = f"${stock.price:.2f}" if stock.price is not None else "N/A"
        change_str = (
            f"{stock.price_change:+.2f}%" if stock.price_change is not None else "N/A"
        )
        eps_surprise_str = (
            f"{stock.eps_surprise:+.2f}%" if stock.eps_surprise is not None else "N/A"
        )
        revenue_surprise_str = (
            f"{stock.revenue_surprise:+.2f}%"
            if stock.revenue_surprise is not None
            else "N/A"
        )
        perf_1w_str = (
            f"{stock.performance_1w:+.2f}%"
            if stock.performance_1w is not None
            else "N/A"
        )
        volatility_str = (
            f"{stock.volatility:.2f}" if stock.volatility is not None else "N/A"
        )
        volume_str = (
            format_large_number(stock.volume) if stock.volume is not None else "N/A"
        )

        ticker_display = stock.ticker or "N/A"
        company_display = (
            (stock.company_name[:15] + "...")
            if stock.company_name and len(stock.company_name) > 15
            else (stock.company_name or "N/A")
        )
        sector_display = (
            (stock.sector[:12] + "...")
            if stock.sector and len(stock.sector) > 12
            else (stock.sector or "N/A")
        )

        output_lines.append(
            f"| {ticker_display:<6} | {company_display:<15} | {sector_display:<12} | {price_str:<7} | {change_str:<8} | {eps_surprise_str:<12} | {revenue_surprise_str:<16} | {perf_1w_str:<7} | {volatility_str:<10} | {volume_str:<6} |"
        )

    output_lines.extend(["", "=" * 100, "", "🏆 上位5銘柄の詳細分析:", ""])

    # 上位5銘柄の詳細情報
    for i, stock in enumerate(results[:5], 1):
        output_lines.extend(
            [
                f"#{i} 📊 {stock.ticker} - {stock.company_name}",
                (
                    "   📈 Price: "
                    + (f"${stock.price:.2f}" if stock.price is not None else "N/A")
                    + " | Change: "
                    + (
                        f"{stock.price_change:+.2f}%"
                        if stock.price_change is not None
                        else "N/A"
                    )
                ),
                (
                    f"   💼 Sector: {stock.sector} | Volume: {format_large_number(stock.volume)}"
                    if stock.sector and stock.volume
                    else f"   💼 Sector: {stock.sector or 'N/A'} | Volume: {format_large_number(stock.volume) if stock.volume is not None else 'N/A'}"
                ),
                (
                    f"   📊 EPS Surprise: {stock.eps_surprise:.2f}%"
                    if stock.eps_surprise is not None
                    else "   📊 EPS Surprise: N/A"
                ),
                (
                    f"   💰 Revenue Surprise: {stock.revenue_surprise:.2f}%"
                    if stock.revenue_surprise is not None
                    else "   💰 Revenue Surprise: N/A"
                ),
                (
                    f"   📈 Performance 1W: {stock.performance_1w:.2f}%"
                    if stock.performance_1w is not None
                    else "   📈 Performance 1W: N/A"
                ),
                (
                    f"   📊 Volatility: {stock.volatility:.2f}"
                    if stock.volatility is not None
                    else "   📊 Volatility: N/A"
                ),
                (
                    f"   📈 Performance 1M: {stock.performance_1m:.2f}%"
                    if stock.performance_1m is not None
                    else "   📈 Performance 1M: N/A"
                ),
                "",
            ]
        )

    # 統計情報
    eps_surprises = [s.eps_surprise for s in results if s.eps_surprise is not None]
    revenue_surprises = [  # noqa: F841
        s.revenue_surprise for s in results if s.revenue_surprise is not None
    ]
    volatilities = [s.volatility for s in results if s.volatility is not None]

    if eps_surprises:
        avg_eps = sum(eps_surprises) / len(eps_surprises)
        max_eps = max(eps_surprises)
        output_lines.extend(
            [
                "📊 EPSサプライズ統計:",
                f"   • 平均: {avg_eps:.2f}%",
                f"   • 最大: {max_eps:.2f}%",
                f"   • サンプル数: {len(eps_surprises)}",
                "",
            ]
        )

    if volatilities:
        avg_volatility = sum(volatilities) / len(volatilities)
        max_volatility = max(volatilities)
        output_lines.extend(
            [
                "📊 ボラティリティ統計:",
                f"   • 平均: {avg_volatility:.2f}",
                f"   • 最大: {max_volatility:.2f}",
                f"   • サンプル数: {len(volatilities)}",
                "",
            ]
        )

    # セクター別分析
    sector_counts = {}
    for stock in results:
        if stock.sector:
            sector_counts[stock.sector] = sector_counts.get(stock.sector, 0) + 1

    if sector_counts:
        output_lines.extend(
            [
                "🏢 セクター別分析:",
                *[
                    f"   • {sector}: {count}銘柄"
                    for sector, count in sorted(
                        sector_counts.items(), key=lambda x: x[1], reverse=True
                    )[:5]
                ],
                "",
            ]
        )

    return output_lines


def _period_label(days_back: int) -> str:
    """Human label for a filings window (``0`` or less = no date filter)."""
    if not days_back or days_back <= 0:
        return "All available history"
    return f"Last {days_back} days"


@server.tool()
def get_sec_filings(
    ticker: str,
    form_types: Optional[List[str]] = None,
    days_back: int = 30,
    max_results: int = 50,
    sort_by: str = "filing_date",
    sort_order: str = "desc",
) -> List[TextContent]:
    """
    指定銘柄のSECファイリングデータを取得

    Args:
        ticker: 銘柄ティッカー
        form_types: フォームタイプフィルタ (例: ["10-K", "10-Q", "8-K"])。
            訂正版（``10-K/A`` 等）も一致する。
        days_back: 過去何日分のファイリング (デフォルト: 30日、0 以下で期間無制限)
        max_results: 最大取得件数 (デフォルト: 50件、0 以下で無制限)
        sort_by: ソート基準 ("filing_date", "report_date", "form")。
            これ以外を渡すとエラー（エンドポイントが解釈しないため）。
        sort_order: ソート順序 ("asc", "desc")
    """
    try:
        # Validate ticker
        if not validate_ticker(ticker):
            raise ValueError(f"Invalid ticker: {ticker}")

        # Get SEC filings data
        filings = finviz_sec.get_sec_filings(
            ticker=ticker,
            form_types=form_types,
            days_back=days_back,
            max_results=max_results,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        if not filings:
            return [
                TextContent(
                    type="text",
                    text=f"No SEC filings found for {ticker} ({_period_label(days_back).lower()}).",
                )
            ]

        # Format output
        form_filter_text = f" (Forms: {', '.join(form_types)})" if form_types else ""
        output_lines = [
            f"📄 SEC Filings for {ticker}{form_filter_text}:",
            f"📅 Period: {_period_label(days_back)} | Results: {len(filings)} filings",
            "=" * 80,
            "",
        ]

        for filing in filings:
            output_lines.extend(
                [
                    f"📅 Filing Date: {filing.filing_date} | Report Date: {filing.report_date}",
                    f"📋 Form: {filing.form}",
                    f"📝 Description: {filing.description}",
                    f"🔗 Filing URL: {filing.filing_url}",
                    f"📄 Document URL: {filing.document_url}",
                    "-" * 60,
                    "",
                ]
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except (ValueError, TypeError) as e:
        logger.error(f"Validation error in get_sec_filings: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Error in get_sec_filings: {str(e)}")
        raise


@server.tool()
def get_major_sec_filings(ticker: str, days_back: int = 90) -> List[TextContent]:
    """
    主要なSECファイリング（10-K, 10-Q, 8-K等）を取得

    Args:
        ticker: 銘柄ティッカー
        days_back: 過去何日分のファイリング (デフォルト: 90日)
    """
    try:
        # Validate ticker
        if not validate_ticker(ticker):
            raise ValueError(f"Invalid ticker: {ticker}")

        # Get major filings
        filings = finviz_sec.get_major_filings(ticker, days_back)

        if not filings:
            return [
                TextContent(
                    type="text",
                    text=f"No major SEC filings found for {ticker} ({_period_label(days_back).lower()}).",
                )
            ]

        # Format output
        output_lines = [
            f"📊 Major SEC Filings for {ticker}:",
            f"📅 Period: {_period_label(days_back)} | Results: {len(filings)} filings",
            "=" * 80,
            "",
            "📋 Form Types: 10-K (Annual), 10-Q (Quarterly), 8-K (Current), "
            "20-F/6-K (Foreign issuers), DEF 14A (Proxy), SC 13G/D (Ownership) "
            "— amendments (e.g. 10-K/A) included",
            "",
            "=" * 80,
            "",
        ]

        # Group by form type for better organization
        forms_dict = {}
        for filing in filings:
            form_type = filing.form
            if form_type not in forms_dict:
                forms_dict[form_type] = []
            forms_dict[form_type].append(filing)

        for form_type, form_filings in forms_dict.items():
            output_lines.extend(
                [f"📋 Form {form_type} ({len(form_filings)} filings):", "-" * 40, ""]
            )

            for filing in form_filings:
                output_lines.extend(
                    [
                        f"  📅 {filing.filing_date} | Report: {filing.report_date}",
                        f"  📝 {filing.description}",
                        f"  🔗 Filing: {filing.filing_url}",
                        f"  📄 Document: {filing.document_url}",
                        "",
                    ]
                )

            output_lines.append("")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except (ValueError, TypeError) as e:
        logger.error(f"Validation error in get_major_sec_filings: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Error in get_major_sec_filings: {str(e)}")
        raise


@server.tool()
def get_insider_sec_filings(ticker: str, days_back: int = 30) -> List[TextContent]:
    """
    インサイダー取引関連のSECファイリング（フォーム3, 4, 5, 144）を取得

    訂正版（``4/A`` 等）も含む。従業員給付制度の年次報告である 11-K は
    インサイダー売買ではないため対象外。

    Args:
        ticker: 銘柄ティッカー
        days_back: 過去何日分のファイリング (デフォルト: 30日)
    """
    try:
        # Validate ticker
        if not validate_ticker(ticker):
            raise ValueError(f"Invalid ticker: {ticker}")

        # Get insider filings
        filings = finviz_sec.get_insider_filings(ticker, days_back)

        if not filings:
            return [
                TextContent(
                    type="text",
                    text=f"No insider SEC filings found for {ticker} ({_period_label(days_back).lower()}).",
                )
            ]

        # Format output
        output_lines = [
            f"👥 Insider SEC Filings for {ticker}:",
            f"📅 Period: {_period_label(days_back)} | Results: {len(filings)} filings",
            "=" * 80,
            "",
            "📋 Form Types (amendments such as 4/A included):",
            "  • Form 3: Initial ownership statement",
            "  • Form 4: Statement of changes in beneficial ownership",
            "  • Form 5: Annual statement of changes in beneficial ownership",
            "  • Form 144: Notice of proposed sale of restricted securities",
            "",
            "=" * 80,
            "",
        ]

        for filing in filings:
            # Determine filing type explanation (base form, ignoring "/A")
            base_form = filing.form.split("/")[0].strip().upper()
            form_explanation = {
                "3": "Initial ownership statement",
                "4": "Changes in beneficial ownership",
                "5": "Annual ownership changes",
                "144": "Proposed sale of restricted securities",
            }.get(base_form, "Insider-related filing")
            if "/" in filing.form:
                form_explanation += " (amendment)"

            output_lines.extend(
                [
                    f"📋 Form {filing.form} - {form_explanation}",
                    f"📅 Filing: {filing.filing_date} | Report: {filing.report_date}",
                    f"📝 {filing.description}",
                    f"🔗 Filing: {filing.filing_url}",
                    f"📄 Document: {filing.document_url}",
                    "-" * 60,
                    "",
                ]
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except (ValueError, TypeError) as e:
        logger.error(f"Validation error in get_insider_sec_filings: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Error in get_insider_sec_filings: {str(e)}")
        raise


@server.tool()
def get_sec_filing_summary(ticker: str, days_back: int = 90) -> List[TextContent]:
    """
    指定期間のSECファイリング概要とサマリーを取得

    Args:
        ticker: 銘柄ティッカー
        days_back: 過去何日分の概要 (デフォルト: 90日)
    """
    try:
        # Validate ticker
        if not validate_ticker(ticker):
            raise ValueError(f"Invalid ticker: {ticker}")

        # Get filing summary
        summary = finviz_sec.get_filing_summary(ticker, days_back)

        if "error" in summary:
            return [
                TextContent(
                    type="text",
                    text=f"Error getting filing summary for {ticker}: {summary['error']}",
                )
            ]

        if summary.get("total_filings", 0) == 0:
            return [
                TextContent(
                    type="text",
                    text=f"No SEC filings found for {ticker} ({_period_label(days_back).lower()}).",
                )
            ]

        # Format output
        output_lines = [
            f"📊 SEC Filing Summary for {ticker}:",
            f"📅 Period: {_period_label(summary['period_days'])}",
            f"📄 Total Filings: {summary['total_filings']}",
            f"📅 Latest Filing: {summary.get('latest_filing_date', 'N/A')} ({summary.get('latest_filing_form', 'N/A')})",
            "=" * 60,
            "",
            "📋 Filing Breakdown by Form Type:",
            "-" * 40,
        ]

        # Sort forms by count (descending). Counts and percentages are over
        # every filing in the window (the client no longer caps at 100); only
        # the *displayed* rows are limited, and that limit is stated.
        forms = summary.get("forms", {})
        sorted_forms = sorted(forms.items(), key=lambda x: x[1], reverse=True)

        max_form_rows = 25
        shown_forms = sorted_forms[:max_form_rows]

        for form_type, count in shown_forms:
            percentage = (
                (count / summary["total_filings"] * 100)
                if summary["total_filings"] > 0
                else 0
            )
            output_lines.append(
                f"  📋 {form_type}: {count} filings ({percentage:.1f}%)"
            )

        if len(sorted_forms) > len(shown_forms):
            remaining = sorted_forms[len(shown_forms) :]
            remaining_filings = sum(count for _, count in remaining)
            output_lines.append(
                f"  … and {len(remaining)} more form types "
                f"({remaining_filings} filings) not shown"
            )

        output_lines.extend(
            [
                "",
                "📝 Common Form Types:",
                "  • 10-K: Annual report (comprehensive overview)",
                "  • 10-Q: Quarterly report (financial updates)",
                "  • 8-K: Current report (material events)",
                "  • DEF 14A: Proxy statement (shareholder meetings)",
                "  • 4: Insider trading activities",
                "  • SC 13G/D: Beneficial ownership (>5% ownership changes)",
            ]
        )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except (ValueError, TypeError) as e:
        logger.error(f"Validation error in get_sec_filing_summary: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Error in get_sec_filing_summary: {str(e)}")
        raise


@server.tool()
def get_edgar_filing_content(
    ticker: str, accession_number: str, primary_document: str, max_length: int = 50000
) -> List[TextContent]:
    """
    EDGAR API経由でSECファイリングドキュメント内容を取得

    HTML/インラインXBRLはテキストへ変換したうえで ``max_length`` を適用する
    （変換前に切ると先頭数万文字が CSS・XBRL タグで埋まる）。

    Args:
        ticker: 銘柄ティッカー
        accession_number: SEC accession number (with dashes)
        primary_document: Primary document filename
        max_length: 最大コンテンツ長（変換後のテキスト、デフォルト: 50,000文字）
    """
    try:
        # Validate ticker
        if not validate_ticker(ticker):
            raise ValueError(f"Invalid ticker: {ticker}")

        logger.info(
            f"Fetching EDGAR document content for {ticker}: {accession_number}/{primary_document}"
        )

        # Get document content via EDGAR API
        content_data = _get_edgar_client().get_filing_document_content(
            ticker=ticker,
            accession_number=accession_number,
            primary_document=primary_document,
            max_length=max_length,
        )

        if content_data.get("status") == "error":
            return [
                TextContent(
                    type="text",
                    text=f"Error: {content_data.get('error', 'Unknown error')}",
                )
            ]

        # Format output
        metadata = content_data.get("metadata", {})
        content = content_data.get("content", "")

        # The client truncates exactly once (after HTML→text conversion) and
        # appends its own marker; re-slicing here used to chop that marker off
        # and mis-report the length. Render what we were given.
        full_length = metadata.get("full_content_length", len(content))
        output_lines = [
            f"📄 SEC Filing Document Content for {ticker}:",
            f"🔗 Document: {accession_number}/{primary_document}",
            f"📅 Retrieved: {metadata.get('retrieved_at', 'N/A')}",
            f"📄 Content Type: {metadata.get('content_type', 'unknown')}",
            f"📊 Document Length: {full_length:,} characters "
            f"(text; source markup {metadata.get('raw_content_length', 0):,} bytes)",
            f"📊 Returned: {metadata.get('content_length', len(content)):,} characters",
            "=" * 80,
            "",
            content,
        ]

        if metadata.get("truncated"):
            output_lines.extend(
                [
                    "",
                    "=" * 80,
                    f"[Truncated: showing the first {max_length:,} of "
                    f"{full_length:,} characters]",
                ]
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except (ValueError, TypeError) as e:
        logger.error(f"Validation error in get_edgar_filing_content: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Error in get_edgar_filing_content: {str(e)}")
        raise


@server.tool()
def get_multiple_edgar_filing_contents(
    ticker: str,
    filings_data: List[Dict[str, str]],
    max_length: int = 5000,
    preview_length: Optional[int] = None,
) -> List[TextContent]:
    """
    複数のSECファイリングドキュメント内容をEDGAR API経由で一括取得

    取得した分をそのまま表示する（旧実装は 1 件あたり 20,000 文字を取得して
    500 文字しか表示しなかった）。全文が必要な場合は
    ``get_edgar_filing_content`` を 1 件ずつ呼ぶこと。

    Args:
        ticker: 銘柄ティッカー
        filings_data: ファイリングデータのリスト [{"accession_number": "...", "primary_document": "..."}]
        max_length: 各ドキュメントの取得上限（変換後テキスト、デフォルト: 5,000文字）
        preview_length: 表示上限。省略時は取得した全文字を表示する。
    """
    try:
        # Validate ticker
        if not validate_ticker(ticker):
            raise ValueError(f"Invalid ticker: {ticker}")

        if not filings_data:
            return [TextContent(type="text", text="No filing data provided.")]

        logger.info(
            f"Fetching {len(filings_data)} EDGAR document contents for {ticker}"
        )

        # Prepare filing data with ticker
        filings_with_ticker = []
        for filing in filings_data:
            filing_copy = filing.copy()
            filing_copy["ticker"] = ticker
            filings_with_ticker.append(filing_copy)

        # Get multiple document contents via EDGAR API
        results = _get_edgar_client().get_multiple_filing_contents(
            filings_data=filings_with_ticker, max_length=max_length
        )

        if not results:
            return [
                TextContent(
                    type="text", text=f"No document contents retrieved for {ticker}."
                )
            ]

        # Format output
        output_lines = [
            f"📄 Multiple SEC Filing Document Contents for {ticker}:",
            f"📊 Retrieved: {len(results)} documents",
            "=" * 80,
            "",
        ]

        for i, result in enumerate(results, 1):
            metadata = result.get("metadata", {})
            content = result.get("content", "")
            status = result.get("status", "unknown")

            full_length = metadata.get("full_content_length", len(content))
            output_lines.extend(
                [
                    f"📋 Document {i}/{len(results)}:",
                    f"   📄 File: {metadata.get('accession_number', 'N/A')}/{metadata.get('primary_document', 'N/A')}",
                    f"   📅 Retrieved: {metadata.get('retrieved_at', 'N/A')}",
                    f"   📊 Document length: {full_length:,} characters "
                    f"| Fetched: {metadata.get('content_length', len(content)):,}",
                    f"   ✅ Status: {status}",
                    "",
                ]
            )

            if status == "error":
                error_msg = result.get("error", "Unknown error")
                output_lines.extend([f"   ❌ Error: {error_msg}", ""])
            else:
                # Render everything that was fetched unless the caller asked
                # for a shorter preview.
                shown = (
                    content
                    if preview_length is None or preview_length >= len(content)
                    else content[:preview_length]
                )
                output_lines.extend(
                    [
                        f"   📝 Content ({len(shown):,} chars shown):",
                        shown,
                        "",
                    ]
                )

                if len(shown) < full_length:
                    output_lines.append(
                        f"   [... {full_length - len(shown):,} more characters — "
                        f"use get_edgar_filing_content for the full document]"
                    )
                    output_lines.append("")

            output_lines.extend(["-" * 60, ""])

        return [TextContent(type="text", text="\n".join(output_lines))]

    except (ValueError, TypeError) as e:
        logger.error(
            f"Validation error in get_multiple_edgar_filing_contents: {str(e)}"
        )
        raise e
    except Exception as e:
        logger.error(f"Error in get_multiple_edgar_filing_contents: {str(e)}")
        raise


@server.tool()
def get_edgar_company_filings(
    ticker: str,
    form_types: Optional[List[str]] = None,
    max_count: int = 50,
    days_back: int = 365,
    include_full_history: bool = False,
) -> List[TextContent]:
    """
    EDGAR API経由で企業のファイリング一覧を取得

    フォーム・期間のフィルタを **先に** 適用し、``max_count`` は最後に効かせる
    （旧実装は先頭 max_count 件に切ってからフィルタしていたため、
    ``form_types=["10-K"]`` がほぼ常に 0 件だった）。

    Args:
        ticker: 銘柄ティッカー
        form_types: フォームタイプフィルタ (例: ["10-K", "10-Q", "8-K"])。
            訂正版（``10-K/A``）も一致する。
        max_count: 最大取得件数 (デフォルト: 50)
        days_back: 過去何日分 (デフォルト: 365日)。**0 以下・None で期間無制限**
            （Finviz 側の SEC ツール群と同じ規約。以前は 0 が「今日だけ」になっていた）。
        include_full_history: True にすると EDGAR のページネーションを辿って
            全履歴を取得する（リクエスト数・転送量が大きい）。既定の False では
            submissions API の ``recent``（最大1,000件。AAPL では2015年まで遡る）
            のみを使う。
    """
    try:
        # Validate ticker
        if not validate_ticker(ticker):
            raise ValueError(f"Invalid ticker: {ticker}")

        logger.info(f"Fetching EDGAR filings for {ticker} via EDGAR API")

        # Calculate date range
        from datetime import datetime, timedelta

        # days_back <= 0 (or None) means "no date window", matching the four
        # Finviz SEC tools. Deriving date_from unconditionally made 0 mean
        # "today only".
        date_to = datetime.now().strftime("%Y-%m-%d")
        if days_back and days_back > 0:
            date_from: Optional[str] = (
                datetime.now() - timedelta(days=days_back)
            ).strftime("%Y-%m-%d")
            period_label = f"{date_from} to {date_to} ({days_back} days)"
        else:
            date_from = None
            period_label = f"All available history (through {date_to})"

        # Get company filings via EDGAR API
        filings = _get_edgar_client().get_company_filings(
            ticker=ticker,
            form_types=form_types,
            date_from=date_from,
            date_to=date_to,
            max_count=max_count,
            include_full_history=include_full_history,
        )

        if not filings:
            form_filter_text = (
                f" (forms: {', '.join(form_types)})" if form_types else ""
            )
            return [
                TextContent(
                    type="text",
                    text=f"No EDGAR filings found for {ticker}{form_filter_text} — {period_label}.",
                )
            ]

        # Format output
        output_lines = [
            f"📊 EDGAR Company Filings for {ticker}:",
            f"📅 Period: {period_label}",
            f"📄 Results: {len(filings)} filings",
        ]

        if form_types:
            output_lines.append(f"📋 Form Filter: {', '.join(form_types)}")

        output_lines.extend(
            [
                "=" * 80,
                "",
                "📋 Available Form Types:",
                "  • 10-K: Annual report",
                "  • 10-Q: Quarterly report",
                "  • 8-K: Current report (material events)",
                "  • DEF 14A: Proxy statement",
                "  • 4: Statement of changes in beneficial ownership",
                "",
                "=" * 80,
                "",
            ]
        )

        for filing in filings:
            output_lines.extend(
                [
                    f"📋 Form {filing['form']} - {filing.get('description', 'N/A')}",
                    f"📅 Filing: {filing['filing_date']} | Report: {filing['report_date']}",
                    f"📄 Document: {filing['accession_number']}/{filing['primary_document']}",
                    f"🔗 Filing URL: {filing['filing_url']}",
                    f"📄 Document URL: {filing['document_url']}",
                    "-" * 60,
                    "",
                ]
            )

        output_lines.extend(
            [
                "",
                "💡 To get document content, use get_edgar_filing_content with:",
                "   ticker, accession_number, and primary_document from above",
            ]
        )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except (ValueError, TypeError) as e:
        logger.error(f"Validation error in get_edgar_company_filings: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Error in get_edgar_company_filings: {str(e)}")
        raise


@server.tool()
def get_edgar_company_facts(ticker: str) -> List[TextContent]:
    """
    EDGAR API経由で企業の基本情報とファクトデータを取得

    Args:
        ticker: 銘柄ティッカー
    """
    try:
        # Validate ticker
        if not validate_ticker(ticker):
            raise ValueError(f"Invalid ticker: {ticker}")

        logger.info(f"Fetching EDGAR company facts for {ticker}")

        # Get CIK from ticker first
        cik = _get_edgar_client()._get_cik_from_ticker(ticker)
        if not cik:
            return [
                TextContent(
                    type="text",
                    text=f"Could not find CIK for ticker {ticker}. Please verify the ticker symbol.",
                )
            ]

        # Get company facts via EDGAR API
        try:
            company_facts = _get_edgar_client().client.get_company_facts(cik)
        except Exception as e:
            return [
                TextContent(
                    type="text",
                    text=f"Error fetching company facts for {ticker}: {str(e)}",
                )
            ]

        if not company_facts:
            return [
                TextContent(type="text", text=f"No company facts found for {ticker}.")
            ]

        # Extract basic information
        cik = company_facts.get("cik", "N/A")
        entity_name = company_facts.get("entityName", "N/A")

        # Format output
        output_lines = [
            f"🏢 EDGAR Company Facts for {ticker}:",
            f"📊 Entity Name: {entity_name}",
            f"🔢 CIK: {cik}",
            "=" * 60,
            "",
        ]

        # Show available facts/concepts
        facts = company_facts.get("facts", {})
        if facts:
            output_lines.extend(["📋 Available Financial Concepts:", ""])

            # Group by taxonomy
            for taxonomy, concepts in facts.items():
                if concepts:
                    output_lines.extend(
                        [
                            f"📊 {taxonomy.upper()} Taxonomy:",
                            f"   📈 Available concepts: {len(concepts)}",
                            "",
                        ]
                    )

                    # Show first few concepts as examples
                    concept_names = list(concepts.keys())[:5]
                    for concept in concept_names:
                        concept_data = concepts[concept]
                        # EDGAR emits explicit nulls for both fields on many
                        # concepts; ``.get(k, default)`` returns that null, so
                        # fall back explicitly (label → concept name).
                        label = concept_data.get("label") or None
                        description = (
                            concept_data.get("description") or label or concept
                        )
                        if label and label != description:
                            output_lines.append(
                                f"   • {concept} ({label}): {description}"
                            )
                        else:
                            output_lines.append(f"   • {concept}: {description}")

                    if len(concepts) > 5:
                        output_lines.append(
                            f"   ... and {len(concepts) - 5} more concepts"
                        )

                    output_lines.append("")

        output_lines.extend(
            [
                "💡 To get specific concept data, use get_edgar_company_concept with:",
                f"   ticker='{ticker}', concept='Assets', taxonomy='us-gaap'",
            ]
        )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except (ValueError, TypeError) as e:
        logger.error(f"Validation error in get_edgar_company_facts: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Error in get_edgar_company_facts: {str(e)}")
        raise


def _format_xbrl_value(value: Any, unit: str) -> str:
    """Format an XBRL fact according to its unit key.

    EDGAR's ``units`` keys carry the dimension: ``USD`` (money), ``shares``
    (counts), ``USD/shares`` (per-share amounts, i.e. EPS), ``pure`` (ratios).
    Rendering every one of them as ``$X.XXB`` — the previous behavior — turned
    a 15-billion **share** count into "$15.20B" and an EPS of 6.60 into
    "$6.60" only by accident. Negatives get a leading sign, not ``$-``.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return str(value)

    unit_key = (unit or "").strip()
    sign = "-" if value < 0 else ""
    magnitude = abs(float(value))

    def _scaled(number: float) -> str:
        if number >= 1_000_000_000:
            return f"{number / 1_000_000_000:.2f}B"
        if number >= 1_000_000:
            return f"{number / 1_000_000:.2f}M"
        if number >= 1_000:
            return f"{number / 1_000:.2f}K"
        return f"{number:,.2f}"

    # Per-share / ratio units such as "USD/shares": a plain decimal.
    if "/" in unit_key:
        numerator = unit_key.split("/", 1)[0].upper()
        if numerator == "USD":
            return f"{sign}${magnitude:,.2f}"
        return f"{sign}{magnitude:,.4f}".rstrip("0").rstrip(".")

    if unit_key.upper() == "USD":
        return f"{sign}${_scaled(magnitude)}"

    if unit_key.lower() == "pure":
        # Ratios/percentages carried as bare numbers.
        if magnitude and magnitude < 1000:
            return f"{sign}{magnitude:,.4f}".rstrip("0").rstrip(".")
        return f"{sign}{magnitude:,.0f}"

    # shares and every other count-like unit: a plain number.
    if float(magnitude).is_integer():
        return f"{sign}{magnitude:,.0f}"
    return f"{sign}{magnitude:,.2f}"


def _duration_months(start: Optional[str], end: Optional[str]) -> Optional[int]:
    """Approximate month count between two ``YYYY-MM-DD`` strings."""
    if not start or not end:
        return None
    try:
        start_dt = datetime.strptime(start, "%Y-%m-%d")
        end_dt = datetime.strptime(end, "%Y-%m-%d")
    except (TypeError, ValueError):
        return None
    days = (end_dt - start_dt).days
    if days < 0:
        return None
    return int(round(days / 30.44))


def _period_bucket(entry: Dict[str, Any]) -> str:
    """Group key so 3-month and 12-month facts never interleave silently."""
    months = _duration_months(entry.get("start"), entry.get("end"))
    if entry.get("start") is None:
        return "Instant (point-in-time balance)"
    if months is None:
        return "Duration (length unknown)"
    if months <= 4:
        return "Quarterly (~3 months)"
    if months <= 7:
        return "Half-year (~6 months)"
    if months <= 10:
        return "Nine months (~9 months)"
    if months <= 14:
        return "Annual (~12 months)"
    return f"Other duration (~{months} months)"


def _describe_period(entry: Dict[str, Any]) -> str:
    """Human-readable period + fiscal labels for one XBRL fact."""
    start = entry.get("start")
    end = entry.get("end", "N/A")
    if start:
        months = _duration_months(start, end)
        span = f"{start} → {end}" + (f" ({months}m)" if months is not None else "")
    else:
        span = f"as of {end}"

    fy = entry.get("fy")
    fp = entry.get("fp")
    labels = []
    if fy and fp:
        labels.append(f"FY{fy} {fp}")
    elif fy:
        labels.append(f"FY{fy}")
    frame = entry.get("frame")
    if frame:
        labels.append(str(frame))
    if labels:
        span += " [" + ", ".join(labels) + "]"
    return span


def _dedupe_concept_entries(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Collapse the same fact reported in several filings.

    EDGAR repeats an unchanged (start, end, val) triple in every subsequent
    filing that includes the comparative period. Keep the most recently filed
    copy and record how many filings carried it.
    """
    ordered = sorted(
        entries,
        key=lambda e: (str(e.get("end", "")), str(e.get("filed", ""))),
        reverse=True,
    )
    deduped: List[Dict[str, Any]] = []
    seen: Dict[tuple, Dict[str, Any]] = {}
    for entry in ordered:
        key = (entry.get("start"), entry.get("end"), entry.get("val"))
        if key in seen:
            seen[key]["_report_count"] = seen[key].get("_report_count", 1) + 1
            continue
        copy = dict(entry)
        copy["_report_count"] = 1
        seen[key] = copy
        deduped.append(copy)
    return deduped


@server.tool()
def get_edgar_company_concept(
    ticker: str, concept: str, taxonomy: str = "us-gaap"
) -> List[TextContent]:
    """
    EDGAR API経由で企業の特定の財務コンセプトデータを取得

    Args:
        ticker: 銘柄ティッカー
        concept: XBRLコンセプト (例: 'Assets', 'Revenues', 'NetIncomeLoss')
        taxonomy: タクソノミー ('us-gaap', 'dei', 'invest')
    """
    try:
        # Validate ticker
        if not validate_ticker(ticker):
            raise ValueError(f"Invalid ticker: {ticker}")

        logger.info(f"Fetching EDGAR concept {concept} for {ticker}")

        # Get company concept via EDGAR API
        concept_data = _get_edgar_client().get_company_concept(
            ticker=ticker, concept=concept, taxonomy=taxonomy
        )

        if "error" in concept_data:
            return [TextContent(type="text", text=f"Error: {concept_data['error']}")]

        # Extract basic information
        cik = concept_data.get("cik", "N/A")
        entity_name = concept_data.get("entityName", "N/A")
        # EDGAR emits explicit nulls here for many concepts; ``.get(k, default)``
        # would hand back that null and render "None".
        concept_label = concept_data.get("label") or concept
        description = concept_data.get("description") or concept_label or "N/A"

        # Format output
        output_lines = [
            f"📊 EDGAR Company Concept: {ticker} - {concept}",
            f"🏢 Entity: {entity_name} (CIK: {cik})",
            f"📋 Concept: {concept_label}",
            f"📝 Description: {description}",
            f"🏷️ Taxonomy: {taxonomy}",
            "=" * 80,
            "",
        ]

        # Show units and values
        units = concept_data.get("units", {})
        if units:
            output_lines.append("📊 Available Data Units:")
            output_lines.append("")

            for unit_type, unit_data in units.items():
                deduped = _dedupe_concept_entries(list(unit_data or []))
                output_lines.extend(
                    [
                        f"💰 Unit: {unit_type}",
                        f"   📈 Data points: {len(unit_data)} reported "
                        f"({len(deduped)} distinct periods after collapsing "
                        f"facts restated identically in later filings)",
                        "",
                    ]
                )

                # Group by period shape so 3-month and 12-month figures are
                # never mixed into one undifferentiated list.
                buckets: Dict[str, List[Dict[str, Any]]] = {}
                for entry in deduped:
                    buckets.setdefault(_period_bucket(entry), []).append(entry)

                per_bucket = 8
                for bucket_name, entries in buckets.items():
                    output_lines.append(f"   📆 {bucket_name} ({len(entries)}):")
                    for entry in entries[:per_bucket]:
                        formatted_value = _format_xbrl_value(
                            entry.get("val", "N/A"), unit_type
                        )
                        form = entry.get("form", "N/A")
                        filed = entry.get("filed", "N/A")
                        repeats = entry.get("_report_count", 1)
                        repeat_note = (
                            f", reported in {repeats} filings" if repeats > 1 else ""
                        )
                        output_lines.append(
                            f"      • {_describe_period(entry)}: {formatted_value} "
                            f"({form} filed: {filed}{repeat_note})"
                        )

                    if len(entries) > per_bucket:
                        output_lines.append(
                            f"      ... and {len(entries) - per_bucket} more "
                            f"{bucket_name.split(' (')[0].lower()} entries"
                        )
                    output_lines.append("")
        else:
            output_lines.append("⚠️ No unit data available for this concept.")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except (ValueError, TypeError) as e:
        logger.error(f"Validation error in get_edgar_company_concept: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Error in get_edgar_company_concept: {str(e)}")
        raise


# Register Field Discovery Tools
logger.info("Registering Field Discovery tools...")
register_field_discovery_tools(server)
logger.info("Field Discovery tools registered successfully")

# ---------------------------------------------------------------------------
# Moving Average Position Tool
# ---------------------------------------------------------------------------


def _sma_pct_to_float(val: Any) -> Optional[float]:
    """Convert a Finviz SMA cell to a float percent distance.

    The parsed fundamentals already deliver floats (``%`` stripped); strings
    are still tolerated for robustness. ``-``/``""``/``None`` mean missing.
    """
    if val is None or (isinstance(val, str) and val.strip() in ("", "-")):
        return None
    try:
        if isinstance(val, (int, float)):
            return float(val)
        str_val = str(val).strip().replace(",", "").rstrip("%")
        return float(str_val)
    except (TypeError, ValueError):
        return None


def _sma_absolute_from_pct(
    price: Optional[float], pct_distance: Optional[float]
) -> Optional[float]:
    """Derive the absolute SMA from price and price-vs-SMA percent distance.

    Finviz's ``*-Day Simple Moving Average`` columns are the **percent
    distance of the price from the SMA** (GROUND_TRUTH.md "Units"), so
    ``price = SMA * (1 + pct/100)`` and therefore
    ``SMA = price / (1 + pct/100)``. Returns None when either input is
    missing or the ratio is degenerate (pct == -100).
    """
    if price is None or pct_distance is None:
        return None
    denominator = 1 + pct_distance / 100
    if denominator == 0:
        return None
    return price / denominator


def _sma_position(pct_distance: Optional[float]) -> Optional[str]:
    """ "above"/"below" for a price-vs-SMA percent distance.

    A price sitting exactly on its SMA counts as *above*, matching the
    repo-wide ``>=`` convention (commit 5be5d8c).
    """
    if pct_distance is None:
        return None
    return "above" if pct_distance >= 0 else "below"


@server.tool()
def get_moving_average_position(ticker: str) -> List[TextContent]:
    """Return current price and its percentage distance to 20-, 50-, and 200-day SMAs.

    Finviz reports SMA columns as the percent distance of the price from the
    SMA; the absolute SMA prices shown here are derived from that distance and
    the current price.

    Args:
        ticker: Stock ticker symbol (e.g. "AAPL").

    Returns:
        Single TextContent with formatted analysis.
    """

    # Validate ticker first
    if not validate_ticker(ticker):
        raise ValueError(f"Invalid ticker: {ticker}")

    # Retrieve fundamentals (full set)
    fundamentals = finviz_client.get_stock_fundamentals(ticker.upper())
    if fundamentals is None:
        return [
            TextContent(type="text", text=f"No data found for ticker: {ticker.upper()}")
        ]

    def _get_sma_pct(period: int) -> Optional[float]:
        """Return the price-vs-SMA percent distance Finviz reports."""
        candidate_keys = [
            f"{period}_day_simple_moving_average",
            f"{period}_day_moving_average",
            f"sma_{period}",
            f"sma{period}",
        ]

        for key in candidate_keys:
            if key in fundamentals:
                return _sma_pct_to_float(fundamentals.get(key))

        # Fallback over whatever keys the parser produced. Compare *normalized*
        # keys for equality — substring matching would let period=20 pick up an
        # "sma200" key and report 200-day data in the 20-day row.
        normalized_candidates = {key.replace("_", "") for key in candidate_keys}
        for key in fundamentals.keys():
            if key.replace("_", "") in normalized_candidates:
                return _sma_pct_to_float(fundamentals.get(key))

        return None

    price_val = _sma_pct_to_float(fundamentals.get("price"))

    lines = [
        f"📐 Moving Average Position for {ticker.upper()}",
        "=" * 60,
        "",
        f"Current Price         : "
        f"{f'${price_val:.2f}' if price_val is not None else 'N/A'}",
        "-" * 60,
    ]

    for period in (20, 50, 200):
        pct = _get_sma_pct(period)
        sma_val = _sma_absolute_from_pct(price_val, pct)
        position = _sma_position(pct)

        if sma_val is not None:
            sma_text = f"${sma_val:.2f} (derived from price and % distance)"
        elif pct is not None and price_val is None:
            sma_text = "N/A (current price unavailable)"
        else:
            # Either no % distance at all, or a degenerate ratio (pct == -100)
            sma_text = "N/A"

        if pct is None:
            detail = "→ Price vs SMA: N/A"
        else:
            detail = f"→ Price is {pct:+.2f}% vs the SMA ({position})"

        label = f"{period}-Day SMA"
        lines.extend(
            [
                f"{label:<22}: {sma_text}",
                f"   {detail}",
                "",
            ]
        )

    return [TextContent(type="text", text="\n".join(lines).rstrip())]


# ---------------------------------------------------------------------------
# Custom Screener Tool
# ---------------------------------------------------------------------------


@server.tool()
def custom_screener(
    filters: str,
    signal: Optional[str] = None,
    order: Optional[str] = None,
    max_results: int = 50,
) -> List[TextContent]:
    """Screen stocks using raw FinViz filter codes for maximum flexibility.

    Unlike the preset screener tools, this accepts raw FinViz filter tokens
    directly so you can combine any filters that FinViz supports.

    Args:
        filters: Comma-separated raw FinViz filter codes.
            Examples:
              "cap_large,fa_div_o3"              - Large cap, dividend > 3%
              "cap_small,fa_pe_u20"              - Small cap, P/E < 20
              "cap_mega,fa_roe_o20,fa_pb_u3"     - Mega cap, ROE > 20%, P/B < 3
              "sec_technology,fa_salesqoq_o25"    - Tech sector, quarterly sales growth > 25%
              "earningsdate_yesterdayafter|todaybefore" - Earnings yesterday after-close through today before-open
            Common filter prefixes:
              cap_  : Market cap (nano/micro/small/mid/large/mega)
              fa_   : Fundamental analysis (pe, div, roe, eps, etc.)
              ta_   : Technical analysis (sma, rsi, pattern, etc.)
              sec_  : Sector
              ind_  : Industry
              geo_  : Country
              sh_   : Share data (price, avgvol, float, etc.)
        signal: Optional FinViz signal identifier (e.g. "ta_topgainers",
            "ta_mostactive", "ta_unusualvolume", "ta_oversold").
        order: Optional sort order. Use a column name for ascending or prefix
            with '-' for descending (e.g. "-marketcap", "change", "-volume").
        max_results: Maximum number of results to return (1-500, default 50).

    Returns:
        List of TextContent with formatted screening results.
    """
    try:
        # --- Validate filters ---
        filter_errors, normalized_filters = validate_and_normalize_raw_filters(filters)
        if filter_errors:
            return [
                TextContent(
                    type="text",
                    text=f"Filter validation error: {'; '.join(filter_errors)}",
                )
            ]

        # --- Validate optional signal ---
        if signal is not None:
            signal_errors = validate_signal(signal)
            if signal_errors:
                return [
                    TextContent(
                        type="text",
                        text=f"Signal validation error: {'; '.join(signal_errors)}",
                    )
                ]

        # --- Validate optional order ---
        if order is not None:
            order_errors = validate_raw_sort_order(order)
            if order_errors:
                return [
                    TextContent(
                        type="text",
                        text=f"Order validation error: {'; '.join(order_errors)}",
                    )
                ]

        # --- Validate max_results ---
        if not isinstance(max_results, int) or max_results < 1 or max_results > 500:
            return [
                TextContent(
                    type="text",
                    text=f"Invalid max_results: {max_results} (must be an integer between 1 and 500)",
                )
            ]

        # --- Execute screening ---
        stocks, total_matches, order_verified = finviz_client.screen_stocks_raw(
            filters=normalized_filters,
            signal=signal,
            order=order,
            max_results=max_results,
        )

        if not stocks:
            return [
                TextContent(
                    type="text",
                    text=f"No stocks found matching filters: {normalized_filters}",
                )
            ]

        # --- Format output ---
        # The export endpoint ignores ``ar``, so every matching row comes back
        # and the cut happens here. Say which of the two situations produced
        # these rows instead of implying the cut selected a top N (audit B7).
        lines = []
        lines.append(f"Custom Screener Results ({len(stocks)} of {total_matches} rows)")
        lines.append("=" * 60)
        lines.append(f"Filters: {normalized_filters}")
        if signal:
            lines.append(f"Signal : {signal}")
        if order:
            if order_verified:
                lines.append(
                    f"Order  : {order} (sent as o={order} and re-sorted "
                    f"client-side on the parsed values before the cut)"
                )
            else:
                lines.append(
                    f"Order  : {order} (sent as o={order}; this column has no "
                    f"client-side equivalent, so the ordering could not be "
                    f"verified - the rows below are the first "
                    f"{len(stocks)} Finviz returned, not a verified ranking)"
                )
        elif total_matches > len(stocks):
            lines.append(
                f"Order  : none requested - these are the first {len(stocks)} "
                f"rows in Finviz's default order (reverse ticker), not a "
                f"ranking. Pass `order` to choose what the cut keeps."
            )
        lines.append("")

        for stock in stocks:
            ticker = getattr(stock, "ticker", "N/A")
            company = getattr(stock, "company_name", "N/A")
            sector = getattr(stock, "sector", "N/A")
            industry = getattr(stock, "industry", "N/A")
            price = getattr(stock, "price", None)
            change = getattr(stock, "price_change", None)
            volume = getattr(stock, "volume", None)
            market_cap = getattr(stock, "market_cap", None)
            pe = getattr(stock, "pe_ratio", None)
            rel_volume = getattr(stock, "relative_volume", None)
            dividend_yield = getattr(stock, "dividend_yield", None)
            eps_surprise = getattr(stock, "eps_surprise", None)

            price_str = f"${price:.2f}" if price is not None else "N/A"
            change_str = f"{change:+.2f}%" if change is not None else "N/A"
            vol_str = format_large_number(volume) if volume is not None else "N/A"
            mcap_str = (
                format_large_number(market_cap * 1e6)
                if market_cap is not None
                else "N/A"
            )
            pe_str = f"{pe:.1f}" if pe is not None else "N/A"
            rv_str = f"{rel_volume:.2f}" if rel_volume is not None else "N/A"

            lines.append(f"{ticker} | {company}")
            lines.append(f"  Sector: {sector} | Industry: {industry}")
            lines.append(
                f"  Price: {price_str} | Change: {change_str} | Volume: {vol_str}"
            )
            lines.append(
                f"  Market Cap: {mcap_str} | P/E: {pe_str} | Rel Volume: {rv_str}"
            )

            extras = []
            if dividend_yield is not None:
                extras.append(f"Div Yield: {dividend_yield:.2f}%")
            if eps_surprise is not None:
                extras.append(f"EPS Surprise: {eps_surprise:+.2f}%")
            if extras:
                lines.append(f"  {' | '.join(extras)}")

            lines.append("")

        return [TextContent(type="text", text="\n".join(lines))]

    except Exception as e:
        logger.error(f"Error in custom_screener: {str(e)}")
        raise
