#!/usr/bin/env python3
"""
Finviz Elite フィルター解析スクリプト

Finviz Elite版のスクリーナーにログインして、
利用可能な全フィルター項目とその値を詳細に解析するスクリプト。

Requirements:
- requests
- beautifulsoup4
- selenium (動的コンテンツ用)
- pandas (結果整理用)

Usage:
    python finviz_elite_analyzer.py
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from dataclasses import dataclass
from typing import List, Dict, Optional
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
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

class FinvizEliteAnalyzer:
    """Finviz Elite フィルター解析クラス"""
    
    def __init__(self):
        self.base_url = "https://elite.finviz.com"
        self.screener_url = f"{self.base_url}/screener.ashx"
        self.login_url = f"{self.base_url}/login.ashx"
        self.session = requests.Session()
        self.driver = None
        self.filters = []
        
        # 除外するフィルターのリスト（個人設定等）
        self.excluded_filters = {
            'screenerpresetsselect',     # スクリーナープリセット選択
            'screenerpresets',           # スクリーナープリセット
            'fs_screenerpresetsselect',  # フルIDバージョン
            'fs_screenerpresets',        # フルIDバージョン
        }
        
        # ユーザーエージェント設定
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        logger.info(f"除外フィルター: {', '.join(self.excluded_filters)}")
    
    def setup_selenium_driver(self, headless: bool = True):
        """Seleniumドライバーをセットアップ"""
        try:
            chrome_options = Options()
            if headless:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # ChromeDriverの自動ダウンロード（webdriver-managerを使用する場合）
            # service = Service(ChromeDriverManager().install())
            
            # 手動でChromeDriverのパスを指定する場合
            service = Service()  # システムPATHのchromedriver使用
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("Seleniumドライバーをセットアップしました")
            return True
            
        except Exception as e:
            logger.error(f"Seleniumドライバーのセットアップに失敗: {e}")
            return False
    
    def login_with_selenium(self, username: str, password: str) -> bool:
        """SeleniumでFinviz Eliteにログイン"""
        try:
            if not self.driver:
                if not self.setup_selenium_driver():
                    return False
            
            logger.info("Finviz Eliteにログイン中...")
            self.driver.get(self.login_url)
            
            # ログインフォーム要素を待機
            wait = WebDriverWait(self.driver, 10)
            
            # ユーザー名とパスワードを入力
            username_field = wait.until(EC.presence_of_element_located((By.NAME, "email")))
            password_field = self.driver.find_element(By.NAME, "password")
            
            username_field.clear()
            username_field.send_keys(username)
            password_field.clear()
            password_field.send_keys(password)
            
            # ログインボタンをクリック
            login_button = self.driver.find_element(By.XPATH, "//input[@type='submit' and @value='Login']")
            login_button.click()
            
            # ログイン成功を確認（URLの変化または特定要素の存在を確認）
            time.sleep(3)
            
            if "screener.ashx" in self.driver.current_url or self.driver.current_url == f"{self.base_url}/":
                logger.info("ログインに成功しました")
                return True
            else:
                logger.error("ログインに失敗しました")
                return False
                
        except Exception as e:
            logger.error(f"ログインエラー: {e}")
            return False
    
    def navigate_to_screener(self):
        """スクリーナーページに移動"""
        try:
            self.driver.get(self.screener_url)
            time.sleep(2)
            logger.info("スクリーナーページに移動しました")
            return True
        except Exception as e:
            logger.error(f"スクリーナーページ移動エラー: {e}")
            return False
    
    def extract_filter_parameters(self) -> List[FilterParameter]:
        """フィルターパラメーターを抽出"""
        try:
            # ページのHTMLを取得
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            filters = []
            
            # selectタグのフィルター要素を検索
            select_elements = soup.find_all('select', class_=re.compile(r'screener-combo|fv-select'))
            
            for select in select_elements:
                try:
                    filter_param = self._parse_select_element(select)
                    if filter_param:
                        filters.append(filter_param)
                except Exception as e:
                    logger.warning(f"selectエレメント解析エラー: {e}")
                    continue
            
            logger.info(f"{len(filters)}個のフィルターパラメーターを検出しました")
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
            
            if not data_filter:
                return None
            
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
                    
                    option = FilterOption(
                        value=value,
                        label=label,
                        group=current_group
                    )
                    options.append(option)
            
            # 選択された値を取得
            selected_option = select.find('option', selected=True)
            selected_value = selected_option.get('value', '') if selected_option else None
            
            return FilterParameter(
                name=self._get_filter_name_from_id(select_id),
                id=select_id,
                data_filter=data_filter,
                options=options,
                selected_value=selected_value
            )
            
        except Exception as e:
            logger.warning(f"selectエレメント解析中にエラー: {e}")
            return None
    
    def _get_filter_name_from_id(self, element_id: str) -> str:
        """element IDからフィルター名を推定"""
        # ID → 名前のマッピング
        id_to_name = {
            'fs_exch': 'Exchange',
            'fs_idx': 'Index',
            'fs_sec': 'Sector',
            'fs_ind': 'Industry',
            'fs_geo': 'Country',
            'fs_cap': 'Market Cap',
            'fs_sh_price': 'Price',
            'fs_fa_div': 'Dividend Yield',
            'fs_fa_epsrev': 'EPS/Revenue Revision',
            'fs_sh_short': 'Short Float',
            'fs_an_recom': 'Analyst Recommendation',
            'fs_earningsdate': 'Earnings Date',
            'fs_ipodate': 'IPO Date',
            'fs_sh_avgvol': 'Average Volume',
            'fs_sh_relvol': 'Relative Volume',
            'fs_sh_curvol': 'Current Volume',
            'fs_sh_outstanding': 'Shares Outstanding',
            'fs_sh_float': 'Float',
            'fs_ta_perf2': 'Performance 2',
            'fs_targetprice': 'Target Price',
            # 他のマッピングを追加
        }
        
        return id_to_name.get(element_id, element_id)
    
    def categorize_filters(self, filters: List[FilterParameter]) -> Dict[str, List[FilterParameter]]:
        """フィルターをカテゴリー別に分類"""
        categories = {
            '基本情報': [],
            '株価・時価総額': [],
            '配当・財務': [],
            'アナリスト・推奨': [],
            '日付': [],
            '出来高・取引': [],
            '株式発行': [],
            'テクニカル分析': [],
            'その他': []
        }
        
        category_mapping = {
            'Exchange': '基本情報',
            'Index': '基本情報',
            'Sector': '基本情報',
            'Industry': '基本情報',
            'Country': '基本情報',
            'Market Cap': '株価・時価総額',
            'Price': '株価・時価総額',
            'Target Price': '株価・時価総額',
            'Dividend Yield': '配当・財務',
            'EPS/Revenue Revision': '配当・財務',
            'Short Float': '配当・財務',
            'Analyst Recommendation': 'アナリスト・推奨',
            'Earnings Date': '日付',
            'IPO Date': '日付',
            'Average Volume': '出来高・取引',
            'Relative Volume': '出来高・取引',
            'Current Volume': '出来高・取引',
            'Shares Outstanding': '株式発行',
            'Float': '株式発行',
            'Performance 2': 'テクニカル分析',
        }
        
        for filter_param in filters:
            category = category_mapping.get(filter_param.name, 'その他')
            categories[category].append(filter_param)
        
        return categories
    
    def export_to_markdown(self, filters: List[FilterParameter], output_file: str = 'finviz_elite_filters.md'):
        """フィルター情報をMarkdown形式でエクスポート"""
        try:
            categorized_filters = self.categorize_filters(filters)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("# Finviz Elite フィルターパラメーター詳細一覧\n\n")
                f.write("Elite会員向けの詳細なフィルターパラメーター一覧です。\n\n")
                
                for category, category_filters in categorized_filters.items():
                    if not category_filters:
                        continue
                        
                    f.write(f"## {category}\n\n")
                    
                    for filter_param in category_filters:
                        f.write(f"### {filter_param.name} - `{filter_param.data_filter}`\n\n")
                        
                        if filter_param.options:
                            f.write("| 値 | 説明 | グループ |\n")
                            f.write("|---|---|---|\n")
                            
                            for option in filter_param.options:
                                group = option.group or "-"
                                f.write(f"| `{option.value}` | {option.label} | {group} |\n")
                            
                            f.write("\n")
                        
                        f.write("\n")
            
            logger.info(f"フィルター情報を {output_file} に出力しました")
            
        except Exception as e:
            logger.error(f"Markdown出力エラー: {e}")
    
    def export_to_json(self, filters: List[FilterParameter], output_file: str = 'finviz_elite_filters.json'):
        """フィルター情報をJSON形式でエクスポート"""
        try:
            filter_data = []
            
            for filter_param in filters:
                options_data = []
                for option in filter_param.options:
                    options_data.append({
                        'value': option.value,
                        'label': option.label,
                        'group': option.group
                    })
                
                filter_data.append({
                    'name': filter_param.name,
                    'id': filter_param.id,
                    'data_filter': filter_param.data_filter,
                    'selected_value': filter_param.selected_value,
                    'options': options_data
                })
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(filter_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"フィルター情報を {output_file} に出力しました")
            
        except Exception as e:
            logger.error(f"JSON出力エラー: {e}")
    
    def analyze_specific_filter(self, data_filter: str) -> Optional[FilterParameter]:
        """特定のフィルターを詳細解析"""
        try:
            filters = self.extract_filter_parameters()
            
            for filter_param in filters:
                if filter_param.data_filter == data_filter:
                    logger.info(f"フィルター '{data_filter}' の詳細:")
                    logger.info(f"  名前: {filter_param.name}")
                    logger.info(f"  ID: {filter_param.id}")
                    logger.info(f"  選択値: {filter_param.selected_value}")
                    logger.info(f"  オプション数: {len(filter_param.options)}")
                    
                    return filter_param
            
            logger.warning(f"フィルター '{data_filter}' が見つかりませんでした")
            return None
            
        except Exception as e:
            logger.error(f"特定フィルター解析エラー: {e}")
            return None
    
    def run_full_analysis(self, username: str, password: str, export_format: str = 'both'):
        """完全なフィルター解析を実行"""
        try:
            # Seleniumセットアップ
            if not self.setup_selenium_driver():
                return False
            
            # ログイン
            if not self.login_with_selenium(username, password):
                return False
            
            # スクリーナーページに移動
            if not self.navigate_to_screener():
                return False
            
            # フィルター解析
            filters = self.extract_filter_parameters()
            
            if not filters:
                logger.error("フィルターが検出されませんでした")
                return False
            
            # 結果出力
            if export_format in ['markdown', 'both']:
                self.export_to_markdown(filters)
            
            if export_format in ['json', 'both']:
                self.export_to_json(filters)
            
            # 統計情報表示
            categorized = self.categorize_filters(filters)
            logger.info("=== 解析結果統計 ===")
            for category, category_filters in categorized.items():
                if category_filters:
                    logger.info(f"{category}: {len(category_filters)}個のフィルター")
            
            return True
            
        except Exception as e:
            logger.error(f"完全解析実行エラー: {e}")
            return False
        
        finally:
            if self.driver:
                self.driver.quit()

def main():
    """メイン実行関数"""
    import getpass
    
    print("=== Finviz Elite フィルター解析ツール ===")
    print()
    
    # ログイン情報入力
    username = input("Finviz Elite ユーザー名: ")
    password = getpass.getpass("Finviz Elite パスワード: ")
    
    # 解析実行
    analyzer = FinvizEliteAnalyzer()
    
    print("\nフィルター解析を開始します...")
    success = analyzer.run_full_analysis(username, password, export_format='both')
    
    if success:
        print("\n✅ 解析が完了しました！")
        print("📄 finviz_elite_filters.md - Markdown形式の詳細レポート")
        print("📊 finviz_elite_filters.json - JSON形式の構造化データ")
    else:
        print("\n❌ 解析に失敗しました。ログ情報を確認してください。")

if __name__ == "__main__":
    main() 