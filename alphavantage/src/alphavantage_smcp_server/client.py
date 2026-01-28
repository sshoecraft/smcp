"""Alpha Vantage API client wrapper."""

import logging
from dataclasses import dataclass
from typing import Dict, List, Any, Optional

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://www.alphavantage.co/query"


@dataclass
class AlphaVantageConfig:
    """Configuration for Alpha Vantage API."""

    api_key: str

    @classmethod
    def from_smcp_creds(cls, creds: Dict[str, str]) -> "AlphaVantageConfig":
        """Create config from SMCP credentials."""
        api_key = creds.get("ALPHAVANTAGE_API_KEY", "")
        if not api_key:
            raise ValueError("ALPHAVANTAGE_API_KEY is required")

        return cls(api_key=api_key)


class AlphaVantageClient:
    """Client for Alpha Vantage API."""

    def __init__(self, config: AlphaVantageConfig):
        self.config = config
        self.session = requests.Session()
        logger.info("Alpha Vantage client initialized")

    def _request(self, params: Dict[str, str]) -> Dict[str, Any]:
        """Make a request to the Alpha Vantage API."""
        params["apikey"] = self.config.api_key

        logger.debug(f"API request: function={params.get('function')}")

        response = self.session.get(BASE_URL, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()

        # Check for API errors
        if "Error Message" in data:
            raise ValueError(data["Error Message"])
        if "Note" in data:
            raise ValueError(f"Rate limit: {data['Note']}")
        if "Information" in data:
            raise ValueError(data["Information"])

        return data

    @staticmethod
    def _clean_key(key: str) -> str:
        """Clean API response keys by removing numbered prefixes.

        Alpha Vantage returns keys like "01. symbol", "02. open".
        This strips the prefix to get just "symbol", "open".
        """
        if ". " in key:
            return key.split(". ", 1)[1]
        return key

    @staticmethod
    def _clean_dict(data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean all keys in a dictionary."""
        return {AlphaVantageClient._clean_key(k): v for k, v in data.items()}

    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get current quote for a symbol.

        Returns: {symbol, price, open, high, low, volume, latest_trading_day,
                  previous_close, change, change_percent}
        """
        data = self._request({
            "function": "GLOBAL_QUOTE",
            "symbol": symbol.upper(),
        })

        quote = data.get("Global Quote", {})
        if not quote:
            raise ValueError(f"No quote data for {symbol}")

        cleaned = self._clean_dict(quote)

        # Convert numeric strings to floats
        result = {
            "symbol": cleaned.get("symbol", symbol.upper()),
            "price": float(cleaned.get("price", 0)),
            "open": float(cleaned.get("open", 0)),
            "high": float(cleaned.get("high", 0)),
            "low": float(cleaned.get("low", 0)),
            "volume": int(cleaned.get("volume", 0)),
            "latest_trading_day": cleaned.get("latest trading day", ""),
            "previous_close": float(cleaned.get("previous close", 0)),
            "change": float(cleaned.get("change", 0)),
            "change_percent": cleaned.get("change percent", "0%").rstrip("%"),
        }

        return result

    def get_intraday(
        self,
        symbol: str,
        interval: str = "5min",
        outputsize: str = "compact",
        extended_hours: bool = True,
    ) -> List[Dict[str, Any]]:
        """Get intraday OHLCV data.

        Args:
            symbol: Stock ticker symbol
            interval: Time interval - "1min", "5min", "15min", "30min", "60min"
            outputsize: "compact" (100 data points) or "full" (full intraday data)
            extended_hours: Include extended hours data

        Returns: List of {timestamp, open, high, low, close, volume}
        """
        data = self._request({
            "function": "TIME_SERIES_INTRADAY",
            "symbol": symbol.upper(),
            "interval": interval,
            "outputsize": outputsize,
            "extended_hours": "true" if extended_hours else "false",
        })

        # The key varies by interval
        key = f"Time Series ({interval})"
        time_series = data.get(key, {})
        if not time_series:
            raise ValueError(f"No intraday data for {symbol}")

        result = []
        for timestamp, values in sorted(time_series.items(), reverse=True):
            cleaned = self._clean_dict(values)
            result.append({
                "timestamp": timestamp,
                "open": float(cleaned.get("open", 0)),
                "high": float(cleaned.get("high", 0)),
                "low": float(cleaned.get("low", 0)),
                "close": float(cleaned.get("close", 0)),
                "volume": int(cleaned.get("volume", 0)),
            })

        return result

    def get_daily(self, symbol: str, outputsize: str = "compact") -> List[Dict[str, Any]]:
        """Get historical daily OHLCV data.

        Args:
            symbol: Stock ticker symbol
            outputsize: "compact" (100 days) or "full" (20+ years)

        Returns: List of {date, open, high, low, close, volume}
        """
        data = self._request({
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol.upper(),
            "outputsize": outputsize,
        })

        time_series = data.get("Time Series (Daily)", {})
        if not time_series:
            raise ValueError(f"No daily data for {symbol}")

        result = []
        for date, values in sorted(time_series.items(), reverse=True):
            cleaned = self._clean_dict(values)
            result.append({
                "date": date,
                "open": float(cleaned.get("open", 0)),
                "high": float(cleaned.get("high", 0)),
                "low": float(cleaned.get("low", 0)),
                "close": float(cleaned.get("close", 0)),
                "volume": int(cleaned.get("volume", 0)),
            })

        return result

    def get_weekly(self, symbol: str, adjusted: bool = False) -> List[Dict[str, Any]]:
        """Get weekly OHLCV data.

        Args:
            symbol: Stock ticker symbol
            adjusted: Use adjusted values (splits/dividends)

        Returns: List of {date, open, high, low, close, volume}
        """
        function = "TIME_SERIES_WEEKLY_ADJUSTED" if adjusted else "TIME_SERIES_WEEKLY"
        data = self._request({
            "function": function,
            "symbol": symbol.upper(),
        })

        key = "Weekly Adjusted Time Series" if adjusted else "Weekly Time Series"
        time_series = data.get(key, {})
        if not time_series:
            raise ValueError(f"No weekly data for {symbol}")

        result = []
        for date, values in sorted(time_series.items(), reverse=True):
            cleaned = self._clean_dict(values)
            entry = {
                "date": date,
                "open": float(cleaned.get("open", 0)),
                "high": float(cleaned.get("high", 0)),
                "low": float(cleaned.get("low", 0)),
                "close": float(cleaned.get("close", 0)),
                "volume": int(cleaned.get("volume", 0)),
            }
            if adjusted:
                entry["adjusted_close"] = float(cleaned.get("adjusted close", 0))
                entry["dividend"] = float(cleaned.get("dividend amount", 0))
            result.append(entry)

        return result

    def get_monthly(self, symbol: str, adjusted: bool = False) -> List[Dict[str, Any]]:
        """Get monthly OHLCV data.

        Args:
            symbol: Stock ticker symbol
            adjusted: Use adjusted values (splits/dividends)

        Returns: List of {date, open, high, low, close, volume}
        """
        function = "TIME_SERIES_MONTHLY_ADJUSTED" if adjusted else "TIME_SERIES_MONTHLY"
        data = self._request({
            "function": function,
            "symbol": symbol.upper(),
        })

        key = "Monthly Adjusted Time Series" if adjusted else "Monthly Time Series"
        time_series = data.get(key, {})
        if not time_series:
            raise ValueError(f"No monthly data for {symbol}")

        result = []
        for date, values in sorted(time_series.items(), reverse=True):
            cleaned = self._clean_dict(values)
            entry = {
                "date": date,
                "open": float(cleaned.get("open", 0)),
                "high": float(cleaned.get("high", 0)),
                "low": float(cleaned.get("low", 0)),
                "close": float(cleaned.get("close", 0)),
                "volume": int(cleaned.get("volume", 0)),
            }
            if adjusted:
                entry["adjusted_close"] = float(cleaned.get("adjusted close", 0))
                entry["dividend"] = float(cleaned.get("dividend amount", 0))
            result.append(entry)

        return result

    def get_rsi(self, symbol: str, time_period: int = 14, interval: str = "daily") -> Dict[str, float]:
        """Get RSI (Relative Strength Index) values.

        Returns: Dict mapping date -> RSI value
        """
        data = self._request({
            "function": "RSI",
            "symbol": symbol.upper(),
            "interval": interval,
            "time_period": str(time_period),
            "series_type": "close",
        })

        rsi_data = data.get("Technical Analysis: RSI", {})
        if not rsi_data:
            raise ValueError(f"No RSI data for {symbol}")

        # Return most recent RSI value and historical
        result = {}
        for date, values in rsi_data.items():
            result[date] = float(values.get("RSI", 0))

        return result

    def get_macd(self, symbol: str, interval: str = "daily") -> Dict[str, Dict[str, float]]:
        """Get MACD (Moving Average Convergence/Divergence) values.

        Returns: Dict mapping date -> {macd, signal, histogram}
        """
        data = self._request({
            "function": "MACD",
            "symbol": symbol.upper(),
            "interval": interval,
            "series_type": "close",
        })

        macd_data = data.get("Technical Analysis: MACD", {})
        if not macd_data:
            raise ValueError(f"No MACD data for {symbol}")

        result = {}
        for date, values in macd_data.items():
            result[date] = {
                "macd": float(values.get("MACD", 0)),
                "signal": float(values.get("MACD_Signal", 0)),
                "histogram": float(values.get("MACD_Hist", 0)),
            }

        return result

    def get_sma(self, symbol: str, time_period: int, interval: str = "daily") -> Dict[str, float]:
        """Get SMA (Simple Moving Average) values.

        Returns: Dict mapping date -> SMA value
        """
        data = self._request({
            "function": "SMA",
            "symbol": symbol.upper(),
            "interval": interval,
            "time_period": str(time_period),
            "series_type": "close",
        })

        sma_data = data.get("Technical Analysis: SMA", {})
        if not sma_data:
            raise ValueError(f"No SMA data for {symbol}")

        result = {}
        for date, values in sma_data.items():
            result[date] = float(values.get("SMA", 0))

        return result

    def get_ema(self, symbol: str, time_period: int, interval: str = "daily") -> Dict[str, float]:
        """Get EMA (Exponential Moving Average) values.

        Returns: Dict mapping date -> EMA value
        """
        data = self._request({
            "function": "EMA",
            "symbol": symbol.upper(),
            "interval": interval,
            "time_period": str(time_period),
            "series_type": "close",
        })

        ema_data = data.get("Technical Analysis: EMA", {})
        if not ema_data:
            raise ValueError(f"No EMA data for {symbol}")

        result = {}
        for date, values in ema_data.items():
            result[date] = float(values.get("EMA", 0))

        return result

    def get_bbands(
        self,
        symbol: str,
        time_period: int = 20,
        interval: str = "daily",
        nbdevup: int = 2,
        nbdevdn: int = 2,
    ) -> Dict[str, Dict[str, float]]:
        """Get Bollinger Bands values.

        Returns: Dict mapping date -> {upper, middle, lower}
        """
        data = self._request({
            "function": "BBANDS",
            "symbol": symbol.upper(),
            "interval": interval,
            "time_period": str(time_period),
            "series_type": "close",
            "nbdevup": str(nbdevup),
            "nbdevdn": str(nbdevdn),
        })

        bbands_data = data.get("Technical Analysis: BBANDS", {})
        if not bbands_data:
            raise ValueError(f"No BBANDS data for {symbol}")

        result = {}
        for date, values in bbands_data.items():
            result[date] = {
                "upper": float(values.get("Real Upper Band", 0)),
                "middle": float(values.get("Real Middle Band", 0)),
                "lower": float(values.get("Real Lower Band", 0)),
            }

        return result

    def get_atr(self, symbol: str, time_period: int = 14, interval: str = "daily") -> Dict[str, float]:
        """Get ATR (Average True Range) values.

        Returns: Dict mapping date -> ATR value
        """
        data = self._request({
            "function": "ATR",
            "symbol": symbol.upper(),
            "interval": interval,
            "time_period": str(time_period),
        })

        atr_data = data.get("Technical Analysis: ATR", {})
        if not atr_data:
            raise ValueError(f"No ATR data for {symbol}")

        result = {}
        for date, values in atr_data.items():
            result[date] = float(values.get("ATR", 0))

        return result

    def get_vwap(self, symbol: str, interval: str = "15min") -> Dict[str, float]:
        """Get VWAP (Volume Weighted Average Price) values.

        Note: VWAP is only available for intraday intervals.

        Returns: Dict mapping timestamp -> VWAP value
        """
        data = self._request({
            "function": "VWAP",
            "symbol": symbol.upper(),
            "interval": interval,
        })

        vwap_data = data.get("Technical Analysis: VWAP", {})
        if not vwap_data:
            raise ValueError(f"No VWAP data for {symbol}")

        result = {}
        for timestamp, values in vwap_data.items():
            result[timestamp] = float(values.get("VWAP", 0))

        return result

    def get_stoch(
        self,
        symbol: str,
        interval: str = "daily",
        fastkperiod: int = 5,
        slowkperiod: int = 3,
        slowdperiod: int = 3,
    ) -> Dict[str, Dict[str, float]]:
        """Get Stochastic Oscillator values.

        Returns: Dict mapping date -> {slowk, slowd}
        """
        data = self._request({
            "function": "STOCH",
            "symbol": symbol.upper(),
            "interval": interval,
            "fastkperiod": str(fastkperiod),
            "slowkperiod": str(slowkperiod),
            "slowdperiod": str(slowdperiod),
        })

        stoch_data = data.get("Technical Analysis: STOCH", {})
        if not stoch_data:
            raise ValueError(f"No STOCH data for {symbol}")

        result = {}
        for date, values in stoch_data.items():
            result[date] = {
                "slowk": float(values.get("SlowK", 0)),
                "slowd": float(values.get("SlowD", 0)),
            }

        return result

    def get_adx(self, symbol: str, time_period: int = 14, interval: str = "daily") -> Dict[str, float]:
        """Get ADX (Average Directional Index) values.

        Returns: Dict mapping date -> ADX value
        """
        data = self._request({
            "function": "ADX",
            "symbol": symbol.upper(),
            "interval": interval,
            "time_period": str(time_period),
        })

        adx_data = data.get("Technical Analysis: ADX", {})
        if not adx_data:
            raise ValueError(f"No ADX data for {symbol}")

        result = {}
        for date, values in adx_data.items():
            result[date] = float(values.get("ADX", 0))

        return result

    def get_obv(self, symbol: str, interval: str = "daily") -> Dict[str, float]:
        """Get OBV (On Balance Volume) values.

        Returns: Dict mapping date -> OBV value
        """
        data = self._request({
            "function": "OBV",
            "symbol": symbol.upper(),
            "interval": interval,
        })

        obv_data = data.get("Technical Analysis: OBV", {})
        if not obv_data:
            raise ValueError(f"No OBV data for {symbol}")

        result = {}
        for date, values in obv_data.items():
            result[date] = float(values.get("OBV", 0))

        return result

    def get_news(self, symbol: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get news and sentiment for a symbol.

        Returns: List of {title, summary, url, published, sentiment_score, sentiment_label}
        """
        data = self._request({
            "function": "NEWS_SENTIMENT",
            "tickers": symbol.upper(),
        })

        feed = data.get("feed", [])
        if not feed:
            return []

        result = []
        for article in feed[:limit]:
            # Find sentiment for this specific ticker
            ticker_sentiment = None
            for ts in article.get("ticker_sentiment", []):
                if ts.get("ticker", "").upper() == symbol.upper():
                    ticker_sentiment = ts
                    break

            result.append({
                "title": article.get("title", ""),
                "summary": article.get("summary", ""),
                "url": article.get("url", ""),
                "published": article.get("time_published", ""),
                "sentiment_score": float(ticker_sentiment.get("ticker_sentiment_score", 0)) if ticker_sentiment else float(article.get("overall_sentiment_score", 0)),
                "sentiment_label": ticker_sentiment.get("ticker_sentiment_label", "") if ticker_sentiment else article.get("overall_sentiment_label", ""),
            })

        return result

    def get_overview(self, symbol: str) -> Dict[str, Any]:
        """Get company fundamentals/overview.

        Returns: {name, sector, industry, market_cap, pe_ratio, eps, dividend_yield,
                  week_52_high, week_52_low, sma_50, sma_200, ...}
        """
        data = self._request({
            "function": "OVERVIEW",
            "symbol": symbol.upper(),
        })

        if not data or "Symbol" not in data:
            raise ValueError(f"No overview data for {symbol}")

        def safe_float(val: str, default: float = 0.0) -> float:
            if not val or val == "None" or val == "-":
                return default
            try:
                return float(val)
            except (ValueError, TypeError):
                return default

        result = {
            "symbol": data.get("Symbol", symbol.upper()),
            "name": data.get("Name", ""),
            "description": data.get("Description", ""),
            "sector": data.get("Sector", ""),
            "industry": data.get("Industry", ""),
            "market_cap": safe_float(data.get("MarketCapitalization")),
            "pe_ratio": safe_float(data.get("PERatio")),
            "peg_ratio": safe_float(data.get("PEGRatio")),
            "book_value": safe_float(data.get("BookValue")),
            "dividend_per_share": safe_float(data.get("DividendPerShare")),
            "dividend_yield": safe_float(data.get("DividendYield")),
            "eps": safe_float(data.get("EPS")),
            "revenue_per_share": safe_float(data.get("RevenuePerShareTTM")),
            "profit_margin": safe_float(data.get("ProfitMargin")),
            "week_52_high": safe_float(data.get("52WeekHigh")),
            "week_52_low": safe_float(data.get("52WeekLow")),
            "sma_50": safe_float(data.get("50DayMovingAverage")),
            "sma_200": safe_float(data.get("200DayMovingAverage")),
            "shares_outstanding": safe_float(data.get("SharesOutstanding")),
            "beta": safe_float(data.get("Beta")),
        }

        return result

    def get_income_statement(self, symbol: str) -> Dict[str, Any]:
        """Get income statement data (annual and quarterly).

        Returns: {annual: [...], quarterly: [...]}
        """
        data = self._request({
            "function": "INCOME_STATEMENT",
            "symbol": symbol.upper(),
        })

        if "annualReports" not in data and "quarterlyReports" not in data:
            raise ValueError(f"No income statement data for {symbol}")

        return {
            "symbol": symbol.upper(),
            "annual": data.get("annualReports", []),
            "quarterly": data.get("quarterlyReports", []),
        }

    def get_balance_sheet(self, symbol: str) -> Dict[str, Any]:
        """Get balance sheet data (annual and quarterly).

        Returns: {annual: [...], quarterly: [...]}
        """
        data = self._request({
            "function": "BALANCE_SHEET",
            "symbol": symbol.upper(),
        })

        if "annualReports" not in data and "quarterlyReports" not in data:
            raise ValueError(f"No balance sheet data for {symbol}")

        return {
            "symbol": symbol.upper(),
            "annual": data.get("annualReports", []),
            "quarterly": data.get("quarterlyReports", []),
        }

    def get_cash_flow(self, symbol: str) -> Dict[str, Any]:
        """Get cash flow statement data (annual and quarterly).

        Returns: {annual: [...], quarterly: [...]}
        """
        data = self._request({
            "function": "CASH_FLOW",
            "symbol": symbol.upper(),
        })

        if "annualReports" not in data and "quarterlyReports" not in data:
            raise ValueError(f"No cash flow data for {symbol}")

        return {
            "symbol": symbol.upper(),
            "annual": data.get("annualReports", []),
            "quarterly": data.get("quarterlyReports", []),
        }

    def search_symbols(self, keywords: str) -> List[Dict[str, Any]]:
        """Search for symbols by keyword.

        Returns: List of {symbol, name, type, region, currency, match_score}
        """
        data = self._request({
            "function": "SYMBOL_SEARCH",
            "keywords": keywords,
        })

        matches = data.get("bestMatches", [])

        result = []
        for match in matches:
            cleaned = self._clean_dict(match)
            result.append({
                "symbol": cleaned.get("symbol", ""),
                "name": cleaned.get("name", ""),
                "type": cleaned.get("type", ""),
                "region": cleaned.get("region", ""),
                "currency": cleaned.get("currency", ""),
                "match_score": float(cleaned.get("matchScore", 0)),
            })

        return result

    def get_market_status(self) -> List[Dict[str, Any]]:
        """Get global market status (open/closed for major exchanges).

        Returns: List of {market_type, region, exchange, current_status, local_open, local_close}
        """
        data = self._request({
            "function": "MARKET_STATUS",
        })

        markets = data.get("markets", [])

        result = []
        for market in markets:
            result.append({
                "market_type": market.get("market_type", ""),
                "region": market.get("region", ""),
                "primary_exchanges": market.get("primary_exchanges", ""),
                "current_status": market.get("current_status", ""),
                "local_open": market.get("local_open", ""),
                "local_close": market.get("local_close", ""),
                "notes": market.get("notes", ""),
            })

        return result
