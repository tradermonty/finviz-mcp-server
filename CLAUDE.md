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
- FastMCP-based MCP server with 20+ financial screening tools
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

**Stock Screening (7 tools)**
- `earnings_screener`: Basic earnings date filtering
- `volume_surge_screener`: High volume with price movement
- `trend_reversion_screener`: Oversold stocks with good fundamentals
- `uptrend_screener`: Strong uptrend identification
- `dividend_growth_screener`: Dividend growth stocks
- `etf_screener`: ETF screening
- `technical_analysis_screener`: Technical indicator based

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

**Market Analysis (5 tools)**
- `get_sector_performance`: Sector performance metrics
- `get_industry_performance`: Industry performance
- `get_country_performance`: Country market performance
- `get_market_overview`: Overall market status
- `get_relative_volume_stocks`: Unusual volume detection

## Configuration

### Environment Variables
- `FINVIZ_API_KEY`: Finviz Elite API key (required for all Finviz-backed tools)
- `EDGAR_USER_AGENT`: Required only for EDGAR tools (e.g. `Your Name your.email@example.com`); EDGAR does not require a Finviz key
- `LOG_LEVEL`: Logging level (INFO, DEBUG, WARNING, ERROR)
- `RATE_LIMIT_REQUESTS_PER_MINUTE`: Currently not read by the Finviz client; it uses a fixed one-second delay before each request attempt
- `MCP_SERVER_PORT`: Server port (default: stdio mode)

The server can start without either credential. Finviz credentials are checked when a Finviz-backed tool makes a request; EDGAR credentials are checked independently when an EDGAR tool is used.

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
        "LOG_LEVEL": "INFO"
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
        "LOG_LEVEL": "INFO"
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
```

**Requirements:**
- **Finviz Elite Subscription Required**: Every Finviz-backed tool requires a Finviz Elite subscription and a valid `FINVIZ_API_KEY`. EDGAR tools require `EDGAR_USER_AGENT` independently

## Troubleshooting

### Common Issues
1. **Import Errors**: Ensure all dependencies are installed with `pip install -e .`
2. **Authentication Errors**: A missing key raises an explicit `FINVIZ_API_KEY is required` error. HTTP 401/403 responses and HTML login pages also raise authentication errors; check the key and your Finviz Elite subscription. These failures do not mean that a screen has no matches.
3. **Rate Limiting**: The client waits one second before each request attempt and makes up to three attempts for request failures, including HTTP 429/503, with exponential backoff between attempts. Adding a key does not configure this delay; `RATE_LIMIT_REQUESTS_PER_MINUTE` is currently unused
4. **Connection Issues**: Check network connectivity and Finviz server status
5. **Data Parsing Errors**: Verify Finviz response format hasn't changed

### Debug Mode
```bash
export LOG_LEVEL=DEBUG
python3 run_server.py
```

### Performance Optimization
- Reduce repeated requests by reusing results where appropriate
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