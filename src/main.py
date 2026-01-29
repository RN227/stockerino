"""Main CLI entry point for stocker."""

import sys
from datetime import datetime

import click
from rich.console import Console

from .config import config
from .fetchers import FinnhubClient, FMPClient, TradierClient
from .analyzer import ClaudeAnalyzer
from .formatters import TerminalFormatter
from .models import StockData


console = Console()


def fetch_stock_data(ticker: str, include_options: bool = True) -> StockData:
    """Fetch all stock data from APIs."""
    finnhub = FinnhubClient()
    fmp = FMPClient()
    tradier = TradierClient()

    console.print(f"[dim]Fetching data for {ticker}...[/dim]")

    # Initialize stock data
    data = StockData(ticker=ticker.upper(), fetched_at=datetime.utcnow())

    # Fetch from Finnhub
    console.print("[dim]  → Fetching price quote...[/dim]")
    data.price = finnhub.get_quote(ticker)

    console.print("[dim]  → Fetching news...[/dim]")
    data.news = finnhub.get_company_news(ticker, days=config.NEWS_DAYS)

    console.print("[dim]  → Fetching analyst recommendations...[/dim]")
    data.recommendations = finnhub.get_recommendations(ticker)

    # Fetch from FMP
    console.print("[dim]  → Fetching company profile...[/dim]")
    data.profile = fmp.get_profile(ticker)

    console.print("[dim]  → Fetching price targets...[/dim]")
    data.price_targets = fmp.get_price_target_consensus(ticker)

    # If FMP price targets fail, try Finnhub
    if not data.price_targets:
        data.price_targets = finnhub.get_price_target(ticker)

    console.print("[dim]  → Fetching earnings data...[/dim]")
    data.upcoming_earnings = finnhub.get_upcoming_earnings(ticker)
    data.earnings_history = finnhub.get_earnings_history(ticker)

    # Fetch options if configured and requested
    if include_options and config.has_tradier():
        console.print("[dim]  → Fetching options chain...[/dim]")
        data.options = tradier.get_options_chain(ticker)

    return data


@click.command()
@click.argument("tickers", nargs=-1, required=True)
@click.option("--no-options", is_flag=True, help="Skip options data")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON data")
@click.option("--brief", is_flag=True, help="Show brief summary only")
def main(tickers: tuple[str, ...], no_options: bool, output_json: bool, brief: bool):
    """
    Analyze stocks and get trading recommendations.

    Usage: stocker AAPL [MSFT] [GOOGL] ...
    """
    # Validate configuration
    missing = config.validate()
    if missing:
        console.print(f"[bold red]Error:[/bold red] Missing required API keys: {', '.join(missing)}")
        console.print("\nPlease set the following environment variables:")
        for key in missing:
            console.print(f"  export {key}=your_key_here")
        console.print("\nOr create a .env file based on .env.example")
        sys.exit(1)

    formatter = TerminalFormatter()
    analyzer = ClaudeAnalyzer()

    for ticker in tickers:
        try:
            # Fetch data
            data = fetch_stock_data(ticker, include_options=not no_options)

            # Check if we got valid data
            if not data.price:
                formatter.print_error(f"Could not fetch data for '{ticker}'. Is it a valid ticker?")
                continue

            if output_json:
                # Output raw JSON
                import json
                console.print(json.dumps(data.to_analysis_dict(), indent=2, default=str))
            else:
                # Get Claude analysis
                console.print("[dim]  → Analyzing with Claude...[/dim]")
                analysis = analyzer.analyze(data)

                # Display formatted output
                if brief:
                    formatter.print_header(data.ticker)
                    formatter.print_price(data)
                    formatter.print_analysis(analysis)
                else:
                    formatter.display(data, analysis)

        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted[/yellow]")
            sys.exit(0)
        except Exception as e:
            formatter.print_error(f"Failed to analyze {ticker}: {e}")
            continue


if __name__ == "__main__":
    main()
