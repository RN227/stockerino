#!/usr/bin/env python3
"""
Market Scanner - Daily Pre-Market Analysis
Runs via GitHub Actions cron at 6 AM ET on weekdays

Usage:
    python -m scanner.main              # Full run (PDF + email)
    python -m scanner.main --dry-run    # Local test (no email)
    python -m scanner.main --verbose    # Show detailed output
"""

import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich import box

from .config import validate_config, DATA_DIR, LOGS_DIR, SEND_EMAIL
from .scanners import EarningsScanner, NewsScanner, MomentumScanner, OptionsScanner, MarketContextScanner, TechnicalsScanner
from .analyzer import ScannerAnalyzer
from .output.pdf_generator import generate_pdf_report
from .output.email_sender import send_scan_email

console = Console()


def load_watchlist() -> dict:
    """Load watchlist from JSON file."""
    watchlist_path = DATA_DIR / "watchlist.json"
    with open(watchlist_path) as f:
        return json.load(f)


def flatten_watchlist(watchlist: dict) -> list:
    """Flatten sector-grouped watchlist into single list."""
    return [ticker for tickers in watchlist.values() for ticker in tickers]


def run_scan(dry_run: bool = False, verbose: bool = False):
    """Execute full market scan pipeline."""
    
    start_time = datetime.now()
    console.print(f"\n[bold blue]Market Scanner[/bold blue] - {start_time.strftime('%Y-%m-%d %H:%M')}")
    console.print("=" * 50)
    
    # Validate configuration
    missing = validate_config()
    if missing:
        console.print(f"[bold red]Error:[/bold red] Missing API keys: {', '.join(missing)}")
        sys.exit(1)
    
    # Load watchlist
    watchlist = load_watchlist()
    all_tickers = flatten_watchlist(watchlist)
    console.print(f"[dim]Watchlist loaded: {len(all_tickers)} tickers across {len(watchlist)} sectors[/dim]")
    
    # Run scanners
    console.print("\n[bold cyan]Running Scanners...[/bold cyan]")
    
    console.print("[dim]  → Market context...[/dim]")
    market_scanner = MarketContextScanner()
    market_context = market_scanner.scan()
    if market_context:
        sentiment_emoji = "🟢" if market_context.market_sentiment == "risk_on" else "🔴" if market_context.market_sentiment == "risk_off" else "🟡"
        console.print(f"[dim]     {sentiment_emoji} SPY {market_context.spy_change_pct:+.1f}% | QQQ {market_context.qqq_change_pct:+.1f}% | VIX {market_context.vix_level}[/dim]")
    
    console.print("[dim]  → Earnings scanner...[/dim]")
    earnings_scanner = EarningsScanner()
    earnings_results = earnings_scanner.scan(all_tickers)
    console.print(f"[dim]     Found {len(earnings_results)} upcoming earnings[/dim]")
    
    console.print("[dim]  → News scanner...[/dim]")
    news_scanner = NewsScanner()
    news_results = news_scanner.scan(all_tickers)
    console.print(f"[dim]     Found {len(news_results)} news catalysts[/dim]")
    
    console.print("[dim]  → Momentum scanner...[/dim]")
    momentum_scanner = MomentumScanner()
    momentum_results = momentum_scanner.scan(all_tickers)
    console.print(f"[dim]     Found {len(momentum_results)} momentum signals[/dim]")
    
    console.print("[dim]  → Technicals scanner...[/dim]")
    technicals_scanner = TechnicalsScanner()
    technicals_results = technicals_scanner.scan(all_tickers)
    console.print(f"[dim]     Found {len(technicals_results)} technical signals[/dim]")
    
    console.print("[dim]  → Options flow scanner...[/dim]")
    options_scanner = OptionsScanner()
    options_results = options_scanner.scan(all_tickers)
    call_put_ratios = options_scanner.get_call_put_ratio(all_tickers)
    console.print(f"[dim]     Found {len(options_results)} unusual options signals[/dim]")
    
    # Verbose output
    if verbose:
        if market_context:
            console.print("\n[yellow]Market Context:[/yellow]")
            console.print(f"  SPY: ${market_context.spy_price} ({market_context.spy_change_pct:+.1f}%)")
            console.print(f"  QQQ: ${market_context.qqq_price} ({market_context.qqq_change_pct:+.1f}%)")
            console.print(f"  VIX: {market_context.vix_level} ({market_context.vix_change_pct:+.1f}%)")
            console.print(f"  Sentiment: {market_context.market_sentiment.upper()}")
            if market_context.sector_performance:
                console.print("  Sectors: " + " | ".join([f"{k} {v:+.1f}%" for k, v in market_context.sector_performance.items()]))
        
        if earnings_results:
            console.print("\n[yellow]Earnings:[/yellow]")
            for e in earnings_results:
                console.print(f"  {e.symbol}: {e.report_date}")
        
        if news_results:
            console.print("\n[yellow]News Catalysts:[/yellow]")
            for n in news_results[:5]:
                icon = "+" if n.sentiment == "bullish" else "-"
                console.print(f"  [{icon}] {n.symbol}: {n.title[:60]}...")
        
        if momentum_results:
            console.print("\n[yellow]Momentum:[/yellow]")
            for m in momentum_results:
                console.print(f"  {m.symbol}: {m.change_pct:+.1f}% - {', '.join(m.signals)}")
        
        if technicals_results:
            console.print("\n[yellow]Technicals:[/yellow]")
            for t in technicals_results:
                console.print(f"  {t.symbol}: RSI {t.rsi_14} | {', '.join(t.signals)}")
        
        if options_results:
            console.print("\n[yellow]Options Flow:[/yellow]")
            for o in options_results[:10]:
                emoji = "📈" if o.option_type == "call" else "📉"
                console.print(f"  {emoji} {o.symbol}: {o.expiry} ${o.strike} {o.option_type.upper()} - Vol/OI: {o.volume_oi_ratio}x ({o.signal_strength})")
    
    # Analyze with Claude
    console.print("\n[bold cyan]Analyzing with Claude...[/bold cyan]")
    analyzer = ScannerAnalyzer()
    analysis = analyzer.analyze(
        earnings=earnings_results,
        news=news_results,
        momentum=momentum_results,
        technicals=technicals_results,
        options=options_results,
        call_put_ratios=call_put_ratios,
        market_context=market_context,
        watchlist=watchlist
    )
    console.print(f"[dim]  Found {len(analysis.top_opportunities)} top opportunities[/dim]")
    
    # Generate PDF
    LOGS_DIR.mkdir(exist_ok=True)
    pdf_filename = f"market-scan-{datetime.now().strftime('%Y-%m-%d')}.pdf"
    pdf_path = LOGS_DIR / pdf_filename
    generate_pdf_report(analysis, str(pdf_path))
    console.print(f"\n[green]✓[/green] PDF generated: {pdf_path}")
    
    # Send email with PDF attachment
    if not dry_run and SEND_EMAIL:
        console.print("[dim]  → Sending email with PDF attachment...[/dim]")
        send_scan_email(analysis, str(pdf_path))
        console.print("[green]✓[/green] Email sent")
    elif dry_run:
        console.print("[yellow]⊘[/yellow] Dry run - skipping email")
    
    # Summary
    duration = (datetime.now() - start_time).total_seconds()
    console.print(f"\n[bold]Scan completed in {duration:.1f}s[/bold]")
    
    # Show top opportunities
    if analysis.top_opportunities:
        console.print()
        console.print(Panel(
            "\n".join([
                f"[bold]#{o.rank} {o.ticker}[/bold] - {o.setup_type} (Conviction: {o.conviction}/10)"
                f"\n   {o.catalyst}"
                for o in analysis.top_opportunities
            ]),
            title="[bold white]TOP OPPORTUNITIES[/bold white]",
            box=box.ROUNDED,
            border_style="green"
        ))
    
    return analysis


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Market Scanner - Daily Pre-Market Analysis"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate PDF but skip email"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed scanner output"
    )
    
    args = parser.parse_args()
    
    try:
        run_scan(dry_run=args.dry_run, verbose=args.verbose)
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        raise


if __name__ == "__main__":
    main()
