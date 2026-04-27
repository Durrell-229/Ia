import csv
import io
import json
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.utils import timezone

from .models import AuditLog, DataExport
from .utils import log_audit


@login_required
def audit_log_view(request):
    if request.user.role not in ['admin', 'conseiller']:
        return HttpResponseForbidden()
    logs = AuditLog.objects.all().select_related('user')
    action_filter = request.GET.get('action', '')
    user_filter = request.GET.get('user', '')
    if action_filter:
        logs = logs.filter(action=action_filter)
    if user_filter:
        logs = logs.filter(user__email__icontains=user_filter)
    logs = logs[:200]
    return render(request, 'audittrail/logs.html', {'logs': logs})


@login_required
def export_data_view(request):
    """Export de données en CSV, Excel ou JSON."""
    if request.user.role not in ['admin', 'conseiller', 'professeur']:
        return HttpResponseForbidden()

    export_type = request.GET.get('type', 'resultats')
    format_type = request.GET.get('format', 'csv')

    log_audit(request.user, 'export', 'data_export', f'Export {export_type} en {format_type}',
              ip_address=request.META.get('REMOTE_ADDR'))

    if export_type == 'resultats':
        from compositions.models import Resultat
        qs = Resultat.objects.select_related('session__eleve', 'session__exam')
        if request.user.role == 'professeur':
            qs = qs.filter(session__exam__createur=request.user)
        data = [{
            'Eleve': r.session.eleve.full_name,
            'Email': r.session.eleve.email,
            'Examen': r.session.exam.titre,
            'Note': float(r.note),
            'Note_Sur': float(r.note_sur),
            'Mention': r.get_mention_display(),
            'Classement': r.classement,
            'Corrige_IA': r.corrige_par_ia,
            'Date': r.corrige_at.strftime('%d/%m/%Y') if r.corrige_at else '',
        } for r in qs]
    elif export_type == 'utilisateurs':
        from accounts.models import User
        data = [{
            'Nom': u.full_name,
            'Email': u.email,
            'Role': u.get_role_display(),
            'Pays': u.country,
            'Niveau': u.get_niveau_display(),
            'Matricule': u.matricule,
            'Inscrit_le': u.date_joined.strftime('%d/%m/%Y'),
        } for u in User.objects.all()]
    elif export_type == 'examens':
        from exams.models import Exam
        data = [{
            'Titre': e.titre,
            'Type': e.get_type_exam_display(),
            'Matiere': e.matiere.nom if e.matiere else '',
            'Createur': e.createur.full_name,
            'Statut': e.get_statut_display(),
            'Date_Debut': e.date_debut.strftime('%d/%m/%Y %H:%M'),
            'Date_Fin': e.date_fin.strftime('%d/%m/%Y %H:%M'),
        } for e in Exam.objects.select_related('matiere', 'createur')]
    else:
        data = []

    if format_type == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{export_type}_{timezone.now().strftime("%Y%m%d")}.csv"'
        if data:
            writer = csv.DictWriter(response, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        return response

    elif format_type == 'json':
        response = HttpResponse(content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="{export_type}_{timezone.now().strftime("%Y%m%d")}.json"'
        json.dump(data, response, indent=2, ensure_ascii=False)
        return response

    elif format_type == 'excel':
        try:
            import openpyxl
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = export_type.capitalize()
            if data:
                headers = list(data[0].keys())
                ws.append(headers)
                for row in data:
                    ws.append(list(row.values()))
            output = io.BytesIO()
            wb.save(output)
            output.seek(0)
            response = HttpResponse(output.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename="{export_type}_{timezone.now().strftime("%Y%m%d")}.xlsx"'
            return response
        except ImportError:
            return JsonResponse({'error': 'openpyxl non installé'}, status=500)

    return JsonResponse({'error': 'Format non supporté'}, status=400)
