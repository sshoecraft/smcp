# Alpaca SMCP Server

An MCP server for Alpaca Markets trading and market data with SMCP (Secure MCP Credential Protocol) support for secure credential injection.

## Overview

This server provides comprehensive stock, crypto, and options trading along with market data access via the Model Context Protocol (MCP). It wraps the Alpaca Markets API for commission-free trading. Unlike traditional MCP servers that receive credentials via command-line arguments or environment variables, this server uses SMCP for secure credential injection at startup.

## Features

- **Trading**: Stocks, crypto, and options
- **Order Types**: Market, limit, stop, stop-limit, trailing stop
- **Position Management**: View, close partial/full, close all
- **Watchlists**: Create, update, manage symbol watchlists
- **Market Data**: Real-time quotes, trades, bars, snapshots
- **Crypto Data**: Bars, quotes, trades, orderbook
- **Options Data**: Contracts, quotes, Greeks
- **Corporate Actions**: Dividends, splits, spinoffs, mergers
- **Secure Credentials**: SMCP injection (no env vars, no CLI args)

## Installation

```bash
pip install -e .
```

## SMCP Credentials

| Credential | Required | Description |
|------------|----------|-------------|
| `ALPACA_API_KEY` | Yes | Alpaca API Key ID |
| `ALPACA_SECRET_KEY` | Yes | Alpaca API Secret Key |
| `ALPACA_PAPER` | No | Use paper trading: "true" or "false" (default: "true") |
| `LOG_LEVEL` | No | Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO) |

Get API keys at: https://app.alpaca.markets/

**Note:** Paper trading is enabled by default for safety. Set `ALPACA_PAPER=false` for live trading.

## Quick Start with Shepherd

```bash
shepherd smcp add alpaca --command "alpaca-smcp-server" \
  --credential "ALPACA_API_KEY=PK..." \
  --credential "ALPACA_SECRET_KEY=..." \
  --credential "ALPACA_PAPER=true"
```

## MCP Tools (47 tools)

### Account (2 tools)

| Tool | Description |
|------|-------------|
| `get_account` | Get account info (buying power, equity, status) |
| `get_portfolio_history` | Get portfolio value history over time |

### Orders (8 tools)

| Tool | Description |
|------|-------------|
| `create_order` | Place a new stock order |
| `list_orders` | List orders with filtering |
| `get_order` | Get order by ID |
| `get_order_by_client_id` | Get order by client order ID |
| `replace_order` | Modify an existing order |
| `cancel_order` | Cancel a specific order |
| `cancel_all_orders` | Cancel all open orders |

### Positions (4 tools)

| Tool | Description |
|------|-------------|
| `list_positions` | List all open positions |
| `get_position` | Get position for symbol |
| `close_position` | Close position (full or partial) |
| `close_all_positions` | Liquidate all positions |

### Watchlists (7 tools)

| Tool | Description |
|------|-------------|
| `list_watchlists` | List all watchlists |
| `get_watchlist` | Get watchlist by ID |
| `create_watchlist` | Create a new watchlist |
| `update_watchlist` | Update watchlist symbols |
| `add_to_watchlist` | Add symbol to watchlist |
| `remove_from_watchlist` | Remove symbol from watchlist |
| `delete_watchlist` | Delete a watchlist |

### Stock Market Data (8 tools)

| Tool | Description |
|------|-------------|
| `get_bars` | Get historical OHLCV bars |
| `get_latest_bar` | Get latest bar |
| `get_quotes` | Get historical quotes |
| `get_latest_quote` | Get latest quote |
| `get_trades` | Get historical trades |
| `get_latest_trade` | Get latest trade |
| `get_snapshot` | Get full market snapshot |

### Crypto Market Data (6 tools)

| Tool | Description |
|------|-------------|
| `get_crypto_bars` | Get crypto OHLCV bars |
| `get_crypto_latest_bar` | Get latest crypto bar |
| `get_crypto_latest_quote` | Get latest crypto quote |
| `get_crypto_latest_trade` | Get latest crypto trade |
| `get_crypto_snapshot` | Get crypto snapshot |
| `get_crypto_orderbook` | Get crypto bid/ask depth |

### Options (7 tools)

| Tool | Description |
|------|-------------|
| `get_option_contracts` | Search option contracts |
| `get_option_contract` | Get specific contract |
| `create_option_order` | Place an option order |
| `exercise_option` | Exercise an option position |
| `get_option_latest_quote` | Get option quote |
| `get_option_snapshot` | Get option snapshot with Greeks |

### Assets (2 tools)

| Tool | Description |
|------|-------------|
| `list_assets` | List tradable assets |
| `get_asset` | Get asset details |

### Market Info (2 tools)

| Tool | Description |
|------|-------------|
| `get_clock` | Get market clock (open/close) |
| `get_calendar` | Get market calendar |

### Corporate Actions (1 tool)

| Tool | Description |
|------|-------------|
| `get_corporate_actions` | Get dividends, splits, mergers |

## Order Types

| Type | Description | Required Params |
|------|-------------|-----------------|
| market | Execute at market price | qty or notional |
| limit | Execute at limit price or better | qty, limit_price |
| stop | Trigger market order at stop price | qty, stop_price |
| stop_limit | Trigger limit order at stop price | qty, limit_price, stop_price |
| trailing_stop | Stop follows price | qty, trail_price or trail_percent |

## Time in Force

| TIF | Description |
|-----|-------------|
| day | Valid for trading day only |
| gtc | Good til cancelled |
| opg | Market on open |
| ioc | Immediate or cancel |
| fok | Fill or kill |

## Examples

### Get Account
```json
{"name": "get_account"}
```

### Place Market Order
```json
{
  "name": "create_order",
  "arguments": {
    "symbol": "AAPL",
    "side": "buy",
    "order_type": "market",
    "time_in_force": "day",
    "qty": 10
  }
}
```

### Place Limit Order
```json
{
  "name": "create_order",
  "arguments": {
    "symbol": "AAPL",
    "side": "buy",
    "order_type": "limit",
    "time_in_force": "gtc",
    "qty": 10,
    "limit_price": 150.00
  }
}
```

### Get Crypto Quote
```json
{"name": "get_crypto_latest_quote", "arguments": {"symbol": "BTC/USD"}}
```

### Search Option Contracts
```json
{
  "name": "get_option_contracts",
  "arguments": {
    "underlying_symbol": "AAPL",
    "option_type": "call",
    "expiration_date_gte": "2025-02-01"
  }
}
```

### Create Watchlist
```json
{
  "name": "create_watchlist",
  "arguments": {
    "name": "Tech Stocks",
    "symbols": ["AAPL", "GOOGL", "MSFT", "NVDA"]
  }
}
```

### Get Portfolio History
```json
{"name": "get_portfolio_history", "arguments": {"period": "1M", "timeframe": "1D"}}
```

## Security

- Credentials injected via SMCP at startup
- Never appear in environment, CLI args, or files
- Paper trading enabled by default
- HTTPS for all Alpaca API calls

## Dependencies

- `mcp>=1.6.0` - Model Context Protocol SDK
- `smcp` - SMCP credential injection library
- `requests>=2.28.0` - HTTP client

## Version History

- **0.2.0** - Full feature parity with official alpaca-mcp-server (47 tools)
- **0.1.0** - Initial release with basic trading tools (18 tools)

## License

MIT
