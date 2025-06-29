import logging
from typing import List, Optional, Dict, Any
import pandas as pd

from .base import FinvizClient
from ..models import SectorPerformance

logger = logging.getLogger(__name__)

class FinvizSectorAnalysisClient(FinvizClient):
    """Finvizセクター・業界分析専用クライアント"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
    
    def get_sector_performance(self, timeframe: str = "1d", 
                             sectors: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        セクター別パフォーマンス分析（CSV export使用）
        
        Args:
            timeframe: 分析期間 (1d, 1w, 1m, 3m, 6m, 1y) - 現在は無視される
            sectors: 対象セクター（Noneの場合は全セクター）
            
        Returns:
            SectorPerformance オブジェクトのリスト
        """
        try:
            # 基本的なセクターデータを取得（v=152パラメーター追加）
            params = {
                'g': 'sector',
                'v': '152'  # 正しいビューフォーマット
            }
            
            # APIキーを追加（base.pyと同様の処理）
            if self.api_key:
                params['auth'] = self.api_key
            else:
                logger.warning("No API key provided. Using test API key.")
                params['auth'] = '***REMOVED***'
            
            # CSVからセクターパフォーマンスデータを取得
            df = self._fetch_csv_from_url(self.GROUPS_EXPORT_URL, params)
            
            if df.empty:
                logger.warning("No sector performance data returned")
                return []
            
            # CSVデータからSectorPerformanceオブジェクトのリストに変換
            sector_data = []
            for _, row in df.iterrows():
                try:
                    sector_perf = self._parse_sector_performance_from_csv(row)
                    if sector_perf:
                        sector_data.append(sector_perf)
                except Exception as e:
                    logger.warning(f"Failed to parse sector performance from CSV: {e}")
                    continue
            
            # セクターフィルタリング
            if sectors:
                sector_data = [s for s in sector_data if s.get('name') in sectors]
            
            logger.info(f"Retrieved performance data for {len(sector_data)} sectors")
            return sector_data
            
        except Exception as e:
            logger.error(f"Error retrieving sector performance: {e}")
            return []
    
    def get_industry_performance(self, industries: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        業界別パフォーマンス分析（CSV export使用）
        
        Args:
            industries: 対象業界（Noneの場合は全業界）
            
        Returns:
            業界パフォーマンスデータのリスト
        """
        try:
            params = {
                'g': 'industry',
                'v': '152',  # 固定値
                'o': 'name',  # ソート順序
                'c': '0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26'  # 全カラム指定
            }
            
            # CSVから業界パフォーマンスデータを取得
            df = self._fetch_csv_from_url(self.GROUPS_EXPORT_URL, params)
            
            if df.empty:
                logger.warning("No industry performance data returned")
                return []
            
            # CSVデータから業界パフォーマンスデータのリストに変換
            industry_data = []
            for _, row in df.iterrows():
                try:
                    industry_perf = self._parse_industry_performance_from_csv(row)
                    if industry_perf:
                        industry_data.append(industry_perf)
                except Exception as e:
                    logger.warning(f"Failed to parse industry performance from CSV: {e}")
                    continue
                    
            # 業界フィルタリング
            if industries:
                industry_data = [i for i in industry_data if i.get('industry') in industries]
            
            logger.info(f"Retrieved performance data for {len(industry_data)} industries")
            return industry_data
            
        except Exception as e:
            logger.error(f"Error retrieving industry performance: {e}")
            return []
    
    def get_country_performance(self, countries: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        国別市場パフォーマンス分析（CSV export使用）
        
        Args:
            countries: 対象国（Noneの場合は全国）
            
        Returns:
            国別パフォーマンスデータのリスト
        """
        try:
            params = {
                'g': 'country',
                'v': '152',  # 固定値
                'o': 'name',  # ソート順序
                'c': '0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26'  # 全カラム指定
            }
            
            # CSVから国別パフォーマンスデータを取得
            df = self._fetch_csv_from_url(self.GROUPS_EXPORT_URL, params)
            
            if df.empty:
                logger.warning("No country performance data returned")
                return []
            
            # CSVデータから国別パフォーマンスデータのリストに変換
            country_data = []
            for _, row in df.iterrows():
                try:
                    country_perf = self._parse_country_performance_from_csv(row)
                    if country_perf:
                        country_data.append(country_perf)
                except Exception as e:
                    logger.warning(f"Failed to parse country performance from CSV: {e}")
                    continue
            
            # 国フィルタリング
            if countries:
                country_data = [c for c in country_data if c.get('country') in countries]
            
            logger.info(f"Retrieved performance data for {len(country_data)} countries")
            return country_data
            
        except Exception as e:
            logger.error(f"Error retrieving country performance: {e}")
            return []
    
    def get_sector_specific_industry_performance(self, sector: str) -> List[Dict[str, Any]]:
        """
        特定セクター内の業界別パフォーマンス分析
        
        Args:
            sector: セクター名 (basicmaterials, communicationservices, consumercyclical, etc.)
            
        Returns:
            業界パフォーマンスデータのリスト
        """
        try:
            # セクター名を正規化
            sector_mapping = {
                'basicmaterials': 'basicmaterials',
                'basic_materials': 'basicmaterials',
                'communicationservices': 'communicationservices',
                'communication_services': 'communicationservices',
                'consumercyclical': 'consumercyclical',
                'consumer_cyclical': 'consumercyclical',
                'consumerdefensive': 'consumerdefensive',
                'consumer_defensive': 'consumerdefensive',
                'energy': 'energy',
                'financial': 'financial',
                'healthcare': 'healthcare',
                'industrials': 'industrials',
                'realestate': 'realestate',
                'real_estate': 'realestate',
                'technology': 'technology',
                'utilities': 'utilities'
            }
            
            sector_code = sector_mapping.get(sector.lower(), sector.lower())
            
            params = {
                'g': 'industry',
                'sg': sector_code,
                'v': '152',  # 固定値
                'o': 'name',  # ソート順序
                'c': '0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26'  # 全カラム指定
            }
            
            # CSVからセクター別業界パフォーマンスデータを取得
            df = self._fetch_csv_from_url(self.GROUPS_EXPORT_URL, params)
            
            if df.empty:
                logger.warning(f"No industry performance data returned for sector {sector}")
                return []
            
            # CSVデータから業界パフォーマンスデータのリストに変換
            industry_data = []
            for _, row in df.iterrows():
                try:
                    industry_perf = self._parse_industry_performance_from_csv(row)
                    if industry_perf:
                        # セクター情報を追加
                        industry_perf['parent_sector'] = sector
                        industry_data.append(industry_perf)
                except Exception as e:
                    logger.warning(f"Failed to parse sector-specific industry performance from CSV: {e}")
                    continue
            
            logger.info(f"Retrieved performance data for {len(industry_data)} industries in {sector} sector")
            return industry_data
            
        except Exception as e:
            logger.error(f"Error retrieving sector-specific industry performance: {e}")
            return []

    def get_capitalization_performance(self) -> List[Dict[str, Any]]:
        """
        時価総額別パフォーマンス分析
        
        Returns:
            時価総額別パフォーマンスデータのリスト
        """
        try:
            params = {
                'g': 'capitalization',
                'v': '152',  # 固定値
                'o': 'name',  # ソート順序
                'c': '0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26'  # 全カラム指定
            }
            
            # CSVから時価総額別パフォーマンスデータを取得
            df = self._fetch_csv_from_url(self.GROUPS_EXPORT_URL, params)
            
            if df.empty:
                logger.warning("No capitalization performance data returned")
                return []
            
            # CSVデータから時価総額別パフォーマンスデータのリストに変換
            cap_data = []
            for _, row in df.iterrows():
                try:
                    cap_perf = self._parse_capitalization_performance_from_csv(row)
                    if cap_perf:
                        cap_data.append(cap_perf)
                except Exception as e:
                    logger.warning(f"Failed to parse capitalization performance from CSV: {e}")
                    continue
            
            logger.info(f"Retrieved performance data for {len(cap_data)} capitalization categories")
            return cap_data
            
        except Exception as e:
            logger.error(f"Error retrieving capitalization performance: {e}")
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
    

    
    def _parse_sector_performance_from_csv(self, row: 'pd.Series') -> Optional[Dict[str, Any]]:
        """
        CSV行からセクターパフォーマンスデータを作成
        
        Args:
            row: pandasのSeries（CSV行データ）
            
        Returns:
            セクターパフォーマンスデータ辞書またはNone
        """
        try:
            import pandas as pd
            
            sector_name = str(row.get('Name', ''))
            if not sector_name:
                return None
            
            return {
                'name': sector_name,
                'market_cap': str(row.get('Market Cap', 'N/A')),
                'pe_ratio': str(row.get('P/E', 'N/A')),
                'dividend_yield': str(row.get('Dividend Yield', 'N/A')),
                'change': str(row.get('Change', 'N/A')),
                'stocks': str(row.get('Stocks', 'N/A'))
            }
            
        except Exception as e:
            logger.warning(f"Failed to parse sector performance from CSV row: {e}")
            return None
    
    def _parse_industry_performance_from_csv(self, row: 'pd.Series') -> Optional[Dict[str, Any]]:
        """
        CSV行から業界パフォーマンスデータを作成
        
        Args:
            row: pandasのSeries（CSV行データ）
            
        Returns:
            業界パフォーマンスデータ辞書またはNone
        """
        try:
            import pandas as pd
            
            industry_name = str(row.get('Industry', ''))
            if not industry_name:
                return None
            
            return {
                'industry': industry_name,
                'performance_1d': self._safe_parse_percentage(row.get('1D %', 0)),
                'performance_1w': self._safe_parse_percentage(row.get('1W %', 0)),
                'performance_1m': self._safe_parse_percentage(row.get('1M %', 0)),
                'performance_3m': self._safe_parse_percentage(row.get('3M %', 0)),
                'performance_6m': self._safe_parse_percentage(row.get('6M %', 0)),
                'performance_1y': self._safe_parse_percentage(row.get('1Y %', 0)),
                'stock_count': self._safe_parse_number(row.get('Stocks', 0))
            }
            
        except Exception as e:
            logger.warning(f"Failed to parse industry performance from CSV row: {e}")
            return None
    
    def _parse_country_performance_from_csv(self, row: 'pd.Series') -> Optional[Dict[str, Any]]:
        """
        CSV行から国別パフォーマンスデータを作成
        
        Args:
            row: pandasのSeries（CSV行データ）
            
        Returns:
            国別パフォーマンスデータ辞書またはNone
        """
        try:
            import pandas as pd
            
            country_name = str(row.get('Country', ''))
            if not country_name:
                return None
            
            return {
                'country': country_name,
                'performance_1d': self._safe_parse_percentage(row.get('1D %', 0)),
                'performance_1w': self._safe_parse_percentage(row.get('1W %', 0)),
                'performance_1m': self._safe_parse_percentage(row.get('1M %', 0)),
                'performance_3m': self._safe_parse_percentage(row.get('3M %', 0)),
                'performance_6m': self._safe_parse_percentage(row.get('6M %', 0)),
                'performance_1y': self._safe_parse_percentage(row.get('1Y %', 0)),
                'stock_count': self._safe_parse_number(row.get('Stocks', 0))
            }
            
        except Exception as e:
            logger.warning(f"Failed to parse country performance from CSV row: {e}")
            return None
    
    def _safe_parse_percentage(self, value) -> float:
        """
        安全にパーセンテージを解析
        
        Args:
            value: パーセンテージ値
            
        Returns:
            float値
        """
        if value is None or str(value) in ['-', 'N/A', 'nan', '']:
            return 0.0
        
        try:
            if isinstance(value, str):
                # パーセント記号を削除して数値に変換
                cleaned_value = value.replace('%', '').strip()
                return float(cleaned_value)
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
    def _parse_capitalization_performance_from_csv(self, row: 'pd.Series') -> Optional[Dict[str, Any]]:
        """
        CSV行から時価総額別パフォーマンスデータを作成
        
        Args:
            row: pandasのSeries（CSV行データ）
            
        Returns:
            時価総額別パフォーマンスデータ辞書またはNone
        """
        try:
            import pandas as pd
            
            cap_name = str(row.get('Name', ''))
            if not cap_name:
                return None
            
            return {
                'capitalization': cap_name,
                'market_cap': str(row.get('Market Cap', 'N/A')),
                'pe_ratio': str(row.get('P/E', 'N/A')),
                'dividend_yield': str(row.get('Dividend Yield', 'N/A')),
                'change': str(row.get('Change', 'N/A')),
                'stocks': str(row.get('Stocks', 'N/A'))
            }
            
        except Exception as e:
            logger.warning(f"Failed to parse capitalization performance from CSV row: {e}")
            return None

    def _safe_parse_number(self, value) -> int:
        """
        安全に数値を解析
        
        Args:
            value: 数値
            
        Returns:
            int値
        """
        if value is None or str(value) in ['-', 'N/A', 'nan', '']:
            return 0
        
        try:
            if isinstance(value, str):
                # カンマを削除して数値に変換
                cleaned_value = value.replace(',', '').strip()
                return int(float(cleaned_value))
            return int(value)
        except (ValueError, TypeError):
            return 0