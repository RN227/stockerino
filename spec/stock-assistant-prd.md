# Product Requirements Document: Stock Trading Assistant CLI

**Version:** 1.0  
**Author:** Raghav  
**Date:** January 29, 2026  
**Status:** Draft

---

## 1. Overview

### 1.1 Product Description

A command-line tool that accepts a stock ticker as input and returns a comprehensive analysis including news, price targets, earnings data, and actionable trade recommendations. Built for personal use, optimized for US equity markets.

### 1.2 Core User Flow

```
Input: stock-assistant AAPL
       ↓
Output: Formatted analysis with recommendation
```

---

## 2. Data Sources and API Configuration

### 2.1 API Selection Matrix

| Data Type | Primary API | Free Tier Limits | Backup API |
|-----------|-------------|------------------|------------|
| News + Sentiment | Finnhub | 60 calls/min | FMP |
| Price Targets | FMP | 250 calls/day | Finnhub |
| Earnings Calendar | FMP | 250 calls/day | Finnhub |
| Current Price | Finnhub | 60 calls/min | Yahoo Finance |
| Company Profile | FMP | 250 calls/day | - |
| Options Chain | Tradier | Free with account | - |

### 2.2 API Setup Instructions

#### Finnhub (Primary - News, Quotes, Sentiment)

**Sign Up:**
1. Go to https://finnhub.io
2. Create free account
3. Navigate to Dashboard → API Keys
4. Copy API key

**Free Tier:**
- 60 API calls/minute
- Real-time US stock data
- Company news with sentiment scores
- Basic fundamentals

**Environment Variable:**
```bash
export FINNHUB_API_KEY="your_key_here"
```

**Endpoints Used:**
```
GET /api/v1/quote?symbol={TICKER}           # Current price
GET /api/v1/company-news?symbol={TICKER}    # News articles
GET /api/v1/stock/recommendation?symbol={TICKER}  # Analyst recommendations
GET /api/v1/stock/price-target?symbol={TICKER}    # Price targets
```

---

#### Financial Modeling Prep (FMP) - Earnings, Targets, Fundamentals

**Sign Up:**
1. Go to https://financialmodelingprep.com
2. Create free account
3. Navigate to Dashboard → API Keys
4. Copy API key

**Free Tier:**
- 250 API calls/day
- Historical earnings data
- Analyst estimates
- Price targets (high/low/consensus)
- 5 years of financial statements

**Environment Variable:**
```bash
export FMP_API_KEY="your_key_here"
```

**Endpoints Used:**
```
GET /api/v3/earning_calendar?symbol={TICKER}        # Upcoming earnings
GET /api/v3/analyst-estimates/{TICKER}              # EPS/revenue estimates
GET /api/v3/price-target-consensus/{TICKER}         # Consensus price target
GET /api/v3/stock_news?tickers={TICKER}&limit=10    # Stock news
GET /api/v3/profile/{TICKER}                        # Company profile
GET /api/v3/earnings-surprises/{TICKER}             # Historical earnings beats/misses
```

---

#### Tradier (Options Data - Optional)

**Sign Up:**
1. Go to https://tradier.com
2. Create brokerage account (required for API access)
3. Navigate to Settings → API → Generate Token

**Free Tier:**
- Free with brokerage account
- Real-time options chains
- Greeks data via ORATS
- Paper trading sandbox

**Environment Variable:**
```bash
export TRADIER_API_KEY="your_token_here"
```

**Endpoints Used:**
```
GET /v1/markets/options/chains?symbol={TICKER}      # Options chain
GET /v1/markets/options/expirations?symbol={TICKER} # Expiration dates
```

---

#### Claude API (Analysis Engine)

**Sign Up:**
1. Go to https://console.anthropic.com
2. Create account
3. Navigate to API Keys → Create Key

**Pricing:**
- Pay per token (no free tier for API)
- Claude Sonnet 4 recommended for cost/performance balance

**Environment Variable:**
```bash
export ANTHROPIC_API_KEY="your_key_here"
```

---

## 3. Data Fetching Specification

### 3.1 Data Objects to Fetch

For each stock ticker, fetch the following data objects:

#### A. Current Price Data
```json
{
  "source": "finnhub",
  "endpoint": "/quote",
  "fields": {
    "c": "current_price",
    "h": "high_today",
    "l": "low_today",
    "o": "open_price",
    "pc": "previous_close",
    "d": "change",
    "dp": "change_percent"
  }
}
```

#### B. Company Profile
```json
{
  "source": "fmp",
  "endpoint": "/profile/{ticker}",
  "fields": {
    "companyName": "name",
    "sector": "sector",
    "industry": "industry",
    "mktCap": "market_cap",
    "beta": "beta",
    "description": "description"
  }
}
```

