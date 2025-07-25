# Finviz MCP Server

**English** | [日本語](README_ja.md)

A Model Context Protocol (MCP) server that provides comprehensive stock screening and fundamental analysis capabilities using Finviz data.

## Features

### Stock Screening Tools
- **Earnings Screener**: Find stocks with upcoming earnings announcements
- **Volume Surge Screener**: Detect stocks with unusual volume and price movements
- **Trend Analysis**: Identify uptrend and momentum stocks
- **Dividend Growth Screener**: Find dividend-paying stocks with growth potential
- **ETF Screener**: Screen exchange-traded funds
- **Premarket/Afterhours Earnings**: Track earnings reactions in extended hours

### Fundamental Analysis
- Individual stock fundamental data retrieval
- Multiple stock comparison
- Sector and industry performance analysis
- News and sentiment tracking

### Technical Analysis
- RSI, Beta, and volatility metrics
- Moving average analysis (SMA 20/50/200)
    - **NEW:** `get_moving_average_position` – see how far price sits above/below the 20-, 50-, and 200-day SMAs in a single call
- Relative volume analysis
- 52-week high/low tracking

## 📄 SEC Filing Features

17. **SEC Filing List Retrieval**
    ```python
    # All AAPL filings (past 30 days)
    finviz_get_sec_filings(ticker="AAPL", days_back=30)
    
    # Major forms only (10-K, 10-Q, 8-K, etc.)
    finviz_get_major_sec_filings(ticker="AAPL", days_back=90)
    
    # Insider trading related (Form 3, 4, 5, etc.)
    finviz_get_insider_sec_filings(ticker="AAPL", days_back=30)
    ```

## Installation

### Prerequisites
- Python 3.11 or higher
- **Finviz Elite Subscription** (required for full functionality)
- Finviz API key (optional but recommended for higher rate limits)

> **Important**: This MCP server requires a Finviz Elite subscription to access comprehensive screening and data features. For more details about Finviz Elite and subscription options, visit: https://elite.finviz.com/elite.ashx

### Setup

1. **Clone and setup the project:**
```bash
# Clone the repository
git clone <repository-url>
cd finviz-mcp-server

# Create virtual environment with Python 3.11
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# or
venv\\Scripts\\activate     # On Windows

# Install the package in development mode
pip install -e .
```

2. **Configure environment variables:**
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env file and add your Finviz API key
FINVIZ_API_KEY=your_actual_api_key_here
```

3. **Test the installation:**
```bash
# Test if the server starts correctly (press Ctrl+C to stop)
finviz-mcp-server

# You should see the server starting in stdio mode
```

## Configuration

The server can be configured using environment variables:

- `FINVIZ_API_KEY`: Your Finviz Elite API key (required for Elite features, improves rate limits)
- `MCP_SERVER_PORT`: Server port (default: 8080)
- `LOG_LEVEL`: Logging level (default: INFO)
- `RATE_LIMIT_REQUESTS_PER_MINUTE`: Rate limiting (default: 100)

> **Note**: While the API key is technically optional, many advanced screening features require a Finviz Elite subscription and API key to function properly.

## Usage

### Running the MCP Server

The server runs as a stdio-based MCP server:

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Run the server
finviz-mcp-server
```

### Integration with Claude Desktop

Add the server to your Claude Desktop MCP configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "finviz": {
      "command": "/path/to/your/project/venv/bin/finviz-mcp-server",
      "args": [],
      "cwd": "/path/to/your/project/finviz-mcp-server",
      "env": {
        "FINVIZ_API_KEY": "your_api_key_here",
        "LOG_LEVEL": "INFO",
        "RATE_LIMIT_REQUESTS_PER_MINUTE": "100"
      }
    }
  }
}
```

**Important Configuration Notes:**
- Replace `/path/to/your/project/` with your actual project path
- Use the absolute path to the `finviz-mcp-server` executable in your virtual environment
- Set the `cwd` (current working directory) to your project root
- Replace `your_api_key_here` with your actual Finviz API key

**Alternative: Using .env file**
If you prefer to use a `.env` file (recommended for security):

```json
{
  "mcpServers": {
    "finviz": {
      "command": "/path/to/your/project/venv/bin/finviz-mcp-server",
      "args": [],
      "cwd": "/path/to/your/project/finviz-mcp-server"
    }
  }
}
```

Make sure your `.env` file contains all required environment variables.

### MCP Tools

#### Earnings Screener
```python
# Find stocks with earnings today after market close
earnings_screener(
    earnings_date="today_after",
    market_cap="large",
    min_price=10,
    min_volume=1000000,
    sectors=["Technology", "Healthcare"]
)
```

#### Volume Surge Screener
```python
# Find stocks with high volume and price increases
volume_surge_screener(
    market_cap="smallover",
    min_price=10,
    min_relative_volume=1.5,
    min_price_change=2.0,
    sma_filter="above_sma200"
)
```

#### Stock Fundamentals
```python
# Get fundamental data for a single stock
get_stock_fundamentals(
    ticker="AAPL",
    data_fields=["pe_ratio", "eps", "dividend_yield", "market_cap"]
)

