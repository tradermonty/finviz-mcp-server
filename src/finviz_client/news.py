import logging
from typing import List, Optional
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

from .base import FinvizClient
from ..models import NewsData

logger = logging.getLogger(__name__)

class FinvizNewsClient(FinvizClient):
    """Finvizニュース機能専用クライアント"""
    
    NEWS_URL = f"{FinvizClient.BASE_URL}/news.ashx"
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
    
    def get_stock_news(self, ticker: str, days_back: int = 7, 
                      news_type: str = "all") -> List[NewsData]:
        """
        指定銘柄のニュースを取得
        
        Args:
            ticker: 銘柄ティッカー
            days_back: 過去何日分のニュース
            news_type: ニュースタイプ (all, earnings, analyst, insider, general)
            
        Returns:
            NewsData オブジェクトのリスト
        """
        try:
            params = {
                't': ticker,
                'tab': 'news'
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
            
            response = self._make_request(self.QUOTE_URL, params)
            news_list = self._parse_news_from_quote_page(response.text, ticker, days_back)
            
            logger.info(f"Retrieved {len(news_list)} news items for {ticker}")
            return news_list
            
        except Exception as e:
            logger.error(f"Error retrieving news for {ticker}: {e}")
            return []
    
    def get_market_news(self, days_back: int = 3, max_items: int = 50) -> List[NewsData]:
        """
        市場全体のニュースを取得
        
        Args:
            days_back: 過去何日分のニュース
            max_items: 最大取得件数
            
        Returns:
            NewsData オブジェクトのリスト
        """
        try:
            response = self._make_request(self.NEWS_URL)
            news_list = self._parse_market_news(response.text, days_back, max_items)
            
            logger.info(f"Retrieved {len(news_list)} market news items")
            return news_list
            
        except Exception as e:
            logger.error(f"Error retrieving market news: {e}")
            return []
    
    def get_sector_news(self, sector: str, days_back: int = 5, 
                       max_items: int = 30) -> List[NewsData]:
        """
        特定セクターのニュースを取得
        
        Args:
            sector: セクター名
            days_back: 過去何日分のニュース
            max_items: 最大取得件数
            
        Returns:
            NewsData オブジェクトのリスト
        """
        try:
            params = {
                'sec': sector.lower().replace(' ', '_')
            }
            
            response = self._make_request(self.NEWS_URL, params)
            news_list = self._parse_sector_news(response.text, sector, days_back, max_items)
            
            logger.info(f"Retrieved {len(news_list)} news items for {sector} sector")
            return news_list
            
        except Exception as e:
            logger.error(f"Error retrieving news for {sector} sector: {e}")
            return []
    
    def _parse_news_from_quote_page(self, html_content: str, ticker: str, 
                                  days_back: int) -> List[NewsData]:
        """
        株式詳細ページからニュースを解析
        
        Args:
            html_content: HTMLコンテンツ
            ticker: 銘柄ティッカー
            days_back: 過去何日分
            
        Returns:
            NewsData オブジェクトのリスト
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        news_list = []
        
        # ニュースセクションを検索
        news_section = soup.find('table', {'id': 'news-table'})
        if not news_section:
            logger.warning(f"News section not found for {ticker}")
            return []
        
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        # ニュース行を処理
        for row in news_section.find_all('tr'):
            try:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    # 日時の解析
                    date_cell = cells[0]
                    news_cell = cells[1]
                    
                    date_text = date_cell.get_text(strip=True)
                    news_date = self._parse_news_date(date_text)
                    
                    if news_date and news_date >= cutoff_date:
                        # ニュース情報の抽出
                        news_link = news_cell.find('a')
                        if news_link:
                            title = news_link.get_text(strip=True)
                            url = news_link.get('href', '')
                            
                            # 絶対URLに変換
                            if url.startswith('/'):
                                url = self.BASE_URL + url
                            
                            # ソースの抽出
                            source = self._extract_news_source(news_cell)
                            
                            # カテゴリの推定
                            category = self._categorize_news(title)
                            
                            news_data = NewsData(
                                ticker=ticker,
                                title=title,
                                source=source,
                                date=news_date,
                                url=url,
                                category=category
                            )
                            news_list.append(news_data)
                            
            except Exception as e:
                logger.warning(f"Failed to parse news row: {e}")
                continue
        
        return news_list
    
    def _parse_market_news(self, html_content: str, days_back: int, 
                          max_items: int) -> List[NewsData]:
        """
        市場ニュースページを解析
        
        Args:
            html_content: HTMLコンテンツ
            days_back: 過去何日分
            max_items: 最大取得件数
            
        Returns:
            NewsData オブジェクトのリスト
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        news_list = []
        
        # ニュースアイテムを検索
        news_items = soup.find_all('div', {'class': 'news-link-container'})
        
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        for item in news_items[:max_items]:
            try:
                # タイトルとURLの抽出
                link = item.find('a')
                if link:
                    title = link.get_text(strip=True)
                    url = link.get('href', '')
                    
                    if url.startswith('/'):
                        url = self.BASE_URL + url
                    
                    # 日時の抽出
                    date_span = item.find('span', {'class': 'news-date'})
                    if date_span:
                        date_text = date_span.get_text(strip=True)
                        news_date = self._parse_news_date(date_text)
                        
                        if news_date and news_date >= cutoff_date:
                            # ソースの抽出
                            source = self._extract_news_source(item)
                            
                            # カテゴリの推定
                            category = self._categorize_news(title)
                            
                            news_data = NewsData(
                                ticker="MARKET",  # 市場全体ニュース
                                title=title,
                                source=source,
                                date=news_date,
                                url=url,
                                category=category
                            )
                            news_list.append(news_data)
                            
            except Exception as e:
                logger.warning(f"Failed to parse market news item: {e}")
                continue
        
        return news_list
    
    def _parse_sector_news(self, html_content: str, sector: str, 
                          days_back: int, max_items: int) -> List[NewsData]:
        """
        セクターニュースページを解析
        
        Args:
            html_content: HTMLコンテンツ
            sector: セクター名
            days_back: 過去何日分
            max_items: 最大取得件数
            
        Returns:
            NewsData オブジェクトのリスト
        """
        # 市場ニュースと同様の構造と仮定
        news_list = self._parse_market_news(html_content, days_back, max_items)
        
        # セクター情報を更新
        for news in news_list:
            news.ticker = f"SECTOR_{sector.upper()}"
        
        return news_list
    
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