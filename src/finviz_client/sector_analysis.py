import logging
from typing import List, Optional, Dict, Any
from bs4 import BeautifulSoup

from .base import FinvizClient
from ..models import SectorPerformance

logger = logging.getLogger(__name__)

class FinvizSectorAnalysisClient(FinvizClient):
    """Finvizセクター・業界分析専用クライアント"""
    
    GROUPS_URL = f"{FinvizClient.BASE_URL}/groups.ashx"
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
    
    def get_sector_performance(self, timeframe: str = "1d", 
                             sectors: Optional[List[str]] = None) -> List[SectorPerformance]:
        """
        セクター別パフォーマンス分析
        
        Args:
            timeframe: 分析期間 (1d, 1w, 1m, 3m, 6m, 1y)
            sectors: 対象セクター（Noneの場合は全セクター）
            
        Returns:
            SectorPerformance オブジェクトのリスト
        """
        try:
            params = {
                'g': 'sector',
                'v': self._get_timeframe_code(timeframe)
            }
            
            response = self._make_request(self.GROUPS_URL, params)
            sector_data = self._parse_sector_performance(response.text)
            
            # セクターフィルタリング
            if sectors:
                sector_data = [s for s in sector_data if s.sector in sectors]
            
            logger.info(f"Retrieved performance data for {len(sector_data)} sectors")
            return sector_data
            
        except Exception as e:
            logger.error(f"Error retrieving sector performance: {e}")
            return []
    
    def get_industry_performance(self, timeframe: str = "1d", 
                               industries: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        業界別パフォーマンス分析
        
        Args:
            timeframe: 分析期間 (1d, 1w, 1m, 3m, 6m, 1y)
            industries: 対象業界（Noneの場合は全業界）
            
        Returns:
            業界パフォーマンスデータのリスト
        """
        try:
            params = {
                'g': 'industry',
                'v': self._get_timeframe_code(timeframe)
            }
            
            response = self._make_request(self.GROUPS_URL, params)
            industry_data = self._parse_industry_performance(response.text)
            
            # 業界フィルタリング
            if industries:
                industry_data = [i for i in industry_data if i.get('industry') in industries]
            
            logger.info(f"Retrieved performance data for {len(industry_data)} industries")
            return industry_data
            
        except Exception as e:
            logger.error(f"Error retrieving industry performance: {e}")
            return []
    
    def get_country_performance(self, timeframe: str = "1d", 
                              countries: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        国別市場パフォーマンス分析
        
        Args:
            timeframe: 分析期間 (1d, 1w, 1m, 3m, 6m, 1y)
            countries: 対象国（Noneの場合は全国）
            
        Returns:
            国別パフォーマンスデータのリスト
        """
        try:
            params = {
                'g': 'country',
                'v': self._get_timeframe_code(timeframe)
            }
            
            response = self._make_request(self.GROUPS_URL, params)
            country_data = self._parse_country_performance(response.text)
            
            # 国フィルタリング
            if countries:
                country_data = [c for c in country_data if c.get('country') in countries]
            
            logger.info(f"Retrieved performance data for {len(country_data)} countries")
            return country_data
            
        except Exception as e:
            logger.error(f"Error retrieving country performance: {e}")
            return []
    
    def get_market_overview(self) -> Dict[str, Any]:
        """
        市場全体の概要を取得
        
        Returns:
            市場概要データ
        """
        try:
            # メインページから市場指標を取得
            response = self._make_request(self.BASE_URL)
            overview = self._parse_market_overview(response.text)
            
            logger.info("Retrieved market overview data")
            return overview
            
        except Exception as e:
            logger.error(f"Error retrieving market overview: {e}")
            return {}
    
    def _get_timeframe_code(self, timeframe: str) -> str:
        """
        時間枠をFinvizのコードに変換
        
        Args:
            timeframe: 時間枠
            
        Returns:
            Finvizコード
        """
        mapping = {
            '1d': '110',    # 1 day
            '1w': '120',    # 1 week  
            '1m': '130',    # 1 month
            '3m': '160',    # 3 months
            '6m': '170',    # 6 months
            '1y': '180'     # 1 year
        }
        return mapping.get(timeframe, '110')
    
    def _parse_sector_performance(self, html_content: str) -> List[SectorPerformance]:
        """
        セクターパフォーマンステーブルを解析
        
        Args:
            html_content: HTMLコンテンツ
            
        Returns:
            SectorPerformance オブジェクトのリスト
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        sectors = []
        
        # パフォーマンステーブルを検索
        table = soup.find('table', {'class': 'groups-table'})
        if not table:
            logger.warning("Sector performance table not found")
            return []
        
        # ヘッダー行を取得
        header_row = table.find('tr')
        if not header_row:
            return []
        
        headers = [th.get_text(strip=True) for th in header_row.find_all('th')]
        
        # データ行を処理
        for row in table.find_all('tr')[1:]:  # ヘッダー行をスキップ
            cells = row.find_all('td')
            if len(cells) >= len(headers):
                try:
                    sector_name = cells[0].get_text(strip=True)
                    
                    # パフォーマンスデータの抽出
                    perf_1d = self._parse_percentage(cells[1].get_text(strip=True)) if len(cells) > 1 else 0.0
                    perf_1w = self._parse_percentage(cells[2].get_text(strip=True)) if len(cells) > 2 else 0.0
                    perf_1m = self._parse_percentage(cells[3].get_text(strip=True)) if len(cells) > 3 else 0.0
                    perf_3m = self._parse_percentage(cells[4].get_text(strip=True)) if len(cells) > 4 else 0.0
                    perf_6m = self._parse_percentage(cells[5].get_text(strip=True)) if len(cells) > 5 else 0.0
                    perf_1y = self._parse_percentage(cells[6].get_text(strip=True)) if len(cells) > 6 else 0.0
                    
                    # 株式数の抽出
                    stock_count = self._parse_number(cells[7].get_text(strip=True)) if len(cells) > 7 else 0
                    
                    sector_perf = SectorPerformance(
                        sector=sector_name,
                        performance_1d=perf_1d,
                        performance_1w=perf_1w,
                        performance_1m=perf_1m,
                        performance_3m=perf_3m,
                        performance_6m=perf_6m,
                        performance_1y=perf_1y,
                        stock_count=stock_count
                    )
                    sectors.append(sector_perf)
                    
                except Exception as e:
                    logger.warning(f"Failed to parse sector row: {e}")
                    continue
        
        return sectors
    
    def _parse_industry_performance(self, html_content: str) -> List[Dict[str, Any]]:
        """
        業界パフォーマンステーブルを解析
        
        Args:
            html_content: HTMLコンテンツ
            
        Returns:
            業界パフォーマンスデータのリスト
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        industries = []
        
        # パフォーマンステーブルを検索
        table = soup.find('table', {'class': 'groups-table'})
        if not table:
            logger.warning("Industry performance table not found")
            return []
        
        # データ行を処理
        for row in table.find_all('tr')[1:]:  # ヘッダー行をスキップ
            cells = row.find_all('td')
            if len(cells) >= 3:
                try:
                    industry_data = {
                        'industry': cells[0].get_text(strip=True),
                        'performance_1d': self._parse_percentage(cells[1].get_text(strip=True)),
                        'performance_1w': self._parse_percentage(cells[2].get_text(strip=True)) if len(cells) > 2 else 0.0,
                        'performance_1m': self._parse_percentage(cells[3].get_text(strip=True)) if len(cells) > 3 else 0.0,
                        'stock_count': self._parse_number(cells[4].get_text(strip=True)) if len(cells) > 4 else 0
                    }
                    industries.append(industry_data)
                    
                except Exception as e:
                    logger.warning(f"Failed to parse industry row: {e}")
                    continue
        
        return industries
    
    def _parse_country_performance(self, html_content: str) -> List[Dict[str, Any]]:
        """
        国別パフォーマンステーブルを解析
        
        Args:
            html_content: HTMLコンテンツ
            
        Returns:
            国別パフォーマンスデータのリスト
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        countries = []
        
        # パフォーマンステーブルを検索
        table = soup.find('table', {'class': 'groups-table'})
        if not table:
            logger.warning("Country performance table not found")
            return []
        
        # データ行を処理
        for row in table.find_all('tr')[1:]:  # ヘッダー行をスキップ
            cells = row.find_all('td')
            if len(cells) >= 3:
                try:
                    country_data = {
                        'country': cells[0].get_text(strip=True),
                        'performance_1d': self._parse_percentage(cells[1].get_text(strip=True)),
                        'performance_1w': self._parse_percentage(cells[2].get_text(strip=True)) if len(cells) > 2 else 0.0,
                        'performance_1m': self._parse_percentage(cells[3].get_text(strip=True)) if len(cells) > 3 else 0.0,
                        'stock_count': self._parse_number(cells[4].get_text(strip=True)) if len(cells) > 4 else 0
                    }
                    countries.append(country_data)
                    
                except Exception as e:
                    logger.warning(f"Failed to parse country row: {e}")
                    continue
        
        return countries
    
    def _parse_market_overview(self, html_content: str) -> Dict[str, Any]:
        """
        市場概要を解析
        
        Args:
            html_content: HTMLコンテンツ
            
        Returns:
            市場概要データ
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        overview = {}
        
        try:
            # 主要指数の検索
            index_section = soup.find('div', {'class': 'market-overview'})
            if index_section:
                # S&P 500, NASDAQ, Dow Jones等の情報を抽出
                for index_item in index_section.find_all('div', {'class': 'index-item'}):
                    name_elem = index_item.find('span', {'class': 'index-name'})
                    value_elem = index_item.find('span', {'class': 'index-value'})
                    change_elem = index_item.find('span', {'class': 'index-change'})
                    
                    if name_elem and value_elem:
                        index_name = name_elem.get_text(strip=True)
                        overview[index_name] = {
                            'value': value_elem.get_text(strip=True),
                            'change': change_elem.get_text(strip=True) if change_elem else "N/A"
                        }
            
            # 市場サマリー
            overview['market_status'] = 'Open'  # デフォルト値
            overview['timestamp'] = 'Live'
            
        except Exception as e:
            logger.warning(f"Failed to parse market overview: {e}")
        
        return overview
    
    def _parse_percentage(self, text: str) -> float:
        """
        パーセンテージ文字列を数値に変換
        
        Args:
            text: パーセンテージ文字列
            
        Returns:
            数値
        """
        try:
            # "%"記号を削除して数値に変換
            clean_text = text.replace('%', '').replace('+', '').strip()
            if clean_text == '-' or clean_text == 'N/A':
                return 0.0
            return float(clean_text)
        except ValueError:
            return 0.0
    
    def _parse_number(self, text: str) -> int:
        """
        数値文字列を整数に変換
        
        Args:
            text: 数値文字列
            
        Returns:
            整数
        """
        try:
            clean_text = text.replace(',', '').strip()
            if clean_text == '-' or clean_text == 'N/A':
                return 0
            return int(clean_text)
        except ValueError:
            return 0