# Get fundamental data for multiple stocks
get_multiple_stocks_fundamentals(
    tickers=["AAPL", "MSFT", "GOOGL"],
    data_fields=["pe_ratio", "eps", "market_cap"]
)
```

## Advanced Screening Examples

### Earnings-Based Strategies

#### Premarket Earnings Momentum
```python
earnings_premarket_screener(
    earnings_timing="today_before",
    market_cap="large",
    min_price=25,
    min_price_change=2.0,
    include_premarket_data=True
)
```

#### Afterhours Earnings Reactions
```python
earnings_afterhours_screener(
    earnings_timing="today_after",
    min_afterhours_change=5.0,
    market_cap="mid",
    include_afterhours_data=True
)
```



### Technical Analysis Strategies

#### Trend Reversal Candidates
```python
trend_reversion_screener(
    market_cap="large",
    eps_growth_qoq=10.0,
    rsi_max=30,
    sectors=["Technology", "Healthcare"]
)
```

#### Strong Uptrend Stocks
```python
uptrend_screener(
    trend_type="strong_uptrend",
    sma_period="20",
    relative_volume=2.0,
    price_change=5.0
)
```

### Value Investment Strategies

#### Dividend Growth
```python
dividend_growth_screener(
    min_dividend_yield=2.0,
    max_dividend_yield=6.0,
    min_dividend_growth=5.0,
    min_roe=15.0
)
```

## Data Models

### StockData
Comprehensive stock information including:
- Basic info (ticker, company, sector, industry)
- Price and volume data
- Technical indicators (RSI, Beta, moving averages)
- Fundamental metrics (P/E, EPS, dividend yield)
- Earnings data (surprises, estimates, growth rates)
- Performance metrics (1w, 1m, YTD)

### Screening Results
Structured results with:
- Query parameters used
- List of matching stocks
- Total count and execution time
- Formatted output for easy reading

## Error Handling

The server includes comprehensive error handling:
- Input validation for all parameters
- Rate limiting protection
- Network error recovery with retries
- Detailed error messages and logging

## Rate Limiting

To respect Finviz's servers:
- Default 1-second delay between requests
- Configurable rate limiting
- Automatic retry with exponential backoff
- Finviz Elite API key support for higher limits

## Logging

Configurable logging levels:
- DEBUG: Detailed request/response information
- INFO: General operation information (default)
- WARNING: Non-critical issues
- ERROR: Critical errors

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for educational and research purposes only. Always conduct your own research before making investment decisions. The authors are not responsible for any financial losses incurred using this software.

**Finviz Elite Requirement**: This MCP server requires a Finviz Elite subscription for full functionality. Free Finviz accounts have limited access to screening features and data. For comprehensive stock screening capabilities, please subscribe to Finviz Elite at https://elite.finviz.com/elite.ashx

## Support

For issues and feature requests, please use the GitHub issue tracker.

## Support the Project

If you find this project helpful, consider supporting its development:

[![Buy Me A Coffee](https://img.shields.io/badge/Buy_Me_A_Coffee-Support_Development-orange?style=for-the-badge&logo=buy-me-a-coffee)](https://coff.ee/tradermonty)

## Changelog

### v1.0.0
- Initial release
- Basic screening tools implementation
- Fundamental data retrieval
- MCP server integration
- Comprehensive error handling and validation