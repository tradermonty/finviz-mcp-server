#!/usr/bin/env python3
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent

from .utils.validators import validate_ticker, validate_market_cap, validate_earnings_date, validate_price_range, validate_sector, validate_volume, validate_screening_params, validate_data_fields
from .utils.formatters import format_large_number
from .finviz_client.base import FinvizClient
from .finviz_client.screener import FinvizScreener
from .finviz_client.news import FinvizNewsClient
from .finviz_client.sector_analysis import FinvizSectorAnalysisClient
from .finviz_client.sec_filings import FinvizSECFilingsClient
# from .finviz_client.edgar_client import EdgarAPIClient  # Disabled due to missing dependency

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP Server
server = FastMCP("Finviz MCP Server")

# Initialize Finviz clients
finviz_client = FinvizClient()
finviz_screener = FinvizScreener()
finviz_news = FinvizNewsClient()
finviz_sector = FinvizSectorAnalysisClient()
finviz_sec = FinvizSECFilingsClient()

# Initialize EDGAR API client
# edgar_client = EdgarAPIClient()  # Disabled due to missing dependency

# Create stub for EDGAR client when disabled
class EdgarClientStub:
    def get_filing_document_content(self, *args, **kwargs):
        return {"status": "error", "error": "EDGAR API client is disabled due to missing dependencies"}
    
    def get_multiple_filing_contents(self, *args, **kwargs):
        return []
    
    def get_company_filings(self, *args, **kwargs):
        return []
    
    def _get_cik_from_ticker(self, *args, **kwargs):
        return None
    
    def get_company_concept(self, *args, **kwargs):
        return {"error": "EDGAR API client is disabled due to missing dependencies"}
    
    @property
    def client(self):
        class StubClient:
            def get_company_facts(self, *args, **kwargs):
                return None
        return StubClient()

edgar_client = EdgarClientStub()

