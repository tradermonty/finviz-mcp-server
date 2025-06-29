import requests
import pandas as pd
import time
import logging
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urlencode

import os
from dotenv import load_dotenv

from ..models import StockData, FINVIZ_FIELD_MAPPING

# 環境変数の読み込み
load_dotenv()

logger = logging.getLogger(__name__)

class FinvizClient:
    """Finviz APIクライアントの基本クラス"""
    
    BASE_URL = "https://elite.finviz.com"
    EXPORT_URL = f"{BASE_URL}/export.ashx"
    GROUPS_EXPORT_URL = f"{BASE_URL}/grp_export.ashx"
    NEWS_EXPORT_URL = f"{BASE_URL}/news_export.ashx"
    QUOTE_EXPORT_URL = f"{BASE_URL}/quote_export.ashx"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初期化
        
        Args:
            api_key: Finviz Elite API キー（環境変数FINVIZ_API_KEYからも取得可能）
        """
        self.api_key = api_key or os.getenv('FINVIZ_API_KEY')
        self.session = requests.Session()
        self.rate_limit_delay = 1.0  # 1秒のデフォルト遅延
        
        # ヘッダーの設定
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session.headers.update(self.headers)
        
        logger.info("Finviz client initialized")
    
    def _make_request(self, url: str, params: Optional[Dict[str, Any]] = None, 
                     retries: int = 3) -> requests.Response:
        """
        HTTPリクエストを実行
        
        Args:
            url: リクエストURL
            params: パラメータ
            retries: リトライ回数
            
        Returns:
            Response オブジェクト
        """
        for attempt in range(retries):
            try:
                # レート制限対応
                time.sleep(self.rate_limit_delay)
                
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                
                logger.debug(f"Request successful: {url}")
                return response
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}/{retries}): {e}")
                if attempt == retries - 1:
                    raise
                time.sleep(2 ** attempt)  # 指数バックオフ
        
        raise Exception("Max retries exceeded")
    

    

    
    def _clean_numeric_value(self, value: str) -> Optional[Union[float, int]]:
        """
        数値文字列をクリーンアップして数値に変換
        
        Args:
            value: 文字列値
            
        Returns:
            数値またはNone
        """
        if not value or value == '-' or value == 'N/A':
            return None
        
        # パーセント記号を削除
        if value.endswith('%'):
            try:
                return float(value[:-1])
            except ValueError:
                return None
        
        # 通貨記号を削除
        if value.startswith('$'):
            value = value[1:]
        
        # カンマを削除
        value = value.replace(',', '')
        
        # 単位を処理 (B = billion, M = million, K = thousand)
        multipliers = {'B': 1e9, 'M': 1e6, 'K': 1e3}
        for suffix, multiplier in multipliers.items():
            if value.endswith(suffix):
                try:
                    return float(value[:-1]) * multiplier
                except ValueError:
                    return None
        
        # 普通の数値として処理
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            return None
    

    
    def get_stock_data(self, ticker: str, fields: Optional[List[str]] = None) -> Optional[StockData]:
        """
        個別銘柄のデータを取得（CSV export使用）
        
        Args:
            ticker: 銘柄ティッカー
            fields: 取得するフィールドのリスト（Noneの場合は全フィールド）
            
        Returns:
            StockData オブジェクトまたはNone
        """
        try:
            params = {'t': ticker}
            
            # CSVから銘柄データを取得
            df = self._fetch_csv_from_url(self.QUOTE_EXPORT_URL, params)
            
            if df.empty:
                logger.warning(f"No data returned for ticker: {ticker}")
                return None
            
            # CSVの最初の行からStockDataオブジェクトを作成
            first_row = df.iloc[0]
            stock_data = self._parse_stock_data_from_csv(first_row)
            
            logger.info(f"Successfully retrieved data for {ticker}")
            return stock_data
            
        except Exception as e:
            logger.error(f"Error retrieving data for {ticker}: {e}")
            return None
    
    def screen_stocks(self, filters: Dict[str, Any]) -> List[StockData]:
        """
        株式スクリーニングを実行（CSV export使用）
        
        Args:
            filters: スクリーニングフィルタ
            
        Returns:
            StockData オブジェクトのリスト
        """
        try:
            # CSVデータを取得
            df = self._fetch_csv_data(filters)
            
            if df.empty:
                logger.warning("No data returned from CSV export")
                return []
            
            # CSVデータからStockDataオブジェクトのリストに変換
            stocks = []
            for _, row in df.iterrows():
                try:
                    stock_data = self._parse_stock_data_from_csv(row)
                    stocks.append(stock_data)
                except Exception as e:
                    logger.warning(f"Failed to parse stock data from CSV: {e}")
                    continue
            
            logger.info(f"Successfully screened {len(stocks)} stocks using CSV export")
            return stocks
            
        except Exception as e:
            logger.error(f"Error in stock screening: {e}")
            return []
    
    def _convert_filters_to_finviz(self, filters: Dict[str, Any]) -> Dict[str, str]:
        """
        内部フィルタ形式をFinviz URLパラメータに変換（強化版）
        
        Args:
            filters: 内部フィルタ形式
            
        Returns:
            Finviz URLパラメータ
        """
        params = {'v': '111'}  # デフォルトビュー
        
        # 時価総額フィルタ
        if 'market_cap' in filters and filters['market_cap']:
            cap_mapping = {
                'mega': 'mega',      # $200B+
                'large': 'large',    # $10B to $200B
                'mid': 'mid',        # $2B to $10B
                'small': 'small',    # $300M to $2B
                'micro': 'micro',    # $50M to $300M
                'nano': 'nano',      # Under $50M
                'smallover': 'smallover',  # $300M+
                'midover': 'midover'       # $2B+
            }
            if filters['market_cap'] in cap_mapping:
                params['f'] = params.get('f', '') + f'cap_{cap_mapping[filters["market_cap"]]},'
        
        # 価格フィルタ
        if 'price_min' in filters and filters['price_min'] is not None:
            params['f'] = params.get('f', '') + f'sh_price_o{filters["price_min"]},'
        if 'price_max' in filters and filters['price_max'] is not None:
            params['f'] = params.get('f', '') + f'sh_price_u{filters["price_max"]},'
        
        # 出来高フィルタ
        if 'volume_min' in filters and filters['volume_min'] is not None:
            params['f'] = params.get('f', '') + f'sh_volume_o{filters["volume_min"]},'
        if 'avg_volume_min' in filters and filters['avg_volume_min'] is not None:
            params['f'] = params.get('f', '') + f'sh_avgvol_o{filters["avg_volume_min"]},'
        if 'relative_volume_min' in filters and filters['relative_volume_min'] is not None:
            params['f'] = params.get('f', '') + f'sh_relvol_o{filters["relative_volume_min"]},'
        
        # 価格変動フィルタ
        if 'price_change_min' in filters and filters['price_change_min'] is not None:
            params['f'] = params.get('f', '') + f'change_o{filters["price_change_min"]},'
        
        # RSIフィルタ
        if 'rsi_min' in filters and filters['rsi_min'] is not None:
            params['f'] = params.get('f', '') + f'rsi_o{filters["rsi_min"]},'
        if 'rsi_max' in filters and filters['rsi_max'] is not None:
            params['f'] = params.get('f', '') + f'rsi_u{filters["rsi_max"]},'
        
        # 移動平均フィルタ
        if 'sma20_above' in filters and filters['sma20_above']:
            params['f'] = params.get('f', '') + 'sma20_pa,'
        if 'sma50_above' in filters and filters['sma50_above']:
            params['f'] = params.get('f', '') + 'sma50_pa,'
        if 'sma200_above' in filters and filters['sma200_above']:
            params['f'] = params.get('f', '') + 'sma200_pa,'
        
        # PEフィルタ
        if 'pe_min' in filters and filters['pe_min'] is not None:
            params['f'] = params.get('f', '') + f'pe_o{filters["pe_min"]},'
        if 'pe_max' in filters and filters['pe_max'] is not None:
            params['f'] = params.get('f', '') + f'pe_u{filters["pe_max"]},'
        
        # 配当利回りフィルタ
        if 'dividend_yield_min' in filters and filters['dividend_yield_min'] is not None:
            params['f'] = params.get('f', '') + f'dividendyield_o{filters["dividend_yield_min"]},'
        if 'dividend_yield_max' in filters and filters['dividend_yield_max'] is not None:
            params['f'] = params.get('f', '') + f'dividendyield_u{filters["dividend_yield_max"]},'
        
        # セクターフィルタ  
        if 'sectors' in filters and filters['sectors']:
            sector_codes = []
            for sector in filters['sectors']:
                sector_code = self._get_sector_code(sector)
                if sector_code:
                    sector_codes.append(sector_code)
            if sector_codes:
                params['f'] = params.get('f', '') + f'sec_{"|".join(sector_codes)},'
        
        # 決算関連フィルタ
        if 'earnings_date' in filters and filters['earnings_date']:
            earnings_mapping = {
                'today_after': 'earningsdate_today',
                'today_before': 'earningsdate_todaybefore',
                'tomorrow_before': 'earningsdate_tomorrow',
                'this_week': 'earningsdate_thisweek',
                'next_week': 'earningsdate_nextweek',  # 追加
                'within_2_weeks': 'earningsdate_within2weeks',
                'yesterday_after': 'earningsdate_yesterday'
            }
            if filters['earnings_date'] in earnings_mapping:
                params['f'] = params.get('f', '') + f'{earnings_mapping[filters["earnings_date"]]},'
        
        # ETFフィルタ
        if 'exclude_etfs' in filters and filters['exclude_etfs']:
            params['f'] = params.get('f', '') + 'geo_usa,'  # 米国株のみ
        
        # フィルタ文字列の末尾のカンマを除去
        if 'f' in params:
            params['f'] = params['f'].rstrip(',')
        
        return params
    
    def _get_sector_code(self, sector: str) -> Optional[str]:
        """
        セクター名をFinvizコードに変換
        
        Args:
            sector: セクター名
            
        Returns:
            Finvizセクターコード
        """
        sector_mapping = {
            'Basic Materials': 'basicmaterials',
            'Communication Services': 'communicationservices',
            'Consumer Cyclical': 'consumercyclical',
            'Consumer Defensive': 'consumerdefensive',
            'Energy': 'energy',
            'Financial Services': 'financial',
            'Healthcare': 'healthcare',
            'Industrials': 'industrials',
            'Real Estate': 'realestate',
            'Technology': 'technology',
            'Utilities': 'utilities'
        }
        return sector_mapping.get(sector)
    

    
    def _fetch_csv_data(self, filters: Dict[str, Any]) -> pd.DataFrame:
        """
        FinvizからCSVデータを取得
        
        Args:
            filters: スクリーニングフィルタ
            
        Returns:
            pandas DataFrame
        """
        try:
            # フィルタをFinviz形式に変換
            finviz_params = self._convert_filters_to_finviz(filters)
            
            # CSV export用のAPIキーパラメータを追加
            if self.api_key:
                finviz_params['auth'] = self.api_key
            else:
                logger.warning("No API key provided. CSV export may not work without Elite subscription.")
                # テスト用のAPIキーを使用（提供されたもの）
                finviz_params['auth'] = '***REMOVED***'
            
            # CSV データを取得
            response = self._make_request(self.EXPORT_URL, finviz_params)
            
            # レスポンスがCSVかHTMLかをチェック
            if response.text.startswith('<!DOCTYPE html>'):
                logger.error("Received HTML instead of CSV. API key may be invalid or not authorized.")
                return pd.DataFrame()
            
            # CSVをDataFrameに変換
            from io import StringIO
            csv_data = StringIO(response.text)
            df = pd.read_csv(csv_data)
            
            logger.info(f"Successfully fetched CSV data with {len(df)} rows")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching CSV data: {e}")
            return pd.DataFrame()
    
    def _parse_stock_data_from_csv(self, row: pd.Series) -> StockData:
        """
        CSV行からStockDataオブジェクトを作成
        
        Args:
            row: pandasのSeries（CSV行データ）
            
        Returns:
            StockData オブジェクト
        """
        # 基本情報
        ticker = str(row.get('Ticker', ''))
        company = str(row.get('Company', ''))
        sector = str(row.get('Sector', ''))
        industry = str(row.get('Industry', ''))
        
        # StockDataオブジェクトを作成
        stock_data = StockData(
            ticker=ticker,
            company_name=company,
            sector=sector,
            industry=industry
        )
        
        # 数値フィールドのマッピング
        numeric_fields = {
            'price': 'Price',
            'market_cap': 'Market Cap',
            'pe_ratio': 'P/E',
            'eps': 'EPS (ttm)',
            'dividend_yield': 'Dividend %',
            'volume': 'Volume',
            'avg_volume': 'Avg Volume',
            'relative_volume': 'Rel Volume',
            'price_change': 'Change',
            'rsi': 'RSI (14)',
            'beta': 'Beta',
            'target_price': 'Target Price',
            'performance_1w': 'Perf Week',
            'performance_1m': 'Perf Month',
            'week_52_high': '52W High',
            'week_52_low': '52W Low'
        }
        
        # 数値フィールドを設定
        for field, csv_column in numeric_fields.items():
            if csv_column in row.index:
                value = row[csv_column]
                if pd.notna(value):
                    # 数値変換
                    if isinstance(value, str):
                        cleaned_value = self._clean_numeric_value(value)
                        setattr(stock_data, field, cleaned_value)
                    else:
                        setattr(stock_data, field, float(value) if value != 0 else None)
        
        # 文字列フィールドを設定
        string_fields = {
            'country': 'Country',
            'analyst_recommendation': 'Recom',
            'earnings_date': 'Earnings'
        }
        
        for field, csv_column in string_fields.items():
            if csv_column in row.index:
                value = row[csv_column]
                if pd.notna(value) and str(value) != '-':
                    setattr(stock_data, field, str(value))
        
        return stock_data
    
    def _fetch_csv_from_url(self, export_url: str, params: Dict[str, Any] = None) -> pd.DataFrame:
        """
        指定されたエクスポートURLからCSVデータを取得
        
        Args:
            export_url: エクスポートURL
            params: パラメータ（オプション）
            
        Returns:
            pandas DataFrame
        """
        try:
            # パラメータを準備
            export_params = params.copy() if params else {}
            
            # APIキーを追加
            if self.api_key:
                export_params['auth'] = self.api_key
            else:
                logger.warning(f"No API key provided for {export_url}. Using test API key.")
                export_params['auth'] = '***REMOVED***'
            
            # CSV データを取得
            response = self._make_request(export_url, export_params)
            
            # レスポンスがCSVかHTMLかをチェック
            if response.text.startswith('<!DOCTYPE html>'):
                logger.error(f"Received HTML instead of CSV from {export_url}. API key may be invalid.")
                return pd.DataFrame()
            
            # CSVをDataFrameに変換
            from io import StringIO
            csv_data = StringIO(response.text)
            df = pd.read_csv(csv_data)
            
            logger.info(f"Successfully fetched CSV data from {export_url} with {len(df)} rows")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching CSV data from {export_url}: {e}")
            return pd.DataFrame()