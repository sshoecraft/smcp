"""eBay API client wrapper with OAuth2 authentication."""

import base64
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

import requests

logger = logging.getLogger(__name__)

# eBay API endpoints
TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
SEARCH_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"
ITEM_URL = "https://api.ebay.com/buy/browse/v1/item"
API_SCOPE = "https://api.ebay.com/oauth/api_scope"


@dataclass
class EbayConfig:
    """Configuration for eBay client."""
    client_id: str
    client_secret: str

    @classmethod
    def from_smcp_creds(cls, creds: Dict[str, str]) -> "EbayConfig":
        """Create config from SMCP credentials."""
        client_id = creds.get("EBAY_CLIENT_ID")
        if not client_id:
            raise ValueError("EBAY_CLIENT_ID credential is required")

        client_secret = creds.get("EBAY_CLIENT_SECRET")
        if not client_secret:
            raise ValueError("EBAY_CLIENT_SECRET credential is required")

        return cls(
            client_id=client_id,
            client_secret=client_secret,
        )


class EbayError(Exception):
    """eBay API error."""
    pass


class EbayClient:
    """eBay API client with OAuth2 authentication."""

    # Buying options mapping (including aliases)
    BUYING_OPTIONS = {
        "fixed_price": "FIXED_PRICE",
        "buy_it_now": "FIXED_PRICE",  # alias
        "auction": "AUCTION",
        "best_offer": "BEST_OFFER",
        "all": None,
    }

    # Condition mapping
    CONDITIONS = {
        "new": "NEW",
        "used": "USED",
        "any": None,
    }

    def __init__(self, config: EbayConfig):
        """Initialize the eBay client."""
        self.config = config
        self.client_id = config.client_id
        self.client_secret = config.client_secret
        self.access_token = None
        self.token_expires_at = None

    def _get_access_token(self) -> str:
        """Get a valid access token, refreshing if necessary."""
        # Check if we have a valid cached token (with 5 minute buffer)
        if self.access_token and self.token_expires_at:
            if datetime.now() < self.token_expires_at:
                return self.access_token

        # Generate new token
        logger.info("Requesting new eBay access token")
        auth = f"{self.client_id}:{self.client_secret}"
        encoded_auth = base64.b64encode(auth.encode()).decode()

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {encoded_auth}",
        }

        data = {
            "grant_type": "client_credentials",
            "scope": API_SCOPE,
        }

        response = requests.post(TOKEN_URL, headers=headers, data=data)

        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 7200)
            # Cache with 5 minute buffer
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)
            logger.info("Successfully obtained eBay access token")
            return self.access_token
        else:
            raise EbayError(f"Failed to get access token: {response.status_code} {response.text}")

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with valid access token."""
        token = self._get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    async def search(
        self,
        query: str,
        limit: int = 10,
        buying_options: str = "all",
        condition: str = "any",
    ) -> List[Dict[str, Any]]:
        """Search eBay listings.

        Args:
            query: Search query string
            limit: Maximum number of results (default: 10)
            buying_options: Filter type - all, fixed_price, buy_it_now, auction, best_offer
            condition: Filter condition - any, new, used

        Returns:
            List of item dictionaries
        """
        try:
            headers = self._get_headers()

            # Build params
            params = {
                "q": query,
                "limit": min(limit, 200),  # eBay max is 200
            }

            # Add buying options filter
            buying_opt = buying_options.lower()
            if buying_opt not in self.BUYING_OPTIONS:
                raise EbayError(f"Invalid buying_options: {buying_options}. Valid: {list(self.BUYING_OPTIONS.keys())}")

            ebay_buying_opt = self.BUYING_OPTIONS[buying_opt]
            if ebay_buying_opt:
                params["filter"] = f"buyingOptions:{{{ebay_buying_opt}}}"

            # Add condition filter
            cond = condition.lower()
            if cond not in self.CONDITIONS:
                raise EbayError(f"Invalid condition: {condition}. Valid: {list(self.CONDITIONS.keys())}")

            ebay_condition = self.CONDITIONS[cond]
            if ebay_condition:
                if "filter" in params:
                    params["filter"] += f",conditions:{{{ebay_condition}}}"
                else:
                    params["filter"] = f"conditions:{{{ebay_condition}}}"

            response = requests.get(SEARCH_URL, headers=headers, params=params)

            if response.status_code != 200:
                raise EbayError(f"Search failed: {response.status_code} {response.text}")

            data = response.json()
            items = data.get("itemSummaries", [])

            if not items:
                return []

            # Format results
            results = []
            for item in items:
                result = self._format_item_summary(item)
                results.append(result)

            return results

        except EbayError:
            raise
        except Exception as e:
            logger.error(f"Error searching eBay: {e}")
            raise EbayError(f"Search error: {e}")

    async def get_item(self, item_id: str) -> Dict[str, Any]:
        """Get detailed information for a specific item.

        Args:
            item_id: eBay item ID

        Returns:
            Item details dictionary
        """
        try:
            headers = self._get_headers()
            url = f"{ITEM_URL}/{item_id}"

            response = requests.get(url, headers=headers)

            if response.status_code != 200:
                raise EbayError(f"Get item failed: {response.status_code} {response.text}")

            item = response.json()
            return self._format_item_detail(item)

        except EbayError:
            raise
        except Exception as e:
            logger.error(f"Error getting item {item_id}: {e}")
            raise EbayError(f"Get item error: {e}")

    def _format_item_summary(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Format an item summary from search results."""
        # Price
        price_info = item.get("price", {})
        price = price_info.get("value", "N/A")
        currency = price_info.get("currency", "USD")

        # Shipping
        shipping_options = item.get("shippingOptions", [])
        if shipping_options:
            ship_cost = shipping_options[0].get("shippingCost", {})
            shipping_value = ship_cost.get("value", "0")
            if shipping_value in ("0", "0.00"):
                shipping = "FREE"
            else:
                shipping = f"{shipping_value} {ship_cost.get('currency', 'USD')}"
        else:
            shipping = "N/A"

        # Seller
        seller = item.get("seller", {})

        # End date
        end_date = item.get("itemEndDate", "")
        if end_date:
            try:
                dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                end_date = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                pass

        return {
            "item_id": item.get("itemId", ""),
            "title": item.get("title", ""),
            "price": price,
            "currency": currency,
            "shipping": shipping,
            "condition": item.get("condition", "N/A"),
            "url": item.get("itemWebUrl", ""),
            "image": item.get("image", {}).get("imageUrl", ""),
            "seller": {
                "username": seller.get("username", ""),
                "feedback_score": seller.get("feedbackScore", 0),
                "feedback_percent": seller.get("feedbackPercentage", ""),
            },
            "end_date": end_date,
            "buying_options": item.get("buyingOptions", []),
        }

    def _format_item_detail(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Format detailed item information."""
        # Start with summary fields
        result = {
            "item_id": item.get("itemId", ""),
            "title": item.get("title", ""),
            "price": item.get("price", {}).get("value", "N/A"),
            "currency": item.get("price", {}).get("currency", "USD"),
            "url": item.get("itemWebUrl", ""),
        }

        # Condition
        condition = item.get("condition", "")
        if isinstance(condition, dict):
            result["condition"] = condition.get("conditionDisplayName", "N/A")
        else:
            result["condition"] = condition or "N/A"

        # Description
        result["description"] = item.get("description", item.get("shortDescription", ""))

        # Item specifics
        aspects = item.get("localizedAspects", [])
        if aspects:
            result["specifics"] = {a.get("name", ""): a.get("value", "") for a in aspects}
        else:
            result["specifics"] = {}

        # Seller
        seller = item.get("seller", {})
        result["seller"] = {
            "username": seller.get("username", ""),
            "feedback_score": seller.get("feedbackScore", 0),
            "feedback_percent": seller.get("feedbackPercentage", ""),
        }

        # Shipping
        ship_options = item.get("shippingOptions", [])
        if ship_options:
            result["shipping"] = []
            for opt in ship_options:
                ship_info = {
                    "type": opt.get("shippingServiceCode", ""),
                    "cost": opt.get("shippingCost", {}).get("value", "N/A"),
                    "currency": opt.get("shippingCost", {}).get("currency", "USD"),
                }
                result["shipping"].append(ship_info)
        else:
            result["shipping"] = []

        # Images
        images = item.get("image", {})
        result["image"] = images.get("imageUrl", "")

        additional = item.get("additionalImages", [])
        result["additional_images"] = [img.get("imageUrl", "") for img in additional]

        # Location
        result["location"] = item.get("itemLocation", {}).get("postalCode", "")
        result["country"] = item.get("itemLocation", {}).get("country", "")

        return result
