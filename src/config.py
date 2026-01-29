"""Configuration module for API keys and settings."""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration loaded from environment variables."""

    # Required API Keys
    FINNHUB_API_KEY: str = os.getenv("FINNHUB_API_KEY", "")
    FMP_API_KEY: str = os.getenv("FMP_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    # Optional API Keys
    TRADIER_API_KEY: str = os.getenv("TRADIER_API_KEY", "")

    # Settings
    CACHE_TTL: int = int(os.getenv("STOCK_ASSISTANT_CACHE_TTL", "300"))
    NEWS_DAYS: int = int(os.getenv("STOCK_ASSISTANT_NEWS_DAYS", "7"))

    # API Base URLs
    FINNHUB_BASE_URL: str = "https://finnhub.io/api/v1"
    FMP_BASE_URL: str = "https://financialmodelingprep.com/stable"
    TRADIER_BASE_URL: str = "https://api.tradier.com/v1"

    # Rate limits (calls per period in seconds)
    RATE_LIMITS: dict = {
        "finnhub": {"calls": 60, "period": 60},
        "fmp": {"calls": 250, "period": 86400},
    }

    @classmethod
    def validate(cls) -> list[str]:
        """Validate required configuration. Returns list of missing keys."""
        missing = []
        if not cls.FINNHUB_API_KEY:
            missing.append("FINNHUB_API_KEY")
        if not cls.FMP_API_KEY:
            missing.append("FMP_API_KEY")
        if not cls.ANTHROPIC_API_KEY:
            missing.append("ANTHROPIC_API_KEY")
        return missing

    @classmethod
    def has_tradier(cls) -> bool:
        """Check if Tradier API is configured."""
        return bool(cls.TRADIER_API_KEY)


config = Config()
