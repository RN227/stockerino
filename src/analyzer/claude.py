"""Claude API integration for stock analysis."""

import json
import anthropic
from typing import Optional

from ..config import config
from ..models.stock_data import StockData


SYSTEM_PROMPT = """You are a stock analysis assistant. Your job is to analyze the provided market data and give actionable trading recommendations.

ANALYSIS FRAMEWORK:
1. Summarize the current state (price, momentum, sentiment)
2. Evaluate news impact (bullish/bearish/neutral signals)
3. Compare current price to analyst targets
4. Assess earnings positioning (upcoming date, historical beats/misses)
5. Identify short-term trade opportunities if any exist

RECOMMENDATION FORMAT:
- Overall Sentiment: [Bullish/Bearish/Neutral]
- Confidence: [1-10]
- Time Horizon: [Immediate/1 week/1 month/3 months/6 months]
- Action: [Strong Buy/Buy/Hold/Sell/Strong Sell]
- Trade Setup (if applicable): Specific options strategy or entry point

RULES:
- Be concise but thorough
- Flag any red flags or catalysts
- If earnings are within 2 weeks, factor earnings risk into recommendations
- If news is significant (M&A, major partnership, regulatory), weight it heavily
- Always mention the key risk to your thesis"""


class ClaudeAnalyzer:
    """Analyzes stock data using Claude API."""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        self.model = "claude-sonnet-4-20250514"

    def _format_price_data(self, data: StockData) -> str:
        """Format price data for prompt."""
        if not data.price:
            return "No price data available"

        p = data.price
        return f"""Price: ${p.current_price:.2f}
Change: ${p.change:+.2f} ({p.change_percent:+.2f}%)
Day Range: ${p.low_today:.2f} - ${p.high_today:.2f}
Previous Close: ${p.previous_close:.2f}"""

    def _format_profile(self, data: StockData) -> str:
        """Format company profile for prompt."""
        if not data.profile:
            return "No company profile available"

        p = data.profile
        market_cap_str = ""
        if p.market_cap:
            if p.market_cap >= 1e12:
                market_cap_str = f"${p.market_cap/1e12:.2f}T"
            elif p.market_cap >= 1e9:
                market_cap_str = f"${p.market_cap/1e9:.2f}B"
            else:
                market_cap_str = f"${p.market_cap/1e6:.2f}M"

        return f"""{p.name}
Sector: {p.sector or 'N/A'} | Industry: {p.industry or 'N/A'}
Market Cap: {market_cap_str or 'N/A'} | Beta: {p.beta or 'N/A'}"""

    def _format_news(self, data: StockData) -> str:
        """Format news articles for prompt."""
        if not data.news:
            return "No recent news"

        lines = []
        for article in data.news[:10]:
            days_ago = (data.fetched_at - article.published_at).days
            time_str = f"{days_ago} days ago" if days_ago > 0 else "today"
            lines.append(f"- {article.title} ({time_str}, {article.source})")

        return "\n".join(lines)

    def _format_targets(self, data: StockData) -> str:
        """Format price targets for prompt."""
        if not data.price_targets:
            return "No price targets available"

        t = data.price_targets
        parts = []
        if t.consensus:
            parts.append(f"Consensus: ${t.consensus:.2f}")
        if t.high:
            parts.append(f"High: ${t.high:.2f}")
        if t.low:
            parts.append(f"Low: ${t.low:.2f}")
        if t.median:
            parts.append(f"Median: ${t.median:.2f}")

        if parts and data.price and t.consensus:
            upside = ((t.consensus - data.price.current_price) / data.price.current_price) * 100
            parts.append(f"Upside to Consensus: {upside:+.1f}%")

        return " | ".join(parts) if parts else "No targets available"

    def _format_recommendations(self, data: StockData) -> str:
        """Format analyst recommendations for prompt."""
        if not data.recommendations:
            return "No recommendations available"

        r = data.recommendations
        return f"Strong Buy: {r.strong_buy} | Buy: {r.buy} | Hold: {r.hold} | Sell: {r.sell} | Strong Sell: {r.strong_sell}"

    def _format_earnings(self, data: StockData) -> str:
        """Format earnings data for prompt."""
        parts = []

        if data.upcoming_earnings and data.upcoming_earnings.earnings_date:
            e = data.upcoming_earnings
            parts.append(f"Next Report: {e.earnings_date.strftime('%B %d, %Y')}")
            if e.eps_estimate:
                parts.append(f"EPS Estimate: ${e.eps_estimate:.2f}")
            if e.revenue_estimate:
                rev_str = f"${e.revenue_estimate/1e9:.1f}B" if e.revenue_estimate >= 1e9 else f"${e.revenue_estimate/1e6:.1f}M"
                parts.append(f"Revenue Estimate: {rev_str}")

        return "\n".join(parts) if parts else "No upcoming earnings data"

    def _format_earnings_history(self, data: StockData) -> str:
        """Format earnings history for prompt."""
        if not data.earnings_history:
            return "No earnings history available"

        results = []
        for e in data.earnings_history:
            result = "Beat" if e.beat else "Miss"
            results.append(f"{e.quarter_date.strftime('%Y-%m-%d')}: {result} (Actual: ${e.actual_eps:.2f}, Est: ${e.estimated_eps:.2f})")

        return "\n".join(results)

    def _format_options(self, data: StockData) -> str:
        """Format options data for prompt."""
        if not data.options:
            return ""

        o = data.options
        lines = [f"\nOPTIONS DATA (Expiration: {o.expiration}):"]

        # Show ATM options if price is available
        if data.price:
            current_price = data.price.current_price

            # Find nearest ATM calls
            atm_calls = sorted(o.calls, key=lambda x: abs(x.strike - current_price))[:3]
            if atm_calls:
                lines.append("\nNear-the-money Calls:")
                for c in atm_calls:
                    iv_str = f", IV: {c.implied_volatility:.1%}" if c.implied_volatility else ""
                    lines.append(f"  ${c.strike} strike: Bid ${c.bid:.2f} / Ask ${c.ask:.2f}, Volume: {c.volume}, OI: {c.open_interest}{iv_str}")

            # Find nearest ATM puts
            atm_puts = sorted(o.puts, key=lambda x: abs(x.strike - current_price))[:3]
            if atm_puts:
                lines.append("\nNear-the-money Puts:")
                for p in atm_puts:
                    iv_str = f", IV: {p.implied_volatility:.1%}" if p.implied_volatility else ""
                    lines.append(f"  ${p.strike} strike: Bid ${p.bid:.2f} / Ask ${p.ask:.2f}, Volume: {p.volume}, OI: {p.open_interest}{iv_str}")

        return "\n".join(lines)

    def analyze(self, data: StockData) -> str:
        """Analyze stock data and return recommendation."""
        user_prompt = f"""Analyze {data.ticker} based on the following data:

CURRENT PRICE:
{self._format_price_data(data)}

COMPANY:
{self._format_profile(data)}

RECENT NEWS (last 7 days):
{self._format_news(data)}

ANALYST PRICE TARGETS:
{self._format_targets(data)}

ANALYST RECOMMENDATIONS:
{self._format_recommendations(data)}

UPCOMING EARNINGS:
{self._format_earnings(data)}

EARNINGS HISTORY (last 4 quarters):
{self._format_earnings_history(data)}
{self._format_options(data)}

Provide your analysis and recommendation."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )

            return response.content[0].text
        except anthropic.APIError as e:
            return f"[Error] Failed to get analysis from Claude: {e}"
