"""
Test script for EDGAR API Client functionality
"""

import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.finviz_client.edgar_client import EdgarAPIClient


def test_edgar_client_basic():
    """Test basic EDGAR API client functionality"""
    print("=" * 60)
    print("EDGAR API Client Test")
    print("=" * 60)
    
    try:
        # Initialize client
        client = EdgarAPIClient()
        print("✅ EDGAR API client initialized successfully")
        
        # Test company facts
        print("\n📊 Testing get_company_facts for AAPL...")
        try:
            facts = client.client.get_company_facts('AAPL')
            entity_name = facts.get('entityName', 'N/A')
            cik = facts.get('cik', 'N/A')
            print(f"   Company: {entity_name}")
            print(f"   CIK: {cik}")
            print("   ✅ Company facts retrieved successfully")
            
            # Check available facts
            fact_count = len(facts.get('facts', {}))
            print(f"   📈 Available fact taxonomies: {fact_count}")
            
        except Exception as e:
            print(f"   ❌ Error getting company facts: {e}")
        
        # Test company filings
        print("\n📄 Testing get_company_filings for AAPL...")
        try:
            filings = client.get_company_filings(
                ticker='AAPL',
                form_types=['10-K', '10-Q'],
                max_count=5
            )
            print(f"   📋 Retrieved {len(filings)} filings")
            
            if filings:
                latest = filings[0]
                print(f"   Latest filing: {latest['form']} - {latest['filing_date']}")
                print("   ✅ Company filings retrieved successfully")
            
        except Exception as e:
            print(f"   ❌ Error getting company filings: {e}")
        
        # Test document content (if filings available)
        if 'filings' in locals() and filings:
            print("\n📖 Testing document content retrieval...")
            try:
                filing = filings[0]
                content = client.get_filing_document_content(
                    ticker='AAPL',
                    accession_number=filing['accession_number'],
                    primary_document=filing['primary_document'],
                    max_length=1000  # Small length for test
                )
                
                if content.get('status') == 'success':
                    content_length = len(content.get('content', ''))
                    print(f"   📝 Document content retrieved: {content_length} characters")
                    print("   ✅ Document content retrieval successful")
                else:
                    print(f"   ⚠️ Document content retrieval failed: {content.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"   ❌ Error getting document content: {e}")
        
        print("\n" + "=" * 60)
        print("✅ EDGAR API client test completed")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ EDGAR API client test failed: {e}")


def test_company_concept():
    """Test company concept functionality"""
    print("\n📊 Testing EDGAR company concept...")
    
    try:
        client = EdgarAPIClient()
        
        concept_data = client.get_company_concept(
            ticker='AAPL',
            concept='Assets',
            taxonomy='us-gaap'
        )
        
        if 'error' not in concept_data:
            entity_name = concept_data.get('entityName', 'N/A')
            print(f"   Company: {entity_name}")
            print(f"   Concept: {concept_data.get('label', 'Assets')}")
            
            units = concept_data.get('units', {})
            unit_count = sum(len(unit_data) for unit_data in units.values())
            print(f"   📈 Total data points: {unit_count}")
            print("   ✅ Company concept retrieved successfully")
        else:
            print(f"   ❌ Error: {concept_data['error']}")
            
    except Exception as e:
        print(f"   ❌ Error testing company concept: {e}")


if __name__ == "__main__":
    test_edgar_client_basic()
    test_company_concept() 