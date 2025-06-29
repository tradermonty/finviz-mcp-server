#!/usr/bin/env python3
"""
Finviz HTML ファイル解析スクリプト

保存されたFinviz HTMLファイルを解析して、
利用可能な全フィルター項目とその値を詳細に解析するスクリプト。

Usage:
    python finviz_html_analyzer.py [html_file_path]
"""

from bs4 import BeautifulSoup
import json
import re
from dataclasses import dataclass
from typing import List, Dict, Optional
import sys
import os
from pathlib import Path
import argparse
import logging

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class FilterOption:
    """フィルターオプションのデータクラス"""
    value: str
    label: str
    group: Optional[str] = None

@dataclass
class FilterParameter:
    """フィルターパラメーターのデータクラス"""
    name: str
    id: str
    data_filter: str
    options: List[FilterOption]
    selected_value: Optional[str] = None
    category: Optional[str] = None
    data_url: Optional[str] = None
    data_url_selected: Optional[str] = None

class FinvizHTMLAnalyzer:
    """Finviz HTML解析クラス"""
    
    def __init__(self, html_file_path: str):
        self.html_file_path = Path(html_file_path)
        self.filters = []
        
        # 除外するフィルターのリスト（個人設定等）
        self.excluded_filters = {
            'screenerpresetsselect',     # スクリーナープリセット選択
            'screenerpresets',           # スクリーナープリセット
            'fs_screenerpresetsselect',  # フルIDバージョン
            'fs_screenerpresets',        # フルIDバージョン
        }
        
        if not self.html_file_path.exists():
            raise FileNotFoundError(f"HTMLファイルが見つかりません: {html_file_path}")
        
        logger.info(f"除外フィルター: {', '.join(self.excluded_filters)}")
    
    def load_html(self) -> BeautifulSoup:
        """HTMLファイルを読み込み"""
        try:
            with open(self.html_file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            logger.info(f"HTMLファイルを読み込みました: {self.html_file_path}")
            return soup
            
        except UnicodeDecodeError:
            # UTF-8で読み込めない場合、他のエンコーディングを試す
            try:
                with open(self.html_file_path, 'r', encoding='iso-8859-1') as f:
                    html_content = f.read()
                soup = BeautifulSoup(html_content, 'html.parser')
                logger.info(f"HTMLファイル読み込み成功 (iso-8859-1): {self.html_file_path}")
                return soup
            except Exception as e:
                logger.error(f"HTMLファイル読み込みエラー: {e}")
                raise
        except Exception as e:
            logger.error(f"HTMLファイル読み込みエラー: {e}")
            raise
    
    def extract_filter_parameters(self) -> List[FilterParameter]:
        """フィルターパラメーターを抽出"""
        try:
            soup = self.load_html()
            filters = []
            
            # selectタグのフィルター要素を検索（複数のクラスパターンに対応）
            select_patterns = [
                {'class': re.compile(r'screener-combo')},
                {'class': re.compile(r'fv-select')},
                {'class': re.compile(r'screener.*combo')},
                {'id': re.compile(r'^fs_')},  # IDがfs_で始まるもの
            ]
            
            found_selects = set()  # 重複を防ぐ
            
            for pattern in select_patterns:
                selects = soup.find_all('select', pattern)
                for select in selects:
                    select_id = select.get('id', '')
                    if select_id and select_id not in found_selects:
                        found_selects.add(select_id)
                        try:
                            filter_param = self._parse_select_element(select)
                            if filter_param:
                                filters.append(filter_param)
                        except Exception as e:
                            logger.warning(f"selectエレメント解析エラー ({select_id}): {e}")
                            continue
            
            # data-filter属性を持つselect要素も検索
            data_filter_selects = soup.find_all('select', attrs={'data-filter': True})
            for select in data_filter_selects:
                select_id = select.get('id', '')
                if select_id and select_id not in found_selects:
                    found_selects.add(select_id)
                    try:
                        filter_param = self._parse_select_element(select)
                        if filter_param:
                            filters.append(filter_param)
                    except Exception as e:
                        logger.warning(f"data-filter select解析エラー ({select_id}): {e}")
                        continue
            
            logger.info(f"{len(filters)}個のフィルターパラメーターを検出しました")
            
            # フィルターをdata-filter順でソート
            filters.sort(key=lambda x: x.data_filter)
            
            return filters
            
        except Exception as e:
            logger.error(f"フィルターパラメーター抽出エラー: {e}")
            return []
    
    def _parse_select_element(self, select) -> Optional[FilterParameter]:
        """selectエレメントを解析してFilterParameterオブジェクトを作成"""
        try:
            # 基本属性を取得
            select_id = select.get('id', '')
            data_filter = select.get('data-filter', '')
            data_url = select.get('data-url', '')
            data_url_selected = select.get('data-url-selected', '')
            
            if not data_filter and not select_id:
                return None
            
            # data-filterがない場合、IDから推測
            if not data_filter and select_id.startswith('fs_'):
                data_filter = select_id[3:]  # fs_を除去
            
            # 除外フィルターをチェック
            if (select_id.lower() in self.excluded_filters or 
                data_filter.lower() in self.excluded_filters):
                logger.debug(f"フィルターを除外しました: {select_id} (data-filter: {data_filter})")
                return None
            
            # オプションを解析
            options = []
            current_group = None
            
            for element in select.find_all(['option', 'optgroup']):
                if element.name == 'optgroup':
                    current_group = element.get('label', '')
                elif element.name == 'option':
                    value = element.get('value', '')
                    label = element.get_text(strip=True)
                    
                    # 空のラベルをスキップ
                    if not label:
                        continue
                    
                    option = FilterOption(
                        value=value,
                        label=label,
                        group=current_group
                    )
                    options.append(option)
            
            # 選択された値を取得
            selected_option = select.find('option', selected=True)
            if not selected_option:
                # data-selected属性もチェック
                selected_value = select.get('data-selected', '')
            else:
                selected_value = selected_option.get('value', '')
            
            return FilterParameter(
                name=self._get_filter_name_from_id(select_id, data_filter),
                id=select_id,
                data_filter=data_filter,
                options=options,
                selected_value=selected_value,
                data_url=data_url,
                data_url_selected=data_url_selected
            )
            
        except Exception as e:
            logger.warning(f"selectエレメント解析中にエラー: {e}")
            return None
    
    def _get_filter_name_from_id(self, element_id: str, data_filter: str = '') -> str:
        """element IDまたはdata-filterからフィルター名を推定"""
        # ID → 名前のマッピング（拡張版）
        id_to_name = {
            'fs_exch': 'Exchange (取引所)',
            'fs_idx': 'Index (指数)',
            'fs_sec': 'Sector (セクター)',
            'fs_ind': 'Industry (業界)',
            'fs_geo': 'Country (国)',
            'fs_cap': 'Market Cap (時価総額)',
            'fs_sh_price': 'Price (株価)',
            'fs_fa_div': 'Dividend Yield (配当利回り)',
            'fs_fa_epsrev': 'EPS/Revenue Revision (EPS・売上改訂)',
            'fs_sh_short': 'Short Float (ショート比率)',
            'fs_an_recom': 'Analyst Recommendation (アナリスト推奨)',
            'fs_sh_opt': 'Option/Short (オプション/ショート)',
            'fs_earningsdate': 'Earnings Date (決算日)',
            'fs_ipodate': 'IPO Date (IPO日)',
            'fs_sh_avgvol': 'Average Volume (平均出来高)',
            'fs_sh_relvol': 'Relative Volume (相対出来高)',
            'fs_sh_curvol': 'Current Volume (当日出来高)',
            'fs_sh_trades': 'Trades (取引回数)',
            'fs_sh_outstanding': 'Shares Outstanding (発行済株式数)',
            'fs_sh_float': 'Float (浮動株数)',
            'fs_ta_perf2': 'Performance 2 (パフォーマンス 2)',
            'fs_ta_perf': 'Performance (パフォーマンス)',
            'fs_targetprice': 'Target Price (目標株価)',
            'fs_ta_highlow52w': '52W High/Low (52週高値/安値)',
            'fs_ta_sma20': 'SMA20 (20日移動平均)',
            'fs_ta_sma50': 'SMA50 (50日移動平均)',
            'fs_ta_sma200': 'SMA200 (200日移動平均)',
            'fs_ta_change': 'Change (変化)',
            'fs_ta_volume': 'Volume (出来高)',
            'fs_fa_pe': 'P/E Ratio (PER)',
            'fs_fa_peg': 'PEG Ratio (PEG比)',
            'fs_fa_ps': 'P/S Ratio (PSR)',
            'fs_fa_pb': 'P/B Ratio (PBR)',
            'fs_fa_pc': 'P/C Ratio (PCR)',
            'fs_fa_pfcf': 'P/FCF Ratio (P/FCF比)',
            'fs_fa_epsyoy': 'EPS Growth YoY (EPS前年比成長)',
            'fs_fa_epsqoq': 'EPS Growth QoQ (EPS前四半期比成長)',
            'fs_fa_salesyoy': 'Sales Growth YoY (売上前年比成長)',
            'fs_fa_salesqoq': 'Sales Growth QoQ (売上前四半期比成長)',
            'fs_fa_eps5y': 'EPS Growth 5Y (EPS5年成長)',
            'fs_fa_sales5y': 'Sales Growth 5Y (売上5年成長)',
            'fs_fa_roe': 'ROE',
            'fs_fa_roa': 'ROA',
            'fs_fa_roi': 'ROI',
            'fs_fa_curratio': 'Current Ratio (流動比率)',
            'fs_fa_quickratio': 'Quick Ratio (当座比率)',
            'fs_fa_ltdebt': 'LT Debt/Eq (長期負債比率)',
            'fs_fa_debt': 'Debt/Eq (負債比率)',
            'fs_fa_grossmargin': 'Gross Margin (売上総利益率)',
            'fs_fa_opermargin': 'Operating Margin (営業利益率)',
            'fs_fa_profitmargin': 'Profit Margin (純利益率)',
            'fs_fa_payout': 'Payout Ratio (配当性向)',
            'fs_fa_insiderown': 'Insider Own (インサイダー所有)',
            'fs_fa_insidertrans': 'Insider Trans (インサイダー取引)',
            'fs_fa_insthold': 'Inst Hold (機関投資家保有)',
            'fs_fa_insttrans': 'Inst Trans (機関投資家取引)',
        }
        
        # data-filter → 名前のマッピング
        filter_to_name = {
            'exch': 'Exchange (取引所)',
            'idx': 'Index (指数)',
            'sec': 'Sector (セクター)',
            'ind': 'Industry (業界)',
            'geo': 'Country (国)',
            'cap': 'Market Cap (時価総額)',
            'sh_price': 'Price (株価)',
            'fa_div': 'Dividend Yield (配当利回り)',
            'fa_epsrev': 'EPS/Revenue Revision (EPS・売上改訂)',
            'sh_short': 'Short Float (ショート比率)',
            'an_recom': 'Analyst Recommendation (アナリスト推奨)',
            'sh_opt': 'Option/Short (オプション/ショート)',
            'earningsdate': 'Earnings Date (決算日)',
            'ipodate': 'IPO Date (IPO日)',
            'sh_avgvol': 'Average Volume (平均出来高)',
            'sh_relvol': 'Relative Volume (相対出来高)',
            'sh_curvol': 'Current Volume (当日出来高)',
            'sh_trades': 'Trades (取引回数)',
            'sh_outstanding': 'Shares Outstanding (発行済株式数)',
            'sh_float': 'Float (浮動株数)',
            'ta_perf2': 'Performance 2 (パフォーマンス 2)',
            'ta_perf': 'Performance (パフォーマンス)',
            'targetprice': 'Target Price (目標株価)',
        }
        
        # IDから名前を取得
        if element_id in id_to_name:
            return id_to_name[element_id]
        
        # data-filterから名前を取得
        if data_filter in filter_to_name:
            return filter_to_name[data_filter]
        
        # フォールバック
        if element_id:
            return element_id.replace('fs_', '').replace('_', ' ').title()
        elif data_filter:
            return data_filter.replace('_', ' ').title()
        else:
            return 'Unknown Filter'
    
    def categorize_filters(self, filters: List[FilterParameter]) -> Dict[str, List[FilterParameter]]:
        """フィルターをカテゴリー別に分類"""
        categories = {
            '基本情報系パラメーター': [],
            '株価・時価総額系パラメーター': [],
            '配当・財務系パラメーター': [],
            'アナリスト・推奨系パラメーター': [],
            '日付系パラメーター': [],
            '出来高・取引系パラメーター': [],
            '株式発行系パラメーター': [],
            'テクニカル分析系パラメーター': [],
            'その他パラメーター': []
        }
        
        category_keywords = {
            '基本情報系パラメーター': ['exchange', 'index', 'sector', 'industry', 'country', 'exch', 'idx', 'sec', 'ind', 'geo'],
            '株価・時価総額系パラメーター': ['market cap', 'price', 'target price', 'cap', 'sh_price', 'targetprice'],
            '配当・財務系パラメーター': ['dividend', 'eps', 'revenue', 'short', 'pe', 'pb', 'ps', 'roe', 'roa', 'margin', 'debt', 'fa_'],
            'アナリスト・推奨系パラメーター': ['analyst', 'recommendation', 'an_recom'],
            '日付系パラメーター': ['earnings date', 'ipo date', 'earningsdate', 'ipodate'],
            '出来高・取引系パラメーター': ['volume', 'trades', 'sh_avgvol', 'sh_relvol', 'sh_curvol', 'sh_trades'],
            '株式発行系パラメーター': ['shares', 'float', 'outstanding', 'sh_outstanding', 'sh_float'],
            'テクニカル分析系パラメーター': ['performance', 'sma', 'change', 'high', 'low', 'ta_'],
        }
        
        for filter_param in filters:
            assigned = False
            search_text = f"{filter_param.name.lower()} {filter_param.data_filter.lower()}"
            
            for category, keywords in category_keywords.items():
                if any(keyword in search_text for keyword in keywords):
                    categories[category].append(filter_param)
                    assigned = True
                    break
            
            if not assigned:
                categories['その他パラメーター'].append(filter_param)
        
        return categories
    
    def export_to_markdown(self, filters: List[FilterParameter], output_file: str = None):
        """フィルター情報をMarkdown形式でエクスポート"""
        if output_file is None:
            output_file = f"finviz_filters_analysis_{self.html_file_path.stem}.md"
        
        try:
            categorized_filters = self.categorize_filters(filters)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("# Finviz フィルターパラメーター詳細一覧\n\n")
                f.write(f"HTMLファイル: `{self.html_file_path.name}`\n")
                f.write(f"解析日時: {os.path.getctime(self.html_file_path)}\n\n")
                f.write("このドキュメントは、Finvizのスクリーニング機能で使用できる全パラメーターとその取得可能な値を詳細に記載しています。\n\n")
                
                for category, category_filters in categorized_filters.items():
                    if not category_filters:
                        continue
                        
                    f.write(f"## {category}\n\n")
                    
                    for filter_param in category_filters:
                        f.write(f"### {filter_param.name} - `{filter_param.data_filter}`\n")
                        
                        if filter_param.selected_value:
                            f.write(f"**現在選択値**: `{filter_param.selected_value}`\n\n")
                        
                        if filter_param.options:
                            # グループがある場合とない場合で表示を分ける
                            has_groups = any(option.group for option in filter_param.options)
                            
                            if has_groups:
                                f.write("| 値 | 説明 | グループ |\n")
                                f.write("|---|---|---|\n")
                                
                                for option in filter_param.options:
                                    group = option.group or "-"
                                    f.write(f"| `{option.value}` | {option.label} | {group} |\n")
                            else:
                                f.write("| 値 | 説明 |\n")
                                f.write("|---|---|\n")
                                
                                for option in filter_param.options:
                                    f.write(f"| `{option.value}` | {option.label} |\n")
                            
                            f.write("\n")
                        
                        # data-url情報があれば追加
                        if filter_param.data_url:
                            f.write(f"**Data URL**: `{filter_param.data_url}`\n\n")
                        
                        f.write("\n")
                
                # 使用方法セクション
                f.write("## 使用方法\n\n")
                f.write("これらのパラメーターは、Finvizのスクリーニング機能でURLのクエリパラメーターとして使用されます。\n\n")
                f.write("### 例:\n")
                f.write("```\n")
                f.write("https://finviz.com/screener.ashx?v=111&f=cap_large,sec_technology,ta_perf_1w_o5\n")
                f.write("```\n\n")
                f.write("### 複数条件の組み合わせ:\n")
                f.write("- パラメーターはカンマ区切りで複数指定可能\n")
                f.write("- 異なるカテゴリーのパラメーターは AND 条件で結合\n")
                f.write("- 同一カテゴリーの複数値は OR 条件で結合（一部例外あり）\n\n")
            
            logger.info(f"フィルター情報を {output_file} に出力しました")
            
        except Exception as e:
            logger.error(f"Markdown出力エラー: {e}")
    
    def export_to_json(self, filters: List[FilterParameter], output_file: str = None):
        """フィルター情報をJSON形式でエクスポート"""
        if output_file is None:
            output_file = f"finviz_filters_analysis_{self.html_file_path.stem}.json"
        
        try:
            filter_data = {
                'source_file': str(self.html_file_path),
                'total_filters': len(filters),
                'filters': []
            }
            
            for filter_param in filters:
                options_data = []
                for option in filter_param.options:
                    options_data.append({
                        'value': option.value,
                        'label': option.label,
                        'group': option.group
                    })
                
                filter_info = {
                    'name': filter_param.name,
                    'id': filter_param.id,
                    'data_filter': filter_param.data_filter,
                    'selected_value': filter_param.selected_value,
                    'options_count': len(options_data),
                    'options': options_data
                }
                
                # data-url情報があれば追加
                if filter_param.data_url:
                    filter_info['data_url'] = filter_param.data_url
                if filter_param.data_url_selected:
                    filter_info['data_url_selected'] = filter_param.data_url_selected
                
                filter_data['filters'].append(filter_info)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(filter_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"フィルター情報を {output_file} に出力しました")
            
        except Exception as e:
            logger.error(f"JSON出力エラー: {e}")
    
    def print_summary(self, filters: List[FilterParameter]):
        """解析結果のサマリーを表示"""
        print("\n" + "="*60)
        print("📊 Finviz フィルター解析結果サマリー")
        print("="*60)
        
        categorized = self.categorize_filters(filters)
        
        print(f"📄 ソースファイル: {self.html_file_path.name}")
        print(f"🔢 総フィルター数: {len(filters)}")
        print(f"📂 カテゴリー数: {len([c for c, f in categorized.items() if f])}")
        
        print("\n📋 カテゴリー別統計:")
        for category, category_filters in categorized.items():
            if category_filters:
                print(f"  📊 {category}: {len(category_filters)}個")
        
        # Top 5 フィルター（オプション数順）
        top_filters = sorted(filters, key=lambda x: len(x.options), reverse=True)[:5]
        print(f"\n🔝 オプション数上位5フィルター:")
        for i, filter_param in enumerate(top_filters, 1):
            print(f"  {i}. {filter_param.name}: {len(filter_param.options)}個のオプション")
        
        print("\n" + "="*60)
    
    def analyze(self, export_format: str = 'both'):
        """完全な解析を実行"""
        try:
            logger.info("フィルター解析を開始します...")
            
            # フィルター抽出
            filters = self.extract_filter_parameters()
            
            if not filters:
                logger.error("フィルターが検出されませんでした")
                return False
            
            # サマリー表示
            self.print_summary(filters)
            
            # 結果出力
            if export_format in ['markdown', 'both']:
                self.export_to_markdown(filters)
            
            if export_format in ['json', 'both']:
                self.export_to_json(filters)
            
            return True
            
        except Exception as e:
            logger.error(f"解析実行エラー: {e}")
            return False

def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(
        description='Finviz HTMLファイル解析ツール',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python finviz_html_analyzer.py finviz_screen_page.html
  python finviz_html_analyzer.py finviz_screen_page.html --format json
  python finviz_html_analyzer.py finviz_screen_page.html --format markdown
        """
    )
    
    parser.add_argument(
        'html_file',
        nargs='?',
        default='finviz_screen_page.html',
        help='解析するHTMLファイルのパス (デフォルト: finviz_screen_page.html)'
    )
    
    parser.add_argument(
        '--format', '-f',
        choices=['markdown', 'json', 'both'],
        default='both',
        help='出力形式を指定 (デフォルト: both)'
    )
    
    args = parser.parse_args()
    
    print("🔍 Finviz HTML フィルター解析ツール")
    print("="*50)
    
    try:
        # 解析器初期化
        analyzer = FinvizHTMLAnalyzer(args.html_file)
        
        # 解析実行
        success = analyzer.analyze(export_format=args.format)
        
        if success:
            print("\n✅ 解析が完了しました！")
            
            # 出力ファイル確認
            stem = Path(args.html_file).stem
            
            if args.format in ['markdown', 'both']:
                md_file = f"finviz_filters_analysis_{stem}.md"
                if os.path.exists(md_file):
                    size = os.path.getsize(md_file) / 1024
                    print(f"📄 {md_file} ({size:.1f} KB)")
            
            if args.format in ['json', 'both']:
                json_file = f"finviz_filters_analysis_{stem}.json"
                if os.path.exists(json_file):
                    size = os.path.getsize(json_file) / 1024
                    print(f"📊 {json_file} ({size:.1f} KB)")
        else:
            print("\n❌ 解析に失敗しました")
            return 1
            
    except FileNotFoundError as e:
        print(f"❌ ファイルエラー: {e}")
        return 1
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 