# Alpha Vantage SMCP Server

An MCP server for Alpha Vantage market data with SMCP (Secure MCP Credential Protocol) support for secure credential injection.

## Overview

This server provides comprehensive stock market data, technical indicators, news sentiment, and company fundamentals via the Model Context Protocol (MCP). It wraps the Alpha Vantage API. Unlike traditional MCP servers that receive credentials via command-line arguments or environment variables, this server uses SMCP for secure credential injection at startup.

## Features

- Real-time and historical stock quotes
- Intraday, daily, weekly, and monthly price data
- Technical indicators (RSI, MACD, SMA, EMA, Bollinger Bands, ATR, Stochastic, ADX, OBV)
- News and sentiment analysis
- Company fundamentals and financial statements
- Symbol search
- Global market status
- Secure credential injection via SMCP

## Installation

```bash
pip install -e .
```

## SMCP Credentials

| Credential | Required | Description |
|------------|----------|-------------|
| `ALPHAVANTAGE_API_KEY` | Yes | Alpha Vantage API key |
| `LOG_LEVEL` | No | Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO) |

Get a free API key at: https://www.alphavantage.co/support/#api-key

## Rate Limits

Alpha Vantage free tier:
- **25 API calls per day**
- **5 API calls per minute**

Premium plans available for higher limits.

**Note:** Some tools (like `get_technicals` and `get_batch_quotes`) make multiple API calls per invocation.

## Quick Start with Shepherd

```bash
shepherd smcp add alphavantage --command "alphavantage-smcp-server" --credential "ALPHAVANTAGE_API_KEY=your-api-key"
```

## MCP Tools

### Price Data

#### get_quote
Get current price and volume for a stock symbol.
- `symbol` (string, required): Stock ticker symbol

#### get_history
Get historical daily OHLCV data.
- `symbol` (string, required): Stock ticker symbol
- `days` (int, optional): Number of days (default: 30)

#### get_intraday
Get intraday OHLCV data.
- `symbol` (string, required): Stock ticker symbol
- `interval` (string, optional): "1min", "5min", "15min", "30min", "60min" (default: "5min")
- `limit` (int, optional): Number of data points (default: 100)
- `extended_hours` (bool, optional): Include extended hours (default: true)

#### get_weekly
Get weekly OHLCV data.
- `symbol` (string, required): Stock ticker symbol
- `weeks` (int, optional): Number of weeks (default: 52)
- `adjusted` (bool, optional): Use adjusted values (default: false)

#### get_monthly
Get monthly OHLCV data.
- `symbol` (string, required): Stock ticker symbol
- `months` (int, optional): Number of months (default: 60)
- `adjusted` (bool, optional): Use adjusted values (default: false)

#### get_batch_quotes
Get quotes for multiple symbols.
- `symbols` (array, required): List of ticker symbols

### Technical Indicators

#### get_technicals
Get technical indicators for a stock.
- `symbol` (string, required): Stock ticker symbol
- `indicators` (array, optional): List of indicators to fetch

**Available indicators:**
- `rsi` - Relative Strength Index (14-period)
- `macd` - Moving Average Convergence/Divergence
- `sma20`, `sma50`, `sma200` - Simple Moving Averages
- `ema20`, `ema50`, `ema200` - Exponential Moving Averages
- `bbands` - Bollinger Bands (upper, middle, lower)
- `atr` - Average True Range
- `stoch` - Stochastic Oscillator (slowK, slowD)
- `adx` - Average Directional Index
- `obv` - On Balance Volume

**Example:**
```json
{"name": "get_technicals", "arguments": {"symbol": "AAPL", "indicators": ["rsi", "macd", "bbands"]}}
```

### Fundamentals

#### get_fundamentals
Get company overview (P/E ratio, market cap, EPS, etc.).
- `symbol` (string, required): Stock ticker symbol

#### get_income_statement
Get income statement data.
- `symbol` (string, required): Stock ticker symbol
- `period` (string, optional): "annual" or "quarterly" (default: "annual")

#### get_balance_sheet
Get balance sheet data.
- `symbol` (string, required): Stock ticker symbol
- `period` (string, optional): "annual" or "quarterly" (default: "annual")

#### get_cash_flow
Get cash flow statement data.
- `symbol` (string, required): Stock ticker symbol
- `period` (string, optional): "annual" or "quarterly" (default: "annual")

### News & Sentiment

#### get_news
Get recent news and sentiment for a stock.
- `symbol` (string, required): Stock ticker symbol
- `limit` (int, optional): Maximum articles (default: 5)

### Utilities

#### search_symbols
Search for stock symbols by keyword.
- `keywords` (string, required): Search keywords (company name, partial symbol)

#### get_market_status
Get global market status (open/closed for major exchanges).
- No parameters

## Testing

Alpha Vantage provides a demo key that works with the IBM symbol only:

```json
{
  "ALPHAVANTAGE_API_KEY": "demo"
}
```

Use this for testing without consuming your API quota.

## Example Usage

### SMCP Launcher Configuration

```json
{
  "smcp_servers": [
    {
      "name": "alphavantage",
      "command": "alphavantage-smcp-server",
      "credentials": {
        "ALPHAVANTAGE_API_KEY": "your-api-key-here"
      }
    }
  ]
}
```

### Tool Call Examples

Get a stock quote:
```json
{"name": "get_quote", "arguments": {"symbol": "AAPL"}}
```

Get intraday data:
```json
{"name": "get_intraday", "arguments": {"symbol": "MSFT", "interval": "15min", "limit": 50}}
```

Get technical indicators:
```json
{"name": "get_technicals", "arguments": {"symbol": "GOOGL", "indicators": ["rsi", "macd", "bbands", "atr"]}}
```

Search for symbols:
```json
{"name": "search_symbols", "arguments": {"keywords": "Tesla"}}
```

Get financial statements:
```json
{"name": "get_income_statement", "arguments": {"symbol": "NVDA", "period": "quarterly"}}
```

Check market status:
```json
{"name": "get_market_status"}
```

## Security

- API key is injected via SMCP at startup
- Credentials never appear in environment variables, CLI args, or config files
- All communication with Alpha Vantage uses HTTPS

## Dependencies

- `mcp>=1.6.0` - Model Context Protocol SDK
- `smcp` - SMCP credential injection library
- `requests>=2.28.0` - HTTP client

## License

MIT
