# Stockerino — Daily Pre-Market Scanner

An automated daily scanner that analyzes your portfolio and watchlist, identifies the top trade setups for the day, and emails you a PDF report every weekday morning at 6 AM ET.

Powered by Claude AI, Finnhub, Financial Modeling Prep, and yfinance.

---

## What It Does

Every weekday before market open, the scanner:

1. Pulls market context (SPY, QQQ, VIX, sector ETFs)
2. Scans for pre-market movers across your full ticker universe
3. Checks macro calendar for upcoming Fed, CPI, and jobs data
4. Flags upcoming earnings with historical beat rates
5. Surfaces news catalysts from the last 24 hours
6. Detects momentum signals, technical setups, and unusual options flow
7. Sends everything to Claude, which identifies the **top 3 actionable setups**
8. Generates a PDF report and emails it to you

Each setup is classified as either a **day trade** (intraday, catalyst-driven) or a **swing** (multi-day/week, technical or fundamental). Stocks you hold are tagged **★ PORTFOLIO** with position management guidance (add/hold/trim/hedge).

---

## Setup

### 1. Fork and configure secrets

In your GitHub repo: **Settings → Secrets and variables → Actions → New repository secret**

| Secret | Where to get it |
|--------|----------------|
| `FINNHUB_API_KEY` | [finnhub.io](https://finnhub.io) — free tier |
| `FMP_API_KEY` | [financialmodelingprep.com](https://financialmodelingprep.com) — free tier |
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) — ~$1-2/month usage |
| `RESEND_API_KEY` | [resend.com](https://resend.com) — free tier |
| `ALERT_EMAIL` | Your email address |

### 2. Update your watchlist and portfolio

Edit `scanner/data/watchlist.json`:

```json
{
  "portfolio": ["NVDA", "TSLA", "PLTR"],
  "ai_semiconductors": ["NVDA", "AMD", "AVGO"],
  "your_sector": ["TICK1", "TICK2"]
}
```

- **`portfolio`** — stocks you currently hold. These are scanned with priority, tagged throughout the report, and receive position management guidance.
- **Sector keys** — thematic groupings for your watchlist. Add or rename sectors freely.
- Tickers can appear in both `portfolio` and a sector — deduplication is handled automatically.

### 3. That's it

The GitHub Actions workflow (`.github/workflows/daily-scan.yml`) runs automatically at **6 AM ET on weekdays**. No server needed.

---

## Running Locally

```bash
pip install -r requirements.txt

# Dry run — generates PDF but skips email
python -m scanner.main --dry-run

# Full run with verbose output
python -m scanner.main --verbose

# Manual trigger in GitHub: Actions → Daily Market Scan → Run workflow
```

You'll need a `.env` file with your API keys for local runs:

```bash
FINNHUB_API_KEY=your_key
FMP_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
RESEND_API_KEY=your_key
ALERT_EMAIL=your@email.com
```

---

## PDF Report Structure

1. **Top 3 Opportunities** — ranked by conviction (1–10)
   - Setup type: Day Trade or Swing
   - Time horizon (intraday / 1-2 days / 1-3 weeks)
   - ★ PORTFOLIO badge if you hold the stock
   - Catalyst, thesis, specific trade setup, key risk
2. **Watchlist** — stocks worth monitoring but not immediately actionable
3. **No Action** — flagged stocks that didn't make the cut and why
4. **Sector Summary** — outlook and overview for each tracked sector

---

## Project Structure

```
stockerino/
├── scanner/
│   ├── main.py                  # Orchestrator — runs all scanners, calls Claude, generates PDF
│   ├── analyzer.py              # Claude integration — formats data, parses response
│   ├── models.py                # Pydantic data models
│   ├── config.py                # Environment variable configuration
│   ├── scanners/
│   │   ├── market_context.py    # SPY, QQQ, VIX, sector ETFs
│   │   ├── premarket.py         # Pre-market movers (±3%+)
│   │   ├── macro_calendar.py    # Fed, CPI, jobs, sector-moving earnings
│   │   ├── earnings.py          # Upcoming earnings with beat rate history
│   │   ├── news.py              # News catalysts with sentiment scoring
│   │   ├── momentum.py          # Price momentum and 52-week range signals
│   │   ├── technicals.py        # RSI, 50/200 MA, golden/death cross
│   │   └── options.py           # Unusual options flow (Vol/OI ratio)
│   ├── data/
│   │   ├── watchlist.json       # Your tickers — edit this
│   │   └── prompts.py           # Claude system and user prompts — edit to tune behavior
│   └── output/
│       ├── pdf_generator.py     # ReportLab PDF generation
│       └── email_sender.py      # Resend email with PDF attachment
├── .github/workflows/
│   └── daily-scan.yml           # Cron job — 6 AM ET weekdays
├── spec/
│   └── market-scanner-prd.md    # Product requirements document
└── requirements.txt
```

---

## Tuning Claude's Behavior

Edit `scanner/data/prompts.py` to change how Claude analyzes and ranks setups. The system prompt controls:
- Day trade vs swing classification criteria
- How portfolio holdings are treated
- Risk weighting (VIX thresholds, MA filters, etc.)
- Output format and what fields are required

---

## Data Sources

| Source | Used For | Free Tier |
|--------|----------|-----------|
| Finnhub | Quotes, news, analyst recs, earnings | 60 calls/min |
| Financial Modeling Prep | Company profiles, price targets | 250 calls/day |
| yfinance | Price history, technicals, options chains | Unlimited |
| Anthropic (Claude) | AI analysis and ranking | Pay per use |
| Resend | Email delivery | 100 emails/day |
