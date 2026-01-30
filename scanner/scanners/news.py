"""News Scanner - Identify catalyst-driven opportunities from recent news."""

import requests
from datetime import datetime, timedelta
from typing import List

from ..config import FMP_BASE_URL, FMP_API_KEY, FINNHUB_BASE_URL, FINNHUB_API_KEY, SCAN_LOOKBACK_HOURS
from ..models import NewsResult


# Keywords for sentiment scoring
BULLISH_KEYWORDS = [
    "acquisition", "acquire", "merger", "deal", "partnership",
    "contract", "awarded", "patent", "fda approval", "breakthrough",
    "upgrade", "outperform", "buy rating", "price target raised",
    "beat", "exceeds", "record revenue", "guidance raised",
    "ai", "artificial intelligence", "data center", "quantum",
    "nuclear", "smr", "uranium", "robot", "autonomous"
]

BEARISH_KEYWORDS = [
    "downgrade", "sell rating", "price target cut", "misses",
    "lawsuit", "investigation", "recall", "warning", "layoffs",
    "guidance cut", "below expectations", "delays", "loss",
    "bankruptcy", "default", "fraud", "sec probe"
]


class NewsScanner:
    """Scans for news catalysts in watchlist."""

    def __init__(self):
        self.fmp_base = FMP_BASE_URL
        self.fmp_key = FMP_API_KEY
        self.finnhub_base = FINNHUB_BASE_URL
        self.finnhub_key = FINNHUB_API_KEY

    def _get_finnhub_news(self, ticker: str, from_date: str, to_date: str) -> List[dict]:
        """Fetch company news from Finnhub."""
        try:
            url = f"{self.finnhub_base}/company-news"
            params = {
                "symbol": ticker,
                "from": from_date,
                "to": to_date,
                "token": self.finnhub_key
            }
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return data if isinstance(data, list) else []
        except Exception as e:
            print(f"[Warning] Failed to fetch news for {ticker}: {e}")
            return []

    def _score_article(self, title: str, summary: str = "") -> tuple:
        """Score article for sentiment. Returns (score, sentiment, keywords)."""
        text = f"{title} {summary}".lower()
        
        bullish_hits = []
        bearish_hits = []
        
        for kw in BULLISH_KEYWORDS:
            if kw in text:
                bullish_hits.append(kw)
        
        for kw in BEARISH_KEYWORDS:
            if kw in text:
                bearish_hits.append(kw)
        
        score = len(bullish_hits) - len(bearish_hits)
        
        if score > 0:
            sentiment = "bullish"
            keywords = bullish_hits
        elif score < 0:
            sentiment = "bearish"
            keywords = bearish_hits
        else:
            sentiment = "neutral"
            keywords = bullish_hits + bearish_hits
        
        return score, sentiment, keywords

    def scan(self, watchlist: List[str]) -> List[NewsResult]:
        """Scan for news catalysts in watchlist."""
        cutoff = datetime.now() - timedelta(hours=SCAN_LOOKBACK_HOURS)
        to_date = datetime.now().strftime("%Y-%m-%d")
        from_date = cutoff.strftime("%Y-%m-%d")

        results = []
        
        for ticker in watchlist:
            articles = self._get_finnhub_news(ticker, from_date, to_date)
            
            for article in articles[:5]:  # Limit per ticker
                try:
                    # Parse timestamp
                    timestamp = article.get("datetime", 0)
                    if timestamp:
                        pub_date = datetime.fromtimestamp(timestamp)
                        if pub_date < cutoff:
                            continue
                    else:
                        continue
                    
                    title = article.get("headline", "")
                    summary = article.get("summary", "")
                    
                    # Score the article
                    score, sentiment, keywords = self._score_article(title, summary)
                    
                    # Only include if has sentiment signal
                    if score != 0:
                        results.append(NewsResult(
                            symbol=ticker,
                            title=title,
                            published_date=pub_date,
                            url=article.get("url", ""),
                            source=article.get("source", "Unknown"),
                            sentiment=sentiment,
                            sentiment_score=score,
                            keywords_matched=keywords
                        ))
                except Exception:
                    continue

        # Sort by absolute sentiment score
        results.sort(key=lambda x: abs(x.sentiment_score), reverse=True)
        
        return results
