"""MCP tool definitions for Alpha Vantage operations."""

import json
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


def register_tools(mcp):
    """Register all Alpha Vantage MCP tools."""

    @mcp.tool()
    def get_quote(symbol: str) -> Dict[str, str]:
        """Get current price and volume for a stock symbol.

        Args:
            symbol: Stock ticker symbol (e.g., AAPL, MSFT, IBM)

        Returns:
            Current quote data including price, open, high, low, volume,
            change, and change percent.
        """
        try:
            client = mcp.client
            result = client.get_quote(symbol)

            return {
                "success": "true",
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error getting quote for {symbol}: {e}")
            return {
                "success": "false",
                "error": str(e),
            }

    @mcp.tool()
    def get_history(symbol: str, days: int = 30) -> Dict[str, str]:
        """Get historical daily OHLCV data for a stock.

        Args:
            symbol: Stock ticker symbol (e.g., AAPL, MSFT, IBM)
            days: Number of days of history (max 100 for compact output)

        Returns:
            Array of daily price data with date, open, high, low, close, volume.
        """
        try:
            client = mcp.client
            # Use compact (100 days max) or full based on request
            outputsize = "full" if days > 100 else "compact"
            result = client.get_daily(symbol, outputsize=outputsize)

            # Limit to requested number of days
            result = result[:days]

            return {
                "success": "true",
                "count": str(len(result)),
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error getting history for {symbol}: {e}")
            return {
                "success": "false",
                "error": str(e),
            }

    @mcp.tool()
    def get_intraday(
        symbol: str,
        interval: str = "5min",
        limit: int = 100,
        extended_hours: bool = True,
    ) -> Dict[str, str]:
        """Get intraday OHLCV data for a stock.

        Args:
            symbol: Stock ticker symbol (e.g., AAPL, MSFT, IBM)
            interval: Time interval - "1min", "5min", "15min", "30min", "60min"
            limit: Number of data points to return (max 100 for compact)
            extended_hours: Include extended hours trading data

        Returns:
            Array of intraday price data with timestamp, open, high, low, close, volume.
        """
        try:
            client = mcp.client
            outputsize = "full" if limit > 100 else "compact"
            result = client.get_intraday(
                symbol,
                interval=interval,
                outputsize=outputsize,
                extended_hours=extended_hours,
            )

            result = result[:limit]

            return {
                "success": "true",
                "count": str(len(result)),
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error getting intraday for {symbol}: {e}")
            return {
                "success": "false",
                "error": str(e),
            }

    @mcp.tool()
    def get_weekly(symbol: str, weeks: int = 52, adjusted: bool = False) -> Dict[str, str]:
        """Get weekly OHLCV data for a stock.

        Args:
            symbol: Stock ticker symbol (e.g., AAPL, MSFT, IBM)
            weeks: Number of weeks of history to return
            adjusted: Use split/dividend adjusted values

        Returns:
            Array of weekly price data with date, open, high, low, close, volume.
        """
        try:
            client = mcp.client
            result = client.get_weekly(symbol, adjusted=adjusted)

            result = result[:weeks]

            return {
                "success": "true",
                "count": str(len(result)),
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error getting weekly for {symbol}: {e}")
            return {
                "success": "false",
                "error": str(e),
            }

    @mcp.tool()
    def get_monthly(symbol: str, months: int = 60, adjusted: bool = False) -> Dict[str, str]:
        """Get monthly OHLCV data for a stock.

        Args:
            symbol: Stock ticker symbol (e.g., AAPL, MSFT, IBM)
            months: Number of months of history to return
            adjusted: Use split/dividend adjusted values

        Returns:
            Array of monthly price data with date, open, high, low, close, volume.
        """
        try:
            client = mcp.client
            result = client.get_monthly(symbol, adjusted=adjusted)

            result = result[:months]

            return {
                "success": "true",
                "count": str(len(result)),
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error getting monthly for {symbol}: {e}")
            return {
                "success": "false",
                "error": str(e),
            }

    @mcp.tool()
    def get_technicals(
        symbol: str,
        indicators: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """Get technical indicators for a stock.

        Args:
            symbol: Stock ticker symbol (e.g., AAPL, MSFT, IBM)
            indicators: List of indicators to fetch. Options:
                - rsi: Relative Strength Index (14-period)
                - macd: Moving Average Convergence/Divergence
                - sma20, sma50, sma200: Simple Moving Averages
                - ema20, ema50, ema200: Exponential Moving Averages
                - bbands: Bollinger Bands
                - atr: Average True Range
                - stoch: Stochastic Oscillator
                - adx: Average Directional Index
                - obv: On Balance Volume
                Defaults to ["rsi", "macd", "sma20"]

        Returns:
            Technical indicator values. Note: Each indicator requires a separate API call.
        """
        if indicators is None:
            indicators = ["rsi", "macd", "sma20"]

        try:
            client = mcp.client
            result = {}
            errors = []

            for indicator in indicators:
                try:
                    indicator_lower = indicator.lower()

                    if indicator_lower == "rsi":
                        rsi_data = client.get_rsi(symbol)
                        if rsi_data:
                            latest_date = max(rsi_data.keys())
                            result["rsi"] = {
                                "value": rsi_data[latest_date],
                                "date": latest_date,
                            }

                    elif indicator_lower == "macd":
                        macd_data = client.get_macd(symbol)
                        if macd_data:
                            latest_date = max(macd_data.keys())
                            result["macd"] = {
                                "value": macd_data[latest_date]["macd"],
                                "signal": macd_data[latest_date]["signal"],
                                "histogram": macd_data[latest_date]["histogram"],
                                "date": latest_date,
                            }

                    elif indicator_lower == "sma20":
                        sma_data = client.get_sma(symbol, 20)
                        if sma_data:
                            latest_date = max(sma_data.keys())
                            result["sma20"] = {"value": sma_data[latest_date], "date": latest_date}

                    elif indicator_lower == "sma50":
                        sma_data = client.get_sma(symbol, 50)
                        if sma_data:
                            latest_date = max(sma_data.keys())
                            result["sma50"] = {"value": sma_data[latest_date], "date": latest_date}

                    elif indicator_lower == "sma200":
                        sma_data = client.get_sma(symbol, 200)
                        if sma_data:
                            latest_date = max(sma_data.keys())
                            result["sma200"] = {"value": sma_data[latest_date], "date": latest_date}

                    elif indicator_lower == "ema20":
                        ema_data = client.get_ema(symbol, 20)
                        if ema_data:
                            latest_date = max(ema_data.keys())
                            result["ema20"] = {"value": ema_data[latest_date], "date": latest_date}

                    elif indicator_lower == "ema50":
                        ema_data = client.get_ema(symbol, 50)
                        if ema_data:
                            latest_date = max(ema_data.keys())
                            result["ema50"] = {"value": ema_data[latest_date], "date": latest_date}

                    elif indicator_lower == "ema200":
                        ema_data = client.get_ema(symbol, 200)
                        if ema_data:
                            latest_date = max(ema_data.keys())
                            result["ema200"] = {"value": ema_data[latest_date], "date": latest_date}

                    elif indicator_lower == "bbands":
                        bbands_data = client.get_bbands(symbol)
                        if bbands_data:
                            latest_date = max(bbands_data.keys())
                            result["bbands"] = {
                                "upper": bbands_data[latest_date]["upper"],
                                "middle": bbands_data[latest_date]["middle"],
                                "lower": bbands_data[latest_date]["lower"],
                                "date": latest_date,
                            }

                    elif indicator_lower == "atr":
                        atr_data = client.get_atr(symbol)
                        if atr_data:
                            latest_date = max(atr_data.keys())
                            result["atr"] = {"value": atr_data[latest_date], "date": latest_date}

                    elif indicator_lower == "stoch":
                        stoch_data = client.get_stoch(symbol)
                        if stoch_data:
                            latest_date = max(stoch_data.keys())
                            result["stoch"] = {
                                "slowk": stoch_data[latest_date]["slowk"],
                                "slowd": stoch_data[latest_date]["slowd"],
                                "date": latest_date,
                            }

                    elif indicator_lower == "adx":
                        adx_data = client.get_adx(symbol)
                        if adx_data:
                            latest_date = max(adx_data.keys())
                            result["adx"] = {"value": adx_data[latest_date], "date": latest_date}

                    elif indicator_lower == "obv":
                        obv_data = client.get_obv(symbol)
                        if obv_data:
                            latest_date = max(obv_data.keys())
                            result["obv"] = {"value": obv_data[latest_date], "date": latest_date}

                    else:
                        errors.append(f"Unknown indicator: {indicator}")

                except Exception as e:
                    errors.append(f"{indicator}: {str(e)}")

            response = {
                "success": "true",
                "symbol": symbol.upper(),
                "data": json.dumps(result, indent=2),
            }

            if errors:
                response["warnings"] = json.dumps(errors)

            return response

        except Exception as e:
            logger.error(f"Error getting technicals for {symbol}: {e}")
            return {
                "success": "false",
                "error": str(e),
            }

    @mcp.tool()
    def get_news(symbol: str, limit: int = 5) -> Dict[str, str]:
        """Get recent news and sentiment for a stock.

        Args:
            symbol: Stock ticker symbol (e.g., AAPL, MSFT, IBM)
            limit: Maximum number of articles to return (default 5)

        Returns:
            Array of news articles with title, summary, url, published time,
            sentiment score, and sentiment label.
        """
        try:
            client = mcp.client
            result = client.get_news(symbol, limit=limit)

            return {
                "success": "true",
                "count": str(len(result)),
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error getting news for {symbol}: {e}")
            return {
                "success": "false",
                "error": str(e),
            }

    @mcp.tool()
    def get_fundamentals(symbol: str) -> Dict[str, str]:
        """Get company fundamentals (P/E ratio, market cap, EPS, etc.).

        Args:
            symbol: Stock ticker symbol (e.g., AAPL, MSFT, IBM)

        Returns:
            Company fundamental data including market cap, P/E ratio, EPS,
            dividend yield, 52-week high/low, moving averages, and more.
        """
        try:
            client = mcp.client
            result = client.get_overview(symbol)

            return {
                "success": "true",
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error getting fundamentals for {symbol}: {e}")
            return {
                "success": "false",
                "error": str(e),
            }

    @mcp.tool()
    def get_batch_quotes(symbols: List[str]) -> Dict[str, str]:
        """Get quotes for multiple stock symbols.

        Args:
            symbols: List of stock ticker symbols (e.g., ["AAPL", "MSFT", "GOOGL"])

        Returns:
            Array of quote objects for each symbol.
            Note: Each symbol requires a separate API call.
        """
        try:
            client = mcp.client
            results = []
            errors = []

            for symbol in symbols:
                try:
                    quote = client.get_quote(symbol)
                    results.append(quote)
                except Exception as e:
                    errors.append({
                        "symbol": symbol.upper(),
                        "error": str(e),
                    })

            response = {
                "success": "true",
                "count": str(len(results)),
                "data": json.dumps(results, indent=2),
            }

            if errors:
                response["errors"] = json.dumps(errors)

            return response

        except Exception as e:
            logger.error(f"Error getting batch quotes: {e}")
            return {
                "success": "false",
                "error": str(e),
            }

    @mcp.tool()
    def search_symbols(keywords: str) -> Dict[str, str]:
        """Search for stock symbols by keyword.

        Args:
            keywords: Search keywords (company name, partial symbol, etc.)

        Returns:
            Array of matching symbols with name, type, region, and match score.
        """
        try:
            client = mcp.client
            result = client.search_symbols(keywords)

            return {
                "success": "true",
                "count": str(len(result)),
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error searching symbols for '{keywords}': {e}")
            return {
                "success": "false",
                "error": str(e),
            }

    @mcp.tool()
    def get_market_status() -> Dict[str, str]:
        """Get global market status (open/closed for major exchanges worldwide).

        Returns:
            Array of market status objects for major exchanges including
            region, exchange names, current status, and trading hours.
        """
        try:
            client = mcp.client
            result = client.get_market_status()

            return {
                "success": "true",
                "count": str(len(result)),
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error getting market status: {e}")
            return {
                "success": "false",
                "error": str(e),
            }

    @mcp.tool()
    def get_income_statement(symbol: str, period: str = "annual") -> Dict[str, str]:
        """Get income statement data for a company.

        Args:
            symbol: Stock ticker symbol (e.g., AAPL, MSFT, IBM)
            period: "annual" or "quarterly"

        Returns:
            Income statement data including revenue, gross profit, operating income,
            net income, and other financial metrics.
        """
        try:
            client = mcp.client
            result = client.get_income_statement(symbol)

            # Select the requested period
            data = result.get("annual" if period == "annual" else "quarterly", [])

            return {
                "success": "true",
                "symbol": symbol.upper(),
                "period": period,
                "count": str(len(data)),
                "data": json.dumps(data[:5], indent=2),  # Limit to last 5 periods
            }
        except Exception as e:
            logger.error(f"Error getting income statement for {symbol}: {e}")
            return {
                "success": "false",
                "error": str(e),
            }

    @mcp.tool()
    def get_balance_sheet(symbol: str, period: str = "annual") -> Dict[str, str]:
        """Get balance sheet data for a company.

        Args:
            symbol: Stock ticker symbol (e.g., AAPL, MSFT, IBM)
            period: "annual" or "quarterly"

        Returns:
            Balance sheet data including total assets, total liabilities,
            shareholders equity, cash, debt, and other financial metrics.
        """
        try:
            client = mcp.client
            result = client.get_balance_sheet(symbol)

            # Select the requested period
            data = result.get("annual" if period == "annual" else "quarterly", [])

            return {
                "success": "true",
                "symbol": symbol.upper(),
                "period": period,
                "count": str(len(data)),
                "data": json.dumps(data[:5], indent=2),  # Limit to last 5 periods
            }
        except Exception as e:
            logger.error(f"Error getting balance sheet for {symbol}: {e}")
            return {
                "success": "false",
                "error": str(e),
            }

    @mcp.tool()
    def get_cash_flow(symbol: str, period: str = "annual") -> Dict[str, str]:
        """Get cash flow statement data for a company.

        Args:
            symbol: Stock ticker symbol (e.g., AAPL, MSFT, IBM)
            period: "annual" or "quarterly"

        Returns:
            Cash flow data including operating cash flow, capital expenditures,
            free cash flow, and other financial metrics.
        """
        try:
            client = mcp.client
            result = client.get_cash_flow(symbol)

            # Select the requested period
            data = result.get("annual" if period == "annual" else "quarterly", [])

            return {
                "success": "true",
                "symbol": symbol.upper(),
                "period": period,
                "count": str(len(data)),
                "data": json.dumps(data[:5], indent=2),  # Limit to last 5 periods
            }
        except Exception as e:
            logger.error(f"Error getting cash flow for {symbol}: {e}")
            return {
                "success": "false",
                "error": str(e),
            }

    logger.info("Registered Alpha Vantage MCP tools: get_quote, get_history, get_intraday, "
                "get_weekly, get_monthly, get_technicals, get_news, get_fundamentals, "
                "get_batch_quotes, search_symbols, get_market_status, get_income_statement, "
                "get_balance_sheet, get_cash_flow")
