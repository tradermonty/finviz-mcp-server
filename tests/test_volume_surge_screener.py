import sys
import os

# プロジェクトルートをPythonパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_volume_surge_screener():
    """volume_surge_screenerのテスト実行とデバッグ"""
    try:
        # 直接スクリーナーインスタンスを作成して詳細確認
        from src.finviz_client.screener import FinvizScreener
        screener = FinvizScreener()
        
        # フィルター条件確認
        print("\n=== フィルター条件確認 ===")
        filters = screener._build_volume_surge_filters()
        print(f"フィルター: {filters}")
        
        # Finvizパラメーター変換確認
        print("\n=== Finvizパラメーター変換確認 ===")
        finviz_params = screener._convert_filters_to_finviz(filters)
        print(f"Finvizパラメーター: {finviz_params}")
        
        # 実際のスクリーニング実行
        print("\n=== スクリーニング実行 ===")
        results = screener.volume_surge_screener()
        print(f"結果件数: {len(results)}")
        
        # 結果の詳細表示（最初の5件）
        if results:
            print("\n=== 結果詳細（最初の5件） ===")
            for i, stock in enumerate(results[:5]):
                # StockDataオブジェクトの正しい属性を使用
                company_name = getattr(stock, 'company_name', 'N/A')
                price = getattr(stock, 'price', 'N/A')
                price_change = getattr(stock, 'price_change', 'N/A')
                volume = getattr(stock, 'volume', 'N/A')
                
                print(f"{i+1}. {stock.ticker} - {company_name}")
                print(f"   価格: ${price} | 変動: {price_change}% | 出来高: {volume}")
                print()
        else:
            print("結果が0件です。")
            
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_volume_surge_screener() 