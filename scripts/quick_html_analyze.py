#!/usr/bin/env python3
"""
Finviz HTML クイック解析スクリプト

保存されたFinviz HTMLファイルを簡単に解析するためのラッパースクリプト
"""

import sys
import os
from pathlib import Path

# スクリプトのディレクトリをパスに追加
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

try:
    from finviz_html_analyzer import FinvizHTMLAnalyzer
except ImportError as e:
    print(f"❌ インポートエラー: {e}")
    print("必要なパッケージをインストールしてください:")
    print("pip install beautifulsoup4 lxml")
    sys.exit(1)

def quick_html_analyze(html_file: str = None):
    """HTML解析実行"""
    print("🔍 Finviz HTML フィルター クイック解析")
    print("=" * 50)
    
    # HTMLファイルのパス確認
    if html_file is None:
        # デフォルトの検索順序
        default_files = [
            'finviz_screen_page.html',
            '../docs/finviz_screen_page.html',
            'finviz_elite_page.html',
            '../finviz_screen_page.html'
        ]
        
        found_file = None
        for file_path in default_files:
            if os.path.exists(file_path):
                found_file = file_path
                break
        
        if found_file:
            html_file = found_file
        else:
            print("❌ HTMLファイルが見つかりません。")
            print("\n以下のいずれかのファイルを用意してください:")
            for file_path in default_files:
                print(f"  - {file_path}")
            
            # ユーザー入力を促す
            custom_path = input("\nまたは、HTMLファイルのパスを入力してください: ").strip()
            if custom_path and os.path.exists(custom_path):
                html_file = custom_path
            else:
                print("❌ 指定されたHTMLファイルが見つかりません")
                return False
    
    print(f"📄 HTMLファイル: {html_file}")
    
    try:
        # 解析器初期化
        analyzer = FinvizHTMLAnalyzer(html_file)
        
        print("🔄 解析中...")
        
        # 解析実行
        success = analyzer.analyze(export_format='both')
        
        if success:
            print("\n✅ 解析が完了しました！")
            
            # 出力ファイル確認
            stem = Path(html_file).stem
            
            md_file = f"finviz_filters_analysis_{stem}.md"
            json_file = f"finviz_filters_analysis_{stem}.json"
            
            if os.path.exists(md_file):
                size = os.path.getsize(md_file) / 1024
                print(f"📄 {md_file} ({size:.1f} KB)")
            
            if os.path.exists(json_file):
                size = os.path.getsize(json_file) / 1024
                print(f"📊 {json_file} ({size:.1f} KB)")
            
            print("\n💡 使用方法:")
            print(f"  - Markdown: {md_file} を開いてパラメーター一覧を確認")
            print(f"  - JSON: {json_file} を開いて構造化データを確認")
            
            return True
        else:
            print("\n❌ 解析に失敗しました")
            return False
            
    except FileNotFoundError as e:
        print(f"❌ ファイルエラー: {e}")
        return False
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return False

def main():
    """メイン実行関数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Finviz HTML クイック解析ツール',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python quick_html_analyze.py
  python quick_html_analyze.py finviz_screen_page.html
  python quick_html_analyze.py ../docs/finviz_screen_page.html
        """
    )
    
    parser.add_argument(
        'html_file',
        nargs='?',
        help='解析するHTMLファイルのパス (省略時は自動検索)'
    )
    
    args = parser.parse_args()
    
    success = quick_html_analyze(args.html_file)
    
    if not success:
        print("\n🔧 トラブルシューティング:")
        print("1. HTMLファイルが正しいパスにあることを確認")
        print("2. 必要なパッケージがインストールされていることを確認:")
        print("   pip install beautifulsoup4 lxml")
        print("3. HTMLファイルがFinvizスクリーナーページであることを確認")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 