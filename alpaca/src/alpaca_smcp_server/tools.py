"""MCP tool definitions for Alpaca operations."""

import json
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


def register_tools(mcp):
    """Register all Alpaca MCP tools."""

    # -------------------------------------------------------------------------
    # Account Tools
    # -------------------------------------------------------------------------

    @mcp.tool()
    def get_account() -> Dict[str, str]:
        """Get account information including buying power, equity, and trading status.

        Returns account details such as buying power, cash, portfolio value,
        equity, pattern day trader status, and whether trading is blocked.
        """
        try:
            client = mcp.client
            result = client.get_account()

            return {
                "success": "true",
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error getting account: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def get_portfolio_history(
        period: Optional[str] = None,
        timeframe: Optional[str] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        extended_hours: bool = False,
    ) -> Dict[str, str]:
        """Get portfolio value history over time.

        Args:
            period: Period for history - "1D", "1W", "1M", "3M", "1A", "all"
            timeframe: Timeframe resolution - "1Min", "5Min", "15Min", "1H", "1D"
            start: Start date in YYYY-MM-DD format (alternative to period)
            end: End date in YYYY-MM-DD format
            extended_hours: Include extended hours data

        Returns:
            Portfolio history with timestamps, equity values, and profit/loss.
        """
        try:
            client = mcp.client
            result = client.get_portfolio_history(
                period=period,
                timeframe=timeframe,
                start=start,
                end=end,
                extended_hours=extended_hours,
            )

            return {
                "success": "true",
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error getting portfolio history: {e}")
            return {"success": "false", "error": str(e)}

    # -------------------------------------------------------------------------
    # Order Tools
    # -------------------------------------------------------------------------

    @mcp.tool()
    def create_order(
        symbol: str,
        side: str,
        order_type: str,
        time_in_force: str,
        qty: Optional[float] = None,
        notional: Optional[float] = None,
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
        trail_price: Optional[float] = None,
        trail_percent: Optional[float] = None,
        extended_hours: bool = False,
        client_order_id: Optional[str] = None,
    ) -> Dict[str, str]:
        """Place a new stock order.

        Args:
            symbol: Stock ticker symbol (e.g., AAPL, MSFT)
            side: Order side - "buy" or "sell"
            order_type: Order type - "market", "limit", "stop", "stop_limit", "trailing_stop"
            time_in_force: Time in force - "day", "gtc", "opg", "ioc", "fok"
            qty: Number of shares (use qty OR notional, not both)
            notional: Dollar amount to trade (market orders only)
            limit_price: Limit price (required for limit/stop_limit orders)
            stop_price: Stop price (required for stop/stop_limit orders)
            trail_price: Trail amount in dollars (for trailing_stop)
            trail_percent: Trail percentage (for trailing_stop)
            extended_hours: Allow extended hours trading (limit orders only)
            client_order_id: Custom order ID for tracking

        Returns:
            Order object with id, status, filled_qty, and other details.
        """
        try:
            client = mcp.client
            result = client.create_order(
                symbol=symbol,
                side=side,
                order_type=order_type,
                time_in_force=time_in_force,
                qty=qty,
                notional=notional,
                limit_price=limit_price,
                stop_price=stop_price,
                trail_price=trail_price,
                trail_percent=trail_percent,
                extended_hours=extended_hours,
                client_order_id=client_order_id,
            )

            return {
                "success": "true",
                "order_id": result.get("id", ""),
                "status": result.get("status", ""),
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def list_orders(
        status: str = "open",
        limit: int = 50,
        symbols: Optional[List[str]] = None,
        after: Optional[str] = None,
        until: Optional[str] = None,
        direction: str = "desc",
    ) -> Dict[str, str]:
        """List orders with optional filtering.

        Args:
            status: Filter by status - "open", "closed", or "all" (default: "open")
            limit: Maximum number of orders to return (default: 50, max: 500)
            symbols: Filter by specific symbols (optional)
            after: Filter orders after this timestamp
            until: Filter orders until this timestamp
            direction: Sort direction - "asc" or "desc" (default: "desc")

        Returns:
            Array of order objects.
        """
        try:
            client = mcp.client
            result = client.list_orders(
                status=status,
                limit=limit,
                symbols=symbols,
                after=after,
                until=until,
                direction=direction,
            )

            return {
                "success": "true",
                "count": str(len(result)),
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error listing orders: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def get_order(order_id: str) -> Dict[str, str]:
        """Get a specific order by ID.

        Args:
            order_id: The order ID to retrieve.

        Returns:
            Order object with full details.
        """
        try:
            client = mcp.client
            result = client.get_order(order_id)

            return {
                "success": "true",
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error getting order {order_id}: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def get_order_by_client_id(client_order_id: str) -> Dict[str, str]:
        """Get an order by client order ID.

        Args:
            client_order_id: The client-specified order ID.

        Returns:
            Order object with full details.
        """
        try:
            client = mcp.client
            result = client.get_order_by_client_id(client_order_id)

            return {
                "success": "true",
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error getting order by client ID {client_order_id}: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def replace_order(
        order_id: str,
        qty: Optional[float] = None,
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
        trail: Optional[float] = None,
        time_in_force: Optional[str] = None,
        client_order_id: Optional[str] = None,
    ) -> Dict[str, str]:
        """Replace/modify an existing order.

        Args:
            order_id: The order ID to replace
            qty: New quantity
            limit_price: New limit price
            stop_price: New stop price
            trail: New trail amount
            time_in_force: New time in force
            client_order_id: New client order ID

        Returns:
            New order object (replaces create a new order).
        """
        try:
            client = mcp.client
            result = client.replace_order(
                order_id=order_id,
                qty=qty,
                limit_price=limit_price,
                stop_price=stop_price,
                trail=trail,
                time_in_force=time_in_force,
                client_order_id=client_order_id,
            )

            return {
                "success": "true",
                "order_id": result.get("id", ""),
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error replacing order {order_id}: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def cancel_order(order_id: str) -> Dict[str, str]:
        """Cancel a specific order.

        Args:
            order_id: The order ID to cancel.

        Returns:
            Success or error status.
        """
        try:
            client = mcp.client
            client.cancel_order(order_id)

            return {
                "success": "true",
                "message": f"Order {order_id} cancelled",
            }
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def cancel_all_orders() -> Dict[str, str]:
        """Cancel all open orders.

        Returns:
            Count of cancelled orders.
        """
        try:
            client = mcp.client
            count = client.cancel_all_orders()

            return {
                "success": "true",
                "cancelled_count": str(count),
            }
        except Exception as e:
            logger.error(f"Error cancelling all orders: {e}")
            return {"success": "false", "error": str(e)}

    # -------------------------------------------------------------------------
    # Position Tools
    # -------------------------------------------------------------------------

    @mcp.tool()
    def list_positions() -> Dict[str, str]:
        """List all open positions.

        Returns:
            Array of position objects with symbol, qty, avg_entry_price,
            market_value, unrealized_pl, and other details.
        """
        try:
            client = mcp.client
            result = client.list_positions()

            return {
                "success": "true",
                "count": str(len(result)),
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error listing positions: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def get_position(symbol: str) -> Dict[str, str]:
        """Get position for a specific symbol.

        Args:
            symbol: Stock ticker symbol.

        Returns:
            Position object with qty, avg_entry_price, market_value, unrealized_pl.
        """
        try:
            client = mcp.client
            result = client.get_position(symbol)

            return {
                "success": "true",
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error getting position for {symbol}: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def close_position(
        symbol: str,
        qty: Optional[float] = None,
        percentage: Optional[float] = None,
    ) -> Dict[str, str]:
        """Close a position (sell all or partial shares).

        Args:
            symbol: Stock ticker symbol.
            qty: Number of shares to close (optional, closes all if not specified)
            percentage: Percentage of position to close (optional, 0-100)

        Returns:
            Order object for the closing trade.
        """
        try:
            client = mcp.client
            result = client.close_position(symbol, qty=qty, percentage=percentage)

            return {
                "success": "true",
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error closing position for {symbol}: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def close_all_positions(cancel_orders: bool = False) -> Dict[str, str]:
        """Liquidate all open positions.

        Args:
            cancel_orders: Also cancel all open orders (default: False)

        Returns:
            Array of closing order objects.
        """
        try:
            client = mcp.client
            result = client.close_all_positions(cancel_orders=cancel_orders)

            return {
                "success": "true",
                "count": str(len(result)),
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error closing all positions: {e}")
            return {"success": "false", "error": str(e)}

    # -------------------------------------------------------------------------
    # Watchlist Tools
    # -------------------------------------------------------------------------

    @mcp.tool()
    def list_watchlists() -> Dict[str, str]:
        """List all watchlists.

        Returns:
            Array of watchlist objects with id, name, and assets.
        """
        try:
            client = mcp.client
            result = client.list_watchlists()

            return {
                "success": "true",
                "count": str(len(result)),
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error listing watchlists: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def get_watchlist(watchlist_id: str) -> Dict[str, str]:
        """Get a specific watchlist by ID.

        Args:
            watchlist_id: The watchlist ID.

        Returns:
            Watchlist with id, name, and assets.
        """
        try:
            client = mcp.client
            result = client.get_watchlist(watchlist_id)

            return {
                "success": "true",
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error getting watchlist {watchlist_id}: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def create_watchlist(name: str, symbols: Optional[List[str]] = None) -> Dict[str, str]:
        """Create a new watchlist.

        Args:
            name: Name for the watchlist
            symbols: Initial symbols to add (optional)

        Returns:
            Created watchlist object.
        """
        try:
            client = mcp.client
            result = client.create_watchlist(name, symbols=symbols)

            return {
                "success": "true",
                "watchlist_id": result.get("id", ""),
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error creating watchlist: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def update_watchlist(
        watchlist_id: str,
        name: Optional[str] = None,
        symbols: Optional[List[str]] = None,
    ) -> Dict[str, str]:
        """Update a watchlist (replace symbols).

        Args:
            watchlist_id: The watchlist ID
            name: New name (optional)
            symbols: New list of symbols (replaces existing)

        Returns:
            Updated watchlist object.
        """
        try:
            client = mcp.client
            result = client.update_watchlist(watchlist_id, name=name, symbols=symbols)

            return {
                "success": "true",
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error updating watchlist {watchlist_id}: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def add_to_watchlist(watchlist_id: str, symbol: str) -> Dict[str, str]:
        """Add a symbol to a watchlist.

        Args:
            watchlist_id: The watchlist ID
            symbol: Symbol to add

        Returns:
            Updated watchlist object.
        """
        try:
            client = mcp.client
            result = client.add_to_watchlist(watchlist_id, symbol)

            return {
                "success": "true",
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error adding {symbol} to watchlist: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def remove_from_watchlist(watchlist_id: str, symbol: str) -> Dict[str, str]:
        """Remove a symbol from a watchlist.

        Args:
            watchlist_id: The watchlist ID
            symbol: Symbol to remove

        Returns:
            Updated watchlist or status.
        """
        try:
            client = mcp.client
            result = client.remove_from_watchlist(watchlist_id, symbol)

            return {
                "success": "true",
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error removing {symbol} from watchlist: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def delete_watchlist(watchlist_id: str) -> Dict[str, str]:
        """Delete a watchlist.

        Args:
            watchlist_id: The watchlist ID to delete

        Returns:
            Success status.
        """
        try:
            client = mcp.client
            client.delete_watchlist(watchlist_id)

            return {
                "success": "true",
                "message": f"Watchlist {watchlist_id} deleted",
            }
        except Exception as e:
            logger.error(f"Error deleting watchlist {watchlist_id}: {e}")
            return {"success": "false", "error": str(e)}

    # -------------------------------------------------------------------------
    # Stock Market Data Tools
    # -------------------------------------------------------------------------

    @mcp.tool()
    def get_bars(
        symbol: str,
        timeframe: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
        limit: int = 100,
        adjustment: str = "raw",
    ) -> Dict[str, str]:
        """Get historical price bars (OHLCV data) for a stock.

        Args:
            symbol: Stock ticker symbol
            timeframe: Bar timeframe - "1Min", "5Min", "15Min", "30Min", "1Hour", "1Day", "1Week", "1Month"
            start: Start date/time in ISO format (optional)
            end: End date/time in ISO format (optional)
            limit: Maximum number of bars (default: 100, max: 10000)
            adjustment: Price adjustment - "raw", "split", "dividend", "all" (default: "raw")

        Returns:
            Array of bars with timestamp, open, high, low, close, volume, vwap.
        """
        try:
            client = mcp.client
            result = client.get_bars(
                symbol=symbol,
                timeframe=timeframe,
                start=start,
                end=end,
                limit=limit,
                adjustment=adjustment,
            )

            return {
                "success": "true",
                "count": str(len(result)),
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error getting bars for {symbol}: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def get_latest_bar(symbol: str) -> Dict[str, str]:
        """Get the latest bar for a stock.

        Args:
            symbol: Stock ticker symbol

        Returns:
            Latest bar with open, high, low, close, volume, vwap.
        """
        try:
            client = mcp.client
            result = client.get_latest_bar(symbol)

            return {
                "success": "true",
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error getting latest bar for {symbol}: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def get_quotes(
        symbol: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
        limit: int = 100,
    ) -> Dict[str, str]:
        """Get historical quotes for a stock.

        Args:
            symbol: Stock ticker symbol
            start: Start date/time in ISO format (optional)
            end: End date/time in ISO format (optional)
            limit: Maximum number of quotes (default: 100)

        Returns:
            Array of quotes with bid/ask prices and sizes.
        """
        try:
            client = mcp.client
            result = client.get_quotes(
                symbol=symbol,
                start=start,
                end=end,
                limit=limit,
            )

            return {
                "success": "true",
                "count": str(len(result)),
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error getting quotes for {symbol}: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def get_latest_quote(symbol: str) -> Dict[str, str]:
        """Get latest quote for a stock.

        Args:
            symbol: Stock ticker symbol.

        Returns:
            Quote with bid_price, bid_size, ask_price, ask_size, timestamp.
        """
        try:
            client = mcp.client
            result = client.get_latest_quote(symbol)

            return {
                "success": "true",
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error getting quote for {symbol}: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def get_trades(
        symbol: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
        limit: int = 100,
    ) -> Dict[str, str]:
        """Get historical trades for a stock.

        Args:
            symbol: Stock ticker symbol
            start: Start date/time in ISO format (optional)
            end: End date/time in ISO format (optional)
            limit: Maximum number of trades (default: 100)

        Returns:
            Array of trades with price, size, timestamp.
        """
        try:
            client = mcp.client
            result = client.get_trades(
                symbol=symbol,
                start=start,
                end=end,
                limit=limit,
            )

            return {
                "success": "true",
                "count": str(len(result)),
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error getting trades for {symbol}: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def get_latest_trade(symbol: str) -> Dict[str, str]:
        """Get latest trade for a stock.

        Args:
            symbol: Stock ticker symbol.

        Returns:
            Trade with price, size, timestamp, exchange.
        """
        try:
            client = mcp.client
            result = client.get_latest_trade(symbol)

            return {
                "success": "true",
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error getting trade for {symbol}: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def get_snapshot(symbol: str) -> Dict[str, str]:
        """Get full market snapshot for a stock (quote + trade + bars).

        Args:
            symbol: Stock ticker symbol.

        Returns:
            Snapshot with latest_quote, latest_trade, minute_bar, daily_bar, prev_daily_bar.
        """
        try:
            client = mcp.client
            result = client.get_snapshot(symbol)

            return {
                "success": "true",
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error getting snapshot for {symbol}: {e}")
            return {"success": "false", "error": str(e)}

    # -------------------------------------------------------------------------
    # Crypto Market Data Tools
    # -------------------------------------------------------------------------

    @mcp.tool()
    def get_crypto_bars(
        symbol: str,
        timeframe: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
        limit: int = 100,
    ) -> Dict[str, str]:
        """Get historical price bars for cryptocurrency.

        Args:
            symbol: Crypto symbol (e.g., "BTC/USD", "ETH/USD")
            timeframe: Bar timeframe - "1Min", "5Min", "15Min", "1Hour", "1Day"
            start: Start date/time in ISO format (optional)
            end: End date/time in ISO format (optional)
            limit: Maximum number of bars (default: 100)

        Returns:
            Array of bars with timestamp, open, high, low, close, volume.
        """
        try:
            client = mcp.client
            result = client.get_crypto_bars(
                symbol=symbol,
                timeframe=timeframe,
                start=start,
                end=end,
                limit=limit,
            )

            return {
                "success": "true",
                "count": str(len(result)),
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error getting crypto bars for {symbol}: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def get_crypto_latest_bar(symbol: str) -> Dict[str, str]:
        """Get latest bar for cryptocurrency.

        Args:
            symbol: Crypto symbol (e.g., "BTC/USD")

        Returns:
            Latest bar with open, high, low, close, volume.
        """
        try:
            client = mcp.client
            result = client.get_crypto_latest_bar(symbol)

            return {
                "success": "true",
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error getting crypto latest bar for {symbol}: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def get_crypto_latest_quote(symbol: str) -> Dict[str, str]:
        """Get latest quote for cryptocurrency.

        Args:
            symbol: Crypto symbol (e.g., "BTC/USD")

        Returns:
            Quote with bid/ask prices and sizes.
        """
        try:
            client = mcp.client
            result = client.get_crypto_latest_quote(symbol)

            return {
                "success": "true",
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error getting crypto quote for {symbol}: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def get_crypto_latest_trade(symbol: str) -> Dict[str, str]:
        """Get latest trade for cryptocurrency.

        Args:
            symbol: Crypto symbol (e.g., "BTC/USD")

        Returns:
            Trade with price, size, timestamp.
        """
        try:
            client = mcp.client
            result = client.get_crypto_latest_trade(symbol)

            return {
                "success": "true",
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error getting crypto trade for {symbol}: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def get_crypto_snapshot(symbol: str) -> Dict[str, str]:
        """Get full market snapshot for cryptocurrency.

        Args:
            symbol: Crypto symbol (e.g., "BTC/USD")

        Returns:
            Snapshot with latest_quote, latest_trade, minute_bar, daily_bar.
        """
        try:
            client = mcp.client
            result = client.get_crypto_snapshot(symbol)

            return {
                "success": "true",
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error getting crypto snapshot for {symbol}: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def get_crypto_orderbook(symbol: str) -> Dict[str, str]:
        """Get cryptocurrency orderbook (bid/ask depth).

        Args:
            symbol: Crypto symbol (e.g., "BTC/USD")

        Returns:
            Orderbook with bids and asks arrays.
        """
        try:
            client = mcp.client
            result = client.get_crypto_orderbook(symbol)

            return {
                "success": "true",
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error getting crypto orderbook for {symbol}: {e}")
            return {"success": "false", "error": str(e)}

    # -------------------------------------------------------------------------
    # Options Tools
    # -------------------------------------------------------------------------

    @mcp.tool()
    def get_option_contracts(
        underlying_symbol: Optional[str] = None,
        expiration_date: Optional[str] = None,
        expiration_date_gte: Optional[str] = None,
        expiration_date_lte: Optional[str] = None,
        strike_price_gte: Optional[float] = None,
        strike_price_lte: Optional[float] = None,
        option_type: Optional[str] = None,
        limit: int = 100,
    ) -> Dict[str, str]:
        """Get available option contracts.

        Args:
            underlying_symbol: Filter by underlying stock (e.g., "AAPL")
            expiration_date: Exact expiration date (YYYY-MM-DD)
            expiration_date_gte: Expiration on or after date
            expiration_date_lte: Expiration on or before date
            strike_price_gte: Strike price greater than or equal
            strike_price_lte: Strike price less than or equal
            option_type: "call" or "put"
            limit: Maximum contracts to return (default: 100)

        Returns:
            Array of option contracts with symbol, strike, expiration, type.
        """
        try:
            client = mcp.client
            result = client.get_option_contracts(
                underlying_symbol=underlying_symbol,
                expiration_date=expiration_date,
                expiration_date_gte=expiration_date_gte,
                expiration_date_lte=expiration_date_lte,
                strike_price_gte=strike_price_gte,
                strike_price_lte=strike_price_lte,
                option_type=option_type,
                limit=limit,
            )

            return {
                "success": "true",
                "count": str(len(result)),
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error getting option contracts: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def get_option_contract(symbol_or_id: str) -> Dict[str, str]:
        """Get a specific option contract.

        Args:
            symbol_or_id: Option symbol (OCC format) or contract ID

        Returns:
            Option contract details.
        """
        try:
            client = mcp.client
            result = client.get_option_contract(symbol_or_id)

            return {
                "success": "true",
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error getting option contract {symbol_or_id}: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def create_option_order(
        symbol: str,
        side: str,
        order_type: str,
        time_in_force: str,
        qty: int,
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
    ) -> Dict[str, str]:
        """Place an option order.

        Args:
            symbol: Option symbol in OCC format (e.g., "AAPL230120C00150000")
            side: "buy" or "sell"
            order_type: "market", "limit", "stop", "stop_limit"
            time_in_force: "day", "gtc", "ioc", "fok"
            qty: Number of contracts
            limit_price: Limit price per contract (for limit orders)
            stop_price: Stop price (for stop orders)

        Returns:
            Order object with id and status.
        """
        try:
            client = mcp.client
            result = client.create_option_order(
                symbol=symbol,
                side=side,
                order_type=order_type,
                time_in_force=time_in_force,
                qty=qty,
                limit_price=limit_price,
                stop_price=stop_price,
            )

            return {
                "success": "true",
                "order_id": result.get("id", ""),
                "status": result.get("status", ""),
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error creating option order: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def exercise_option(symbol_or_id: str) -> Dict[str, str]:
        """Exercise an option position.

        Args:
            symbol_or_id: Option symbol or position ID to exercise

        Returns:
            Exercise confirmation.
        """
        try:
            client = mcp.client
            result = client.exercise_option(symbol_or_id)

            return {
                "success": "true",
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error exercising option {symbol_or_id}: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def get_option_latest_quote(symbol: str) -> Dict[str, str]:
        """Get latest quote for an option.

        Args:
            symbol: Option symbol in OCC format

        Returns:
            Quote with bid/ask prices and sizes.
        """
        try:
            client = mcp.client
            result = client.get_option_latest_quote(symbol)

            return {
                "success": "true",
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error getting option quote for {symbol}: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def get_option_snapshot(symbol: str) -> Dict[str, str]:
        """Get option snapshot including Greeks.

        Args:
            symbol: Option symbol in OCC format

        Returns:
            Snapshot with quote, trade, and greeks (delta, gamma, theta, vega, rho).
        """
        try:
            client = mcp.client
            result = client.get_option_snapshot(symbol)

            return {
                "success": "true",
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error getting option snapshot for {symbol}: {e}")
            return {"success": "false", "error": str(e)}

    # -------------------------------------------------------------------------
    # Asset Tools
    # -------------------------------------------------------------------------

    @mcp.tool()
    def list_assets(
        status: Optional[str] = None,
        asset_class: Optional[str] = None,
        exchange: Optional[str] = None,
    ) -> Dict[str, str]:
        """List tradable assets.

        Args:
            status: Filter by status - "active" or "inactive" (optional)
            asset_class: Filter by class - "us_equity", "crypto" (optional)
            exchange: Filter by exchange (optional)

        Returns:
            Array of asset objects (limited to first 100 for display).
        """
        try:
            client = mcp.client
            result = client.list_assets(status=status, asset_class=asset_class, exchange=exchange)

            return {
                "success": "true",
                "count": str(len(result)),
                "data": json.dumps(result[:100], indent=2),
                "note": f"Showing first 100 of {len(result)} assets" if len(result) > 100 else "",
            }
        except Exception as e:
            logger.error(f"Error listing assets: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def get_asset(symbol: str) -> Dict[str, str]:
        """Get asset details for a symbol.

        Args:
            symbol: Stock ticker symbol.

        Returns:
            Asset with id, symbol, name, exchange, tradable, fractionable, marginable, shortable.
        """
        try:
            client = mcp.client
            result = client.get_asset(symbol)

            return {
                "success": "true",
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error getting asset {symbol}: {e}")
            return {"success": "false", "error": str(e)}

    # -------------------------------------------------------------------------
    # Market Info Tools
    # -------------------------------------------------------------------------

    @mcp.tool()
    def get_clock() -> Dict[str, str]:
        """Get market clock (current time, open/close status).

        Returns:
            Clock with is_open, next_open, next_close, timestamp.
        """
        try:
            client = mcp.client
            result = client.get_clock()

            return {
                "success": "true",
                "is_open": str(result.get("is_open", False)).lower(),
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error getting clock: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def get_calendar(
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> Dict[str, str]:
        """Get market calendar (trading days and hours).

        Args:
            start: Start date in YYYY-MM-DD format (optional)
            end: End date in YYYY-MM-DD format (optional)

        Returns:
            Array of calendar days with date, open time, close time.
        """
        try:
            client = mcp.client
            result = client.get_calendar(start=start, end=end)

            return {
                "success": "true",
                "count": str(len(result)),
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error getting calendar: {e}")
            return {"success": "false", "error": str(e)}

    # -------------------------------------------------------------------------
    # Corporate Actions Tools
    # -------------------------------------------------------------------------

    @mcp.tool()
    def get_corporate_actions(
        symbols: Optional[List[str]] = None,
        types: Optional[List[str]] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        limit: int = 100,
    ) -> Dict[str, str]:
        """Get corporate actions (dividends, splits, spinoffs, mergers).

        Args:
            symbols: Filter by symbols (optional)
            types: Filter by types - "dividend", "split", "spinoff", "merger" (optional)
            start: Start date in YYYY-MM-DD format
            end: End date in YYYY-MM-DD format
            limit: Maximum results (default: 100)

        Returns:
            Corporate actions organized by type.
        """
        try:
            client = mcp.client
            result = client.get_corporate_actions(
                symbols=symbols,
                types=types,
                start=start,
                end=end,
                limit=limit,
            )

            return {
                "success": "true",
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error getting corporate actions: {e}")
            return {"success": "false", "error": str(e)}

    logger.info("Registered 47 Alpaca MCP tools")
