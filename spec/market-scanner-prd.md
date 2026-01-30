# Market Scanner PRD
## Daily Pre-Market Trading Opportunities Scanner

**Version:** 2.0  
**Last Updated:** January 29, 2026

---

## 1. Executive Summary

A Python-based scanner that runs daily at 6 AM ET via GitHub Actions, identifies short-term trading opportunities, uploads a PDF report to Google Drive, and emails you a link.

**Stack (100% Free except Claude API):**
- **GitHub Actions** - Runs scanner on schedule
- **Google Drive** - Stores organized PDFs
- **Resend** - Sends email with Drive link
- **Claude** - Analyzes data (~$1-2/month)

**What You Get:**
```
6 AM ET → Scanner runs → PDF uploaded to Drive
                              ↓
         Email arrives: "Market Scan | Top: NVDA"
                              ↓
              [ Open Full Report ] → PDF in Drive
```

**Folder Structure in Drive:**
```
Market Scanner/
└── 2026/
    └── 01-January/
        └── Week-05/
            └── 2026-01-29-Wed-Market-Scan.pdf
```

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                  GITHUB ACTIONS (Cron: 6 AM ET)                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                  │
│  │ Earnings │    │   News   │    │ Momentum │                  │
│  │ Scanner  │    │ Scanner  │    │ Scanner  │                  │
│  └────┬─────┘    └────┬─────┘    └────┬─────┘                  │
│       │               │               │                         │
│       └───────────────┼───────────────┘                         │
│                       ▼                                         │
│              ┌──────────────┐                                   │
│              │    Claude    │                                   │
│              │   Analyzer   │                                   │
│              └──────┬───────┘                                   │
│                     ▼                                           │
│              ┌──────────────┐                                   │
│              │     PDF      │                                   │
│              │  Generator   │                                   │
│              └──────┬───────┘                                   │
│                     ▼                                           │
│              ┌──────────────┐      ┌──────────────┐            │
│              │ Google Drive │─────▶│    Resend    │            │
│              │   Upload     │      │    Email     │            │
│              └──────────────┘      └──────┬───────┘            │
│                                           │                     │
└───────────────────────────────────────────│─────────────────────┘
                                            ▼
                                     📧 Your Inbox
                                   (with Drive link)
```

---

## 3. Watchlist (20 Stocks)

### 3.1 AI / Semiconductors (5)
| Ticker | Company | Why Included |
|--------|---------|--------------|
| NVDA | NVIDIA | AI bellwether, highest volume |
| AMD | AMD | GPU competition, high catalyst density |
| AVGO | Broadcom | AI networking, dividend aristocrat |
| SMCI | Super Micro | AI server pure-play, volatile |
| PLTR | Palantir | AI software, government contracts |

### 3.2 Robotics / Automation (5)
| Ticker | Company | Why Included |
|--------|---------|--------------|
| ISRG | Intuitive Surgical | Surgical robotics leader |
| SERV | Serve Robotics | Delivery robots, high beta |
| KTOS | Kratos Defense | Defense drones, government spend |
| TER | Teradyne | Robot testing, Universal Robots |
| AVAV | AeroVironment | Military drones, backlog growth |

### 3.3 Nuclear / SMR / Uranium (5)
| Ticker | Company | Why Included |
|--------|---------|--------------|
| SMR | NuScale Power | SMR pure-play, first mover |
| OKLO | Oklo | Sam Altman backed, speculative |
| CCJ | Cameco | Largest uranium producer |
| LEU | Centrus Energy | Uranium enrichment monopoly |
| BWXT | BWX Technologies | Nuclear components, defense |

### 3.4 Quantum Computing (5)
| Ticker | Company | Why Included |
|--------|---------|--------------|
| IONQ | IonQ | Leading pure-play quantum |
| RGTI | Rigetti | Quantum-classical hybrid |
| QBTS | D-Wave Quantum | Quantum annealing |
| QUBT | Quantum Computing Inc | High volatility |
| ARQQ | Arqit Quantum | Quantum encryption |

### 3.5 Watchlist Configuration

```json
// src/data/watchlist.json
{
  "ai_semiconductors": ["NVDA", "AMD", "AVGO", "SMCI", "PLTR"],
  "robotics_automation": ["ISRG", "SERV", "KTOS", "TER", "AVAV"],
  "nuclear_smr_uranium": ["SMR", "OKLO", "CCJ", "LEU", "BWXT"],
  "quantum_computing": ["IONQ", "RGTI", "QBTS", "QUBT", "ARQQ"]
}
```

---

## 4. Data Sources & API Specifications

### 4.1 FMP (Financial Modeling Prep)
**Free Tier:** 250 calls/day  
**Base URL:** `https://financialmodelingprep.com/api/v3`

| Endpoint | Purpose | Call Cost |
|----------|---------|-----------|
| `/earning_calendar?from={date}&to={date}` | All earnings in date range | 1 call |
| `/quote/{tickers}` | Batch quotes (comma-separated) | 1 call per 50 tickers |
| `/stock_news?tickers={tickers}&limit=50` | Multi-ticker news | 1 call |
| `/analyst-estimates/{ticker}` | EPS/revenue estimates | 1 call per ticker |

### 4.2 Finnhub
**Free Tier:** 60 calls/minute  
**Base URL:** `https://finnhub.io/api/v1`

| Endpoint | Purpose | Call Cost |
|----------|---------|-----------|
| `/company-news?symbol={ticker}&from={date}&to={date}` | Company news | 1 call per ticker |
| `/stock/recommendation?symbol={ticker}` | Analyst ratings | 1 call per ticker |
| `/quote?symbol={ticker}` | Real-time quote | 1 call per ticker |

### 4.3 Anthropic (Claude)
**Model:** claude-sonnet-4-20250514  
**Cost:** ~$0.003 per 1K input tokens, ~$0.015 per 1K output tokens

### 4.4 Resend (Email)
**Free Tier:** 3,000 emails/month (100/day)  
**Feature:** PDF attachments supported via base64

### 4.5 API Budget Per Scan

| API | Calls Used | Limit | Headroom |
|-----|------------|-------|----------|
| FMP | ~30 | 250/day | 88% |
| Finnhub | ~40 | 60/min | 33% |
| Claude | 1-2 | Pay per use | ~$0.05 |
| Resend | 1 | 100/day | 99% |

---

## 5. Scanner Specifications

### 5.1 Earnings Scanner

**Purpose:** Find stocks reporting earnings in next 5 trading days

