"""Configuration for Market Scanner."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR.parent / "logs"

# API Keys (reuse from stocker)
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
FMP_API_KEY = os.getenv("FMP_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# API Base URLs
FINNHUB_BASE_URL = "https://finnhub.io/api/v1"
FMP_BASE_URL = "https://financialmodelingprep.com/stable"

# Scanner settings
EARNINGS_LOOKAHEAD_DAYS = 7
SCAN_LOOKBACK_HOURS = 24
VOLUME_THRESHOLD = 1.5  # 1.5x average volume
PRICE_CHANGE_THRESHOLD = 3.0  # 3% price change

# Email (Resend)
SEND_EMAIL = os.getenv("SEND_EMAIL", "false").lower() == "true"
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
ALERT_EMAIL = os.getenv("ALERT_EMAIL")

# Google Drive (disabled - service accounts don't work with personal Drive)
UPLOAD_TO_GDRIVE = False
GDRIVE_ROOT_FOLDER_ID = None
GOOGLE_SERVICE_ACCOUNT_JSON = None


def validate_config() -> list:
    """Check required config and return list of missing items."""
    missing = []
    if not FINNHUB_API_KEY:
        missing.append("FINNHUB_API_KEY")
    if not FMP_API_KEY:
        missing.append("FMP_API_KEY")
    if not ANTHROPIC_API_KEY:
        missing.append("ANTHROPIC_API_KEY")
    return missing
