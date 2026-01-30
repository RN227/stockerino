"""Technical Analysis Scanner - RSI, Moving Averages, Short Interest."""

import requests
import yfinance as yf
import numpy as np
from typing import List, Optional
from pydantic import BaseModel, Field

from ..config import FINNHUB_API_KEY, FINNHUB_BASE_URL


class TechnicalSignal(BaseModel):
    """Technical analysis for a stock."""
    symbol: str
    price: float
    rsi_14: Optional[float] = None  # 14-day RSI
    ma_50: Optional[float] = None   # 50-day moving average
    ma_200: Optional[float] = None  # 200-day moving average
    above_50ma: Optional[bool] = None
    above_200ma: Optional[bool] = None
    short_interest_ratio: Optional[float] = None  # Days to cover
    short_percent_float: Optional[float] = None   # % of float shorted
    signals: List[str] = Field(default_factory=list)


class TechnicalsScanner:
    """Scans for technical signals (RSI, MA, Short Interest)."""

    def __init__(self):
        self.rsi_overbought = 70
        self.rsi_oversold = 30
        self.high_short_interest = 10  # >10% of float

    def scan(self, tickers: List[str]) -> List[TechnicalSignal]:
        """Scan tickers for technical signals."""
        results = []
        
        for ticker in tickers:
            try:
                signal = self._analyze_ticker(ticker)
                if signal and signal.signals:  # Only include if has signals
                    results.append(signal)
            except Exception as e:
                print(f"[Warning] Technical scan failed for {ticker}: {e}")
                continue
        
        return results

    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> Optional[float]:
        """Calculate RSI from price array."""
        if len(prices) < period + 1:
            return None
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])
        
        if avg_loss == 0:
            return 100.0
        
        # Smoothed RS calculation
        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return round(rsi, 1)

    def _get_short_interest(self, ticker: str) -> tuple:
        """Get short interest data from Finnhub."""
        try:
            url = f"{FINNHUB_BASE_URL}/stock/short-interest"
            params = {"symbol": ticker, "token": FINNHUB_API_KEY}
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()
            
            if data and "data" in data and len(data["data"]) > 0:
                latest = data["data"][0]
                short_ratio = latest.get("shortInterestRatio")  # Days to cover
                short_pct = latest.get("shortInterestPercentFloat")
                return short_ratio, short_pct
        except:
            pass
        return None, None

    def _analyze_ticker(self, ticker: str) -> Optional[TechnicalSignal]:
        """Analyze single ticker for technical signals."""
        stock = yf.Ticker(ticker)
        
        # Get historical data for calculations (200 days + buffer)
        hist = stock.history(period="1y")
        
        if hist.empty or len(hist) < 50:
            return None
        
        closes = hist['Close'].values
        current_price = closes[-1]
        
        # Calculate RSI
        rsi = self._calculate_rsi(closes)
        
        # Calculate moving averages
        ma_50 = np.mean(closes[-50:]) if len(closes) >= 50 else None
        ma_200 = np.mean(closes[-200:]) if len(closes) >= 200 else None
        
        above_50ma = current_price > ma_50 if ma_50 else None
        above_200ma = current_price > ma_200 if ma_200 else None
        
        # Get short interest
        short_ratio, short_pct = self._get_short_interest(ticker)
        
        # Build signals
        signals = []
        
        # RSI signals
        if rsi:
            if rsi >= self.rsi_overbought:
                signals.append(f"RSI overbought ({rsi})")
            elif rsi <= self.rsi_oversold:
                signals.append(f"RSI oversold ({rsi})")
        
        # Moving average signals
        if ma_50 and ma_200:
            if above_50ma and above_200ma:
                signals.append("Above 50 & 200 MA (bullish)")
            elif not above_50ma and not above_200ma:
                signals.append("Below 50 & 200 MA (bearish)")
            
            # Golden/Death cross check (approximate)
            ma_50_prev = np.mean(closes[-55:-5]) if len(closes) >= 55 else None
            ma_200_prev = np.mean(closes[-205:-5]) if len(closes) >= 205 else None
            
            if ma_50_prev and ma_200_prev:
                if ma_50 > ma_200 and ma_50_prev <= ma_200_prev:
                    signals.append("Golden cross forming")
                elif ma_50 < ma_200 and ma_50_prev >= ma_200_prev:
                    signals.append("Death cross forming")
        
        # Short interest signals
        if short_pct and short_pct >= self.high_short_interest:
            signals.append(f"High short interest ({short_pct:.1f}%)")
        
        return TechnicalSignal(
            symbol=ticker,
            price=round(current_price, 2),
            rsi_14=rsi,
            ma_50=round(ma_50, 2) if ma_50 else None,
            ma_200=round(ma_200, 2) if ma_200 else None,
            above_50ma=above_50ma,
            above_200ma=above_200ma,
            short_interest_ratio=short_ratio,
            short_percent_float=short_pct,
            signals=signals
        )
