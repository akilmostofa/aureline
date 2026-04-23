from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def build_pdf(title, subtitle=None, filters=None, headers=None, rows=None):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), leftMargin=1.2 * cm, rightMargin=1.2 * cm, topMargin=1.2 * cm, bottomMargin=1.2 * cm)
    styles = getSampleStyleSheet()
    story = [Paragraph(f"<b>{title}</b>", styles['Title'])]
    if subtitle:
        story.append(Paragraph(subtitle, styles['Normal']))
    if filters:
        story.append(Spacer(1, 0.2 * cm))
        filter_lines = "<br/>".join(f"<b>{label}:</b> {value}" for label, value in filters.items() if value not in (None, '', 'all'))
        if filter_lines:
            story.append(Paragraph(filter_lines, styles['BodyText']))
    story.append(Spacer(1, 0.5 * cm))

    table_data = [headers or []]
    for row in rows or []:
        table_data.append([str(value) if value is not None else "" for value in row])
    if len(table_data) == 1:
        table_data.append(["No records found."] + [""] * (len(table_data[0]) - 1))

    col_count = max(len(table_data[0]), 1)
    table = Table(table_data, repeatRows=1, colWidths=[26.0 / col_count * cm for _ in range(col_count)])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4e79')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.HexColor('#edf3fb')]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(table)
    doc.build(story)
    buffer.seek(0)
    return buffer
