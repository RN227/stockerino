"""Pre-Market Movers Scanner."""

import yfinance as yf
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class PreMarketMover(BaseModel):
    """Pre-market mover data."""
    symbol: str
    name: str
    price: float
    change_pct: float
    volume: int
    on_watchlist: bool
    reason: str = ""  # Why it's moving if known


class PreMarketScanner:
    """Scans for pre-market movers."""

    def __init__(self):
        self.significant_move_pct = 3.0  # 3% move is significant
        
        # Additional high-profile stocks to monitor beyond watchlist
        self.always_watch = [
            "SPY", "QQQ", "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META"
        ]

    def scan(self, watchlist_tickers: List[str]) -> List[PreMarketMover]:
        """Scan pre-market movers."""
        movers = []
        
        # Combine watchlist with always-watch list
        all_tickers = list(set(watchlist_tickers + self.always_watch))
        
        for ticker in all_tickers:
            try:
                mover = self._check_ticker(ticker, ticker in watchlist_tickers)
                if mover:
                    movers.append(mover)
            except Exception as e:
                continue
        
        # Sort by absolute change percentage
        movers.sort(key=lambda x: abs(x.change_pct), reverse=True)
        
        return movers

    def _check_ticker(self, ticker: str, on_watchlist: bool) -> Optional[PreMarketMover]:
        """Check single ticker for pre-market activity."""
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Get pre-market or regular price
        pre_market_price = info.get('preMarketPrice')
        regular_price = info.get('currentPrice') or info.get('regularMarketPrice')
        prev_close = info.get('previousClose') or info.get('regularMarketPreviousClose')
        
        if not prev_close:
            return None
        
        # Use pre-market price if available, otherwise regular price
        current_price = pre_market_price or regular_price
        if not current_price:
            return None
        
        change_pct = ((current_price - prev_close) / prev_close) * 100
        
        # Only return if significant move
        if abs(change_pct) < self.significant_move_pct:
            return None
        
        # Get volume
        volume = info.get('preMarketVolume') or info.get('volume') or 0
        
        # Get company name
        name = info.get('shortName', ticker)
        
        return PreMarketMover(
            symbol=ticker,
            name=name,
            price=round(current_price, 2),
            change_pct=round(change_pct, 2),
            volume=volume,
            on_watchlist=on_watchlist
        )

    def get_market_futures(self) -> dict:
        """Get index futures for market direction."""
        futures = {}
        
        # S&P 500 futures (ES)
        try:
            spy = yf.Ticker("ES=F")
            info = spy.info
            price = info.get('regularMarketPrice', 0)
            prev = info.get('previousClose', price)
            change = ((price - prev) / prev * 100) if prev else 0
            futures['S&P 500 Futures'] = round(change, 2)
        except:
            pass
        
        # Nasdaq futures (NQ)
        try:
            nq = yf.Ticker("NQ=F")
            info = nq.info
            price = info.get('regularMarketPrice', 0)
            prev = info.get('previousClose', price)
            change = ((price - prev) / prev * 100) if prev else 0
            futures['Nasdaq Futures'] = round(change, 2)
        except:
            pass
        
        return futures