#### C. News Articles (Last 7 Days)
```json
{
  "source": "finnhub",
  "endpoint": "/company-news",
  "params": {
    "from": "7_days_ago",
    "to": "today"
  },
  "fields": {
    "headline": "title",
    "summary": "summary",
    "datetime": "published_at",
    "source": "source",
    "url": "url"
  },
  "limit": 10
}
```

#### D. Price Targets
```json
{
  "source": "fmp",
  "endpoint": "/price-target-consensus/{ticker}",
  "fields": {
    "targetHigh": "high",
    "targetLow": "low",
    "targetConsensus": "consensus",
    "targetMedian": "median"
  }
}
```

#### E. Analyst Recommendations
```json
{
  "source": "finnhub",
  "endpoint": "/stock/recommendation",
  "fields": {
    "buy": "buy_count",
    "hold": "hold_count",
    "sell": "sell_count",
    "strongBuy": "strong_buy_count",
    "strongSell": "strong_sell_count",
    "period": "period"
  }
}
```

#### F. Earnings Data
```json
{
  "source": "fmp",
  "endpoint": "/earning_calendar",
  "params": {
    "symbol": "{ticker}"
  },
  "fields": {
    "date": "earnings_date",
    "epsEstimated": "eps_estimate",
    "revenueEstimated": "revenue_estimate"
  }
}
```

#### G. Earnings Surprises (Last 4 Quarters)
```json
{
  "source": "fmp",
  "endpoint": "/earnings-surprises/{ticker}",
  "fields": {
    "date": "quarter_date",
    "actualEarningResult": "actual_eps",
    "estimatedEarning": "estimated_eps"
  },
  "limit": 4
}
```

#### H. Options Chain (Optional - if Tradier configured)
```json
{
  "source": "tradier",
  "endpoint": "/markets/options/chains",
  "params": {
    "symbol": "{ticker}",
    "expiration": "nearest_monthly"
  },
  "fields": {
    "strike": "strike",
    "bid": "bid",
    "ask": "ask",
    "volume": "volume",
    "open_interest": "open_interest",
    "greeks.delta": "delta",
    "greeks.iv": "implied_volatility"
  }
}
```

---

## 4. Claude Integration

### 4.1 Data Packaging

All fetched data is combined into a single JSON object and passed to Claude:

```json
{
  "ticker": "AAPL",
  "fetched_at": "2026-01-29T10:30:00Z",
  "current_price": { ... },
  "company_profile": { ... },
  "news": [ ... ],
  "price_targets": { ... },
  "analyst_recommendations": { ... },
  "upcoming_earnings": { ... },
  "earnings_history": [ ... ],
  "options_chain": { ... }
}
```

### 4.2 Claude System Prompt

```
You are a stock analysis assistant. Your job is to analyze the provided market data and give actionable trading recommendations.

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
- Always mention the key risk to your thesis
```

### 4.3 Claude User Prompt Template

```
Analyze {TICKER} based on the following data:

CURRENT PRICE:
{current_price_data}

COMPANY:
{company_profile}

RECENT NEWS (last 7 days):
{news_summaries}

ANALYST PRICE TARGETS:
{price_targets}

ANALYST RECOMMENDATIONS:
{recommendations}

UPCOMING EARNINGS:
{earnings_data}

EARNINGS HISTORY (last 4 quarters):
{earnings_history}

{OPTIONS_SECTION_IF_AVAILABLE}

Provide your analysis and recommendation.
```

---

## 5. Output Format

### 5.1 CLI Output Structure

```
================================================================================
                         STOCK ANALYSIS: AAPL
================================================================================

CURRENT PRICE
-------------
Price: $198.45  |  Change: +$2.30 (+1.17%)
Day Range: $196.10 - $199.20  |  Prev Close: $196.15

COMPANY SNAPSHOT
----------------
Apple Inc. | Technology | Consumer Electronics
Market Cap: $3.05T | Beta: 1.24

NEWS HIGHLIGHTS
---------------
[+] Apple announces record Q1 services revenue (2 days ago)
    Source: Reuters
[~] iPhone sales flat in China amid competition (4 days ago)
    Source: Bloomberg
[-] EU antitrust probe expanded to App Store (6 days ago)
    Source: Financial Times

ANALYST TARGETS
---------------
Consensus: $215.00 | High: $250.00 | Low: $180.00
Upside to Consensus: +8.3%

RECOMMENDATIONS
---------------
Strong Buy: 12 | Buy: 18 | Hold: 8 | Sell: 2 | Strong Sell: 0

EARNINGS
--------
Next Report: February 6, 2026
EPS Estimate: $2.35 | Revenue Estimate: $124.5B
Last 4 Quarters: Beat | Beat | Beat | Miss

--------------------------------------------------------------------------------
                              RECOMMENDATION
--------------------------------------------------------------------------------

Sentiment: BULLISH
Confidence: 7/10
Time Horizon: 1-3 months
Action: BUY

THESIS:
Strong services growth momentum and consistent earnings beats support the bull
case. Current price offers 8% upside to consensus. Earnings in 8 days is a
near-term catalyst - historical beat rate is 75%.

TRADE SETUP:
- Entry: Current levels ($198-200)
- Target: $215 (consensus)
- Stop Loss: $188 (5% below)

ALTERNATIVE (if options):
- Feb 21 $200 Call @ $5.50
- Risk: Premium paid
- Reward: Leveraged upside into earnings

KEY RISK:
China iPhone weakness could pressure Q2 guidance despite Q1 beat.

================================================================================
```

