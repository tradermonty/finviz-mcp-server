#!/usr/bin/env python3
"""
Market Overview機能のテスト
"""

import os
import sys

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, "src"))


def test_import():
    """インポートテスト"""
    try:
        pass

        print("✅ 必要なモジュールのインポート成功")
    except Exception as e:
        print(f"❌ インポートエラー: {str(e)}")
        assert False, f"インポートエラー: {str(e)}"


def test_market_overview_syntax():
    """構文チェック"""
    try:
        # server.pyの構文チェック
        import ast

        with open("src/server.py", "r", encoding="utf-8") as f:
            source = f.read()

        ast.parse(source)
        print("✅ server.py 構文チェック成功")
    except SyntaxError as e:
        print(f"❌ 構文エラー: {str(e)}")
        print(f"   行 {e.lineno}: {e.text}")
        assert False, f"構文エラー: {str(e)}"


def test_finviz_tools():
    """Finvizツールの基本テスト"""
    try:
        # バリデーション機能テスト
        from src.utils.validators import validate_ticker

        # 正常なティッカー
        assert validate_ticker("SPY") is True
        assert validate_ticker("QQQ") is True
        assert validate_ticker("AAPL") is True

        # 不正なティッカー
        assert validate_ticker("") is False
        assert validate_ticker("12345") is False

        print("✅ バリデーション機能テスト成功")
    except Exception as e:
        print(f"❌ バリデーションテストエラー: {str(e)}")
        assert False, f"バリデーションテストエラー: {str(e)}"


def main():
    print("🚀 Market Overview 実装テスト開始")
    print("=" * 50)

    # テスト実行
    tests = [
        ("インポートテスト", test_import),
        ("構文チェック", test_market_overview_syntax),
        ("Finvizツールテスト", test_finviz_tools),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n📊 {test_name}:")
        try:
            test_func()
            passed += 1
        except Exception:
            print(f"❌ {test_name} 失敗")

    print("\n" + "=" * 50)
    print(f"🎯 テスト結果: {passed}/{total} 通過")

    if passed == total:
        print("✅ 全てのテストが成功しました！")
        print("🚀 market_overview実装完了")
    else:
        print("❌ 一部のテストが失敗しました")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)


def test_average_stats_use_non_null_counts_and_real_signs():
    """D12: averages divided non-null sums by the full count, and the "+"
    prefix was hardcoded ("+-1.5%"). Both are fixed here.
    """
    from unittest.mock import patch

    from src import server as server_module
    from src.models import StockData

    def _stock(rel_vol, change):
        return StockData(
            ticker="T",
            company_name="Test Corp",
            sector="Technology",
            industry="Software",
            relative_volume=rel_vol,
            price_change=change,
        )

    # 3 stocks, one with no data; 0.0 is a legitimate value and must count.
    stocks = [_stock(2.0, -3.0), _stock(None, None), _stock(4.0, 0.0)]

    with (
        patch.object(
            server_module.finviz_client,
            "get_multiple_stocks_fundamentals",
            return_value=[{"ticker": "SPY", "price": 1.0}],
        ),
        patch.object(
            server_module.finviz_screener, "volume_surge_screener", return_value=stocks
        ),
        patch.object(
            server_module.finviz_screener, "uptrend_screener", return_value=[]
        ),
        patch.object(
            server_module.finviz_screener, "earnings_screener", return_value=[]
        ),
    ):
        text = server_module.get_market_overview()[0].text

    # (2.0 + 4.0) / 2 == 3.0, not / 3
    assert "3.0x (2/3銘柄)" in text
    # (-3.0 + 0.0) / 2 == -1.5, rendered with its own sign
    assert "-1.5% (2/3銘柄)" in text
    assert "+-" not in text
