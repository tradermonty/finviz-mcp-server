# Field Discovery Enhancement Proposal

## Overview

This document outlines a comprehensive enhancement to the Finviz MCP Server to enable dynamic field discovery capabilities for MCP clients. Currently, users must know field names in advance, which creates a poor developer experience and limits the server's usability.

## Problem Statement

### Current Limitations
- **No field enumeration**: MCP clients cannot programmatically discover available fields
- **No field documentation**: No descriptions of what each field contains
- **Manual field specification**: Users must refer to external documentation or source code
- **No schema discovery**: No way to understand field types, formats, or categories
- **Error-prone field usage**: Invalid field names result in runtime errors

### User Pain Points
1. **Discovery friction**: New users struggle to understand available data fields
2. **Documentation dependency**: Users must consult external documentation
3. **Trial-and-error approach**: Invalid field names lead to failed requests
4. **Limited introspection**: No way to explore data capabilities programmatically

## Proposed Solution

### New MCP Tools for Field Discovery

#### 1. `list_available_fields`
**Purpose**: Enumerate all available data fields

```python
@server.tool()
def list_available_fields() -> List[TextContent]:
    """
    List all available data fields for stock fundamentals.
    
    Returns:
        Complete list of field names that can be used with 
        get_stock_fundamentals and get_multiple_stocks_fundamentals
    """
```

**Sample Output**:
```
Available Data Fields (128 total):

Basic Information:
- ticker: Stock ticker symbol
- company: Company name
- sector: Business sector
- industry: Industry classification
- country: Country of incorporation

Valuation Metrics:
- pe_ratio: Price-to-Earnings ratio
- pb_ratio: Price-to-Book ratio
- dividend_yield: Annual dividend yield percentage
- payout_ratio: Dividend payout ratio
...

[Complete field listing with brief descriptions]
```

#### 2. `get_field_categories`
**Purpose**: Organize fields by functional categories

```python
@server.tool()
def get_field_categories() -> List[TextContent]:
    """
    Get available data fields organized by category.
    
    Returns:
        Fields grouped by functionality (valuation, performance, 
        technical, fundamental, etc.)
    """
```

**Sample Output**:
```
Field Categories:

📊 BASIC INFORMATION (8 fields)
- ticker, company, sector, industry, country, exchange, market_cap, employees

💰 VALUATION METRICS (12 fields)  
- pe_ratio, pb_ratio, ps_ratio, peg_ratio, dividend_yield, payout_ratio, ...

📈 PERFORMANCE METRICS (18 fields)
- performance_week, performance_month, performance_quarter, performance_year, ...

🔧 TECHNICAL INDICATORS (15 fields)
- rsi, beta, volatility, sma20, sma50, sma200, relative_volume, ...

📋 FUNDAMENTAL DATA (25 fields)
- eps_ttm, revenue, profit_margin, roe, debt_equity, current_ratio, ...

📅 EARNINGS & GROWTH (20 fields)
- eps_growth_qtr, eps_growth_this_y, sales_growth_qtr, earnings_date, ...

🏢 ETF SPECIFIC (10 fields)
- aum, expense_ratio, inception_date, fund_family, ...

📰 NEWS & SENTIMENT (8 fields)
- news_title, news_url, analyst_recom, insider_ownership, ...

🎯 TRADING DATA (12 fields)
- volume, avg_volume, float, short_interest, option_volume, ...
```

#### 3. `describe_field`
**Purpose**: Get detailed information about specific fields

```python
@server.tool()
def describe_field(field_name: str) -> List[TextContent]:
    """
    Get detailed description and metadata for a specific field.
    
    Args:
        field_name: The field name to describe
        
    Returns:
        Detailed field information including description, data type,
        format, and usage examples
    """
```

**Sample Output**:
```
Field Description: pe_ratio

📋 Basic Info:
- Name: pe_ratio
- Display Name: Price-to-Earnings Ratio
- Category: Valuation Metrics
- Data Type: Float

📖 Description:
The Price-to-Earnings ratio measures a company's current share price 
relative to its per-share earnings. It indicates how much investors 
are willing to pay per dollar of earnings.

📊 Format:
- Unit: Ratio (e.g., 15.5 means 15.5x earnings)
- Precision: 2 decimal places
- Special Values: N/A for companies with negative earnings

💡 Usage Examples:
- Low P/E (< 15): Potentially undervalued or slow growth
- High P/E (> 25): Growth expectations or overvaluation
- N/A: Company has negative earnings

🔗 Related Fields:
- forward_pe: Forward P/E ratio based on estimated earnings
- peg_ratio: P/E ratio adjusted for growth rate
- eps_ttm: Trailing twelve months earnings per share
```

#### 4. `search_fields`
**Purpose**: Search fields by keyword or pattern

```python
@server.tool()
def search_fields(keyword: str, category: Optional[str] = None) -> List[TextContent]:
    """
    Search for fields matching a keyword or pattern.
    
    Args:
        keyword: Search term (e.g., "growth", "ratio", "performance")
        category: Optional category filter
        
    Returns:
        Matching fields with descriptions
    """
```

