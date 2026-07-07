# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment Setup
```bash
# Create virtual environment with Python 3.11+
python3.11 -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate     # On Windows

# Install dependencies in development mode
pip install -e .
```

### Running the Server
```bash
# Start the MCP server (stdio mode)
finviz-mcp-server

# Alternative: Run directly with Python
python3 run_server.py

# Alternative: Run as module
python3 -m src.server
```

### Testing
```bash
# Basic functionality test
python3 test_basic.py

# All features test
python3 test_all_features.py

# Live features test (requires API access)
python3 test_live_features.py
```

### Code Quality
```bash
# Code formatting (if available)
black src/ --line-length 88

# Type checking (if mypy configured)
mypy src/

# Linting (if flake8 configured)
flake8 src/
```

## Architecture Overview

### Core Components

**Server Architecture (src/server.py)**
- FastMCP-based MCP server with 40 financial data tools (screening, fundamentals, news, market/performance analysis, SEC/EDGAR filings, and field discovery)
- Each tool is a decorated function that returns `List[TextContent]`
- Comprehensive error handling and logging for all tools
- Validates inputs using `src/utils/validators.py`

**Client Architecture (src/finviz_client/)**
- `base.py`: Core HTTP client with rate limiting and retry logic
- `screener.py`: Stock screening functionality with various filters
- `news.py`: News retrieval and processing
- `sector_analysis.py`: Sector and market performance analysis

**Data Models (src/models.py)**
- `StockData`: Comprehensive stock information with 70+ fields
- `NewsData`: News article information
- `SectorPerformance`: Sector performance metrics
- `EarningsData`: Earnings-specific data
- `UpcomingEarningsData`: Pre-earnings analysis data
- Field mappings for Finviz API integration

**Utilities (src/utils/)**
- `validators.py`: Input validation for all parameters
- `formatters.py`: Output formatting utilities

### Key Design Patterns

**Tool Implementation Pattern**
```python
@server.tool()
def tool_name(param1: type, param2: Optional[type] = None) -> List[TextContent]:
    try:
        # Parameter validation
        # Call appropriate client method
        # Format results
        return [TextContent(type="text", text=formatted_output)]
    except Exception as e:
        logger.error(f"Error in tool_name: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
```

**Screening Workflow**
1. Validate input parameters using validators
2. Build Finviz URL filters
3. Make HTTP request with rate limiting
4. Parse HTML/CSV response
5. Convert to StockData objects
6. Format for display

### MCP Tool Categories

The server exposes 40 tools. 35 are defined in `src/server.py`; the 5 field-discovery
tools are defined in `src/field_discovery/tools.py` and registered on the same server.

**Stock Screening (8 tools)**
- `earnings_screener`: Basic earnings date filtering
- `volume_surge_screener`: High volume with price movement
- `trend_reversion_screener`: Oversold stocks with good fundamentals
- `uptrend_screener`: Strong uptrend identification
- `dividend_growth_screener`: Dividend growth stocks
- `etf_screener`: ETF screening
- `technical_analysis_screener`: Technical indicator based
- `custom_screener`: Arbitrary filter/field combinations with custom output columns

**Earnings-Focused Tools (5 tools)**
- `earnings_premarket_screener`: Pre-market earnings reactions
- `earnings_afterhours_screener`: After-hours earnings reactions
- `earnings_trading_screener`: Earnings trading opportunities
- `earnings_winners_screener`: Detailed earnings winners analysis
- `upcoming_earnings_screener`: Next week earnings calendar

**Fundamental Analysis (2 tools)**
- `get_stock_fundamentals`: Single stock data
- `get_multiple_stocks_fundamentals`: Batch stock data

**News Analysis (3 tools)**
- `get_stock_news`: Stock-specific news
- `get_market_news`: General market news
- `get_sector_news`: Sector-specific news

**Market & Performance Analysis (8 tools)**
- `get_sector_performance`: Sector performance metrics
- `get_industry_performance`: Industry performance
- `get_sector_specific_industry_performance`: Industries within a given sector
- `get_country_performance`: Country market performance
- `get_capitalization_performance`: Performance by market-cap tier
- `get_market_overview`: Overall market status
- `get_relative_volume_stocks`: Unusual volume detection
- `get_moving_average_position`: Price position relative to moving averages for a ticker

