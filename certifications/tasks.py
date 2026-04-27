import io
import logging
from django.core.files.base import ContentFile
from django.utils import timezone
import segno
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics import renderPDF

from .models import Certificate

logger = logging.getLogger(__name__)


def generate_certificate_pdf(certificate_id: str):
    """Génération certificat PDF SYNCHRONE."""
    try:
        cert = Certificate.objects.select_related('eleve', 'matiere', 'delivre_par').get(id=certificate_id)

        # Generate QR Code
        if not cert.qr_code:
            qr = segno.make(f"https://academie-numerique.com/certificates/verify/{cert.code_verification}/")
            buffer = io.BytesIO()
            qr.save(buffer, kind='png', scale=8)
            cert.qr_code.save(f'qr_cert_{cert.id}.png', ContentFile(buffer.getvalue()), save=False)

        # Generate PDF
        buffer = io.BytesIO()
        page_size = landscape(A4)
        doc = SimpleDocTemplate(
            buffer, pagesize=page_size,
            rightMargin=2*cm, leftMargin=2*cm,
            topMargin=2*cm, bottomMargin=2*cm,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('CertTitle', parent=styles['Title'], fontSize=32, textColor=colors.HexColor('#6366F1'), alignment=TA_CENTER, spaceAfter=10, fontName='Helvetica-Bold')
        subtitle_style = ParagraphStyle('CertSubtitle', parent=styles['Normal'], fontSize=16, textColor=colors.HexColor('#8B5CF6'), alignment=TA_CENTER, spaceAfter=20, fontName='Helvetica')
        body_style = ParagraphStyle('CertBody', parent=styles['Normal'], fontSize=14, alignment=TA_CENTER, spaceAfter=12, leading=20)
        name_style = ParagraphStyle('CertName', parent=styles['Normal'], fontSize=28, textColor=colors.HexColor('#4F46E5'), alignment=TA_CENTER, spaceAfter=8, fontName='Helvetica-Bold')
        detail_style = ParagraphStyle('CertDetail', parent=styles['Normal'], fontSize=12, textColor=colors.HexColor('#475569'), alignment=TA_CENTER, spaceAfter=6)
        footer_style = ParagraphStyle('CertFooter', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#94A3B8'), alignment=TA_CENTER)

        elements = []

        # Gold border
        elements.append(Spacer(1, 0.5*cm))

        # Header decoration
        elements.append(Paragraph("ACADÉMIE NUMÉRIQUE", ParagraphStyle('HeaderOrg', fontSize=12, textColor=colors.HexColor('#6366F1'), alignment=TA_CENTER, fontName='Helvetica', spaceAfter=4)))
        elements.append(Paragraph("Certificat Mondial de Composition et d'Évaluation", detail_style))
        elements.append(Spacer(1, 1*cm))

        # Decorative line
        d = Drawing(500, 4)
        d.add(Rect(0, 0, 500, 4, fillColor=colors.HexColor('#6366F1'), strokeColor=None))
        elements.append(d)
        elements.append(Spacer(1, 1*cm))

        # Certificate type
        type_labels = {
            'excellence': 'CERTIFICAT D\'EXCELLENCE',
            'mention': 'CERTIFICAT DE MENTION',
            'completion': 'CERTIFICAT DE COMPLÉTION',
            'participation': 'CERTIFICAT DE PARTICIPATION',
            'competence': 'CERTIFICAT DE COMPÉTENCE',
        }
        elements.append(Paragraph(type_labels.get(cert.type_certificat, 'CERTIFICAT'), title_style))
        elements.append(Spacer(1, 0.5*cm))

        # Body text
        elements.append(Paragraph("Ce certificat est décerné à", body_style))
        elements.append(Spacer(1, 0.3*cm))
        elements.append(Paragraph(cert.eleve.full_name.upper(), name_style))
        elements.append(Spacer(1, 0.5*cm))

        # Achievement text
        achievement_text = f"pour avoir obtenu la note de <b>{float(cert.note_obtenue):.2f}/{float(cert.note_sur):.0f}</b>"
        if cert.mention:
            achievement_text += f" avec la mention <b>{cert.mention}</b>"
        if cert.matiere:
            achievement_text += f" en <b>{cert.matiere.nom}</b>"
        achievement_text += "."
        elements.append(Paragraph(achievement_text, body_style))
        elements.append(Spacer(1, 0.5*cm))

        if cert.description:
            elements.append(Paragraph(cert.description, detail_style))

        elements.append(Spacer(1, 1*cm))

        # Info row
        info_data = [
            [Paragraph(f"<b>Date :</b> {cert.date_delivrance.strftime('%d/%m/%Y')}", detail_style),
             Paragraph(f"<b>Code :</b> {cert.code_verification}", detail_style)],
        ]
        if cert.institution:
            info_data.append([Paragraph(f"<b>Institution :</b> {cert.institution}", detail_style), ''])

        info_table = Table(info_data, colWidths=[10*cm, 10*cm])
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 1*cm))

        # Decorative line
        elements.append(d)
        elements.append(Spacer(1, 0.5*cm))

        # Footer with verification info
        elements.append(Paragraph(
            f"Vérifiable en ligne : academie-numerique.com/certificates/verify/{cert.code_verification}/",
            footer_style
        ))
        elements.append(Paragraph(
            f"Signature numérique : {cert.signature_numerique[:32]}...",
            footer_style
        ))

        doc.build(elements)
        pdf_content = buffer.getvalue()
        buffer.close()

        filename = f"certificat_{cert.code_verification}.pdf"
        cert.pdf.save(filename, ContentFile(pdf_content), save=True)

        logger.info(f"Certificat PDF généré : {certificate_id}")
        return {"status": "success", "filename": filename}

    except Exception as e:
        logger.error(f"Erreur génération certificat {certificate_id}: {e}")
        raise
