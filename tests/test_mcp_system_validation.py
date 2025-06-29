#!/usr/bin/env python3
"""
MCP System Validation Test Suite
リリース時実行推奨：実際のMCP呼び出しによるシステムレベル機能テスト
データ妥当性確認を含む包括的テスト
"""

import pytest
import asyncio
import sys
import os
import re
import time
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# MCP tools import（実際のMCP呼び出し用）
from src.server import (
    earnings_screener,
    earnings_trading_screener,
    earnings_premarket_screener,
    earnings_afterhours_screener,
    volume_surge_screener,
    uptrend_screener,
    upcoming_earnings_screener,
    get_stock_fundamentals,
    get_multiple_stocks_fundamentals,
    get_market_overview,
    dividend_growth_screener,
    earnings_winners_screener
)

@dataclass
class TestResult:
    """テスト結果を管理するデータクラス"""
    test_name: str
    success: bool
    execution_time: float
    result_data: Any
    error_message: Optional[str] = None
    data_quality_score: float = 0.0
    stocks_found: int = 0

class MCPSystemValidationTest:
    """MCP システム検証テストクラス"""

    def __init__(self):
        self.test_results: List[TestResult] = []
        self.total_tests = 0
        self.passed_tests = 0
        
    def log_test_result(self, result: TestResult):
        """テスト結果をログに記録"""
        self.test_results.append(result)
        self.total_tests += 1
        
        if result.success:
            self.passed_tests += 1
            print(f"✅ {result.test_name} - 実行時間: {result.execution_time:.2f}s, 銘柄数: {result.stocks_found}")
        else:
            print(f"❌ {result.test_name} - エラー: {result.error_message}")

    def validate_stock_data_quality(self, result_text: str, test_name: str) -> tuple[float, int]:
        """株式データの品質を検証"""
        quality_score = 0.0
        stocks_found = 0
        
        # ティッカーシンボルの検出
        ticker_pattern = r'\b[A-Z]{1,5}\b'
        tickers = re.findall(ticker_pattern, result_text)
        stocks_found = len(set(tickers))
        
        # 基本的な品質チェック
        quality_checks = [
            ('価格データ', r'\$\d+\.\d+'),
            ('パーセンテージ', r'[+-]?\d+\.\d+%'),
            ('出来高', r'[\d,]+(?:K|M|B)?'),
            ('セクター情報', r'(Technology|Healthcare|Financial|Energy|Consumer|Industrial|Real Estate|Utilities|Communication|Basic Materials)'),
            ('結果フォーマット', r'(Results|銘柄|found|検出)'),
        ]
        
        for check_name, pattern in quality_checks:
            if re.search(pattern, result_text):
                quality_score += 20.0  # 各チェック20点
        
        # エラーパターンの検出（減点）
        error_patterns = [
            r'Error|Exception|Failed',
            r'AttributeError|TypeError|KeyError',
            r'NoneType|object has no attribute',
            r'connection error|timeout'
        ]
        
        for error_pattern in error_patterns:
            if re.search(error_pattern, result_text, re.IGNORECASE):
                quality_score -= 30.0
        
        return max(0.0, min(100.0, quality_score)), stocks_found

    def test_earnings_related_functions(self):
        """決算関連機能の包括テスト"""
        print("\n🔍 決算関連機能テスト開始...")
        
        # 1. 決算発表予定銘柄スクリーニング
        start_time = time.time()
        try:
            result = earnings_screener(earnings_date="today_after")
            execution_time = time.time() - start_time
            result_text = str(result[0].text) if result and len(result) > 0 else str(result)
            quality_score, stocks_found = self.validate_stock_data_quality(result_text, "earnings_screener")
            
            self.log_test_result(TestResult(
                test_name="決算発表予定銘柄スクリーニング",
                success=True,
                execution_time=execution_time,
                result_data=result,
                data_quality_score=quality_score,
                stocks_found=stocks_found
            ))
        except Exception as e:
            self.log_test_result(TestResult(
                test_name="決算発表予定銘柄スクリーニング",
                success=False,
                execution_time=time.time() - start_time,
                result_data=None,
                error_message=str(e)
            ))

        # 2. 決算トレード対象銘柄
        start_time = time.time()
        try:
            result = earnings_trading_screener()
            execution_time = time.time() - start_time
            result_text = str(result[0].text) if result and len(result) > 0 else str(result)
            quality_score, stocks_found = self.validate_stock_data_quality(result_text, "earnings_trading_screener")
            
            # 期待値：0件でも正常（時間外のため）
            success = True  # エラーが発生しなければ成功
            
            self.log_test_result(TestResult(
                test_name="決算トレード対象銘柄",
                success=success,
                execution_time=execution_time,
                result_data=result,
                data_quality_score=quality_score,
                stocks_found=stocks_found
            ))
        except Exception as e:
            self.log_test_result(TestResult(
                test_name="決算トレード対象銘柄",
                success=False,
                execution_time=time.time() - start_time,
                result_data=None,
                error_message=str(e)
            ))

    def test_basic_screening_functions(self):
        """基本スクリーニング機能テスト"""
        print("\n🔍 基本スクリーニング機能テスト開始...")
        
        # 1. 出来高急増銘柄
        start_time = time.time()
        try:
            result = volume_surge_screener()
            execution_time = time.time() - start_time
            result_text = str(result[0].text) if result and len(result) > 0 else str(result)
            quality_score, stocks_found = self.validate_stock_data_quality(result_text, "volume_surge_screener")
            
            # 50銘柄以上検出で高品質
            if stocks_found >= 50:
                quality_score += 20.0
            
            self.log_test_result(TestResult(
                test_name="出来高急増銘柄スクリーニング",
                success=True,
                execution_time=execution_time,
                result_data=result,
                data_quality_score=quality_score,
                stocks_found=stocks_found
            ))
        except Exception as e:
            self.log_test_result(TestResult(
                test_name="出来高急増銘柄スクリーニング",
                success=False,
                execution_time=time.time() - start_time,
                result_data=None,
                error_message=str(e)
            ))

        # 2. 上昇トレンド銘柄
        start_time = time.time()
        try:
            result = uptrend_screener()
            execution_time = time.time() - start_time
            result_text = str(result[0].text) if result and len(result) > 0 else str(result)
            quality_score, stocks_found = self.validate_stock_data_quality(result_text, "uptrend_screener")
            
            # 200銘柄以上検出で高品質
            if stocks_found >= 200:
                quality_score += 20.0
            
            self.log_test_result(TestResult(
                test_name="上昇トレンド銘柄スクリーニング",
                success=True,
                execution_time=execution_time,
                result_data=result,
                data_quality_score=quality_score,
                stocks_found=stocks_found
            ))
        except Exception as e:
            self.log_test_result(TestResult(
                test_name="上昇トレンド銘柄スクリーニング",
                success=False,
                execution_time=time.time() - start_time,
                result_data=None,
                error_message=str(e)
            ))

    def test_stock_data_functions(self):
        """個別銘柄データ取得機能テスト"""
        print("\n🔍 個別銘柄データ取得機能テスト開始...")
        
        # 1. 単一銘柄ファンダメンタルデータ
        start_time = time.time()
        try:
            result = get_stock_fundamentals(
                ticker="AAPL",
                data_fields=["price", "change", "volume", "pe_ratio", "eps"]
            )
            execution_time = time.time() - start_time
            result_text = str(result[0].text) if result and len(result) > 0 else str(result)
            
            # AAPL特有のデータ検証
            quality_score = 0.0
            if "AAPL" in result_text: quality_score += 25.0
            if re.search(r'\$\d+\.\d+', result_text): quality_score += 25.0  # 価格
            if re.search(r'[\d,]+', result_text): quality_score += 25.0  # 出来高
            if "Fundamental Data" in result_text: quality_score += 25.0
            
            self.log_test_result(TestResult(
                test_name="単一銘柄ファンダメンタルデータ（AAPL）",
                success=True,
                execution_time=execution_time,
                result_data=result,
                data_quality_score=quality_score,
                stocks_found=1
            ))
        except Exception as e:
            self.log_test_result(TestResult(
                test_name="単一銘柄ファンダメンタルデータ（AAPL）",
                success=False,
                execution_time=time.time() - start_time,
                result_data=None,
                error_message=str(e)
            ))

        # 2. 複数銘柄ファンダメンタルデータ
        start_time = time.time()
        try:
            result = get_multiple_stocks_fundamentals(
                tickers=["MSFT", "GOOGL", "NVDA"],
                data_fields=["price", "change", "market_cap", "pe_ratio"]
            )
            execution_time = time.time() - start_time
            result_text = str(result[0].text) if result and len(result) > 0 else str(result)
            
            # 複数銘柄データ検証
            quality_score = 0.0
            target_tickers = ["MSFT", "GOOGL", "NVDA"]
            found_tickers = sum(1 for ticker in target_tickers if ticker in result_text)
            quality_score += (found_tickers / len(target_tickers)) * 50.0
            
            if "Fundamental Data" in result_text: quality_score += 25.0
            if re.search(r'\$\d+\.\d+', result_text): quality_score += 25.0
            
            self.log_test_result(TestResult(
                test_name="複数銘柄ファンダメンタルデータ（MSFT,GOOGL,NVDA）",
                success=True,
                execution_time=execution_time,
                result_data=result,
                data_quality_score=quality_score,
                stocks_found=found_tickers
            ))
        except Exception as e:
            self.log_test_result(TestResult(
                test_name="複数銘柄ファンダメンタルデータ（MSFT,GOOGL,NVDA）",
                success=False,
                execution_time=time.time() - start_time,
                result_data=None,
                error_message=str(e)
            ))

        # 3. 市場概要データ
        start_time = time.time()
        try:
            result = get_market_overview()
            execution_time = time.time() - start_time
            result_text = str(result[0].text) if result and len(result) > 0 else str(result)
            
            # 市場概要データ検証
            quality_score = 0.0
            market_indicators = ["SPY", "QQQ", "DIA", "IWM", "TLT", "GLD"]
            found_indicators = sum(1 for indicator in market_indicators if indicator in result_text)
            quality_score += (found_indicators / len(market_indicators)) * 50.0
            
            if "市場概要" in result_text or "Market Overview" in result_text: quality_score += 25.0
            if re.search(r'\$\d+\.\d+', result_text): quality_score += 25.0
            
            self.log_test_result(TestResult(
                test_name="市場概要データ",
                success=True,
                execution_time=execution_time,
                result_data=result,
                data_quality_score=quality_score,
                stocks_found=found_indicators
            ))
        except Exception as e:
            self.log_test_result(TestResult(
                test_name="市場概要データ",
                success=False,
                execution_time=time.time() - start_time,
                result_data=None,
                error_message=str(e)
            ))

    def test_parameter_type_validation(self):
        """パラメータ型修正テスト（min_volume等）"""
        print("\n🔍 パラメータ型修正テスト開始...")
        
        # 1. Finviz文字列形式テスト - "o100"
        start_time = time.time()
        try:
            result = earnings_screener(
                earnings_date="within_2_weeks",
                min_volume="o100"
            )
            execution_time = time.time() - start_time
            result_text = str(result[0].text) if result and len(result) > 0 else str(result)
            quality_score, stocks_found = self.validate_stock_data_quality(result_text, "earnings_screener_o100")
            
            self.log_test_result(TestResult(
                test_name="min_volume型修正テスト（o100形式）",
                success=True,
                execution_time=execution_time,
                result_data=result,
                data_quality_score=quality_score,
                stocks_found=stocks_found
            ))
        except Exception as e:
            self.log_test_result(TestResult(
                test_name="min_volume型修正テスト（o100形式）",
                success=False,
                execution_time=time.time() - start_time,
                result_data=None,
                error_message=str(e)
            ))

    def test_advanced_screening_functions(self):
        """高度なスクリーニング機能テスト"""
        print("\n🔍 高度なスクリーニング機能テスト開始...")
        
        # 1. 配当成長銘柄
        start_time = time.time()
        try:
            result = dividend_growth_screener(min_dividend_yield=2)
            execution_time = time.time() - start_time
            result_text = str(result[0].text) if result and len(result) > 0 else str(result)
            quality_score, stocks_found = self.validate_stock_data_quality(result_text, "dividend_growth_screener")
            
            # 配当関連データの検証
            if "Dividend" in result_text or "配当" in result_text:
                quality_score += 20.0
            
            self.log_test_result(TestResult(
                test_name="配当成長銘柄スクリーニング",
                success=True,
                execution_time=execution_time,
                result_data=result,
                data_quality_score=quality_score,
                stocks_found=stocks_found
            ))
        except Exception as e:
            self.log_test_result(TestResult(
                test_name="配当成長銘柄スクリーニング",
                success=False,
                execution_time=time.time() - start_time,
                result_data=None,
                error_message=str(e)
            ))

    def generate_test_report(self) -> str:
        """包括的なテストレポートを生成"""
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        report = f"""
==============================================================================
🧪 MCP SYSTEM VALIDATION TEST REPORT
==============================================================================
📊 テスト実行サマリー:
   総テスト数: {self.total_tests}
   成功: {self.passed_tests}
   失敗: {self.total_tests - self.passed_tests}
   成功率: {success_rate:.1f}%

==============================================================================
📈 機能別テスト結果:
"""
        
        # カテゴリ別結果
        categories = {
            "決算関連": ["決算発表予定", "決算トレード"],
            "基本スクリーニング": ["出来高急増", "上昇トレンド"],
            "データ取得": ["単一銘柄", "複数銘柄", "市場概要"],
            "パラメータ型": ["o100形式"],
            "高度機能": ["配当成長"]
        }
        
        for category, keywords in categories.items():
            category_tests = [r for r in self.test_results if any(kw in r.test_name for kw in keywords)]
            if category_tests:
                category_success = sum(1 for r in category_tests if r.success)
                category_total = len(category_tests)
                category_rate = (category_success / category_total * 100) if category_total > 0 else 0
                
                report += f"\n🔹 {category}: {category_success}/{category_total} ({category_rate:.1f}%)\n"
                
                for result in category_tests:
                    status = "✅" if result.success else "❌"
                    report += f"   {status} {result.test_name}\n"
                    if result.success:
                        report += f"      実行時間: {result.execution_time:.2f}s, "
                        report += f"品質スコア: {result.data_quality_score:.1f}, "
                        report += f"銘柄数: {result.stocks_found}\n"
                    else:
                        report += f"      エラー: {result.error_message}\n"

        # 品質分析
        successful_tests = [r for r in self.test_results if r.success]
        if successful_tests:
            avg_quality = sum(r.data_quality_score for r in successful_tests) / len(successful_tests)
            total_stocks = sum(r.stocks_found for r in successful_tests)
            avg_execution_time = sum(r.execution_time for r in successful_tests) / len(successful_tests)
            
            report += f"""
==============================================================================
📊 品質分析:
   平均品質スコア: {avg_quality:.1f}/100
   総検出銘柄数: {total_stocks}
   平均実行時間: {avg_execution_time:.2f}秒

==============================================================================
🎯 リリース判定:
"""
            
            if success_rate >= 90 and avg_quality >= 70:
                report += "   🟢 PASS - リリース可能\n"
            elif success_rate >= 80 and avg_quality >= 60:
                report += "   🟡 CAUTION - 要注意点確認\n" 
            else:
                report += "   🔴 FAIL - 修正必要\n"

        report += "\n=============================================================================="
        
        return report

    def run_all_tests(self):
        """全テストを実行"""
        print("🚀 MCP System Validation Test Suite 開始")
        print("=" * 80)
        
        # 各テストカテゴリを順次実行
        self.test_earnings_related_functions()
        self.test_basic_screening_functions()
        self.test_stock_data_functions()
        self.test_parameter_type_validation()
        self.test_advanced_screening_functions()
        
        # レポート生成・表示
        report = self.generate_test_report()
        print(report)
        
        return self.passed_tests == self.total_tests

# メイン実行関数
def main():
    """メインテスト実行"""
    validator = MCPSystemValidationTest()
    success = validator.run_all_tests()
    
    if success:
        print("\n🎉 全テスト成功! MCP System は本格運用可能です。")
        return True
    else:
        print("\n⚠️  一部テストが失敗しました。上記レポートを確認してください。")
        return False

if __name__ == "__main__":
    result = main()
    sys.exit(0 if result else 1) 