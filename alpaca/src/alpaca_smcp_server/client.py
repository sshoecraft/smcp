"""Alpaca Markets API client wrapper."""

import logging
from dataclasses import dataclass
from typing import Dict, List, Any, Optional

import requests

logger = logging.getLogger(__name__)

PAPER_TRADING_URL = "https://paper-api.alpaca.markets"
LIVE_TRADING_URL = "https://api.alpaca.markets"
DATA_URL = "https://data.alpaca.markets"


@dataclass
class AlpacaConfig:
    """Configuration for Alpaca API."""

    api_key: str
    secret_key: str
    paper: bool = True

    @classmethod
    def from_smcp_creds(cls, creds: Dict[str, str]) -> "AlpacaConfig":
        """Create config from SMCP credentials."""
        api_key = creds.get("ALPACA_API_KEY", "")
        secret_key = creds.get("ALPACA_SECRET_KEY", "")

        if not api_key:
            raise ValueError("ALPACA_API_KEY is required")
        if not secret_key:
            raise ValueError("ALPACA_SECRET_KEY is required")

        # Default to paper trading for safety
        paper_str = creds.get("ALPACA_PAPER", "true").lower()
        paper = paper_str in ("true", "1", "yes")

        return cls(api_key=api_key, secret_key=secret_key, paper=paper)


