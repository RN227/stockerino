"""Financial Modeling Prep API client (stable endpoints)."""

import requests
from datetime import datetime
from typing import Optional, Union

from ..config import config
from ..models.stock_data import (
    CompanyProfile,
    PriceTargets,
)


class FMPClient:
    """Client for Financial Modeling Prep API (stable endpoints)."""

    def __init__(self):
        self.base_url = config.FMP_BASE_URL
        self.api_key = config.FMP_API_KEY

    def _request(self, endpoint: str, params: Optional[dict] = None) -> Union[dict, list]:
        """Make authenticated request to FMP API."""
        if params is None:
            params = {}
        params["apikey"] = self.api_key

        url = f"{self.base_url}{endpoint}"
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

    def get_profile(self, ticker: str) -> Optional[CompanyProfile]:
        """Get company profile for a ticker."""
        try:
            data = self._request("/profile", {"symbol": ticker.upper()})

            if not data or not isinstance(data, list) or len(data) == 0:
                return None

            profile = data[0]

            return CompanyProfile(
                name=profile.get("companyName", ticker.upper()),
                sector=profile.get("sector"),
                industry=profile.get("industry"),
                market_cap=profile.get("marketCap"),
                beta=profile.get("beta"),
                description=profile.get("description"),
            )
        except requests.RequestException as e:
            print(f"[Warning] Failed to fetch profile from FMP: {e}")
            return None

    def get_price_target_consensus(self, ticker: str) -> Optional[PriceTargets]:
        """Get consensus price targets for a ticker."""
        try:
            data = self._request("/price-target-consensus", {"symbol": ticker.upper()})

            if not data or not isinstance(data, list) or len(data) == 0:
                return None

            targets = data[0]

            return PriceTargets(
                high=targets.get("targetHigh"),
                low=targets.get("targetLow"),
                consensus=targets.get("targetConsensus"),
                median=targets.get("targetMedian"),
            )
        except requests.RequestException as e:
            print(f"[Warning] Failed to fetch price targets from FMP: {e}")
            return None