**Logic:**
```python
def scan_earnings(watchlist: list[str]) -> list[dict]:
    # 1. Fetch bulk earnings calendar (1 API call)
    today = datetime.now()
    end_date = today + timedelta(days=7)  # Include weekends buffer
    
    calendar = fmp.get_earnings_calendar(
        from_date=today.strftime("%Y-%m-%d"),
        to_date=end_date.strftime("%Y-%m-%d")
    )
    
    # 2. Filter to watchlist
    watchlist_earnings = [
        e for e in calendar 
        if e["symbol"] in watchlist
    ]
    
    # 3. Enrich with beat history
    for stock in watchlist_earnings:
        history = fmp.get_earnings_surprises(stock["symbol"], limit=4)
        stock["beat_rate"] = calculate_beat_rate(history)
        stock["avg_surprise"] = calculate_avg_surprise(history)
    
    return watchlist_earnings
```

**Output Schema:**
```python
{
    "symbol": "NVDA",
    "report_date": "2026-02-26",
    "report_time": "AMC",  # AMC = After Market Close, BMO = Before Market Open
    "eps_estimate": 0.84,
    "revenue_estimate": 38200000000,
    "beat_rate": 1.0,  # 100% beat rate last 4 quarters
    "avg_surprise_pct": 12.5
}
```

### 5.2 News Scanner

**Purpose:** Identify catalyst-driven opportunities from recent news

**Keywords to Flag:**
```python
BULLISH_KEYWORDS = [
    "acquisition", "acquire", "merger", "deal", "partnership",
    "contract", "awarded", "patent", "FDA approval", "breakthrough",
    "upgrade", "outperform", "buy rating", "price target raised",
    "beat", "exceeds", "record revenue", "guidance raised"
]

BEARISH_KEYWORDS = [
    "downgrade", "sell rating", "price target cut", "misses",
    "lawsuit", "investigation", "recall", "warning", "layoffs",
    "guidance cut", "below expectations", "delays"
]
```

**Logic:**
```python
def scan_news(watchlist: list[str]) -> list[dict]:
    # 1. Batch fetch news (1 call per 10 tickers)
    all_news = []
    for batch in chunk(watchlist, 10):
        news = fmp.get_stock_news(
            tickers=",".join(batch),
            limit=50
        )
        all_news.extend(news)
    
    # 2. Filter to last 48 hours
    cutoff = datetime.now() - timedelta(hours=48)
    recent_news = [n for n in all_news if parse_date(n["publishedDate"]) > cutoff]
    
    # 3. Score by keywords
    scored_news = []
    for article in recent_news:
        text = f"{article['title']} {article['text']}".lower()
        
        bullish_hits = sum(1 for kw in BULLISH_KEYWORDS if kw in text)
        bearish_hits = sum(1 for kw in BEARISH_KEYWORDS if kw in text)
        
        if bullish_hits > 0 or bearish_hits > 0:
            article["sentiment_score"] = bullish_hits - bearish_hits
            article["sentiment"] = "bullish" if article["sentiment_score"] > 0 else "bearish"
            scored_news.append(article)
    
    return sorted(scored_news, key=lambda x: abs(x["sentiment_score"]), reverse=True)
```

**Output Schema:**
```python
{
    "symbol": "SMCI",
    "title": "Super Micro Announces Partnership with NVIDIA for AI Servers",
    "published_date": "2026-01-28T14:30:00Z",
    "url": "https://...",
    "sentiment": "bullish",
    "sentiment_score": 3,
    "keywords_matched": ["partnership", "AI"]
}
```

### 5.3 Momentum Scanner

**Purpose:** Flag unusual price/volume activity

**Thresholds:**
```python
MOMENTUM_THRESHOLDS = {
    "volume_multiplier": 2.0,      # Volume > 2x 20-day average
    "price_change_pct": 3.0,       # |Price change| > 3%
    "gap_threshold_pct": 2.0,      # Gap up/down > 2%
    "high_proximity_pct": 5.0      # Within 5% of 52-week high
}
```

**Logic:**
```python
def scan_momentum(watchlist: list[str]) -> list[dict]:
    # 1. Batch fetch quotes (1 call for all 20 tickers)
    quotes = fmp.get_batch_quotes(",".join(watchlist))
    
    flagged = []
    for q in quotes:
        signals = []
        
        # Volume spike
        if q["volume"] > q["avgVolume"] * MOMENTUM_THRESHOLDS["volume_multiplier"]:
            signals.append(f"Volume {q['volume']/q['avgVolume']:.1f}x average")
        
        # Price change
        change_pct = q["changesPercentage"]
        if abs(change_pct) > MOMENTUM_THRESHOLDS["price_change_pct"]:
            direction = "up" if change_pct > 0 else "down"
            signals.append(f"Price {direction} {abs(change_pct):.1f}%")
        
        # 52-week high proximity
        if q["price"] > q["yearHigh"] * (1 - MOMENTUM_THRESHOLDS["high_proximity_pct"]/100):
            signals.append(f"Near 52-week high (${q['yearHigh']})")
        
        if signals:
            flagged.append({
                "symbol": q["symbol"],
                "price": q["price"],
                "change_pct": change_pct,
                "volume": q["volume"],
                "avg_volume": q["avgVolume"],
                "signals": signals
            })
    
    return flagged
```

**Output Schema:**
```python
{
    "symbol": "IONQ",
    "price": 42.50,
    "change_pct": 8.2,
    "volume": 15000000,
    "avg_volume": 5000000,
    "signals": ["Volume 3.0x average", "Price up 8.2%", "Near 52-week high ($44.00)"]
}
```

---

## 6. Claude Analysis Integration

### 6.1 System Prompt

```python
SYSTEM_PROMPT = """You are a pre-market trading analyst identifying short-term opportunities.

Your job:
1. Analyze the provided market data for the given watchlist
2. Identify the TOP 3 most actionable setups for today
3. Rank by conviction (risk-adjusted potential, catalyst timing, setup clarity)

For each opportunity, provide:
- Ticker and company name
- Setup type (Earnings Play / News Catalyst / Momentum Breakout)
- Catalyst: What's driving this opportunity
- Thesis: 2-3 sentences on why this setup is compelling
- Trade Setup: Specific entry strategy (stock or options)
- Key Risk: Primary reason this could fail
- Conviction Score: 1-10

Also provide:
- WATCHLIST: 2-3 stocks worth monitoring but not immediately actionable
- NO ACTION: Briefly explain why certain flagged stocks don't make the cut

Be direct and actionable. No fluff. Traders reading this have 30 minutes before market open."""
```