class AlpacaClient:
    """Client for Alpaca Markets API."""

    def __init__(self, config: AlpacaConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update(self._headers())

        mode = "paper" if config.paper else "LIVE"
        logger.info(f"Alpaca client initialized ({mode} trading)")

    def _headers(self) -> Dict[str, str]:
        """Get authentication headers."""
        return {
            "APCA-API-KEY-ID": self.config.api_key,
            "APCA-API-SECRET-KEY": self.config.secret_key,
        }

    def _trading_url(self) -> str:
        """Get trading API base URL."""
        return PAPER_TRADING_URL if self.config.paper else LIVE_TRADING_URL

    def _data_url(self) -> str:
        """Get market data API base URL."""
        return DATA_URL

    def _request(
        self,
        method: str,
        url: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
    ) -> Any:
        """Make an authenticated request."""
        logger.debug(f"API request: {method} {url}")

        response = self.session.request(
            method=method,
            url=url,
            params=params,
            json=json_data,
            timeout=30,
        )

        # Handle errors
        if not response.ok:
            try:
                error_data = response.json()
                error_msg = error_data.get("message", response.text)
            except Exception:
                error_msg = response.text
            raise ValueError(f"API error ({response.status_code}): {error_msg}")

        # Handle empty responses (e.g., DELETE)
        if response.status_code == 204 or not response.content:
            return None

        return response.json()

    # -------------------------------------------------------------------------
    # Account Methods
    # -------------------------------------------------------------------------

    def get_account(self) -> Dict[str, Any]:
        """Get account information."""
        url = f"{self._trading_url()}/v2/account"
        data = self._request("GET", url)

        return {
            "id": data.get("id"),
            "account_number": data.get("account_number"),
            "status": data.get("status"),
            "currency": data.get("currency"),
            "buying_power": float(data.get("buying_power", 0)),
            "cash": float(data.get("cash", 0)),
            "portfolio_value": float(data.get("portfolio_value", 0)),
            "equity": float(data.get("equity", 0)),
            "last_equity": float(data.get("last_equity", 0)),
            "long_market_value": float(data.get("long_market_value", 0)),
            "short_market_value": float(data.get("short_market_value", 0)),
            "pattern_day_trader": data.get("pattern_day_trader", False),
            "trading_blocked": data.get("trading_blocked", False),
            "transfers_blocked": data.get("transfers_blocked", False),
            "account_blocked": data.get("account_blocked", False),
            "daytrade_count": data.get("daytrade_count", 0),
            "daytrading_buying_power": float(data.get("daytrading_buying_power", 0)),
            "regt_buying_power": float(data.get("regt_buying_power", 0)),
        }

    def get_portfolio_history(
        self,
        period: Optional[str] = None,
        timeframe: Optional[str] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        extended_hours: bool = False,
    ) -> Dict[str, Any]:
        """Get portfolio history."""
        url = f"{self._trading_url()}/v2/account/portfolio/history"
        params = {}
        if period:
            params["period"] = period
        if timeframe:
            params["timeframe"] = timeframe
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        if extended_hours:
            params["extended_hours"] = "true"

        data = self._request("GET", url, params=params if params else None)

        return {
            "timestamp": data.get("timestamp", []),
            "equity": data.get("equity", []),
            "profit_loss": data.get("profit_loss", []),
            "profit_loss_pct": data.get("profit_loss_pct", []),
            "base_value": data.get("base_value", 0),
            "timeframe": data.get("timeframe"),
        }

    # -------------------------------------------------------------------------
    # Order Methods
    # -------------------------------------------------------------------------

    def create_order(
        self,
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
    ) -> Dict[str, Any]:
        """Create a new order."""
        url = f"{self._trading_url()}/v2/orders"

        order_data = {
            "symbol": symbol.upper(),
            "side": side.lower(),
            "type": order_type.lower(),
            "time_in_force": time_in_force.lower(),
        }

        if qty is not None:
            order_data["qty"] = str(qty)
        if notional is not None:
            order_data["notional"] = str(notional)
        if limit_price is not None:
            order_data["limit_price"] = str(limit_price)
        if stop_price is not None:
            order_data["stop_price"] = str(stop_price)
        if trail_price is not None:
            order_data["trail_price"] = str(trail_price)
        if trail_percent is not None:
            order_data["trail_percent"] = str(trail_percent)
        if extended_hours:
            order_data["extended_hours"] = True
        if client_order_id:
            order_data["client_order_id"] = client_order_id

        data = self._request("POST", url, json_data=order_data)
        return self._format_order(data)

    def list_orders(
        self,
        status: str = "open",
        limit: int = 50,
        symbols: Optional[List[str]] = None,
        after: Optional[str] = None,
        until: Optional[str] = None,
        direction: str = "desc",
        nested: bool = False,
    ) -> List[Dict[str, Any]]:
        """List orders."""
        url = f"{self._trading_url()}/v2/orders"
        params = {
            "status": status,
            "limit": limit,
            "direction": direction,
        }
        if symbols:
            params["symbols"] = ",".join(s.upper() for s in symbols)
        if after:
            params["after"] = after
        if until:
            params["until"] = until
        if nested:
            params["nested"] = "true"

        data = self._request("GET", url, params=params)
        return [self._format_order(order) for order in data]

    def get_order(self, order_id: str) -> Dict[str, Any]:
        """Get a specific order."""
        url = f"{self._trading_url()}/v2/orders/{order_id}"
        data = self._request("GET", url)
        return self._format_order(data)

    def get_order_by_client_id(self, client_order_id: str) -> Dict[str, Any]:
        """Get order by client order ID."""
        url = f"{self._trading_url()}/v2/orders:by_client_order_id"
        params = {"client_order_id": client_order_id}
        data = self._request("GET", url, params=params)
        return self._format_order(data)

    def replace_order(
        self,
        order_id: str,
        qty: Optional[float] = None,
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
        trail: Optional[float] = None,
        time_in_force: Optional[str] = None,
        client_order_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Replace/modify an existing order."""
        url = f"{self._trading_url()}/v2/orders/{order_id}"
        order_data = {}

        if qty is not None:
            order_data["qty"] = str(qty)
        if limit_price is not None:
            order_data["limit_price"] = str(limit_price)
        if stop_price is not None:
            order_data["stop_price"] = str(stop_price)
        if trail is not None:
            order_data["trail"] = str(trail)
        if time_in_force:
            order_data["time_in_force"] = time_in_force.lower()
        if client_order_id:
            order_data["client_order_id"] = client_order_id

        data = self._request("PATCH", url, json_data=order_data)
        return self._format_order(data)

    def cancel_order(self, order_id: str) -> None:
        """Cancel a specific order."""
        url = f"{self._trading_url()}/v2/orders/{order_id}"
        self._request("DELETE", url)

    def cancel_all_orders(self) -> int:
        """Cancel all open orders. Returns count of cancelled orders."""
        url = f"{self._trading_url()}/v2/orders"
        data = self._request("DELETE", url)
        return len(data) if data else 0

    def _format_order(self, data: Dict) -> Dict[str, Any]:
        """Format order response."""
        return {
            "id": data.get("id"),
            "client_order_id": data.get("client_order_id"),
            "symbol": data.get("symbol"),
            "asset_class": data.get("asset_class"),
            "side": data.get("side"),
            "type": data.get("type"),
            "time_in_force": data.get("time_in_force"),
            "qty": data.get("qty"),
            "filled_qty": data.get("filled_qty"),
            "filled_avg_price": data.get("filled_avg_price"),
            "limit_price": data.get("limit_price"),
            "stop_price": data.get("stop_price"),
            "trail_price": data.get("trail_price"),
            "trail_percent": data.get("trail_percent"),
            "status": data.get("status"),
            "created_at": data.get("created_at"),
            "updated_at": data.get("updated_at"),
            "submitted_at": data.get("submitted_at"),
            "filled_at": data.get("filled_at"),
            "expired_at": data.get("expired_at"),
            "canceled_at": data.get("canceled_at"),
            "extended_hours": data.get("extended_hours", False),
            "legs": data.get("legs"),
        }

    # -------------------------------------------------------------------------
    # Position Methods
    # -------------------------------------------------------------------------

    def list_positions(self) -> List[Dict[str, Any]]:
        """List all open positions."""
        url = f"{self._trading_url()}/v2/positions"
        data = self._request("GET", url)
        return [self._format_position(pos) for pos in data]

    def get_position(self, symbol: str) -> Dict[str, Any]:
        """Get position for a specific symbol."""
        url = f"{self._trading_url()}/v2/positions/{symbol.upper()}"
        data = self._request("GET", url)
        return self._format_position(data)

    def close_position(
        self,
        symbol: str,
        qty: Optional[float] = None,
        percentage: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Close a position."""
        url = f"{self._trading_url()}/v2/positions/{symbol.upper()}"
        params = {}
        if qty is not None:
            params["qty"] = str(qty)
        if percentage is not None:
            params["percentage"] = str(percentage)

        data = self._request("DELETE", url, params=params if params else None)
        return self._format_order(data) if data else {"status": "closed"}

    def close_all_positions(self, cancel_orders: bool = False) -> List[Dict[str, Any]]:
        """Close all positions."""
        url = f"{self._trading_url()}/v2/positions"
        params = {}
        if cancel_orders:
            params["cancel_orders"] = "true"
        data = self._request("DELETE", url, params=params if params else None)
        return data if data else []

    def _format_position(self, data: Dict) -> Dict[str, Any]:
        """Format position response."""
        return {
            "asset_id": data.get("asset_id"),
            "symbol": data.get("symbol"),
            "exchange": data.get("exchange"),
            "asset_class": data.get("asset_class"),
            "qty": float(data.get("qty", 0)),
            "avg_entry_price": float(data.get("avg_entry_price", 0)),
            "side": data.get("side"),
            "market_value": float(data.get("market_value", 0)),
            "cost_basis": float(data.get("cost_basis", 0)),
            "unrealized_pl": float(data.get("unrealized_pl", 0)),
            "unrealized_plpc": float(data.get("unrealized_plpc", 0)),
            "unrealized_intraday_pl": float(data.get("unrealized_intraday_pl", 0)),
            "unrealized_intraday_plpc": float(data.get("unrealized_intraday_plpc", 0)),
            "current_price": float(data.get("current_price", 0)),
            "lastday_price": float(data.get("lastday_price", 0)),
            "change_today": float(data.get("change_today", 0)),
        }

    # -------------------------------------------------------------------------
    # Watchlist Methods
    # -------------------------------------------------------------------------

    def list_watchlists(self) -> List[Dict[str, Any]]:
        """List all watchlists."""
        url = f"{self._trading_url()}/v2/watchlists"
        data = self._request("GET", url)
        return [self._format_watchlist(wl) for wl in data]

    def get_watchlist(self, watchlist_id: str) -> Dict[str, Any]:
        """Get a specific watchlist."""
        url = f"{self._trading_url()}/v2/watchlists/{watchlist_id}"
        data = self._request("GET", url)
        return self._format_watchlist(data)

    def create_watchlist(self, name: str, symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create a new watchlist."""
        url = f"{self._trading_url()}/v2/watchlists"
        watchlist_data = {"name": name}
        if symbols:
            watchlist_data["symbols"] = [s.upper() for s in symbols]

        data = self._request("POST", url, json_data=watchlist_data)
        return self._format_watchlist(data)

    def update_watchlist(
        self,
        watchlist_id: str,
        name: Optional[str] = None,
        symbols: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Update a watchlist."""
        url = f"{self._trading_url()}/v2/watchlists/{watchlist_id}"
        watchlist_data = {}
        if name:
            watchlist_data["name"] = name
        if symbols is not None:
            watchlist_data["symbols"] = [s.upper() for s in symbols]

        data = self._request("PUT", url, json_data=watchlist_data)
        return self._format_watchlist(data)

    def add_to_watchlist(self, watchlist_id: str, symbol: str) -> Dict[str, Any]:
        """Add a symbol to a watchlist."""
        url = f"{self._trading_url()}/v2/watchlists/{watchlist_id}"
        data = self._request("POST", url, json_data={"symbol": symbol.upper()})
        return self._format_watchlist(data)

    def remove_from_watchlist(self, watchlist_id: str, symbol: str) -> Dict[str, Any]:
        """Remove a symbol from a watchlist."""
        url = f"{self._trading_url()}/v2/watchlists/{watchlist_id}/{symbol.upper()}"
        data = self._request("DELETE", url)
        return self._format_watchlist(data) if data else {"status": "removed"}

    def delete_watchlist(self, watchlist_id: str) -> None:
        """Delete a watchlist."""
        url = f"{self._trading_url()}/v2/watchlists/{watchlist_id}"
        self._request("DELETE", url)

    def _format_watchlist(self, data: Dict) -> Dict[str, Any]:
        """Format watchlist response."""
        return {
            "id": data.get("id"),
            "account_id": data.get("account_id"),
            "name": data.get("name"),
            "created_at": data.get("created_at"),
            "updated_at": data.get("updated_at"),
            "assets": data.get("assets", []),
        }

    # -------------------------------------------------------------------------
    # Stock Market Data Methods
    # -------------------------------------------------------------------------

    def get_bars(
        self,
        symbol: str,
        timeframe: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
        limit: int = 100,
        adjustment: str = "raw",
        feed: str = "iex",
    ) -> List[Dict[str, Any]]:
        """Get historical bars."""
        url = f"{self._data_url()}/v2/stocks/{symbol.upper()}/bars"
        params = {
            "timeframe": timeframe,
            "limit": limit,
            "adjustment": adjustment,
            "feed": feed,
        }
        if start:
            params["start"] = start
        if end:
            params["end"] = end

        data = self._request("GET", url, params=params)
        bars = data.get("bars", [])

        return [self._format_bar(bar) for bar in bars]

    def get_latest_bar(self, symbol: str, feed: str = "iex") -> Dict[str, Any]:
        """Get latest bar for a symbol."""
        url = f"{self._data_url()}/v2/stocks/{symbol.upper()}/bars/latest"
        params = {"feed": feed}
        data = self._request("GET", url, params=params)
        bar = data.get("bar", {})
        result = self._format_bar(bar)
        result["symbol"] = symbol.upper()
        return result

    def get_quotes(
        self,
        symbol: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
        limit: int = 100,
        feed: str = "iex",
    ) -> List[Dict[str, Any]]:
        """Get historical quotes."""
        url = f"{self._data_url()}/v2/stocks/{symbol.upper()}/quotes"
        params = {"limit": limit, "feed": feed}
        if start:
            params["start"] = start
        if end:
            params["end"] = end

        data = self._request("GET", url, params=params)
        quotes = data.get("quotes", [])
        return [self._format_quote(q) for q in quotes]

    def get_latest_quote(self, symbol: str, feed: str = "iex") -> Dict[str, Any]:
        """Get latest quote for a symbol."""
        url = f"{self._data_url()}/v2/stocks/{symbol.upper()}/quotes/latest"
        params = {"feed": feed}
        data = self._request("GET", url, params=params)
        quote = data.get("quote", {})

        return {
            "symbol": symbol.upper(),
            "bid_price": float(quote.get("bp", 0)),
            "bid_size": int(quote.get("bs", 0)),
            "ask_price": float(quote.get("ap", 0)),
            "ask_size": int(quote.get("as", 0)),
            "timestamp": quote.get("t"),
            "conditions": quote.get("c", []),
        }

    def get_trades(
        self,
        symbol: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
        limit: int = 100,
        feed: str = "iex",
    ) -> List[Dict[str, Any]]:
        """Get historical trades."""
        url = f"{self._data_url()}/v2/stocks/{symbol.upper()}/trades"
        params = {"limit": limit, "feed": feed}
        if start:
            params["start"] = start
        if end:
            params["end"] = end

        data = self._request("GET", url, params=params)
        trades = data.get("trades", [])
        return [self._format_trade(t) for t in trades]

    def get_latest_trade(self, symbol: str, feed: str = "iex") -> Dict[str, Any]:
        """Get latest trade for a symbol."""
        url = f"{self._data_url()}/v2/stocks/{symbol.upper()}/trades/latest"
        params = {"feed": feed}
        data = self._request("GET", url, params=params)
        trade = data.get("trade", {})

        return {
            "symbol": symbol.upper(),
            "price": float(trade.get("p", 0)),
            "size": int(trade.get("s", 0)),
            "timestamp": trade.get("t"),
            "exchange": trade.get("x"),
            "conditions": trade.get("c", []),
        }

    def get_snapshot(self, symbol: str, feed: str = "iex") -> Dict[str, Any]:
        """Get market snapshot for a symbol."""
        url = f"{self._data_url()}/v2/stocks/{symbol.upper()}/snapshot"
        params = {"feed": feed}
        data = self._request("GET", url, params=params)

        result = {"symbol": symbol.upper()}

        if "latestQuote" in data:
            q = data["latestQuote"]
            result["latest_quote"] = {
                "bid_price": float(q.get("bp", 0)),
                "bid_size": int(q.get("bs", 0)),
                "ask_price": float(q.get("ap", 0)),
                "ask_size": int(q.get("as", 0)),
                "timestamp": q.get("t"),
            }

        if "latestTrade" in data:
            t = data["latestTrade"]
            result["latest_trade"] = {
                "price": float(t.get("p", 0)),
                "size": int(t.get("s", 0)),
                "timestamp": t.get("t"),
            }

        if "minuteBar" in data:
            result["minute_bar"] = self._format_bar(data["minuteBar"])

        if "dailyBar" in data:
            result["daily_bar"] = self._format_bar(data["dailyBar"])

        if "prevDailyBar" in data:
            result["prev_daily_bar"] = self._format_bar(data["prevDailyBar"])

        return result

    def _format_bar(self, bar: Dict) -> Dict[str, Any]:
        """Format bar data."""
        return {
            "timestamp": bar.get("t"),
            "open": float(bar.get("o", 0)),
            "high": float(bar.get("h", 0)),
            "low": float(bar.get("l", 0)),
            "close": float(bar.get("c", 0)),
            "volume": int(bar.get("v", 0)),
            "vwap": float(bar.get("vw", 0)),
            "trade_count": int(bar.get("n", 0)),
        }

    def _format_quote(self, quote: Dict) -> Dict[str, Any]:
        """Format quote data."""
        return {
            "timestamp": quote.get("t"),
            "bid_price": float(quote.get("bp", 0)),
            "bid_size": int(quote.get("bs", 0)),
            "ask_price": float(quote.get("ap", 0)),
            "ask_size": int(quote.get("as", 0)),
            "conditions": quote.get("c", []),
        }

    def _format_trade(self, trade: Dict) -> Dict[str, Any]:
        """Format trade data."""
        return {
            "timestamp": trade.get("t"),
            "price": float(trade.get("p", 0)),
            "size": int(trade.get("s", 0)),
            "exchange": trade.get("x"),
            "conditions": trade.get("c", []),
        }

    # -------------------------------------------------------------------------
    # Crypto Market Data Methods
    # -------------------------------------------------------------------------

    def get_crypto_bars(
        self,
        symbol: str,
        timeframe: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get crypto historical bars."""
        # Crypto symbols use format like BTC/USD
        url = f"{self._data_url()}/v1beta3/crypto/us/bars"
        params = {
            "symbols": symbol.upper(),
            "timeframe": timeframe,
            "limit": limit,
        }
        if start:
            params["start"] = start
        if end:
            params["end"] = end

        data = self._request("GET", url, params=params)
        bars = data.get("bars", {}).get(symbol.upper(), [])
        return [self._format_bar(bar) for bar in bars]

    def get_crypto_latest_bar(self, symbol: str) -> Dict[str, Any]:
        """Get latest crypto bar."""
        url = f"{self._data_url()}/v1beta3/crypto/us/latest/bars"
        params = {"symbols": symbol.upper()}
        data = self._request("GET", url, params=params)
        bar = data.get("bars", {}).get(symbol.upper(), {})
        result = self._format_bar(bar)
        result["symbol"] = symbol.upper()
        return result

    def get_crypto_quotes(
        self,
        symbol: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get crypto historical quotes."""
        url = f"{self._data_url()}/v1beta3/crypto/us/quotes"
        params = {"symbols": symbol.upper(), "limit": limit}
        if start:
            params["start"] = start
        if end:
            params["end"] = end

        data = self._request("GET", url, params=params)
        quotes = data.get("quotes", {}).get(symbol.upper(), [])
        return [self._format_quote(q) for q in quotes]

    def get_crypto_latest_quote(self, symbol: str) -> Dict[str, Any]:
        """Get latest crypto quote."""
        url = f"{self._data_url()}/v1beta3/crypto/us/latest/quotes"
        params = {"symbols": symbol.upper()}
        data = self._request("GET", url, params=params)
        quote = data.get("quotes", {}).get(symbol.upper(), {})

        return {
            "symbol": symbol.upper(),
            "bid_price": float(quote.get("bp", 0)),
            "bid_size": float(quote.get("bs", 0)),
            "ask_price": float(quote.get("ap", 0)),
            "ask_size": float(quote.get("as", 0)),
            "timestamp": quote.get("t"),
        }

    def get_crypto_trades(
        self,
        symbol: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get crypto historical trades."""
        url = f"{self._data_url()}/v1beta3/crypto/us/trades"
        params = {"symbols": symbol.upper(), "limit": limit}
        if start:
            params["start"] = start
        if end:
            params["end"] = end

        data = self._request("GET", url, params=params)
        trades = data.get("trades", {}).get(symbol.upper(), [])
        return [self._format_trade(t) for t in trades]

    def get_crypto_latest_trade(self, symbol: str) -> Dict[str, Any]:
        """Get latest crypto trade."""
        url = f"{self._data_url()}/v1beta3/crypto/us/latest/trades"
        params = {"symbols": symbol.upper()}
        data = self._request("GET", url, params=params)
        trade = data.get("trades", {}).get(symbol.upper(), {})

        return {
            "symbol": symbol.upper(),
            "price": float(trade.get("p", 0)),
            "size": float(trade.get("s", 0)),
            "timestamp": trade.get("t"),
            "taker_side": trade.get("tks"),
        }

    def get_crypto_snapshot(self, symbol: str) -> Dict[str, Any]:
        """Get crypto snapshot."""
        url = f"{self._data_url()}/v1beta3/crypto/us/snapshots"
        params = {"symbols": symbol.upper()}
        data = self._request("GET", url, params=params)
        snapshot = data.get("snapshots", {}).get(symbol.upper(), {})

        result = {"symbol": symbol.upper()}

        if "latestQuote" in snapshot:
            q = snapshot["latestQuote"]
            result["latest_quote"] = {
                "bid_price": float(q.get("bp", 0)),
                "bid_size": float(q.get("bs", 0)),
                "ask_price": float(q.get("ap", 0)),
                "ask_size": float(q.get("as", 0)),
                "timestamp": q.get("t"),
            }

        if "latestTrade" in snapshot:
            t = snapshot["latestTrade"]
            result["latest_trade"] = {
                "price": float(t.get("p", 0)),
                "size": float(t.get("s", 0)),
                "timestamp": t.get("t"),
            }

        if "minuteBar" in snapshot:
            result["minute_bar"] = self._format_bar(snapshot["minuteBar"])

        if "dailyBar" in snapshot:
            result["daily_bar"] = self._format_bar(snapshot["dailyBar"])

        if "prevDailyBar" in snapshot:
            result["prev_daily_bar"] = self._format_bar(snapshot["prevDailyBar"])

        return result

    def get_crypto_orderbook(self, symbol: str) -> Dict[str, Any]:
        """Get crypto orderbook."""
        url = f"{self._data_url()}/v1beta3/crypto/us/latest/orderbooks"
        params = {"symbols": symbol.upper()}
        data = self._request("GET", url, params=params)
        orderbook = data.get("orderbooks", {}).get(symbol.upper(), {})

        return {
            "symbol": symbol.upper(),
            "timestamp": orderbook.get("t"),
            "bids": [{"price": float(b.get("p", 0)), "size": float(b.get("s", 0))} for b in orderbook.get("b", [])],
            "asks": [{"price": float(a.get("p", 0)), "size": float(a.get("s", 0))} for a in orderbook.get("a", [])],
        }

    # -------------------------------------------------------------------------
    # Options Methods
    # -------------------------------------------------------------------------

    def get_option_contracts(
        self,
        underlying_symbol: Optional[str] = None,
        expiration_date: Optional[str] = None,
        expiration_date_gte: Optional[str] = None,
        expiration_date_lte: Optional[str] = None,
        strike_price_gte: Optional[float] = None,
        strike_price_lte: Optional[float] = None,
        option_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get option contracts."""
        url = f"{self._trading_url()}/v2/options/contracts"
        params = {"limit": limit}

        if underlying_symbol:
            params["underlying_symbols"] = underlying_symbol.upper()
        if expiration_date:
            params["expiration_date"] = expiration_date
        if expiration_date_gte:
            params["expiration_date_gte"] = expiration_date_gte
        if expiration_date_lte:
            params["expiration_date_lte"] = expiration_date_lte
        if strike_price_gte is not None:
            params["strike_price_gte"] = str(strike_price_gte)
        if strike_price_lte is not None:
            params["strike_price_lte"] = str(strike_price_lte)
        if option_type:
            params["type"] = option_type.lower()

        data = self._request("GET", url, params=params)
        contracts = data.get("option_contracts", [])

        return [self._format_option_contract(c) for c in contracts]

    def get_option_contract(self, symbol_or_id: str) -> Dict[str, Any]:
        """Get a specific option contract."""
        url = f"{self._trading_url()}/v2/options/contracts/{symbol_or_id}"
        data = self._request("GET", url)
        return self._format_option_contract(data)

    def create_option_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        time_in_force: str,
        qty: int,
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
        client_order_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create an option order."""
        url = f"{self._trading_url()}/v2/orders"

        order_data = {
            "symbol": symbol.upper(),
            "side": side.lower(),
            "type": order_type.lower(),
            "time_in_force": time_in_force.lower(),
            "qty": str(qty),
        }

        if limit_price is not None:
            order_data["limit_price"] = str(limit_price)
        if stop_price is not None:
            order_data["stop_price"] = str(stop_price)
        if client_order_id:
            order_data["client_order_id"] = client_order_id

        data = self._request("POST", url, json_data=order_data)
        return self._format_order(data)

    def exercise_option(self, symbol_or_id: str) -> Dict[str, Any]:
        """Exercise an option position."""
        url = f"{self._trading_url()}/v2/positions/{symbol_or_id}/exercise"
        data = self._request("POST", url)
        return data if data else {"status": "exercised"}

    def get_option_latest_quote(self, symbol: str, feed: str = "indicative") -> Dict[str, Any]:
        """Get latest option quote."""
        url = f"{self._data_url()}/v1beta1/options/quotes/latest"
        params = {"symbols": symbol.upper(), "feed": feed}
        data = self._request("GET", url, params=params)
        quote = data.get("quotes", {}).get(symbol.upper(), {})

        return {
            "symbol": symbol.upper(),
            "bid_price": float(quote.get("bp", 0)),
            "bid_size": int(quote.get("bs", 0)),
            "ask_price": float(quote.get("ap", 0)),
            "ask_size": int(quote.get("as", 0)),
            "timestamp": quote.get("t"),
        }

    def get_option_snapshot(self, symbol: str, feed: str = "indicative") -> Dict[str, Any]:
        """Get option snapshot including greeks."""
        url = f"{self._data_url()}/v1beta1/options/snapshots/{symbol.upper()}"
        params = {"feed": feed}
        data = self._request("GET", url, params=params)
        snapshot = data.get("snapshot", {})

        result = {"symbol": symbol.upper()}

        if "latestQuote" in snapshot:
            q = snapshot["latestQuote"]
            result["latest_quote"] = {
                "bid_price": float(q.get("bp", 0)),
                "bid_size": int(q.get("bs", 0)),
                "ask_price": float(q.get("ap", 0)),
                "ask_size": int(q.get("as", 0)),
                "timestamp": q.get("t"),
            }

        if "latestTrade" in snapshot:
            t = snapshot["latestTrade"]
            result["latest_trade"] = {
                "price": float(t.get("p", 0)),
                "size": int(t.get("s", 0)),
                "timestamp": t.get("t"),
            }

        if "greeks" in snapshot:
            g = snapshot["greeks"]
            result["greeks"] = {
                "delta": float(g.get("delta", 0)),
                "gamma": float(g.get("gamma", 0)),
                "theta": float(g.get("theta", 0)),
                "vega": float(g.get("vega", 0)),
                "rho": float(g.get("rho", 0)),
            }

        if "impliedVolatility" in snapshot:
            result["implied_volatility"] = float(snapshot["impliedVolatility"])

        return result

    def _format_option_contract(self, data: Dict) -> Dict[str, Any]:
        """Format option contract."""
        return {
            "id": data.get("id"),
            "symbol": data.get("symbol"),
            "name": data.get("name"),
            "status": data.get("status"),
            "tradable": data.get("tradable", False),
            "expiration_date": data.get("expiration_date"),
            "strike_price": float(data.get("strike_price", 0)),
            "type": data.get("type"),
            "underlying_symbol": data.get("underlying_symbol"),
            "underlying_asset_id": data.get("underlying_asset_id"),
            "size": data.get("size"),
            "open_interest": data.get("open_interest"),
            "open_interest_date": data.get("open_interest_date"),
            "close_price": data.get("close_price"),
            "close_price_date": data.get("close_price_date"),
        }

    # -------------------------------------------------------------------------
    # Asset Methods
    # -------------------------------------------------------------------------

    def list_assets(
        self,
        status: Optional[str] = None,
        asset_class: Optional[str] = None,
        exchange: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List tradable assets."""
        url = f"{self._trading_url()}/v2/assets"
        params = {}
        if status:
            params["status"] = status
        if asset_class:
            params["asset_class"] = asset_class
        if exchange:
            params["exchange"] = exchange

        data = self._request("GET", url, params=params if params else None)
        return [self._format_asset(asset) for asset in data]

    def get_asset(self, symbol: str) -> Dict[str, Any]:
        """Get asset details."""
        url = f"{self._trading_url()}/v2/assets/{symbol.upper()}"
        data = self._request("GET", url)
        return self._format_asset(data)

    def _format_asset(self, data: Dict) -> Dict[str, Any]:
        """Format asset response."""
        return {
            "id": data.get("id"),
            "class": data.get("class"),
            "exchange": data.get("exchange"),
            "symbol": data.get("symbol"),
            "name": data.get("name"),
            "status": data.get("status"),
            "tradable": data.get("tradable", False),
            "marginable": data.get("marginable", False),
            "shortable": data.get("shortable", False),
            "fractionable": data.get("fractionable", False),
            "easy_to_borrow": data.get("easy_to_borrow", False),
            "maintenance_margin_requirement": data.get("maintenance_margin_requirement"),
        }

    # -------------------------------------------------------------------------
    # Market Info Methods
    # -------------------------------------------------------------------------

    def get_clock(self) -> Dict[str, Any]:
        """Get market clock."""
        url = f"{self._trading_url()}/v2/clock"
        data = self._request("GET", url)

        return {
            "timestamp": data.get("timestamp"),
            "is_open": data.get("is_open", False),
            "next_open": data.get("next_open"),
            "next_close": data.get("next_close"),
        }

    def get_calendar(
        self,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get market calendar."""
        url = f"{self._trading_url()}/v2/calendar"
        params = {}
        if start:
            params["start"] = start
        if end:
            params["end"] = end

        data = self._request("GET", url, params=params if params else None)

        return [
            {
                "date": day.get("date"),
                "open": day.get("open"),
                "close": day.get("close"),
                "session_open": day.get("session_open"),
                "session_close": day.get("session_close"),
            }
            for day in data
        ]

    # -------------------------------------------------------------------------
    # Corporate Actions Methods
    # -------------------------------------------------------------------------

    def get_corporate_actions(
        self,
        symbols: Optional[List[str]] = None,
        types: Optional[List[str]] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """Get corporate actions (dividends, splits, spinoffs, mergers)."""
        url = f"{self._data_url()}/v1beta1/corporate-actions"
        params = {"limit": limit}

        if symbols:
            params["symbols"] = ",".join(s.upper() for s in symbols)
        if types:
            params["types"] = ",".join(types)
        if start:
            params["start"] = start
        if end:
            params["end"] = end

        data = self._request("GET", url, params=params)

        return {
            "corporate_actions": data.get("corporate_actions", {}),
            "next_page_token": data.get("next_page_token"),
        }
