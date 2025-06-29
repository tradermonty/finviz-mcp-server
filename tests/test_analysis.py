import sys
import os
from collections import defaultdict, Counter

# プロジェクトルートをPythonパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def analyze_volume_surge_stocks():
    """出来高急増銘柄の詳細分析"""
    try:
        from src.finviz_client.screener import FinvizScreener
        screener = FinvizScreener()
        
        print("=== 出来高急増銘柄の詳細分析 ===")
        
        # スクリーニング実行
        results = screener.volume_surge_screener()
        print(f"総銘柄数: {len(results)}")
        
        # セクター別分析
        sector_analysis = defaultdict(list)
        industry_analysis = defaultdict(list)
        
        # 価格変動率別分析
        price_change_ranges = {
            "10%以上": [],
            "5-10%": [],
            "2-5%": []
        }
        
        # 時価総額別分析
        market_cap_ranges = {
            "大型 (50B+)": [],
            "中型 (2B-50B)": [],
            "小型 (300M-2B)": []
        }
        
        # 上位銘柄詳細
        top_performers = []
        
        for i, stock in enumerate(results[:20]):  # 上位20銘柄を詳細分析
            # セクター情報
            sector = getattr(stock, 'sector', 'Unknown')
            industry = getattr(stock, 'industry', 'Unknown')
            
            # 基本情報
            ticker = stock.ticker
            price = getattr(stock, 'price', 0)
            price_change = getattr(stock, 'price_change', 0)
            volume = getattr(stock, 'volume', 0)
            market_cap = getattr(stock, 'market_cap', 0)
            
            # データ蓄積
            sector_analysis[sector].append({
                'ticker': ticker,
                'price_change': price_change,
                'volume': volume
            })
            
            industry_analysis[industry].append(ticker)
            
            # 価格変動率分類
            if price_change >= 10:
                price_change_ranges["10%以上"].append(ticker)
            elif price_change >= 5:
                price_change_ranges["5-10%"].append(ticker)
            else:
                price_change_ranges["2-5%"].append(ticker)
            
            # 時価総額分類（概算）
            if market_cap and market_cap > 50000:  # 50B+
                market_cap_ranges["大型 (50B+)"].append(ticker)
            elif market_cap and market_cap > 2000:  # 2B-50B
                market_cap_ranges["中型 (2B-50B)"].append(ticker)
            else:
                market_cap_ranges["小型 (300M-2B)"].append(ticker)
            
            # 上位パフォーマー
            if i < 10:
                top_performers.append({
                    'rank': i + 1,
                    'ticker': ticker,
                    'price': price,
                    'price_change': price_change,
                    'volume': volume,
                    'sector': sector
                })
        
        # 結果出力
        print("\n=== TOP 10 パフォーマー ===")
        for performer in top_performers:
            print(f"{performer['rank']:2d}. {performer['ticker']:6s} | "
                  f"{performer['price_change']:+6.2f}% | "
                  f"${performer['price']:7.2f} | "
                  f"{performer['volume']/1000000:6.1f}M vol | "
                  f"{performer['sector']}")
        
        print("\n=== セクター別分布 ===")
        sector_summary = {}
        for sector, stocks in sector_analysis.items():
            count = len(stocks)
            avg_change = sum(s['price_change'] for s in stocks) / count if count > 0 else 0
            sector_summary[sector] = {'count': count, 'avg_change': avg_change}
            print(f"{sector:25s}: {count:3d}銘柄 (平均変動: {avg_change:+5.2f}%)")
        
        print("\n=== 価格変動率分布 ===")
        for range_name, tickers in price_change_ranges.items():
            print(f"{range_name:10s}: {len(tickers):3d}銘柄 ({len(tickers)/len(results)*100:4.1f}%)")
            if tickers:
                print(f"  代表銘柄: {', '.join(tickers[:5])}")
        
        print("\n=== 時価総額別分布 ===")
        for cap_range, tickers in market_cap_ranges.items():
            print(f"{cap_range:15s}: {len(tickers):3d}銘柄")
        
        # 分析結果を辞書で返す
        return {
            'total_stocks': len(results),
            'top_performers': top_performers,
            'sector_summary': sector_summary,
            'price_change_distribution': {k: len(v) for k, v in price_change_ranges.items()},
            'market_cap_distribution': {k: len(v) for k, v in market_cap_ranges.items()},
            'top_sectors': sorted(sector_summary.items(), key=lambda x: x[1]['count'], reverse=True)[:5]
        }
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    analyze_volume_surge_stocks() 