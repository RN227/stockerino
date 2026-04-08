# Market Scanner PRD
## Daily Pre-Market Trading Opportunities Scanner

**Version:** 3.0
**Last Updated:** April 2026

---

## 1. Executive Summary

A Python-based scanner that runs daily at 6 AM ET via GitHub Actions, analyzes a personal portfolio and watchlist, identifies the top 3 trade setups for the day (classified as day trades or swings), generates a PDF report, and emails it directly.

**Stack:**
- **GitHub Actions** — Runs scanner on schedule, no server needed
- **Resend** — Sends email with PDF attachment
- **Claude (Sonnet)** — Analyzes and ranks trade setups (~$1-2/month)
- **Finnhub / FMP / yfinance** — Market data (all free tier)

**Daily Flow:**
```
6 AM ET (weekdays)
    ↓
GitHub Actions triggers scanner
    ↓
8 scanners run in sequence
    ↓
Claude identifies Top 3 setups (day trade or swing)
    ↓
PDF generated → emailed to ALERT_EMAIL
    ↓
📧 Your inbox, before market open
```

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│               GITHUB ACTIONS (Cron: 6 AM ET)                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌──────────┐  ┌──────────┐              │
│  │   Market    │  │Premarket │  │  Macro   │              │
│  │  Context   │  │  Movers  │  │ Calendar │              │
│  └──────┬──────┘  └────┬─────┘  └────┬─────┘              │
│         │              │              │                      │
│  ┌──────┴──────┐  ┌────┴─────┐  ┌────┴─────┐              │
│  │  Earnings  │  │   News   │  │ Momentum │              │
│  │  Scanner   │  │ Scanner  │  │ Scanner  │              │
│  └──────┬──────┘  └────┬─────┘  └────┬─────┘              │
│         │              │              │                      │
│  ┌──────┴──────┐  ┌────┴─────┐       │                     │
│  │ Technicals │  │ Options  │       │                     │
│  │  Scanner   │  │ Scanner  │       │                     │
│  └──────┬──────┘  └────┬─────┘       │                     │
│         └──────────────┴─────────────┘                      │
│                         ▼                                    │
│                ┌──────────────────┐                         │
│                │  Claude Analyzer │                         │
│                │  (Sonnet 4)      │                         │
│                └────────┬─────────┘                         │
│                         ▼                                    │
│                ┌──────────────────┐                         │
│                │  PDF Generator   │                         │
│                └────────┬─────────┘                         │
│                         ▼                                    │
│                ┌──────────────────┐                         │
│                │   Resend Email   │                         │
│                └──────────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Ticker Universe

### Portfolio (16 stocks — highest priority)
Stocks the user currently holds. Tagged `[PORTFOLIO]` throughout all scan data. Claude provides position management guidance (add/hold/trim/hedge) for these in every trade setup.

```
ASTS  BBAI  COIN  CRWV  IREN  NVDA  OKLO  PLTR
QBTS  RGTI  SBET  SOFI  TER   TSLA  UNH   ZETA
```

### Watchlist by Sector (32 stocks)

| Sector | Tickers |
|--------|---------|
| AI Semiconductors | NVDA, AMD, AVGO, MRVL, ARM, SMCI |
| AI Infrastructure | CRWV, IREN, BTDR, CORZ |
| AI Software | PLTR, SNOW, MDB, CRWD, BBAI, SOUN, PATH |
| Defense & Aerospace | LMT, RTX, KTOS, AVAV, LDOS, RKLB |
| Nuclear Energy | CCJ, LEU, BWXT, SMR, OKLO, VST, CEG |
| Quantum Computing | IONQ, RGTI |

Tickers appearing in both portfolio and a sector are deduplicated in scanning.

---

## 4. Scanners

### 4.1 Market Context (`market_context.py`)
- Fetches SPY, QQQ, VIX real-time prices and % changes
- Determines market sentiment: `risk_on` (VIX < 15, SPY up), `risk_off` (VIX > 25), `neutral`
- Fetches 5 sector ETF prices: SMH, IGV, XLE, ITA, ARKQ
- **Data source:** yfinance

### 4.2 Pre-Market Movers (`premarket.py`)
- Monitors all watchlist + portfolio tickers plus core mega-caps
- Flags moves ≥ 3% from previous close
- Tags whether mover is on the watchlist
- **Data source:** yfinance

### 4.3 Macro Calendar (`macro_calendar.py`)
- Fetches US economic calendar from Finnhub for next 5 days
- Filters for high/medium impact events (Fed, CPI, jobs, GDP)
- Separately tracks earnings for sector-moving stocks (NVDA, AMD, MSFT, etc.)
- **Data source:** Finnhub

### 4.4 Earnings Scanner (`earnings.py`)
- Finds watchlist stocks reporting within 7 days
- Calculates historical beat rate and average surprise % (last 4 quarters)
- Sorts by proximity of report date
- **Data sources:** FMP (calendar), Finnhub (history)

