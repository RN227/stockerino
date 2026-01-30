"""Options Flow Scanner using Yahoo Finance."""

import yfinance as yf
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel, Field


class OptionsSignal(BaseModel):
    """Unusual options activity signal."""
    symbol: str
    expiry: str
    strike: float
    option_type: str  # call or put
    volume: int
    open_interest: int
    volume_oi_ratio: float  # Volume / Open Interest
    implied_volatility: Optional[float] = None
    last_price: Optional[float] = None
    signal_type: str  # "unusual_volume", "high_iv", "call_sweep", "put_sweep"
    signal_strength: str  # "strong", "moderate"


class OptionsScanner:
    """Scans for unusual options activity."""

    def __init__(self):
        self.min_volume = 100  # Minimum volume to consider
        self.min_oi = 50  # Minimum open interest
        self.unusual_vol_oi_ratio = 1.0  # V/OI > 1 is unusual
        self.high_vol_oi_ratio = 2.0  # V/OI > 2 is very unusual
        self.max_expiry_days = 30  # Focus on near-term options

    def scan(self, tickers: List[str]) -> List[OptionsSignal]:
        """Scan tickers for unusual options activity."""
        all_signals = []
        
        for ticker in tickers:
            try:
                signals = self._scan_ticker(ticker)
                all_signals.extend(signals)
            except Exception as e:
                print(f"[Warning] Options scan failed for {ticker}: {e}")
                continue
        
        # Sort by volume/OI ratio (most unusual first)
        all_signals.sort(key=lambda x: x.volume_oi_ratio, reverse=True)
        
        return all_signals

    def _scan_ticker(self, ticker: str) -> List[OptionsSignal]:
        """Scan single ticker for unusual options activity."""
        signals = []
        
        stock = yf.Ticker(ticker)
        
        # Get available expiration dates
        try:
            expirations = stock.options
        except:
            return []
        
        if not expirations:
            return []
        
        # Filter to near-term expirations (next 30 days)
        today = datetime.now().date()
        max_expiry = today + timedelta(days=self.max_expiry_days)
        
        near_term_expiries = []
        for exp in expirations[:5]:  # Check first 5 expiries
            try:
                exp_date = datetime.strptime(exp, "%Y-%m-%d").date()
                if exp_date <= max_expiry:
                    near_term_expiries.append(exp)
            except:
                continue
        
        # Scan each near-term expiry
        for expiry in near_term_expiries:
            try:
                chain = stock.option_chain(expiry)
                
                # Scan calls
                calls_signals = self._scan_chain(ticker, expiry, chain.calls, "call")
                signals.extend(calls_signals)
                
                # Scan puts
                puts_signals = self._scan_chain(ticker, expiry, chain.puts, "put")
                signals.extend(puts_signals)
                
            except Exception as e:
                continue
        
        return signals

    def _scan_chain(self, ticker: str, expiry: str, chain_df, option_type: str) -> List[OptionsSignal]:
        """Scan options chain for unusual activity."""
        signals = []
        
        if chain_df is None or chain_df.empty:
            return []
        
        for _, row in chain_df.iterrows():
            volume = int(row.get('volume', 0) or 0)
            open_interest = int(row.get('openInterest', 0) or 0)
            
            # Skip low activity options
            if volume < self.min_volume or open_interest < self.min_oi:
                continue
            
            # Calculate volume/OI ratio
            vol_oi_ratio = volume / open_interest if open_interest > 0 else 0
            
            # Check if unusual
            if vol_oi_ratio < self.unusual_vol_oi_ratio:
                continue
            
            # Determine signal type and strength
            if vol_oi_ratio >= self.high_vol_oi_ratio:
                signal_type = f"{option_type}_sweep"
                signal_strength = "strong"
            else:
                signal_type = "unusual_volume"
                signal_strength = "moderate"
            
            # Get IV if available
            iv = row.get('impliedVolatility')
            if iv and iv > 0:
                iv = round(iv * 100, 1)  # Convert to percentage
            else:
                iv = None
            
            signals.append(OptionsSignal(
                symbol=ticker,
                expiry=expiry,
                strike=float(row['strike']),
                option_type=option_type,
                volume=volume,
                open_interest=open_interest,
                volume_oi_ratio=round(vol_oi_ratio, 2),
                implied_volatility=iv,
                last_price=float(row.get('lastPrice', 0) or 0),
                signal_type=signal_type,
                signal_strength=signal_strength
            ))
        
        return signals

    def get_call_put_ratio(self, tickers: List[str]) -> dict:
        """Calculate call/put volume ratio for tickers."""
        ratios = {}
        
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                expirations = stock.options
                
                if not expirations:
                    continue
                
                total_call_vol = 0
                total_put_vol = 0
                
                # Check first 2 expiries for recent sentiment
                for exp in expirations[:2]:
                    try:
                        chain = stock.option_chain(exp)
                        total_call_vol += chain.calls['volume'].sum() or 0
                        total_put_vol += chain.puts['volume'].sum() or 0
                    except:
                        continue
                
                if total_put_vol > 0:
                    ratios[ticker] = round(total_call_vol / total_put_vol, 2)
                elif total_call_vol > 0:
                    ratios[ticker] = float('inf')  # All calls, no puts
                    
            except Exception as e:
                continue
        
        return ratios
