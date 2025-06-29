#!/usr/bin/env python3
"""
実際のMCP呼び出しによる包括的E2Eテスト
型エラーやカラム名エラーを検出するためのテスト
"""

import pytest
import asyncio
import sys
import os
import logging
from typing import List, Dict, Any, Optional
from unittest.mock import patch, Mock

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.server import server
from src.models import StockData
from src.finviz_client.screener import FinvizScreener
from src.finviz_client.base import FinvizClient
from src.finviz_client.news import FinvizNewsClient
from src.finviz_client.sector_analysis import FinvizSectorAnalysisClient
from src.finviz_client.sec_filings import FinvizSECFilingsClient

# ログ設定
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class TestComprehensiveE2E:
    """実際のMCP呼び出しによる包括的E2Eテスト"""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """各テスト前のセットアップ"""
        # テスト用の完全なStockDataサンプル
        self.sample_stock_data = StockData(
            ticker="AAPL",
            company_name="Apple Inc.",
            sector="Technology",
            industry="Consumer Electronics",
            price=180.50,
            price_change=2.35,
            price_change_percent=1.32,
            volume=45000000,
            avg_volume=55000000,
            relative_volume=0.82,
            market_cap=2800000000000,
            pe_ratio=28.5,
            eps=6.12,
            eps_next_y=6.50,
            eps_surprise=0.12,
            revenue_surprise=0.08,
            dividend_yield=0.48,
            beta=1.23,
            volatility=0.25,
            performance_1w=1.8,
            performance_1m=4.5,
            performance_3m=8.2,
            performance_6m=12.7,
            performance_ytd=18.9,
            performance_1y=22.1,
            sma_20=175.80,
            sma_50=170.20,
            sma_200=165.10,
            rsi=58.5,
            eps_qoq_growth=15.2,
            sales_qoq_growth=8.7,
            target_price=195.0,
            debt_to_equity=1.45,
            current_ratio=1.05,
            roe=28.5,
            roa=15.2,
            gross_margin=0.38,
            operating_margin=0.30,
            profit_margin=0.25,
            insider_ownership=0.07,
            institutional_ownership=0.59,
            shares_outstanding=15500000000,
            shares_float=15400000000,
            earnings_date="2024-01-25",
            week_52_high=195.89,
            week_52_low=124.17
        )

        # 複数銘柄のサンプルデータ
        self.sample_stocks_list = [
            self.sample_stock_data,
            StockData(
                ticker="MSFT",
                company_name="Microsoft Corporation",
                sector="Technology",
                industry="Software—Infrastructure",
                price=420.75,
                price_change=8.25,
                price_change_percent=2.00,
                volume=25000000,
                market_cap=3100000000000,
                pe_ratio=32.1,
                eps=12.05
            )
        ]

    # ===========================================
    # 決算関連スクリーナーテスト
    # ===========================================

    @pytest.mark.asyncio
    async def test_earnings_screener_real_call(self):
        """決算発表予定銘柄スクリーニングの実際の呼び出しテスト"""
        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.return_value = self.sample_stocks_list

            result = await server.call_tool("earnings_screener", {
                "earnings_date": "this_week"
            })

            assert result is not None
            assert len(result) > 0
            result_text = str(result[0].text)
            assert "AAPL" in result_text
            mock_screener.assert_called_once()

    @pytest.mark.asyncio
    async def test_volume_surge_screener_real_call(self):
        """出来高急増スクリーナーのテスト"""
        with patch.object(FinvizScreener, "volume_surge_screener") as mock_screener:
            mock_screener.return_value = self.sample_stocks_list

            result = await server.call_tool("volume_surge_screener", {
                "random_string": "test"
            })

            assert result is not None
            result_text = str(result[0].text)
            assert "固定フィルタ条件" in result_text
            mock_screener.assert_called_once()

    @pytest.mark.asyncio
    async def test_earnings_trading_screener_real_call(self):
        """決算トレード対象銘柄スクリーナーのテスト"""
        with patch.object(FinvizScreener, "earnings_trading_screener") as mock_screener:
            mock_screener.return_value = self.sample_stocks_list

            result = await server.call_tool("earnings_trading_screener", {
                "random_string": "test"
            })

            assert result is not None
            result_text = str(result[0].text)
            assert "EPS Surprise" in result_text or "Revenue Surprise" in result_text
            mock_screener.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_stock_fundamentals_real_call(self):
        """単一銘柄ファンダメンタルデータ取得のテスト"""
        with patch.object(FinvizClient, "get_stock_fundamentals") as mock_client:
            mock_client.return_value = self.sample_stock_data

            result = await server.call_tool("get_stock_fundamentals", {
                "ticker": "AAPL"
            })

            assert result is not None
            result_text = str(result[0].text)
            assert "AAPL" in result_text
            assert "Apple Inc." in result_text
            mock_client.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_multiple_stocks_fundamentals_real_call(self):
        """複数銘柄ファンダメンタルデータ取得のテスト"""
        with patch.object(FinvizClient, "get_multiple_stocks_fundamentals") as mock_client:
            mock_client.return_value = self.sample_stocks_list

            result = await server.call_tool("get_multiple_stocks_fundamentals", {
                "tickers": ["AAPL", "MSFT"]
            })

            assert result is not None
            result_text = str(result[0].text)
            assert "AAPL" in result_text
            assert "MSFT" in result_text
            mock_client.assert_called_once()

    # ===========================================
    # 属性アクセスパターンテスト
    # ===========================================

    def test_stockdata_attribute_access_comprehensive(self):
        """StockDataの属性アクセスパターンの包括的テスト"""
        stock = self.sample_stock_data

        # 基本情報のアクセステスト
        basic_attrs = [
            'ticker', 'company_name', 'sector', 'industry',
            'price', 'price_change', 'price_change_percent'
        ]
        for attr in basic_attrs:
            try:
                value = getattr(stock, attr)
                assert value is not None, f"{attr} should not be None"
            except AttributeError as e:
                pytest.fail(f"Missing attribute: {attr}")

        # パフォーマンス属性のアクセステスト
        performance_attrs = [
            'performance_1w', 'performance_1m', 'performance_3m',
            'performance_6m', 'performance_ytd', 'performance_1y'
        ]
        for attr in performance_attrs:
            try:
                value = getattr(stock, attr)
                assert value is None or isinstance(value, (int, float))
            except AttributeError as e:
                pytest.fail(f"Missing performance attribute: {attr}")

        # 決算関連属性のアクセステスト
        earnings_attrs = [
            'eps_surprise', 'revenue_surprise', 'eps_qoq_growth',
            'sales_qoq_growth', 'earnings_date'
        ]
        for attr in earnings_attrs:
            try:
                value = getattr(stock, attr)
                assert value is None or isinstance(value, (int, float, str))
            except AttributeError as e:
                pytest.fail(f"Missing earnings attribute: {attr}")

    def test_stockdata_formatting_patterns(self):
        """StockDataのフォーマットパターンテスト"""
        stock = self.sample_stock_data

        # server.pyで使われるフォーマットパターンをシミュレート
        try:
            # 基本情報フォーマット
            basic_info = f"Ticker: {stock.ticker}"
            basic_info += f", Company: {stock.company_name}"
            basic_info += f", Sector: {stock.sector}"
            
            # 価格情報フォーマット
            if stock.price:
                price_info = f"Price: ${stock.price:.2f}"
            if stock.price_change:
                price_info += f", Change: {stock.price_change:.2f}%"

            # パフォーマンス情報フォーマット
            if stock.performance_1w:
                perf_info = f"1W Performance: {stock.performance_1w:.2f}%"
            if stock.performance_1m:
                perf_info += f", 1M Performance: {stock.performance_1m:.2f}%"

            # 決算情報フォーマット
            if stock.eps_surprise:
                earnings_info = f"EPS Surprise: {stock.eps_surprise:.2f}%"
            if stock.revenue_surprise:
                earnings_info += f", Revenue Surprise: {stock.revenue_surprise:.2f}%"

            assert len(basic_info) > 0
            
        except Exception as e:
            pytest.fail(f"Formatting pattern failed: {e}")

    # ===========================================
    # エラーハンドリングテスト
    # ===========================================

    @pytest.mark.asyncio
    async def test_invalid_ticker_handling(self):
        """無効なティッカーのエラーハンドリングテスト"""
        with patch.object(FinvizClient, "get_stock_fundamentals") as mock_client:
            mock_client.side_effect = ValueError("Invalid ticker: INVALID")

            result = await server.call_tool("get_stock_fundamentals", {
                "ticker": "INVALID"
            })

            assert result is not None
            result_text = str(result[0].text)
            assert "Error" in result_text or "エラー" in result_text

    @pytest.mark.asyncio
    async def test_invalid_parameters_handling(self):
        """無効なパラメータのエラーハンドリングテスト"""
        # 無効な決算日でテスト
        result = await server.call_tool("earnings_screener", {
            "earnings_date": "invalid_date"
        })

        assert result is not None
        result_text = str(result[0].text)
        assert "Error" in result_text or "Invalid" in result_text

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 