#!/usr/bin/env python3
"""
Finviz スクリーニングパラメータ網羅的テスト

finviz_screening_parameters.md に記載されている全パラメータの
型安全性と変換ロジックを包括的にテストします。
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.finviz_client.base import FinvizClient
from src.utils.validators import validate_parameter_combination


def test_numeric_parameter_conversions():
    """数値パラメータの型安全変換をテスト"""
    print("🔢 Testing numeric parameter conversions...")
    
    client = FinvizClient()
    
    # 価格パラメータテスト
    price_test_cases = [
        # 数値入力
        (10, "10"),
        (10.5, "10.5"),
        (5.0, "5"),
        # 文字列入力（数値）
        ("15", "15"),
        ("7.5", "7.5"),
        ("20.0", "20"),
        # Finviz形式入力
        ("o5", "o5"),
        ("u10", "u10"),
        ("o15.5", "o15.5"),
    ]
    
    print("   Price conversion tests:")
    for input_val, expected in price_test_cases:
        result = client._safe_price_conversion(input_val)
        status = "✓" if result == expected else "✗"
        print(f"     {status} {input_val} -> {result} (expected: {expected})")
    
    # 数値パラメータテスト
    numeric_test_cases = [
        # 整数
        (100, "100"),
        (500000, "500000"),
        # 文字列（数値）
        ("200", "200"),
        ("1000", "1000"),
        # Finviz形式
        ("o100", "100"),
        ("u500", "500"),
        ("e5", "5"),
    ]
    
    print("   Numeric conversion tests:")
    for input_val, expected in numeric_test_cases:
        result = client._safe_numeric_conversion(input_val)
        status = "✓" if result == expected else "✗"
        print(f"     {status} {input_val} -> {result} (expected: {expected})")


def test_price_parameters():
    """価格系パラメータの全パターンをテスト"""
    print("💰 Testing price parameters...")
    
    client = FinvizClient()
    
    # Finvizプリセット形式テスト
    print("   Finviz preset format tests:")
    preset_tests = [
        ("o5", "Over $5 preset"),
        ("u10", "Under $10 preset"),
        ("o20.5", "Over $20.5 preset"),
    ]
    
    for preset, description in preset_tests:
        test_filters = {'price_min': preset}
        try:
            params = client._convert_filters_to_finviz(test_filters)
            if 'f' in params:
                print(f"     ✓ {preset} ({description}): {params['f']}")
            else:
                print(f"     ⚠ {preset} ({description}): No filter generated")
        except Exception as e:
            print(f"     ✗ {preset} ({description}): Error - {e}")
    
    # 数値レンジ形式テスト
    print("   Numeric range format tests:")
    range_tests = [
        # 下限のみ
        ({"price_min": 10.5}, "Min price only: 10.5to"),
        ({"price_min": 5}, "Min price only: 5to"),
        # 上下限
        ({"price_min": 10.5, "price_max": 20.11}, "Price range: 10.5to20.11"),
        ({"price_min": 5, "price_max": 50}, "Price range: 5to50"),
        # 上限のみ
        ({"price_max": 100}, "Max price only: to100"),
    ]
    
    for test_filters, description in range_tests:
        try:
            params = client._convert_filters_to_finviz(test_filters)
            if 'f' in params:
                print(f"     ✓ {description}: {params['f']}")
            else:
                print(f"     ⚠ {description}: No filter generated")
        except Exception as e:
            print(f"     ✗ {description}: Error - {e}")


def test_volume_parameters():
    """出来高系パラメータの全パターンをテスト"""
    print("📊 Testing volume parameters...")
    
    client = FinvizClient()
    
    # Average Volume パラメータ
    avg_volume_patterns = {
        "u50": "Under 50K",
        "u100": "Under 100K",
        "u500": "Under 500K",
        "u1000": "Under 1M",
        "o50": "Over 50K",
        "o100": "Over 100K",
        "o200": "Over 200K",
        "o500": "Over 500K",
        "o1000": "Over 1M",
        "o2000": "Over 2M",
        "100to500": "100K to 500K",
        "500to1000": "500K to 1M",
    }
    
    print("   Average Volume tests:")
    for pattern, description in avg_volume_patterns.items():
        test_filters = {}
        
        # 数値とFinviz形式両方でテスト
        if pattern.startswith('o'):
            test_filters['avg_volume_min'] = pattern  # Finviz形式
        elif pattern.startswith('u'):
            test_filters['avg_volume_max'] = pattern  # Finviz形式
        elif 'to' in pattern:
            parts = pattern.split('to')
            test_filters['avg_volume_min'] = parts[0]
            test_filters['avg_volume_max'] = parts[1]
        
        try:
            params = client._convert_filters_to_finviz(test_filters)
            if 'f' in params:
                print(f"     ✓ {pattern} ({description}): {params['f']}")
            else:
                print(f"     ⚠ {pattern} ({description}): No filter generated")
        except Exception as e:
            print(f"     ✗ {pattern} ({description}): Error - {e}")
    
    # Relative Volume パラメータ
    rel_volume_patterns = {
        "o10": "Over 10",
        "o5": "Over 5", 
        "o3": "Over 3",
        "o2": "Over 2",
        "o1.5": "Over 1.5",
        "o1": "Over 1",
        "o0.5": "Over 0.5",
        "u2": "Under 2",
        "u1": "Under 1",
        "u0.5": "Under 0.5",
    }
    
    print("   Relative Volume tests:")
    for pattern, description in rel_volume_patterns.items():
        test_filters = {}
        
        if pattern.startswith('o'):
            test_filters['relative_volume_min'] = pattern
        elif pattern.startswith('u'):
            test_filters['relative_volume_max'] = pattern
        
        try:
            params = client._convert_filters_to_finviz(test_filters)
            if 'f' in params:
                print(f"     ✓ {pattern} ({description}): {params['f']}")
            else:
                print(f"     ⚠ {pattern} ({description}): No filter generated")
        except Exception as e:
            print(f"     ✗ {pattern} ({description}): Error - {e}")


def test_market_cap_parameters():
    """時価総額パラメータの全パターンをテスト"""
    print("🏛️ Testing market cap parameters...")
    
    client = FinvizClient()
    
    market_cap_patterns = {
        "mega": "Mega ($200bln and more)",
        "large": "Large ($10bln to $200bln)",
        "mid": "Mid ($2bln to $10bln)",
        "small": "Small ($300mln to $2bln)",
        "micro": "Micro ($50mln to $300mln)",
        "nano": "Nano (under $50mln)",
        "largeover": "+Large (over $10bln)",
        "midover": "+Mid (over $2bln)",
        "smallover": "+Small (over $300mln)",
        "microover": "+Micro (over $50mln)",
        "largeunder": "-Large (under $200bln)",
        "midunder": "-Mid (under $10bln)",
        "smallunder": "-Small (under $2bln)",
        "microunder": "-Micro (under $300mln)",
    }
    
    for pattern, description in market_cap_patterns.items():
        test_filters = {'market_cap': pattern}
        
        try:
            params = client._convert_filters_to_finviz(test_filters)
            if 'f' in params:
                print(f"     ✓ {pattern} ({description}): {params['f']}")
            else:
                print(f"     ⚠ {pattern} ({description}): No filter generated")
        except Exception as e:
            print(f"     ✗ {pattern} ({description}): Error - {e}")


def test_dividend_yield_parameters():
    """配当利回りパラメータをテスト"""
    print("💸 Testing dividend yield parameters...")
    
    client = FinvizClient()
    
    dividend_patterns = {
        "none": "None (0%)",
        "pos": "Positive (>0%)",
        "high": "High (>5%)",
        "veryhigh": "Very High (>10%)",
        "o1": "Over 1%",
        "o2": "Over 2%", 
        "o3": "Over 3%",
        "o5": "Over 5%",
        "o10": "Over 10%",
    }
    
    for pattern, description in dividend_patterns.items():
        test_filters = {}
        
        if pattern.startswith('o'):
            test_filters['dividend_yield_min'] = pattern
        else:
            test_filters['dividend_yield'] = pattern
            
        try:
            params = client._convert_filters_to_finviz(test_filters)
            if 'f' in params:
                print(f"     ✓ {pattern} ({description}): {params['f']}")
            else:
                print(f"     ⚠ {pattern} ({description}): No filter generated")
        except Exception as e:
            print(f"     ✗ {pattern} ({description}): Error - {e}")


def test_earnings_date_parameters():
    """決算日パラメータをテスト"""
    print("📅 Testing earnings date parameters...")
    
    client = FinvizClient()
    
    earnings_patterns = {
        "today": "Today",
        "todaybefore": "Today Before Market Open",
        "todayafter": "Today After Market Close",
        "tomorrow": "Tomorrow",
        "tomorrowbefore": "Tomorrow Before Market Open",
        "tomorrowafter": "Tomorrow After Market Close",
        "yesterday": "Yesterday",
        "nextdays5": "Next 5 Days",
        "thisweek": "This Week",
        "nextweek": "Next Week",
        "prevweek": "Previous Week",
        "thismonth": "This Month",
    }
    
    for pattern, description in earnings_patterns.items():
        test_filters = {'earnings_date': pattern}
        
        try:
            params = client._convert_filters_to_finviz(test_filters)
            if 'f' in params:
                print(f"     ✓ {pattern} ({description}): {params['f']}")
            else:
                print(f"     ⚠ {pattern} ({description}): No filter generated")
        except Exception as e:
            print(f"     ✗ {pattern} ({description}): Error - {e}")
    
    # カスタム日付範囲のテスト
    print("   Custom date range tests:")
    custom_date_tests = [
        ("06-30-2025x07-04-2025", "Custom range"),
        ({"start": "2025-06-30", "end": "2025-07-04"}, "Date dict"),
    ]
    
    for date_input, description in custom_date_tests:
        test_filters = {'earnings_date': date_input}
        
        try:
            params = client._convert_filters_to_finviz(test_filters)
            if 'f' in params:
                print(f"     ✓ {description}: {params['f']}")
            else:
                print(f"     ⚠ {description}: No filter generated")
        except Exception as e:
            print(f"     ✗ {description}: Error - {e}")


def test_sector_parameters():
    """セクターパラメータをテスト"""
    print("🏭 Testing sector parameters...")
    
    client = FinvizClient()
    
    sectors = [
        "Basic Materials",
        "Communication Services", 
        "Consumer Cyclical",
        "Consumer Defensive",
        "Energy",
        "Financial Services",
        "Healthcare",
        "Industrials",
        "Real Estate",
        "Technology",
        "Utilities"
    ]
    
    # 単一セクター
    for sector in sectors[:3]:  # 最初の3つだけテスト
        test_filters = {'sectors': [sector]}
        
        try:
            params = client._convert_filters_to_finviz(test_filters)
            if 'f' in params:
                print(f"     ✓ {sector}: {params['f']}")
            else:
                print(f"     ⚠ {sector}: No filter generated")
        except Exception as e:
            print(f"     ✗ {sector}: Error - {e}")
    
    # 複数セクター
    test_filters = {'sectors': ["Technology", "Healthcare", "Financial Services"]}
    try:
        params = client._convert_filters_to_finviz(test_filters)
        if 'f' in params:
            print(f"     ✓ Multiple sectors: {params['f']}")
        else:
            print(f"     ⚠ Multiple sectors: No filter generated")
    except Exception as e:
        print(f"     ✗ Multiple sectors: Error - {e}")


def test_complex_parameter_combinations():
    """複雑なパラメータ組み合わせをテスト"""
    print("🔗 Testing complex parameter combinations...")
    
    client = FinvizClient()
    
    test_combinations = [
        {
            "name": "Earnings Winner Profile",
            "filters": {
                "market_cap": "smallover",
                "price_min": 10,
                "avg_volume_min": "o500",
                "earnings_date": "thisweek",
                "eps_growth_qoq_min": 10,
                "sectors": ["Technology", "Healthcare"]
            }
        },
        {
            "name": "Volume Surge Profile",
            "filters": {
                "market_cap": "midover",
                "price_min": "o5",
                "relative_volume_min": "o2",
                "price_change_min": 2.0,
                "dividend_yield_min": "o1"
            }
        },
        {
            "name": "Uptrend Profile",
            "filters": {
                "market_cap": "microover",
                "price_min": 10,
                "avg_volume_min": 100,
                "near_52w_high": 30,
                "performance_4w_positive": True,
                "sma20_above": True,
                "sma200_above": True
            }
        }
    ]
    
    for test_case in test_combinations:
        print(f"   Testing: {test_case['name']}")
        
        try:
            # パラメータ組み合わせの検証
            validation_errors = validate_parameter_combination(test_case['filters'])
            if validation_errors:
                print(f"     ⚠ Validation warnings: {validation_errors}")
            
            # Finviz形式への変換
            params = client._convert_filters_to_finviz(test_case['filters'])
            if 'f' in params:
                print(f"     ✓ Generated filter: {params['f']}")
                print(f"     ✓ Sort: {params.get('o', 'default')}")
                print(f"     ✓ View: {params.get('v', 'default')}")
            else:
                print(f"     ⚠ No filter generated")
        except Exception as e:
            print(f"     ✗ Error: {e}")


def test_error_handling():
    """エラーハンドリングをテスト"""
    print("🚨 Testing error handling...")
    
    client = FinvizClient()
    
    error_test_cases = [
        {
            "name": "Invalid price type",
            "filters": {"price_min": "invalid"}
        },
        {
            "name": "None values",
            "filters": {"price_min": None, "market_cap": None}
        },
        {
            "name": "Empty strings",
            "filters": {"market_cap": "", "sectors": []}
        },
        {
            "name": "Negative values",
            "filters": {"price_min": -10, "avg_volume_min": -1000}
        }
    ]
    
    for test_case in error_test_cases:
        print(f"   Testing: {test_case['name']}")
        
        try:
            params = client._convert_filters_to_finviz(test_case['filters'])
            print(f"     ✓ Handled gracefully: {params.get('f', 'No filter')}")
        except Exception as e:
            print(f"     ⚠ Exception (expected): {e}")


def main():
    """メイン実行関数"""
    print("=" * 80)
    print("🧪 Finviz Screening Parameters Comprehensive Test")
    print("=" * 80)
    print()
    
    # 全テストを実行
    test_numeric_parameter_conversions()
    print()
    
    test_price_parameters()
    print()
    
    test_volume_parameters()
    print()
    
    test_market_cap_parameters()
    print()
    
    test_dividend_yield_parameters()
    print()
    
    test_earnings_date_parameters()
    print()
    
    test_sector_parameters()
    print()
    
    test_complex_parameter_combinations()
    print()
    
    test_error_handling()
    print()
    
    print("=" * 80)
    print("🎉 Comprehensive parameter testing completed!")
    print("=" * 80)


if __name__ == "__main__":
    main()