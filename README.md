# Stocker - Stock Trading Assistant CLI

A command-line tool that analyzes stocks and provides AI-powered trading recommendations.

## Features

- Real-time price quotes from Finnhub
- Recent news aggregation
- Analyst price targets and recommendations
- Earnings data and historical beat/miss tracking
- Options chain data (optional, requires Tradier)
- AI-powered analysis using Claude

## Installation

1. Clone the repository and install dependencies:

```bash
cd stockerino
pip install -e .
```

2. Set up your API keys by creating a `.env` file:

```bash
cp .env.example .env
```

3. Edit `.env` with your API keys:

```bash
# Required
FINNHUB_API_KEY=your_key      # Get from https://finnhub.io
FMP_API_KEY=your_key          # Get from https://financialmodelingprep.com
ANTHROPIC_API_KEY=your_key    # Get from https://console.anthropic.com

# Optional
TRADIER_API_KEY=your_key      # Get from https://tradier.com (for options data)
```

## Usage

```bash
# Analyze a single stock
stocker AAPL

# Analyze multiple stocks
stocker AAPL MSFT GOOGL

# Skip options data
stocker AAPL --no-options

# Get raw JSON output
stocker AAPL --json

# Brief summary only
stocker AAPL --brief
```

## API Keys Setup

### Finnhub (Free)
1. Sign up at https://finnhub.io
2. Go to Dashboard → API Keys
3. Copy your API key

### Financial Modeling Prep (Free)
1. Sign up at https://financialmodelingprep.com
2. Go to Dashboard → API Keys
3. Copy your API key

### Anthropic (Paid)
1. Sign up at https://console.anthropic.com
2. Create an API key
3. Copy your API key

### Tradier (Optional, Free with account)
1. Create a brokerage account at https://tradier.com
2. Go to Settings → API → Generate Token
3. Copy your access token

## Output

The tool displays:
- Current price and daily change
- Company snapshot (sector, market cap, beta)
- Recent news headlines
- Analyst price targets and recommendations
- Upcoming earnings and historical performance
- Options data (if Tradier is configured)
- AI-generated analysis with trading recommendation
