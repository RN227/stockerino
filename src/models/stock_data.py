"""Data models for stock information."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class PriceData(BaseModel):
    """Current price data for a stock."""

    current_price: float = Field(description="Current stock price")
    high_today: float = Field(description="Today's high")
    low_today: float = Field(description="Today's low")
    open_price: float = Field(description="Opening price")
    previous_close: float = Field(description="Previous closing price")
    change: float = Field(description="Price change")
    change_percent: float = Field(description="Price change percentage")


class CompanyProfile(BaseModel):
    """Company profile information."""

    name: str = Field(description="Company name")
    sector: Optional[str] = Field(default=None, description="Business sector")
    industry: Optional[str] = Field(default=None, description="Industry")
    market_cap: Optional[float] = Field(default=None, description="Market capitalization")
    beta: Optional[float] = Field(default=None, description="Beta coefficient")
    description: Optional[str] = Field(default=None, description="Company description")


class NewsArticle(BaseModel):
    """News article about a stock."""

    title: str = Field(description="Article headline")
    summary: Optional[str] = Field(default=None, description="Article summary")
    published_at: datetime = Field(description="Publication timestamp")
    source: str = Field(description="News source")
    url: str = Field(description="Article URL")
    sentiment: Optional[str] = Field(default=None, description="Sentiment: positive/negative/neutral")


class PriceTargets(BaseModel):
    """Analyst price targets."""

    high: Optional[float] = Field(default=None, description="Highest price target")
    low: Optional[float] = Field(default=None, description="Lowest price target")
    consensus: Optional[float] = Field(default=None, description="Consensus price target")
    median: Optional[float] = Field(default=None, description="Median price target")


class AnalystRecommendations(BaseModel):
    """Analyst recommendations breakdown."""

    strong_buy: int = Field(default=0, description="Strong buy count")
    buy: int = Field(default=0, description="Buy count")
    hold: int = Field(default=0, description="Hold count")
    sell: int = Field(default=0, description="Sell count")
    strong_sell: int = Field(default=0, description="Strong sell count")
    period: Optional[str] = Field(default=None, description="Recommendation period")


class EarningsData(BaseModel):
    """Upcoming earnings information."""

    earnings_date: Optional[datetime] = Field(default=None, description="Next earnings date")
    eps_estimate: Optional[float] = Field(default=None, description="EPS estimate")
    revenue_estimate: Optional[float] = Field(default=None, description="Revenue estimate")


class EarningsSurprise(BaseModel):
    """Historical earnings surprise data."""

    quarter_date: datetime = Field(description="Quarter end date")
    actual_eps: float = Field(description="Actual EPS")
    estimated_eps: float = Field(description="Estimated EPS")

    @property
    def beat(self) -> bool:
        """Did earnings beat estimates?"""
        return self.actual_eps > self.estimated_eps


class OptionContract(BaseModel):
    """Single option contract data."""

    strike: float = Field(description="Strike price")
    bid: float = Field(description="Bid price")
    ask: float = Field(description="Ask price")
    volume: int = Field(description="Trading volume")
    open_interest: int = Field(description="Open interest")
    delta: Optional[float] = Field(default=None, description="Delta")
    implied_volatility: Optional[float] = Field(default=None, description="Implied volatility")
    option_type: str = Field(description="call or put")


class OptionsData(BaseModel):
    """Options chain data."""

    expiration: str = Field(description="Expiration date")
    calls: list[OptionContract] = Field(default_factory=list, description="Call options")
    puts: list[OptionContract] = Field(default_factory=list, description="Put options")


class StockData(BaseModel):
    """Complete stock data for analysis."""

    ticker: str = Field(description="Stock ticker symbol")
    fetched_at: datetime = Field(default_factory=datetime.utcnow, description="Data fetch timestamp")
    price: Optional[PriceData] = Field(default=None, description="Current price data")
    profile: Optional[CompanyProfile] = Field(default=None, description="Company profile")
    news: list[NewsArticle] = Field(default_factory=list, description="Recent news")
    price_targets: Optional[PriceTargets] = Field(default=None, description="Analyst price targets")
    recommendations: Optional[AnalystRecommendations] = Field(default=None, description="Analyst recommendations")
    upcoming_earnings: Optional[EarningsData] = Field(default=None, description="Upcoming earnings")
    earnings_history: list[EarningsSurprise] = Field(default_factory=list, description="Historical earnings")
    options: Optional[OptionsData] = Field(default=None, description="Options chain")

    def to_analysis_dict(self) -> dict:
        """Convert to dictionary format for Claude analysis."""
        return {
            "ticker": self.ticker,
            "fetched_at": self.fetched_at.isoformat(),
            "current_price": self.price.model_dump() if self.price else None,
            "company_profile": self.profile.model_dump() if self.profile else None,
            "news": [n.model_dump() for n in self.news],
            "price_targets": self.price_targets.model_dump() if self.price_targets else None,
            "analyst_recommendations": self.recommendations.model_dump() if self.recommendations else None,
            "upcoming_earnings": self.upcoming_earnings.model_dump() if self.upcoming_earnings else None,
            "earnings_history": [e.model_dump() for e in self.earnings_history],
            "options_chain": self.options.model_dump() if self.options else None,
        }
