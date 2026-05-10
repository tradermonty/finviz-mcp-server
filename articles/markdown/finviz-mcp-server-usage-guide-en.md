# Finviz MCP Server Usage Guide: Daily Stock Screening Workflow

> **Meta description**: A practical guide to using `finviz-mcp-server` from Claude. Covers setup, morning market checks, weekly review, earnings patterns, dividend growth screening, sector analysis, and reusable prompts.

> ⚠️ **Disclaimer**: This article is an educational usage guide. It is not investment advice and does not promise any specific performance or profit. The screening conditions and thresholds are general references — make your own investment decisions.

## Why use finviz-mcp-server?

**Pain points of manual screening**:

- Switching between the Finviz web UI and other analysis tools
- Re-entering filter conditions every time you tweak a screen
- Reconciling screener output with separate news / fundamental sources
- Repeating the same operations daily

**What finviz-mcp-server brings**:

- Drive Finviz screeners from Claude with natural-language prompts
- 20+ screening tools (earnings, dividend, technical, sector, etc.) callable as functions
- Ask follow-up questions and dig deeper on results in the same conversation
- Build reproducible workflows over the Model Context Protocol (MCP)

> 💰 **Cost**: A Finviz Elite subscription is required ($24.96/mo billed annually, or $39.50/mo billed monthly — pricing may change, see the [official page](https://finviz.com/elite)). The free Finviz account does **not** work.

---

## Setup Guide

### Prerequisites

| Item | Requirement | How to check |
|------|-------------|--------------|
| Python | 3.11 or higher | `python3 --version` |
| Finviz Elite | Subscription required | [Finviz Elite](https://finviz.com/elite.ashx) |
| Claude Desktop | Latest version | [Official site](https://claude.ai/download) |

> ⚠️ The current `finviz-mcp-server` **requires a Finviz Elite API key**. The free tier does not work.

---

### Step 1: Set up the project environment

```bash
# Create a working directory
mkdir ~/finviz-trading && cd ~/finviz-trading

# Create a Python virtual environment
python3.11 -m venv venv
source venv/bin/activate  # macOS / Linux
# On Windows
venv\Scripts\activate

# Install finviz-mcp-server
git clone https://github.com/tradermonty/finviz-mcp-server.git
cd finviz-mcp-server
pip install -e .
```

### Step 2: Get a Finviz Elite API key

1. Subscribe at [Finviz Elite](https://finviz.com/elite.ashx)
2. Sign in and go to **Account Settings → API Access**
3. Click **Generate New API Key**
4. Copy the generated key (used in Step 3)

---

### Step 3: Configure Claude Desktop's MCP

#### Config file location

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

#### Example config

```json
{
  "mcpServers": {
    "finviz": {
      "command": "/Users/your-username/finviz-trading/finviz-mcp-server/venv/bin/finviz-mcp-server",
      "args": [],
      "cwd": "/Users/your-username/finviz-trading/finviz-mcp-server",
      "env": {
        "FINVIZ_API_KEY": "your_actual_finviz_elite_api_key_here",
        "LOG_LEVEL": "INFO",
        "RATE_LIMIT_REQUESTS_PER_MINUTE": "100"
      }
    }
  }
}
```

> ⚠️ Adjust the paths for your environment, and put the API key from Step 2 in `FINVIZ_API_KEY`.

#### Restart Claude Desktop

1. Fully quit Claude Desktop
2. Relaunch the app
3. Open a new chat and verify

---

### Step 4: Smoke test

In Claude Desktop, try:

```
Give me a quick market overview for today.
```

If you get back the major indices, sector performance, and VIX, you're set up correctly.

---

## 1. Morning Market Check

### Step 1: Overall market

```python
# Get a snapshot of the broader market
market_overview = get_market_overview()
```

**What to look at**:

| Indicator | Notes |
|-----------|-------|
| S&P 500 | Daily change |
| NASDAQ | Tech-heavy direction |
| VIX | Volatility regime |

> 💡 A VIX above 30 is generally interpreted as an "elevated" regime — it's a rough reference, not an absolute threshold.

### Step 2: Sector performance

```python
# All sectors
sector_performance = get_sector_performance()

# Specific sectors only
tech_performance = get_sector_performance(sectors=["Technology"])
```

Comparing sector strength gives you a feel for the day's money flow.

### Step 3: Unusual volume

```python
# Volume surge candidates
volume_surge_stocks = volume_surge_screener()
```

Stocks trading well above average volume are often reacting to news or analyst actions, so pair this with news lookups.

---

### Sample morning-routine prompt

```
Summarize today's market for me:

1. Major index changes (S&P 500, NASDAQ, VIX)
2. The 3 strongest and 3 weakest sectors
3. Names with relative volume of 2x or more AND a price move of 3% or more

Return everything in tables.
```

---

## 2. Weekly Review

### Weekly performance

```python
# Sector / country / market-cap performance
weekly_sectors = get_sector_performance()
country_performance = get_country_performance()
cap_performance = get_capitalization_performance()
```

### Trend analysis

```python
# Names still in an uptrend
uptrend_stocks = uptrend_screener()

# Reversal candidates
reversal_candidates = trend_reversion_screener()
```

### What to track each week

1. Weekly index performance and VIX shifts
2. Sector rotation and which sectors lead vs. lag
3. Top movers, new highs / new lows
4. Next week's known catalysts (earnings, economic data, FOMC, etc.)

---

## 3. Earnings Trading Patterns

### 3.1 Pre-earnings preparation

#### Pull next week's earnings calendar

```python
upcoming_earnings = upcoming_earnings_screener(
    earnings_period="next_week",
    market_cap="smallover",        # $300M and up
    min_price=10,                  # $10 and up
    min_avg_volume="o500"          # avg volume 500k+
)
```

**Reference filters**:

| Filter | Reference value | Reason |
|--------|----------------|--------|
| Market cap | $300M+ | Liquidity |
| Price | $10+ | Avoid penny stocks |
| Avg volume | 500k+ | Reduce slippage |

#### Add a technical filter

```python
technical_candidates = technical_analysis_screener(
    rsi_min=30,
    rsi_max=70,
    price_vs_sma20="above",
    min_price=10,
    min_volume=500000
)
```

### 3.2 Earnings day

#### Pre-market reactions

```python
premarket_earnings = earnings_premarket_screener()
```

#### After-hours reactions

```python
afterhours_earnings = earnings_afterhours_screener()
```

### 3.3 Post-earnings winners

```python
earnings_winners = earnings_winners_screener(
    earnings_period="this_week",
    market_cap="smallover",
    min_eps_growth_qoq=10,
    min_sales_growth_qoq=5
)
```

---

### Sample earnings prompts

#### Weekend prep

```
Help me build a plan for next week's earnings:

1. Screen names reporting next week with market cap >= $500M and avg volume >= 1M
2. Of those, keep names with RSI 40-60 and price above the 20-day SMA
3. Build a table with earnings date, expected EPS, last 4 quarters' surprise
4. With sector diversification in mind, surface 5 high-priority names

Add a one-line rationale for each pick.
```

#### Earnings-day morning

```
For names that reported pre-market today:

- Pre-market move >= +2%
- Market cap >= $300M
- Avg volume >= 500k

For each, summarize:
1. EPS / revenue surprise
2. Guidance changes
3. Initial analyst takes and notable headlines
4. Sector and peer comparison
```

#### After-hours

```
For names that reported after the close and are up 3%+ in after-hours:

- Market cap >= $1B
- Surprise on EPS or revenue

For each, give me:
1. Size of the surprise (estimate vs. actual)
2. Whether guidance was raised
3. CEO / call highlights
4. A plan for tomorrow's open (gap expectation, entry idea, stop level)
```

---

## 4. Dividend Growth Screening

### 4.1 Filter for dividend growers

```python
dividend_growers = dividend_growth_screener(
    market_cap="midover",           # $2B and up
    min_dividend_yield=2.0,
    max_dividend_yield=8.0,         # cap unsustainably high yields
    min_dividend_growth=5.0,        # 5%+ dividend growth
    max_payout_ratio=70.0,
    min_roe=12.0,
    max_debt_equity=0.5
)
```

**Common reference ranges for dividend evaluation**:

| Metric | Generally healthy | Caution zone |
|--------|------------------|---------------|
| Dividend yield | 3-6% | 10%+ (sustainability concerns) |
| Payout ratio | 40-60% | 80%+ |
| ROE | 12%+ | 5% or lower |
| Debt / equity | 0.3 or lower | 0.7 or higher |

> 💡 These are general references. Appropriate ranges differ by industry — for example, utilities and REITs typically run higher payout ratios.

### 4.2 Drill into a single name

```python
# data_fields takes internal keys (snake_case)
stock_fundamentals = get_stock_fundamentals(
    ticker="VZ",
    data_fields=[
        "dividend_yield",
        "payout_ratio",
        "roe",
        "debt_to_equity",
        "eps_growth_past_5y",
        "sales_growth_past_5y",
    ]
)
```

> ℹ️ `data_fields` takes **internal keys (snake_case)**, not display names. To discover available keys, use `mcp__finviz__list_available_fields` or `mcp__finviz__search_fields`.

### 4.3 Filtering for REITs

`dividend_growth_screener` does not have a sector argument, so to focus on REITs you can either:

- Use `custom_screener` with a sector filter, or
- Take the output of `dividend_growth_screener` and post-filter via `get_multiple_stocks_fundamentals` to keep only `sector == "Real Estate"` rows.

```python
# custom_screener takes a raw Finviz filter string (comma-separated), not a dict.
# Example: Real Estate sector, dividend yield 4-12%, mid-cap or larger
reit_results = custom_screener(
    filters="sec_realestate,fa_div_o4,fa_div_u12,cap_midover"
)
```

> ℹ️ `custom_screener`'s `filters` is **a raw Finviz filter string** (e.g. `"sec_realestate,fa_div_o4"`), not a dict. Common prefixes: `cap_` (market cap), `fa_` (fundamentals), `ta_` (technicals), `sec_` (sector), `ind_` (industry), `geo_` (country), `sh_` (share data).

---

### Sample dividend prompt

```
Screen for dividend growth candidates with:
- Yield 3-7%
- 5-year dividend growth >= 5% / year
- Payout ratio <= 70%
- ROE >= 12%
- Debt / equity <= 0.5
- Market cap >= $2B

Sort by yield. If consecutive-dividend-increase years are available, include that column.
```

---

## 5. Other Screening Strategies

### 5.1 Momentum

```python
momentum_stocks = technical_analysis_screener(
    rsi_min=60,
    rsi_max=80,
    price_vs_sma20="above",
    price_vs_sma50="above",
    price_vs_sma200="above",
    min_volume=1000000
)
```

### 5.2 Reversion / value-leaning

```python
value_candidates = trend_reversion_screener(
    market_cap="large",
    eps_growth_qoq=5.0,
    revenue_growth_qoq=3.0,
    rsi_max=40
)
```

### 5.3 ETF screening

```python
sector_etfs = etf_screener(
    strategy_type="long",
    asset_class="equity",
    min_aum=100_000_000,    # $100M and up
    max_expense_ratio=0.75
)
```

> ℹ️ `etf_screener` does not accept a `data_fields` argument; the output schema is fixed.

---

## 6. Portfolio Checks

### 6.1 Multi-name fundamentals

```python
portfolio_stocks = get_multiple_stocks_fundamentals(
    tickers=["AAPL", "MSFT", "GOOGL", "AMZN"],
    data_fields=[
        "sector",
        "beta",
        "volatility_week",
        "market_cap",
    ]
)
```

### 6.2 Sector breakdown

```python
portfolio_sectors = get_sector_performance(
    sectors=["Technology", "Healthcare", "Financial", "Consumer Defensive"]
)
```

Visualizing sector concentration helps surface where the portfolio is over- or under-exposed.

---

## 7. Scenario Prompts

### 7.1 Pre-day-trade check

```
Run my pre-trade checklist:

1. Market overview (S&P 500, NASDAQ, VIX)
2. Volume-surge names (relative volume >= 2x AND |price change| >= 3%)
3. Top 3 strongest / weakest sectors
4. Major news driving today's tape

Wrap it up as a "today's playbook" memo.
```

### 7.2 Swing-trade candidates

```
Build me a swing-trade watchlist for next week.

Conditions:
- SMA20 > SMA50 > SMA200 alignment
- RSI 40-60
- No earnings next week
- Market cap >= $1B
- Avg volume >= 1M

Score by technicals + fundamentals + sector diversification, and surface the top 10.
```

### 7.3 Monthly portfolio review

```
Run my monthly review:

1. Health check on dividend growers (yield 3-8%, payout <= 70%, 5+ years of consecutive raises)
2. Value candidates (market cap >= $10B, P/E <= 15, P/B <= 2, ROE >= 12%)
3. This month's sector rotation

Add suggestions for adjusting my long-term positioning.
```

---

## 8. Tool Reference

| Category | Tool | Purpose |
|---|---|---|
| Market overview | `get_market_overview` | Major indices / VIX / sentiment |
| Market overview | `get_sector_performance` | Sector performance |
| Market overview | `get_industry_performance` | Industry performance |
| Screening | `volume_surge_screener` | Volume-surge names |
| Screening | `uptrend_screener` | Uptrend names |
| Screening | `trend_reversion_screener` | Reversal candidates |
| Screening | `technical_analysis_screener` | Technical filters |
| Screening | `dividend_growth_screener` | Dividend growers |
| Screening | `etf_screener` | ETFs |
| Screening | `custom_screener` | Arbitrary custom filters |
| Earnings | `upcoming_earnings_screener` | Earnings calendar (e.g. next week) |
| Earnings | `earnings_premarket_screener` | Pre-market earnings reactions |
| Earnings | `earnings_afterhours_screener` | After-hours earnings reactions |
| Earnings | `earnings_winners_screener` | Post-earnings winners |
| Earnings | `earnings_trading_screener` | Earnings trading candidates |
| Fundamentals | `get_stock_fundamentals` | Single-name fundamentals |
| Fundamentals | `get_multiple_stocks_fundamentals` | Bulk fundamentals |
| News | `get_stock_news` / `get_market_news` / `get_sector_news` | News feeds |
| Field discovery | `list_available_fields` / `search_fields` / `describe_field` | Discover `data_fields` keys |

For full argument details, ask Claude (`Show me the parameters for the finviz-mcp-server tool XXX`) or read `src/server.py` in the repository.

---

## 9. Troubleshooting

### MCP server isn't detected

```bash
# Verify the path
which finviz-mcp-server

# Check executability
ls -la /path/to/finviz-mcp-server/venv/bin/finviz-mcp-server

# Run it manually
/path/to/finviz-mcp-server/venv/bin/finviz-mcp-server

# Re-check Claude Desktop config
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

### Code changes don't take effect

```bash
# Fully quit Claude Desktop, wait ~30 seconds, relaunch.

# Make sure no stale process is running
ps aux | grep finviz-mcp-server

# Reinstall if needed
cd /path/to/finviz-mcp-server
pip install -e . --force-reinstall
```

### API key errors

If you see `API key required` or similar:

1. Confirm your Finviz Elite subscription is active (the free tier does not work)
2. Verify the API key is valid (re-issue from the API Access page if unsure)
3. Confirm `FINVIZ_API_KEY` is set correctly in `claude_desktop_config.json`
4. Fully restart Claude Desktop

### No data / slow responses

```json
{
  "mcpServers": {
    "finviz": {
      "env": {
        "RATE_LIMIT_REQUESTS_PER_MINUTE": "200",
        "LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

`LOG_LEVEL=DEBUG` surfaces request-level detail in logs, which makes diagnosis much easier.

---

## 10. Prompting Tips

### Less effective

```
Show me some stocks.
```

### More effective

```
Find up to 5 names in the Technology sector with:
- Market cap >= $1B
- RSI 30-70
- Dividend yield >= 2%

Return the result as:
- Ticker
- Company name
- Last price
- RSI
- Dividend yield
- Selection rationale
```

Specify conditions, count, and output format — that's what makes results reproducible.

---

## Summary

`finviz-mcp-server` exposes Finviz's screening capabilities to AI assistants like Claude through MCP. This guide walked through:

- Setup
- Daily morning check and weekly review routines
- Earnings, dividend-growth, and technical screening patterns
- A reference of the main tools and prompts you can reuse

Adjust the conditions to fit your own style, and start by integrating one workflow at a time.

---

## Resources

- **GitHub Repository**: [tradermonty/finviz-mcp-server](https://github.com/tradermonty/finviz-mcp-server)
- **Finviz Elite**: [finviz.com/elite.ashx](https://finviz.com/elite.ashx)
- **Claude Desktop**: [claude.ai/download](https://claude.ai/download)
- **Updates**: [@monty_investor](https://x.com/monty_investor)

---

## Disclaimer

- This article is an educational usage guide. It is not investment advice.
- Investing carries risk of loss of principal. All investment decisions are your own responsibility.
- Past figures and examples are not indicative of future results.
- Comply with Finviz's Terms of Service and API rate limits.

---

*Last updated: 2026-05-10 | finviz-mcp-server compatible*
