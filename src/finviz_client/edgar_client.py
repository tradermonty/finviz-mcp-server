"""
EDGAR API Client for SEC filings document content retrieval

This module provides functionality to retrieve SEC filing document content
using the official EDGAR API instead of web scraping.
"""

import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import requests
from sec_edgar_api import EdgarClient

from ..models import SECFilingData
from ..utils.validators import validate_ticker

logger = logging.getLogger(__name__)


class EdgarAPIClient:
    """EDGAR API client for retrieving SEC filing document content"""
    
    def __init__(self, user_agent: str = "Finviz MCP Server contact@example.com"):
        """
        Initialize EDGAR API client
        
        Args:
            user_agent: User agent string for SEC API requests (required by SEC)
        """
        self.client = EdgarClient(user_agent=user_agent)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })
        
    def _get_cik_from_ticker(self, ticker: str) -> Optional[str]:
        """Get CIK from ticker using SEC company tickers JSON"""
        try:
            # Use SEC's company tickers endpoint
            response = self.session.get('https://www.sec.gov/files/company_tickers.json', timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Search for ticker in the data
            for entry in data.values():
                if entry.get('ticker', '').upper() == ticker.upper():
                    cik = str(entry.get('cik_str', '')).zfill(10)
                    logger.info(f"Found CIK {cik} for ticker {ticker}")
                    return cik
            
            logger.warning(f"CIK not found for ticker {ticker}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting CIK for ticker {ticker}: {e}")
            return None

    def get_company_filings(
        self,
        ticker: str,
        form_types: Optional[List[str]] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        max_count: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get company filings using EDGAR API
        
        Args:
            ticker: Stock ticker symbol
            form_types: List of form types to filter (e.g., ['10-K', '10-Q'])
            date_from: Start date (YYYY-MM-DD format)
            date_to: End date (YYYY-MM-DD format)
            max_count: Maximum number of filings to retrieve
            
        Returns:
            List of filing dictionaries with metadata
        """
        try:
            if not validate_ticker(ticker):
                raise ValueError(f"Invalid ticker: {ticker}")
            
            logger.info(f"Fetching filings for {ticker} via EDGAR API")
            
            # Get CIK from ticker
            cik = self._get_cik_from_ticker(ticker)
            if not cik:
                logger.error(f"Could not find CIK for ticker {ticker}")
                return []
            
            # Get submissions data
            submissions = self.client.get_submissions(cik=cik)
            if not submissions or 'filings' not in submissions:
                logger.warning(f"No submissions found for {ticker} (CIK: {cik})")
                return []
            
            recent_filings = submissions['filings']['recent']
            
            # Extract filing data
            filings = []
            forms = recent_filings.get('form', [])
            filing_dates = recent_filings.get('filingDate', [])
            report_dates = recent_filings.get('reportDate', [])
            accession_numbers = recent_filings.get('accessionNumber', [])
            primary_documents = recent_filings.get('primaryDocument', [])
            descriptions = recent_filings.get('primaryDocDescription', [])
            
            for i in range(min(len(forms), max_count)):
                form = forms[i]
                filing_date = filing_dates[i] if i < len(filing_dates) else ''
                report_date = report_dates[i] if i < len(report_dates) else ''
                accession = accession_numbers[i] if i < len(accession_numbers) else ''
                primary_doc = primary_documents[i] if i < len(primary_documents) else ''
                description = descriptions[i] if i < len(descriptions) else ''
                
                # Filter by form types if specified
                if form_types and form not in form_types:
                    continue
                
                # Filter by date range if specified
                if date_from and filing_date < date_from:
                    continue
                if date_to and filing_date > date_to:
                    continue
                
                # Construct document URL
                accession_clean = accession.replace('-', '')
                document_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_clean}/{primary_doc}"
                filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_clean}/{accession}-index.html"
                
                filing_data = {
                    'ticker': ticker,
                    'cik': cik,
                    'form': form,
                    'filing_date': filing_date,
                    'report_date': report_date,
                    'accession_number': accession,
                    'primary_document': primary_doc,
                    'description': description,
                    'document_url': document_url,
                    'filing_url': filing_url
                }
                
                filings.append(filing_data)
            
            logger.info(f"Retrieved {len(filings)} filings for {ticker}")
            return filings
            
        except Exception as e:
            logger.error(f"Error fetching EDGAR filings for {ticker}: {e}")
            return []
    
    def get_filing_document_content(
        self,
        ticker: str,
        accession_number: str,
        primary_document: str,
        max_length: int = 50000
    ) -> Dict[str, Any]:
        """
        Get SEC filing document content via EDGAR API
        
        Args:
            ticker: Stock ticker symbol
            accession_number: SEC accession number (with dashes)
            primary_document: Primary document filename
            max_length: Maximum content length to return
            
        Returns:
            Dictionary with document content and metadata
        """
        try:
            logger.info(f"Fetching document content for {ticker}: {accession_number}/{primary_document}")
            
            # Get CIK from ticker
            cik = self._get_cik_from_ticker(ticker)
            
            if not cik:
                return {
                    'content': '',
                    'metadata': {},
                    'status': 'error',
                    'error': f'Could not find CIK for ticker {ticker}'
                }
            
            # Construct document URL
            accession_clean = accession_number.replace('-', '')
            document_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_clean}/{primary_document}"
            
            # Fetch document content with rate limiting
            time.sleep(0.1)  # SEC API rate limit compliance
            response = self.session.get(document_url, timeout=30)
            response.raise_for_status()
            
            # Extract text content
            content = response.text
            
            # Apply length limit
            if len(content) > max_length:
                content = content[:max_length] + "\n\n[Content truncated due to length limit]"
            
            metadata = {
                'ticker': ticker,
                'cik': cik,
                'accession_number': accession_number,
                'primary_document': primary_document,
                'document_url': document_url,
                'content_length': len(content),
                'retrieved_at': datetime.now().isoformat()
            }
            
            logger.info(f"Successfully retrieved content: {len(content)} characters")
            
            return {
                'content': content,
                'metadata': metadata,
                'status': 'success',
                'url': document_url
            }
            
        except requests.RequestException as e:
            logger.error(f"Network error fetching document: {e}")
            return {
                'content': '',
                'metadata': {},
                'status': 'error',
                'error': f'Network error: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Error fetching document content: {e}")
            return {
                'content': '',
                'metadata': {},
                'status': 'error',
                'error': str(e)
            }
    
    def get_multiple_filing_contents(
        self,
        filings_data: List[Dict[str, str]],
        max_length: int = 20000
    ) -> List[Dict[str, Any]]:
        """
        Get content for multiple SEC filings
        
        Args:
            filings_data: List of filing data dictionaries with keys:
                         ticker, accession_number, primary_document
            max_length: Maximum content length per document
            
        Returns:
            List of content dictionaries
        """
        results = []
        
        for i, filing_data in enumerate(filings_data):
            logger.info(f"Processing filing {i+1}/{len(filings_data)}")
            
            ticker = filing_data.get('ticker')
            accession = filing_data.get('accession_number')
            primary_doc = filing_data.get('primary_document')
            
            if not all([ticker, accession, primary_doc]):
                results.append({
                    'content': '',
                    'metadata': filing_data,
                    'status': 'error',
                    'error': 'Missing required filing data fields'
                })
                continue
            
            content = self.get_filing_document_content(
                ticker=ticker,
                accession_number=accession,
                primary_document=primary_doc,
                max_length=max_length
            )
            
            results.append(content)
            
            # Rate limiting between requests
            if i < len(filings_data) - 1:
                time.sleep(0.2)
        
        return results
    
    def get_company_concept(
        self,
        ticker: str,
        concept: str,
        taxonomy: str = "us-gaap"
    ) -> Dict[str, Any]:
        """
        Get company concept data (financial metrics) via EDGAR API
        
        Args:
            ticker: Stock ticker symbol
            concept: XBRL concept (e.g., 'Assets', 'Revenues')
            taxonomy: Taxonomy ('us-gaap', 'dei', 'invest')
            
        Returns:
            Company concept data dictionary
        """
        try:
            logger.info(f"Fetching concept {concept} for {ticker}")
            
            # Get CIK from ticker
            cik = self._get_cik_from_ticker(ticker)
            
            if not cik:
                return {'error': f'Could not find CIK for ticker {ticker}'}
            
            # Get concept data
            concept_data = self.client.get_company_concept(
                cik=cik,
                taxonomy=taxonomy,
                concept=concept
            )
            
            return concept_data
            
        except Exception as e:
            logger.error(f"Error fetching concept {concept} for {ticker}: {e}")
            return {'error': str(e)} 