import logging
from src.server import server, volume_surge_screener

# ログレベルを設定（必要に応じて）
logging.basicConfig(level=logging.INFO)

def test_volume_surge_screener():
    """volume_surge_screenerの固定条件テスト"""
    print("Testing volume_surge_screener with fixed conditions...")
    
    try:
        # volume_surge_screenerを直接実行
        # パラメーターなし（固定条件）
        results = volume_surge_screener('test')
        
        # 結果を出力
        print("\nResults received:")
        for result in results:
            print(f"Type: {result.type}")
            text_lines = result.text.split('\n')
            print(f"Total lines: {len(text_lines)}")
            print(f"Total length: {len(result.text)} characters")
            
            # 最初の20行を表示
            print("\nFirst 20 lines:")
            for i, line in enumerate(text_lines[:20]):
                print(f"{i+1:2d}: {line}")
            
            if len(text_lines) > 20:
                print(f"... (showing first 20 of {len(text_lines)} lines)")
        
        print("\nTest completed successfully!")
        
    except Exception as e:
        print(f"Error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_volume_surge_screener() 