### 6.2 User Prompt Template

```python
USER_PROMPT_TEMPLATE = """
## Market Scan Results - {date}

### EARNINGS (Next 5 Days)
{earnings_data}

### NEWS CATALYSTS (Last 48 Hours)
{news_data}

### MOMENTUM SIGNALS
{momentum_data}

### SECTOR CONTEXT
{sector_summary}

---

Analyze this data and provide your TOP 3 opportunities for today.
"""
```

### 6.3 Claude Response Schema

```python
{
    "scan_date": "2026-01-29",
    "top_opportunities": [
        {
            "rank": 1,
            "ticker": "NVDA",
            "company": "NVIDIA Corporation",
            "setup_type": "Earnings Play",
            "catalyst": "Q4 earnings Feb 26 BMO",
            "thesis": "100% beat rate last 8 quarters. Data center revenue acceleration expected. Options IV relatively low for earnings proximity.",
            "trade_setup": "Feb 28 $140 calls if holding through earnings, or stock entry on any pre-earnings dip to $135",
            "key_risk": "China export restrictions could weigh on guidance despite Q4 beat",
            "conviction": 8
        }
    ],
    "watchlist": [
        {
            "ticker": "SMR",
            "reason": "Nuclear momentum continuing but no immediate catalyst. Wait for pullback entry."
        }
    ],
    "no_action": [
        {
            "ticker": "QBTS",
            "reason": "Volume spike but no news. Likely retail-driven, avoid chasing."
        }
    ],
    "sector_summary": {
        "ai_semiconductors": "Bullish - NVDA earnings setup driving sector",
        "robotics_automation": "Neutral - No major catalysts this week",
        "nuclear_smr_uranium": "Bullish - Policy tailwinds continuing",
        "quantum_computing": "Cautious - Recent run-up needs consolidation"
    }
}
```

---

## 7. PDF Report Generation

### 7.1 Report Structure

```
┌────────────────────────────────────────────┐
│          MARKET SCANNER REPORT             │
│            January 29, 2026                │
│          Pre-Market Analysis               │
├────────────────────────────────────────────┤
│                                            │
│  TOP OPPORTUNITIES                         │
│  ═══════════════════                       │
│                                            │
│  #1 NVDA - NVIDIA Corporation              │
│  ─────────────────────────────             │
│  Type: Earnings Play                       │
│  Conviction: ████████░░ 8/10               │
│                                            │
│  Catalyst: Q4 earnings Feb 26 BMO          │
│                                            │
│  Thesis: 100% beat rate last 8 quarters... │
│                                            │
│  Trade Setup: Feb 28 $140 calls...         │
│                                            │
│  Key Risk: China export restrictions...    │
│                                            │
├────────────────────────────────────────────┤
│  WATCHLIST                                 │
│  • SMR: Nuclear momentum, wait for dip     │
│  • PLTR: Government contract rumors        │
├────────────────────────────────────────────┤
│  SECTOR SUMMARY                            │
│  AI/Semi: Bullish ▲                        │
│  Robotics: Neutral ─                       │
│  Nuclear: Bullish ▲                        │
│  Quantum: Cautious ▼                       │
└────────────────────────────────────────────┘
```

### 7.2 ReportLab Implementation

```python
# src/output/pdf_generator.py

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.units import inch
from datetime import datetime

def generate_pdf_report(analysis: dict, output_path: str) -> str:
    """Generate PDF report from Claude analysis."""
    
    doc = SimpleDocTemplate(output_path, pagesize=letter,
                           leftMargin=0.75*inch, rightMargin=0.75*inch,
                           topMargin=0.75*inch, bottomMargin=0.75*inch)
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    styles.add(ParagraphStyle(
        name='ReportTitle',
        parent=styles['Title'],
        fontSize=24,
        spaceAfter=6,
        textColor=colors.HexColor('#1a1a2e')
    ))
    
    styles.add(ParagraphStyle(
        name='SectionHeader',
        parent=styles['Heading1'],
        fontSize=14,
        spaceBefore=20,
        spaceAfter=10,
        textColor=colors.HexColor('#16213e')
    ))
    
    styles.add(ParagraphStyle(
        name='TickerHeader',
        parent=styles['Heading2'],
        fontSize=12,
        spaceBefore=15,
        spaceAfter=5,
        textColor=colors.HexColor('#0f3460')
    ))
    
    styles.add(ParagraphStyle(
        name='BodyText',
        parent=styles['Normal'],
        fontSize=10,
        spaceBefore=3,
        spaceAfter=3,
        leading=14
    ))
    
    styles.add(ParagraphStyle(
        name='Label',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#666666'),
        spaceBefore=8
    ))
    
    story = []
    
    # Title
    story.append(Paragraph("MARKET SCANNER REPORT", styles['ReportTitle']))
    story.append(Paragraph(
        f"{datetime.now().strftime('%B %d, %Y')} | Pre-Market Analysis",
        styles['Normal']
    ))
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#1a1a2e')))
    
    # Top Opportunities
    story.append(Paragraph("TOP OPPORTUNITIES", styles['SectionHeader']))
    
    for i, opp in enumerate(analysis['top_opportunities'], 1):
        # Ticker header with conviction
        conviction_bar = "█" * opp['conviction'] + "░" * (10 - opp['conviction'])
        story.append(Paragraph(
            f"#{i} {opp['ticker']} - {opp['company']}",
            styles['TickerHeader']
        ))
        
        # Type and conviction
        story.append(Paragraph(
            f"<b>Type:</b> {opp['setup_type']} | <b>Conviction:</b> {conviction_bar} {opp['conviction']}/10",
            styles['BodyText']
        ))
        
        # Details
        story.append(Paragraph(f"<b>Catalyst:</b> {opp['catalyst']}", styles['BodyText']))
        story.append(Paragraph(f"<b>Thesis:</b> {opp['thesis']}", styles['BodyText']))
        story.append(Paragraph(f"<b>Trade Setup:</b> {opp['trade_setup']}", styles['BodyText']))
        story.append(Paragraph(f"<b>Key Risk:</b> {opp['key_risk']}", styles['BodyText']))
        
        story.append(Spacer(1, 10))
    
    # Watchlist
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cccccc')))
    story.append(Paragraph("WATCHLIST", styles['SectionHeader']))
    
    for item in analysis['watchlist']:
        story.append(Paragraph(
            f"• <b>{item['ticker']}:</b> {item['reason']}",
            styles['BodyText']
        ))
    
    # Sector Summary
    story.append(Spacer(1, 15))
    story.append(Paragraph("SECTOR SUMMARY", styles['SectionHeader']))
    
    sector_icons = {"Bullish": "▲", "Neutral": "─", "Cautious": "▼", "Bearish": "▼"}
    
    for sector, outlook in analysis['sector_summary'].items():
        sentiment = outlook.split(" - ")[0] if " - " in outlook else outlook
        icon = sector_icons.get(sentiment, "─")
        display_name = sector.replace("_", " ").title()
        story.append(Paragraph(
            f"<b>{display_name}:</b> {outlook} {icon}",
            styles['BodyText']
        ))
    
    # Build PDF
    doc.build(story)
    return output_path
```

