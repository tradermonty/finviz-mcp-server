#!/usr/bin/env python3
"""
Debug script for Finviz screener issues
Finvizスクリーナーの問題をデバッグするためのスクリプト
"""

import sys
import os
import logging

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Enable debug logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

from src.finviz_client.screener import FinvizScreener
from src.finviz_client.base import FinvizClient

def test_direct_url_construction():
    """直接URLを構築してテスト"""
    print("=== URL構築テスト ===")
    
    screener = FinvizScreener()
    
    # 来週決算予定のフィルタを構築
    filters = {
        'earnings_date': 'next_week',
        'market_cap': 'smallover',
        'price_min': 10,
        'avg_volume_min': 500,
        'sectors': ['Technology', 'Industrials', 'Healthcare', 
                   'Communication Services', 'Consumer Cyclical', 
                   'Financial Services', 'Consumer Defensive', 'Basic Materials']
    }
    
    # Finvizパラメータに変換
    finviz_params = screener._convert_filters_to_finviz(filters)
    print(f"構築されたパラメータ: {finviz_params}")
    
    # URLを構築
    from urllib.parse import urlencode
    base_url = "https://finviz.com/screener.ashx"
    full_url = f"{base_url}?{urlencode(finviz_params)}"
    print(f"構築されたURL: {full_url}")
    
    # 実際のFinvizサイトのURL（参考）
    expected_url = "https://elite.finviz.com/screener.ashx?v=311&p=w&f=cap_smallover,earningsdate_nextweek,sec_technology|industrials|healthcare|communicationservices|consumercyclical|financial|consumerdefensive|basicmaterials,sh_avgvol_o500,sh_price_o10&ft=4&o=ticker&ar=10"
    print(f"期待されるURL: {expected_url}")

def test_basic_request():
    """基本的なHTTPリクエストテスト"""
    print("\n=== 基本HTTPリクエストテスト ===")
    
    client = FinvizClient()
    
    try:
        # 基本的なスクリーナーページにアクセス
        response = client._make_request("https://finviz.com/screener.ashx", {'v': '111'})
        print(f"レスポンスステータス: {response.status_code}")
        print(f"レスポンスサイズ: {len(response.text)} 文字")
        
        # HTMLの一部をチェック
        if "screener" in response.text.lower():
            print("✓ スクリーナーページが正常に読み込まれました")
        else:
            print("✗ スクリーナーページの読み込みに問題があります")
            
    except Exception as e:
        print(f"✗ HTTPリクエストエラー: {e}")

def test_csv_export():
    """CSVエクスポートのテスト"""
    print("\n=== CSVエクスポートテスト ===")
    
    client = FinvizClient()
    
    try:
        # 最もシンプルなフィルタでCSVエクスポートを試行
        params = {'v': '111'}
        response = client._make_request("https://finviz.com/export.ashx", params)
        print(f"CSVレスポンスステータス: {response.status_code}")
        print(f"CSVレスポンスサイズ: {len(response.text)} 文字")
        print(f"CSVレスポンス最初の200文字: {response.text[:200]}")
        
        if "ticker" in response.text.lower() or "symbol" in response.text.lower():
            print("✓ CSVデータが正常に取得されました")
        else:
            print("✗ CSVデータの取得に問題があります")
            
    except Exception as e:
        print(f"✗ CSVエクスポートエラー: {e}")

def test_html_parsing():
    """HTMLパースのテスト"""
    print("\n=== HTMLパースのテスト ===")
    
    client = FinvizClient()
    
    try:
        # 基本的なスクリーナーのHTMLを取得してパース
        params = {'v': '111', 'f': 'cap_smallover'}
        response = client._make_request("https://finviz.com/screener.ashx", params)
        
        # HTMLをパース
        parsed_data = client._parse_finviz_table(response.text)
        print(f"パースされた行数: {len(parsed_data)}")
        
        if parsed_data:
            print("✓ HTMLパースが成功しました")
            print(f"最初の行のキー: {list(parsed_data[0].keys())}")
        else:
            print("✗ HTMLパースで0行しか取得できませんでした")
            
    except Exception as e:
        print(f"✗ HTMLパースエラー: {e}")

def main():
    """メイン実行関数"""
    print("🔍 Finviz スクリーナー デバッグテスト開始")
    print("=" * 60)
    
    test_direct_url_construction()
    test_basic_request()
    test_csv_export()
    test_html_parsing()
    
    print("\n" + "=" * 60)
    print("📊 デバッグテスト完了")

if __name__ == "__main__":
    main() 