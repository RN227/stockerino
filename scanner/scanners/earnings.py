"""Earnings Scanner - Find stocks reporting earnings in next 5 trading days."""

import requests
from datetime import datetime, timedelta
from typing import List, Optional

from ..config import FMP_BASE_URL, FMP_API_KEY, FINNHUB_BASE_URL, FINNHUB_API_KEY, EARNINGS_LOOKAHEAD_DAYS
from ..models import EarningsResult


class EarningsScanner:
    """Scans for upcoming earnings in watchlist."""

    def __init__(self):
        self.fmp_base = FMP_BASE_URL
        self.fmp_key = FMP_API_KEY
        self.finnhub_base = FINNHUB_BASE_URL
        self.finnhub_key = FINNHUB_API_KEY

    def _get_earnings_calendar(self, from_date: str, to_date: str) -> List[dict]:
        """Fetch earnings calendar from FMP."""
        try:
            url = f"{self.fmp_base}/earnings-calendar"
            params = {
                "from": from_date,
                "to": to_date,
                "apikey": self.fmp_key
            }
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json() if isinstance(resp.json(), list) else []
        except Exception as e:
            print(f"[Warning] Failed to fetch earnings calendar: {e}")
            return []

    def _get_earnings_history(self, ticker: str) -> List[dict]:
        """Fetch earnings history from Finnhub for beat rate calculation."""
        try:
            url = f"{self.finnhub_base}/stock/earnings"
            params = {"symbol": ticker, "token": self.finnhub_key}
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json() if isinstance(resp.json(), list) else []
        except Exception as e:
            print(f"[Warning] Failed to fetch earnings history for {ticker}: {e}")
            return []

    def _calculate_beat_rate(self, history: List[dict]) -> Optional[float]:
        """Calculate beat rate from earnings history."""
        if not history:
            return None
        
        beats = sum(1 for e in history[:4] if e.get("actual") and e.get("estimate") 
                    and e["actual"] > e["estimate"])
        total = min(len(history), 4)
        return beats / total if total > 0 else None

    def _calculate_avg_surprise(self, history: List[dict]) -> Optional[float]:
        """Calculate average surprise percentage."""
        if not history:
            return None
        
        surprises = []
        for e in history[:4]:
            actual = e.get("actual")
            estimate = e.get("estimate")
            if actual and estimate and estimate != 0:
                surprise_pct = ((actual - estimate) / abs(estimate)) * 100
                surprises.append(surprise_pct)
        
        return sum(surprises) / len(surprises) if surprises else None

    def scan(self, watchlist: List[str]) -> List[EarningsResult]:
        """Scan for earnings in watchlist within lookahead period."""
        today = datetime.now()
        end_date = today + timedelta(days=EARNINGS_LOOKAHEAD_DAYS + 2)  # Buffer for weekends

        # Fetch calendar
        calendar = self._get_earnings_calendar(
            today.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d")
        )

        # Filter to watchlist
        watchlist_set = set(t.upper() for t in watchlist)
        watchlist_earnings = [e for e in calendar if e.get("symbol", "").upper() in watchlist_set]

        results = []
        for e in watchlist_earnings:
            symbol = e.get("symbol", "")
            
            # Get earnings history for beat rate
            history = self._get_earnings_history(symbol)
            beat_rate = self._calculate_beat_rate(history)
            avg_surprise = self._calculate_avg_surprise(history)

            results.append(EarningsResult(
                symbol=symbol,
                report_date=e.get("date", ""),
                report_time=e.get("time", "").upper() if e.get("time") else None,
                eps_estimate=e.get("epsEstimated"),
                revenue_estimate=e.get("revenueEstimated"),
                beat_rate=beat_rate,
                avg_surprise_pct=avg_surprise
            ))

        return results
