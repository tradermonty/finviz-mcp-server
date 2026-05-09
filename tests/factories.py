"""Shared test factories for model-shaped fixtures."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Any

from src.models import NewsData, SectorPerformance, StockData


def make_stock_data(
    ticker: str = "AAPL",
    company_name: str | None = None,
    sector: str = "Technology",
    industry: str = "Consumer Electronics",
    **overrides: Any,
) -> StockData:
    """Create a StockData instance with formatter-friendly defaults."""
    data: dict[str, Any] = {
        "ticker": ticker,
        "company_name": company_name or f"{ticker} Inc.",
        "sector": sector,
        "industry": industry,
        "country": "USA",
        "price": 150.0,
        "price_change": 1.5,
        "price_change_percent": 1.0,
        "volume": 1_250_000,
        "avg_volume": 1_000_000,
        "relative_volume": 1.25,
        "rel_volume": 1.25,
        "market_cap": 3_000_000.0,
        "pe_ratio": 25.0,
        "eps": 6.0,
        "dividend_yield": 0.6,
        "profit_margin": 22.5,
        "performance_1w": 2.0,
        "performance_1m": 5.0,
        "performance_3m": 8.0,
        "rsi": 55.0,
        "sma_20": 145.0,
        "sma_50": 140.0,
        "sma_200": 125.0,
        "above_sma_20": True,
        "above_sma_50": True,
        "above_sma_200": True,
        "sma_20_relative": 3.45,
        "sma_50_relative": 7.14,
        "sma_200_relative": 20.0,
        "week_52_high": 180.0,
        "week_52_low": 110.0,
        "high_52w_relative": -16.67,
        "low_52w_relative": 36.36,
        "eps_surprise": 4.5,
        "revenue_surprise": 3.0,
        "target_price": 175.0,
        "analyst_recommendation": "Buy",
    }
    data.update(overrides)
    return StockData(**data)


def make_stock_data_batch(
    tickers: Sequence[str] = ("AAPL", "MSFT"),
    **overrides: Any,
) -> list[StockData]:
    """Create multiple StockData objects with distinct tickers."""
    stocks: list[StockData] = []
    for index, ticker in enumerate(tickers):
        item_overrides = dict(overrides)
        item_overrides.setdefault("company_name", f"{ticker} Inc.")
        item_overrides.setdefault("price", 150.0 + index)
        stocks.append(make_stock_data(ticker=ticker, **item_overrides))
    return stocks


def make_news_data(
    ticker: str = "AAPL",
    title: str | None = None,
    source: str = "Example News",
    date: datetime | None = None,
    url: str | None = None,
    category: str = "company",
    **overrides: Any,
) -> NewsData:
    """Create a NewsData instance with a stable datetime value."""
    data: dict[str, Any] = {
        "ticker": ticker,
        "title": title or f"{ticker} reports test headline",
        "source": source,
        "date": date or datetime(2026, 1, 2, 15, 30),
        "url": url or f"https://example.test/news/{ticker.lower()}",
        "category": category,
    }
    data.update(overrides)
    return NewsData(**data)


def make_sector_performance(
    sector: str = "Technology",
    **overrides: Any,
) -> SectorPerformance:
    """Create a SectorPerformance instance with complete numeric fields."""
    data: dict[str, Any] = {
        "sector": sector,
        "performance_1d": 1.1,
        "performance_1w": 2.2,
        "performance_1m": 4.4,
        "performance_3m": 7.7,
        "performance_6m": 12.5,
        "performance_1y": 24.0,
        "stock_count": 84,
    }
    data.update(overrides)
    return SectorPerformance(**data)
