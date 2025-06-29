#!/usr/bin/env python3
"""
Finviz Elite クイック解析スクリプト

簡単にFinviz Eliteのフィルター解析を実行するためのラッパースクリプト
"""

import sys
import os
from pathlib import Path

# スクリプトのディレクトリをパスに追加
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

try:
    from finviz_elite_analyzer import FinvizEliteAnalyzer
except ImportError as e:
    print(f"❌ インポートエラー: {e}")
    print("必要なパッケージをインストールしてください:")
    print("pip install -r requirements.txt")
    sys.exit(1)

def quick_analyze():
    """クイック解析実行"""
    print("🔍 Finviz Elite フィルター クイック解析")
    print("=" * 50)
    
    # ログイン情報取得
    import getpass
    
    username = input("📧 Elite ユーザー名: ").strip()
    if not username:
        print("❌ ユーザー名が入力されていません")
        return False
    
    password = getpass.getpass("🔐 Elite パスワード: ")
    if not password:
        print("❌ パスワードが入力されていません")
        return False
    
    # 解析実行
    print("\n🚀 解析を開始します...")
    print("📝 ログイン中...")
    
    analyzer = FinvizEliteAnalyzer()
    
    try:
        success = analyzer.run_full_analysis(
            username=username,
            password=password,
            export_format='both'
        )
        
        if success:
            print("\n✅ 解析完了！")
            print("\n📄 生成されたファイル:")
            
            # ファイル存在確認
            md_file = "finviz_elite_filters.md"
            json_file = "finviz_elite_filters.json"
            
            if os.path.exists(md_file):
                file_size = os.path.getsize(md_file) / 1024  # KB
                print(f"  📋 {md_file} ({file_size:.1f} KB)")
            
            if os.path.exists(json_file):
                file_size = os.path.getsize(json_file) / 1024  # KB
                print(f"  📊 {json_file} ({file_size:.1f} KB)")
            
            print("\n🎉 解析が正常に完了しました！")
            return True
        else:
            print("\n❌ 解析に失敗しました")
            print("💡 以下を確認してください:")
            print("  - ログイン情報が正しいか")
            print("  - Elite会員が有効か")
            print("  - インターネット接続が安定しているか")
            return False
            
    except KeyboardInterrupt:
        print("\n⏹️  ユーザーによって中断されました")
        return False
    except Exception as e:
        print(f"\n❌ 予期しないエラー: {e}")
        return False

def main():
    """メイン実行"""
    try:
        success = quick_analyze()
        
        if success:
            # 結果ファイルの簡単な統計を表示
            try:
                import json
                
                with open('finviz_elite_filters.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                print(f"\n📈 統計情報:")
                print(f"  🔢 検出されたフィルター数: {len(data)}")
                
                # カテゴリー別統計
                categories = {}
                for item in data:
                    category = "その他"  # デフォルト
                    # 簡単なカテゴリー判定
                    name = item.get('name', '')
                    if 'Exchange' in name or 'Index' in name or 'Sector' in name:
                        category = "基本情報"
                    elif 'Price' in name or 'Cap' in name:
                        category = "株価・時価総額"
                    elif 'Volume' in name:
                        category = "出来高・取引"
                    elif 'Performance' in name:
                        category = "テクニカル分析"
                    
                    categories[category] = categories.get(category, 0) + 1
                
                for cat, count in categories.items():
                    if count > 0:
                        print(f"  📊 {cat}: {count}個")
                        
            except Exception as e:
                print(f"  📊 統計情報取得エラー: {e}")
        
        print("\n👋 解析完了")
        
    except KeyboardInterrupt:
        print("\n👋 解析を中断しました")
    except Exception as e:
        print(f"❌ 実行エラー: {e}")

if __name__ == "__main__":
    main() 