"""Macro Event Calendar - Fed, CPI, Jobs, Major Earnings."""

import requests
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel, Field

from ..config import FINNHUB_API_KEY, FINNHUB_BASE_URL


class MacroEvent(BaseModel):
    """Macro economic event."""
    date: str
    event: str
    impact: str  # "high", "medium", "low"
    description: str = ""


class EarningsEvent(BaseModel):
    """Major earnings that could move sectors."""
    date: str
    symbol: str
    company: str
    sector_impact: List[str] = Field(default_factory=list)  # Which sectors this affects


class MacroCalendar:
    """Scans for upcoming macro events and major earnings."""

    def __init__(self):
        # High-impact earnings that move entire sectors
        self.sector_movers = {
            "NVDA": ["ai_semiconductors", "ai_infrastructure", "ai_software"],
            "AMD": ["ai_semiconductors"],
            "MSFT": ["ai_software", "ai_infrastructure"],
            "GOOGL": ["ai_software", "ai_infrastructure"],
            "AMZN": ["ai_software", "ai_infrastructure"],
            "META": ["ai_software"],
            "AAPL": ["ai_semiconductors"],
            "TSLA": ["robotics_defense"],
            "LMT": ["defense_aerospace"],
            "RTX": ["defense_aerospace"],
            "CCJ": ["nuclear_energy"],
        }

    def get_economic_calendar(self, days_ahead: int = 7) -> List[MacroEvent]:
        """Get upcoming economic events from Finnhub."""
        events = []
        
        try:
            today = datetime.now()
            end_date = today + timedelta(days=days_ahead)
            
            url = f"{FINNHUB_BASE_URL}/calendar/economic"
            params = {
                "from": today.strftime("%Y-%m-%d"),
                "to": end_date.strftime("%Y-%m-%d"),
                "token": FINNHUB_API_KEY
            }
            
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()
            
            if "economicCalendar" in data:
                for item in data["economicCalendar"]:
                    # Filter for US and high-impact events
                    country = item.get("country", "")
                    impact = item.get("impact", "").lower()
                    
                    if country == "US" and impact in ["high", "medium"]:
                        event_name = item.get("event", "")
                        
                        # Flag key events
                        is_fed = any(x in event_name.lower() for x in ["fomc", "fed", "interest rate", "powell"])
                        is_jobs = any(x in event_name.lower() for x in ["nonfarm", "employment", "jobless", "unemployment"])
                        is_inflation = any(x in event_name.lower() for x in ["cpi", "ppi", "inflation", "pce"])
                        is_gdp = "gdp" in event_name.lower()
                        
                        # Only include major events
                        if is_fed or is_jobs or is_inflation or is_gdp or impact == "high":
                            description = ""
                            if is_fed:
                                description = "⚠️ Fed event - HIGH volatility expected, all bets risky"
                            elif is_inflation:
                                description = "⚠️ Inflation data - Can reverse market direction"
                            elif is_jobs:
                                description = "⚠️ Jobs data - Market moving event"
                            
                            events.append(MacroEvent(
                                date=item.get("time", "")[:10],
                                event=event_name,
                                impact="high" if (is_fed or is_inflation or is_jobs) else impact,
                                description=description
                            ))
            
        except Exception as e:
            print(f"[Warning] Failed to get economic calendar: {e}")
        
        # Sort by date
        events.sort(key=lambda x: x.date)
        
        return events

    def get_major_earnings(self, days_ahead: int = 7) -> List[EarningsEvent]:
        """Get upcoming earnings that could move sectors."""
        events = []
        
        try:
            today = datetime.now()
            end_date = today + timedelta(days=days_ahead)
            
            url = f"{FINNHUB_BASE_URL}/calendar/earnings"
            params = {
                "from": today.strftime("%Y-%m-%d"),
                "to": end_date.strftime("%Y-%m-%d"),
                "token": FINNHUB_API_KEY
            }
            
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()
            
            if "earningsCalendar" in data:
                for item in data["earningsCalendar"]:
                    symbol = item.get("symbol", "")
                    
                    # Only include sector-moving earnings
                    if symbol in self.sector_movers:
                        events.append(EarningsEvent(
                            date=item.get("date", ""),
                            symbol=symbol,
                            company=symbol,  # Could fetch name but keeping simple
                            sector_impact=self.sector_movers[symbol]
                        ))
            
        except Exception as e:
            print(f"[Warning] Failed to get earnings calendar: {e}")
        
        # Sort by date
        events.sort(key=lambda x: x.date)
        
        return events

    def get_landmines(self, days_ahead: int = 5) -> dict:
        """Get all upcoming 'landmines' - events that could blow up any thesis."""
        return {
            "economic_events": self.get_economic_calendar(days_ahead),
            "sector_moving_earnings": self.get_major_earnings(days_ahead)
        }

    def format_warnings(self, days_ahead: int = 5) -> str:
        """Format landmines as warnings for Claude."""
        landmines = self.get_landmines(days_ahead)
        
        lines = []
        
        # Economic events
        econ = landmines["economic_events"]
        if econ:
            lines.append("⚠️ MACRO LANDMINES (Economic Events):")
            for e in econ[:5]:  # Top 5
                lines.append(f"  {e.date}: {e.event}")
                if e.description:
                    lines.append(f"    {e.description}")
        
        # Sector-moving earnings
        earnings = landmines["sector_moving_earnings"]
        if earnings:
            lines.append("\n⚠️ SECTOR-MOVING EARNINGS:")
            for e in earnings[:5]:  # Top 5
                sectors = ", ".join(e.sector_impact)
                lines.append(f"  {e.date}: {e.symbol} - Impacts: {sectors}")
        
        if not lines:
            return "No major macro events in the next 5 days."
        
        return "\n".join(lines)
