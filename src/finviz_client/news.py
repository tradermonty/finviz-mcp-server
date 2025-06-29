import logging
from typing import List, Optional
from datetime import datetime, timedelta

import pandas as pd

from .base import FinvizClient
from ..models import NewsData

logger = logging.getLogger(__name__)

class FinvizNewsClient(FinvizClient):
    """Finvizニュース機能専用クライアント"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
    
    def get_stock_news(self, ticker: str, days_back: int = 7, 
                      news_type: str = "all") -> List[NewsData]:
        """
        指定銘柄のニュースを取得（CSV export使用）
        
        Args:
            ticker: 銘柄ティッカー
            days_back: 過去何日分のニュース
            news_type: ニュースタイプ (all, earnings, analyst, insider, general)
            
        Returns:
            NewsData オブジェクトのリスト
        """
        try:
            params = {
                'v': '3',  # バージョンパラメータを追加
                't': ticker
            }
            
            # ニュースタイプフィルタ
            if news_type != "all":
                type_mapping = {
                    'earnings': 'earnings',
                    'analyst': 'analyst',
                    'insider': 'insider',
                    'general': 'general'
                }
                if news_type in type_mapping:
                    params['filter'] = type_mapping[news_type]
            
            # CSVからニュースデータを取得
            df = self._fetch_csv_from_url(self.NEWS_EXPORT_URL, params)
            
            if df.empty:
                logger.warning(f"No news data returned for {ticker}")
                return []
            
            # CSVデータからNewsDataオブジェクトのリストに変換
            news_list = []
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            for _, row in df.iterrows():
                try:
                    news_data = self._parse_news_from_csv(row, ticker, cutoff_date)
                    if news_data:
                        news_list.append(news_data)
                except Exception as e:
                    logger.warning(f"Failed to parse news data from CSV: {e}")
                    continue
            
            logger.info(f"Retrieved {len(news_list)} news items for {ticker}")
            return news_list
            
        except Exception as e:
            logger.error(f"Error retrieving news for {ticker}: {e}")
            return []
    
    def get_market_news(self, days_back: int = 3, max_items: int = 50) -> List[NewsData]:
        """
        市場全体のニュースを取得（CSV export使用）
        
        Args:
            days_back: 過去何日分のニュース
            max_items: 最大取得件数
            
        Returns:
            NewsData オブジェクトのリスト
        """
        try:
            params = {
                'v': '3'  # バージョンパラメータを追加
            }
            
            # CSVから市場ニュースデータを取得
            df = self._fetch_csv_from_url(self.NEWS_EXPORT_URL, params)
            
            if df.empty:
                logger.warning("No market news data returned")
                return []
            
            # CSVデータからNewsDataオブジェクトのリストに変換
            news_list = []
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            for _, row in df.iterrows():
                try:
                    news_data = self._parse_news_from_csv(row, "MARKET", cutoff_date)
                    if news_data:
                        news_list.append(news_data)
                        if len(news_list) >= max_items:
                            break
                except Exception as e:
                    logger.warning(f"Failed to parse market news data from CSV: {e}")
                    continue
            
            logger.info(f"Retrieved {len(news_list)} market news items")
            return news_list
            
        except Exception as e:
            logger.error(f"Error retrieving market news: {e}")
            return []
    
    def get_sector_news(self, sector: str, days_back: int = 5, 
                       max_items: int = 30) -> List[NewsData]:
        """
        特定セクターのニュースを取得（CSV export使用）
        
        Args:
            sector: セクター名
            days_back: 過去何日分のニュース
            max_items: 最大取得件数
            
        Returns:
            NewsData オブジェクトのリスト
        """
        try:
            params = {
                'v': '3',  # バージョンパラメータを追加
                'sec': sector.lower().replace(' ', '_')
            }
            
            # CSVからセクターニュースデータを取得
            df = self._fetch_csv_from_url(self.NEWS_EXPORT_URL, params)
            
            if df.empty:
                logger.warning(f"No news data returned for {sector} sector")
                return []
            
            # CSVデータからNewsDataオブジェクトのリストに変換
            news_list = []
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            for _, row in df.iterrows():
                try:
                    news_data = self._parse_news_from_csv(row, f"SECTOR_{sector}", cutoff_date)
                    if news_data:
                        news_list.append(news_data)
                        if len(news_list) >= max_items:
                            break
                except Exception as e:
                    logger.warning(f"Failed to parse sector news data from CSV: {e}")
                    continue
            
            logger.info(f"Retrieved {len(news_list)} news items for {sector} sector")
            return news_list
            
        except Exception as e:
            logger.error(f"Error retrieving news for {sector} sector: {e}")
            return []
    

    
    def _parse_news_date(self, date_text: str) -> Optional[datetime]:
        """
        ニュースの日付文字列を解析
        
        Args:
            date_text: 日付文字列
            
        Returns:
            datetime オブジェクトまたはNone
        """
        try:
            # Finvizの日付形式に対応
            # "Dec-29-23 08:00AM" のような形式
            date_text = date_text.strip()
            
            if not date_text:
                return None
            
            # 今日・昨日の表記
            if 'Today' in date_text or 'today' in date_text:
                return datetime.now()
            elif 'Yesterday' in date_text or 'yesterday' in date_text:
                return datetime.now() - timedelta(days=1)
            
            # 時刻のみの場合（今日の記事）
            if ':' in date_text and len(date_text) < 10:
                return datetime.now()
            
            # 標準的な日付形式の処理
            # "Dec-29-23" -> "2023-12-29"
            parts = date_text.split()
            if len(parts) >= 1:
                date_part = parts[0]
                if '-' in date_part:
                    try:
                        # "Dec-29-23" 形式
                        month_str, day_str, year_str = date_part.split('-')
                        
                        # 月名を数値に変換
                        month_mapping = {
                            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4,
                            'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8,
                            'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
                        }
                        
                        month = month_mapping.get(month_str, 1)
                        day = int(day_str)
                        year = 2000 + int(year_str) if len(year_str) == 2 else int(year_str)
                        
                        return datetime(year, month, day)
                        
                    except ValueError:
                        pass
            
            # その他の形式（デフォルトで現在時刻）
            return datetime.now()
            
        except Exception as e:
            logger.warning(f"Failed to parse date '{date_text}': {e}")
            return datetime.now()
    
    def _extract_news_source(self, element) -> str:
        """
        ニュースソースを抽出
        
        Args:
            element: BeautifulSoup element
            
        Returns:
            ソース名
        """
        try:
            # ソースの検索パターン
            source_span = element.find('span', {'class': 'news-source'})
            if source_span:
                return source_span.get_text(strip=True)
            
            # 括弧内のソース情報
            text = element.get_text()
            if '(' in text and ')' in text:
                # 最後の括弧内の文字列をソースとして取得
                parts = text.split('(')
                if len(parts) > 1:
                    source_part = parts[-1].split(')')[0]
                    return source_part.strip()
            
            return "Finviz"
            
        except Exception:
            return "Unknown"
    
    def _categorize_news(self, title: str) -> str:
        """
        ニュースタイトルからカテゴリを推定
        
        Args:
            title: ニュースタイトル
            
        Returns:
            カテゴリ名
        """
        title_lower = title.lower()
        
        # キーワードベースの分類
        if any(word in title_lower for word in ['earnings', 'revenue', 'profit', 'eps', 'guidance']):
            return 'earnings'
        elif any(word in title_lower for word in ['upgrade', 'downgrade', 'rating', 'analyst', 'target']):
            return 'analyst'
        elif any(word in title_lower for word in ['insider', 'ceo', 'cfo', 'director', 'executive']):
            return 'insider'
        elif any(word in title_lower for word in ['merger', 'acquisition', 'deal', 'buyout']):
            return 'merger'
        elif any(word in title_lower for word in ['fda', 'approval', 'clinical', 'trial']):
            return 'regulatory'
        elif any(word in title_lower for word in ['dividend', 'split', 'buyback']):
            return 'corporate_action'
        else:
            return 'general'
    
    def _parse_news_from_csv(self, row: 'pd.Series', ticker: str, cutoff_date: datetime) -> Optional[NewsData]:
        """
        CSV行からNewsDataオブジェクトを作成
        
        Args:
            row: pandasのSeries（CSV行データ）
            ticker: 対象ティッカー
            cutoff_date: カットオフ日時
            
        Returns:
            NewsData オブジェクトまたはNone
        """
        try:
            import pandas as pd
            
            # 必要なフィールドを抽出
            title = str(row.get('Title', ''))
            source = str(row.get('Source', ''))
            url = str(row.get('URL', ''))
            
            # 日時の解析
            date_str = str(row.get('Date', ''))
            news_date = self._parse_news_date_from_csv(date_str)
            
            if not news_date or news_date < cutoff_date:
                return None
            
            # カテゴリの推定
            category = self._categorize_news(title)
            
            return NewsData(
                ticker=ticker,
                title=title,
                source=source,
                date=news_date,
                url=url,
                category=category
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse news data from CSV row: {e}")
            return None
    
    def _parse_news_date_from_csv(self, date_str: str) -> Optional[datetime]:
        """
        CSV日時文字列をdatetimeオブジェクトに変換
        
        Args:
            date_str: 日時文字列
            
        Returns:
            datetime オブジェクトまたはNone
        """
        if not date_str or date_str == '-':
            return None
        
        try:
            # ISO形式の日時をパース
            if 'T' in date_str:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            
            # その他の形式をパース
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%m/%d/%Y', '%m-%d-%Y']:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            logger.warning(f"Could not parse date string: {date_str}")
            return None
            
        except Exception as e:
            logger.warning(f"Error parsing date '{date_str}': {e}")
            return None