**SEC & EDGAR Filings (9 tools)**
- `get_sec_filings`: Recent SEC filings for a ticker
- `get_major_sec_filings`: Material/major filings only
- `get_insider_sec_filings`: Insider transaction filings
- `get_sec_filing_summary`: Summarized view of recent filings
- `get_edgar_company_filings`: EDGAR filing index for a company
- `get_edgar_company_facts`: XBRL company facts from EDGAR
- `get_edgar_company_concept`: Single XBRL concept/time series for a company
- `get_edgar_filing_content`: Fetch the content of one EDGAR filing
- `get_multiple_edgar_filing_contents`: Batch-fetch multiple EDGAR filing contents

**Field Discovery (5 tools)** — defined in `src/field_discovery/tools.py`
- `list_available_fields`: All screener/output fields the server supports
- `get_field_categories`: Fields grouped by category
- `describe_field`: Details and valid values for a single field
- `search_fields`: Keyword search across fields (optional category filter)
- `validate_fields`: Validate a list of field names before use

## Configuration

### Environment Variables
- `FINVIZ_API_KEY`: Finviz Elite API key (optional, improves rate limits)
- `LOG_LEVEL`: Logging level (INFO, DEBUG, WARNING, ERROR)
- `RATE_LIMIT_REQUESTS_PER_MINUTE`: Rate limiting (default: 100)
- `MCP_SERVER_PORT`: Server port (default: stdio mode)

### MCP Integration

#### For Claude Desktop
Configure in `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "finviz": {
      "command": "/path/to/finviz-mcp-server/venv/bin/finviz-mcp-server",
      "args": [],
      "cwd": "/path/to/finviz-mcp-server",
      "env": {
        "FINVIZ_API_KEY": "your_finviz_elite_api_key",
        "LOG_LEVEL": "INFO",
        "RATE_LIMIT_REQUESTS_PER_MINUTE": "100"
      }
    }
  }
}
```

#### For Claude Code
Claude Code automatically detects this CLAUDE.md file and the MCP server configuration.

**MCP Server Configuration for Claude Code:**
```json
{
  "mcpServers": {
    "finviz": {
      "command": "/path/to/finviz-mcp-server/venv/bin/finviz-mcp-server",
      "args": [],
      "cwd": "/path/to/finviz-mcp-server",
      "env": {
        "FINVIZ_API_KEY": "${FINVIZ_API_KEY}",
        "LOG_LEVEL": "INFO",
        "RATE_LIMIT_REQUESTS_PER_MINUTE": "100"
      }
    }
  }
}
```

**Environment Setup:**
Create `.env` file in project root:
```env
FINVIZ_API_KEY=your_finviz_elite_api_key_here
LOG_LEVEL=INFO
RATE_LIMIT_REQUESTS_PER_MINUTE=100
```

**Requirements:**
- **Finviz Elite Subscription Required**: Full functionality requires Finviz Elite

## Troubleshooting

### Common Issues
1. **Import Errors**: Ensure all dependencies are installed with `pip install -e .`
2. **Rate Limiting**: Add FINVIZ_API_KEY to environment variables
3. **Connection Issues**: Check network connectivity and Finviz server status
4. **Data Parsing Errors**: Verify Finviz response format hasn't changed

### Debug Mode
```bash
export LOG_LEVEL=DEBUG
python3 run_server.py
```

### Performance Optimization
- Use Finviz Elite API key for higher rate limits
- Implement caching for frequently accessed data
- Batch multiple stock requests when possible

## Contributing

### Code Style
- Follow PEP 8 guidelines
- Use type hints for all functions
- Include docstrings for public methods
- Add comprehensive error handling

### Testing
- Write unit tests for new functionality
- Test with real Finviz data
- Verify MCP integration compatibility
- Check performance with large result sets

### Documentation
- Update this guide for new features
- Document API changes in README files
- Include examples in tool reference
- Update setup instructions as needed 