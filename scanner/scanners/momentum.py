"""Momentum Scanner - Flag unusual price/volume activity."""

import requests
from typing import List

from ..config import FINNHUB_BASE_URL, FINNHUB_API_KEY, VOLUME_THRESHOLD, PRICE_CHANGE_THRESHOLD
from ..models import MomentumResult


class MomentumScanner:
    """Scans for momentum signals in watchlist using Finnhub."""

    def __init__(self):
        self.finnhub_base = FINNHUB_BASE_URL
        self.finnhub_key = FINNHUB_API_KEY
        self.volume_threshold = VOLUME_THRESHOLD
        self.price_threshold = PRICE_CHANGE_THRESHOLD
        self.high_proximity_pct = 5.0  # Within 5% of 52-week high

    def _get_quote(self, ticker: str) -> dict:
        """Fetch quote from Finnhub."""
        try:
            url = f"{self.finnhub_base}/quote"
            params = {"symbol": ticker, "token": self.finnhub_key}
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"[Warning] Failed to fetch quote for {ticker}: {e}")
            return {}

    def _get_basic_financials(self, ticker: str) -> dict:
        """Fetch basic financials from Finnhub for 52-week high/low."""
        try:
            url = f"{self.finnhub_base}/stock/metric"
            params = {"symbol": ticker, "metric": "all", "token": self.finnhub_key}
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return data.get("metric", {})
        except Exception:
            return {}

    def scan(self, watchlist: List[str]) -> List[MomentumResult]:
        """Scan for momentum signals in watchlist."""
        results = []
        
        for ticker in watchlist:
            quote = self._get_quote(ticker)
            if not quote or quote.get("c") is None:
                continue
            
            price = quote.get("c", 0)
            prev_close = quote.get("pc", 0)
            change_pct = quote.get("dp", 0) or 0
            
            # Get 52-week data
            metrics = self._get_basic_financials(ticker)
            year_high = metrics.get("52WeekHigh")
            year_low = metrics.get("52WeekLow")
            
            # Finnhub doesn't have volume in quote, skip volume signals
            # Focus on price-based signals
            signals = []
            
            # Price change
            if abs(change_pct) > self.price_threshold:
                direction = "up" if change_pct > 0 else "down"
                signals.append(f"Price {direction} {abs(change_pct):.1f}%")
            
            # Near 52-week high
            if year_high and price > year_high * (1 - self.high_proximity_pct / 100):
                signals.append(f"Near 52-week high (${year_high:.2f})")
            
            # Near 52-week low
            if year_low and price < year_low * (1 + self.high_proximity_pct / 100):
                signals.append(f"Near 52-week low (${year_low:.2f})")
            
            # Gap detection (significant open vs prev close)
            open_price = quote.get("o", 0)
            if prev_close and open_price:
                gap_pct = ((open_price - prev_close) / prev_close) * 100
                if abs(gap_pct) > 2.0:
                    direction = "up" if gap_pct > 0 else "down"
                    signals.append(f"Gap {direction} {abs(gap_pct):.1f}%")
            
            # Only include if has signals
            if signals:
                results.append(MomentumResult(
                    symbol=ticker,
                    price=price,
                    change_pct=change_pct,
                    volume=0,  # Not available in Finnhub free quote
                    avg_volume=0,
                    year_high=year_high,
                    year_low=year_low,
                    signals=signals
                ))
        
        # Sort by number of signals, then by price change
        results.sort(key=lambda x: (len(x.signals), abs(x.change_pct)), reverse=True)
        
        return results
