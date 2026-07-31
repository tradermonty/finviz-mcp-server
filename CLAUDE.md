# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment Setup
```bash
# Create virtual environment with Python 3.10+
python3 -m venv venv
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
# Offline suite (no network, no API key)
python3 -m pytest tests/ -q -k "not e2e and not live" \
  --ignore=tests/test_comprehensive_e2e_real_calls.py \
  --ignore=tests/test_e2e_screeners.py \
  --ignore=tests/test_e2e_with_real_objects.py \
  --ignore=tests/test_e2e_screener_invariants.py

# Everything, including live Finviz/EDGAR calls (needs FINVIZ_API_KEY)
python3 -m pytest tests/ -q
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
- `StockData`: One row of the Finviz export — 150 mapped columns
- `NewsData`: News article information
- `SectorPerformance`: Sector performance metrics
- `EarningsData`: Earnings-specific data
- `UpcomingEarningsData`: Upcoming-earnings row data
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

Exact parameters live in the tool docstrings (`src/server.py`) and
`docs/tools_reference.md`. Notes below record behavior that is easy to assume
wrongly.

**Stock Screening (8 tools)**
- `earnings_screener`: Earnings date + price/volume/sector filters. `min_volume` is
  *current-day* volume (`sh_curvol_*`).
- `volume_surge_screener`: **No parameters** — fixed criteria
- `trend_reversion_screener`: Oversold stocks with good fundamentals
- `uptrend_screener`: **No parameters** — fixed criteria
- `dividend_growth_screener`: Dividend growth stocks. There is no dividend-growth
  filter parameter: Finviz has no such token, so the knob was removed.
- `etf_screener`: ETF screening. AUM / expense-ratio / asset-class filters are applied
  **client-side** on the fetched rows (no Finviz tokens exist for them).
- `technical_analysis_screener`: Technical indicator based. With no filters set it
  returns the first `max_results` by ticker plus the total match count.
- `custom_screener`: Raw Finviz filter tokens, optional signal/sort (output columns are fixed)

**Earnings-Focused Tools (5 tools)**
- `earnings_premarket_screener`: Pre-market earnings reactions — **no parameters**
- `earnings_afterhours_screener`: After-hours earnings reactions — **no parameters**
- `earnings_trading_screener`: Earnings trading opportunities — **no parameters**
- `earnings_winners_screener`: Detailed earnings winners analysis (sorts before truncating)
- `upcoming_earnings_screener`: Earnings calendar. `next_2_weeks` / `next_month` are sent
  as explicit date ranges; `pre_earnings_analysis` / `risk_assessment` / `data_fields`
  were removed (they were accepted and discarded).

**Fundamental Analysis (2 tools)**
- `get_stock_fundamentals`: Single stock data (all 150 columns unless `data_fields` given)
- `get_multiple_stocks_fundamentals`: Batch stock data

**News Analysis (3 tools)**
- `get_stock_news`: Per-ticker feed (`v=3`); each item keeps its real `Ticker` cell.
  There is no `news_type` parameter — Finviz ignores `filter=`.
- `get_market_news`: Real market feed (`v=1`), with a client-side `category` filter
  (`Market` / `Blog` — the only values that exist).
- `get_sector_news`: No sector feed exists; this resolves the sector's largest
  constituents, then fetches their news. Two requests per call.

**Market & Performance Analysis (8 tools)**
- `get_sector_performance`: Sector performance metrics (honors its `sectors` filter)
- `get_industry_performance`: Industry performance
- `get_sector_specific_industry_performance`: Industries within a given sector
- `get_country_performance`: Country market performance
- `get_capitalization_performance`: Performance by market-cap tier
- `get_market_overview`: Overall market status
- `get_relative_volume_stocks`: Unusual volume detection
- `get_moving_average_position`: Percent distance from the 20/50/200-day SMAs (Finviz
  reports SMA columns as percent distance; absolute prices shown are derived)

The four group tools share one parser and always send explicit column ids; the group
name column is `Name` and market cap is exported in millions.

**SEC & EDGAR Filings (9 tools)**
- `get_sec_filings`: Recent SEC filings for a ticker (`days_back`/`max_results` <= 0 = unlimited)
- `get_major_sec_filings`: Material/major filings only
- `get_insider_sec_filings`: Forms 3/4/5/144 and amendments (11-K excluded)
- `get_sec_filing_summary`: Aggregates the whole period, not just the displayed rows
- `get_edgar_company_filings`: EDGAR filing index; filters apply before `max_count`,
  and `include_full_history=True` walks EDGAR's pagination
- `get_edgar_company_facts`: XBRL company facts from EDGAR
- `get_edgar_company_concept`: Single XBRL concept/time series (formatted per unit)
- `get_edgar_filing_content`: One filing, HTML/iXBRL converted to text *before* truncation
- `get_multiple_edgar_filing_contents`: Batch fetch; `preview_length` caps what is shown

**Field Discovery (5 tools)** — defined in `src/field_discovery/tools.py`
- `list_available_fields`: All 150 mapped fields, grouped by category
- `get_field_categories`: The same fields grouped compactly
- `describe_field`: Details and valid values for a single field
- `search_fields`: Keyword search across fields. The optional category filter uses the
  same derived categories the listing tools show (short alias or full name); an unknown
  category is an error, not an empty result.
- `validate_fields`: Validate field names before use. Shares
  `validators.get_valid_data_field_names()` with the request path, so it accepts
  aliases, CSV result keys, derived keys and `all` — exactly what the tools accept.

## Configuration

### Environment Variables
- `FINVIZ_API_KEY`: Finviz Elite API key (optional, improves rate limits)
- `LOG_LEVEL`: Logging level (INFO, DEBUG, WARNING, ERROR)
- `RATE_LIMIT_REQUESTS_PER_MINUTE`: Rate limiting (default: 100)
- `MCP_TRANSPORT` / `MCP_HOST` / `MCP_PORT`: only for non-stdio transports (default: stdio)
- `EDGAR_USER_AGENT`: required by the 5 EDGAR tools (SEC rejects requests without a contact UA)

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