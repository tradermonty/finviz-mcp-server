#!/usr/bin/env python3
"""
Finviz カスタム範囲解析 - クイックスタート

最も簡単な実行方法：
  python quick_range_analyze.py

もしくは：
  cd scripts && python quick_range_analyze.py
"""

import os
import sys
from pathlib import Path

def main():
    print("🎯 Finviz カスタム範囲解析 - クイックスタート")
    print("="*60)
    
    # HTMLファイルの自動検索
    possible_paths = [
        '../docs/finviz_screen_page.html',
        'docs/finviz_screen_page.html',
        'finviz_screen_page.html'
    ]
    
    html_file = None
    for path in possible_paths:
        if os.path.exists(path):
            html_file = path
            print(f"✅ HTMLファイルを発見: {path}")
            break
    
    if not html_file:
        print("❌ finviz_screen_page.html が見つかりません")
        print("以下の場所を確認してください:")
        for path in possible_paths:
            print(f"  - {path}")
        return 1
    
    try:
        # finviz_range_analyzer.pyをインポート
        from finviz_range_analyzer import FinvizRangeAnalyzer
        
        print(f"📊 カスタム範囲解析を開始します...")
        
        # 解析器を初期化して実行
        analyzer = FinvizRangeAnalyzer(html_file)
        success = analyzer.analyze_with_ranges(export_format='both')
        
        if success:
            print("\n🎉 カスタム範囲解析が完了しました！")
            
            # 出力ファイルの確認
            stem = Path(html_file).stem
            output_files = [
                f"finviz_range_analysis_{stem}.md",
                f"finviz_range_analysis_{stem}.json"
            ]
            
            print("\n📁 出力ファイル:")
            for file in output_files:
                if os.path.exists(file):
                    size = os.path.getsize(file) / 1024
                    print(f"  ✅ {file} ({size:.1f} KB)")
                else:
                    print(f"  ❌ {file} (未作成)")
            
            print("\n💡 カスタム範囲URLの例:")
            print("  🔗 sh_price_10to50 → 株価 $10-$50")
            print("  🔗 cap_1to10 → 時価総額 $1B-$10B")
            print("  🔗 fa_pe_10to20 → PER 10-20倍")
            print("  🔗 fa_div_3to7 → 配当利回り 3-7%")
            
            return 0
        else:
            print("\n❌ カスタム範囲解析に失敗しました")
            return 1
            
    except ImportError as e:
        print(f"❌ インポートエラー: {e}")
        print("finviz_range_analyzer.py が同じディレクトリにあることを確認してください")
        return 1
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 