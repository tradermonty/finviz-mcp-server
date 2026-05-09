#!/usr/bin/env python3
"""
全機能の包括的テストランナー
型エラーやカラム名エラーの詳細検出
"""

import asyncio
import os
import sys
import time
import traceback
from unittest.mock import patch

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.finviz_client.screener import FinvizScreener  # noqa: E402
from src.models import StockData  # noqa: E402
from src.server import server  # noqa: E402


class ComprehensiveTestRunner:
    """包括的テストランナー"""

    def __init__(self):
        """初期化"""
        self.results = []
        self.failed_tests = []
        self.total_tests = 0
        self.passed_tests = 0

        # テスト用サンプルデータ
        self.sample_stock_data = self._create_sample_stock_data()
        self.sample_stocks_list = [self.sample_stock_data, self._create_msft_sample()]

    def _create_sample_stock_data(self) -> StockData:
        """完全なStockDataサンプルを作成"""
        return StockData(
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
            week_52_low=124.17,
        )

    def _create_msft_sample(self) -> StockData:
        """MSFTのサンプルデータ"""
        return StockData(
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
            eps=12.05,
            performance_1w=2.5,
            performance_1m=6.8,
            rsi=65.2,
            eps_surprise=0.08,
            revenue_surprise=0.05,
        )

    def log_test_result(self, test_name: str, success: bool, error_message: str = None):
        """テスト結果をログ"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            print(f"✓ {test_name}")
        else:
            self.failed_tests.append((test_name, error_message))
            print(f"✗ {test_name}")
            if error_message:
                print(f"  エラー: {error_message}")

    async def test_all_screeners(self):
        """全スクリーナーのテスト"""
        print("\n=== スクリーナー機能テスト ===")

        # 決算関連スクリーナー
        screener_tests = [
            {
                "name": "earnings_screener",
                "params": {"earnings_date": "this_week"},
                "mock_method": "earnings_screener",
                "expected_content": ["Earnings Screening Results", "AAPL"],
            },
            {
                "name": "volume_surge_screener",
                "params": {"random_string": "test"},
                "mock_method": "volume_surge_screener",
                "expected_content": ["固定フィルタ条件", "出来高急増"],
            },
            {
                "name": "earnings_trading_screener",
                "params": {"random_string": "test"},
                "mock_method": "earnings_trading_screener",
                "expected_content": ["EPS Surprise", "Revenue Surprise"],
            },
        ]

        for test in screener_tests:
            try:
                with patch.object(FinvizScreener, test["mock_method"]) as mock_screener:
                    mock_screener.return_value = self.sample_stocks_list

                    result = await server.call_tool(test["name"], test["params"])

                    if result and len(result) > 0:
                        result_text = str(result[0].text)

                        # 期待するコンテンツが含まれているかチェック
                        content_found = any(
                            content in result_text
                            for content in test["expected_content"]
                        )

                        if content_found:
                            self.log_test_result(
                                f"{test['name']} - コンテンツチェック", True
                            )
                        else:
                            self.log_test_result(
                                f"{test['name']} - コンテンツチェック",
                                False,
                                f"期待するコンテンツが見つかりません: {test['expected_content']}",
                            )

                        # 属性アクセスエラーをチェック
                        self._check_attribute_access_in_result(
                            test["name"], result_text
                        )

                    else:
                        self.log_test_result(
                            f"{test['name']} - 結果取得", False, "結果がNullまたは空"
                        )

            except Exception as e:
                self.log_test_result(
                    f"{test['name']} - 実行",
                    False,
                    f"{str(e)}\n{traceback.format_exc()}",
                )

    def _check_attribute_access_in_result(self, function_name: str, result_text: str):
        """結果テキストから属性アクセスエラーを検出"""
        error_indicators = [
            "AttributeError",
            "KeyError",
            "TypeError",
            "NoneType",
            "object has no attribute",
            "missing attribute",
            "column not found",
            "field not found",
        ]

        for indicator in error_indicators:
            if indicator in result_text:
                self.log_test_result(
                    f"{function_name} - 属性アクセス",
                    False,
                    f"属性アクセスエラー検出: {indicator}",
                )
                return

        self.log_test_result(f"{function_name} - 属性アクセス", True)

    async def run_all_tests(self):
        """全テストの実行"""
        print("=== Finviz MCP Server 包括的テスト開始 ===")
        start_time = time.time()

        # 各テストカテゴリの実行
        await self.test_all_screeners()

        # 結果の集計と表示
        end_time = time.time()
        execution_time = end_time - start_time

        print("\n=== テスト結果サマリー ===")
        print(f"総テスト数: {self.total_tests}")
        print(f"成功: {self.passed_tests}")
        print(f"失敗: {len(self.failed_tests)}")
        print(f"成功率: {(self.passed_tests / self.total_tests * 100):.1f}%")
        print(f"実行時間: {execution_time:.2f}秒")

        if self.failed_tests:
            print("\n=== 失敗したテスト詳細 ===")
            for test_name, error_message in self.failed_tests:
                print(f"\n❌ {test_name}")
                if error_message:
                    print(f"   エラー: {error_message}")

        return len(self.failed_tests) == 0


async def main():
    """メイン実行関数"""
    runner = ComprehensiveTestRunner()
    success = await runner.run_all_tests()

    if success:
        print("\n🎉 全テストが成功しました！")
        return 0
    else:
        print("\n❌ テストに失敗がありました。上記の詳細を確認してください。")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