---

## 8. Output: Google Drive + Email Notification

**Flow:**
```
GitHub Actions (6 AM ET)
    ↓
Scanner runs → PDF generated
    ↓
Upload to Google Drive (organized folders)
    ↓
Send email with summary + Drive link
    ↓
You tap link → Opens PDF
```

**What lands in your inbox:**
```
Subject: Market Scan Jan 29 | Top: NVDA

┌─────────────────────────────────────┐
│  Market Scan Complete               │
│  January 29, 2026                   │
│                                     │
│  Top Opportunities                  │
│  #1 NVDA - Earnings Play (8/10)     │
│  #2 IONQ - Momentum (7/10)          │
│  #3 SMR - News Catalyst (6/10)      │
│                                     │
│      [ Open Full Report ]           │
│           ↓                         │
│    Links to Drive PDF               │
└─────────────────────────────────────┘
```

---

## 8A. Google Drive Integration

### 8A.1 Folder Structure

Reports saved with organized naming:
```
Market Scanner/
├── 2026/
│   ├── 01-January/
│   │   ├── Week-01/
│   │   │   ├── 2026-01-06-Mon-Market-Scan.pdf
│   │   │   ├── 2026-01-07-Tue-Market-Scan.pdf
│   │   │   └── ...
│   │   ├── Week-05/
│   │   │   └── 2026-01-29-Wed-Market-Scan.pdf
│   │   └── ...
│   ├── 02-February/
│   └── ...
```

**File naming:** `YYYY-MM-DD-Day-Market-Scan.pdf`

### 8A.2 Google Cloud Setup (One-Time, ~10 min)

**Step 1: Create GCP Project**
1. Go to https://console.cloud.google.com
2. Create new project: "Market Scanner"

**Step 2: Enable Google Drive API**
1. Go to APIs & Services → Library
2. Search "Google Drive API" → Click Enable

**Step 3: Create Service Account**
1. Go to APIs & Services → Credentials
2. Create Credentials → Service Account
3. Name: `market-scanner-bot`
4. Click Create → Done
5. Click on the service account email
6. Keys tab → Add Key → Create new key → JSON
7. Download the JSON file

**Step 4: Share Your Drive Folder**
1. In Google Drive, create folder: "Market Scanner"
2. Right-click → Share
3. Add the service account email (e.g., `market-scanner-bot@your-project.iam.gserviceaccount.com`)
4. Give "Editor" permission
5. Copy folder ID from URL: `https://drive.google.com/drive/folders/THIS_IS_THE_ID`

### 8A.3 Google Drive Implementation

```python
# src/output/gdrive_uploader.py

import os
import json
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import structlog

log = structlog.get_logger()

SCOPES = ['https://www.googleapis.com/auth/drive.file']


class GoogleDriveUploader:
    def __init__(self):
        creds_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
        creds_dict = json.loads(creds_json)
        self.creds = service_account.Credentials.from_service_account_info(
            creds_dict, scopes=SCOPES
        )
        self.service = build('drive', 'v3', credentials=self.creds)
        self.root_folder_id = os.getenv("GDRIVE_ROOT_FOLDER_ID")
    
    def get_or_create_folder(self, name: str, parent_id: str) -> str:
        """Get existing folder or create new one."""
        query = f"name='{name}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = self.service.files().list(q=query, fields="files(id)").execute()
        files = results.get('files', [])
        
        if files:
            return files[0]['id']
        
        folder_metadata = {
            'name': name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_id]
        }
        folder = self.service.files().create(body=folder_metadata, fields='id').execute()
        log.info("folder_created", name=name)
        return folder['id']
    
    def build_folder_path(self, date: datetime) -> str:
        """Build nested folder structure: Year/Month/Week."""
        # Year folder
        year_folder = self.get_or_create_folder(str(date.year), self.root_folder_id)
        
        # Month folder: "01-January"
        month_name = date.strftime("%m-%B")
        month_folder = self.get_or_create_folder(month_name, year_folder)
        
        # Week folder: "Week-05"
        week_num = date.isocalendar()[1]
        week_folder = self.get_or_create_folder(f"Week-{week_num:02d}", month_folder)
        
        return week_folder
    
    def upload_report(self, pdf_path: str, date: datetime = None) -> dict:
        """Upload PDF and return file info with link."""
        if date is None:
            date = datetime.now()
        
        target_folder = self.build_folder_path(date)
        
        # File name: "2026-01-29-Wed-Market-Scan.pdf"
        file_name = f"{date.strftime('%Y-%m-%d-%a')}-Market-Scan.pdf"
        
        file_metadata = {
            'name': file_name,
            'parents': [target_folder]
        }
        
        media = MediaFileUpload(pdf_path, mimetype='application/pdf')
        
        file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, name, webViewLink'
        ).execute()
        
        log.info("file_uploaded", name=file['name'], link=file['webViewLink'])
        
        return {
            'id': file['id'],
            'name': file['name'],
            'link': file['webViewLink']
        }
```

---

## 8B. Email Notification (Resend)

### 8B.1 Resend Setup

1. Go to https://resend.com/signup
2. Create account (free tier: 3,000 emails/month)
3. Dashboard → API Keys → Create → Copy key

### 8B.2 Email Implementation

