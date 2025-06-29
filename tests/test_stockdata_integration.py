#!/usr/bin/env python3
"""
StockData統合テスト - 実際のオブジェクト作成と属性アクセスをテスト
server.pyで発生する可能性のある AttributeError を事前に検出
"""

import pytest
from src.models import StockData
from src.server import server

class TestStockDataIntegration:
    """StockDataモデルの統合テスト"""

    def test_stockdata_required_attributes_for_earnings_trading_screener(self):
        """earnings_trading_screenerで使用される属性の存在確認"""
        
        # 実際のStockDataオブジェクトを作成
        stock = StockData(
            ticker="AAPL",
            company_name="Apple Inc.",
            sector="Technology",
            industry="Consumer Electronics"
        )
        
        # server.pyの748行目で使用される属性をテスト
        required_attributes = [
            'ticker', 'company_name', 'sector', 'price', 'price_change',
            'eps_surprise', 'revenue_surprise', 'volatility', 'performance_1m'
        ]
        
        for attr in required_attributes:
            assert hasattr(stock, attr), f"StockData lacks required attribute: {attr}"
        
        # 属性アクセスが例外を発生させないことを確認
        try:
            # server.pyで行われる操作をシミュレート
            ticker = stock.ticker
            company = stock.company_name
            sector = stock.sector
            price = stock.price
            change = stock.price_change
            eps_surprise = stock.eps_surprise
            revenue_surprise = stock.revenue_surprise
            volatility = stock.volatility
            performance_1m = stock.performance_1m  # performance_4w から修正
        except AttributeError as e:
            pytest.fail(f"AttributeError accessing StockData attribute: {e}")

    def test_stockdata_performance_attributes_comprehensive(self):
        """パフォーマンス関連の全属性をテスト"""
        
        stock = StockData(
            ticker="MSFT",
            company_name="Microsoft Corp.",
            sector="Technology",
            industry="Software"
        )
        
        # パフォーマンス関連属性をすべてチェック
        performance_attributes = [
            'performance_1min', 'performance_2min', 'performance_3min',
            'performance_5min', 'performance_10min', 'performance_15min',
            'performance_30min', 'performance_1h', 'performance_2h',
            'performance_4h', 'performance_1w', 'performance_1m',
            'performance_3m', 'performance_6m', 'performance_ytd',
            'performance_1y', 'performance_2y', 'performance_3y',
            'performance_5y', 'performance_10y', 'performance_since_inception'
        ]
        
        for attr in performance_attributes:
            assert hasattr(stock, attr), f"StockData lacks performance attribute: {attr}"
            # None値でもAttributeErrorが発生しないことを確認
            value = getattr(stock, attr)
            assert value is None or isinstance(value, (int, float))

    def test_mock_stockdata_with_complete_attributes(self):
        """完全な属性を持つStockDataオブジェクトのテスト"""
        
        # 完全なサンプルデータでStockDataを作成
        complete_stock = StockData(
            ticker="GOOGL",
            company_name="Alphabet Inc.",
            sector="Technology",
            industry="Internet Content",
            price=150.0,
            price_change=2.5,
            price_change_percent=1.67,
            volume=25000000,
            market_cap=1900000000000,
            pe_ratio=28.5,
            eps=5.89,
            eps_surprise=0.15,
            revenue_surprise=0.05,
            volatility=0.25,
            performance_1w=3.2,
            performance_1m=5.8,
            performance_3m=12.5,
            performance_ytd=18.9,
            performance_1y=22.1,
            eps_qoq_growth=15.2,
            sales_qoq_growth=8.7,
            target_price=165.0,
            rsi=58.5,
            beta=1.05
        )
        
        # server.pyで使用される全ての属性をテスト
        assert complete_stock.ticker == "GOOGL"
        assert complete_stock.company_name == "Alphabet Inc."
        assert complete_stock.price == 150.0
        assert complete_stock.performance_1m == 5.8
        assert complete_stock.eps_surprise == 0.15
        assert complete_stock.revenue_surprise == 0.05

    def test_earnings_trading_screener_output_format(self):
        """earnings_trading_screenerの出力フォーマットをテスト"""
        
        # テスト用のStockDataリストを作成
        test_stocks = [
            StockData(
                ticker="AAPL",
                company_name="Apple Inc.",
                sector="Technology",
                industry="Consumer Electronics",
                price=180.0,
                price_change=2.5,
                eps_surprise=0.12,
                revenue_surprise=0.08,
                volatility=0.22,
                performance_1m=4.5
            ),
            StockData(
                ticker="MSFT",
                company_name="Microsoft Corp.",
                sector="Technology",
                industry="Software",
                price=420.0,
                price_change=-1.2,
                eps_surprise=0.18,
                revenue_surprise=0.03,
                volatility=0.19,
                performance_1m=7.2
            )
        ]
        
        # 各StockDataオブジェクトから文字列を生成
        for stock in test_stocks:
            # server.pyで行われる処理をシミュレート
            try:
                ticker_line = f"Ticker: {stock.ticker}"
                company_line = f"Company: {stock.company_name}"
                sector_line = f"Sector: {stock.sector}"
                price_line = f"Price: ${stock.price:.2f}" if stock.price else "Price: N/A"
                change_line = f"Change: {stock.price_change:.2f}%" if stock.price_change else "Change: N/A"
                eps_surprise_line = f"EPS Surprise: {stock.eps_surprise:.2f}%" if stock.eps_surprise else "EPS Surprise: N/A"
                revenue_surprise_line = f"Revenue Surprise: {stock.revenue_surprise:.2f}%" if stock.revenue_surprise else "Revenue Surprise: N/A"
                volatility_line = f"Volatility: {stock.volatility:.2f}" if stock.volatility else "Volatility: N/A"
                performance_line = f"1M Performance: {stock.performance_1m:.2f}%" if stock.performance_1m else "1M Performance: N/A"
                
                # 正常に文字列が生成されることを確認
                assert ticker_line.startswith("Ticker:")
                assert company_line.startswith("Company:")
                assert price_line.startswith("Price:")
                assert performance_line.startswith("1M Performance:")
                
            except AttributeError as e:
                pytest.fail(f"AttributeError in output format generation: {e}")

    def test_finviz_128_columns_coverage(self):
        """Finvizの128カラムがStockDataモデルで網羅されているかテスト"""
        
        # 重要な Finviz カラムのサンプル
        key_finviz_columns = [
            'ticker', 'company_name', 'sector', 'industry', 'country',
            'price', 'price_change', 'price_change_percent', 'volume', 'avg_volume',
            'market_cap', 'pe_ratio', 'eps', 'dividend_yield', 'beta',
            'performance_1w', 'performance_1m', 'performance_3m', 'performance_ytd',
            'sma_20', 'sma_50', 'sma_200', 'rsi', 'volatility',
            'earnings_date', 'eps_surprise', 'revenue_surprise', 'target_price'
        ]
        
        stock = StockData(ticker="TEST", company_name="Test Corp", sector="Test", industry="Test")
        
        missing_attributes = []
        for column in key_finviz_columns:
            if not hasattr(stock, column):
                missing_attributes.append(column)
        
        if missing_attributes:
            pytest.fail(f"StockData missing key Finviz columns: {missing_attributes}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 