@server.tool()
def earnings_screener(
    earnings_date: str,
    market_cap: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_volume: Optional[int] = None,
    sectors: Optional[List[str]] = None,
    premarket_price_change: Optional[Dict[str, Any]] = None,
    afterhours_price_change: Optional[Dict[str, Any]] = None
) -> List[TextContent]:
    """
    決算発表予定銘柄のスクリーニング
    
    Args:
        earnings_date: 決算発表日の指定 (today_after, tomorrow_before, this_week, within_2_weeks)
        market_cap: 時価総額フィルタ (small, mid, large, mega)
        min_price: 最低株価
        max_price: 最高株価
        min_volume: 最低出来高
        sectors: 対象セクター
        premarket_price_change: 寄り付き前価格変動フィルタ
        afterhours_price_change: 時間外価格変動フィルタ
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
            'earnings_date': earnings_date,
            'market_cap': market_cap,
            'min_price': min_price,
            'max_price': max_price,
            'min_volume': min_volume,
            'sectors': sectors or [],
            'premarket_price_change': premarket_price_change,
            'afterhours_price_change': afterhours_price_change
        }
        
        results = finviz_screener.earnings_screener(**params)
        
        if not results:
            return [TextContent(type="text", text="No stocks found matching the criteria.")]
        
        output_lines = [
            f"Earnings Screening Results ({len(results)} stocks found):",
            "=" * 60,
            "",
            "Default Screening Conditions Applied:",
            "- Market Cap: Small and above ($300M+)",
            "- Earnings Date: Yesterday after-hours OR today before-market",
            "- EPS Revision: Positive (upward revision)",
            "- Average Volume: 200,000+",
            "- Price: $10+",
            "- Price Trend: Positive change",
            "- 4-Week Performance: 0% to negative (recovery candidates)",
            "- Volatility: 1x and above",
            "- Stocks Only: ETFs excluded",
            "- Sort: EPS Surprise (descending)",
            "",
            "=" * 60,
            ""
        ]
        
        for stock in results:
            output_lines.extend([
                f"Ticker: {stock.ticker}",
                f"Company: {stock.company_name}",
                f"Sector: {stock.sector}",
                f"Price: ${stock.price:.2f}" if stock.price else "Price: N/A",
                f"Change: {stock.price_change:.2f}%" if stock.price_change else "Change: N/A",
                f"EPS Surprise: {stock.eps_surprise:.2f}%" if stock.eps_surprise else "EPS Surprise: N/A",
                f"Revenue Surprise: {stock.revenue_surprise:.2f}%" if stock.revenue_surprise else "Revenue Surprise: N/A",
                f"Volatility: {stock.volatility:.2f}" if stock.volatility else "Volatility: N/A",
                f"1M Performance: {stock.performance_1m:.2f}%" if stock.performance_1m else "1M Performance: N/A",
                "-" * 40,
                ""
            ])
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except Exception as e:
        logger.error(f"Error in earnings_screener: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def volume_surge_screener(
    market_cap: Optional[str] = "smallover",
    min_price: Optional[float] = 10,
    min_avg_volume: int = 100000,
    min_relative_volume: Optional[float] = 1.5,
    min_price_change: Optional[float] = 2.0,
    sma_filter: Optional[str] = "above_sma200",
    stocks_only: Optional[bool] = True,
    max_results: int = 50,
    sort_by: Optional[str] = "price_change",
    sectors: Optional[List[str]] = None,
    exclude_sectors: Optional[List[str]] = None
) -> List[TextContent]:
    """
    出来高急増を伴う上昇銘柄のスクリーニング
    
    デフォルト条件（変更可能）：
    - 時価総額：スモール以上 ($300M+)
    - 株式のみ：ETF除外
    - 平均出来高：100,000以上
    - 株価：$10以上
    - 相対出来高：1.5倍以上
    - 価格変動：2%以上上昇
    - 200日移動平均線上
    - 価格変動降順ソート
    
    Args:
        market_cap: 時価総額フィルタ (デフォルト: smallover)
        min_price: 最低株価 (デフォルト: 10)
        min_avg_volume: 最低平均出来高 (デフォルト: 100000)
        min_relative_volume: 最低相対出来高倍率 (デフォルト: 1.5)
        min_price_change: 最低価格変動率(%) (デフォルト: 2.0)
        sma_filter: 移動平均線フィルタ (デフォルト: above_sma200)
        stocks_only: 株式のみ（ETF除外） (デフォルト: True)
        max_results: 最大取得件数 (デフォルト: 50)
        sort_by: ソート基準 (デフォルト: price_change)
        sectors: 対象セクター
        exclude_sectors: 除外セクター
    """
    try:
        # Validate parameters
        if market_cap is not None and not validate_market_cap(market_cap):
            raise ValueError(f"Invalid market_cap: {market_cap}")
        
        if min_price is not None and min_price <= 0:
            raise ValueError(f"Invalid min_price: {min_price}")
        
        if min_avg_volume <= 0:
            raise ValueError(f"Invalid min_avg_volume: {min_avg_volume}")
        
        if min_relative_volume is not None and min_relative_volume <= 0:
            raise ValueError(f"Invalid min_relative_volume: {min_relative_volume}")
        
        if sectors:
            for sector in sectors:
                if not validate_sector(sector):
                    raise ValueError(f"Invalid sector: {sector}")
        
        if exclude_sectors:
            for sector in exclude_sectors:
                if not validate_sector(sector):
                    raise ValueError(f"Invalid exclude_sector: {sector}")
        
        params = {
            'market_cap': market_cap,
            'min_price': min_price,
            'min_avg_volume': min_avg_volume,
            'min_relative_volume': min_relative_volume,
            'min_price_change': min_price_change,
            'sma_filter': sma_filter,
            'stocks_only': stocks_only,
            'max_results': max_results,
            'sort_by': sort_by,
            'sectors': sectors or [],
            'exclude_sectors': exclude_sectors or []
        }
        
        results = finviz_screener.volume_surge_screener(**params)
        
        if not results:
            return [TextContent(type="text", text="No stocks found matching the criteria.")]
        
        # デフォルト条件の表示
        default_conditions = [
            "デフォルト条件:",
            "- 時価総額: スモール以上 ($300M+)",
            "- 株式のみ: ETF除外",
            "- 平均出来高: 100,000以上",
            "- 株価: $10以上",
            "- 相対出来高: 1.5倍以上",
            "- 価格変動: 2%以上上昇",
            "- 200日移動平均線上",
            "- 価格変動降順ソート"
        ]
        
        output_lines = [
            f"Volume Surge Screening Results ({len(results)} stocks found):",
            "=" * 60,
            ""
        ]
        
        # デフォルト条件を表示
        output_lines.extend(default_conditions)
        output_lines.extend(["", "=" * 60, ""])
        
        for stock in results:
            output_lines.extend([
                f"Ticker: {stock.ticker}",
                f"Company: {stock.company_name}",
                f"Sector: {stock.sector}",
                f"Price: ${stock.price:.2f}" if stock.price else "Price: N/A",
                f"Change: {stock.price_change:.2f}%" if stock.price_change else "Change: N/A",
                f"Volume: {stock.volume:,}" if stock.volume else "Volume: N/A",
                f"Relative Volume: {stock.relative_volume:.2f}x" if stock.relative_volume else "Relative Volume: N/A",
                f"Market Cap: {stock.market_cap}" if stock.market_cap else "Market Cap: N/A",
                "-" * 40,
                ""
            ])
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except (ValueError, TypeError) as e:
        logger.error(f"Validation error in volume_surge_screener: {str(e)}")
        raise e  # Re-raise validation errors
    except Exception as e:
        logger.error(f"Error in volume_surge_screener: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def get_stock_fundamentals(
    ticker: str,
    data_fields: Optional[List[str]] = None
) -> List[TextContent]:
    """
    個別銘柄のファンダメンタルデータ取得
    
    Args:
        ticker: 銘柄ティッカー
        data_fields: 取得データフィールド
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
        stock_data = finviz_client.get_stock_data(ticker, data_fields or [])
        
        if not stock_data:
            return [TextContent(type="text", text=f"No data found for ticker: {ticker}")]
        
        # Format output
        output_lines = [
            f"Fundamental Data for {ticker}:",
            "=" * 40,
            ""
        ]
        
        # Add stock information
        if stock_data.company_name:
            output_lines.append(f"Company: {stock_data.company_name}")
        if stock_data.sector:
            output_lines.append(f"Sector: {stock_data.sector}")
        if stock_data.industry:
            output_lines.append(f"Industry: {stock_data.industry}")
        if stock_data.price:
            output_lines.append(f"Price: ${stock_data.price:.2f}")
        if stock_data.market_cap:
            output_lines.append(f"Market Cap: {stock_data.market_cap}")
        if stock_data.pe_ratio:
            output_lines.append(f"P/E Ratio: {stock_data.pe_ratio:.2f}")
        if stock_data.eps:
            output_lines.append(f"EPS: ${stock_data.eps:.2f}")
        if stock_data.dividend_yield:
            output_lines.append(f"Dividend Yield: {stock_data.dividend_yield:.2f}%")
        if stock_data.volume:
            output_lines.append(f"Volume: {stock_data.volume:,}")
        if stock_data.avg_volume:
            output_lines.append(f"Avg Volume: {stock_data.avg_volume:,}")
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except (ValueError, TypeError) as e:
        logger.error(f"Validation error in get_stock_fundamentals: {str(e)}")
        raise e  # Re-raise validation errors
    except Exception as e:
        logger.error(f"Error in get_stock_fundamentals: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def get_multiple_stocks_fundamentals(
    tickers: List[str],
    data_fields: Optional[List[str]] = None
) -> List[TextContent]:
    """
    複数銘柄のファンダメンタルデータ一括取得
    
    Args:
        tickers: 銘柄ティッカーリスト
        data_fields: 取得データフィールド
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
        
        results = []
        for ticker in tickers:
            try:
                stock_data = finviz_client.get_stock_data(ticker, data_fields or [])
                if stock_data:
                    results.append(stock_data)
            except Exception as e:
                logger.warning(f"Failed to get data for {ticker}: {str(e)}")
        
        if not results:
            return [TextContent(type="text", text="No data found for any of the provided tickers.")]
        
        # Format output
        output_lines = [
            f"Fundamental Data for {len(results)} stocks:",
            "=" * 60,
            ""
        ]
        
        for stock in results:
            output_lines.extend([
                f"Ticker: {stock.ticker}",
                f"Company: {stock.company_name}" if stock.company_name else "Company: N/A",
                f"Sector: {stock.sector}" if stock.sector else "Sector: N/A",
                f"Price: ${stock.price:.2f}" if stock.price else "Price: N/A",
                f"Market Cap: {stock.market_cap}" if stock.market_cap else "Market Cap: N/A",
                f"P/E Ratio: {stock.pe_ratio:.2f}" if stock.pe_ratio else "P/E Ratio: N/A",
                "-" * 40,
                ""
            ])
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except (ValueError, TypeError) as e:
        logger.error(f"Validation error in get_multiple_stocks_fundamentals: {str(e)}")
        raise e  # Re-raise validation errors
    except Exception as e:
        logger.error(f"Error in get_multiple_stocks_fundamentals: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def trend_reversion_screener(
    market_cap: Optional[str] = "mid_large",
    eps_growth_qoq: Optional[float] = None,
    revenue_growth_qoq: Optional[float] = None,
    rsi_max: Optional[float] = None,
    sectors: Optional[List[str]] = None,
    exclude_sectors: Optional[List[str]] = None
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
            'market_cap': market_cap,
            'eps_growth_qoq': eps_growth_qoq,
            'revenue_growth_qoq': revenue_growth_qoq,
            'rsi_max': rsi_max,
            'sectors': sectors or [],
            'exclude_sectors': exclude_sectors or []
        }
        
        results = finviz_screener.trend_reversion_screener(**params)
        
        if not results:
            return [TextContent(type="text", text="No trend reversal candidates found.")]
        
        output_lines = [
            f"Trend Reversal Screening Results ({len(results)} stocks found):",
            "=" * 60,
            ""
        ]
        
        for stock in results:
            output_lines.extend([
                f"Ticker: {stock.ticker}",
                f"Company: {stock.company_name}",
                f"Sector: {stock.sector}",
                f"Price: ${stock.price:.2f}" if stock.price else "Price: N/A",
                f"P/E Ratio: {stock.pe_ratio:.2f}" if stock.pe_ratio else "P/E Ratio: N/A",
                f"RSI: {stock.rsi:.2f}" if stock.rsi else "RSI: N/A",
                f"EPS Growth: {stock.eps_qoq_growth:.2f}%" if stock.eps_qoq_growth else "EPS Growth: N/A",
                f"Revenue Growth: {stock.sales_qoq_growth:.2f}%" if stock.sales_qoq_growth else "Revenue Growth: N/A",
                "-" * 40,
                ""
            ])
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except Exception as e:
        logger.error(f"Error in trend_reversion_screener: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def uptrend_screener(
    trend_type: Optional[str] = "strong_uptrend",
    sma_period: Optional[str] = "20",
    relative_volume: Optional[float] = None,
    price_change: Optional[float] = None,
    market_cap: Optional[str] = None,
    min_price: Optional[float] = None,
    min_avg_volume: Optional[int] = None,
    near_52w_high: Optional[float] = None,
    performance_4w_positive: Optional[bool] = None,
    sma20_above: Optional[bool] = None,
    sma200_above: Optional[bool] = None,
    sma50_above_sma200: Optional[bool] = None,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = None,
    sectors: Optional[List[str]] = None,
    exclude_sectors: Optional[List[str]] = None
) -> List[TextContent]:
    """
    上昇トレンド銘柄のスクリーニング
    
    デフォルト条件（変更可能）：
    - 時価総額：スモール以上
    - 平均出来高：100,000以上
    - 株価：10以上
    - 52週高値から30%以内
    - 4週パフォーマンス上昇
    - 20日移動平均線上
    - 200日移動平均線上
    - 50日移動平均線が200日移動平均線上
    - EPS成長率（年次）降順ソート
    
    Args:
        trend_type: トレンドタイプ (strong_uptrend, breakout, momentum)
        sma_period: 移動平均期間 (20, 50, 200)
        relative_volume: 相対出来高最低値
        price_change: 価格変化率最低値
        market_cap: 時価総額フィルタ（デフォルト: smallover）
        min_price: 最低株価（デフォルト: 10.0）
        min_avg_volume: 最低平均出来高（デフォルト: 100000）
        near_52w_high: 52週高値からの距離%（デフォルト: 30.0）
        performance_4w_positive: 4週パフォーマンス上昇（デフォルト: True）
        sma20_above: 20日移動平均線上（デフォルト: True）
        sma200_above: 200日移動平均線上（デフォルト: True）
        sma50_above_sma200: 50日移動平均線が200日移動平均線上（デフォルト: True）
        sort_by: ソート基準（デフォルト: eps_growth_this_y）
        sort_order: ソート順序（デフォルト: desc）
        sectors: 対象セクター
        exclude_sectors: 除外セクター
    """
    try:
        params = {
            'trend_type': trend_type,
            'sma_period': sma_period,
            'relative_volume': relative_volume,
            'price_change': price_change,
            'market_cap': market_cap,
            'min_price': min_price,
            'min_avg_volume': min_avg_volume,
            'near_52w_high': near_52w_high,
            'performance_4w_positive': performance_4w_positive,
            'sma20_above': sma20_above,
            'sma200_above': sma200_above,
            'sma50_above_sma200': sma50_above_sma200,
            'sort_by': sort_by,
            'sort_order': sort_order,
            'sectors': sectors,
            'exclude_sectors': exclude_sectors
        }
        
        results = finviz_screener.uptrend_screener(**params)
        
        if not results:
            return [TextContent(type="text", text="デフォルト条件または指定された条件で上昇トレンド銘柄が見つかりませんでした。")]
        
        # デフォルト条件の表示
        default_conditions = [
            "デフォルト条件:",
            "- 時価総額: スモール以上",
            "- 平均出来高: 100,000以上",
            "- 株価: 10以上",
            "- 52週高値から30%以内",
            "- 4週パフォーマンス: 上昇",
            "- 20日移動平均線上",
            "- 200日移動平均線上", 
            "- 50日移動平均線が200日移動平均線上",
            "- EPS成長率（年次）降順ソート"
        ]
        
        output_lines = [
            f"上昇トレンドスクリーニング結果 ({len(results)}銘柄発見):",
            "=" * 60,
            ""
        ] + default_conditions + ["", "検出された銘柄:", "-" * 40, ""]
        
        for stock in results:
            # より詳細な情報を表示
            output_lines.extend([
                f"ティッカー: {stock.ticker}",
                f"会社名: {stock.company_name}",
                f"セクター: {stock.sector}",
                f"株価: ${stock.price:.2f}" if stock.price else "株価: N/A",
                f"変動: {stock.price_change:.2f}%" if stock.price_change else "変動: N/A",
                f"相対出来高: {stock.relative_volume:.2f}x" if stock.relative_volume else "相対出来高: N/A",
                f"出来高: {stock.volume:,}" if stock.volume else "出来高: N/A",
                f"20日移動平均: ${stock.sma_20:.2f}" if stock.sma_20 else "20日移動平均: N/A",
                f"50日移動平均: ${stock.sma_50:.2f}" if stock.sma_50 else "50日移動平均: N/A",
                f"200日移動平均: ${stock.sma_200:.2f}" if stock.sma_200 else "200日移動平均: N/A",
                f"52週高値: ${stock.week_52_high:.2f}" if stock.week_52_high else "52週高値: N/A",
                f"52週安値: ${stock.week_52_low:.2f}" if stock.week_52_low else "52週安値: N/A",
                f"P/E比: {stock.pe_ratio:.2f}" if stock.pe_ratio else "P/E比: N/A",
                f"EPS成長率: {stock.eps_growth_this_y:.2f}%" if stock.eps_growth_this_y else "EPS成長率: N/A",
                f"1ヶ月パフォーマンス: {stock.performance_1m:.2f}%" if stock.performance_1m else "1ヶ月パフォーマンス: N/A",
                "-" * 40,
                ""
            ])
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except Exception as e:
        logger.error(f"Error in uptrend_screener: {str(e)}")
        return [TextContent(type="text", text=f"エラー: {str(e)}")]

@server.tool()
def dividend_growth_screener(
    market_cap: Optional[str] = "midover",
    min_dividend_yield: Optional[float] = 2.0,
    max_dividend_yield: Optional[float] = None,
    min_dividend_growth: Optional[float] = None,
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
    sort_by: Optional[str] = "sma200",
    sort_order: Optional[str] = "asc"
) -> List[TextContent]:
    """
    配当成長銘柄のスクリーニング
    
    デフォルト条件（変更可能）：
    - 時価総額：ミッド以上 ($2B+)
    - 配当利回り：2%以上
    - EPS 5年成長率：プラス
    - EPS QoQ成長率：プラス
    - EPS YoY成長率：プラス
    - PBR：5以下
    - PER：30以下
    - 売上5年成長率：プラス
    - 売上QoQ成長率：プラス
    - 地域：アメリカ
    - 株式のみ
    - 200日移動平均でソート
    
    Args:
        market_cap: 時価総額フィルタ (デフォルト: midover)
        min_dividend_yield: 最低配当利回り (デフォルト: 2.0)
        max_dividend_yield: 最高配当利回り
        min_dividend_growth: 最低配当成長率
        min_payout_ratio: 最低配当性向
        max_payout_ratio: 最高配当性向
        min_roe: 最低ROE
        max_debt_equity: 最高負債比率
        max_pb_ratio: 最高PBR (デフォルト: 5.0)
        max_pe_ratio: 最高PER (デフォルト: 30.0)
        eps_growth_5y_positive: EPS 5年成長率プラス (デフォルト: True)
        eps_growth_qoq_positive: EPS QoQ成長率プラス (デフォルト: True)
        eps_growth_yoy_positive: EPS YoY成長率プラス (デフォルト: True)
        sales_growth_5y_positive: 売上5年成長率プラス (デフォルト: True)
        sales_growth_qoq_positive: 売上QoQ成長率プラス (デフォルト: True)
        country: 地域 (デフォルト: USA)
        stocks_only: 株式のみ (デフォルト: True)
        sort_by: ソート基準 (デフォルト: sma200)
        sort_order: ソート順序 (デフォルト: asc)
    """
    try:
        params = {
            'market_cap': market_cap,
            'min_dividend_yield': min_dividend_yield,
            'max_dividend_yield': max_dividend_yield,
            'min_dividend_growth': min_dividend_growth,
            'min_payout_ratio': min_payout_ratio,
            'max_payout_ratio': max_payout_ratio,
            'min_roe': min_roe,
            'max_debt_equity': max_debt_equity,
            'max_pb_ratio': max_pb_ratio,
            'max_pe_ratio': max_pe_ratio,
            'eps_growth_5y_positive': eps_growth_5y_positive,
            'eps_growth_qoq_positive': eps_growth_qoq_positive,
            'eps_growth_yoy_positive': eps_growth_yoy_positive,
            'sales_growth_5y_positive': sales_growth_5y_positive,
            'sales_growth_qoq_positive': sales_growth_qoq_positive,
            'country': country,
            'stocks_only': stocks_only,
            'sort_by': sort_by,
            'sort_order': sort_order
        }
        
        results = finviz_screener.dividend_growth_screener(**params)
        
        if not results:
            return [TextContent(type="text", text="No dividend growth stocks found.")]
        
        # デフォルト条件の表示
        default_conditions = [
            "デフォルト条件:",
            "- 時価総額: ミッド以上 ($2B+)",
            "- 配当利回り: 2%以上",
            "- EPS 5年成長率: プラス",
            "- EPS QoQ成長率: プラス",
            "- EPS YoY成長率: プラス",
            "- PBR: 5以下",
            "- PER: 30以下",
            "- 売上5年成長率: プラス",
            "- 売上QoQ成長率: プラス",
            "- 地域: アメリカ",
            "- 株式のみ",
            "- 200日移動平均でソート"
        ]
        
        output_lines = [
            f"Dividend Growth Screening Results ({len(results)} stocks found):",
            "=" * 60,
            ""
        ]
        
        # デフォルト条件を表示
        output_lines.extend(default_conditions)
        output_lines.extend(["", "=" * 60, ""])
        
        for stock in results:
            output_lines.extend([
                f"Ticker: {stock.ticker}",
                f"Company: {stock.company_name}",
                f"Sector: {stock.sector}",
                f"Price: ${stock.price:.2f}" if stock.price else "Price: N/A",
                f"Dividend Yield: {stock.dividend_yield:.2f}%" if stock.dividend_yield else "Dividend Yield: N/A",
                f"P/E Ratio: {stock.pe_ratio:.2f}" if stock.pe_ratio else "P/E Ratio: N/A",
                f"Market Cap: {stock.market_cap}" if stock.market_cap else "Market Cap: N/A",
                "-" * 40,
                ""
            ])
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except Exception as e:
        logger.error(f"Error in dividend_growth_screener: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def etf_screener(
    strategy_type: Optional[str] = "long",
    asset_class: Optional[str] = "equity",
    min_aum: Optional[float] = None,
    max_expense_ratio: Optional[float] = None
) -> List[TextContent]:
    """
    ETF戦略用スクリーニング
    
    Args:
        strategy_type: 戦略タイプ (long, short)
        asset_class: 資産クラス (equity, bond, commodity, currency)
        min_aum: 最低運用資産額
        max_expense_ratio: 最高経費率
    """
    try:
        params = {
            'strategy_type': strategy_type,
            'asset_class': asset_class,
            'min_aum': min_aum,
            'max_expense_ratio': max_expense_ratio
        }
        
        results = finviz_screener.etf_screener(**params)
        
        if not results:
            return [TextContent(type="text", text="No ETFs found matching criteria.")]
        
        output_lines = [
            f"ETF Screening Results ({len(results)} ETFs found):",
            "=" * 60,
            ""
        ]
        
        for stock in results:
            output_lines.extend([
                f"Ticker: {stock.ticker}",
                f"Name: {stock.company_name}",
                f"Price: ${stock.price:.2f}" if stock.price else "Price: N/A",
                f"Volume: {stock.volume:,}" if stock.volume else "Volume: N/A",
                f"Change: {stock.price_change:.2f}%" if stock.price_change else "Change: N/A",
                "-" * 40,
                ""
            ])
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except Exception as e:
        logger.error(f"Error in etf_screener: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def earnings_premarket_screener(
    earnings_timing: Optional[str] = "today_before",
    market_cap: Optional[str] = "smallover",
    min_price: Optional[float] = 10,
    min_avg_volume: int = 100000,
    min_price_change: Optional[float] = 2.0,
    max_price_change: Optional[float] = None,
    include_premarket_data: Optional[bool] = True,
    max_results: int = 60,
    sort_by: Optional[str] = "price_change",
    sort_order: Optional[str] = "desc",
    sectors: Optional[List[str]] = None,
    exclude_sectors: Optional[List[str]] = None
) -> List[TextContent]:
    """
    寄り付き前決算発表で上昇している銘柄のスクリーニング
    
    デフォルト条件（変更可能）：
    - 時価総額: スモール以上 ($300M+)
    - 決算発表: 今日の寄り付き前
    - 平均出来高: 100,000以上
    - 株価: $10以上
    - 価格変動: 2%以上上昇
    - 株式のみ
    - 価格変動降順ソート
    - 最大結果件数: 60件
    
    Args:
        earnings_timing: 決算発表タイミング (today_before, yesterday_after, this_week)
        market_cap: 時価総額フィルタ
        min_price: 最低株価
        min_avg_volume: 最低平均出来高
        min_price_change: 最低価格変動率(%)
        max_price_change: 最高価格変動率(%)
        include_premarket_data: 寄り付き前取引データを含める
        max_results: 最大取得件数
        sort_by: ソート基準
        sort_order: ソート順序
        sectors: 対象セクター
        exclude_sectors: 除外セクター
    """
    try:
        params = {
            'earnings_timing': earnings_timing,
            'market_cap': market_cap,
            'min_price': min_price,
            'min_avg_volume': min_avg_volume,
            'min_price_change': min_price_change,
            'max_price_change': max_price_change,
            'include_premarket_data': include_premarket_data,
            'max_results': max_results,
            'sort_by': sort_by,
            'sort_order': sort_order,
            'sectors': sectors or [],
            'exclude_sectors': exclude_sectors or []
        }
        
        results = finviz_screener.earnings_premarket_screener(**params)
        
        if not results:
            return [TextContent(type="text", text="No premarket earnings stocks found.")]
        
        # デフォルト条件の表示
        default_conditions = [
            "デフォルト条件:",
            "- 時価総額: スモール以上 ($300M+)",
            "- 決算発表: 今日の寄り付き前",
            "- 平均出来高: 100,000以上",
            "- 株価: $10以上",
            "- 価格変動: 2%以上上昇",
            "- 株式のみ",
            "- 価格変動降順ソート",
            "- 最大結果件数: 60件"
        ]
        
        output_lines = [
            f"Premarket Earnings Screening Results ({len(results)} stocks found):",
            "=" * 60,
            ""
        ] + default_conditions + [
            "",
            "検索結果:",
            ""
        ]
        
        for stock in results:
            output_lines.extend([
                f"Ticker: {stock.ticker}",
                f"Company: {stock.company_name}",
                f"Sector: {stock.sector}",
                f"Price: ${stock.price:.2f}" if stock.price else "Price: N/A",
                f"Change: {stock.price_change:.2f}%" if stock.price_change else "Change: N/A",
                f"Premarket Price: ${stock.premarket_price:.2f}" if stock.premarket_price else "Premarket Price: N/A",
                f"Premarket Change: {stock.premarket_change_percent:.2f}%" if stock.premarket_change_percent else "Premarket Change: N/A",
                f"Volume: {stock.volume:,}" if stock.volume else "Volume: N/A",
                f"Relative Volume: {stock.relative_volume:.2f}x" if stock.relative_volume else "Relative Volume: N/A",
                "-" * 40,
                ""
            ])
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except Exception as e:
        logger.error(f"Error in earnings_premarket_screener: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def earnings_afterhours_screener(
    earnings_timing: Optional[str] = "today_after",
    market_cap: Optional[str] = "smallover",
    min_price: Optional[float] = 10,
    min_avg_volume: int = 100000,
    min_afterhours_change: Optional[float] = 2.0,
    max_afterhours_change: Optional[float] = None,
    include_afterhours_data: Optional[bool] = True,
    max_results: int = 60,
    sort_by: Optional[str] = "afterhours_change",
    sort_order: Optional[str] = "desc",
    sectors: Optional[List[str]] = None,
    exclude_sectors: Optional[List[str]] = None
) -> List[TextContent]:
    """
    引け後決算発表で時間外取引上昇銘柄のスクリーニング
    
    デフォルト条件（変更可能）：
    - 時間外取引変動: 2%以上上昇
    - 時価総額: スモール以上 ($300M+)
    - 決算発表: 今日の引け後
    - 平均出来高: 100,000以上
    - 株価: $10以上
    - 株式のみ
    - 時間外変動降順ソート
    - 最大結果件数: 60件
    
    Args:
        earnings_timing: 決算発表タイミング (today_after, yesterday_after, this_week)
        market_cap: 時価総額フィルタ
        min_price: 最低株価
        min_avg_volume: 最低平均出来高
        min_afterhours_change: 最低時間外価格変動率(%)
        max_afterhours_change: 最高時間外価格変動率(%)
        include_afterhours_data: 時間外取引データを含める
        max_results: 最大取得件数
        sort_by: ソート基準
        sort_order: ソート順序
        sectors: 対象セクター
        exclude_sectors: 除外セクター
    """
    try:
        params = {
            'earnings_timing': earnings_timing,
            'market_cap': market_cap,
            'min_price': min_price,
            'min_avg_volume': min_avg_volume,
            'min_afterhours_change': min_afterhours_change,
            'max_afterhours_change': max_afterhours_change,
            'include_afterhours_data': include_afterhours_data,
            'max_results': max_results,
            'sort_by': sort_by,
            'sort_order': sort_order,
            'sectors': sectors or [],
            'exclude_sectors': exclude_sectors or []
        }
        
        results = finviz_screener.earnings_afterhours_screener(**params)
        
        if not results:
            return [TextContent(type="text", text="No afterhours earnings stocks found.")]
        
        # デフォルト条件の表示
        default_conditions = [
            "デフォルト条件:",
            "- 時間外取引変動: 2%以上上昇",
            "- 時価総額: スモール以上 ($300M+)",
            "- 決算発表: 今日の引け後",
            "- 平均出来高: 100,000以上",
            "- 株価: $10以上",
            "- 株式のみ",
            "- 時間外変動降順ソート",
            "- 最大結果件数: 60件"
        ]
        
        output_lines = [
            f"Afterhours Earnings Screening Results ({len(results)} stocks found):",
            "=" * 60,
            ""
        ] + default_conditions + [
            "",
            "検索結果:",
            ""
        ]
        
        for stock in results:
            output_lines.extend([
                f"Ticker: {stock.ticker}",
                f"Company: {stock.company_name}",
                f"Sector: {stock.sector}",
                f"Price: ${stock.price:.2f}" if stock.price else "Price: N/A",
                f"Change: {stock.price_change:.2f}%" if stock.price_change else "Change: N/A",
                f"Afterhours Price: ${stock.afterhours_price:.2f}" if stock.afterhours_price else "Afterhours Price: N/A",
                f"Afterhours Change: {stock.afterhours_change_percent:.2f}%" if stock.afterhours_change_percent else "Afterhours Change: N/A",
                f"Volume: {stock.volume:,}" if stock.volume else "Volume: N/A",
                "-" * 40,
                ""
            ])
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except Exception as e:
        logger.error(f"Error in earnings_afterhours_screener: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def earnings_trading_screener(
    earnings_window: Optional[str] = "yesterday_after_today_before",
    market_cap: Optional[str] = "smallover",
    min_price: Optional[float] = 10,
    min_avg_volume: int = 200000,
    earnings_revision: Optional[str] = "eps_revenue_positive",
    price_trend: Optional[str] = "positive_change",
    performance_4w_range: Optional[str] = "0_to_negative_4w",
    min_volatility: Optional[float] = 1.0,
    stocks_only: Optional[bool] = True,
    max_results: int = 60,
    sort_by: Optional[str] = "eps_surprise",
    sort_order: Optional[str] = "desc",
    sectors: Optional[List[str]] = None,
    exclude_sectors: Optional[List[str]] = None
) -> List[TextContent]:
    """
    決算トレード対象銘柄のスクリーニング（予想上方修正・下落後回復・サプライズ重視）
    
    デフォルト条件（Finvizフィルタ: f=cap_smallover,earningsdate_yesterdayafter|todaybefore,fa_epsrev_ep,sh_avgvol_o200,sh_price_o10,ta_change_u,ta_perf_0to-4w,ta_volatility_1tox&ft=4&o=-epssurprise&ar=60）：
    - 時価総額：スモール以上 ($300M+)
    - 決算発表：昨日の引け後または今日の寄り付き前
    - EPS予想：上方修正
    - 平均出来高：200,000以上
    - 株価：$10以上
    - 価格変動：上昇トレンド
    - 4週パフォーマンス：0%から下落（下落後回復候補）
    - ボラティリティ：1倍以上
    - 株式のみ
    - EPSサプライズ降順ソート
    - 最大結果件数：60件
    
    Args:
        earnings_window: 決算発表期間
        market_cap: 時価総額フィルタ
        min_price: 最低株価
        min_avg_volume: 最低平均出来高
        earnings_revision: 決算予想修正フィルタ
        price_trend: 価格トレンドフィルタ
        performance_4w_range: 4週パフォーマンス範囲
        min_volatility: 最低ボラティリティ
        stocks_only: 株式のみ
        max_results: 最大取得件数
        sort_by: ソート基準
        sort_order: ソート順序
        sectors: 対象セクター
        exclude_sectors: 除外セクター
    """
    try:
        params = {
            'earnings_window': earnings_window,
            'market_cap': market_cap,
            'min_price': min_price,
            'min_avg_volume': min_avg_volume,
            'earnings_revision': earnings_revision,
            'price_trend': price_trend,
            'performance_4w_range': performance_4w_range,
            'min_volatility': min_volatility,
            'stocks_only': stocks_only,
            'max_results': max_results,
            'sort_by': sort_by,
            'sort_order': sort_order,
            'sectors': sectors or [],
            'exclude_sectors': exclude_sectors or []
        }
        
        results = finviz_screener.earnings_trading_screener(**params)
        
        if not results:
            return [TextContent(type="text", text="No earnings trading candidates found.")]
        
        output_lines = [
            f"Earnings Trading Screening Results ({len(results)} stocks found):",
            "=" * 60,
            "",
            "Default Screening Conditions Applied:",
            "- Market Cap: Small and above ($300M+)",
            "- Earnings Date: Yesterday after-hours OR today before-market",
            "- EPS Revision: Positive (upward revision)",
            "- Average Volume: 200,000+",
            "- Price: $10+",
            "- Price Trend: Positive change",
            "- 4-Week Performance: 0% to negative (recovery candidates)",
            "- Volatility: 1x and above",
            "- Stocks Only: ETFs excluded",
            "- Sort: EPS Surprise (descending)",
            "",
            "=" * 60,
            ""
        ]
        
        for stock in results:
            output_lines.extend([
                f"Ticker: {stock.ticker}",
                f"Company: {stock.company_name}",
                f"Sector: {stock.sector}",
                f"Price: ${stock.price:.2f}" if stock.price else "Price: N/A",
                f"Change: {stock.price_change:.2f}%" if stock.price_change else "Change: N/A",
                f"EPS Surprise: {stock.eps_surprise:.2f}%" if stock.eps_surprise else "EPS Surprise: N/A",
                f"Revenue Surprise: {stock.revenue_surprise:.2f}%" if stock.revenue_surprise else "Revenue Surprise: N/A",
                f"Volatility: {stock.volatility:.2f}" if stock.volatility else "Volatility: N/A",
                f"1M Performance: {stock.performance_1m:.2f}%" if stock.performance_1m else "1M Performance: N/A",
                "-" * 40,
                ""
            ])
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except Exception as e:
        logger.error(f"Error in earnings_trading_screener: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def earnings_positive_surprise_screener(
    earnings_period: Optional[str] = "this_week",
    market_cap: Optional[str] = "smallover",
    min_price: Optional[float] = 10,
    min_avg_volume: int = 500000,
    max_results: int = 50,
    sort_by: Optional[str] = "eps_qoq_growth",
    sort_order: Optional[str] = "desc",
    include_chart_view: Optional[bool] = True
) -> List[TextContent]:
    """
    今週決算発表でポジティブサプライズがあって上昇している銘柄のスクリーニング
    
    Args:
        earnings_period: 決算発表期間
        market_cap: 時価総額フィルタ
        min_price: 最低株価
        min_avg_volume: 最低平均出来高
        max_results: 最大取得件数
        sort_by: ソート基準
        sort_order: ソート順序
        include_chart_view: 週足チャートビューを含める
    """
    try:
        params = {
            'earnings_period': earnings_period,
            'market_cap': market_cap,
            'min_price': min_price,
            'min_avg_volume': min_avg_volume,
            'max_results': max_results,
            'sort_by': sort_by,
            'sort_order': sort_order,
            'include_chart_view': include_chart_view
        }
        
        results = finviz_screener.earnings_positive_surprise_screener(**params)
        
        if not results:
            return [TextContent(type="text", text="No positive surprise earnings stocks found.")]
        
        output_lines = [
            f"Positive Surprise Earnings Results ({len(results)} stocks found):",
            "=" * 60,
            ""
        ]
        
        for stock in results:
            output_lines.extend([
                f"Ticker: {stock.ticker}",
                f"Company: {stock.company_name}",
                f"Sector: {stock.sector}",
                f"Price: ${stock.price:.2f}" if stock.price else "Price: N/A",
                f"EPS QoQ Growth: {stock.eps_qoq_growth:.2f}%" if stock.eps_qoq_growth else "EPS QoQ Growth: N/A",
                f"Sales QoQ Growth: {stock.sales_qoq_growth:.2f}%" if stock.sales_qoq_growth else "Sales QoQ Growth: N/A",
                f"EPS Surprise: {stock.eps_surprise:.2f}%" if stock.eps_surprise else "EPS Surprise: N/A",
                f"Revenue Surprise: {stock.revenue_surprise:.2f}%" if stock.revenue_surprise else "Revenue Surprise: N/A",
                f"1W Performance: {stock.performance_1w:.2f}%" if stock.performance_1w else "1W Performance: N/A",
                f"Target Price: ${stock.target_price:.2f}" if stock.target_price else "Target Price: N/A",
                "-" * 40,
                ""
            ])
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except Exception as e:
        logger.error(f"Error in earnings_positive_surprise_screener: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def get_stock_news(
    ticker: str,
    days_back: int = 7,
    news_type: Optional[str] = "all"
) -> List[TextContent]:
    """
    銘柄関連ニュースの取得
    
    Args:
        ticker: 銘柄ティッカー
        days_back: 過去何日分のニュース
        news_type: ニュースタイプ (all, earnings, analyst, insider, general)
    """
    try:
        # Validate ticker
        if not validate_ticker(ticker):
            raise ValueError(f"Invalid ticker: {ticker}")
        
        # Validate days_back
        if days_back <= 0:
            raise ValueError(f"Invalid days_back: {days_back}")
        
        # Get news data
        news_list = finviz_news.get_stock_news(ticker, days_back or 7, news_type or "all")
        
        if not news_list:
            return [TextContent(type="text", text=f"No news found for {ticker} in the last {days_back} days.")]
        
        # Format output
        output_lines = [
            f"News for {ticker} (last {days_back} days):",
            "=" * 50,
            ""
        ]
        
        for news in news_list:
            output_lines.extend([
                f"📰 {news.title}",
                f"🏢 Source: {news.source}",
                f"📅 Date: {news.date.strftime('%Y-%m-%d %H:%M')}",
                f"🏷️ Category: {news.category}",
                f"🔗 URL: {news.url}",
                "-" * 40,
                ""
            ])
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except (ValueError, TypeError) as e:
        logger.error(f"Validation error in get_stock_news: {str(e)}")
        raise e  # Re-raise validation errors
    except Exception as e:
        logger.error(f"Error in get_stock_news: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def get_market_news(
    days_back: int = 3,
    max_items: int = 20
) -> List[TextContent]:
    """
    市場全体のニュースを取得
    
    Args:
        days_back: 過去何日分のニュース
        max_items: 最大取得件数
    """
    try:
        # Get market news
        news_list = finviz_news.get_market_news(days_back or 3, max_items or 20)
        
        if not news_list:
            return [TextContent(type="text", text=f"No market news found in the last {days_back} days.")]
        
        # Format output
        output_lines = [
            f"Market News (last {days_back} days):",
            "=" * 50,
            ""
        ]
        
        for news in news_list:
            output_lines.extend([
                f"📰 {news.title}",
                f"🏢 Source: {news.source}",
                f"📅 Date: {news.date.strftime('%Y-%m-%d %H:%M')}",
                f"🏷️ Category: {news.category}",
                f"🔗 URL: {news.url}",
                "-" * 30,
                ""
            ])
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except Exception as e:
        logger.error(f"Error in get_market_news: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def get_sector_news(
    sector: str,
    days_back: int = 5,
    max_items: int = 15
) -> List[TextContent]:
    """
    特定セクターのニュースを取得
    
    Args:
        sector: セクター名
        days_back: 過去何日分のニュース
        max_items: 最大取得件数
    """
    try:
        # Get sector news
        news_list = finviz_news.get_sector_news(sector, days_back or 5, max_items or 15)
        
        if not news_list:
            return [TextContent(type="text", text=f"No news found for {sector} sector in the last {days_back} days.")]
        
        # Format output
        output_lines = [
            f"{sector} Sector News (last {days_back} days):",
            "=" * 50,
            ""
        ]
        
        for news in news_list:
            output_lines.extend([
                f"📰 {news.title}",
                f"🏢 Source: {news.source}",
                f"📅 Date: {news.date.strftime('%Y-%m-%d %H:%M')}",
                f"🏷️ Category: {news.category}",
                f"🔗 URL: {news.url}",
                "-" * 30,
                ""
            ])
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except Exception as e:
        logger.error(f"Error in get_sector_news: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def get_sector_performance(
    sectors: Optional[List[str]] = None
) -> List[TextContent]:
    """
    セクター別パフォーマンス分析
    
    Args:
        sectors: 対象セクター
    """
    try:
        # Get sector performance data
        sector_data = finviz_sector.get_sector_performance(sectors)
        
        if not sector_data:
            return [TextContent(type="text", text="No sector performance data found.")]
        
        # Format output
        output_lines = [
            "Sector Performance Analysis:",
            "=" * 60,
            ""
        ]
        
        # ヘッダー行を実際のカラムデータに合わせて調整
        output_lines.extend([
            f"{'Sector':<30} {'Market Cap':<15} {'P/E':<8} {'Div Yield':<10} {'Change':<8} {'Stocks':<6}",
            "-" * 75
        ])
        
        # データ行
        for sector in sector_data:
            output_lines.append(
                f"{sector.get('name', 'N/A'):<30} "
                f"{sector.get('market_cap', 'N/A'):<15} "
                f"{sector.get('pe_ratio', 'N/A'):<8} "
                f"{sector.get('dividend_yield', 'N/A'):<10} "
                f"{sector.get('change', 'N/A'):<8} "
                f"{sector.get('stocks', 'N/A'):<6}"
            )
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except Exception as e:
        logger.error(f"Error in get_sector_performance: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def get_industry_performance(
    industries: Optional[List[str]] = None
) -> List[TextContent]:
    """
    業界別パフォーマンス分析
    
    Args:
        industries: 対象業界
    """
    try:
        # Get industry performance data
        industry_data = finviz_sector.get_industry_performance(industries)
        
        if not industry_data:
            return [TextContent(type="text", text="No industry performance data found.")]
        
        # Format output
        output_lines = [
            "Industry Performance Analysis:",
            "=" * 60,
            ""
        ]
        
        # ヘッダー行
        output_lines.extend([
            f"{'Industry':<40} {'Market Cap':<15} {'P/E':<8} {'Change':<8} {'Stocks':<6}",
            "-" * 80
        ])
        
        # データ行
        for industry in industry_data:
            output_lines.append(
                f"{industry.get('industry', 'N/A'):<40} "
                f"{industry.get('market_cap', 'N/A'):<15} "
                f"{industry.get('pe_ratio', 'N/A'):<8} "
                f"{industry.get('change', 'N/A'):<8} "
                f"{industry.get('stocks', 'N/A'):<6}"
            )
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except Exception as e:
        logger.error(f"Error in get_industry_performance: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def get_country_performance(
    countries: Optional[List[str]] = None
) -> List[TextContent]:
    """
    国別市場パフォーマンス分析
    
    Args:
        countries: 対象国
    """
    try:
        # Get country performance data
        country_data = finviz_sector.get_country_performance(countries)
        
        if not country_data:
            return [TextContent(type="text", text="No country performance data found.")]
        
        # Format output
        output_lines = [
            "Country Performance Analysis:",
            "=" * 60,
            ""
        ]
        
        # ヘッダー行
        output_lines.extend([
            f"{'Country':<30} {'Market Cap':<15} {'P/E':<8} {'Change':<8} {'Stocks':<6}",
            "-" * 70
        ])
        
        # データ行
        for country in country_data:
            output_lines.append(
                f"{country.get('country', 'N/A'):<30} "
                f"{country.get('market_cap', 'N/A'):<15} "
                f"{country.get('pe_ratio', 'N/A'):<8} "
                f"{country.get('change', 'N/A'):<8} "
                f"{country.get('stocks', 'N/A'):<6}"
            )
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except Exception as e:
        logger.error(f"Error in get_country_performance: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def get_sector_specific_industry_performance(
    sector: str
) -> List[TextContent]:
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
        timeframe: 分析期間 (1d, 1w, 1m, 3m, 6m, 1y)
    """
    try:
        # Get sector-specific industry performance data
        industry_data = finviz_sector.get_sector_specific_industry_performance(sector)
        
        if not industry_data:
            return [TextContent(type="text", text=f"No industry performance data found for {sector} sector.")]
        
        # Format output
        sector_display = sector.replace('_', ' ').title()
        output_lines = [
            f"{sector_display} Sector - Industry Performance Analysis:",
            "=" * 70,
            ""
        ]
        
        # ヘッダー行
        output_lines.extend([
            f"{'Industry':<45} {'Market Cap':<15} {'P/E':<8} {'Change':<8} {'Stocks':<6}",
            "-" * 85
        ])
        
        # データ行
        for industry in industry_data:
            output_lines.append(
                f"{industry.get('industry', 'N/A'):<45} "
                f"{industry.get('market_cap', 'N/A'):<15} "
                f"{industry.get('pe_ratio', 'N/A'):<8} "
                f"{industry.get('change', 'N/A'):<8} "
                f"{industry.get('stocks', 'N/A'):<6}"
            )
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except Exception as e:
        logger.error(f"Error in get_sector_specific_industry_performance: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def get_capitalization_performance() -> List[TextContent]:
    """
    時価総額別パフォーマンス分析
    """
    try:
        # Get capitalization performance data
        cap_data = finviz_sector.get_capitalization_performance()
        
        if not cap_data:
            return [TextContent(type="text", text="No capitalization performance data found.")]
        
        # Format output
        output_lines = [
            "Capitalization Performance Analysis:",
            "=" * 70,
            ""
        ]
        
        # ヘッダー行
        output_lines.extend([
            f"{'Capitalization':<30} {'Market Cap':<15} {'P/E':<8} {'Change':<8} {'Stocks':<6}",
            "-" * 70
        ])
        
        # データ行
        for cap in cap_data:
            output_lines.append(
                f"{cap.get('capitalization', 'N/A'):<30} "
                f"{cap.get('market_cap', 'N/A'):<15} "
                f"{cap.get('pe_ratio', 'N/A'):<8} "
                f"{cap.get('change', 'N/A'):<8} "
                f"{cap.get('stocks', 'N/A'):<6}"
            )
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except Exception as e:
        logger.error(f"Error in get_capitalization_performance: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def get_market_overview() -> List[TextContent]:
    """
    市場全体の概要を取得
    """
    try:
        # Get market overview data
        overview = finviz_sector.get_market_overview()
        
        if not overview:
            return [TextContent(type="text", text="No market overview data found.")]
        
        # Format output
        output_lines = [
            "Market Overview:",
            "=" * 40,
            ""
        ]
        
        # 市場指数
        if any(key for key in overview.keys() if key not in ['market_status', 'timestamp']):
            output_lines.append("Major Indices:")
            output_lines.append("-" * 20)
            
            for index_name, index_data in overview.items():
                if index_name not in ['market_status', 'timestamp']:
                    if isinstance(index_data, dict):
                        output_lines.append(
                            f"{index_name}: {index_data.get('value', 'N/A')} "
                            f"({index_data.get('change', 'N/A')})"
                        )
                    else:
                        output_lines.append(f"{index_name}: {index_data}")
            
            output_lines.append("")
        
        # 市場ステータス
        if 'market_status' in overview:
            output_lines.append(f"Market Status: {overview['market_status']}")
        
        if 'timestamp' in overview:
            output_lines.append(f"Data: {overview['timestamp']}")
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except Exception as e:
        logger.error(f"Error in get_market_overview: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def get_relative_volume_stocks(
    min_relative_volume: Any,
    min_price: Optional[float] = None,
    sectors: Optional[List[str]] = None,
    max_results: int = 50
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
        params = {
            'min_relative_volume': min_relative_volume,
            'min_price': min_price,
            'sectors': sectors or [],
            'max_results': max_results or 50
        }
        
        # Use volume surge screener as the base
        results = finviz_screener.screen_stocks({
            'relative_volume_min': min_relative_volume,
            'price_min': min_price,
            'sectors': sectors or []
        })
        
        # Sort by relative volume
        results.sort(key=lambda x: x.relative_volume or 0, reverse=True)
        results = results[:max_results or 50]
        
        if not results:
            return [TextContent(type="text", text=f"No stocks found with relative volume >= {min_relative_volume}x.")]
        
        # Format output
        output_lines = [
            f"High Relative Volume Stocks (>= {min_relative_volume}x):",
            "=" * 60,
            ""
        ]
        
        # ヘッダー行
        output_lines.extend([
            f"{'Ticker':<8} {'Company':<25} {'Price':<8} {'Change%':<8} {'Volume':<12} {'Rel Vol':<8}",
            "-" * 70
        ])
        
        # データ行
        for stock in results:
            company_short = (stock.company_name[:22] + "...") if stock.company_name and len(stock.company_name) > 25 else (stock.company_name or "N/A")
            
            output_lines.append(
                f"{stock.ticker:<8} "
                f"{company_short:<25} "
                f"${stock.price:<7.2f} " if stock.price else f"{'N/A':<8} "
                f"{stock.price_change:>7.2f}% " if stock.price_change else f"{'N/A':<8} "
                f"{stock.volume:>11,} " if stock.volume else f"{'N/A':<12} "
                f"{stock.relative_volume:>7.2f}x" if stock.relative_volume else f"{'N/A':<8}"
            )
        
        output_lines.extend([
            "",
            f"Found {len(results)} stocks with unusual volume activity."
        ])
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except Exception as e:
        logger.error(f"Error in get_relative_volume_stocks: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def technical_analysis_screener(
    rsi_min: Optional[float] = None,
    rsi_max: Optional[float] = None,
    price_vs_sma20: Optional[str] = None,
    price_vs_sma50: Optional[str] = None,
    price_vs_sma200: Optional[str] = None,
    min_price: Optional[float] = None,
    min_volume: Optional[int] = None,
    sectors: Optional[List[str]] = None,
    max_results: int = 50
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
        min_volume: 最低出来高
        sectors: 対象セクター
        max_results: 最大取得件数
    """
    try:
        # Build screening parameters
        filters = {}
        
        if rsi_min is not None:
            filters['rsi_min'] = rsi_min
        if rsi_max is not None:
            filters['rsi_max'] = rsi_max
        if price_vs_sma20 == "above":
            filters['sma20_above'] = True
        elif price_vs_sma20 == "below":
            filters['sma20_below'] = True
        if price_vs_sma50 == "above":
            filters['sma50_above'] = True
        elif price_vs_sma50 == "below":
            filters['sma50_below'] = True
        if price_vs_sma200 == "above":
            filters['sma200_above'] = True
        elif price_vs_sma200 == "below":
            filters['sma200_below'] = True
        if min_price is not None:
            filters['price_min'] = min_price
        if min_volume is not None:
            filters['volume_min'] = min_volume
        if sectors:
            filters['sectors'] = sectors
        
        results = finviz_screener.screen_stocks(filters)
        results = results[:max_results or 50]
        
        if not results:
            return [TextContent(type="text", text="No stocks found matching technical criteria.")]
        
        # Format output
        criteria_text = []
        if rsi_min is not None and rsi_max is not None:
            criteria_text.append(f"RSI: {rsi_min}-{rsi_max}")
        elif rsi_min is not None:
            criteria_text.append(f"RSI >= {rsi_min}")
        elif rsi_max is not None:
            criteria_text.append(f"RSI <= {rsi_max}")
        
        if price_vs_sma20:
            criteria_text.append(f"Price {price_vs_sma20} SMA20")
        if price_vs_sma50:
            criteria_text.append(f"Price {price_vs_sma50} SMA50")
        if price_vs_sma200:
            criteria_text.append(f"Price {price_vs_sma200} SMA200")
        
        output_lines = [
            f"Technical Analysis Screening Results:",
            f"Criteria: {', '.join(criteria_text) if criteria_text else 'All stocks'}",
            "=" * 60,
            ""
        ]
        
        for stock in results:
            output_lines.extend([
                f"Ticker: {stock.ticker}",
                f"Company: {stock.company_name}",
                f"Sector: {stock.sector}",
                f"Price: ${stock.price:.2f}" if stock.price else "Price: N/A",
                f"RSI: {stock.rsi:.2f}" if stock.rsi else "RSI: N/A",
                f"SMA 20: ${stock.sma_20:.2f}" if stock.sma_20 else "SMA 20: N/A",
                f"SMA 50: ${stock.sma_50:.2f}" if stock.sma_50 else "SMA 50: N/A",
                f"SMA 200: ${stock.sma_200:.2f}" if stock.sma_200 else "SMA 200: N/A",
                f"Volume: {stock.volume:,}" if stock.volume else "Volume: N/A",
                "-" * 40,
                ""
            ])
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except Exception as e:
        logger.error(f"Error in technical_analysis_screener: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

def cli_main():
    """CLI entry point"""
    server.run()

@server.tool()
def upcoming_earnings_screener(
    earnings_period: Optional[str] = "next_week",
    market_cap: Optional[str] = "smallover",
    min_price: Optional[float] = 10,
    min_avg_volume: int = 500000,  # Support numeric values only for MCP compatibility
    target_sectors: Optional[List[str]] = None,
    pre_earnings_analysis: Optional[Dict[str, Any]] = None,
    risk_assessment: Optional[Dict[str, Any]] = None,
    data_fields: Optional[List[str]] = None,
    max_results: int = 100,
    sort_by: Optional[str] = "earnings_date",
    sort_order: Optional[str] = "asc",
    include_chart_view: Optional[bool] = True,
    earnings_calendar_format: Optional[bool] = False,
    custom_date_range: Optional[str] = None,  # 新機能: カスタム日付範囲 (例: "06-30-2025x07-04-2025")
    start_date: Optional[str] = None,  # 新機能: 開始日 (YYYY-MM-DD format)
    end_date: Optional[str] = None     # 新機能: 終了日 (YYYY-MM-DD format)
) -> List[TextContent]:
    """
    来週決算予定銘柄のスクリーニング（決算トレード事前準備用）
    
    Args:
        earnings_period: 決算発表期間 ('next_week', 'next_2_weeks', 'next_month', 'custom_range')
        market_cap: 時価総額フィルタ ('small', 'mid', 'large', 'mega', 'smallover')
        min_price: 最低株価
        min_avg_volume: 最低平均出来高
        target_sectors: 対象セクター（8セクター）
        pre_earnings_analysis: 決算前分析項目の設定
        risk_assessment: リスク評価項目の設定
        data_fields: 取得するデータフィールド
        max_results: 最大取得件数
        sort_by: ソート基準 ('earnings_date', 'market_cap', 'target_price_upside', 'volatility', 'earnings_potential_score')
        sort_order: ソート順序 ('asc', 'desc')
        include_chart_view: 週足チャートビューを含める
        earnings_calendar_format: 決算カレンダー形式で出力
        custom_date_range: カスタム日付範囲（Finviz形式: "MM-DD-YYYYxMM-DD-YYYY"）
        start_date: 開始日（YYYY-MM-DD形式、end_dateと組み合わせて使用）
        end_date: 終了日（YYYY-MM-DD形式、start_dateと組み合わせて使用）
    
    Returns:
        来週決算予定銘柄のスクリーニング結果
    """
    try:
        # パラメータの準備と正規化
        params = {
            'earnings_period': earnings_period,
            'market_cap': market_cap,
            'min_price': min_price,
            'max_results': max_results,
            'sort_by': sort_by,
            'sort_order': sort_order
        }
        
        # 出来高パラメータの正規化 - 数値と文字列両方をサポート
        if min_avg_volume is not None:
            if isinstance(min_avg_volume, (int, float)):
                # 数値の場合はそのまま使用
                params['avg_volume_min'] = min_avg_volume
            elif isinstance(min_avg_volume, str):
                # 文字列の場合はフィルター値として使用
                params['average_volume'] = min_avg_volume
        
        # セクターの正規化 - upcoming_earnings_screenで使用されるパラメータ名に合わせる
        if target_sectors:
            params['target_sectors'] = target_sectors
        else:
            params['target_sectors'] = [
                "Technology", "Industrials", "Healthcare", "Communication Services",
                "Consumer Cyclical", "Financial Services", "Consumer Defensive", "Basic Materials"
            ]
        
        # 決算前分析項目の設定
        if pre_earnings_analysis:
            params.update(pre_earnings_analysis)
        
        # リスク評価項目の設定
        if risk_assessment:
            params.update(risk_assessment)
        
        # データフィールドの設定は無視（新実装では不要）
        
        # スクリーニング実行 - 新しいadvanced_screenメソッドを使用
        logger.info(f"Executing upcoming earnings screening with params: {params}")
        
        # earnings_dateパラメータの設定（優先順位順）
        # 1. カスタム日付範囲が指定されている場合
        if custom_date_range:
            params['earnings_date'] = custom_date_range
        # 2. 開始日と終了日が両方指定されている場合
        elif start_date and end_date:
            params['earnings_date'] = {'start': start_date, 'end': end_date}
        # 3. 従来の期間指定
        elif earnings_period == 'next_week':
            params['earnings_date'] = 'nextweek'
        elif earnings_period == 'next_2_weeks':
            params['earnings_date'] = 'nextdays5'
        elif earnings_period == 'next_month':
            params['earnings_date'] = 'thismonth'
        else:
            params['earnings_date'] = 'nextweek'  # デフォルト
        # upcoming_earnings_screenメソッドを使用
        try:
            results = finviz_screener.upcoming_earnings_screener(**params)
        except Exception as e:
            logger.warning(f"upcoming_earnings_screen failed, trying earnings_screen: {e}")
            # フォールバック: earnings_screenメソッドを使用
            fallback_params = {
                'earnings_date': params.get('earnings_date', 'nextweek'),
                'market_cap': params.get('market_cap', 'smallover'),
                'min_price': params.get('min_price'),
                'sectors': params.get('target_sectors')
            }
            # None値を除去
            fallback_params = {k: v for k, v in fallback_params.items() if v is not None}
            results = finviz_screener.earnings_screener(**fallback_params)
        
        if not results:
            return [TextContent(type="text", text="No upcoming earnings stocks found.")]
        
        # 結果の表示
        if earnings_calendar_format:
            output_lines = _format_earnings_calendar(results, include_chart_view)
        else:
            output_lines = _format_upcoming_earnings_list(results, include_chart_view)
        
        # Finviz CSV制限についての注意書きを追加
        output_lines.extend([
            "",
            "📋 Note: Finviz CSV export does not include earnings date information in the response,",
            "    even when filtering by earnings date. The stocks above match your earnings date",
            f"    criteria ({earnings_period}) but specific dates are not shown in the CSV data.",
            "    For exact earnings dates, please check the Finviz website directly.",
            "",
            f"🔗 Finviz URL with your filters:",
            f"    {_generate_finviz_url(market_cap, params.get('earnings_date', 'nextweek'))}"
        ])
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except Exception as e:
        logger.error(f"Error in upcoming_earnings_screener: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

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
        start_formatted = client._format_date_for_finviz(earnings_date['start'])
        end_formatted = client._format_date_for_finviz(earnings_date['end'])
        earnings_filter = f"earningsdate_{start_formatted}x{end_formatted}"
    elif isinstance(earnings_date, str) and 'x' in earnings_date:
        # 日付範囲文字列の場合
        earnings_filter = f"earningsdate_{earnings_date}"
    else:
        # 固定期間の場合
        earnings_filter = f"earningsdate_{earnings_date}"
    
    return f"{base_url}{cap_filter},{earnings_filter}"

def _format_upcoming_earnings_list(results: List, include_chart_view: bool = True) -> List[str]:
    """来週決算予定銘柄をリスト形式でフォーマット"""
    output_lines = [
        f"Upcoming Earnings Screening Results ({len(results)} stocks found):",
        "=" * 70,
        ""
    ]
    
    for stock in results:
        output_lines.extend([
            f"📈 {stock.ticker} - {stock.company_name}",
            f"   Sector: {stock.sector} | Industry: {stock.industry}",
            f"   Earnings Date: {stock.earnings_date or 'Not available in CSV'} | Timing: {stock.earnings_timing or 'N/A'}",
            f"   Current Price: ${stock.current_price:.2f}" if stock.current_price else "   Current Price: N/A",
            f"   Market Cap: {format_large_number(stock.market_cap)}" if stock.market_cap else "   Market Cap: N/A",
            f"   PE Ratio: {stock.pe_ratio:.2f}" if stock.pe_ratio else "   PE Ratio: N/A",
            f"   Target Price: ${stock.target_price:.2f}" if stock.target_price else "   Target Price: N/A",
            f"   Target Upside: {stock.target_price_upside:.1f}%" if stock.target_price_upside else "   Target Upside: N/A",
            f"   Analyst Recommendation: {stock.analyst_recommendation}" if stock.analyst_recommendation else "   Analyst Recommendation: N/A",
            f"   Volatility: {stock.volatility:.2f}" if stock.volatility else "   Volatility: N/A",
            f"   Short Interest: {stock.short_interest:.1f}%" if stock.short_interest else "   Short Interest: N/A",
            f"   Avg Volume: {format_large_number(stock.avg_volume)}" if stock.avg_volume else "   Avg Volume: N/A",
            ""
        ])
        
        # Additional metrics (if available)
        additional_metrics = []
        if stock.performance_1w is not None:
            additional_metrics.append(f"   • 1W Performance: {stock.performance_1w:.1f}%")
        if stock.performance_1m is not None:
            additional_metrics.append(f"   • 1M Performance: {stock.performance_1m:.1f}%")
        if stock.rsi is not None:
            additional_metrics.append(f"   • RSI: {stock.rsi:.1f}")
        
        if additional_metrics:
            output_lines.extend([
                "   📊 Additional Metrics:",
                *additional_metrics,
                ""
            ])
        
        output_lines.append("-" * 70)
        output_lines.append("")
    
    return output_lines

def _format_earnings_calendar(results: List, include_chart_view: bool = True) -> List[str]:
    """来週決算予定銘柄をカレンダー形式でフォーマット"""
    output_lines = [
        f"📅 Upcoming Earnings Calendar ({len(results)} stocks)",
        "=" * 70,
        ""
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
        output_lines.extend([
            f"📅 {date}",
            "-" * 30,
            ""
        ])
        
        for stock in stocks:
            upside_str = f"(+{stock.target_price_upside:.1f}%)" if stock.target_price_upside and stock.target_price_upside > 0 else ""
            output_lines.extend([
                f"  • {stock.ticker} - {stock.company_name}",
                f"    ${stock.current_price:.2f} → ${stock.target_price:.2f} {upside_str}" if stock.current_price and stock.target_price else f"    Current: ${stock.current_price:.2f}" if stock.current_price else "    Price: N/A",
                f"    {stock.sector} | PE: {stock.pe_ratio:.1f}" if stock.pe_ratio else f"    {stock.sector}",
                ""
            ])
        
        output_lines.append("")
    
    return output_lines

@server.tool()
def get_sec_filings(
    ticker: str,
    form_types: Optional[List[str]] = None,
    days_back: int = 30,
    max_results: int = 50,
    sort_by: str = "filing_date",
    sort_order: str = "desc"
) -> List[TextContent]:
    """
    指定銘柄のSECファイリングデータを取得
    
    Args:
        ticker: 銘柄ティッカー
        form_types: フォームタイプフィルタ (例: ["10-K", "10-Q", "8-K"])
        days_back: 過去何日分のファイリング (デフォルト: 30日)
        max_results: 最大取得件数 (デフォルト: 50件)
        sort_by: ソート基準 ("filing_date", "report_date", "form")
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
            sort_order=sort_order
        )
        
        if not filings:
            return [TextContent(type="text", text=f"No SEC filings found for {ticker} in the last {days_back} days.")]
        
        # Format output
        form_filter_text = f" (Forms: {', '.join(form_types)})" if form_types else ""
        output_lines = [
            f"📄 SEC Filings for {ticker}{form_filter_text}:",
            f"📅 Period: Last {days_back} days | Results: {len(filings)} filings",
            "=" * 80,
            ""
        ]
        
        for filing in filings:
            output_lines.extend([
                f"📅 Filing Date: {filing.filing_date} | Report Date: {filing.report_date}",
                f"📋 Form: {filing.form}",
                f"📝 Description: {filing.description}",
                f"🔗 Filing URL: {filing.filing_url}",
                f"📄 Document URL: {filing.document_url}",
                "-" * 60,
                ""
            ])
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except (ValueError, TypeError) as e:
        logger.error(f"Validation error in get_sec_filings: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Error in get_sec_filings: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def get_major_sec_filings(
    ticker: str,
    days_back: int = 90
) -> List[TextContent]:
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
            return [TextContent(type="text", text=f"No major SEC filings found for {ticker} in the last {days_back} days.")]
        
        # Format output
        output_lines = [
            f"📊 Major SEC Filings for {ticker}:",
            f"📅 Period: Last {days_back} days | Results: {len(filings)} filings",
            "=" * 80,
            "",
            "📋 Form Types: 10-K (Annual), 10-Q (Quarterly), 8-K (Current), DEF 14A (Proxy), SC 13G/D (Ownership)",
            "",
            "=" * 80,
            ""
        ]
        
        # Group by form type for better organization
        forms_dict = {}
        for filing in filings:
            form_type = filing.form
            if form_type not in forms_dict:
                forms_dict[form_type] = []
            forms_dict[form_type].append(filing)
        
        for form_type, form_filings in forms_dict.items():
            output_lines.extend([
                f"📋 Form {form_type} ({len(form_filings)} filings):",
                "-" * 40,
                ""
            ])
            
            for filing in form_filings:
                output_lines.extend([
                    f"  📅 {filing.filing_date} | Report: {filing.report_date}",
                    f"  📝 {filing.description}",
                    f"  🔗 Filing: {filing.filing_url}",
                    f"  📄 Document: {filing.document_url}",
                    ""
                ])
            
            output_lines.append("")
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except (ValueError, TypeError) as e:
        logger.error(f"Validation error in get_major_sec_filings: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Error in get_major_sec_filings: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def get_insider_sec_filings(
    ticker: str,
    days_back: int = 30
) -> List[TextContent]:
    """
    インサイダー取引関連のSECファイリング（フォーム3, 4, 5等）を取得
    
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
            return [TextContent(type="text", text=f"No insider SEC filings found for {ticker} in the last {days_back} days.")]
        
        # Format output
        output_lines = [
            f"👥 Insider SEC Filings for {ticker}:",
            f"📅 Period: Last {days_back} days | Results: {len(filings)} filings",
            "=" * 80,
            "",
            "📋 Form Types:",
            "  • Form 3: Initial ownership statement",
            "  • Form 4: Statement of changes in beneficial ownership",
            "  • Form 5: Annual statement of changes in beneficial ownership",
            "  • 11-K: Annual reports of employee stock purchase plans",
            "",
            "=" * 80,
            ""
        ]
        
        for filing in filings:
            # Determine filing type explanation
            form_explanation = {
                "3": "Initial ownership statement",
                "4": "Changes in beneficial ownership",
                "5": "Annual ownership changes",
                "11-K": "Employee stock purchase plan report"
            }.get(filing.form, "Insider-related filing")
            
            output_lines.extend([
                f"📋 Form {filing.form} - {form_explanation}",
                f"📅 Filing: {filing.filing_date} | Report: {filing.report_date}",
                f"📝 {filing.description}",
                f"🔗 Filing: {filing.filing_url}",
                f"📄 Document: {filing.document_url}",
                "-" * 60,
                ""
            ])
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except (ValueError, TypeError) as e:
        logger.error(f"Validation error in get_insider_sec_filings: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Error in get_insider_sec_filings: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def get_sec_filing_summary(
    ticker: str,
    days_back: int = 90
) -> List[TextContent]:
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
            return [TextContent(type="text", text=f"Error getting filing summary for {ticker}: {summary['error']}")]
        
        if summary.get("total_filings", 0) == 0:
            return [TextContent(type="text", text=f"No SEC filings found for {ticker} in the last {days_back} days.")]
        
        # Format output
        output_lines = [
            f"📊 SEC Filing Summary for {ticker}:",
            f"📅 Period: Last {summary['period_days']} days",
            f"📄 Total Filings: {summary['total_filings']}",
            f"📅 Latest Filing: {summary.get('latest_filing_date', 'N/A')} ({summary.get('latest_filing_form', 'N/A')})",
            "=" * 60,
            "",
            "📋 Filing Breakdown by Form Type:",
            "-" * 40
        ]
        
        # Sort forms by count (descending)
        forms = summary.get("forms", {})
        sorted_forms = sorted(forms.items(), key=lambda x: x[1], reverse=True)
        
        for form_type, count in sorted_forms:
            percentage = (count / summary['total_filings'] * 100) if summary['total_filings'] > 0 else 0
            output_lines.append(f"  📋 {form_type}: {count} filings ({percentage:.1f}%)")
        
        output_lines.extend([
            "",
            "📝 Common Form Types:",
            "  • 10-K: Annual report (comprehensive overview)",
            "  • 10-Q: Quarterly report (financial updates)",
            "  • 8-K: Current report (material events)",
            "  • DEF 14A: Proxy statement (shareholder meetings)",
            "  • 4: Insider trading activities",
            "  • SC 13G/D: Beneficial ownership (>5% ownership changes)"
        ])
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except (ValueError, TypeError) as e:
        logger.error(f"Validation error in get_sec_filing_summary: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Error in get_sec_filing_summary: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def get_edgar_filing_content(
    ticker: str,
    accession_number: str,
    primary_document: str,
    max_length: int = 50000
) -> List[TextContent]:
    """
    EDGAR API経由でSECファイリングドキュメント内容を取得
    
    Args:
        ticker: 銘柄ティッカー
        accession_number: SEC accession number (with dashes)
        primary_document: Primary document filename
        max_length: 最大コンテンツ長 (デフォルト: 50,000文字)
    """
    try:
        # Validate ticker
        if not validate_ticker(ticker):
            raise ValueError(f"Invalid ticker: {ticker}")
        
        logger.info(f"Fetching EDGAR document content for {ticker}: {accession_number}/{primary_document}")
        
        # Get document content via EDGAR API
        content_data = edgar_client.get_filing_document_content(
            ticker=ticker,
            accession_number=accession_number,
            primary_document=primary_document,
            max_length=max_length
        )
        
        if content_data.get('status') == 'error':
            return [TextContent(type="text", text=f"Error: {content_data.get('error', 'Unknown error')}")]
        
        # Format output
        metadata = content_data.get('metadata', {})
        content = content_data.get('content', '')
        
        output_lines = [
            f"📄 SEC Filing Document Content for {ticker}:",
            f"🔗 Document: {accession_number}/{primary_document}",
            f"📅 Retrieved: {metadata.get('retrieved_at', 'N/A')}",
            f"📊 Content Length: {metadata.get('content_length', 0):,} characters",
            "=" * 80,
            "",
            content[:max_length] if len(content) > max_length else content
        ]
        
        if len(content) > max_length:
            output_lines.extend([
                "",
                "=" * 80,
                f"[Content truncated - showing first {max_length:,} characters]"
            ])
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except (ValueError, TypeError) as e:
        logger.error(f"Validation error in get_edgar_filing_content: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Error in get_edgar_filing_content: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def get_multiple_edgar_filing_contents(
    ticker: str,
    filings_data: List[Dict[str, str]],
    max_length: int = 20000
) -> List[TextContent]:
    """
    複数のSECファイリングドキュメント内容をEDGAR API経由で一括取得
    
    Args:
        ticker: 銘柄ティッカー
        filings_data: ファイリングデータのリスト [{"accession_number": "...", "primary_document": "..."}]
        max_length: 各ドキュメントの最大コンテンツ長 (デフォルト: 20,000文字)
    """
    try:
        # Validate ticker
        if not validate_ticker(ticker):
            raise ValueError(f"Invalid ticker: {ticker}")
        
        if not filings_data:
            return [TextContent(type="text", text="No filing data provided.")]
        
        logger.info(f"Fetching {len(filings_data)} EDGAR document contents for {ticker}")
        
        # Prepare filing data with ticker
        filings_with_ticker = []
        for filing in filings_data:
            filing_copy = filing.copy()
            filing_copy['ticker'] = ticker
            filings_with_ticker.append(filing_copy)
        
        # Get multiple document contents via EDGAR API
        results = edgar_client.get_multiple_filing_contents(
            filings_data=filings_with_ticker,
            max_length=max_length
        )
        
        if not results:
            return [TextContent(type="text", text=f"No document contents retrieved for {ticker}.")]
        
        # Format output
        output_lines = [
            f"📄 Multiple SEC Filing Document Contents for {ticker}:",
            f"📊 Retrieved: {len(results)} documents",
            "=" * 80,
            ""
        ]
        
        for i, result in enumerate(results, 1):
            metadata = result.get('metadata', {})
            content = result.get('content', '')
            status = result.get('status', 'unknown')
            
            output_lines.extend([
                f"📋 Document {i}/{len(results)}:",
                f"   📄 File: {metadata.get('accession_number', 'N/A')}/{metadata.get('primary_document', 'N/A')}",
                f"   📅 Retrieved: {metadata.get('retrieved_at', 'N/A')}",
                f"   📊 Length: {metadata.get('content_length', 0):,} characters",
                f"   ✅ Status: {status}",
                ""
            ])
            
            if status == 'error':
                error_msg = result.get('error', 'Unknown error')
                output_lines.extend([
                    f"   ❌ Error: {error_msg}",
                    ""
                ])
            else:
                # Show first 500 characters of content
                preview_length = min(500, len(content))
                preview = content[:preview_length]
                output_lines.extend([
                    f"   📝 Content Preview ({preview_length} chars):",
                    f"   {preview}",
                    ""
                ])
                
                if len(content) > preview_length:
                    output_lines.append(f"   [... {len(content) - preview_length:,} more characters]")
                    output_lines.append("")
            
            output_lines.extend(["-" * 60, ""])
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except (ValueError, TypeError) as e:
        logger.error(f"Validation error in get_multiple_edgar_filing_contents: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Error in get_multiple_edgar_filing_contents: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def get_edgar_company_filings(
    ticker: str,
    form_types: Optional[List[str]] = None,
    max_count: int = 50,
    days_back: int = 365
) -> List[TextContent]:
    """
    EDGAR API経由で企業のファイリング一覧を取得
    
    Args:
        ticker: 銘柄ティッカー
        form_types: フォームタイプフィルタ (例: ["10-K", "10-Q", "8-K"])
        max_count: 最大取得件数 (デフォルト: 50)
        days_back: 過去何日分 (デフォルト: 365日)
    """
    try:
        # Validate ticker
        if not validate_ticker(ticker):
            raise ValueError(f"Invalid ticker: {ticker}")
        
        logger.info(f"Fetching EDGAR filings for {ticker} via EDGAR API")
        
        # Calculate date range
        from datetime import datetime, timedelta
        date_to = datetime.now().strftime('%Y-%m-%d')
        date_from = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        # Get company filings via EDGAR API
        filings = edgar_client.get_company_filings(
            ticker=ticker,
            form_types=form_types,
            date_from=date_from,
            date_to=date_to,
            max_count=max_count
        )
        
        if not filings:
            form_filter_text = f" (forms: {', '.join(form_types)})" if form_types else ""
            return [TextContent(type="text", text=f"No EDGAR filings found for {ticker}{form_filter_text} in the last {days_back} days.")]
        
        # Format output
        output_lines = [
            f"📊 EDGAR Company Filings for {ticker}:",
            f"📅 Period: {date_from} to {date_to} ({days_back} days)",
            f"📄 Results: {len(filings)} filings",
        ]
        
        if form_types:
            output_lines.append(f"📋 Form Filter: {', '.join(form_types)}")
        
        output_lines.extend([
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
            ""
        ])
        
        for filing in filings:
            output_lines.extend([
                f"📋 Form {filing['form']} - {filing.get('description', 'N/A')}",
                f"📅 Filing: {filing['filing_date']} | Report: {filing['report_date']}",
                f"📄 Document: {filing['accession_number']}/{filing['primary_document']}",
                f"🔗 Filing URL: {filing['filing_url']}",
                f"📄 Document URL: {filing['document_url']}",
                "-" * 60,
                ""
            ])
        
        output_lines.extend([
            "",
            "💡 To get document content, use get_edgar_filing_content with:",
            "   ticker, accession_number, and primary_document from above"
        ])
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except (ValueError, TypeError) as e:
        logger.error(f"Validation error in get_edgar_company_filings: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Error in get_edgar_company_filings: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def get_edgar_company_facts(
    ticker: str
) -> List[TextContent]:
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
        cik = edgar_client._get_cik_from_ticker(ticker)
        if not cik:
            return [TextContent(type="text", text=f"Could not find CIK for ticker {ticker}. Please verify the ticker symbol.")]
        
        # Get company facts via EDGAR API
        try:
            company_facts = edgar_client.client.get_company_facts(cik)
        except Exception as e:
            return [TextContent(type="text", text=f"Error fetching company facts for {ticker}: {str(e)}")]
        
        if not company_facts:
            return [TextContent(type="text", text=f"No company facts found for {ticker}.")]
        
        # Extract basic information
        cik = company_facts.get('cik', 'N/A')
        entity_name = company_facts.get('entityName', 'N/A')
        
        # Format output
        output_lines = [
            f"🏢 EDGAR Company Facts for {ticker}:",
            f"📊 Entity Name: {entity_name}",
            f"🔢 CIK: {cik}",
            "=" * 60,
            ""
        ]
        
        # Show available facts/concepts
        facts = company_facts.get('facts', {})
        if facts:
            output_lines.extend([
                "📋 Available Financial Concepts:",
                ""
            ])
            
            # Group by taxonomy
            for taxonomy, concepts in facts.items():
                if concepts:
                    output_lines.extend([
                        f"📊 {taxonomy.upper()} Taxonomy:",
                        f"   📈 Available concepts: {len(concepts)}",
                        ""
                    ])
                    
                    # Show first few concepts as examples
                    concept_names = list(concepts.keys())[:5]
                    for concept in concept_names:
                        concept_data = concepts[concept]
                        description = concept_data.get('description', concept)
                        output_lines.append(f"   • {concept}: {description}")
                    
                    if len(concepts) > 5:
                        output_lines.append(f"   ... and {len(concepts) - 5} more concepts")
                    
                    output_lines.append("")
        
        output_lines.extend([
            "💡 To get specific concept data, use get_edgar_company_concept with:",
            f"   ticker='{ticker}', concept='Assets', taxonomy='us-gaap'"
        ])
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except (ValueError, TypeError) as e:
        logger.error(f"Validation error in get_edgar_company_facts: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Error in get_edgar_company_facts: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def get_edgar_company_concept(
    ticker: str,
    concept: str,
    taxonomy: str = "us-gaap"
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
        concept_data = edgar_client.get_company_concept(
            ticker=ticker,
            concept=concept,
            taxonomy=taxonomy
        )
        
        if 'error' in concept_data:
            return [TextContent(type="text", text=f"Error: {concept_data['error']}")]
        
        # Extract basic information
        cik = concept_data.get('cik', 'N/A')
        entity_name = concept_data.get('entityName', 'N/A')
        concept_label = concept_data.get('label', concept)
        description = concept_data.get('description', 'N/A')
        
        # Format output
        output_lines = [
            f"📊 EDGAR Company Concept: {ticker} - {concept}",
            f"🏢 Entity: {entity_name} (CIK: {cik})",
            f"📋 Concept: {concept_label}",
            f"📝 Description: {description}",
            f"🏷️ Taxonomy: {taxonomy}",
            "=" * 80,
            ""
        ]
        
        # Show units and values
        units = concept_data.get('units', {})
        if units:
            output_lines.append("📊 Available Data Units:")
            output_lines.append("")
            
            for unit_type, unit_data in units.items():
                output_lines.extend([
                    f"💰 Unit: {unit_type}",
                    f"   📈 Data points: {len(unit_data)}",
                    ""
                ])
                
                # Show recent values
                if unit_data:
                    output_lines.append("   📅 Recent Values:")
                    # Sort by end date (most recent first)
                    sorted_data = sorted(unit_data, key=lambda x: x.get('end', ''), reverse=True)
                    
                    for i, entry in enumerate(sorted_data[:10]):  # Show last 10 entries
                        end_date = entry.get('end', 'N/A')
                        value = entry.get('val', 'N/A')
                        form = entry.get('form', 'N/A')
                        filed = entry.get('filed', 'N/A')
                        
                        # Format large numbers
                        if isinstance(value, (int, float)):
                            if value >= 1_000_000_000:
                                formatted_value = f"${value/1_000_000_000:.2f}B"
                            elif value >= 1_000_000:
                                formatted_value = f"${value/1_000_000:.2f}M"
                            elif value >= 1_000:
                                formatted_value = f"${value/1_000:.2f}K"
                            else:
                                formatted_value = f"${value:,.2f}"
                        else:
                            formatted_value = str(value)
                        
                        output_lines.append(f"   • {end_date}: {formatted_value} ({form} filed: {filed})")
                    
                    if len(sorted_data) > 10:
                        output_lines.append(f"   ... and {len(sorted_data) - 10} more entries")
                
                output_lines.append("")
        else:
            output_lines.append("⚠️ No unit data available for this concept.")
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except (ValueError, TypeError) as e:
        logger.error(f"Validation error in get_edgar_company_concept: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Error in get_edgar_company_concept: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
