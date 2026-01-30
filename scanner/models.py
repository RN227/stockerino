"""Data models for Market Scanner."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class EarningsResult(BaseModel):
    """Earnings scanner result."""
    symbol: str
    report_date: str
    report_time: Optional[str] = None  # AMC, BMO, or None
    eps_estimate: Optional[float] = None
    revenue_estimate: Optional[float] = None
    beat_rate: Optional[float] = None  # 0.0 to 1.0
    avg_surprise_pct: Optional[float] = None


class NewsResult(BaseModel):
    """News scanner result."""
    symbol: str
    title: str
    published_date: datetime
    url: str
    source: str
    sentiment: str  # bullish, bearish, neutral
    sentiment_score: int
    keywords_matched: List[str] = Field(default_factory=list)


class MomentumResult(BaseModel):
    """Momentum scanner result."""
    symbol: str
    price: float
    change_pct: float
    volume: int
    avg_volume: int
    year_high: Optional[float] = None
    year_low: Optional[float] = None
    signals: List[str] = Field(default_factory=list)


class Opportunity(BaseModel):
    """Top opportunity from Claude analysis."""
    rank: int
    ticker: str
    company: str
    setup_type: str  # Earnings Play, News Catalyst, Momentum Breakout
    catalyst: str
    thesis: str
    trade_setup: str
    key_risk: str
    conviction: int  # 1-10


class WatchlistItem(BaseModel):
    """Watchlist item from Claude analysis."""
    ticker: str
    reason: str


class SectorNews(BaseModel):
    """News link for sector summary."""
    title: str
    url: str


class SectorSummary(BaseModel):
    """Detailed sector summary."""
    outlook: str  # Bullish, Neutral, Cautious, Bearish
    overview: str  # 1-2 line summary
    news: List[SectorNews] = Field(default_factory=list)  # Up to 3 news links


class ScanAnalysis(BaseModel):
    """Complete scan analysis from Claude."""
    scan_date: str
    top_opportunities: List[Opportunity] = Field(default_factory=list)
    watchlist: List[WatchlistItem] = Field(default_factory=list)
    no_action: List[WatchlistItem] = Field(default_factory=list)
    sector_summary: dict = Field(default_factory=dict)  # sector name -> SectorSummary
