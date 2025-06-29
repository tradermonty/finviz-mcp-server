#!/usr/bin/env python3
"""
Basic functionality test for Finviz MCP Server
"""

import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_imports():
    """Test that all modules can be imported successfully"""
    try:
        from src.models import StockData, FINVIZ_FIELD_MAPPING, NewsData, SectorPerformance
        from src.finviz_client.base import FinvizClient
        from src.finviz_client.screener import FinvizScreener
        from src.finviz_client.news import FinvizNewsClient
        from src.finviz_client.sector_analysis import FinvizSectorAnalysisClient
        from src.utils.validators import validate_ticker, validate_market_cap
        from src.utils.formatters import format_large_number
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_validators():
    """Test validation functions"""
    from src.utils.validators import validate_ticker, validate_market_cap, validate_price_range
    
    # Test ticker validation
    assert validate_ticker("AAPL") == True
    assert validate_ticker("MSFT") == True
    assert validate_ticker("invalid") == False  # lowercase
    assert validate_ticker("TOOLONG") == False  # too long
    assert validate_ticker("") == False  # empty
    
    # Test market cap validation
    assert validate_market_cap("large") == True
    assert validate_market_cap("invalid") == False
    
    # Test price range validation
    assert validate_price_range(10, 100) == True
    assert validate_price_range(100, 10) == False  # min > max
    assert validate_price_range(-10, 100) == False  # negative min
    
    print("✓ Validators working correctly")
    return True

def test_formatters():
    """Test formatting functions"""
    from src.utils.formatters import format_large_number
    
    assert format_large_number(1500) == "1.50K"
    assert format_large_number(1500000) == "1.50M"
    assert format_large_number(1500000000) == "1.50B"
    
    print("✓ Formatters working correctly")
    return True

def test_data_models():
    """Test data model creation"""
    from src.models import StockData
    
    stock = StockData(
        ticker="AAPL",
        company_name="Apple Inc.",
        sector="Technology",
        industry="Consumer Electronics",
        price=150.0,
        volume=1000000
    )
    
    assert stock.ticker == "AAPL"
    assert stock.price == 150.0
    
    # Test to_dict conversion
    stock_dict = stock.to_dict()
    assert isinstance(stock_dict, dict)
    assert stock_dict['ticker'] == "AAPL"
    
    print("✓ Data models working correctly")
    return True

def main():
    """Run all basic tests"""
    print("Running basic functionality tests...")
    print("-" * 40)
    
    tests = [
        test_imports,
        test_validators,
        test_formatters,
        test_data_models
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test failed: {e}")
    
    print("-" * 40)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All basic tests passed! The server is ready to use.")
        return True
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)