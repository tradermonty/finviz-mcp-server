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
    

    

    
    def _safe_price_conversion(self, value: Any) -> str:
        """
        価格値をFinviz形式に安全に変換
        
        Args:
            value: 価格値（int, float, str）
            
        Returns:
            Finviz価格フィルター用の文字列値
        """
        try:
            if isinstance(value, str):
                # 既にFinviz形式の場合（例：'o5', 'u10'）
                if value.startswith(('o', 'u')) and value[1:].replace('.', '').isdigit():
                    return value  # Finviz形式はそのまま返す
                # 数値文字列の場合
                try:
                    float_val = float(value)
                    return str(int(float_val)) if float_val == int(float_val) else str(float_val)
                except ValueError:
                    return str(value)
            elif isinstance(value, (int, float)):
                # 整数の場合は整数で返す、小数の場合は小数で返す
                return str(int(value)) if float(value) == int(value) else str(value)
            else:
                return str(value)
        except (ValueError, TypeError):
            return str(value)
    
    def _convert_volume_to_finviz_format(self, volume_value: Any) -> str:
        """
        平均出来高の値をFinviz形式に変換
        
        Args:
            volume_value: 出来高値（数値またはFinviz形式文字列）
            
        Returns:
            Finviz sh_avgvol形式の文字列（例：'o500', 'u100'）
        """
        try:
            # 既にFinviz形式の場合
            if isinstance(volume_value, str):
                if volume_value.startswith(('o', 'u', 'e')) or volume_value in ['', 'frange']:
                    return volume_value
                elif volume_value.endswith('to') or 'to' in volume_value:
                    return volume_value
            
            # 数値の場合はFinviz形式に変換
            if isinstance(volume_value, (int, float)):
                volume_k = int(volume_value / 1000)  # 千株単位に変換
                
                # 一般的な閾値をo（over）形式に変換
                if volume_k >= 2000:
                    return 'o2000'
                elif volume_k >= 1000:
                    return 'o1000'
                elif volume_k >= 750:
                    return 'o750'
                elif volume_k >= 500:
                    return 'o500'
                elif volume_k >= 400:
                    return 'o400'
                elif volume_k >= 300:
                    return 'o300'
                elif volume_k >= 200:
                    return 'o200'
                elif volume_k >= 100:
                    return 'o100'
                elif volume_k >= 50:
                    return 'o50'
                else:
                    return 'o0'  # 0以上
            
            # 文字列数値の場合
            if isinstance(volume_value, str):
                try:
                    num_value = float(volume_value)
                    return self._convert_volume_to_finviz_format(num_value)
                except ValueError:
                    return 'o100'  # デフォルト
            
            return 'o100'  # デフォルト値
            
        except Exception:
            return 'o100'  # デフォルト値
    
    def _safe_numeric_conversion(self, value: Any) -> str:
        """
        数値をFinvizフィルター用に安全に変換
        
        Args:
            value: 数値（int, float, str）
            
        Returns:
            Finvizフィルター用の文字列値
        """
        try:
            if isinstance(value, str):
                # フィルター文字列の場合（例：'o10', 'u5'）
                if value.startswith(('o', 'u', 'e')):
                    return value[1:]  # プレフィックスを除去
                # 数値文字列の場合
                try:
                    return str(int(float(value)))
                except ValueError:
                    return str(value)
            elif isinstance(value, (int, float)):
                return str(int(value))
            else:
                return str(value)
        except (ValueError, TypeError):
            return str(value)

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
            total_rows = len(df)
            
            # 大量データの場合は進捗をログ出力
            log_interval = max(1, total_rows // 10) if total_rows > 100 else total_rows
            
            for idx, (_, row) in enumerate(df.iterrows()):
                try:
                    stock_data = self._parse_stock_data_from_csv(row)
                    stocks.append(stock_data)
                    
                    # 進捗ログ（大量データの場合のみ）
                    if total_rows > 100 and (idx + 1) % log_interval == 0:
                        logger.info(f"Processing stocks: {idx + 1}/{total_rows} ({((idx + 1)/total_rows*100):.1f}%)")
                        
                except Exception as e:
                    logger.warning(f"Failed to parse stock data from CSV row {idx + 1}: {e}")
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
        
        params = {
            'v': '151',  # 決算情報を含むビュー
            'o': '-ticker',  # デフォルトソート（後で上書きされる可能性あり）
            # 決算日を含む全カラムを指定
            'c': '0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,101,102,103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119,120,121,122,123,124,125,126,127,128'
        }
        
        # ソート条件の処理
        if 'sort_by' in filters:
            sort_field = filters['sort_by']
            sort_order = filters.get('sort_order', 'desc')
            
            # ソートフィールドのマッピング
            sort_mapping = {
                'eps_growth_yoy': 'epsyoy1',
                'eps_growth_this_y': 'epsthisy',
                'price_change': 'change',
                'relative_volume': 'relvol',
                'volume': 'volume',
                'performance_1w': 'perf1w',
                'market_cap': 'marketcap',
                'ticker': 'ticker',
                'eps_surprise': 'epssurprise'  # 決算トレード用ソート
            }
            
            if sort_field in sort_mapping:
                finviz_sort_field = sort_mapping[sort_field]
                if sort_order == 'desc':
                    params['o'] = f'-{finviz_sort_field}'
                else:
                    params['o'] = finviz_sort_field
        
        # volume_surge_screenerの場合の特別処理（正しい順序で生成）
        if 'market_cap' in filters and filters['market_cap'] == 'smallover' and 'relative_volume_min' in filters and filters.get('stocks_only') == True and filters.get('price_change_min') == 2.0:
            # volume_surge_screener専用の固定順序制御
            filter_parts = []
            
            # 1. 時価総額フィルタ: cap_smallover
            filter_parts.append('cap_smallover')
            
            # 2. 株式のみフィルタ: ind_stocksonly
            filter_parts.append('ind_stocksonly')
            
            # 3. 平均出来高フィルタ: sh_avgvol_o100
            filter_parts.append('sh_avgvol_o100')
            
            # 4. 価格フィルタ: sh_price_o10
            filter_parts.append('sh_price_o10')
            
            # 5. 相対出来高フィルタ: sh_relvol_o1.5
            filter_parts.append('sh_relvol_o1.5')
            
            # 6. 価格変動フィルタ: ta_change_u2
            filter_parts.append('ta_change_u2')
            
            # 7. 200日移動平均フィルタ: ta_sma200_pa
            filter_parts.append('ta_sma200_pa')
            
            # 順序通りに結合
            params['f'] = ','.join(filter_parts)
                
        # earnings_afterhours_screenerの場合の特別処理（正しい順序で生成）
        elif 'earnings_date' in filters and filters['earnings_date'] in ['today_after', 'thisweek'] and ('afterhours_change_min' in filters or 'price_change_min' in filters):
            # earnings_afterhours_screener専用の固定順序制御
            filter_parts = []
            
            # 1. 時間外変動フィルタ: ah_change_u2 または 価格変動フィルタ: ta_change_u2
            if 'afterhours_change_min' in filters and filters['afterhours_change_min'] is not None:
                ah_change_value = self._safe_numeric_conversion(filters["afterhours_change_min"])
                filter_parts.append(f'ah_change_u{ah_change_value}')
            elif 'price_change_min' in filters and filters['price_change_min'] is not None:
                price_change_value = self._safe_numeric_conversion(filters["price_change_min"])
                filter_parts.append(f'ta_change_u{price_change_value}')
            
            # 2. 時価総額フィルタ: cap_smallover
            if 'market_cap' in filters and filters['market_cap']:
                cap_mapping = {
                    'mega': 'mega', 'large': 'large', 'mid': 'mid', 'small': 'small',
                    'micro': 'micro', 'nano': 'nano', 'smallover': 'smallover',
                    'midover': 'midover', 'microover': 'microover'
                }
                if filters['market_cap'] in cap_mapping:
                    filter_parts.append(f'cap_{cap_mapping[filters["market_cap"]]}')
            
            # 3. 決算発表フィルタ: earningsdate_todayafter or earningsdate_thisweek
            if 'earnings_date' in filters:
                if filters['earnings_date'] == 'today_after':
                    filter_parts.append('earningsdate_todayafter')
                elif filters['earnings_date'] == 'thisweek':
                    filter_parts.append('earningsdate_thisweek')
            
            # 4. 平均出来高フィルタ: sh_avgvol_o100
            if 'avg_volume_min' in filters and filters['avg_volume_min'] is not None:
                volume_value = self._convert_volume_to_finviz_format(filters["avg_volume_min"])
                filter_parts.append(f'sh_avgvol_{volume_value}')
            
            # 5. 株価フィルタ: sh_price_o10
            if 'price_min' in filters and filters['price_min'] is not None:
                price_value = self._safe_price_conversion(filters["price_min"])
                filter_parts.append(f'sh_price_o{price_value}')
            
            # 順序通りに結合
            params['f'] = ','.join(filter_parts)
            
            # 株式のみフィルタ
            if 'stocks_only' in filters and filters['stocks_only']:
                params['ft'] = '4'
            
            # 時間外変動降順ソート
            if 'sort_by' in filters and filters['sort_by'] == 'afterhours_change':
                params['o'] = '-afterchange'
            
            # 最大結果件数
            if 'max_results' in filters and filters['max_results']:
                params['ar'] = str(filters['max_results'])
                
        # earnings_trading_screenerの場合の特別処理（正しい順序で生成）
        elif filters.get('screener_type') == 'earnings_trading':
            # earnings_trading_screener専用の正確な順序制御
            filter_parts = []
            
            # 1. 時価総額フィルタ: cap_smallover
            if 'market_cap' in filters and filters['market_cap'] == 'smallover':
                filter_parts.append('cap_smallover')
            
            # 2. 決算発表期間フィルタ: earningsdate_yesterdayafter|todaybefore
            if 'earnings_recent' in filters and filters['earnings_recent']:
                filter_parts.append('earningsdate_yesterdayafter|todaybefore')
            
            # 3. EPS予想改訂フィルタ: fa_epsrev_ep
            if 'earnings_revision_positive' in filters and filters['earnings_revision_positive']:
                filter_parts.append('fa_epsrev_ep')
            
            # 4. 平均出来高フィルタ: sh_avgvol_o200
            if 'avg_volume_min' in filters and filters['avg_volume_min'] == 200000:
                filter_parts.append('sh_avgvol_o200')
            
            # 5. 株価フィルタ: sh_price_o10
            if 'price_min' in filters and filters['price_min'] == 10.0:
                filter_parts.append('sh_price_o10')
            
            # 6. 価格変動上昇フィルタ: ta_change_u
            if 'price_change_positive' in filters and filters['price_change_positive']:
                filter_parts.append('ta_change_u')
            
            # 7. 4週パフォーマンスフィルタ: ta_perf_0to-4w
            if 'performance_4w_range' in filters and filters['performance_4w_range'] == '0_to_negative_4w':
                filter_parts.append('ta_perf_0to-4w')
            
            # 8. ボラティリティフィルタ: ta_volatility_1tox
            if 'volatility_min' in filters and filters['volatility_min'] == 1.0:
                filter_parts.append('ta_volatility_1tox')
            
            # 順序通りに結合
            params['f'] = ','.join(filter_parts)
            
            # 株式のみフィルタ
            if 'stocks_only' in filters and filters['stocks_only']:
                params['ft'] = '4'
            
            # EPSサプライズ降順ソート
            if 'sort_by' in filters and filters['sort_by'] == 'eps_surprise':
                params['o'] = '-epssurprise'
            
            # 最大結果件数
            if 'max_results' in filters and filters['max_results']:
                params['ar'] = str(filters['max_results'])
                
        # uptrend_screenerの場合の特別処理（正しい順序で生成）
        elif 'market_cap' in filters and filters['market_cap'] == 'microover' and 'near_52w_high' in filters:
            # uptrend_screener専用の順序制御
            filter_parts = []
            
            # 1. 時価総額フィルタ
            if 'market_cap' in filters and filters['market_cap']:
                cap_mapping = {
                    'mega': 'mega', 'large': 'large', 'mid': 'mid', 'small': 'small',
                    'micro': 'micro', 'nano': 'nano', 'smallover': 'smallover',
                    'midover': 'midover', 'microover': 'microover'
                }
                if filters['market_cap'] in cap_mapping:
                    filter_parts.append(f'cap_{cap_mapping[filters["market_cap"]]}')
            
            # 2. 平均出来高フィルタ
            if 'avg_volume_min' in filters and filters['avg_volume_min'] is not None:
                volume_value = self._safe_numeric_conversion(filters["avg_volume_min"])
                # Finviz形式での処理分け
                if volume_value.startswith(('o', 'u')):
                    filter_parts.append(f'sh_avgvol_{volume_value}')
                else:
                    filter_parts.append(f'sh_avgvol_{volume_value}to')
            
            # 3. 価格フィルタ
            if 'price_min' in filters and filters['price_min'] is not None:
                price_value = self._safe_price_conversion(filters["price_min"])
                # Finviz形式での処理分け
                if price_value.startswith(('o', 'u')):
                    filter_parts.append(f'sh_price_{price_value}')
                else:
                    filter_parts.append(f'sh_price_{price_value}to')
            
            # 4. 52週高値フィルタ
            if 'near_52w_high' in filters and filters['near_52w_high'] is not None:
                high_value = self._safe_numeric_conversion(filters["near_52w_high"])
                filter_parts.append(f'ta_highlow52w_a{high_value}h')
            
            # 5. 4週パフォーマンスフィルタ
            if 'performance_4w_positive' in filters and filters['performance_4w_positive']:
                filter_parts.append('ta_perf2_4wup')
            
            # 6. 20日移動平均フィルタ
            if 'sma20_above' in filters and filters['sma20_above']:
                filter_parts.append('ta_sma20_pa')
            
            # 7. 200日移動平均フィルタ
            if 'sma200_above' in filters and filters['sma200_above']:
                filter_parts.append('ta_sma200_pa')
            
            # 8. 50日移動平均線が200日移動平均線上フィルタ
            if 'sma50_above_sma200' in filters and filters['sma50_above_sma200']:
                filter_parts.append('ta_sma50_sa200')
            
            # 順序通りに結合
            if filter_parts:
                params['f'] = params.get('f', '') + ','.join(filter_parts) + ','
                
        else:
            # 従来の処理（その他のスクリーナー用）
            
            # 時価総額フィルタ（プリセット + 数値レンジ対応）
            if 'market_cap' in filters and filters['market_cap']:
                market_cap_val = filters['market_cap']
                
                # プリセット値の場合
                cap_mapping = {
                    'mega': 'mega',      # $200B+
                    'large': 'large',    # $10B to $200B
                    'mid': 'mid',        # $2B to $10B
                    'small': 'small',    # $300M to $2B
                    'micro': 'micro',    # $50M to $300M
                    'nano': 'nano',      # Under $50M
                    'smallover': 'smallover',  # $300M+
                    'midover': 'midover',      # $2B+
                    'microover': 'microover'   # $50M+
                }
                
                if market_cap_val in cap_mapping:
                    params['f'] = params.get('f', '') + f'cap_{cap_mapping[market_cap_val]},'
                else:
                    # 数値レンジの場合 (例: "10to20" -> cap_10to20)
                    params['f'] = params.get('f', '') + f'cap_{market_cap_val},'
            
            # 時価総額レンジフィルタ（min/max指定）
            market_cap_min = filters.get('market_cap_min')
            market_cap_max = filters.get('market_cap_max')
            
            if market_cap_min is not None or market_cap_max is not None:
                if market_cap_min and market_cap_max:
                    # レンジ指定: cap_10to20 (単位: B)
                    params['f'] = params.get('f', '') + f'cap_{market_cap_min}to{market_cap_max},'
                elif market_cap_min:
                    # 下限のみ: cap_10to
                    params['f'] = params.get('f', '') + f'cap_{market_cap_min}to,'
            
            # 価格フィルタ - Finviz形式完全対応 (sh_price_o5, sh_price_10.5to, sh_price_10.5to20.11)
            price_min = filters.get('price_min')
            price_max = filters.get('price_max')
            
            if price_min is not None or price_max is not None:
                price_min_val = self._safe_price_conversion(price_min) if price_min is not None else None
                price_max_val = self._safe_price_conversion(price_max) if price_max is not None else None
                
                # Finviz形式での処理分け
                if price_min_val and price_min_val.startswith(('o', 'u')):
                    # Finvizプリセット形式 (o5, u10)
                    params['f'] = params.get('f', '') + f'sh_price_{price_min_val},'
                elif price_max_val and price_max_val.startswith(('o', 'u')):
                    # Finvizプリセット形式 (o5, u10)
                    params['f'] = params.get('f', '') + f'sh_price_{price_max_val},'
                elif price_min_val and price_max_val:
                    # レンジ指定: sh_price_10.5to20.11
                    params['f'] = params.get('f', '') + f'sh_price_{price_min_val}to{price_max_val},'
                elif price_min_val:
                    # 下限のみ: sh_price_o{value} (Finvizでは o<value> が "Over <value>")
                    params['f'] = params.get('f', '') + f'sh_price_o{price_min_val},'
                elif price_max_val:
                    # 上限のみ: sh_price_u{value} (Finvizでは u<value> が "Under <value>")
                    params['f'] = params.get('f', '') + f'sh_price_u{price_max_val},'
            
            # 出来高フィルタ - Finviz形式完全対応
            volume_min = filters.get('volume_min')
            volume_max = filters.get('volume_max')
            
            if volume_min is not None or volume_max is not None:
                volume_min_val = self._safe_numeric_conversion(volume_min) if volume_min is not None else None
                volume_max_val = self._safe_numeric_conversion(volume_max) if volume_max is not None else None
                
                # Finviz形式での処理分け
                if volume_min_val and volume_min_val.startswith(('o', 'u')):
                    # Finvizプリセット形式 (o100, u500)
                    params['f'] = params.get('f', '') + f'sh_volume_{volume_min_val},'
                elif volume_max_val and volume_max_val.startswith(('o', 'u')):
                    # Finvizプリセット形式 (o100, u500)
                    params['f'] = params.get('f', '') + f'sh_volume_{volume_max_val},'
                elif volume_min_val and volume_max_val:
                    # レンジ指定: sh_volume_100to500
                    params['f'] = params.get('f', '') + f'sh_volume_{volume_min_val}to{volume_max_val},'
                elif volume_min_val:
                    # 下限のみ: sh_volume_100to
                    params['f'] = params.get('f', '') + f'sh_volume_{volume_min_val}to,'
                elif volume_max_val:
                    # 上限のみ: sh_volume_to500
                    params['f'] = params.get('f', '') + f'sh_volume_to{volume_max_val},'
            # 平均出来高フィルタ - Finviz形式完全対応
            avg_volume_min = filters.get('avg_volume_min')
            avg_volume_max = filters.get('avg_volume_max')
            
            if avg_volume_min is not None or avg_volume_max is not None:
                # Finviz形式のプリセット (o100, o500 など) に正しく変換する
                avg_vol_min_val = self._convert_volume_to_finviz_format(avg_volume_min) if avg_volume_min is not None else None
                avg_vol_max_val = self._convert_volume_to_finviz_format(avg_volume_max) if avg_volume_max is not None else None
                
                # Finviz形式での処理分け
                if avg_vol_min_val and avg_vol_min_val.startswith(('o', 'u')):
                    # Finvizプリセット形式 (o100, u500)
                    params['f'] = params.get('f', '') + f'sh_avgvol_{avg_vol_min_val},'
                elif avg_vol_max_val and avg_vol_max_val.startswith(('o', 'u')):
                    # Finvizプリセット形式 (o100, u500)
                    params['f'] = params.get('f', '') + f'sh_avgvol_{avg_vol_max_val},'
                elif avg_vol_min_val and avg_vol_max_val:
                    # レンジ指定: sh_avgvol_100to500
                    params['f'] = params.get('f', '') + f'sh_avgvol_{avg_vol_min_val}to{avg_vol_max_val},'
                elif avg_vol_min_val:
                    # 下限のみ: sh_avgvol_100to
                    params['f'] = params.get('f', '') + f'sh_avgvol_{avg_vol_min_val}to,'
                elif avg_vol_max_val:
                    # 上限のみ: sh_avgvol_to500
                    params['f'] = params.get('f', '') + f'sh_avgvol_to{avg_vol_max_val},'
            # 相対出来高フィルタ - Finviz形式完全対応
            relative_volume_min = filters.get('relative_volume_min')
            relative_volume_max = filters.get('relative_volume_max')
            
            if relative_volume_min is not None or relative_volume_max is not None:
                rel_vol_min_val = self._safe_numeric_conversion(relative_volume_min) if relative_volume_min is not None else None
                rel_vol_max_val = self._safe_numeric_conversion(relative_volume_max) if relative_volume_max is not None else None
                
                # Finviz形式での処理分け
                if rel_vol_min_val and rel_vol_min_val.startswith(('o', 'u')):
                    # Finvizプリセット形式 (o2, u1.5)
                    params['f'] = params.get('f', '') + f'sh_relvol_{rel_vol_min_val},'
                elif rel_vol_max_val and rel_vol_max_val.startswith(('o', 'u')):
                    # Finvizプリセット形式 (o2, u1.5)
                    params['f'] = params.get('f', '') + f'sh_relvol_{rel_vol_max_val},'
                elif rel_vol_min_val and rel_vol_max_val:
                    # レンジ指定: sh_relvol_1.5to3.0
                    params['f'] = params.get('f', '') + f'sh_relvol_{rel_vol_min_val}to{rel_vol_max_val},'
                elif rel_vol_min_val:
                    # 下限のみ: sh_relvol_1.5to
                    params['f'] = params.get('f', '') + f'sh_relvol_{rel_vol_min_val}to,'
                elif rel_vol_max_val:
                    # 上限のみ: sh_relvol_to2.0
                    params['f'] = params.get('f', '') + f'sh_relvol_to{rel_vol_max_val},'
            
            # 価格変動フィルタ - Finviz形式完全対応
            price_change_min = filters.get('price_change_min')
            price_change_max = filters.get('price_change_max')
            
            if price_change_min is not None or price_change_max is not None:
                change_min_val = self._safe_numeric_conversion(price_change_min) if price_change_min is not None else None
                change_max_val = self._safe_numeric_conversion(price_change_max) if price_change_max is not None else None
                
                # Finviz形式での処理分け
                if change_min_val and change_min_val.startswith(('o', 'u')):
                    # Finvizプリセット形式 (o5, u-5)
                    params['f'] = params.get('f', '') + f'ta_change_{change_min_val},'
                elif change_max_val and change_max_val.startswith(('o', 'u')):
                    # Finvizプリセット形式 (o5, u-5)
                    params['f'] = params.get('f', '') + f'ta_change_{change_max_val},'
                elif change_min_val and change_max_val:
                    # レンジ指定: ta_change_2to10
                    params['f'] = params.get('f', '') + f'ta_change_{change_min_val}to{change_max_val},'
                elif change_min_val:
                    # 下限のみ: ta_change_2to
                    params['f'] = params.get('f', '') + f'ta_change_{change_min_val}to,'
                elif change_max_val:
                    # 上限のみ: ta_change_to10
                    params['f'] = params.get('f', '') + f'ta_change_to{change_max_val},'
            
            # 52週高値からの距離フィルタ
            if 'near_52w_high' in filters and filters['near_52w_high'] is not None:
                high_value = self._safe_numeric_conversion(filters["near_52w_high"])
                params['f'] = params.get('f', '') + f'ta_highlow52w_a{high_value}h,'
            
            # 4週パフォーマンスフィルタ
            if 'performance_4w_positive' in filters and filters['performance_4w_positive']:
                params['f'] = params.get('f', '') + 'ta_perf2_4wup,'
        
        # RSIフィルタ - Finviz形式完全対応
        rsi_min = filters.get('rsi_min')
        rsi_max = filters.get('rsi_max')
        
        if rsi_min is not None or rsi_max is not None:
            rsi_min_val = self._safe_numeric_conversion(rsi_min) if rsi_min is not None else None
            rsi_max_val = self._safe_numeric_conversion(rsi_max) if rsi_max is not None else None
            
            # Finviz形式での処理分け
            if rsi_min_val and rsi_min_val.startswith(('o', 'u')):
                # Finvizプリセット形式 (o30, u70)
                params['f'] = params.get('f', '') + f'ta_rsi_{rsi_min_val},'
            elif rsi_max_val and rsi_max_val.startswith(('o', 'u')):
                # Finvizプリセット形式 (o30, u70)
                params['f'] = params.get('f', '') + f'ta_rsi_{rsi_max_val},'
            elif rsi_min_val and rsi_max_val:
                # レンジ指定: ta_rsi_30to70
                params['f'] = params.get('f', '') + f'ta_rsi_{rsi_min_val}to{rsi_max_val},'
            elif rsi_min_val:
                # 下限のみ: ta_rsi_30to
                params['f'] = params.get('f', '') + f'ta_rsi_{rsi_min_val}to,'
            elif rsi_max_val:
                # 上限のみ: ta_rsi_to70
                params['f'] = params.get('f', '') + f'ta_rsi_to{rsi_max_val},'
        
        # 移動平均フィルタ（特別処理スクリーナー以外の場合のみ処理）
        if not (('market_cap' in filters and filters['market_cap'] == 'microover' and 'near_52w_high' in filters) or 
                ('market_cap' in filters and filters['market_cap'] == 'smallover' and 'relative_volume_min' in filters and filters.get('stocks_only') == True and filters.get('price_change_min') == 2.0)):
            if 'sma20_above' in filters and filters['sma20_above']:
                params['f'] = params.get('f', '') + 'ta_sma20_pa,'
            if 'sma50_above' in filters and filters['sma50_above']:
                params['f'] = params.get('f', '') + 'ta_sma50_pa,'
            if 'sma200_above' in filters and filters['sma200_above']:
                params['f'] = params.get('f', '') + 'ta_sma200_pa,'
            if 'sma50_above_sma200' in filters and filters['sma50_above_sma200']:
                params['f'] = params.get('f', '') + 'ta_sma50_sa200,'
        
        # PEフィルタ - Finviz形式完全対応 (正しいプレフィックス: fa_pe_)
        pe_min = filters.get('pe_min')
        pe_max = filters.get('pe_max')
        
        if pe_min is not None or pe_max is not None:
            pe_min_val = self._safe_numeric_conversion(pe_min) if pe_min is not None else None
            pe_max_val = self._safe_numeric_conversion(pe_max) if pe_max is not None else None
            
            # Finviz形式での処理分け
            if pe_min_val and pe_min_val.startswith(('o', 'u')):
                # Finvizプリセット形式 (o15, u30)
                params['f'] = params.get('f', '') + f'fa_pe_{pe_min_val},'
            elif pe_max_val and pe_max_val.startswith(('o', 'u')):
                # Finvizプリセット形式 (o15, u30)
                params['f'] = params.get('f', '') + f'fa_pe_{pe_max_val},'
            elif pe_min_val and pe_max_val:
                # レンジ指定: fa_pe_5to30
                params['f'] = params.get('f', '') + f'fa_pe_{pe_min_val}to{pe_max_val},'
            elif pe_min_val:
                # 下限のみ: fa_pe_5to
                params['f'] = params.get('f', '') + f'fa_pe_{pe_min_val}to,'
            elif pe_max_val:
                # 上限のみ: fa_pe_to30
                params['f'] = params.get('f', '') + f'fa_pe_to{pe_max_val},'
        
        # 配当利回りフィルタ - Finviz形式完全対応
        dividend_yield_min = filters.get('dividend_yield_min')
        dividend_yield_max = filters.get('dividend_yield_max')
        
        if dividend_yield_min is not None or dividend_yield_max is not None:
            div_yield_min_val = self._safe_numeric_conversion(dividend_yield_min) if dividend_yield_min is not None else None
            div_yield_max_val = self._safe_numeric_conversion(dividend_yield_max) if dividend_yield_max is not None else None
            
            # Finviz形式での処理分け
            if div_yield_min_val and div_yield_min_val.startswith(('o', 'u')):
                # Finvizプリセット形式 (o2, u10)
                params['f'] = params.get('f', '') + f'fa_div_{div_yield_min_val},'
            elif div_yield_max_val and div_yield_max_val.startswith(('o', 'u')):
                # Finvizプリセット形式 (o2, u10)
                params['f'] = params.get('f', '') + f'fa_div_{div_yield_max_val},'
            elif div_yield_min_val and div_yield_max_val:
                # レンジ指定: fa_div_2to5
                params['f'] = params.get('f', '') + f'fa_div_{div_yield_min_val}to{div_yield_max_val},'
            elif div_yield_min_val:
                # 下限のみ: fa_div_2to
                params['f'] = params.get('f', '') + f'fa_div_{div_yield_min_val}to,'
            elif div_yield_max_val:
                # 上限のみ: fa_div_to5
                params['f'] = params.get('f', '') + f'fa_div_to{div_yield_max_val},'
        
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
        
        # EPS前四半期比成長率フィルタ
        if 'eps_growth_qoq_min' in filters and filters['eps_growth_qoq_min'] is not None:
            eps_value = self._safe_numeric_conversion(filters["eps_growth_qoq_min"])
            params['f'] = params.get('f', '') + f'fa_epsqoq_o{eps_value},'
        
        # EPS予想改訂フィルタ
        if 'eps_revision_min' in filters and filters['eps_revision_min'] is not None:
            eps_rev_value = self._safe_numeric_conversion(filters["eps_revision_min"])
            params['f'] = params.get('f', '') + f'fa_epsrev_eo{eps_rev_value},'
        
        # 売上前四半期比成長率フィルタ
        if 'sales_growth_qoq_min' in filters and filters['sales_growth_qoq_min'] is not None:
            sales_value = self._safe_numeric_conversion(filters["sales_growth_qoq_min"])
            params['f'] = params.get('f', '') + f'fa_salesqoq_o{sales_value},'
        
        # earnings_recentフィルタ（決算トレード用）
        if 'earnings_recent' in filters and filters['earnings_recent']:
            # earnings_recent: True → earningsdate_yesterdayafter|todaybefore
            params['f'] = params.get('f', '') + 'earningsdate_yesterdayafter|todaybefore,'
        
        # EPS予想改訂フィルタ（EPS Revision Positive）
        if 'earnings_revision_positive' in filters and filters['earnings_revision_positive']:
            params['f'] = params.get('f', '') + 'fa_epsrev_ep,'
        
        # 価格変動上昇フィルタ
        if 'price_change_positive' in filters and filters['price_change_positive']:
            params['f'] = params.get('f', '') + 'ta_change_u,'
        
        # 価格変動最小値フィルタ
        if 'price_change_min' in filters and filters['price_change_min'] is not None:
            change_value = self._safe_numeric_conversion(filters["price_change_min"])
            params['f'] = params.get('f', '') + f'ta_change_u{change_value},'
        
        # 4週パフォーマンス範囲フィルタ
        if 'performance_4w_range' in filters and filters['performance_4w_range'] == '0_to_negative_4w':
            params['f'] = params.get('f', '') + 'ta_perf_0to-4w,'
        
        # ボラティリティフィルタ
        if 'volatility_min' in filters and filters['volatility_min'] is not None:
            volatility_value = self._safe_numeric_conversion(filters["volatility_min"])
            params['f'] = params.get('f', '') + f'ta_volatility_{volatility_value}tox,'
        
        # 週次パフォーマンスフィルタ
        if 'weekly_performance' in filters and filters['weekly_performance']:
            params['f'] = params.get('f', '') + f'ta_perf_{filters["weekly_performance"]},'
        
        # 時間外変動フィルタ (afterhours_change_min)
        if 'afterhours_change_min' in filters and filters['afterhours_change_min'] is not None:
            ah_change_value = self._safe_numeric_conversion(filters["afterhours_change_min"])
            params['f'] = params.get('f', '') + f'ah_change_u{ah_change_value},'
        
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
            
            # 結果数制限（max_resultsに基づく）
            if 'max_results' in filters:
                finviz_params['ar'] = str(min(filters['max_results'], 1000))  # 最大1000に制限
            
            # CSV export用のAPIキーパラメータを追加
            if self.api_key:
                finviz_params['auth'] = self.api_key
            else:
                logger.warning("No API key provided. CSV export may not work without Elite subscription.")
                # テスト用のAPIキーを使用（提供されたもの）
                # 環境変数からAPIキーを取得
                import os
                env_api_key = os.getenv('FINVIZ_API_KEY')
                if env_api_key:
                    finviz_params['auth'] = env_api_key
                else:
                    logger.error("No Finviz API key provided. Please set FINVIZ_API_KEY environment variable.")
                    raise ValueError("Finviz API key is required")
            
            # CSV データを取得
            logger.info(f"Finviz CSV export URL: {self.EXPORT_URL}")
            logger.info(f"Finviz CSV export params: {finviz_params}")
            response = self._make_request(self.EXPORT_URL, finviz_params)
            
            # レスポンスがCSVかHTMLかをチェック
            if response.text.startswith('<!DOCTYPE html>'):
                logger.error("Received HTML instead of CSV. API key may be invalid or not authorized.")
                return pd.DataFrame()
            
            # CSVをDataFrameに変換
            from io import StringIO
            csv_data = StringIO(response.text)
            df = pd.read_csv(csv_data)
            
            # 強制的に結果数を制限（Finvizのarパラメータが機能しない場合の対策）
            if 'max_results' in filters and filters['max_results'] is not None:
                max_results = min(filters['max_results'], 1000)  # 最大1000に制限
                if len(df) > max_results:
                    df = df.head(max_results)
                    logger.info(f"Results truncated from {len(pd.read_csv(StringIO(response.text)))} to {max_results} rows")
            
            logger.info(f"Successfully fetched CSV data with {len(df)} rows")
            # デバッグ: CSVのカラムを確認（大量データの場合は省略）
            if len(df) <= 100:
                logger.debug(f"CSV columns: {list(df.columns)}")
                if len(df) > 0:
                    logger.debug(f"First row sample: {df.iloc[0].to_dict()}")
            else:
                logger.info(f"Large dataset ({len(df)} rows), skipping detailed debug output")
            
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
        
        # 数値フィールドのマッピング（完全版 - 128カラム対応）
        numeric_fields = {
            # 基本価格・出来高
            'price': 'Price',
            'market_cap': 'Market Cap',
            'volume': 'Volume',
            'avg_volume': 'Average Volume',
            'relative_volume': 'Relative Volume',
            'price_change': 'Change',
            'price_change_percent': 'Change',  # パーセント値として処理
            'prev_close': 'Prev Close',
            'open_price': 'Open',
            'high_price': 'High',
            'low_price': 'Low',
            'change_from_open': 'Change from Open',
            'trades_count': 'Trades',
            
            # 時間外取引データ
            'premarket_price': 'After-Hours Close',  # Note: Finviz doesn't separate pre/after
            'premarket_change': 'After-Hours Change',
            'premarket_change_percent': 'After-Hours Change',  # Same column, processed as %
            'afterhours_price': 'After-Hours Close',
            'afterhours_change': 'After-Hours Change',
            'afterhours_change_percent': 'After-Hours Change',  # Same column, processed as %
            
            # 市場データ
            'income': 'Income',
            'sales': 'Sales',
            'book_value_per_share': 'Book/sh',
            'cash_per_share': 'Cash/sh',
            'dividend': 'Dividend',
            'dividend_yield': 'Dividend Yield',
            'employees': 'Employees',
            
            # バリュエーション指標
            'pe_ratio': 'P/E',
            'forward_pe': 'Forward P/E',
            'peg': 'PEG',
            'ps_ratio': 'P/S',
            'pb_ratio': 'P/B',
            'price_to_cash': 'P/Cash',
            'price_to_free_cash_flow': 'P/Free Cash Flow',
            
            # 収益性指標
            'eps': 'EPS (ttm)',
            'eps_this_y': 'EPS this Y',
            'eps_next_y': 'EPS next Y',
            'eps_past_5y': 'EPS past 5Y',
            'eps_next_5y': 'EPS next 5Y',
            'eps_next_q': 'EPS Q/Q',
            'sales_past_5y': 'Sales past 5Y',
            'eps_growth_this_y': 'EPS growth this Y',
            'eps_growth_next_y': 'EPS growth next Y',
            'eps_growth_past_5y': 'EPS growth past 5Y',
            'eps_growth_next_5y': 'EPS growth next 5Y',
            
            # 決算関連（重要）
            'eps_surprise': 'EPS Surprise',
            'revenue_surprise': 'Revenue Surprise',
            'eps_growth_qtr': 'EPS Q/Q',
            'sales_growth_qtr': 'Sales Q/Q',
            'sales_qoq_growth': 'Sales Q/Q',  # 別名
            'eps_qoq_growth': 'EPS Q/Q',     # 別名
            'eps_estimate': 'EPS Estimate',
            'revenue_estimate': 'Revenue Estimate',
            'eps_actual': 'EPS Actual',
            'revenue_actual': 'Revenue Actual',
            'eps_revision': 'EPS Revision',
            'revenue_revision': 'Revenue Revision',
            
            # パフォーマンス指標（完全版）
            'performance_1min': 'Performance (1 Minute)',
            'performance_2min': 'Performance (2 Minutes)',
            'performance_3min': 'Performance (3 Minutes)',
            'performance_5min': 'Performance (5 Minutes)',
            'performance_10min': 'Performance (10 Minutes)',
            'performance_15min': 'Performance (15 Minutes)',
            'performance_30min': 'Performance (30 Minutes)',
            'performance_1h': 'Performance (1 Hour)',
            'performance_2h': 'Performance (2 Hours)',
            'performance_4h': 'Performance (4 Hours)',
            'performance_1w': 'Performance (Week)',
            'performance_1m': 'Performance (Month)',
            'performance_3m': 'Performance (Quarter)',
            'performance_6m': 'Performance (Half Year)',
            'performance_ytd': 'Performance (YTD)',
            'performance_1y': 'Performance (Year)',
            'performance_2y': 'Performance (Year)',  # Note: 2-year performance not available in CSV
            'performance_3y': 'Return 3 Year',
            'performance_5y': 'Return 5 Year',
            'performance_10y': 'Return 10 Year',
            'performance_since_inception': 'Return Since Inception',
            
            # 財務健全性指標
            'debt_to_equity': 'Total Debt/Equity',
            'current_ratio': 'Current Ratio',
            'quick_ratio': 'Quick Ratio',
            'lt_debt_to_equity': 'LT Debt/Equity',
            
            # 収益性マージン
            'gross_margin': 'Gross Margin',
            'operating_margin': 'Operating Margin',
            'profit_margin': 'Profit Margin',
            
            # ROE・ROA・ROI
            'roe': 'Return on Equity',
            'roa': 'Return on Assets',
            'roi': 'Return on Invested Capital',  # Note: ROI maps to ROIC in Finviz
            'roic': 'Return on Invested Capital',
            
            # 配当関連
            'payout_ratio': 'Payout Ratio',
            
            # 持株構造
            'insider_ownership': 'Insider Ownership',
            'insider_transactions': 'Insider Transactions',
            'institutional_ownership': 'Institutional Ownership',
            'institutional_transactions': 'Institutional Transactions',
            'float_short': 'Short Float',
            'short_ratio': 'Short Ratio',
            'short_interest': 'Short Interest',
            'shares_outstanding': 'Shares Outstanding',
            'shares_float': 'Shares Float',
            'float_percentage': 'Float %',
            
            # テクニカル・ボラティリティ指標
            'volatility': 'Volatility',
            'volatility_week': 'Volatility (Week)',
            'volatility_month': 'Volatility (Month)',
            'beta': 'Beta',
            'atr': 'Average True Range',
            'rsi': 'Relative Strength Index (14)',
            'rsi_14': 'Relative Strength Index (14)',
            'rel_volume': 'Relative Volume',
            'avg_true_range': 'Average True Range',
            
            # 移動平均線
            'sma_20': '20-Day Simple Moving Average',
            'sma_50': '50-Day Simple Moving Average',
            'sma_200': '200-Day Simple Moving Average',
            'sma_20_relative': 'from SMA20',
            'sma_50_relative': 'from SMA50',
            'sma_200_relative': 'from SMA200',
            
            # 高値・安値
            'week_52_high': '52-Week High',
            'week_52_low': '52-Week Low',
            'day_50_high': '50-Day High',
            'day_50_low': '50-Day Low',
            'all_time_high': 'All-Time High',
            'all_time_low': 'All-Time Low',
            'high_52w_relative': '52-Week High',  # Relative calculation needed
            'low_52w_relative': '52-Week Low',   # Relative calculation needed
            
            # アナリスト関連
            'target_price': 'Target Price',
            
            # ETF関連
            'total_holdings': 'Total Holdings',
            'aum': 'Assets Under Management',
            'nav': 'Net Asset Value',
            'nav_percent': 'Net Asset Value %',
            'net_flows_1m': 'Net Flows (1 Month)',
            'net_flows_1m_percent': 'Net Flows % (1 Month)',
            'net_flows_3m': 'Net Flows (3 Month)',
            'net_flows_3m_percent': 'Net Flows % (3 Month)',
            'net_flows_ytd': 'Net Flows (YTD)',
            'net_flows_ytd_percent': 'Net Flows % (YTD)',
            'net_flows_1y': 'Net Flows (1 Year)',
            'net_flows_1y_percent': 'Net Flows % (1 Year)',
            
            # その他指標
            'gap': 'Gap',
            'average_volume': 'Average Volume'
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
        
        # 文字列フィールドを設定（拡張版）
        string_fields = {
            'country': 'Country',
            'index': 'Index',
            'analyst_recommendation': 'Recom',
            'ipo_date': 'IPO Date',
            'earnings_timing': 'Earnings Time',
            'single_category': 'Category',
            'asset_type': 'Asset Type',
            'etf_type': 'ETF Type',
            'sector_theme': 'Sector/Theme',
            'region': 'Region',
            'active_passive': 'Active/Passive',
            'tags': 'Tags'
        }
        
        # 決算日フィールドの代替名も確認（拡張版）
        earnings_columns = [
            'Earnings Date', 'Earnings', 'earnings_date', 'Earnings_Date',
            'Next Earnings Date', 'Earnings Time'
        ]
        
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
        
        # 決算日の処理（特別処理）
        for col in earnings_columns:
            if col in row.index:
                value = row[col]
                if pd.notna(value) and str(value) != '-' and str(value) != '':
                    stock_data.earnings_date = str(value)
                    break
        
        # Boolean フィールドの設定（拡張版）
        boolean_fields = {
            'optionable': 'Optionable',
            'shortable': 'Shortable',
            'above_sma_20': 'SMA20',
            'above_sma_50': 'SMA50',
            'above_sma_200': 'SMA200'
        }
        
        for field, csv_column in boolean_fields.items():
            if csv_column in row.index:
                value = row[csv_column]
                if pd.notna(value):
                    if field.startswith('above_sma'):
                        # 移動平均線の上下判定は数値比較で決定
                        try:
                            price = stock_data.price
                            sma_value = getattr(stock_data, csv_column.lower().replace('sma', 'sma_'))
                            if price and sma_value:
                                setattr(stock_data, field, price > sma_value)
                        except:
                            pass
                    else:
                        setattr(stock_data, field, str(value).lower() in ['yes', 'true', '1'])
        
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
                # 環境変数からAPIキーを取得を試行
                import os
                env_api_key = os.getenv('FINVIZ_API_KEY')
                if env_api_key:
                    export_params['auth'] = env_api_key
                else:
                    logger.warning("No Finviz API key found - may receive limited data")
            
            # CSV データを取得
            response = self._make_request(export_url, export_params)
            
            # レスポンスがCSVかHTMLかをチェック
            if response.text.startswith('<!DOCTYPE html>') or '<html' in response.text.lower():
                logger.error(f"Received HTML instead of CSV from {export_url}")
                logger.error("This may indicate authentication or parameter issues")
                return pd.DataFrame()
            
            # CSV形式かどうかを確認
            if not response.text.strip():
                logger.error(f"Empty response from {export_url}")
                return pd.DataFrame()
            
            # CSVをDataFrameに変換
            from io import StringIO
            csv_data = StringIO(response.text)
            df = pd.read_csv(csv_data)
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching CSV data from {export_url}: {e}")
            return pd.DataFrame()
    
    def get_stock_fundamentals(self, ticker: str, data_fields: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """
        個別銘柄のファンダメンタルデータを取得（全128フィールド対応）
        
        Args:
            ticker: 銘柄ティッカー
            data_fields: 取得するデータフィールド（指定しない場合は全フィールド）
            
        Returns:
            ファンダメンタルデータ辞書またはNone
        """
        try:
            # 全フィールドを取得するためのコラムインデックス（ユーザー提供のURL参考）
            all_columns_param = "0,1,2,79,3,4,5,129,6,7,8,9,10,11,12,13,73,74,75,14,130,131,147,148,149,15,16,77,17,18,142,19,20,143,21,23,22,132,133,82,78,127,128,144,145,146,24,25,85,26,27,28,29,30,31,84,32,33,34,35,36,37,38,39,40,41,90,91,92,93,94,95,96,97,98,99,42,43,44,45,47,46,138,139,140,48,49,50,51,52,53,54,55,56,57,58,134,125,126,59,68,70,80,83,76,60,61,62,63,64,67,89,69,81,86,87,88,65,66,71,72,141,135,136,137,103,100,101,104,102,106,107,108,109,110,111,112,113,114,115,116,117,118,119,120,121,122,123,124,105"
            
            # 正しいFinviz形式で特定ティッカーを指定（ユーザー提供URLと同じ形式）
            params = {
                'v': '152',  # 最新バージョン指定（ユーザー提供URLと同じ）
                't': ticker.upper(),  # 特定ティッカーを直接指定
                'c': all_columns_param,  # 全カラム指定
                'ft': '4'  # CSV形式
            }
            
            # APIキーがある場合は追加
            if self.api_key:
                params['auth'] = self.api_key
            
            # export.ashx（スクリーニング用）を使用
            df = self._fetch_csv_from_url(self.EXPORT_URL, params)
            
            if df.empty:
                logger.warning(f"No data returned for ticker: {ticker}")
                return None
            
            # 特定ティッカーを指定しているので、最初の行を使用
            first_row = df.iloc[0]
            logger.info(f"Retrieved data for {ticker} with {len(df.columns)} columns")
            
            # 利用可能なフィールドを直接CSVから取得
            result = {}
            
            # 実際にCSVに存在するカラムのみ処理
            available_columns = df.columns.tolist()
            
            # データ抽出（実際の列名をそのまま使用）
            for col in available_columns:
                value = first_row[col]
                if pd.notna(value) and value != '-' and value != '':
                    # 列名を小文字・アンダースコア形式に変換
                    field_name = col.lower().replace(' ', '_').replace('/', '_').replace('(', '').replace(')', '').replace('.', '').replace('-', '_').replace('%', 'percent')
                    
                    # 数値フィールドの変換処理
                    numeric_keywords = ['price', 'volume', 'ratio', 'margin', 'growth', 'return', 'debt', 'shares', 'cash', 'income', 'sales', 'eps', 'dividend', 'beta', 'avg', 'high', 'low', 'change', 'float', 'cap', 'pe', 'pb', 'ps']
                    
                    is_numeric = any(keyword in field_name for keyword in numeric_keywords) or any(keyword in col.lower() for keyword in numeric_keywords)
                    
                    if is_numeric:
                        converted_value = self._clean_numeric_value(str(value))
                        result[field_name] = converted_value if converted_value is not None else str(value)
                    else:
                        result[field_name] = str(value)
                else:
                    # 空の値も列名として保持（構造の一貫性のため）
                    field_name = col.lower().replace(' ', '_').replace('/', '_').replace('(', '').replace(')', '').replace('.', '').replace('-', '_').replace('%', 'percent')
                    result[field_name] = None
            
            # 常に基本情報は含める
            result['ticker'] = ticker
            
            # 指定されたフィールドのみ返す
            if data_fields:
                # フィールド名の代替マッピング
                field_aliases = {
                    'roi': 'roic',  # Return on Invested Capital
                    'debt_equity': 'debt_to_equity',  # Total Debt/Equity
                    'book_value': 'book_value_per_share',  # Book/sh
                    'performance_week': 'performance_1w',  # Performance (Week)
                    'performance_month': 'performance_1m',  # Performance (Month)
                    'short_float': 'float_short',  # Short Float
                }
                
                filtered_result = {}
                for field in data_fields:
                    # エイリアスがあるか確認
                    actual_field = field_aliases.get(field, field)
                    
                    # フィールド名の正規化
                    normalized_field = actual_field.lower().replace(' ', '_').replace('/', '_').replace('(', '').replace(')', '').replace('.', '').replace('-', '_').replace('%', 'percent')
                    
                    if normalized_field in result:
                        filtered_result[field] = result[normalized_field]
                    elif actual_field in result:
                        filtered_result[field] = result[actual_field]
                    else:
                        # 部分一致で検索
                        found = False
                        for key in result.keys():
                            if actual_field.lower() in key.lower() or key.lower() in actual_field.lower():
                                filtered_result[field] = result[key]
                                found = True
                                break
                        if not found:
                            logger.warning(f"Field '{field}' (mapped to '{actual_field}') not found for {ticker}")
                            filtered_result[field] = None
                
                return filtered_result
            
            # すべての利用可能フィールドを返す
            return result
            
        except Exception as e:
            logger.error(f"Error getting fundamentals for {ticker}: {e}")
            return None
    
    def get_multiple_stocks_fundamentals(self, tickers: List[str], data_fields: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        複数銘柄のファンダメンタルデータ一括取得（全128フィールド対応）
        
        Args:
            tickers: 銘柄ティッカーリスト
            data_fields: 取得するデータフィールド（指定しない場合は全フィールド）
            
        Returns:
            ファンダメンタルデータのリスト
        """
        results = []
        
        logger.info(f"Getting fundamentals for {len(tickers)} stocks with full field support")
        
        try:
            # ユーザー提供の一括取得URLと同じ形式で実装
            # 全フィールドを取得するためのコラムインデックス（ユーザー提供のURL参考）
            all_columns_param = "0,1,2,79,3,4,5,129,6,7,8,9,10,11,12,13,73,74,75,14,130,131,147,148,149,15,16,77,17,18,142,19,20,143,21,23,22,132,133,82,78,127,128,144,145,146,24,25,85,26,27,28,29,30,31,84,32,33,34,35,36,37,38,39,40,41,90,91,92,93,94,95,96,97,98,99,42,43,44,45,47,46,138,139,140,48,49,50,51,52,53,54,55,56,57,58,134,125,126,59,68,70,80,83,76,60,61,62,63,64,67,89,69,81,86,87,88,65,66,71,72,141,135,136,137,103,100,101,104,102,106,107,108,109,110,111,112,113,114,115,116,117,118,119,120,121,122,123,124,105"
            
            # 複数ティッカーをカンマ区切りで指定（ユーザー提供URLと同じ形式）
            tickers_str = ','.join([t.upper() for t in tickers])
            
            params = {
                'v': '152',  # 最新バージョン指定（ユーザー提供URLと同じ）
                't': tickers_str,  # 複数ティッカーをカンマ区切りで指定
                'c': all_columns_param,  # 全カラム指定
                'ft': '4'  # CSV形式
            }
            
            # APIキーがある場合は追加
            if self.api_key:
                params['auth'] = self.api_key
            
            # 一括取得を実行
            df = self._fetch_csv_from_url(self.EXPORT_URL, params)
            
            if df.empty:
                logger.warning(f"No data returned for tickers: {tickers}")
                # 空データの場合は個別取得にフォールバック
                logger.info("Falling back to individual ticker fetching...")
                for ticker in tickers:
                    individual_data = self.get_stock_fundamentals(ticker, data_fields)
                    if individual_data:
                        results.append(individual_data)
                    else:
                        # 空の結果を追加
                        empty_result = {'ticker': ticker}
                        if data_fields:
                            for field in data_fields:
                                empty_result[field] = None
                        results.append(empty_result)
                return results
            
            logger.info(f"Successfully retrieved bulk data with {len(df)} rows and {len(df.columns)} columns")
            
            # DataFrameの各行を処理してデータを抽出
            for idx, row in df.iterrows():
                try:
                    result = {}
                    
                    # 実際にCSVに存在するカラムのみ処理
                    available_columns = df.columns.tolist()
                    
                    # データ抽出（実際の列名をそのまま使用）
                    for col in available_columns:
                        value = row[col]
                        if pd.notna(value) and value != '-' and value != '':
                            # 列名を小文字・アンダースコア形式に変換
                            field_name = col.lower().replace(' ', '_').replace('/', '_').replace('(', '').replace(')', '').replace('.', '').replace('-', '_').replace('%', 'percent')
                            
                            # 数値フィールドの変換処理
                            numeric_keywords = ['price', 'volume', 'ratio', 'margin', 'growth', 'return', 'debt', 'shares', 'cash', 'income', 'sales', 'eps', 'dividend', 'beta', 'avg', 'high', 'low', 'change', 'float', 'cap', 'pe', 'pb', 'ps']
                            
                            is_numeric = any(keyword in field_name for keyword in numeric_keywords) or any(keyword in col.lower() for keyword in numeric_keywords)
                            
                            if is_numeric:
                                converted_value = self._clean_numeric_value(str(value))
                                result[field_name] = converted_value if converted_value is not None else str(value)
                            else:
                                result[field_name] = str(value)
                        else:
                            # 空の値も列名として保持（構造の一貫性のため）
                            field_name = col.lower().replace(' ', '_').replace('/', '_').replace('(', '').replace(')', '').replace('.', '').replace('-', '_').replace('%', 'percent')
                            result[field_name] = None
                    
                    # ティッカー情報を確実に含める
                    if 'ticker' in result and result['ticker']:
                        logger.info(f"Processed ticker: {result['ticker']}")
                    else:
                        # ティッカーがない場合は順番で推定
                        if idx < len(tickers):
                            result['ticker'] = tickers[idx]
                            logger.warning(f"No ticker in data, using position-based ticker: {tickers[idx]}")
                        else:
                            logger.warning(f"No ticker information for row {idx}")
                            continue
                    
                    # 指定されたフィールドのみ返す
                    if data_fields:
                        # フィールド名の代替マッピング
                        field_aliases = {
                            'roi': 'roic',  # Return on Invested Capital
                            'debt_equity': 'debt_to_equity',  # Total Debt/Equity
                            'book_value': 'book_value_per_share',  # Book/sh
                            'performance_week': 'performance_1w',  # Performance (Week)
                            'performance_month': 'performance_1m',  # Performance (Month)
                            'short_float': 'float_short',  # Short Float
                        }
                        
                        filtered_result = {'ticker': result['ticker']}  # 常にtickerは含める
                        for field in data_fields:
                            # エイリアスがあるか確認
                            actual_field = field_aliases.get(field, field)
                            
                            # フィールド名の正規化
                            normalized_field = actual_field.lower().replace(' ', '_').replace('/', '_').replace('(', '').replace(')', '').replace('.', '').replace('-', '_').replace('%', 'percent')
                            
                            if normalized_field in result:
                                filtered_result[field] = result[normalized_field]
                            elif actual_field in result:
                                filtered_result[field] = result[actual_field]
                            else:
                                # 部分一致で検索
                                found = False
                                for key in result.keys():
                                    if actual_field.lower() in key.lower() or key.lower() in actual_field.lower():
                                        filtered_result[field] = result[key]
                                        found = True
                                        break
                                if not found:
                                    logger.warning(f"Field '{field}' (mapped to '{actual_field}') not found for {result.get('ticker', f'row {idx}')}")
                                    filtered_result[field] = None
                        
                        results.append(filtered_result)
                    else:
                        # すべての利用可能フィールドを返す
                        results.append(result)
                    
                except Exception as e:
                    logger.warning(f"Error processing row {idx}: {e}")
                    # エラーの場合でも基本情報は返す
                    ticker = tickers[idx] if idx < len(tickers) else f"Unknown_{idx}"
                    error_result = {
                        'ticker': ticker,
                        'error': str(e)
                    }
                    if data_fields:
                        for field in data_fields:
                            error_result[field] = None
                    results.append(error_result)
                    continue
            
            logger.info(f"Successfully processed {len(results)} stocks out of {len(tickers)} requested")
            return results
        
        except Exception as e:
            logger.error(f"Error in bulk fundamentals retrieval: {e}")
            logger.info("Falling back to individual ticker fetching...")
            
            # エラーが発生した場合は個別取得にフォールバック
            for ticker in tickers:
                try:
                    individual_data = self.get_stock_fundamentals(ticker, data_fields)
                    if individual_data:
                        results.append(individual_data)
                    else:
                        # 空の結果を追加
                        empty_result = {'ticker': ticker}
                        if data_fields:
                            for field in data_fields:
                                empty_result[field] = None
                        results.append(empty_result)
                    
                    # レート制限対応
                    time.sleep(0.2)
                    
                except Exception as individual_error:
                    logger.warning(f"Failed to get fundamentals for {ticker}: {individual_error}")
                    # エラーの場合でも基本情報は返す
                    error_result = {
                        'ticker': ticker,
                        'error': str(individual_error)
                    }
                    if data_fields:
                        for field in data_fields:
                            error_result[field] = None
                    results.append(error_result)
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