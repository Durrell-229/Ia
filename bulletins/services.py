"""
Services avancés de génération de bulletins PDF professionnels
Inspiré des standards internationaux (IB, Cambridge, Baccalauréat)
"""
import os
import uuid
import logging
import base64
from io import BytesIO
from datetime import datetime
from decimal import Decimal
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone

logger = logging.getLogger(__name__)


class BulletinService:
    """
    Service professionnel de génération de bulletins PDF
    Avec templates haute qualité et signatures numériques
    """
    
    PROFESSIONAL_TEMPLATE = 'bulletins/bulletin_professionel_template.html'
    STANDARD_TEMPLATE = 'bulletins/bulletin_officiel_template.html'
    
    @staticmethod
    def generate_bulletin_professionnel(resultat, utiliser_template_pro=True):
        """
        Génère un bulletin PDF professionnel standard international
        
        Args:
            resultat: Instance Resultat
            utiliser_template_pro: Utiliser le template professionnel ou standard
        
        Returns:
            ContentFile du PDF généré
        """
        try:
            session = resultat.session
            eleve = session.eleve
            
            # Calculs statistiques
            moyenne = float(resultat.note)
            note_max = float(resultat.note_sur)
            
            # Récupérer toutes les matières (ici simplifié - dans vrai cas: charger depuis DB)
            lignes = []
            if hasattr(resultat, 'details_correction'):
                details = resultat.details_correction.get('details', [])
                for idx, detail in enumerate(details):
                    lines.append({
                        'matiere': f"{session.exam.matiere} - Q{idx+1}",
                        'note': detail.get('points_obtenus', 0),
                        'note_max': detail.get('points_max', 5),
                        'moyenne_ponderee': (detail.get('points_obtenus', 0) * 1) / detail.get('points_max', 1) * 20,
                        'appreciation': detail.get('commentaire', ''),
                        'coefficient': 1
                    })
            
            # Si pas de détails, créer une ligne par défaut
            if not lignes:
                lignes.append({
                    'matiere': session.exam.matiere,
                    'note': moyenne,
                    'note_max': note_max,
                    'moyenne_ponderee': moyenne,
                    'appreciation': '',
                    'coefficient': 1
                })
            
            # Calculer moyennes pondérées si coefficient non défini
            for ligne in lignes:
                if 'coefficient' not in ligne or ligne['coefficient'] is None:
                    ligne['coefficient'] = 1
                
                if 'moyenne_ponderee' not in ligne or ligne['moyenne_ponderee'] == 0:
                    note = Decimal(str(ligne['note']))
                    coeff = Decimal(str(ligne['coefficient']))
                    max_note = Decimal(str(ligne['note_max']))
                    ligne['moyenne_ponderee'] = float((note * coeff) / (max_note))
            
            # Déterminer la mention
            mention = BulletinService._get_mention(moyenne)
            
            # Génération appréciation automatique via IA si présente
            appreciation_ia = resultat.appreciation
            if not appreciation_ia and hasattr(resultat, 'correction_ia'):
                from ai_engine.orchestrator import SmartOrchestrator
                orchestrator = SmartOrchestrator()
                appreciation_ia = orchestrator.generate_appreciation_automatique(
                    moyenne, 
                    resultat.details_correction
                )
            
            # Contexte complet pour le template
            context = {
                # Identifiants
                'id': session.id,
                'reference_number': f"BUL/{timezone.now().year}/{session.id.time}",
                'verification_token': str(uuid.uuid4()),
                'date_generation': timezone.now(),
                
                # Établissement
                'logo_url': '/static/images/logo.png',  # À adapter
                'annee_scolaire': "2025-2026",
                'periode_display': 'Annuel',
                'periode': 'AN',
                
                # Élève
                'eleve': eleve,
                'classe': getattr(eleve, 'classe', 'Inconnue'),
                'matricule': getattr(eleve, 'matricule', str(eleve.id)),
                
                # Notes
                'moyenne_generale': moyenne,
                'note_max': note_max,
                'mention': mention,
                'lignes': lignes,
                'rang': getattr(resultat, 'classement', 1),
                'total_eleves': getattr(resultat, 'total_participants', 1),
                'taux_reussite': 85.5,  # À calculer selon la classe
                
                # Appréciation IA
                'appreciation_ia': appreciation_ia,
                
                # QR Code
                'qr_code_url': None,  # Sera ajouté si existant
            }
            
            # Rendu HTML
            template = BulletinService.PROFESSIONAL_TEMPLATE if utiliser_template_pro else BulletinService.STANDARD_TEMPLATE
            
            try:
                html = render_to_string(template, context)
            except Exception as e:
                logger.error(f"Template non trouvé: {template}, fallback sur basic")
                html = render_to_string('bulletins/bulletin_template.html', {
                    'student': eleve,
                    'exam': session.exam,
                    'grade': moyenne,
                    'feedback': appreciation_ia or 'Aucune appréciation disponible',
                    'date': timezone.now()
                })
            
            # Conversion PDF
            pdf_content = BulletinService._html_to_pdf(html)
            
            return pdf_content, context
            
        except Exception as e:
            logger.error(f"[BulletinService] Erreur génération PDF: {e}", exc_info=True)
            raise
    
    @staticmethod
    def _html_to_pdf(html: str) -> bytes:
        """Convertit HTML en PDF avec xhtml2pdf"""
        result = BytesIO()
        
        try:
            pdf = pisa.pisaDocument(
                BytesIO(html.encode("UTF-8")),
                result,
                encoding='utf-8'
            )
            
            if pdf.err:
                logger.error(f"[BulletinService] Erreurs PDF: {pdf.err}")
                raise Exception(f"Erreur PDF: {pdf.err}")
            
            return result.getvalue()
            
        except Exception as e:
            logger.error(f"[BulletinService] Échec conversion HTML-PDF: {e}", exc_info=True)
            raise
    
    @staticmethod
    def generate_pdf_from_bulletin(bulletin):
        """
        Génère le PDF d'un objet Bulletin existant
        
        Args:
            bulletin: Modèle Bulletin
        
        Returns:
            bool: Succès échec
        """
        try:
            context = {
                'bulletin': bulletin,
                'eleve': bulletin.eleve,
                'classe': bulletin.classe,
                'periode': bulletin.get_periode_display(),
                'moyenne_generale': float(bulletin.moyenne_generale),
                'rang': bulletin.rang,
                'appreciation_ia': bulletin.appreciation_ia,
                'annee_scolaire': bulletin.annee_scolaire,
                'lignes': bulletin.lignes.all(),
            }
            
            html = render_to_string(
                BulletinService.PROFESSIONAL_TEMPLATE,
                context
            )
            
            pdf_content = BulletinService._html_to_pdf(html)
            
            # Sauvegarde du fichier PDF
            filename = f"bulletin_{bulletin.eleve.last_name}_{bulletin.periode}_{bulletin.annee_scolaire}.pdf"
            
            from django.core.files.base import ContentFile
            bulletin.file_pdf.save(filename, ContentFile(pdf_content), save=True)
            
            # Marquer comme signé numériquement
            bulletin.is_signed = True
            bulletin.signature_numerique = BulletinService._generate_digital_signature(bulletin)
            bulletin.save(update_fields=['file_pdf', 'is_signed', 'signature_numerique'])
            
            logger.info(f"[BulletinService] PDF généré avec succès: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"[BulletinService] Erreur génération PDF depuis bulletin: {e}", exc_info=True)
            return False
    
    @staticmethod
    def _generate_digital_signature(bulletin) -> str:
        """Génère une signature numérique HMAC pour l'intégrité du bulletin"""
        import hmac
        import hashlib
        
        secret_key = getattr(settings, 'SECRET_KEY', 'default_secret')
        
        data = f"{bulletin.id}-{bulletin.eleve.id}-{bulletin.created_at}"
        signature = hmac.new(
            secret_key.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    @staticmethod
    def _get_mention(note: float) -> str:
        """Détermine la mention académique basée sur la note"""
        if note >= 16:
            return "Excellent"
        elif note >= 14:
            return "Très Bien"
        elif note >= 12:
            return "Bien"
        elif note >= 10:
            return "Assez Bien"
        elif note >= 8:
            return "Passable"
        else:
            return "Insuffisant"
    
    @staticmethod
    def download_bulletin_pdf(request, bulletin_id):
        """
        Retourne une réponse HTTP avec le fichier PDF à télécharger
        
        Args:
            request: Request Django
            bulletin_id: UUID du bulletin
        
        Returns:
            HttpResponse avec le PDF
        """
        try:
            from bulletins.models import Bulletin
            
            bulletin = Bulletin.objects.get(id=bulletin_id)
            
            if not bulletin.file_pdf:
                # Générer le PDF s'il n'existe pas encore
                BulletinService.generate_pdf_from_bulletin(bulletin)
            
            # Lecture du fichier
            bulletin.file_pdf.open('rb')
            content = bulletin.file_pdf.read()
            bulletin.file_pdf.close()
            
            filename = os.path.basename(bulletin.file_pdf.name)
            
            from django.http import HttpResponse
            response = HttpResponse(content, content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="{filename}"'
            
            return response
            
        except Bulletin.DoesNotExist:
            from django.http import Http404
            raise Http404("Bulletin non trouvé")
        except Exception as e:
            logger.error(f"[BulletinService] Erreur téléchargement PDF: {e}", exc_info=True)
            raise
    
    @staticmethod
    def generate_qr_code_verification(bulletin_id: str, url_base: str = None) -> str:
        """
        Génère un QR code pour la vérification du bulletin
        
        Args:
            bulletin_id: ID du bulletin
            url_base: URL de vérification (défaut: settings)
        
        Returns:
            Base64 du QR code image
        """
        from reportlab.graphics.barcodes.qr import QrCode
        from reportlab.lib.units import cm
        from reportlab.pdfgen import canvas
        
        if not url_base:
            url_base = getattr(settings, 'BULLETIN_VERIFY_URL', 'https://academie-numerique.bj/verify/')
        
        verification_url = f"{url_base}{bulletin_id}"
        
        # Création buffer
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        
        # Génération QR code
        qr = QrCode()
        qr.data = verification_url
        qr.width = 3 * cm
        qr.height = 3 * cm
        qr.drawOn(c, 20 * cm, 20 * cm)
        
        c.save()
        
        # Reset et lecture
        buffer.seek(0)
        qr_image = buffer.read()
        
        return base64.b64encode(qr_image).decode('utf-8')
    
    @staticmethod
    def batch_generate_bulletins(user, periode: str, annee: str) -> list:
        """
        Génère tous les bulletins pour un utilisateur sur une période donnée
        
        Args:
            user: User Django
            periode: Période (T1, T2, T3, AN, etc.)
            annee: Année scolaire
        
        Returns:
            Liste des URLs de bulletins générés
        """
        from compositions.models import Resultat
        
        bulletins_urls = []
        
        # Récupérer tous les résultats de l'élève
        resultats = Resultat.objects.filter(
            session__eleve=user
        ).select_related(
            'session__exam'
        )
        
        # Grouper par matière pour création bulletins complets
        matieres_notes = {}
        for resultat in resultats:
            matiere = resultat.session.exam.matiere
            if matiere not in matieres_notes:
                matieres_notes[matiere] = []
            matieres_notes[matiere].append({
                'note': float(resultat.note),
                'note_max': float(resultat.note_sur),
                'session': resultat.session,
                'date': resultat.created_at
            })
        
        # Calculer moyennes par matière
        lignes = []
        for matiere, notes in matieres_notes.items():
            moyennes = [n['note'] * 20 / n['note_max'] for n in notes]
            moyenne_matiere = sum(moyennes) / len(moyennes)
            
            lignes.append({
                'matiere': matiere,
                'note': moyenne_matiere,
                'note_max': 20,
                'moyenne_ponderee': moyenne_matiere,
                'appreciation': '',
                'coefficient': 1
            })
        
        # Créer bulletin groupé
        from bulletins.models import Bulletin
        
        bulletin, _ = Bulletin.objects.get_or_create(
            eleve=user,
            periode=periode,
            annee_scolaire=annee,
            defaults={
                'classe': getattr(user, 'classe', 'Inconnue'),
                'moyenne_generale': sum(l['note'] for l in lignes) / len(lignes) if lignes else 0,
                'appreciation_ia': ''
            }
        )
        
        # Sauvegarder lignes
        BulletinService._save_bulletin_lignes(bulletin, lignes)
        
        # Générer PDF
        BulletinService.generate_pdf_from_bulletin(bulletin)
        
        # Stocker URL
        if bulletin.file_pdf:
            bulletins_urls.append(bulletin.file_pdf.url)
        
        return bulletins_urls
    
    @staticmethod
    def _save_bulletin_lignes(bulletin, lignes_data: list):
        """Sauvegarde les lignes du bulletin en base"""
        from bulletins.models import BulletinLigne
        
        # Nettoyer anciennes lignes
        BulletinLigne.objects.filter(bulletin=bulletin).delete()
        
        # Ajouter nouvelles lignes
        for ligne_data in lignes_data:
            BulletinLigne.objects.create(
                bulletin=bulletin,
                matiere=ligne_data['matiere'],
                note=ligne_data['note'],
                note_max=ligne_data['note_max'],
                moyenne_classe=ligne_data.get('moyenne_ponderee', 0),
                appreciation=ligne_data.get('appreciation', '')
            )


# Instance globale réutilisable
bulletin_service = BulletinService()
