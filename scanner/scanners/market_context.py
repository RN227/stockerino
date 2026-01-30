"""Market Context Scanner - SPY, QQQ, VIX, Sector ETFs."""

import yfinance as yf
from typing import Dict, Optional
from pydantic import BaseModel


class MarketContext(BaseModel):
    """Overall market conditions."""
    spy_price: float
    spy_change_pct: float
    qqq_price: float
    qqq_change_pct: float
    vix_level: float
    vix_change_pct: float
    market_sentiment: str  # "risk_on", "risk_off", "neutral"
    sector_performance: Dict[str, float]  # ETF -> change %


class MarketContextScanner:
    """Scans overall market conditions."""

    def __init__(self):
        # Key market indices
        self.indices = {
            "SPY": "S&P 500",
            "QQQ": "Nasdaq 100",
            "^VIX": "VIX"
        }
        
        # Sector ETFs relevant to our watchlist
        self.sector_etfs = {
            "SMH": "Semiconductors",
            "IGV": "Software",
            "XLE": "Energy",
            "ITA": "Aerospace/Defense",
            "ARKQ": "Robotics/Automation"
        }

    def scan(self) -> Optional[MarketContext]:
        """Get current market context."""
        try:
            # Fetch index data
            spy = yf.Ticker("SPY")
            qqq = yf.Ticker("QQQ")
            vix = yf.Ticker("^VIX")
            
            spy_info = spy.info
            qqq_info = qqq.info
            vix_info = vix.info
            
            spy_price = spy_info.get('currentPrice') or spy_info.get('regularMarketPrice', 0)
            spy_prev = spy_info.get('previousClose', spy_price)
            spy_change = ((spy_price - spy_prev) / spy_prev * 100) if spy_prev else 0
            
            qqq_price = qqq_info.get('currentPrice') or qqq_info.get('regularMarketPrice', 0)
            qqq_prev = qqq_info.get('previousClose', qqq_price)
            qqq_change = ((qqq_price - qqq_prev) / qqq_prev * 100) if qqq_prev else 0
            
            vix_level = vix_info.get('currentPrice') or vix_info.get('regularMarketPrice', 0)
            vix_prev = vix_info.get('previousClose', vix_level)
            vix_change = ((vix_level - vix_prev) / vix_prev * 100) if vix_prev else 0
            
            # Determine market sentiment
            if vix_level > 25:
                sentiment = "risk_off"
            elif vix_level < 15 and spy_change > 0:
                sentiment = "risk_on"
            elif spy_change > 0.5 and qqq_change > 0.5:
                sentiment = "risk_on"
            elif spy_change < -0.5 and qqq_change < -0.5:
                sentiment = "risk_off"
            else:
                sentiment = "neutral"
            
            # Fetch sector ETF performance
            sector_perf = {}
            for etf, name in self.sector_etfs.items():
                try:
                    ticker = yf.Ticker(etf)
                    info = ticker.info
                    price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
                    prev = info.get('previousClose', price)
                    change = ((price - prev) / prev * 100) if prev else 0
                    sector_perf[etf] = round(change, 2)
                except:
                    continue
            
            return MarketContext(
                spy_price=round(spy_price, 2),
                spy_change_pct=round(spy_change, 2),
                qqq_price=round(qqq_price, 2),
                qqq_change_pct=round(qqq_change, 2),
                vix_level=round(vix_level, 2),
                vix_change_pct=round(vix_change, 2),
                market_sentiment=sentiment,
                sector_performance=sector_perf
            )
            
        except Exception as e:
            print(f"[Warning] Failed to get market context: {e}")
            return None
