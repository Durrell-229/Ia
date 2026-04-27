from django.template.loader import render_to_string
from weasyprint import HTML
import os
from django.conf import settings

class PDFService:
    @staticmethod
    def generate_bulletin(bulletin_data):
        """
        Génère un bulletin PDF à partir de données.
        bulletin_data: dict contenant les infos de l'élève, les notes, etc.
        """
        html_string = render_to_string('bulletins/pdf_template.html', {'data': bulletin_data})
        
        # Définir le chemin de sortie
        filename = f"bulletin_{bulletin_data['eleve_id']}_{bulletin_data['periode']}.pdf"
        output_path = os.path.join(settings.MEDIA_ROOT, 'bulletins', filename)
        
        # Créer le dossier s'il n'existe pas
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Générer le PDF
        HTML(string=html_string).write_pdf(output_path)
        
        return os.path.join('bulletins', filename)

    @staticmethod
    def generate_exam_report(resultat):
        """
        Génère un rapport de correction pour un examen unique.
        """
        html_string = render_to_string('correction/pdf_report_template.html', {'resultat': resultat})
        filename = f"rapport_{resultat.id}.pdf"
        output_path = os.path.join(settings.MEDIA_ROOT, 'reports', filename)
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        HTML(string=html_string).write_pdf(output_path)
        
        return os.path.join('reports', filename)
