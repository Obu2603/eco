from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
import io

def generate_pdf_report(location_data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.blue,
        spaceAfter=20
    )
    elements.append(Paragraph(f"EcoVision AI+ Sustainability Report", title_style))
    elements.append(Paragraph(f"Project: {location_data.name}", styles['Heading2']))
    elements.append(Spacer(1, 12))

    # Location Info
    elements.append(Paragraph("<b>Location Details</b>", styles['Heading3']))
    loc_info = [
        ["Latitude", f"{location_data.latitude:.4f}"],
        ["Longitude", f"{location_data.longitude:.4f}"],
        ["City", getattr(location_data, 'city', 'N/A')],
        ["Date", location_data.created_at.strftime("%Y-%m-%d %H:%M:%S")]
    ]
    t = Table(loc_info, colWidths=[150, 300])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.whitesmoke),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 20))

    # Environmental Data
    if location_data.environmental_data:
        env = location_data.environmental_data
        elements.append(Paragraph("<b>Analysis Metrics</b>", styles['Heading3']))
        env_info = [
            ["Metric", "Value"],
            ["TOPSIS Score", f"{env.topsis_score:.4f}"],
            ["Classification", env.sustainability_class],
            ["AQI", f"{env.aqi}"],
            ["Carbon Emissions (Est)", f"{env.predicted_carbon_emissions} tons/yr"],
            ["Green Cover (%)", f"{env.green_cover_pct}%"],
            ["Building Density", f"{env.building_density}"],
            ["Material Reuse (%)", f"{env.material_reuse_pct or 0}%"]
        ]
        et = Table(env_info, colWidths=[200, 250])
        et.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.blue),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(et)
        elements.append(Spacer(1, 20))

        # Recommendations
        elements.append(Paragraph("<b>AI Recommendations</b>", styles['Heading3']))
        recs = env.recommendation.split('|')
        for rec in recs:
            elements.append(Paragraph(f"• {rec.strip()}", styles['BodyText']))
            elements.append(Spacer(1, 6))

    doc.build(elements)
    buffer.seek(0)
    return buffer
