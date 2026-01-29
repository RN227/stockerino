"""Finnhub API client for stock data."""

import requests
from datetime import datetime, timedelta
from typing import Optional, Union

from ..config import config
from ..models.stock_data import (
    PriceData,
    NewsArticle,
    AnalystRecommendations,
    PriceTargets,
    EarningsData,
    EarningsSurprise,
)


class FinnhubClient:
    """Client for Finnhub API."""

    def __init__(self):
        self.base_url = config.FINNHUB_BASE_URL
        self.api_key = config.FINNHUB_API_KEY

    def _request(self, endpoint: str, params: Optional[dict] = None) -> Union[dict, list]:
        """Make authenticated request to Finnhub API."""
        if params is None:
            params = {}
        params["token"] = self.api_key

        url = f"{self.base_url}{endpoint}"
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

    def get_quote(self, ticker: str) -> Optional[PriceData]:
        """Get current price data for a ticker."""
        try:
            data = self._request("/quote", {"symbol": ticker.upper()})

            # Check if we got valid data
            if not data or data.get("c") is None or data.get("c") == 0:
                return None

            return PriceData(
                current_price=data.get("c", 0),
                high_today=data.get("h", 0),
                low_today=data.get("l", 0),
                open_price=data.get("o", 0),
                previous_close=data.get("pc", 0),
                change=data.get("d", 0) or 0,
                change_percent=data.get("dp", 0) or 0,
            )
        except requests.RequestException as e:
            print(f"[Warning] Failed to fetch quote from Finnhub: {e}")
            return None

    def get_company_news(self, ticker: str, days: int = 7) -> list[NewsArticle]:
        """Get recent news articles for a ticker."""
        try:
            to_date = datetime.now()
            from_date = to_date - timedelta(days=days)

            data = self._request(
                "/company-news",
                {
                    "symbol": ticker.upper(),
                    "from": from_date.strftime("%Y-%m-%d"),
                    "to": to_date.strftime("%Y-%m-%d"),
                },
            )

            articles = []
            for item in data[:10]:  # Limit to 10 articles
                try:
                    articles.append(
                        NewsArticle(
                            title=item.get("headline", ""),
                            summary=item.get("summary"),
                            published_at=datetime.fromtimestamp(item.get("datetime", 0)),
                            source=item.get("source", "Unknown"),
                            url=item.get("url", ""),
                            sentiment=None,
                        )
                    )
                except Exception:
                    continue

            return articles
        except requests.RequestException as e:
            print(f"[Warning] Failed to fetch news from Finnhub: {e}")
            return []

    def get_recommendations(self, ticker: str) -> Optional[AnalystRecommendations]:
        """Get analyst recommendations for a ticker."""
        try:
            data = self._request("/stock/recommendation", {"symbol": ticker.upper()})

            if not data:
                return None

            # Get the most recent recommendation
            latest = data[0] if data else {}

            return AnalystRecommendations(
                strong_buy=latest.get("strongBuy", 0),
                buy=latest.get("buy", 0),
                hold=latest.get("hold", 0),
                sell=latest.get("sell", 0),
                strong_sell=latest.get("strongSell", 0),
                period=latest.get("period"),
            )
        except requests.RequestException as e:
            print(f"[Warning] Failed to fetch recommendations from Finnhub: {e}")
            return None

    def get_price_target(self, ticker: str) -> Optional[PriceTargets]:
        """Get analyst price targets for a ticker."""
        try:
            data = self._request("/stock/price-target", {"symbol": ticker.upper()})

            if not data:
                return None

            return PriceTargets(
                high=data.get("targetHigh"),
                low=data.get("targetLow"),
                consensus=data.get("targetMean"),
                median=data.get("targetMedian"),
            )
        except requests.RequestException as e:
            print(f"[Warning] Failed to fetch price targets from Finnhub: {e}")
            return None

    def get_upcoming_earnings(self, ticker: str) -> Optional[EarningsData]:
        """Get upcoming earnings date and estimates."""
        try:
            data = self._request("/calendar/earnings", {"symbol": ticker.upper()})

            earnings_list = data.get("earningsCalendar", [])
            if not earnings_list:
                return None

            # Get the first (upcoming) earnings
            earnings = earnings_list[0]

            return EarningsData(
                earnings_date=datetime.strptime(earnings.get("date", ""), "%Y-%m-%d"),
                eps_estimate=earnings.get("epsEstimate"),
                revenue_estimate=earnings.get("revenueEstimate"),
            )
        except (requests.RequestException, ValueError) as e:
            print(f"[Warning] Failed to fetch upcoming earnings from Finnhub: {e}")
            return None

    def get_earnings_history(self, ticker: str, limit: int = 4) -> list[EarningsSurprise]:
        """Get historical earnings surprises."""
        try:
            data = self._request("/stock/earnings", {"symbol": ticker.upper()})

            if not data or not isinstance(data, list):
                return []

            surprises = []
            for item in data[:limit]:
                try:
                    actual = item.get("actual")
                    estimated = item.get("estimate")

                    if actual is not None and estimated is not None:
                        surprises.append(
                            EarningsSurprise(
                                quarter_date=datetime.strptime(item.get("period", ""), "%Y-%m-%d"),
                                actual_eps=actual,
                                estimated_eps=estimated,
                            )
                        )
                except (ValueError, TypeError):
                    continue

            return surprises
        except requests.RequestException as e:
            print(f"[Warning] Failed to fetch earnings history from Finnhub: {e}")
            return []