### 5.2 Color Coding (Terminal)

| Element | Color | Meaning |
|---------|-------|---------|
| `[+]` | Green | Bullish signal |
| `[-]` | Red | Bearish signal |
| `[~]` | Yellow | Neutral signal |
| BUY/BULLISH | Green | Positive recommendation |
| SELL/BEARISH | Red | Negative recommendation |
| HOLD/NEUTRAL | Yellow | Neutral recommendation |

---

## 6. Technical Architecture

### 6.1 Directory Structure

```
stock-assistant/
├── src/
│   ├── main.py              # CLI entry point
│   ├── config.py            # Environment variables, API keys
│   ├── fetchers/
│   │   ├── __init__.py
│   │   ├── finnhub.py       # Finnhub API client
│   │   ├── fmp.py           # FMP API client
│   │   └── tradier.py       # Tradier API client (optional)
│   ├── analyzer/
│   │   ├── __init__.py
│   │   └── claude.py        # Claude API integration
│   ├── formatters/
│   │   ├── __init__.py
│   │   └── terminal.py      # CLI output formatting
│   └── models/
│       ├── __init__.py
│       └── stock_data.py    # Data models/types
├── tests/
│   └── ...
├── requirements.txt
├── .env.example
└── README.md
```

### 6.2 Dependencies

```
# requirements.txt
anthropic>=0.40.0
requests>=2.31.0
python-dotenv>=1.0.0
rich>=13.7.0        # Terminal formatting
click>=8.1.0        # CLI framework
pydantic>=2.5.0     # Data validation
```

### 6.3 CLI Interface

```bash
# Basic usage
stock-assistant AAPL

# Multiple tickers
stock-assistant AAPL MSFT GOOGL

# Options for output
stock-assistant AAPL --json          # JSON output
stock-assistant AAPL --brief         # Short summary only
stock-assistant AAPL --no-options    # Skip options data

# Save to file
stock-assistant AAPL --output report.txt
```

---

## 7. Error Handling

### 7.1 API Failures

| Scenario | Behavior |
|----------|----------|
| Finnhub rate limit (429) | Wait 60s, retry once |
| FMP daily limit exceeded | Show warning, use cached data if available |
| Invalid ticker | Show "Ticker not found" message |
| Network timeout | Retry 3x with exponential backoff |
| Claude API error | Show raw data without analysis |

### 7.2 Graceful Degradation

If a data source fails, the tool should still produce output with available data:

```
WARNING: Could not fetch options data (Tradier API unavailable)
Proceeding with available data...
```

---

## 8. Configuration

### 8.1 Environment Variables

```bash
# .env file
FINNHUB_API_KEY=your_finnhub_key
FMP_API_KEY=your_fmp_key
ANTHROPIC_API_KEY=your_anthropic_key
TRADIER_API_KEY=your_tradier_key  # Optional

# Optional settings
STOCK_ASSISTANT_CACHE_TTL=300     # Cache data for 5 minutes
STOCK_ASSISTANT_NEWS_DAYS=7       # News lookback period
```

### 8.2 Rate Limiting Logic

```python
# Built-in rate limiting to stay within free tiers
RATE_LIMITS = {
    "finnhub": {"calls": 60, "period": 60},   # 60/min
    "fmp": {"calls": 250, "period": 86400},   # 250/day
}
```

---

## 9. Future Enhancements (Out of Scope for v1)

- Watchlist management
- Historical analysis caching
- Automated daily scans (cron)
- Slack/Telegram notifications
- Portfolio integration
- Backtesting recommendations

---

## 10. Success Criteria

| Metric | Target |
|--------|--------|
| Response time | < 10 seconds |
| API cost per analysis | < $0.05 |
| Data freshness | < 15 minutes |
| Recommendation accuracy | Track over time |

---

## 11. Getting Started Checklist

- [ ] Sign up for Finnhub (free)
- [ ] Sign up for FMP (free)
- [ ] Get Anthropic API key (paid)
- [ ] Optional: Create Tradier account for options
- [ ] Set up environment variables
- [ ] Install dependencies
- [ ] Run first analysis

---

*Document End*
