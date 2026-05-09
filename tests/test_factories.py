from datetime import datetime

from src.models import NewsData, SectorPerformance, StockData
from tests import factories


def test_make_stock_data_returns_real_model_with_common_formatter_fields():
    stock = factories.make_stock_data()

    assert isinstance(stock, StockData)
    assert stock.ticker == "AAPL"
    assert stock.company_name == "AAPL Inc."
    assert stock.relative_volume == 1.25
    assert stock.rel_volume == 1.25
    assert stock.above_sma_200 is True
    assert stock.eps_surprise == 4.5


def test_make_stock_data_allows_precise_overrides():
    stock = factories.make_stock_data(
        ticker="MSFT",
        company_name="Microsoft Corp.",
        price=420.0,
        market_cap=3_500_000.0,
        above_sma_200=False,
    )

    assert stock.ticker == "MSFT"
    assert stock.company_name == "Microsoft Corp."
    assert stock.price == 420.0
    assert stock.market_cap == 3_500_000.0
    assert stock.above_sma_200 is False


def test_make_stock_data_batch_creates_distinct_model_objects():
    stocks = factories.make_stock_data_batch(("AA", "BB"), sector="Healthcare")

    assert [stock.ticker for stock in stocks] == ["AA", "BB"]
    assert [stock.price for stock in stocks] == [150.0, 151.0]
    assert all(isinstance(stock, StockData) for stock in stocks)
    assert all(stock.sector == "Healthcare" for stock in stocks)


def test_make_news_data_returns_datetime_backed_model():
    published_at = datetime(2026, 2, 3, 9, 15)

    news = factories.make_news_data(
        ticker="NVDA", date=published_at, category="earnings"
    )

    assert isinstance(news, NewsData)
    assert news.ticker == "NVDA"
    assert news.date == published_at
    assert news.category == "earnings"
    assert news.url == "https://example.test/news/nvda"


def test_make_sector_performance_returns_complete_model():
    sector = factories.make_sector_performance(
        sector="Energy",
        performance_1d=-0.5,
        stock_count=42,
    )

    assert isinstance(sector, SectorPerformance)
    assert sector.sector == "Energy"
    assert sector.performance_1d == -0.5
    assert sector.performance_1y == 24.0
    assert sector.stock_count == 42
