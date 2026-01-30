"""PDF Report Generator using ReportLab."""

from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.units import inch

from ..models import ScanAnalysis


def generate_pdf_report(analysis: ScanAnalysis, output_path: str) -> str:
    """Generate PDF report from scan analysis."""
    
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch
    )
    
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
        name='SubTitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#666666'),
        spaceAfter=20
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
        name='ScanBodyText',
        parent=styles['Normal'],
        fontSize=10,
        spaceBefore=3,
        spaceAfter=3,
        leading=14
    ))
    
    styles.add(ParagraphStyle(
        name='ConvictionText',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#2e7d32')
    ))
    
    styles.add(ParagraphStyle(
        name='RiskText',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#c62828')
    ))
    
    story = []
    
    # Title
    story.append(Paragraph("MARKET SCANNER REPORT", styles['ReportTitle']))
    story.append(Paragraph(
        f"{datetime.now().strftime('%B %d, %Y')} | Pre-Market Analysis",
        styles['SubTitle']
    ))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#1a1a2e')))
    
    # Top Opportunities
    story.append(Paragraph("TOP OPPORTUNITIES", styles['SectionHeader']))
    
    if analysis.top_opportunities:
        for opp in analysis.top_opportunities:
            # Conviction bar
            conviction_bar = "█" * opp.conviction + "░" * (10 - opp.conviction)
            
            story.append(Paragraph(
                f"#{opp.rank} {opp.ticker} - {opp.company}",
                styles['TickerHeader']
            ))
            
            story.append(Paragraph(
                f"<b>Type:</b> {opp.setup_type} &nbsp;&nbsp;|&nbsp;&nbsp; "
                f"<b>Conviction:</b> {conviction_bar} {opp.conviction}/10",
                styles['ScanBodyText']
            ))
            
            story.append(Paragraph(f"<b>Catalyst:</b> {opp.catalyst}", styles['ScanBodyText']))
            story.append(Paragraph(f"<b>Thesis:</b> {opp.thesis}", styles['ScanBodyText']))
            story.append(Paragraph(f"<b>Trade Setup:</b> {opp.trade_setup}", styles['ScanBodyText']))
            story.append(Paragraph(f"<b>Key Risk:</b> {opp.key_risk}", styles['RiskText']))
            
            story.append(Spacer(1, 10))
    else:
        story.append(Paragraph("No actionable opportunities identified today.", styles['ScanBodyText']))
    
    # Watchlist
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cccccc')))
    story.append(Paragraph("WATCHLIST", styles['SectionHeader']))
    
    if analysis.watchlist:
        for item in analysis.watchlist:
            story.append(Paragraph(
                f"• <b>{item.ticker}:</b> {item.reason}",
                styles['ScanBodyText']
            ))
    else:
        story.append(Paragraph("No watchlist items.", styles['ScanBodyText']))
    
    # No Action
    if analysis.no_action:
        story.append(Spacer(1, 10))
        story.append(Paragraph("NO ACTION", styles['SectionHeader']))
        for item in analysis.no_action:
            story.append(Paragraph(
                f"• <b>{item.ticker}:</b> {item.reason}",
                styles['ScanBodyText']
            ))
    
    # Sector Summary
    story.append(Spacer(1, 15))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cccccc')))
    story.append(Paragraph("SECTOR SUMMARY", styles['SectionHeader']))
    
    sector_icons = {"Bullish": "▲", "Neutral": "─", "Cautious": "▼", "Bearish": "▼"}
    sector_colors = {
        "Bullish": colors.HexColor('#2e7d32'),
        "Neutral": colors.HexColor('#666666'),
        "Cautious": colors.HexColor('#f57c00'),
        "Bearish": colors.HexColor('#c62828')
    }
    
    for sector, summary in analysis.sector_summary.items():
        display_name = sector.replace("_", " ").title()
        
        # Handle both old string format and new SectorSummary object
        if hasattr(summary, 'outlook'):
            outlook = summary.outlook
            overview = summary.overview
            news_items = summary.news if hasattr(summary, 'news') else []
        else:
            # Fallback for old string format
            outlook = str(summary).split(" - ")[0] if " - " in str(summary) else "Neutral"
            overview = str(summary)
            news_items = []
        
        icon = sector_icons.get(outlook, "─")
        color = sector_colors.get(outlook, colors.HexColor('#666666'))
        
        # Sector header with outlook
        story.append(Paragraph(
            f"<b>{display_name}</b> — <font color='{color.hexval()}'>{outlook} {icon}</font>",
            styles['TickerHeader']
        ))
        
        # Overview
        if overview:
            story.append(Paragraph(overview, styles['ScanBodyText']))
        
        # News links
        if news_items:
            for news in news_items[:3]:
                story.append(Paragraph(
                    f"• <link href='{news.url}'><font color='#1565c0'>{news.title}</font></link>",
                    styles['ScanBodyText']
                ))
        
        story.append(Spacer(1, 8))
    
    # Footer
    story.append(Spacer(1, 30))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#eeeeee')))
    story.append(Paragraph(
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
        "This is an automated scan. Not financial advice.",
        ParagraphStyle(
            name='Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#999999'),
            spaceBefore=10
        )
    ))
    
    # Build PDF
    doc.build(story)
    
    return output_path
