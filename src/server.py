#!/usr/bin/env python3
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent

from .utils.validators import validate_ticker
from .finviz_client.base import FinvizClient
from .finviz_client.screener import FinvizScreener
from .finviz_client.news import FinvizNewsClient
from .finviz_client.sector_analysis import FinvizSectorAnalysisClient

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
        # Build screening parameters
        params = {
            'earnings_date': earnings_date,
            'market_cap': market_cap,
            'min_price': min_price,
            'max_price': max_price,
            'min_volume': min_volume,
            'sectors': sectors or [],
            'premarket_price_change': premarket_price_change or {},
            'afterhours_price_change': afterhours_price_change or {}
        }
        
        # Execute screening
        results = finviz_screener.earnings_screen(**params)
        
        # Format results
        if not results:
            return [TextContent(type="text", text="No stocks found matching the criteria.")]
        
        # Create formatted output
        output_lines = [
            f"Earnings Screening Results ({len(results)} stocks found):",
            "=" * 60,
            ""
        ]
        
        for stock in results:
            output_lines.extend([
                f"Ticker: {stock.ticker}",
                f"Company: {stock.company_name}",
                f"Sector: {stock.sector}",
                f"Price: ${stock.price:.2f}" if stock.price else "Price: N/A",
                f"Market Cap: {stock.market_cap}" if stock.market_cap else "Market Cap: N/A",
                f"Volume: {stock.volume:,}" if stock.volume else "Volume: N/A",
                f"Change: {stock.price_change:.2f}%" if stock.price_change else "Change: N/A",
                f"Earnings Date: {stock.earnings_date}" if stock.earnings_date else "Earnings Date: N/A",
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
    min_avg_volume: Optional[int] = 100000,
    min_relative_volume: Optional[float] = 1.5,
    min_price_change: Optional[float] = 2.0,
    sma_filter: Optional[str] = "above_sma200",
    stocks_only: Optional[bool] = True,
    max_results: Optional[int] = 50,
    sort_by: Optional[str] = "price_change",
    sectors: Optional[List[str]] = None,
    exclude_sectors: Optional[List[str]] = None
) -> List[TextContent]:
    """
    出来高急増を伴う上昇銘柄のスクリーニング
    
    Args:
        market_cap: 時価総額フィルタ
        min_price: 最低株価
        min_avg_volume: 最低平均出来高
        min_relative_volume: 最低相対出来高倍率
        min_price_change: 最低価格変動率(%)
        sma_filter: 移動平均線フィルタ
        stocks_only: 株式のみ（ETF除外）
        max_results: 最大取得件数
        sort_by: ソート基準
        sectors: 対象セクター
        exclude_sectors: 除外セクター
    """
    try:
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
        
        results = finviz_screener.volume_surge_screen(**params)
        
        if not results:
            return [TextContent(type="text", text="No stocks found matching the criteria.")]
        
        output_lines = [
            f"Volume Surge Screening Results ({len(results)} stocks found):",
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
                f"Volume: {stock.volume:,}" if stock.volume else "Volume: N/A",
                f"Relative Volume: {stock.relative_volume:.2f}x" if stock.relative_volume else "Relative Volume: N/A",
                f"Market Cap: {stock.market_cap}" if stock.market_cap else "Market Cap: N/A",
                "-" * 40,
                ""
            ])
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
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
            return [TextContent(type="text", text=f"Invalid ticker: {ticker}")]
        
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
            return [TextContent(type="text", text="No tickers provided.")]
        
        # Validate all tickers
        invalid_tickers = [ticker for ticker in tickers if not validate_ticker(ticker)]
        if invalid_tickers:
            return [TextContent(type="text", text=f"Invalid tickers: {', '.join(invalid_tickers)}")]
        
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
        
        results = finviz_screener.trend_reversion_screen(**params)
        
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
    price_change: Optional[float] = None
) -> List[TextContent]:
    """
    上昇トレンド銘柄のスクリーニング
    
    Args:
        trend_type: トレンドタイプ (strong_uptrend, breakout, momentum)
        sma_period: 移動平均期間 (20, 50, 200)
        relative_volume: 相対出来高最低値
        price_change: 価格変化率最低値
    """
    try:
        params = {
            'trend_type': trend_type,
            'sma_period': sma_period,
            'relative_volume': relative_volume,
            'price_change': price_change
        }
        
        results = finviz_screener.uptrend_screen(**params)
        
        if not results:
            return [TextContent(type="text", text="No uptrend stocks found.")]
        
        output_lines = [
            f"Uptrend Screening Results ({len(results)} stocks found):",
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
                f"Relative Volume: {stock.relative_volume:.2f}x" if stock.relative_volume else "Relative Volume: N/A",
                f"SMA 20: ${stock.sma_20:.2f}" if stock.sma_20 else "SMA 20: N/A",
                f"SMA 50: ${stock.sma_50:.2f}" if stock.sma_50 else "SMA 50: N/A",
                "-" * 40,
                ""
            ])
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except Exception as e:
        logger.error(f"Error in uptrend_screener: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def dividend_growth_screener(
    min_dividend_yield: Optional[float] = None,
    max_dividend_yield: Optional[float] = None,
    min_dividend_growth: Optional[float] = None,
    min_payout_ratio: Optional[float] = None,
    max_payout_ratio: Optional[float] = None,
    min_roe: Optional[float] = None,
    max_debt_equity: Optional[float] = None
) -> List[TextContent]:
    """
    配当成長銘柄のスクリーニング
    
    Args:
        min_dividend_yield: 最低配当利回り
        max_dividend_yield: 最高配当利回り
        min_dividend_growth: 最低配当成長率
        min_payout_ratio: 最低配当性向
        max_payout_ratio: 最高配当性向
        min_roe: 最低ROE
        max_debt_equity: 最高負債比率
    """
    try:
        params = {
            'min_dividend_yield': min_dividend_yield,
            'max_dividend_yield': max_dividend_yield,
            'min_dividend_growth': min_dividend_growth,
            'min_payout_ratio': min_payout_ratio,
            'max_payout_ratio': max_payout_ratio,
            'min_roe': min_roe,
            'max_debt_equity': max_debt_equity
        }
        
        results = finviz_screener.dividend_growth_screen(**params)
        
        if not results:
            return [TextContent(type="text", text="No dividend growth stocks found.")]
        
        output_lines = [
            f"Dividend Growth Screening Results ({len(results)} stocks found):",
            "=" * 60,
            ""
        ]
        
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
        
        results = finviz_screener.etf_screen(**params)
        
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
    min_avg_volume: Optional[int] = 100000,
    min_price_change: Optional[float] = 2.0,
    max_price_change: Optional[float] = None,
    include_premarket_data: Optional[bool] = True,
    max_results: Optional[int] = 60,
    sort_by: Optional[str] = "change_percent",
    sort_order: Optional[str] = "desc",
    sectors: Optional[List[str]] = None,
    exclude_sectors: Optional[List[str]] = None
) -> List[TextContent]:
    """
    寄り付き前決算発表で上昇している銘柄のスクリーニング
    
    Args:
        earnings_timing: 決算発表タイミング
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
        
        results = finviz_screener.earnings_premarket_screen(**params)
        
        if not results:
            return [TextContent(type="text", text="No premarket earnings stocks found.")]
        
        output_lines = [
            f"Premarket Earnings Screening Results ({len(results)} stocks found):",
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
    min_avg_volume: Optional[int] = 100000,
    min_afterhours_change: Optional[float] = 2.0,
    max_afterhours_change: Optional[float] = None,
    include_afterhours_data: Optional[bool] = True,
    max_results: Optional[int] = 60,
    sort_by: Optional[str] = "afterhours_change_percent",
    sort_order: Optional[str] = "desc",
    sectors: Optional[List[str]] = None,
    exclude_sectors: Optional[List[str]] = None
) -> List[TextContent]:
    """
    引け後決算発表で時間外取引上昇銘柄のスクリーニング
    
    Args:
        earnings_timing: 決算発表タイミング
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
        
        results = finviz_screener.earnings_afterhours_screen(**params)
        
        if not results:
            return [TextContent(type="text", text="No afterhours earnings stocks found.")]
        
        output_lines = [
            f"Afterhours Earnings Screening Results ({len(results)} stocks found):",
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
    min_avg_volume: Optional[int] = 200000,
    earnings_revision: Optional[str] = "eps_revenue_positive",
    price_trend: Optional[str] = "positive_change",
    max_results: Optional[int] = 60,
    sort_by: Optional[str] = "eps_surprise",
    sort_order: Optional[str] = "desc",
    sectors: Optional[List[str]] = None,
    exclude_sectors: Optional[List[str]] = None
) -> List[TextContent]:
    """
    決算トレード対象銘柄のスクリーニング（予想上方修正・下落後回復・サプライズ重視）
    
    Args:
        earnings_window: 決算発表期間
        market_cap: 時価総額フィルタ
        min_price: 最低株価
        min_avg_volume: 最低平均出来高
        earnings_revision: 決算予想修正フィルタ
        price_trend: 価格トレンドフィルタ
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
            'max_results': max_results,
            'sort_by': sort_by,
            'sort_order': sort_order,
            'sectors': sectors or [],
            'exclude_sectors': exclude_sectors or []
        }
        
        results = finviz_screener.earnings_trading_screen(**params)
        
        if not results:
            return [TextContent(type="text", text="No earnings trading candidates found.")]
        
        output_lines = [
            f"Earnings Trading Screening Results ({len(results)} stocks found):",
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
                f"4W Performance: {stock.performance_4w:.2f}%" if stock.performance_4w else "4W Performance: N/A",
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
    min_avg_volume: Optional[int] = 500000,
    max_results: Optional[int] = 50,
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
        
        results = finviz_screener.earnings_positive_surprise_screen(**params)
        
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
    days_back: Optional[int] = 7,
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
            return [TextContent(type="text", text=f"Invalid ticker: {ticker}")]
        
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
        
    except Exception as e:
        logger.error(f"Error in get_stock_news: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def get_market_news(
    days_back: Optional[int] = 3,
    max_items: Optional[int] = 20
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
    days_back: Optional[int] = 5,
    max_items: Optional[int] = 15
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
    timeframe: Optional[str] = "1d",
    sectors: Optional[List[str]] = None
) -> List[TextContent]:
    """
    セクター別パフォーマンス分析
    
    Args:
        timeframe: 分析期間 (1d, 1w, 1m, 3m, 6m, 1y)
        sectors: 対象セクター
    """
    try:
        # Get sector performance data
        sector_data = finviz_sector.get_sector_performance(timeframe or "1d", sectors)
        
        if not sector_data:
            return [TextContent(type="text", text="No sector performance data found.")]
        
        # Format output
        output_lines = [
            f"Sector Performance ({timeframe}):",
            "=" * 60,
            ""
        ]
        
        # ヘッダー行
        output_lines.extend([
            f"{'Sector':<25} {'1D':<8} {'1W':<8} {'1M':<8} {'3M':<8} {'6M':<8} {'1Y':<8} {'Stocks':<6}",
            "-" * 75
        ])
        
        # データ行
        for sector in sector_data:
            output_lines.append(
                f"{sector.sector:<25} "
                f"{sector.performance_1d:>7.2f}% "
                f"{sector.performance_1w:>7.2f}% "
                f"{sector.performance_1m:>7.2f}% "
                f"{sector.performance_3m:>7.2f}% "
                f"{sector.performance_6m:>7.2f}% "
                f"{sector.performance_1y:>7.2f}% "
                f"{sector.stock_count:>5}"
            )
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except Exception as e:
        logger.error(f"Error in get_sector_performance: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def get_industry_performance(
    timeframe: Optional[str] = "1d",
    industries: Optional[List[str]] = None
) -> List[TextContent]:
    """
    業界別パフォーマンス分析
    
    Args:
        timeframe: 分析期間 (1d, 1w, 1m, 3m, 6m, 1y)
        industries: 対象業界
    """
    try:
        # Get industry performance data
        industry_data = finviz_sector.get_industry_performance(timeframe or "1d", industries)
        
        if not industry_data:
            return [TextContent(type="text", text="No industry performance data found.")]
        
        # Format output
        output_lines = [
            f"Industry Performance ({timeframe}):",
            "=" * 60,
            ""
        ]
        
        # ヘッダー行
        output_lines.extend([
            f"{'Industry':<35} {'1D':<8} {'1W':<8} {'1M':<8} {'Stocks':<6}",
            "-" * 65
        ])
        
        # データ行
        for industry in industry_data:
            output_lines.append(
                f"{industry['industry']:<35} "
                f"{industry['performance_1d']:>7.2f}% "
                f"{industry['performance_1w']:>7.2f}% "
                f"{industry['performance_1m']:>7.2f}% "
                f"{industry['stock_count']:>5}"
            )
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except Exception as e:
        logger.error(f"Error in get_industry_performance: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def get_country_performance(
    timeframe: Optional[str] = "1d",
    countries: Optional[List[str]] = None
) -> List[TextContent]:
    """
    国別市場パフォーマンス分析
    
    Args:
        timeframe: 分析期間 (1d, 1w, 1m, 3m, 6m, 1y)
        countries: 対象国
    """
    try:
        # Get country performance data
        country_data = finviz_sector.get_country_performance(timeframe or "1d", countries)
        
        if not country_data:
            return [TextContent(type="text", text="No country performance data found.")]
        
        # Format output
        output_lines = [
            f"Country Performance ({timeframe}):",
            "=" * 60,
            ""
        ]
        
        # ヘッダー行
        output_lines.extend([
            f"{'Country':<25} {'1D':<8} {'1W':<8} {'1M':<8} {'Stocks':<6}",
            "-" * 55
        ])
        
        # データ行
        for country in country_data:
            output_lines.append(
                f"{country['country']:<25} "
                f"{country['performance_1d']:>7.2f}% "
                f"{country['performance_1w']:>7.2f}% "
                f"{country['performance_1m']:>7.2f}% "
                f"{country['stock_count']:>5}"
            )
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except Exception as e:
        logger.error(f"Error in get_country_performance: {str(e)}")
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
    min_relative_volume: float,
    min_price: Optional[float] = None,
    sectors: Optional[List[str]] = None,
    max_results: Optional[int] = 50
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
    max_results: Optional[int] = 50
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
    min_avg_volume: Optional[int] = 500000,
    target_sectors: Optional[List[str]] = None,
    pre_earnings_analysis: Optional[Dict[str, Any]] = None,
    risk_assessment: Optional[Dict[str, Any]] = None,
    data_fields: Optional[List[str]] = None,
    max_results: Optional[int] = 100,
    sort_by: Optional[str] = "earnings_date",
    sort_order: Optional[str] = "asc",
    include_chart_view: Optional[bool] = True,
    earnings_calendar_format: Optional[bool] = False
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
    
    Returns:
        来週決算予定銘柄のスクリーニング結果
    """
    try:
        # パラメータの準備
        params = {
            'earnings_period': earnings_period,
            'market_cap': market_cap,
            'min_price': min_price,
            'min_avg_volume': min_avg_volume,
            'target_sectors': target_sectors or [
                "technology", "industrials", "healthcare", "communication_services",
                "consumer_cyclical", "financial", "consumer_defensive", "basic_materials"
            ],
            'max_results': max_results,
            'sort_by': sort_by,
            'sort_order': sort_order
        }
        
        # 決算前分析項目の設定
        if pre_earnings_analysis:
            params['pre_earnings_analysis'] = pre_earnings_analysis
        
        # リスク評価項目の設定
        if risk_assessment:
            params['risk_assessment'] = risk_assessment
        
        # データフィールドの設定
        if data_fields:
            params['data_fields'] = data_fields
        
        # スクリーニング実行
        finviz_screener = FinvizScreener()
        results = finviz_screener.upcoming_earnings_screen(**params)
        
        if not results:
            return [TextContent(type="text", text="No upcoming earnings stocks found.")]
        
        # 結果の表示
        if earnings_calendar_format:
            output_lines = _format_earnings_calendar(results, include_chart_view)
        else:
            output_lines = _format_upcoming_earnings_list(results, include_chart_view)
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except Exception as e:
        logger.error(f"Error in upcoming_earnings_screener: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

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
            f"   Earnings Date: {stock.earnings_date} | Timing: {stock.earnings_timing}",
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
        
        # スコア表示
        if stock.earnings_potential_score or stock.risk_score:
            output_lines.extend([
                "   📊 Analysis Scores:",
                f"   • Earnings Potential: {stock.earnings_potential_score:.1f}/10" if stock.earnings_potential_score else "   • Earnings Potential: N/A",
                f"   • Risk Score: {stock.risk_score:.1f}/10" if stock.risk_score else "   • Risk Score: N/A",
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

if __name__ == "__main__":
    cli_main()