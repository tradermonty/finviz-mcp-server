import pandas as pd
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import requests

from .base import FinvizClient
from ..models import SECFilingData

logger = logging.getLogger(__name__)

class FinvizSECFilingsClient(FinvizClient):
    """Finviz SECファイリングデータクライアント"""
    
    SEC_FILINGS_EXPORT_URL = f"{FinvizClient.BASE_URL}/export/latest-filings"
    
    def get_sec_filings(
        self,
        ticker: str,
        form_types: Optional[List[str]] = None,
        days_back: int = 30,
        max_results: int = 50,
        sort_by: str = "filing_date",
        sort_order: str = "desc"
    ) -> List[SECFilingData]:
        """
        指定銘柄のSECファイリングデータを取得
        
        Args:
            ticker: 銘柄ティッカー
            form_types: フォームタイプフィルタ (例: ["10-K", "10-Q", "8-K"])
            days_back: 過去何日分のファイリング
            max_results: 最大取得件数
            sort_by: ソート基準 ("filing_date", "report_date", "form")
            sort_order: ソート順序 ("asc", "desc")
            
        Returns:
            SECFilingData オブジェクトのリスト
        """
        try:
            # パラメータの構築
            # sort_byがfiling_dateの場合は、Finvizの正しいパラメータ名に変換
            finviz_sort_param = "filingDate" if sort_by == "filing_date" else sort_by
            params = {
                't': ticker,
                'o': f"-{finviz_sort_param}" if sort_order == "desc" else finviz_sort_param
            }
            
            # APIキーを追加（テスト用キーをデフォルトとして使用）
            if self.api_key:
                params['auth'] = self.api_key
            else:
                params['auth'] = '***REMOVED***'
            
            # CSVデータを取得
            response = self._make_request(self.SEC_FILINGS_EXPORT_URL, params)
            
            # CSVデータをパース
            filings_data = self._parse_sec_filings_csv(response.text, ticker)
            
            # フィルタリング
            if form_types:
                filings_data = [f for f in filings_data if f.form in form_types]
            
            # 日付フィルタリング
            cutoff_date = datetime.now() - timedelta(days=days_back)
            filings_data = [
                f for f in filings_data 
                if self._parse_date(f.filing_date) >= cutoff_date
            ]
            
            # 最大件数制限
            if max_results and max_results > 0:
                filings_data = filings_data[:max_results]
            
            logger.info(f"Retrieved {len(filings_data)} SEC filings for {ticker}")
            return filings_data
            
        except Exception as e:
            logger.error(f"Error retrieving SEC filings for {ticker}: {e}")
            return []
    
    def get_recent_filings_by_form(
        self,
        ticker: str,
        form_type: str,
        limit: int = 10
    ) -> List[SECFilingData]:
        """
        特定のフォームタイプの最新ファイリングを取得
        
        Args:
            ticker: 銘柄ティッカー
            form_type: フォームタイプ (例: "10-K", "10-Q", "8-K")
            limit: 最大取得件数
            
        Returns:
            SECFilingData オブジェクトのリスト
        """
        return self.get_sec_filings(
            ticker=ticker,
            form_types=[form_type],
            days_back=365,  # 1年分
            max_results=limit,
            sort_by="filing_date",
            sort_order="desc"
        )
    
    def get_major_filings(
        self,
        ticker: str,
        days_back: int = 90
    ) -> List[SECFilingData]:
        """
        主要フォーム（10-K, 10-Q, 8-K）のファイリングを取得
        
        Args:
            ticker: 銘柄ティッカー
            days_back: 過去何日分
            
        Returns:
            SECFilingData オブジェクトのリスト
        """
        major_forms = ["10-K", "10-Q", "8-K", "DEF 14A", "SC 13G", "SC 13D"]
        return self.get_sec_filings(
            ticker=ticker,
            form_types=major_forms,
            days_back=days_back,
            max_results=50,
            sort_by="filing_date",
            sort_order="desc"
        )
    
    def get_insider_filings(
        self,
        ticker: str,
        days_back: int = 30
    ) -> List[SECFilingData]:
        """
        インサイダー取引関連のファイリング（フォーム4等）を取得
        
        Args:
            ticker: 銘柄ティッカー
            days_back: 過去何日分
            
        Returns:
            SECFilingData オブジェクトのリスト
        """
        insider_forms = ["3", "4", "5", "11-K"]
        return self.get_sec_filings(
            ticker=ticker,
            form_types=insider_forms,
            days_back=days_back,
            max_results=30,
            sort_by="filing_date",
            sort_order="desc"
        )
    
    def _parse_sec_filings_csv(self, csv_text: str, ticker: str) -> List[SECFilingData]:
        """
        CSV形式のSECファイリングデータをパースしてSECFilingDataオブジェクトのリストに変換
        
        Args:
            csv_text: CSV形式のテキスト
            ticker: 銘柄ティッカー
            
        Returns:
            SECFilingData オブジェクトのリスト
        """
        try:
            # CSVテキストをDataFrameに変換（エラー処理を強化）
            from io import StringIO
            
            # CSVパラメータを調整してエラーを回避
            df = pd.read_csv(
                StringIO(csv_text),
                on_bad_lines='skip',  # 不正な行をスキップ
                dtype=str,  # 全てを文字列として読み込み
                na_filter=False  # NAフィルタを無効化
            )
            
            logger.info(f"Successfully parsed CSV with {len(df)} rows")
            
            filings = []
            for idx, row in df.iterrows():
                try:
                    # 安全にデータを取得（デフォルト値を設定）
                    filing_date = str(row.get('Filing Date', '')).strip()
                    report_date = str(row.get('Report Date', '')).strip()
                    form = str(row.get('Form', '')).strip()
                    description = str(row.get('Description', '')).strip()
                    filing_url = str(row.get('Filing', '')).strip()
                    document_url = str(row.get('Document', '')).strip()
                    
                    # 必須フィールドの検証
                    if not filing_date or not form:
                        logger.warning(f"Skipping row {idx}: missing required fields")
                        continue
                    
                    filing = SECFilingData(
                        ticker=ticker,
                        filing_date=filing_date,
                        report_date=report_date if report_date else filing_date,
                        form=form,
                        description=description if description else f"{form} filing",
                        filing_url=filing_url,
                        document_url=document_url
                    )
                    filings.append(filing)
                    
                except Exception as e:
                    logger.warning(f"Failed to parse filing row {idx}: {e}")
                    continue
            
            logger.info(f"Successfully parsed {len(filings)} filings for {ticker}")
            return filings
            
        except Exception as e:
            logger.error(f"Error parsing SEC filings CSV: {e}")
            # デバッグ用にCSVテキストの最初の部分をログ出力
            csv_preview = csv_text[:500] if csv_text else "Empty CSV"
            logger.debug(f"CSV preview: {csv_preview}")
            return []
    
    def _parse_date(self, date_str: str) -> datetime:
        """
        日付文字列をdatetimeオブジェクトに変換
        
        Args:
            date_str: 日付文字列
            
        Returns:
            datetime オブジェクト
        """
        try:
            # MM/DD/YY形式を想定
            return datetime.strptime(date_str, '%m/%d/%y')
        except ValueError:
            try:
                # YYYY-MM-DD形式も試す
                return datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                # パースできない場合は現在日時を返す
                logger.warning(f"Could not parse date: {date_str}")
                return datetime.now()
    
    def get_filing_summary(
        self,
        ticker: str,
        days_back: int = 90
    ) -> Dict[str, Any]:
        """
        指定期間のファイリング概要を取得
        
        Args:
            ticker: 銘柄ティッカー
            days_back: 過去何日分
            
        Returns:
            ファイリング概要の辞書
        """
        try:
            filings = self.get_sec_filings(
                ticker, 
                days_back=days_back, 
                max_results=100,
                sort_by="filing_date",
                sort_order="desc"
            )
            
            if not filings:
                return {"ticker": ticker, "total_filings": 0, "forms": {}}
            
            # フォームタイプ別集計
            form_counts = {}
            for filing in filings:
                form_type = filing.form
                if form_type not in form_counts:
                    form_counts[form_type] = 0
                form_counts[form_type] += 1
            
            # 最新ファイリング日
            latest_filing = max(filings, key=lambda x: self._parse_date(x.filing_date))
            
            summary = {
                "ticker": ticker,
                "total_filings": len(filings),
                "forms": form_counts,
                "latest_filing_date": latest_filing.filing_date,
                "latest_filing_form": latest_filing.form,
                "period_days": days_back
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating filing summary for {ticker}: {e}")
            return {"ticker": ticker, "error": str(e)}
