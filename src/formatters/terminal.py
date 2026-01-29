"""Terminal output formatter using Rich."""

from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from ..models.stock_data import StockData


class TerminalFormatter:
    """Formats stock data for terminal output."""

    def __init__(self):
        self.console = Console()

    def _format_market_cap(self, market_cap: Optional[float]) -> str:
        """Format market cap in human-readable format."""
        if not market_cap:
            return "N/A"
        if market_cap >= 1e12:
            return f"${market_cap/1e12:.2f}T"
        elif market_cap >= 1e9:
            return f"${market_cap/1e9:.2f}B"
        else:
            return f"${market_cap/1e6:.2f}M"

    def _get_change_color(self, change: float) -> str:
        """Get color for price change."""
        if change > 0:
            return "green"
        elif change < 0:
            return "red"
        return "yellow"

    def print_header(self, ticker: str):
        """Print the main header."""
        self.console.print()
        self.console.print(
            Panel(
                f"[bold white]STOCK ANALYSIS: {ticker}[/bold white]",
                box=box.DOUBLE,
                style="bold blue",
            )
        )

    def print_price(self, data: StockData):
        """Print current price section."""
        if not data.price:
            self.console.print("[yellow]Price data unavailable[/yellow]")
            return

        p = data.price
        color = self._get_change_color(p.change)

        self.console.print("\n[bold cyan]CURRENT PRICE[/bold cyan]")
        self.console.print("-" * 40)

        price_line = Text()
        price_line.append(f"Price: ${p.current_price:.2f}  |  ")
        price_line.append(f"Change: ${p.change:+.2f} ({p.change_percent:+.2f}%)", style=color)
        self.console.print(price_line)

        self.console.print(
            f"Day Range: ${p.low_today:.2f} - ${p.high_today:.2f}  |  Prev Close: ${p.previous_close:.2f}"
        )

    def print_profile(self, data: StockData):
        """Print company profile section."""
        if not data.profile:
            return

        p = data.profile

        self.console.print("\n[bold cyan]COMPANY SNAPSHOT[/bold cyan]")
        self.console.print("-" * 40)
        self.console.print(f"{p.name} | {p.sector or 'N/A'} | {p.industry or 'N/A'}")
        self.console.print(
            f"Market Cap: {self._format_market_cap(p.market_cap)} | Beta: {p.beta or 'N/A'}"
        )

    def print_news(self, data: StockData):
        """Print news highlights section."""
        if not data.news:
            self.console.print("\n[yellow]No recent news[/yellow]")
            return

        self.console.print("\n[bold cyan]NEWS HIGHLIGHTS[/bold cyan]")
        self.console.print("-" * 40)

        for article in data.news[:5]:
            days_ago = (data.fetched_at - article.published_at).days
            time_str = f"{days_ago} days ago" if days_ago > 0 else "today"

            # Use neutral indicator since we don't have sentiment
            indicator = "[~]"
            color = "yellow"

            self.console.print(f"[{color}]{indicator}[/{color}] {article.title} ({time_str})")
            self.console.print(f"    [dim]Source: {article.source}[/dim]")
            if article.url:
                self.console.print(f"    [dim blue]{article.url}[/dim blue]")

    def print_targets(self, data: StockData):
        """Print analyst price targets section."""
        if not data.price_targets:
            return

        t = data.price_targets

        self.console.print("\n[bold cyan]ANALYST TARGETS[/bold cyan]")
        self.console.print("-" * 40)

        parts = []
        if t.consensus:
            parts.append(f"Consensus: ${t.consensus:.2f}")
        if t.high:
            parts.append(f"High: ${t.high:.2f}")
        if t.low:
            parts.append(f"Low: ${t.low:.2f}")

        self.console.print(" | ".join(parts))

        if data.price and t.consensus:
            upside = ((t.consensus - data.price.current_price) / data.price.current_price) * 100
            color = "green" if upside > 0 else "red"
            self.console.print(f"[{color}]Upside to Consensus: {upside:+.1f}%[/{color}]")

    def print_recommendations(self, data: StockData):
        """Print analyst recommendations section."""
        if not data.recommendations:
            return

        r = data.recommendations

        self.console.print("\n[bold cyan]RECOMMENDATIONS[/bold cyan]")
        self.console.print("-" * 40)

        rec_text = Text()
        rec_text.append(f"Strong Buy: {r.strong_buy}", style="bold green")
        rec_text.append(" | ")
        rec_text.append(f"Buy: {r.buy}", style="green")
        rec_text.append(" | ")
        rec_text.append(f"Hold: {r.hold}", style="yellow")
        rec_text.append(" | ")
        rec_text.append(f"Sell: {r.sell}", style="red")
        rec_text.append(" | ")
        rec_text.append(f"Strong Sell: {r.strong_sell}", style="bold red")

        self.console.print(rec_text)

    def print_earnings(self, data: StockData):
        """Print earnings section."""
        self.console.print("\n[bold cyan]EARNINGS[/bold cyan]")
        self.console.print("-" * 40)

        if data.upcoming_earnings and data.upcoming_earnings.earnings_date:
            e = data.upcoming_earnings
            self.console.print(f"Next Report: {e.earnings_date.strftime('%B %d, %Y')}")

            if e.eps_estimate:
                self.console.print(f"EPS Estimate: ${e.eps_estimate:.2f}", end="")
            if e.revenue_estimate:
                rev_str = (
                    f"${e.revenue_estimate/1e9:.1f}B"
                    if e.revenue_estimate >= 1e9
                    else f"${e.revenue_estimate/1e6:.1f}M"
                )
                self.console.print(f" | Revenue Estimate: {rev_str}")
            else:
                self.console.print()
        else:
            self.console.print("[dim]No upcoming earnings data[/dim]")

        if data.earnings_history:
            results = []
            for e in data.earnings_history:
                if e.beat:
                    results.append("[green]Beat[/green]")
                else:
                    results.append("[red]Miss[/red]")

            self.console.print(f"Last {len(results)} Quarters: " + " | ".join(results))

    def print_options(self, data: StockData):
        """Print options data section."""
        if not data.options:
            return

        o = data.options

        self.console.print(f"\n[bold cyan]OPTIONS (Exp: {o.expiration})[/bold cyan]")
        self.console.print("-" * 40)

        if data.price and (o.calls or o.puts):
            current_price = data.price.current_price

            # Show ATM calls
            if o.calls:
                atm_calls = sorted(o.calls, key=lambda x: abs(x.strike - current_price))[:3]
                self.console.print("[dim]Near ATM Calls:[/dim]")
                for c in atm_calls:
                    iv_str = f" IV:{c.implied_volatility:.0%}" if c.implied_volatility else ""
                    self.console.print(
                        f"  ${c.strike:.0f}C: ${c.bid:.2f}/${c.ask:.2f} Vol:{c.volume} OI:{c.open_interest}{iv_str}"
                    )

    def print_analysis(self, analysis: str):
        """Print Claude's analysis."""
        self.console.print()
        self.console.print(
            Panel(
                analysis,
                title="[bold white]RECOMMENDATION[/bold white]",
                box=box.DOUBLE,
                border_style="green",
                padding=(1, 2),
            )
        )

    def print_error(self, message: str):
        """Print an error message."""
        self.console.print(f"\n[bold red]Error:[/bold red] {message}")

    def print_warning(self, message: str):
        """Print a warning message."""
        self.console.print(f"[yellow]Warning:[/yellow] {message}")

    def print_links(self, data: StockData):
        """Print useful reference links."""
        ticker = data.ticker

        self.console.print("\n[bold cyan]QUICK LINKS[/bold cyan]")
        self.console.print("-" * 40)
        self.console.print(f"[dim]Yahoo Finance:[/dim] https://finance.yahoo.com/quote/{ticker}")
        self.console.print(f"[dim]TradingView:[/dim]  https://www.tradingview.com/symbols/{ticker}")
        self.console.print(f"[dim]Finviz:[/dim]       https://finviz.com/quote.ashx?t={ticker}")
        self.console.print(f"[dim]SEC Filings:[/dim]  https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}&type=&dateb=&owner=include&count=40")

    def display(self, data: StockData, analysis: str):
        """Display complete stock analysis."""
        self.print_header(data.ticker)
        self.print_price(data)
        self.print_profile(data)
        self.print_news(data)
        self.print_targets(data)
        self.print_recommendations(data)
        self.print_earnings(data)
        self.print_options(data)
        self.print_analysis(analysis)
        self.print_links(data)
        self.console.print()
