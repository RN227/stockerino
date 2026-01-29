"""Tradier API client for options data."""

import requests
from datetime import datetime
from typing import Optional

from ..config import config
from ..models.stock_data import OptionsData, OptionContract


class TradierClient:
    """Client for Tradier API (options data)."""

    def __init__(self):
        self.base_url = config.TRADIER_BASE_URL
        self.api_key = config.TRADIER_API_KEY

    def _request(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """Make authenticated request to Tradier API."""
        if params is None:
            params = {}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }

        url = f"{self.base_url}{endpoint}"
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()

    def get_expirations(self, ticker: str) -> list[str]:
        """Get available option expiration dates."""
        try:
            data = self._request("/markets/options/expirations", {"symbol": ticker.upper()})

            expirations = data.get("expirations", {}).get("date", [])

            if isinstance(expirations, str):
                return [expirations]

            return expirations or []
        except requests.RequestException as e:
            print(f"[Warning] Failed to fetch expirations from Tradier: {e}")
            return []

    def get_options_chain(self, ticker: str, expiration: Optional[str] = None) -> Optional[OptionsData]:
        """Get options chain for a ticker."""
        if not config.has_tradier():
            return None

        try:
            # Get nearest expiration if not specified
            if not expiration:
                expirations = self.get_expirations(ticker)
                if not expirations:
                    return None
                expiration = expirations[0]

            data = self._request(
                "/markets/options/chains",
                {"symbol": ticker.upper(), "expiration": expiration, "greeks": "true"},
            )

            options = data.get("options", {}).get("option", [])

            if not options:
                return None

            calls = []
            puts = []

            for opt in options:
                try:
                    greeks = opt.get("greeks", {}) or {}

                    contract = OptionContract(
                        strike=opt.get("strike", 0),
                        bid=opt.get("bid", 0) or 0,
                        ask=opt.get("ask", 0) or 0,
                        volume=opt.get("volume", 0) or 0,
                        open_interest=opt.get("open_interest", 0) or 0,
                        delta=greeks.get("delta"),
                        implied_volatility=greeks.get("mid_iv"),
                        option_type=opt.get("option_type", "call"),
                    )

                    if opt.get("option_type") == "call":
                        calls.append(contract)
                    else:
                        puts.append(contract)
                except Exception:
                    continue

            return OptionsData(
                expiration=expiration,
                calls=calls,
                puts=puts,
            )
        except requests.RequestException as e:
            print(f"[Warning] Failed to fetch options chain from Tradier: {e}")
            return None