```python
# src/output/email_sender.py

import resend
import os
from datetime import datetime
import structlog

log = structlog.get_logger()


def send_scan_email(analysis: dict, drive_link: str) -> dict:
    """Send email with summary and Drive link."""
    
    resend.api_key = os.getenv("RESEND_API_KEY")
    
    # Subject line
    date_str = datetime.now().strftime("%b %d")
    top_picks = analysis.get('top_opportunities', [])
    top_ticker = top_picks[0]['ticker'] if top_picks else "N/A"
    subject = f"Market Scan {date_str} | Top: {top_ticker}"
    
    # Build summary
    if top_picks:
        picks_html = ""
        for i, p in enumerate(top_picks[:3], 1):
            picks_html += f"""
            <tr>
                <td style="padding: 8px 0; border-bottom: 1px solid #eee;">
                    <strong>#{i} {p['ticker']}</strong> - {p['company']}<br>
                    <span style="color: #666; font-size: 13px;">
                        {p['setup_type']} | Conviction: {p['conviction']}/10
                    </span><br>
                    <span style="font-size: 13px;">{p['catalyst']}</span>
                </td>
            </tr>
            """
    else:
        picks_html = "<tr><td>No actionable setups today.</td></tr>"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; 
                 max-width: 550px; margin: 0 auto; padding: 20px;">
        
        <h1 style="font-size: 22px; margin-bottom: 5px; color: #1a1a2e;">
            Market Scan Complete
        </h1>
        <p style="color: #666; margin-top: 0;">
            {datetime.now().strftime('%B %d, %Y')} | Pre-Market Analysis
        </p>
        
        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <strong style="font-size: 14px;">Today's Top Opportunities</strong>
            <table style="width: 100%; margin-top: 10px;">
                {picks_html}
            </table>
        </div>
        
        <a href="{drive_link}" 
           style="display: inline-block; background: #4285f4; color: white; 
                  padding: 12px 28px; text-decoration: none; border-radius: 6px; 
                  font-weight: 500; font-size: 15px;">
            Open Full Report
        </a>
        
        <p style="color: #999; font-size: 11px; margin-top: 30px;">
            This is an automated scan. Not financial advice. Do your own research.
        </p>
    </body>
    </html>
    """
    
    response = resend.Emails.send({
        "from": "Market Scanner <onboarding@resend.dev>",
        "to": [os.getenv("ALERT_EMAIL")],
        "subject": subject,
        "html": html
    })
    
    log.info("email_sent", to=os.getenv("ALERT_EMAIL"))
    return response
```

```python
# src/output/email_sender.py

import resend
import base64
import os
from datetime import datetime

def send_report_email(
    pdf_path: str,
    recipient: str,
    analysis: dict
) -> dict:
    """Send PDF report via Resend."""
    
    resend.api_key = os.getenv("RESEND_API_KEY")
    
    # Read PDF as base64
    with open(pdf_path, "rb") as f:
        pdf_content = base64.b64encode(f.read()).decode()
    
    # Build email subject
    date_str = datetime.now().strftime("%b %d")
    top_ticker = analysis['top_opportunities'][0]['ticker'] if analysis['top_opportunities'] else "N/A"
    subject = f"Market Scanner {date_str} | Top Pick: {top_ticker}"
    
    # Build HTML body (brief summary)
    html_body = build_email_html(analysis)
    
    # Send
    response = resend.Emails.send({
        "from": "Market Scanner <onboarding@resend.dev>",  # Or your verified domain
        "to": [recipient],
        "subject": subject,
        "html": html_body,
        "attachments": [
            {
                "filename": f"market-scan-{datetime.now().strftime('%Y-%m-%d')}.pdf",
                "content": pdf_content
            }
        ]
    })
    
    return response


def build_email_html(analysis: dict) -> str:
    """Build HTML email body with quick summary."""
    
    opportunities_html = ""
    for i, opp in enumerate(analysis['top_opportunities'][:3], 1):
        opportunities_html += f"""
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #eee;">
                <strong>#{i} {opp['ticker']}</strong><br>
                <span style="color: #666; font-size: 13px;">{opp['setup_type']} | Conviction: {opp['conviction']}/10</span><br>
                <span style="font-size: 13px;">{opp['catalyst']}</span>
            </td>
        </tr>
        """
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            h1 {{ color: #1a1a2e; font-size: 24px; }}
            .summary {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0; }}
            table {{ width: 100%; border-collapse: collapse; }}
            .footer {{ color: #999; font-size: 12px; margin-top: 30px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Market Scanner Report</h1>
            <p style="color: #666;">{datetime.now().strftime('%B %d, %Y')} | Pre-Market Analysis</p>
            
            <div class="summary">
                <strong>Today's Top Opportunities</strong>
                <table>
                    {opportunities_html}
                </table>
            </div>
            
            <p>Full analysis with trade setups attached as PDF.</p>
            
            <p class="footer">
                This is an automated scan. Not financial advice. Do your own research.
            </p>
        </div>
    </body>
    </html>
    """
```

---

## 9. Hosting (GitHub Actions)

### 9.1 Why GitHub Actions

| Feature | GitHub Actions | Railway | Vercel |
|---------|----------------|---------|--------|
| Native cron | Yes | Yes | No |
| Free tier | 2,000 min/month | $5 credit | N/A for scripts |
| Setup complexity | Low (YAML file) | Low | High (workaround needed) |
| Cost for this project | $0 | ~$1-2/month | N/A |

You'll use ~50 minutes/month (5 min/day × ~22 weekdays). Well within free tier.

### 9.2 GitHub Actions Workflow

Create `.github/workflows/daily-scan.yml`:

```yaml
name: Daily Market Scan

on:
  schedule:
    # 6 AM ET = 11:00 UTC (EST winter) / 10:00 UTC (EDT summer)
    # Using 11:00 UTC for EST. Adjust to 10:00 UTC during daylight saving.
    - cron: '0 11 * * 1-5'  # Weekdays only
  
  workflow_dispatch:  # Allows manual trigger for testing

jobs:
  scan:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run market scanner
        env:
          # API Keys
          FMP_API_KEY: ${{ secrets.FMP_API_KEY }}
          FINNHUB_API_KEY: ${{ secrets.FINNHUB_API_KEY }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          
          # Google Drive
          UPLOAD_TO_GDRIVE: 'true'
          GDRIVE_ROOT_FOLDER_ID: ${{ secrets.GDRIVE_ROOT_FOLDER_ID }}
          GOOGLE_SERVICE_ACCOUNT_JSON: ${{ secrets.GOOGLE_SERVICE_ACCOUNT_JSON }}
          
          # Email
          SEND_EMAIL: 'true'
          RESEND_API_KEY: ${{ secrets.RESEND_API_KEY }}
          ALERT_EMAIL: ${{ secrets.ALERT_EMAIL }}
        run: python -m src.main
      
      - name: Upload logs on failure
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: scan-logs
          path: logs/
          retention-days: 7
```

