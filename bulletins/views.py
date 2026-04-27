"""
Vues complètes pour la gestion des bulletins PDF
Dashboard élève/prof/admin pour visualisation et téléchargement
"""
import logging
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse, FileResponse, Http404, HttpResponseForbidden
from django.core.files.base import ContentFile
from django.utils import timezone
from datetime import datetime
from django.db.models import Avg, Q
from decimal import Decimal

from .models import Bulletin, BulletinLigne

logger = logging.getLogger(__name__)


@login_required
def index(request):
    """Dashboard bulletin - liste tous les bulletins selon rôle utilisateur"""
    
    if request.user.role == 'eleve':
        bulletins = Bulletin.objects.filter(
            eleve=request.user
        ).select_related('lignes__bulletin').order_by('-created_at')
    elif request.user.role == 'professeur':
        # Récupérer classes enseignées par le prof
        from exams.models import Exam
        exam_matiere = Exam.objects.filter(createur=request.user).values_list('matiere', flat=True)
        bulletins = Bulletin.objects.filter(
            eleve__composition_sessions__exam__matiere__in=exam_matiere
        ).distinct().select_related('eleve').order_by('-created_at')
    else:  # Admin
        bulletins = Bulletin.objects.all().select_related('eleve').prefetch_related('lignes').order_by('-created_at')
    
    context = {
        'bulletins': bulletins,
        'total_bulletins': bulletins.count(),
    }
    
    return render(request, 'bulletins/index.html', context)


@login_required
def detail(request, bulletin_id):
    """Affiche détails d'un bulletin spécifique"""
    bulletin = get_object_or_404(Bulletin, id=bulletin_id)
    
    # Vérification permissions
    if request.user.role == 'eleve' and bulletin.eleve != request.user:
        return HttpResponseForbidden("Accès refusé")
    
    lignes = bulletin.lignes.all()
    
    # Calcul moyenne si non définie
    if not bulletin.moyenne_generale and lignes.exists():
        moyennes = [float(ligne.note) for ligne in lignes]
        bulletin.moyenne_generale = sum(moyennes) / len(moyennes)
        bulletin.save(update_fields=['moyenne_generale'])
    
    mention = _get_mention(float(bulletin.moyenne_generale)) if bulletin.moyenne_generale else ''
    
    context = {
        'bulletin': bulletin,
        'lignes': lignes,
        'appreciation_ia': bulletin.appreciation_ia,
        'mention': mention,
    }
    
    return render(request, 'bulletins/detail.html', context)


@login_required
def download(request, bulletin_id):
    """Télécharge le bulletin PDF"""
    bulletin = get_object_or_404(Bulletin, id=bulletin_id)
    
    # Vérification permissions
    if request.user.role == 'eleve' and bulletin.eleve != request.user:
        return HttpResponseForbidden("Accès refusé")
    
    # Si pas de PDF, le générer
    if not bulletin.file_pdf:
        try:
            from bulletins.services import BulletinService
            pdf_content, _ = BulletinService.generate_bulletin_professionnel(bulletin)
            
            filename = f"bulletin_{bulletin.eleve.last_name}_{bulletin.periode}_{bulletin.annee_scolaire}.pdf"
            bulletin.file_pdf.save(filename, ContentFile(pdf_content), save=True)
            bulletin.is_signed = True
            
            signature = BulletinService._generate_digital_signature(bulletin)
            bulletin.signature_numerique = signature
            bulletin.save(update_fields=['file_pdf', 'is_signed', 'signature_numerique'])
            
        except Exception as e:
            logger.error(f"[PDFDownload] Erreur génération: {e}")
            raise Http404("Erreur génération PDF")
    
    # Retourner fichier
    if bulletin.file_pdf:
        bulletin.file_pdf.open('rb')
        content = bulletin.file_pdf.read()
        bulletin.file_pdf.close()
        
        filename = os.path.basename(bulletin.file_pdf.name)
        
        response = HttpResponse(content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
    
    raise Http404("Fichier PDF introuvable")


@login_required
def generate_on_demand(request, result_id):
    """Génère bulletin sur demande pour un résultat"""
    from compositions.models import Resultat
    
    resultat = get_object_or_404(Resultat, id=result_id)
    
    if request.user.role == 'eleve' and resultat.session.eleve != request.user:
        return HttpResponseForbidden("Accès refusé")
    
    try:
        from bulletins.services import BulletinService
        
        eleve = resultat.session.eleve
        moyenne = float(resultat.note) / float(resultat.note_sur) * 20
        
        bulletin, _ = Bulletin.objects.get_or_create(
            eleve=eleve,
            periode='AN',
            annee_scolaire="2025-2026",
            defaults={
                'classe': getattr(eleve, 'classe', 'Inconnue'),
                'moyenne_generale': moyenne,
            }
        )
        
        from bulletins.models import BulletinLigne
        BulletinLigne.objects.filter(bulletin=bulletin).delete()
        
        BulletinLigne.objects.create(
            bulletin=bulletin,
            matiere=getattr(resultat.session.exam, 'matiere', 'Composition'),
            note=moyenne,
            note_max=Decimal('20.00'),
            moyenne_classe=moyenne,
            appreciation=resultat.appreciation or '-'
        )
        
        pdf_content, context = BulletinService.generate_bulletin_professionnel(resultat)
        
        filename = f"bulletin_{eleve.last_name}_on_demand_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        bulletin.file_pdf.save(filename, ContentFile(pdf_content), save=True)
        
        return JsonResponse({
            'success': True,
            'message': 'Bulletin généré',
            'bulletin_id': str(bulletin.id),
            'download_url': f'/bulletins/download/{bulletin.id}/'
        })
        
    except Exception as e:
        logger.error(f"[GenerateOnDemand] Erreur: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def stats(request):
    """Statistiques académiques élève"""
    if request.user.role != 'eleve':
        return HttpResponseForbidden("Réservé aux élèves")
    
    bulletins = Bulletin.objects.filter(eleve=request.user)
    
    if not bulletins.exists():
        return JsonResponse({
            'total_bulletins': 0,
            'moyenne_generale': 0,
            'mentions': {}
        })
    
    moyennes = [float(b.moyenne_generale) for b in bulletins]
    moyenne_globale = sum(moyennes) / len(moyennes)
    
    mentions_count = {}
    for bulletin in bulletins:
        mention = _get_mention(float(bulletin.moyenne_generale))
        mentions_count[mention] = mentions_count.get(mention, 0) + 1
    
    data = {
        'total_bulletins': bulletins.count(),
        'moyenne_generale': round(moyenne_globale, 2),
        'meilleure_note': max(moyennes),
        'moindre_note': min(moyennes),
        'mentions': mentions_count,
        'bulletins_recents': [
            {
                'id': str(b.id),
                'periode': b.periode,
                'moyenne': float(b.moyenne_generale),
                'date': b.created_at.isoformat()
            }
            for b in bulletins.order_by('-created_at')[:5]
        ]
    }
    
    return JsonResponse(data)


@login_required
def bulk_download(request):
    """Placeholder téléchargement groupé ZIP"""
    return JsonResponse({
        'status': 'coming_soon',
        'message': 'Téléchargement groupé en développement'
    })


# ===========================================================================
# Utilitaires
# ===========================================================================

def _get_mention(note: float) -> str:
    """Détermine mention académique"""
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


def check_bulletin_permission(user, bulletin):
    """Vérifie permissions accès bulletin"""
    if user.role == 'admin':
        return True
    if user.role == 'eleve':
        return bulletin.eleve == user
    if user.role == 'professeur':
        return False  # À implémenter
    return False
