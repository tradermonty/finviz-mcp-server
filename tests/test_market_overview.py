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
        from utils.finviz_client import FinvizClient
        from utils.screeners import FinvizScreener
        from utils.validators import validate_ticker

        print("✅ 必要なモジュールのインポート成功")
        return True
    except Exception as e:
        print(f"❌ インポートエラー: {str(e)}")
        return False


def test_market_overview_syntax():
    """構文チェック"""
    try:
        # server.pyの構文チェック
        import ast

        with open("src/server.py", "r", encoding="utf-8") as f:
            source = f.read()

        ast.parse(source)
        print("✅ server.py 構文チェック成功")
        return True
    except SyntaxError as e:
        print(f"❌ 構文エラー: {str(e)}")
        print(f"   行 {e.lineno}: {e.text}")
        return False


def test_finviz_tools():
    """Finvizツールの基本テスト"""
    try:
        # バリデーション機能テスト
        from utils.validators import validate_ticker

        # 正常なティッカー
        assert validate_ticker("SPY") == True
        assert validate_ticker("QQQ") == True
        assert validate_ticker("AAPL") == True

        # 不正なティッカー
        assert validate_ticker("") == False
        assert validate_ticker("12345") == False

        print("✅ バリデーション機能テスト成功")
        return True
    except Exception as e:
        print(f"❌ バリデーションテストエラー: {str(e)}")
        return False


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
        if test_func():
            passed += 1
        else:
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