### 9.3 Adding GitHub Secrets

1. Go to your repo → **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret** for each:

| Secret Name | Value |
|-------------|-------|
| `FMP_API_KEY` | Your FMP API key |
| `FINNHUB_API_KEY` | Your Finnhub API key |
| `ANTHROPIC_API_KEY` | Your Anthropic API key |
| `GDRIVE_ROOT_FOLDER_ID` | Your Google Drive folder ID |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Entire JSON file contents (single line) |
| `RESEND_API_KEY` | Your Resend API key |
| `ALERT_EMAIL` | Your email address |

### 9.4 Converting Service Account JSON for GitHub

Your `service_account.json` needs to be a single line:

```bash
# On Mac/Linux
cat service_account.json | jq -c .

# Or use Python
python -c "import json; print(json.dumps(json.load(open('service_account.json'))))"
```

Copy the output and paste as the `GOOGLE_SERVICE_ACCOUNT_JSON` secret.

### 9.5 Testing the Workflow

**Manual trigger:**
1. Go to repo → **Actions** → **Daily Market Scan**
2. Click **Run workflow** → **Run workflow**
3. Watch the logs in real-time

**Verify success:**
- Check your Google Drive for the PDF
- Check your email for the notification with link

### 9.6 Monitoring

- **View runs:** Repo → Actions → Daily Market Scan
- **Email on failure:** GitHub sends email automatically if workflow fails
- **Logs:** Click any run to see full output

---

## 10. Directory Structure

```
market-scanner/
├── .github/
│   └── workflows/
│       └── daily-scan.yml      # GitHub Actions cron job
├── src/
│   ├── __init__.py
│   ├── main.py                 # Entry point
│   ├── config.py               # Environment variables
│   │
│   ├── data/
│   │   ├── __init__.py
│   │   └── watchlist.json      # Ticker watchlist
│   │
│   ├── fetchers/
│   │   ├── __init__.py
│   │   ├── base.py             # Retry logic
│   │   ├── fmp.py              # FMP API client
│   │   └── finnhub.py          # Finnhub API client
│   │
│   ├── scanners/
│   │   ├── __init__.py
│   │   ├── earnings.py         # Earnings scanner
│   │   ├── news.py             # News scanner
│   │   └── momentum.py         # Momentum scanner
│   │
│   ├── analyzer/
│   │   ├── __init__.py
│   │   └── claude.py           # Claude integration
│   │
│   ├── output/
│   │   ├── __init__.py
│   │   ├── pdf_generator.py    # ReportLab PDF
│   │   ├── gdrive_uploader.py  # Google Drive upload
│   │   └── email_sender.py     # Resend email
│   │
│   └── models/
│       ├── __init__.py
│       └── schemas.py          # Pydantic models
│
├── tests/
│   ├── __init__.py
│   └── test_scanners.py
│
├── logs/
│   └── .gitkeep
│
├── .env.example
├── .gitignore
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## 11. Dependencies

**requirements.txt:**
```
# API clients
requests>=2.31.0
anthropic>=0.18.0

# Data processing
pydantic>=2.5.0
python-dateutil>=2.8.2

# PDF generation
reportlab>=4.1.0

# Google Drive
google-auth>=2.22.0
google-api-python-client>=2.97.0

# Email (optional - only if using Resend)
resend>=0.7.0

# Configuration
python-dotenv>=1.0.0

# CLI (optional, for local testing)
click>=8.1.0
rich>=13.7.0

# Logging
structlog>=24.1.0
```

---

## 12. Configuration

**.env.example:**
```bash
# === API Keys (Required) ===
FMP_API_KEY=your_fmp_api_key
FINNHUB_API_KEY=your_finnhub_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# === Google Drive (Required) ===
UPLOAD_TO_GDRIVE=true
GDRIVE_ROOT_FOLDER_ID=your_folder_id_from_drive_url
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"..."}

# === Email Notification (Required) ===
SEND_EMAIL=true
RESEND_API_KEY=your_resend_api_key
ALERT_EMAIL=your@email.com

# === Scanner Settings (Optional - defaults shown) ===
SCAN_LOOKBACK_HOURS=48
EARNINGS_LOOKAHEAD_DAYS=5
VOLUME_THRESHOLD=2.0
PRICE_CHANGE_THRESHOLD=3.0
LOG_LEVEL=INFO
```

**src/config.py:**
```python
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "src" / "data"
LOGS_DIR = BASE_DIR / "logs"

# API Keys
FMP_API_KEY = os.getenv("FMP_API_KEY")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Google Drive
UPLOAD_TO_GDRIVE = os.getenv("UPLOAD_TO_GDRIVE", "true").lower() == "true"
GDRIVE_ROOT_FOLDER_ID = os.getenv("GDRIVE_ROOT_FOLDER_ID")
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

# Email (Resend)
SEND_EMAIL = os.getenv("SEND_EMAIL", "true").lower() == "true"
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
ALERT_EMAIL = os.getenv("ALERT_EMAIL")

