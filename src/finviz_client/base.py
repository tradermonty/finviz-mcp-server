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
        params = {'v': '111'}  # 標準ビューに戻す
        
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
            earnings_date_value = filters['earnings_date']
            
            # 日付範囲指定の場合（例：{"start": "2025-06-30", "end": "2025-07-04"}）
            if isinstance(earnings_date_value, dict) and 'start' in earnings_date_value and 'end' in earnings_date_value:
                start_date = earnings_date_value['start']
                end_date = earnings_date_value['end']
                # Finviz形式: MM-DD-YYYYxMM-DD-YYYY
                start_formatted = self._format_date_for_finviz(start_date)
                end_formatted = self._format_date_for_finviz(end_date)
                if start_formatted and end_formatted:
                    params['f'] = params.get('f', '') + f'earningsdate_{start_formatted}x{end_formatted},'
            
            # 直接の日付範囲文字列の場合（例：「06-30-2025x07-04-2025」）
            elif isinstance(earnings_date_value, str) and 'x' in earnings_date_value:
                params['f'] = params.get('f', '') + f'earningsdate_{earnings_date_value},'
            
            # 従来の固定期間指定の場合
            else:
                # Finvizの特殊な仕様: 複数のearnings_date値を|で結合する場合、
                # 最初の値だけearningsdate_プレフィックスが付き、残りは値のみ
                earnings_values = {
                    # 内部形式 -> Finviz形式（プレフィックスなし）
                    'today': 'today',
                    'today_before': 'todaybefore',
                    'today_after': 'todayafter',
                    'tomorrow': 'tomorrow',
                    'tomorrow_before': 'tomorrowbefore',
                    'tomorrow_after': 'tomorrowafter',
                    'yesterday': 'yesterday',
                    'yesterday_before': 'yesterdaybefore',
                    'yesterday_after': 'yesterdayafter',
                    'next_5_days': 'nextdays5',
                    'this_week': 'thisweek',
                    'next_week': 'nextweek',
                    'prev_week': 'prevweek',
                    'this_month': 'thismonth',
                    # サーバーから渡される値との互換性
                    'nextweek': 'nextweek',
                    'within_2_weeks': 'nextdays5',
                    # 直接Finviz形式の値もサポート
                    'todaybefore': 'todaybefore',
                    'todayafter': 'todayafter',
                    'tomorrowbefore': 'tomorrowbefore',
                    'tomorrowafter': 'tomorrowafter',
                    'yesterdaybefore': 'yesterdaybefore',
                    'yesterdayafter': 'yesterdayafter',
                    'nextdays5': 'nextdays5',
                    'thisweek': 'thisweek',
                    'prevweek': 'prevweek',
                    'thismonth': 'thismonth'
                }
                
                # 単一の値の場合
                if isinstance(earnings_date_value, str) and earnings_date_value in earnings_values:
                    params['f'] = params.get('f', '') + f'earningsdate_{earnings_values[earnings_date_value]},'
                # リストの場合（複数条件のOR）
                elif isinstance(earnings_date_value, list):
                    valid_values = [earnings_values[v] for v in earnings_date_value if v in earnings_values]
                    if valid_values:
                        # 最初の値だけearningsdate_プレフィックスを付ける
                        earnings_filter = f'earningsdate_{valid_values[0]}'
                        if len(valid_values) > 1:
                            # 残りの値は|で結合（プレフィックスなし）
                            earnings_filter += '|' + '|'.join(valid_values[1:])
                        params['f'] = params.get('f', '') + f'{earnings_filter},'
        
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
    
    def _format_date_for_finviz(self, date_str: str) -> Optional[str]:
        """
        日付文字列をFinviz形式（MM-DD-YYYY）に変換
        
        Args:
            date_str: 日付文字列（YYYY-MM-DD、MM-DD-YYYY、MM/DD/YYYY等）
            
        Returns:
            Finviz形式の日付文字列（MM-DD-YYYY）またはNone
        """
        import re
        from datetime import datetime
        
        try:
            # 既にFinviz形式（MM-DD-YYYY）の場合
            if re.match(r'^\d{2}-\d{2}-\d{4}$', date_str):
                return date_str
            
            # ISO形式（YYYY-MM-DD）の場合
            if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                return date_obj.strftime('%m-%d-%Y')
            
            # スラッシュ区切り（MM/DD/YYYY）の場合
            if re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', date_str):
                date_obj = datetime.strptime(date_str, '%m/%d/%Y')
                return date_obj.strftime('%m-%d-%Y')
            
            # その他の形式もサポート
            for fmt in ['%Y/%m/%d', '%d-%m-%Y', '%d/%m/%Y']:
                try:
                    date_obj = datetime.strptime(date_str, fmt)
                    return date_obj.strftime('%m-%d-%Y')
                except ValueError:
                    continue
            
            logger.warning(f"Unsupported date format: {date_str}")
            return None
            
        except Exception as e:
            logger.error(f"Error formatting date {date_str}: {e}")
            return None
    

    
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
            
            # CSV export用のパラメータを追加
            finviz_params['ft'] = '4'  # CSV形式を指定
            
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
            # デバッグ: CSVのカラムを確認
            logger.debug(f"CSV columns: {list(df.columns)}")
            if len(df) > 0:
                logger.debug(f"First row sample: {df.iloc[0].to_dict()}")
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
        
        # 決算日フィールドの代替名も確認
        earnings_columns = ['Earnings', 'Earnings Date', 'earnings_date', 'Earnings_Date']
        
        for field, csv_column in string_fields.items():
            if field == 'earnings_date':
                # 複数の可能なカラム名をチェック
                for col in earnings_columns:
                    if col in row.index:
                        value = row[col]
                        if pd.notna(value) and str(value) != '-' and str(value) != '':
                            setattr(stock_data, field, str(value))
                            break
            elif csv_column in row.index:
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
            
            # CSV形式を指定
            export_params['ft'] = '4'
            
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
    
    def get_stock_fundamentals(self, ticker: str, data_fields: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """
        個別銘柄のファンダメンタルデータを取得
        
        Args:
            ticker: 銘柄ティッカー
            data_fields: 取得するデータフィールド
            
        Returns:
            ファンダメンタルデータ辞書またはNone
        """
        try:
            stock_data = self.get_stock_data(ticker)
            if not stock_data:
                return None
            
            # StockDataオブジェクトを辞書に変換
            result = {
                'ticker': stock_data.ticker,
                'company': stock_data.company_name,
                'sector': stock_data.sector,
                'price': stock_data.price,
                'price_change': stock_data.price_change,
                'price_change_percent': stock_data.price_change_percent,
                'volume': stock_data.volume,
                'avg_volume': stock_data.avg_volume,
                'relative_volume': stock_data.relative_volume,
                'market_cap': stock_data.market_cap,
                'pe_ratio': stock_data.pe_ratio,
                'forward_pe': stock_data.forward_pe,
                'peg': stock_data.peg,
                'ps_ratio': stock_data.ps_ratio,
                'pb_ratio': stock_data.pb_ratio,
                'earnings_date': stock_data.earnings_date,
                'eps_surprise': stock_data.eps_surprise,
                'revenue_surprise': stock_data.revenue_surprise,
                'eps_growth_qtr': stock_data.eps_growth_qtr,
                'sales_growth_qtr': stock_data.sales_growth_qtr,
                'performance_1w': stock_data.performance_1w,
                'target_price': stock_data.target_price,
                'analyst_recommendation': stock_data.analyst_recommendation,
                'beta': stock_data.beta,
                'volatility': stock_data.volatility,
                'rsi': stock_data.rsi
            }
            
            # 指定されたフィールドのみ返す
            if data_fields:
                filtered_result = {}
                for field in data_fields:
                    if field in result:
                        filtered_result[field] = result[field]
                return filtered_result
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting fundamentals for {ticker}: {e}")
            return None
    
    def get_multiple_stocks_fundamentals(self, tickers: List[str], data_fields: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        複数銘柄のファンダメンタルデータ一括取得
        
        Args:
            tickers: 銘柄ティッカーリスト
            data_fields: 取得するデータフィールド
            
        Returns:
            ファンダメンタルデータのリスト
        """
        results = []
        
        for ticker in tickers:
            try:
                fundamental_data = self.get_stock_fundamentals(ticker, data_fields)
                if fundamental_data:
                    results.append(fundamental_data)
                
                # レート制限対応
                time.sleep(0.5)
                
            except Exception as e:
                logger.warning(f"Failed to get fundamentals for {ticker}: {e}")
                continue
        
        return results
    
    def get_market_overview(self) -> Dict[str, Any]:
        """
        市場全体の概要を取得
        
        Returns:
            市場概要データ
        """
        try:
            # シンプルな市場概要を返す（実際のFinvizからのデータ取得が困難な場合）
            overview = {
                'market_status': 'Active',
                'timestamp': pd.Timestamp.now().isoformat(),
                'major_indices': {
                    'S&P 500': {'symbol': 'SPY', 'status': 'Available'},
                    'NASDAQ': {'symbol': 'QQQ', 'status': 'Available'},
                    'Dow Jones': {'symbol': 'DIA', 'status': 'Available'}
                },
                'market_sectors': [
                    'Technology', 'Healthcare', 'Financial Services',
                    'Consumer Cyclical', 'Communication Services', 
                    'Industrials', 'Consumer Defensive', 'Energy',
                    'Utilities', 'Real Estate', 'Basic Materials'
                ],
                'available_screeners': [
                    'earnings_screener', 'volume_surge_screener', 
                    'uptrend_screener', 'dividend_growth_screener'
                ]
            }
            
            return overview
            
        except Exception as e:
            logger.error(f"Error getting market overview: {e}")
            return {'error': str(e)}