**Sample Output**:
```
Search Results for "growth":

📈 GROWTH-RELATED FIELDS (8 matches):

eps_growth_qtr
└── EPS Growth Quarter over Quarter (%)

eps_growth_this_y  
└── EPS Growth This Year (%)

eps_growth_next_y
└── EPS Growth Next Year Estimate (%)

eps_growth_past_5y
└── EPS Growth Past 5 Years (Annual %)

sales_growth_qtr
└── Sales Growth Quarter over Quarter (%)

sales_growth_past_5y
└── Sales Growth Past 5 Years (Annual %)

dividend_growth_1_year
└── Dividend Growth Rate (1 Year %)

dividend_growth_5_years
└── Dividend Growth Rate (5 Years %)
```

#### 5. `validate_fields`
**Purpose**: Validate field names before use

```python
@server.tool()
def validate_fields(field_names: List[str]) -> List[TextContent]:
    """
    Validate a list of field names and suggest corrections.
    
    Args:
        field_names: List of field names to validate
        
    Returns:
        Validation results with suggestions for invalid fields
    """
```

**Sample Output**:
```
Field Validation Results:

✅ VALID FIELDS (6):
- ticker
- company  
- pe_ratio
- dividend_yield
- market_cap
- sector

❌ INVALID FIELDS (2):
- eps_yoy → Did you mean: eps_growth_this_y?
- sales_growth_yoy → Did you mean: sales_growth_past_5y?

💡 SUGGESTIONS:
For yearly growth metrics, use:
- eps_growth_this_y (current year EPS growth)
- eps_growth_past_5y (5-year average EPS growth)
- sales_growth_past_5y (5-year average sales growth)
```

## Implementation Plan

### Phase 1: Core Field Discovery (Week 1)
1. **Implement `list_available_fields`**
   - Extract field definitions from `FINVIZ_COMPREHENSIVE_FIELD_MAPPING`
   - Format output with categorization
   - Add basic field descriptions

2. **Implement `get_field_categories`**
   - Create field categorization logic
   - Group fields by functionality
   - Add category descriptions and icons

### Phase 2: Enhanced Discovery (Week 2)
3. **Implement `describe_field`**
   - Create detailed field metadata
   - Add usage examples and data format info
   - Include related field suggestions

4. **Implement `search_fields`**
   - Add keyword search functionality
   - Support category filtering
   - Implement fuzzy matching for better UX

### Phase 3: Validation & Polish (Week 3)
5. **Implement `validate_fields`**
   - Enhance existing validation logic
   - Add field name suggestions for typos
   - Provide helpful error messages

6. **Documentation & Testing**
   - Update README.md with new capabilities
   - Add usage examples to CLAUDE.md
   - Write comprehensive tests

## Technical Implementation Details

### Field Metadata Structure
```python
@dataclass
class FieldMetadata:
    name: str
    display_name: str
    category: str
    description: str
    data_type: str
    format_info: str
    special_values: List[str]
    related_fields: List[str]
    usage_examples: List[str]
```

### Category Definitions
```python
FIELD_CATEGORIES = {
    "basic": {
        "name": "Basic Information",
        "icon": "📊",
        "description": "Company identification and basic metrics"
    },
    "valuation": {
        "name": "Valuation Metrics", 
        "icon": "💰",
        "description": "Price ratios and valuation measures"
    },
    "performance": {
        "name": "Performance Metrics",
        "icon": "📈", 
        "description": "Historical price performance across timeframes"
    },
    # ... additional categories
}
```

### Search Implementation
- **Keyword matching**: Direct substring search in field names and descriptions
- **Fuzzy matching**: Levenshtein distance for typo tolerance
- **Category filtering**: Filter results by field category
- **Relevance scoring**: Rank results by match quality

## Benefits

### For Users
- **Improved discoverability**: Easy exploration of available data
- **Reduced learning curve**: Self-documenting API capabilities
- **Better error handling**: Proactive field validation with suggestions
- **Enhanced productivity**: No need to consult external documentation

### For Developers
- **Better API design**: Follows REST/GraphQL introspection patterns
- **Reduced support burden**: Self-service field discovery
- **Improved adoption**: Lower barrier to entry for new users
- **Future flexibility**: Easy to extend with new fields

### For the Project
- **Professional polish**: Industry-standard API introspection
- **User experience**: Significant improvement in usability
- **Documentation**: Self-documenting capabilities reduce maintenance
- **Ecosystem growth**: Easier integration with other tools

## Testing Strategy

### Unit Tests
- Field enumeration completeness
- Category organization accuracy
- Search functionality correctness
- Validation logic reliability

### Integration Tests  
- MCP tool registration verification
- Cross-tool consistency checks
- Performance with large field sets
- Error handling robustness

### User Acceptance Tests
- Discovery workflow validation
- Documentation completeness verification
- Real-world usage scenario testing
- Developer experience evaluation

## Future Enhancements

### Advanced Features
- **Field usage analytics**: Track which fields are most commonly requested
- **Smart recommendations**: Suggest field combinations based on usage patterns
- **API versioning**: Support for field deprecation and new field introduction
- **Custom field sets**: Allow users to save and reuse field combinations

### Integration Possibilities
- **IDE integration**: Autocomplete support for field names
- **Documentation generation**: Auto-generate field reference docs
- **Schema export**: Export field definitions for external tools
- **Validation plugins**: Pre-request field validation in client tools

## Conclusion

This enhancement will significantly improve the developer experience of the Finviz MCP Server by providing comprehensive field discovery capabilities. The proposed tools follow MCP best practices while addressing real user pain points around API discoverability and usability.

The implementation plan balances immediate value delivery with long-term extensibility, ensuring that these features will serve users well as the project grows and evolves.