"""Email Sender using Resend for Market Scanner notifications."""

import os
import base64
from datetime import datetime
from typing import Optional
from pathlib import Path

from ..config import RESEND_API_KEY, ALERT_EMAIL, SEND_EMAIL
from ..models import ScanAnalysis


def send_scan_email(analysis: ScanAnalysis, pdf_path: Optional[str] = None) -> Optional[dict]:
    """Send email with summary and PDF attachment."""
    
    if not SEND_EMAIL:
        print("[Info] Email sending disabled")
        return None
    
    if not RESEND_API_KEY or not ALERT_EMAIL:
        print("[Warning] Resend API key or alert email not configured")
        return None
    
    try:
        import resend
        resend.api_key = RESEND_API_KEY
        
        # Subject line
        date_str = datetime.now().strftime("%b %d")
        top_picks = analysis.top_opportunities
        top_ticker = top_picks[0].ticker if top_picks else "N/A"
        subject = f"Market Scan {date_str} | Top: {top_ticker}"
        
        # Build picks HTML
        if top_picks:
            picks_html = ""
            for i, p in enumerate(top_picks[:3], 1):
                picks_html += f"""
                <tr>
                    <td style="padding: 8px 0; border-bottom: 1px solid #eee;">
                        <strong>#{i} {p.ticker}</strong> - {p.company}<br>
                        <span style="color: #666; font-size: 13px;">
                            {p.setup_type} | Conviction: {p.conviction}/10
                        </span><br>
                        <span style="font-size: 13px;">{p.catalyst}</span>
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
            
            <p style="color: #333; font-size: 14px;">
                📎 Full PDF report attached below.
            </p>
            
            <p style="color: #999; font-size: 11px; margin-top: 30px;">
                This is an automated scan. Not financial advice. Do your own research.
            </p>
        </body>
        </html>
        """
        
        # Build email params
        email_params = {
            "from": "Market Scanner <onboarding@resend.dev>",
            "to": [ALERT_EMAIL],
            "subject": subject,
            "html": html
        }
        
        # Attach PDF if provided
        if pdf_path and Path(pdf_path).exists():
            with open(pdf_path, "rb") as f:
                pdf_content = base64.b64encode(f.read()).decode("utf-8")
            
            email_params["attachments"] = [{
                "filename": Path(pdf_path).name,
                "content": pdf_content
            }]
            print(f"[Info] Attaching PDF: {Path(pdf_path).name}")
        
        response = resend.Emails.send(email_params)
        
        print(f"[Info] Email sent to {ALERT_EMAIL}")
        return response
        
    except ImportError:
        print("[Warning] Resend package not installed. Run: pip install resend")
        return None
    except Exception as e:
        print(f"[Error] Failed to send email: {e}")
        return None
