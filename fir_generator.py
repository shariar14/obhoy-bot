"""
OBHOY — FIR Draft Generator
Generates a legally formatted First Information Report
in Bangla for Bangladesh Police
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import os

def generate_fir_pdf(answers: dict, output_path: str) -> str:
    """
    Generate a PDF FIR document from survivor answers
    
    answers dict keys:
    - victim_age: age of victim
    - incident_date: when it happened
    - incident_time: time of day
    - incident_location: district and area
    - perpetrator_relation: relationship to victim
    - description: what happened
    - witness: any witnesses
    - previous_report: any previous report filed
    - contact_district: victim's district
    """
    
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Normal'],
        fontSize=16,
        fontName='Helvetica-Bold',
        alignment=1,  # Center
        spaceAfter=6,
        textColor=colors.HexColor('#0D2B5E')
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        fontName='Helvetica-Bold',
        alignment=1,
        spaceAfter=4,
        textColor=colors.HexColor('#1A56A4')
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Normal'],
        fontSize=11,
        fontName='Helvetica-Bold',
        spaceAfter=4,
        textColor=colors.HexColor('#0D2B5E')
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica',
        spaceAfter=4,
        leading=14
    )
    
    small_style = ParagraphStyle(
        'CustomSmall',
        parent=styles['Normal'],
        fontSize=9,
        fontName='Helvetica',
        textColor=colors.grey
    )
    
    # Build content
    content = []
    now = datetime.now()
    
    # ── HEADER ──────────────────────────────────────────
    content.append(Paragraph("OBHOY (ABHOY) FOUNDATION", title_style))
    content.append(Paragraph("Sexual Violence Prevention & Justice Platform", subtitle_style))
    content.append(Paragraph("obhoy.com | bolun@obhoy.com | @ObhoyBDbot", small_style))
    content.append(Spacer(1, 0.15*inch))
    
    # Divider line
    divider_data = [['─' * 90]]
    divider_table = Table(divider_data, colWidths=[7*inch])
    divider_table.setStyle(TableStyle([
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#1A56A4')),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))
    content.append(divider_table)
    content.append(Spacer(1, 0.1*inch))
    
    # Title
    content.append(Paragraph(
        "FIRST INFORMATION REPORT (FIR) DRAFT",
        title_style
    ))
    content.append(Paragraph(
        "প্রাথমিক তথ্য বিবরণী (এফআইআর) খসড়া",
        subtitle_style
    ))
    content.append(Paragraph(
        "Under: Women and Children Repression Prevention Act 2000 / Penal Code Section 376",
        small_style
    ))
    content.append(Spacer(1, 0.15*inch))
    
    # Reference info table
    ref_data = [
        ['Report Generated:', now.strftime('%d %B %Y, %I:%M %p'),
         'Report ID:', f'OBH-{now.strftime("%Y%m%d%H%M%S")}'],
        ['District:', answers.get('contact_district', 'Not specified'),
         'Status:', 'DRAFT — Needs Police Filing'],
    ]
    ref_table = Table(ref_data, colWidths=[1.5*inch, 2*inch, 1.2*inch, 2.3*inch])
    ref_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F4F6F8')),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (2,0), (2,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CCCCCC')),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    content.append(ref_table)
    content.append(Spacer(1, 0.2*inch))
    
    # ── SECTION 1: INCIDENT DETAILS ─────────────────────
    content.append(Paragraph("SECTION 1: INCIDENT DETAILS", heading_style))
    
    incident_data = [
        ['Field', 'Information Provided'],
        ['Date of Incident', answers.get('incident_date', 'Not specified')],
        ['Time of Incident', answers.get('incident_time', 'Not specified')],
        ['Location of Incident', answers.get('incident_location', 'Not specified')],
        ['District', answers.get('contact_district', 'Not specified')],
    ]
    
    incident_table = Table(incident_data, colWidths=[2.5*inch, 4.5*inch])
    incident_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0D2B5E')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTNAME', (0,1), (0,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CCCCCC')),
        ('PADDING', (0,0), (-1,-1), 8),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), 
         [colors.HexColor('#F4F6F8'), colors.white]),
    ]))
    content.append(incident_table)
    content.append(Spacer(1, 0.15*inch))
    
    # ── SECTION 2: VICTIM INFORMATION ───────────────────
    content.append(Paragraph("SECTION 2: VICTIM INFORMATION", heading_style))
    
    victim_data = [
        ['Field', 'Information Provided'],
        ['Victim Age', answers.get('victim_age', 'Not specified')],
        ['Relationship to Perpetrator', answers.get('perpetrator_relation', 'Not specified')],
        ['Any Witnesses Present', answers.get('witness', 'Not specified')],
        ['Previous Report Filed', answers.get('previous_report', 'No')],
    ]
    
    victim_table = Table(victim_data, colWidths=[2.5*inch, 4.5*inch])
    victim_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0D2B5E')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTNAME', (0,1), (0,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CCCCCC')),
        ('PADDING', (0,0), (-1,-1), 8),
        ('ROWBACKGROUNDS', (0,1), (-1,-1),
         [colors.HexColor('#F4F6F8'), colors.white]),
    ]))
    content.append(victim_table)
    content.append(Spacer(1, 0.15*inch))
    
    # ── SECTION 3: INCIDENT DESCRIPTION ─────────────────
    content.append(Paragraph("SECTION 3: INCIDENT DESCRIPTION", heading_style))
    
    desc_data = [
        ['Description of Incident (as provided by survivor):'],
        [answers.get('description', 'No description provided')],
    ]
    desc_table = Table(desc_data, colWidths=[7*inch])
    desc_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0D2B5E')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CCCCCC')),
        ('PADDING', (0,0), (-1,-1), 8),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#FFF9F9')),
        ('VALIGN', (0,1), (-1,1), 'TOP'),
        ('MINROWHEIGHT', (0,1), (-1,1), 1*inch),
    ]))
    content.append(desc_table)
    content.append(Spacer(1, 0.15*inch))
    
    # ── SECTION 4: LEGAL BASIS ───────────────────────────
    content.append(Paragraph("SECTION 4: APPLICABLE LAWS", heading_style))
    
    law_data = [
        ['Law', 'Section', 'Punishment'],
        ['Women & Children Repression\nPrevention Act 2000',
         'Section 9(1)', 'Life imprisonment + fine'],
        ['Penal Code Bangladesh',
         'Section 376', 'Min 7 years to life imprisonment'],
        ['Women & Children Act 2000\n(if victim under 18)',
         'Section 9(4)', 'Death penalty or life imprisonment'],
        ['Digital Security Act 2018\n(if online evidence)',
         'Section 26', '5 years + BDT 5 lakh fine'],
    ]
    
    law_table = Table(law_data, colWidths=[2.8*inch, 1.5*inch, 2.7*inch])
    law_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0D2B5E')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CCCCCC')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('ROWBACKGROUNDS', (0,1), (-1,-1),
         [colors.HexColor('#F4F6F8'), colors.white]),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    content.append(law_table)
    content.append(Spacer(1, 0.15*inch))
    
    # ── SECTION 5: NEXT STEPS ────────────────────────────
    content.append(Paragraph("SECTION 5: IMMEDIATE NEXT STEPS", heading_style))
    
    steps_data = [
        ['Step', 'Action', 'Contact'],
        ['1', 'Visit nearest police station with this document',
         'Emergency: 999'],
        ['2', 'Request a female police officer',
         'Women Support: 10921'],
        ['3', 'Get free legal help from BLAST',
         '01730-329945'],
        ['4', 'Get free legal help from ASK',
         '01730-029945'],
        ['5', 'Visit One Stop Crisis Centre for medical exam',
         'Dhaka OCC: 02-55165088'],
        ['6', 'National Legal Aid (free lawyer)',
         'Hotline: 16430'],
    ]
    
    steps_table = Table(steps_data, colWidths=[0.5*inch, 4*inch, 2.5*inch])
    steps_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A7A4A')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTNAME', (0,1), (0,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CCCCCC')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('ROWBACKGROUNDS', (0,1), (-1,-1),
         [colors.HexColor('#D6F0E4'), colors.white]),
        ('ALIGN', (0,0), (0,-1), 'CENTER'),
    ]))
    content.append(steps_table)
    content.append(Spacer(1, 0.2*inch))
    
    # ── DISCLAIMER ───────────────────────────────────────
    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontSize=8,
        fontName='Helvetica',
        textColor=colors.HexColor('#888888'),
        borderColor=colors.HexColor('#CCCCCC'),
        borderWidth=1,
        borderPadding=6,
        backColor=colors.HexColor('#F9F9F9'),
    )
    content.append(Paragraph(
        "IMPORTANT NOTICE: This is an auto-generated draft prepared by OBHOY to help survivors. "
        "This document is a supporting tool and does not replace an official FIR filed at a police station. "
        "The information in this document is kept strictly confidential by OBHOY. "
        "Survivor identity is never disclosed without explicit consent. "
        "For immediate danger call 999. For free legal help call 16430.",
        disclaimer_style
    ))
    
    content.append(Spacer(1, 0.15*inch))
    
    # Footer
    footer_data = [[
        'Generated by OBHOY Bot (@ObhoyBDbot)',
        f'Date: {now.strftime("%d/%m/%Y %H:%M")}',
        'obhoy.com'
    ]]
    footer_table = Table(footer_data, colWidths=[2.5*inch, 2.5*inch, 2*inch])
    footer_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#0D2B5E')),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.white),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    content.append(footer_table)
    
    # Build PDF
    doc.build(content)
    return output_path
```

**Step 4.** Scroll down → Click **Commit changes** → **Commit changes** again

---

## 🔷 PART 2 — Create the FIR Conversation Handler

**Step 1.** Go to:
```
github.com/shariar14/obhoy-bot/new/main
```

**Step 2.** Filename:
```
fir_handler.py