### 4.5 News Scanner (`news.py`)
- Pulls company news from last 24 hours for all tickers
- Scores sentiment via keyword matching (bullish/bearish lists)
- Returns top 5 articles per ticker sorted by sentiment score
- **Data source:** Finnhub

### 4.6 Momentum Scanner (`momentum.py`)
- Fetches current quote: price, % change, open/prev close
- Detects: moves > 3%, near 52-week high/low (within 5%), gap > 2%
- Only includes tickers with active signals
- **Data source:** Finnhub

### 4.7 Technical Analysis Scanner (`technicals.py`)
- Downloads 1 year of daily closes
- Calculates: 14-period RSI, 50-day MA, 200-day MA
- Detects: overbought/oversold RSI, golden/death cross forming, high short interest
- **Data sources:** yfinance (price), Finnhub (short interest)

### 4.8 Options Flow Scanner (`options.py`)
- Fetches option chains for near-term expirations (< 30 days)
- Flags unusual activity when volume/OI ratio > 1.0 (moderate) or > 2.0 (strong)
- Computes call/put volume ratios per ticker
- **Data source:** yfinance

---

## 5. Claude Analysis

**Model:** `claude-sonnet-4-20250514`
**Max tokens:** 2,000

Claude receives all scanner outputs formatted into sections and is instructed to:

1. Identify the **top 3 most actionable setups** ranked by conviction
2. Classify each as `day_trade` or `swing` (no other values allowed)
3. Provide `time_horizon` for each (e.g. "intraday", "2-5 days", "1-3 weeks")
4. For `[PORTFOLIO]` tagged stocks: include position management guidance
5. Provide a watchlist (2-3 stocks to monitor), no-action list, and sector summary

### Day Trade Criteria
Focus on: pre-market movers, news catalysts, unusual options flow, RSI extremes, gap setups.

### Swing Criteria
Focus on: upcoming earnings, technical breakouts, sector rotation, analyst upgrades, price target gaps.

### Output JSON Schema
```json
{
  "top_opportunities": [
    {
      "rank": 1,
      "ticker": "NVDA",
      "company": "NVIDIA Corporation",
      "setup_type": "swing",
      "time_horizon": "1-3 weeks",
      "catalyst": "...",
      "thesis": "...",
      "trade_setup": "...",
      "key_risk": "...",
      "conviction": 8
    }
  ],
  "watchlist": [{"ticker": "...", "reason": "..."}],
  "no_action": [{"ticker": "...", "reason": "..."}],
  "sector_summary": {
    "ai_semiconductors": {
      "outlook": "Bullish",
      "overview": "...",
      "news": [{"title": "...", "url": "..."}]
    }
  }
}
```

---

## 6. PDF Report

Generated with ReportLab. Sections:

1. **Header** — "MARKET SCANNER REPORT", date
2. **Top Opportunities** — for each of the 3 setups:
   - `#1 TICKER — Company Name`
   - `★ PORTFOLIO HOLDING` badge (amber, if applicable)
   - Type (Day Trade / Swing) | Horizon | Conviction bar (█████░░░░░ 5/10)
   - Catalyst, Thesis, Trade Setup, Key Risk (in red)
3. **Watchlist** — monitoring candidates
4. **No Action** — filtered stocks with explanation
5. **Sector Summary** — per-sector outlook with news links
6. **Footer** — timestamp, "Not financial advice"

---

## 7. Email Delivery

- **Provider:** Resend
- **Trigger:** After PDF generation, if `SEND_EMAIL=true`
- **Subject:** `Market Scan [Date] | Top: [TOP_TICKER]`
- **Body:** HTML summary of top 3 picks
- **Attachment:** PDF report

---

## 8. Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `FINNHUB_API_KEY` | Yes | Finnhub API key |
| `FMP_API_KEY` | Yes | Financial Modeling Prep key |
| `ANTHROPIC_API_KEY` | Yes | Claude API key |
| `RESEND_API_KEY` | Yes (for email) | Resend API key |
| `ALERT_EMAIL` | Yes (for email) | Recipient email address |
| `SEND_EMAIL` | No | Set to `"true"` to enable email (default: false) |
| `EARNINGS_LOOKAHEAD_DAYS` | No | Days ahead for earnings scan (default: 7) |
| `SCAN_LOOKBACK_HOURS` | No | Hours back for news scan (default: 24) |
| `PRICE_CHANGE_THRESHOLD` | No | Min % move for momentum/premarket (default: 3.0) |

---

## 9. GitHub Actions Schedule

**File:** `.github/workflows/daily-scan.yml`

- **Cron:** `0 11 * * 1-5` — 11:00 UTC = 6:00 AM ET on weekdays
- **Manual trigger:** `workflow_dispatch` available
- **Artifacts:** PDF retained for 30 days under `market-scan-{run_id}`
- **Secrets required:** All 5 API key secrets must be set in repo settings