# Scanner Settings
SCAN_LOOKBACK_HOURS = int(os.getenv("SCAN_LOOKBACK_HOURS", "48"))
EARNINGS_LOOKAHEAD_DAYS = int(os.getenv("EARNINGS_LOOKAHEAD_DAYS", "5"))
VOLUME_THRESHOLD = float(os.getenv("VOLUME_THRESHOLD", "2.0"))
PRICE_CHANGE_THRESHOLD = float(os.getenv("PRICE_CHANGE_THRESHOLD", "3.0"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# API Endpoints
FMP_BASE_URL = "https://financialmodelingprep.com/api/v3"
FINNHUB_BASE_URL = "https://finnhub.io/api/v1"


def validate_config():
    """Validate all required environment variables are set."""
    required = [
        ("FMP_API_KEY", FMP_API_KEY),
        ("FINNHUB_API_KEY", FINNHUB_API_KEY),
        ("ANTHROPIC_API_KEY", ANTHROPIC_API_KEY),
        ("GDRIVE_ROOT_FOLDER_ID", GDRIVE_ROOT_FOLDER_ID),
        ("GOOGLE_SERVICE_ACCOUNT_JSON", GOOGLE_SERVICE_ACCOUNT_JSON),
        ("RESEND_API_KEY", RESEND_API_KEY),
        ("ALERT_EMAIL", ALERT_EMAIL),
    ]
    
    missing = [name for name, value in required if not value]
    
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
```
```

---

## 13. Main Entry Point

**src/main.py:**
```python
#!/usr/bin/env python3
"""
Market Scanner - Daily Pre-Market Analysis
Runs via GitHub Actions cron at 6 AM ET on weekdays
"""

import sys
import json
import structlog
from datetime import datetime
from pathlib import Path

from src.config import (
    validate_config, DATA_DIR, LOGS_DIR,
    UPLOAD_TO_GDRIVE, SEND_EMAIL
)
from src.fetchers.fmp import FMPClient
from src.fetchers.finnhub import FinnhubClient
from src.scanners.earnings import EarningsScanner
from src.scanners.news import NewsScanner
from src.scanners.momentum import MomentumScanner
from src.analyzer.claude import ClaudeAnalyzer
from src.output.pdf_generator import generate_pdf_report
from src.output.gdrive_uploader import GoogleDriveUploader
from src.output.email_sender import send_scan_email

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)
log = structlog.get_logger()


def load_watchlist() -> dict:
    """Load watchlist from JSON file."""
    watchlist_path = DATA_DIR / "watchlist.json"
    with open(watchlist_path) as f:
        return json.load(f)


def flatten_watchlist(watchlist: dict) -> list[str]:
    """Flatten sector-grouped watchlist into single list."""
    return [ticker for tickers in watchlist.values() for ticker in tickers]


def run_scan():
    """Execute full market scan pipeline."""
    
    start_time = datetime.now()
    log.info("scan_started", timestamp=start_time.isoformat())
    
    try:
        # Validate configuration
        validate_config()
        
        # Load watchlist
        watchlist = load_watchlist()
        all_tickers = flatten_watchlist(watchlist)
        log.info("watchlist_loaded", ticker_count=len(all_tickers))
        
        # Initialize API clients
        fmp = FMPClient()
        finnhub = FinnhubClient()
        
        # Run scanners
        log.info("running_scanners")
        
        earnings_scanner = EarningsScanner(fmp)
        earnings_results = earnings_scanner.scan(all_tickers)
        log.info("earnings_scan_complete", count=len(earnings_results))
        
        news_scanner = NewsScanner(fmp, finnhub)
        news_results = news_scanner.scan(all_tickers)
        log.info("news_scan_complete", count=len(news_results))
        
        momentum_scanner = MomentumScanner(fmp)
        momentum_results = momentum_scanner.scan(all_tickers)
        log.info("momentum_scan_complete", count=len(momentum_results))
        
        # Analyze with Claude
        log.info("running_claude_analysis")
        analyzer = ClaudeAnalyzer()
        analysis = analyzer.analyze(
            earnings=earnings_results,
            news=news_results,
            momentum=momentum_results,
            watchlist=watchlist
        )
        log.info("analysis_complete", 
                 opportunities=len(analysis.get('top_opportunities', [])))
        
        # Generate PDF
        LOGS_DIR.mkdir(exist_ok=True)
        pdf_filename = f"market-scan-{datetime.now().strftime('%Y-%m-%d')}.pdf"
        pdf_path = LOGS_DIR / pdf_filename
        generate_pdf_report(analysis, str(pdf_path))
        log.info("pdf_generated", path=str(pdf_path))
        
        # Upload to Google Drive
        drive_link = None
        if UPLOAD_TO_GDRIVE:
            uploader = GoogleDriveUploader()
            result = uploader.upload_report(str(pdf_path))
            drive_link = result['link']
            log.info("uploaded_to_drive", link=drive_link)
        
        # Send email with Drive link
        if SEND_EMAIL and drive_link:
            send_scan_email(analysis, drive_link)
            log.info("email_sent")
        
        # Done
        duration = (datetime.now() - start_time).total_seconds()
        log.info("scan_completed", duration_seconds=round(duration, 1))
        
        return analysis
        
    except Exception as e:
        log.error("scan_failed", error=str(e), error_type=type(e).__name__)
        raise


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Market Scanner")
    parser.add_argument("--dry-run", action="store_true", 
                        help="Generate PDF but skip upload/email")
    args = parser.parse_args()
    
    if args.dry_run:
        import src.config as config
        config.UPLOAD_TO_GDRIVE = False
        config.SEND_EMAIL = False
        log.info("dry_run_mode")
    
    run_scan()


if __name__ == "__main__":
    main()
```

---

## 14. Error Handling

### 14.1 API Error Handling

```python
# src/fetchers/base.py
import time
import requests
from functools import wraps
import structlog

log = structlog.get_logger()


class APIError(Exception):
    """Base API error."""
    pass


class RateLimitError(APIError):
    """Rate limit exceeded."""
    pass


class QuotaExceededError(APIError):
    """Daily quota exceeded."""
    pass


def retry_with_backoff(max_retries=3, base_delay=1):
    """Decorator for exponential backoff retry."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except RateLimitError as e:
                    last_exception = e
                    delay = base_delay * (2 ** attempt)
                    log.warning("rate_limited", attempt=attempt + 1, delay=delay)
                    time.sleep(delay)
                except requests.exceptions.Timeout as e:
                    last_exception = e
                    delay = base_delay * (2 ** attempt)
                    log.warning("request_timeout", attempt=attempt + 1, delay=delay)
                    time.sleep(delay)
            
            raise last_exception
        return wrapper
    return decorator
```

### 14.2 Graceful Degradation

```python
def run_scan():
    """Execute scan with graceful degradation."""
    
    results = {
        "earnings": [],
        "news": [],
        "momentum": []
    }
    
    # Try each scanner independently
    try:
        results["earnings"] = earnings_scanner.scan(all_tickers)
    except QuotaExceededError:
        log.warning("earnings_scan_skipped", reason="FMP quota exceeded")
    
    try:
        results["news"] = news_scanner.scan(all_tickers)
    except Exception as e:
        log.warning("news_scan_failed", error=str(e))
    
    try:
        results["momentum"] = momentum_scanner.scan(all_tickers)
    except Exception as e:
        log.warning("momentum_scan_failed", error=str(e))
    
    # Only fail if ALL scanners failed
    if not any(results.values()):
        raise RuntimeError("All scanners failed, no data to analyze")
    
    # Continue with whatever data we have
    return analyzer.analyze(**results)
```

---

## 15. Testing

### 15.1 Test with Mock Data

```python
# tests/test_scanners.py
import pytest
from src.scanners.earnings import EarningsScanner
from tests.mock_data import MOCK_EARNINGS_CALENDAR


class MockFMPClient:
    def get_earnings_calendar(self, from_date, to_date):
        return MOCK_EARNINGS_CALENDAR


def test_earnings_scanner_filters_watchlist():
    watchlist = ["NVDA", "AMD", "AAPL"]
    scanner = EarningsScanner(MockFMPClient())
    
    results = scanner.scan(watchlist)
    
    # Should only return tickers in watchlist
    result_tickers = [r["symbol"] for r in results]
    assert all(t in watchlist for t in result_tickers)
```

### 15.2 Integration Test Script

```bash
#!/bin/bash
# test_integration.sh

echo "Running integration test..."

# Set test environment
export SEND_EMAIL=false
export LOG_LEVEL=DEBUG

# Run scan
python -m src.main --dry-run

# Check exit code
if [ $? -eq 0 ]; then
    echo "✓ Integration test passed"
else
    echo "✗ Integration test failed"
    exit 1
fi
```

---

## 16. Deployment Checklist

### One-Time Setup (~20 min)

**API Keys:**
- [ ] FMP account created → API key copied
- [ ] Finnhub account created → API key copied
- [ ] Anthropic account created → API key copied
- [ ] Resend account created → API key copied

**Google Cloud Setup:**
- [ ] GCP project created
- [ ] Google Drive API enabled
- [ ] Service account created
- [ ] JSON key downloaded
- [ ] JSON converted to single line for GitHub secret

**Google Drive Setup:**
- [ ] "Market Scanner" folder created in Drive
- [ ] Folder shared with service account email (Editor)
- [ ] Folder ID copied from URL

### GitHub Setup

- [ ] Code pushed to GitHub repo
- [ ] `.github/workflows/daily-scan.yml` created
- [ ] All secrets added in Settings → Secrets → Actions:
  - [ ] `FMP_API_KEY`
  - [ ] `FINNHUB_API_KEY`
  - [ ] `ANTHROPIC_API_KEY`
  - [ ] `GDRIVE_ROOT_FOLDER_ID`
  - [ ] `GOOGLE_SERVICE_ACCOUNT_JSON`
  - [ ] `RESEND_API_KEY`
  - [ ] `ALERT_EMAIL`

### Testing

- [ ] Manual workflow trigger (Actions → Run workflow)
- [ ] Workflow completes successfully (green checkmark)
- [ ] PDF appears in Google Drive (correct folder structure)
- [ ] Email received with Drive link
- [ ] Link opens PDF correctly

### Post-Deployment

- [ ] Wait for first scheduled run (6 AM ET)
- [ ] Verify automated run works
- [ ] Check GitHub sends failure notification emails (if any issues)

---

## 17. Cost Estimation

### Monthly Costs

| Service | Usage | Cost |
|---------|-------|------|
| GitHub Actions | ~50 min/month | **Free** (2,000 min limit) |
| Google Drive | ~1 MB/month | **Free** (15 GB limit) |
| Resend | ~22 emails/month | **Free** (3,000/month limit) |
| FMP API | ~30 calls/day | **Free** (250/day limit) |
| Finnhub API | ~40 calls/day | **Free** (60/min limit) |
| Claude API | ~22 calls/month | **~$1-2** |

**Total: ~$1-2/month** (only Claude API costs money)

---

## 18. Future Enhancements

1. **Slack/Discord alerts** - Real-time notifications for high-conviction setups
2. **Historical tracking** - Log all recommendations, track win rate
3. **Intraday re-scans** - Run again at 9:30 AM if major news breaks
4. **Custom watchlist UI** - Web interface to manage tickers
5. **Backtesting** - Test Claude's recommendations against historical data

---

## Appendix A: API Key Setup

### FMP (Financial Modeling Prep)
1. Go to https://financialmodelingprep.com
2. Sign up for free account
3. Dashboard → API Keys → Copy key

### Finnhub
1. Go to https://finnhub.io
2. Sign up for free account
3. Dashboard → API Keys → Copy key

### Anthropic
1. Go to https://console.anthropic.com
2. Sign up / Log in
3. API Keys → Create Key → Copy key

### Resend
1. Go to https://resend.com/signup
2. Create account
3. Dashboard → API Keys → Create → Copy key
4. (Optional) Add and verify custom domain for branded emails

---

## Appendix B: Cron Expression Reference

```
┌───────────── minute (0-59)
│ ┌───────────── hour (0-23)
│ │ ┌───────────── day of month (1-31)
│ │ │ ┌───────────── month (1-12)
│ │ │ │ ┌───────────── day of week (0-6, Sun=0)
│ │ │ │ │
* * * * *
```

**Examples:**
- `0 11 * * 1-5` = 11:00 UTC (6:00 AM ET), Monday-Friday
- `0 11 * * *` = 11:00 UTC, every day
- `30 10 * * 1-5` = 10:30 UTC (5:30 AM ET), Monday-Friday

**Time Zone Conversion:**
- 6:00 AM ET = 11:00 UTC (EST, winter)
- 6:00 AM ET = 10:00 UTC (EDT, summer)

Railway uses UTC. Adjust cron expression for daylight saving time manually, or use a timezone-aware scheduler.

---

## Appendix C: Sample API Responses

### FMP Earnings Calendar Response
```json
[
  {
    "date": "2026-02-26",
    "symbol": "NVDA",
    "eps": null,
    "epsEstimated": 0.84,
    "time": "bmo",
    "revenue": null,
    "revenueEstimated": 38200000000,
    "fiscalDateEnding": "2026-01-31",
    "updatedFromDate": "2026-01-15"
  }
]
```

### FMP Batch Quote Response
```json
[
  {
    "symbol": "NVDA",
    "name": "NVIDIA Corporation",
    "price": 142.50,
    "changesPercentage": 2.35,
    "change": 3.27,
    "dayLow": 138.20,
    "dayHigh": 143.80,
    "yearHigh": 152.89,
    "yearLow": 85.62,
    "marketCap": 3520000000000,
    "volume": 45000000,
    "avgVolume": 38000000
  }
]
```

### Finnhub Company News Response
```json
[
  {
    "category": "company",
    "datetime": 1706500000,
    "headline": "NVIDIA Announces New AI Chip Partnership",
    "id": 123456,
    "image": "https://...",
    "related": "NVDA",
    "source": "Reuters",
    "summary": "NVIDIA announced a strategic partnership...",
    "url": "https://..."
  }
]
```