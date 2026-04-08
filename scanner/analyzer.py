"""Claude Analyzer for Market Scanner."""

import json
import anthropic
from datetime import datetime
from typing import List, Optional

from .config import ANTHROPIC_API_KEY
from .models import EarningsResult, NewsResult, MomentumResult, ScanAnalysis, Opportunity, WatchlistItem, SectorSummary, SectorNews
from .scanners.options import OptionsSignal
from .scanners.market_context import MarketContext
from .scanners.technicals import TechnicalSignal
from .scanners.premarket import PreMarketMover
from .data.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE


class ScannerAnalyzer:
    """Analyzes scan results using Claude."""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.model = "claude-sonnet-4-20250514"
        self._portfolio: set = set()

    def _tag(self, symbol: str) -> str:
        """Return symbol with [PORTFOLIO] prefix if held."""
        return f"[PORTFOLIO] {symbol}" if symbol in self._portfolio else symbol

    def _format_earnings(self, earnings: List[EarningsResult]) -> str:
        """Format earnings data for prompt."""
        if not earnings:
            return "No earnings in the next 5 trading days for watchlist stocks."

        lines = []
        for e in earnings:
            beat_str = f"{e.beat_rate*100:.0f}% beat rate" if e.beat_rate else "No history"
            surprise_str = f"{e.avg_surprise_pct:+.1f}% avg surprise" if e.avg_surprise_pct else ""
            time_str = f" ({e.report_time})" if e.report_time else ""

            lines.append(f"- {self._tag(e.symbol)}: {e.report_date}{time_str}")
            lines.append(f"  EPS Est: ${e.eps_estimate:.2f}" if e.eps_estimate else "  EPS Est: N/A")
            lines.append(f"  History: {beat_str} {surprise_str}")

        return "\n".join(lines)

    def _format_news(self, news: List[NewsResult]) -> str:
        """Format news data for prompt."""
        if not news:
            return "No significant news catalysts in the last 48 hours."

        lines = []
        for n in news[:15]:  # Limit to top 15
            sentiment_icon = "+" if n.sentiment == "bullish" else "-" if n.sentiment == "bearish" else "~"
            keywords_str = ", ".join(n.keywords_matched[:3])
            lines.append(f"[{sentiment_icon}] {self._tag(n.symbol)}: {n.title}")
            lines.append(f"    Source: {n.source} | Keywords: {keywords_str}")
            lines.append(f"    URL: {n.url}")

        return "\n".join(lines)

    def _format_momentum(self, momentum: List[MomentumResult]) -> str:
        """Format momentum data for prompt."""
        if not momentum:
            return "No unusual momentum signals detected."

        lines = []
        for m in momentum:
            signals_str = " | ".join(m.signals)
            lines.append(f"- {self._tag(m.symbol)}: ${m.price:.2f} ({m.change_pct:+.1f}%)")
            lines.append(f"  Signals: {signals_str}")

        return "\n".join(lines)

    def _format_options(self, options: List[OptionsSignal], call_put_ratios: dict) -> str:
        """Format options flow data for prompt."""
        if not options and not call_put_ratios:
            return "No unusual options activity detected."

        lines = []

        # Group by symbol
        by_symbol = {}
        for o in options:
            if o.symbol not in by_symbol:
                by_symbol[o.symbol] = []
            by_symbol[o.symbol].append(o)

        # Format unusual activity
        if by_symbol:
            lines.append("UNUSUAL OPTIONS ACTIVITY:")
            for symbol, signals in by_symbol.items():
                top_signals = sorted(signals, key=lambda x: x.volume_oi_ratio, reverse=True)[:3]
                for s in top_signals:
                    direction = "CALL" if s.option_type == "call" else "PUT"
                    strength = "🔥" if s.signal_strength == "strong" else ""
                    lines.append(f"  {strength}{self._tag(symbol)}: {s.expiry} ${s.strike} {direction} - Vol: {s.volume:,} / OI: {s.open_interest:,} ({s.volume_oi_ratio}x)")

        # Format call/put ratios
        if call_put_ratios:
            lines.append("\nCALL/PUT VOLUME RATIOS (>1.5 = bullish, <0.7 = bearish):")
            sorted_ratios = sorted(call_put_ratios.items(), key=lambda x: x[1], reverse=True)
            for symbol, ratio in sorted_ratios:
                if ratio > 1.5:
                    sentiment = "📈 Bullish"
                elif ratio < 0.7:
                    sentiment = "📉 Bearish"
                else:
                    sentiment = "➡️ Neutral"
                lines.append(f"  {self._tag(symbol)}: {ratio:.2f} {sentiment}")

        return "\n".join(lines)

    def _format_market_context(self, ctx: Optional[MarketContext]) -> str:
        """Format market context for prompt."""
        if not ctx:
            return "Market context unavailable."

        lines = [
            "MARKET OVERVIEW:",
            f"  SPY (S&P 500): ${ctx.spy_price} ({ctx.spy_change_pct:+.1f}%)",
            f"  QQQ (Nasdaq): ${ctx.qqq_price} ({ctx.qqq_change_pct:+.1f}%)",
            f"  VIX (Fear Index): {ctx.vix_level} ({ctx.vix_change_pct:+.1f}%)",
            f"  Overall Sentiment: {ctx.market_sentiment.upper()}",
        ]

        if ctx.vix_level > 25:
            lines.append("  ⚠️ HIGH VIX - Market is fearful, consider reducing position sizes")
        elif ctx.vix_level < 15:
            lines.append("  ✅ LOW VIX - Market is calm, favorable for risk-on trades")

        if ctx.sector_performance:
            lines.append("\nSECTOR ETF PERFORMANCE:")
            for etf, change in ctx.sector_performance.items():
                icon = "▲" if change > 0 else "▼" if change < 0 else "─"
                lines.append(f"  {etf}: {change:+.1f}% {icon}")

        return "\n".join(lines)

    def _format_technicals(self, technicals: List[TechnicalSignal]) -> str:
        """Format technical signals for prompt."""
        if not technicals:
            return "No notable technical signals."

        lines = ["TECHNICAL SIGNALS:"]

        for t in technicals:
            rsi_str = f"RSI: {t.rsi_14}" if t.rsi_14 else "RSI: N/A"
            ma_status = []
            if t.above_50ma is not None:
                ma_status.append("Above 50MA" if t.above_50ma else "Below 50MA")
            if t.above_200ma is not None:
                ma_status.append("Above 200MA" if t.above_200ma else "Below 200MA")
            ma_str = ", ".join(ma_status) if ma_status else ""

            short_str = ""
            if t.short_percent_float and t.short_percent_float > 5:
                short_str = f" | Short: {t.short_percent_float:.1f}%"

            lines.append(f"  {self._tag(t.symbol)}: {rsi_str} | {ma_str}{short_str}")
            if t.signals:
                lines.append(f"    → {', '.join(t.signals)}")

        return "\n".join(lines)

    def _format_premarket(self, movers: List[PreMarketMover]) -> str:
        """Format pre-market movers for prompt."""
        if not movers:
            return "No significant pre-market moves (±3%)."

        lines = ["PRE-MARKET MOVERS (±3%+):"]

        for m in movers[:10]:
            direction = "🚀" if m.change_pct > 0 else "📉"
            watchlist_tag = "" if m.on_watchlist else " (NOT ON WATCHLIST - consider adding)"
            lines.append(f"  {direction} {self._tag(m.symbol)}: {m.change_pct:+.1f}% ${m.price}{watchlist_tag}")

        return "\n".join(lines)

    def _format_portfolio_context(self) -> str:
        """Build a dedicated portfolio section for the prompt."""
        if not self._portfolio:
            return ""
        tickers = ", ".join(sorted(self._portfolio))
        return f"### PORTFOLIO HOLDINGS\nThe user currently holds the following positions: {tickers}\nThese are tagged [PORTFOLIO] throughout the data above. Always include position management guidance (add/hold/trim/hedge) for these in trade setups.\n"

    def analyze(
        self,
        earnings: List[EarningsResult],
        news: List[NewsResult],
        momentum: List[MomentumResult],
        technicals: List[TechnicalSignal] = None,
        options: List[OptionsSignal] = None,
        call_put_ratios: dict = None,
        market_context: MarketContext = None,
        premarket_movers: List[PreMarketMover] = None,
        macro_warnings: str = None,
        watchlist: dict = None,
        portfolio_tickers: List[str] = None
    ) -> ScanAnalysis:
        """Analyze scan results and return structured analysis."""

        date_str = datetime.now().strftime("%Y-%m-%d")
        technicals = technicals or []
        options = options or []
        call_put_ratios = call_put_ratios or {}
        premarket_movers = premarket_movers or []
        macro_warnings = macro_warnings or "No major macro events in next 5 days."
        watchlist = watchlist or {}
        self._portfolio = set(portfolio_tickers or [])

        # Build sector context (skip portfolio key)
        sector_lines = ["Sectors being tracked:"]
        for sector_name, tickers in watchlist.items():
            if sector_name == "portfolio":
                continue
            display_name = sector_name.replace("_", " ").title()
            tagged = [self._tag(t) for t in tickers]
            sector_lines.append(f"- {display_name}: {', '.join(tagged)}")
        sector_context = "\n".join(sector_lines)

        # Build user prompt from template
        user_prompt = USER_PROMPT_TEMPLATE.format(
            date=date_str,
            market_context=self._format_market_context(market_context),
            premarket=self._format_premarket(premarket_movers),
            macro_warnings=macro_warnings,
            earnings=self._format_earnings(earnings),
            news=self._format_news(news),
            momentum=self._format_momentum(momentum),
            technicals=self._format_technicals(technicals),
            options=self._format_options(options, call_put_ratios),
            sectors=sector_context,
            portfolio_context=self._format_portfolio_context()
        )

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}]
            )

            response_text = response.content[0].text

            # Parse JSON response — strip markdown code blocks if present
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]

            data = json.loads(response_text.strip())

            # Build Opportunity objects and flag portfolio holdings
            opportunities = []
            for opp in data.get("top_opportunities", []):
                opportunity = Opportunity(**opp)
                if opportunity.ticker in self._portfolio:
                    opportunity.is_portfolio = True
                opportunities.append(opportunity)

            watchlist_items = [
                WatchlistItem(**item) for item in data.get("watchlist", [])
            ]
            no_action_items = [
                WatchlistItem(**item) for item in data.get("no_action", [])
            ]

            # Parse sector summaries
            raw_sectors = data.get("sector_summary", {})
            sector_summaries = {}
            for sector, info in raw_sectors.items():
                if isinstance(info, dict):
                    news_items = [
                        SectorNews(**n) for n in info.get("news", [])
                    ]
                    sector_summaries[sector] = SectorSummary(
                        outlook=info.get("outlook", "Neutral"),
                        overview=info.get("overview", ""),
                        news=news_items
                    )
                else:
                    sector_summaries[sector] = SectorSummary(
                        outlook=info.split(" - ")[0] if " - " in str(info) else "Neutral",
                        overview=str(info),
                        news=[]
                    )

            return ScanAnalysis(
                scan_date=date_str,
                top_opportunities=opportunities,
                watchlist=watchlist_items,
                no_action=no_action_items,
                sector_summary=sector_summaries
            )

        except json.JSONDecodeError as e:
            print(f"[Warning] Failed to parse Claude response as JSON: {e}")
            return ScanAnalysis(scan_date=date_str)
        except anthropic.APIError as e:
            print(f"[Error] Claude API error: {e}")
            return ScanAnalysis(scan_date=date_str)
