"""
Views pour le système de Notifications Intelligentes Style Discord
Admin interface + Frontend utilisateur
"""
from django.views.decorators.csrf import csrf_exempt
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

from .models import Notification, NotificationSetting, NotificationCategory

@login_required
def notification_create_view(request):
    """
    Interface admin pour créer des notifications professionnelles
    Inspirée de Discord: cartes élégantes, options avancées, preview en temps réel
    """
    from .models import NotificationTemplate
    
    if request.user.role not in ['admin', 'conseiller']:
        return HttpResponseForbidden("Accès administrateur réservé")
    
    template = None
    templates = NotificationTemplate.objects.filter(is_active=True)
    
    if request.method == 'POST':
        titre = request.POST.get('titre', '')
        message = request.POST.get('message', '')
        type_notif = request.POST.get('type_notif', 'general')
        priorite = request.POST.get('priorite', 'normal')
        
        # Options avancées
        image_url = request.POST.get('image_url', '') or None
        action_label = request.POST.get('action_label', 'Voir')
        action_url = request.POST.get('action_url', '') or None
        
        # Destinataires
        destinateur_ids = request.POST.getlist('destinateur_id[]')
        categorie_id = request.POST.get('categorie_id')
        
        # Template selectionné
        template_id = request.POST.get('template_id')
        if template_id:
            template = get_object_or_404(NotificationTemplate, id=template_id)
            try:
                variables = json.loads(request.POST.get('template_variables', '{}'))
                notification = template.render_notification(
                    variables_dict=variables,
                    recipient=None
                )
                titre = notification.titre
                message = notification.message
            except KeyError as e:
                pass  # Variable manquante, utiliser formulaire manuel
        
        # Création notification
        notif_data = {
            'titre': titre,
            'message': message,
            'type_notif': type_notif,
            'priorite': priorite,
            'image_url': image_url,
            'action_label': action_label,
            'action_url': action_url,
            'categorie_id': categorie_id,
        }
        
        # Destinataires multiples ou tous les utilisateurs
        if destinateur_ids:
            from django.contrib.auth.models import User as DjangoUser
            destinateurs = DjangoUser.objects.filter(id__in=destinateur_ids)
            
            for user in destinateurs:
                notif_data['destinateur'] = user
                Notification.objects.create(**notif_data)
        else:
            # Notification générale à tous
            from django.contrib.auth.models import User as DjangoUser
            tous_utilisateurs = DjangoUser.objects.all()
            
            for user in tous_utilisateurs[:500]:  # Limit protection
                notif_data['destinateur'] = user
                Notification.objects.create(**notif_data)
        
        return redirect('notifications:list_notifications')
    
    context = {
        'templates': templates,
        'selected_template': template,
        'types_choices': Notification.Type.choices,
        'priorites_choices': Notification.Priorité.choices,
    }
    
    return render(request, 'notifications/create.html', context)


@login_required
def notification_preview_view(request, notification_id):
    """Preview notification style Discord"""
    notification = get_object_or_404(Notification, id=notification_id)
    
    # Calcul badge priorité
    badge_style = {
        Notification.Priorité.BAS: 'green',
        Notification.Priorité.NORMALE: 'blue',
        Notification.Priorité.HAUTE: 'orange',
        Notification.Priorité.URGENTE: 'red',
        Notification.Priorité.CRITIQUE: 'purple',
    }.get(notification.priorite, 'gray')
    
    context = {
        'notification': notification,
        'badge_style': badge_style,
    }
    
    return render(request, 'notifications/preview_discord.html', context)


# ===========================================================================
# UTILISATEUR - CONSULTATION DES NOTIFICATIONS
# ===========================================================================

@login_required
def notification_list_view(request):
    """Liste notifications utilisateur (sidebar style Discord)"""
    notifications = Notification.objects.filter(
        destinateur=request.user,
        is_read=False,
        is_deleted_for_user=False,
        Q(expires_at__gte=timezone.now()) | Q(expires_at__isnull=True)
    ).order_by('-created_at')[:100]
    
    # Pagination simple
    page = request.GET.get('page', 1)
    per_page = 50
    
    total_unread = notifications.count()
    
    # Groupe par jour
    grouped = {}
    today_str = timezone.now().strftime('%d/%m/%Y')
    
    for notif in notifications:
        date_str = notif.created_at.strftime('%d/%m/%Y')
        if date_str == today_str:
            key = "Aujourd'hui"
        elif date_str == (timezone.now() - timedelta(days=1)).strftime('%d/%m/%Y'):
            key = "Hier"
        else:
            key = date_str
        
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(notif)
    
    context = {
        'notifications': list(grouped.items()),
        'total_unread': total_unread,
    }
    
    return render(request, 'notifications/list.html', context)


@login_required
def notification_read_one_view(request, notification_id):
    """Marquer comme lue et récupérer la notification complète"""
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        destinateur=request.user
    )
    
    notification.marquer_comme_lue()
    
    # Si notification a une action URL, rediriger sinon retour avec données
    if notification.action_url:
        return redirect(notification.action_url)
    
    return JsonResponse({
        'success': True,
        'id': str(notification.id),
        'notification': {
            'id': str(notification.id),
            'titre': notification.titre,
            'message': notification.message,
            'image_url': notification.image_url,
            'action_url': notification.action_url,
            'action_label': notification.action_label,
            'time_ago': notification.time_ago,
        }
    })


@login_required
def mark_all_read_view(request):
    """Marquer toutes les notifications comme lues"""
    Notification.objects.filter(
        destinateur=request.user,
        is_read=False,
        is_deleted_for_user=False
    ).update(
        is_read=True,
        read_at=timezone.now()
    )
    
    return JsonResponse({'success': True, 'message': 'Toutes marquées comme lues'})


# ===========================================================================
# API POUR TEMPS RÉEL & PUSH NOTIFICATIONS
# ===========================================================================

@login_required
def notifications_api_unread_count(request):
    """Count notifications non-lues (AJAX poll)"""
    count = Notification.objects.filter(
        destinateur=request.user,
        is_read=False,
        is_deleted_for_user=False,
        Q(expires_at__gte=timezone.now()) | Q(expires_at__isnull=True)
    ).count()
    
    return JsonResponse({'unread_count': count})


@login_required
def notifications_api_mark_as_read(request, notification_id):
    """API pour marquer lecture (optimisé AJAX)"""
    try:
        notification = Notification.objects.get(
            id=notification_id,
            destinateur=request.user
        )
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save(update_fields=['is_read', 'read_at'])
        
        return JsonResponse({'success': True})
    except Notification.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Notification not found'}, status=404)


@login_required
def toggle_push_notifications(request):
    """Activer/désactiver push notifications navigateur"""
    if request.method == 'POST':
        enabled = request.POST.get('enabled') == 'true'
        
        setting, created = NotificationSetting.objects.get_or_create(user=request.user)
        setting.push_enabled = enabled
        
        # Browser push subscription
        if enabled:
            data = json.loads(request.body or '{}')
            setting.push_browser_id = data.get('subscription_endpoint')
        
        setting.save()
        
        return JsonResponse({
            'success': True,
            'push_enabled': enabled
        })
    
    # GET: vérifier statut
    try:
        setting = NotificationSetting.objects.get(user=request.user)
        return JsonResponse({'push_enabled': setting.push_enabled})
    except NotificationSetting.DoesNotExist:
        return JsonResponse({'push_enabled': True})


# ===========================================================================
# PARAMÈTRES UTILISATEUR
# ===========================================================================

@login_required
def notification_settings_view(request):
    """Paramètres notifications utilisateur"""
    setting, created = NotificationSetting.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Sauvegarder préférences
        setting.son_notifications = request.POST.get('son_notifications') == 'on'
        setting.push_enabled = request.POST.get('push_enabled') == 'on'
        setting.email_digest_daily = request.POST.get('email_digest_daily') == 'on'
        setting.do_not_disturb = request.POST.get('do_not_disturb') == 'on'
        setting.dnd_start_time = request.POST.get('dnd_start_time') or None
        setting.dnd_end_time = request.POST.get('dnd_end_time') or None
        
        # Enabled types
        enabled_types = {}
        for key in ['examens', 'notes', 'badges', 'commentaires', 'mentions']:
            enabled_types[key] = request.POST.get(f'enable_{key}') == 'on'
        setting.enabled_types = enabled_types
        
        setting.save()
        
        return redirect('notifications:list_settings')
    
    context = {'setting': setting}
    return render(request, 'notifications/settings.html', context)


# ===========================================================================
# NOTIFICATIONS PUBLIQUES / GÉNÉRALES
# ===========================================================================

def public_notifications_view(request):
    """Notifications publiques visibles par tous"""
    notifications = Notification.objects.filter(
        destinateur__isnull=True,  # NULL = publiques
        is_deleted_for_user=False,
        Q(expires_at__gte=timezone.now()) | Q(expires_at__isnull=True)
    ).order_by('-created_at')[:20]
    
    context = {'notifications': notifications}
    return render(request, 'notifications/public.html', context)


# ===========================================================================
# NOUVEAUX API ENDPOINTS POUR TEMPS RÉEL & GESTION AVANCÉE
# ===========================================================================

@login_required
def notifications_api_toggle_read(request, notification_id):
    """API POST: Basculer statut LU/NON-LU (AJAX)"""
    try:
        notification = Notification.objects.get(
            id=notification_id,
            destinateur=request.user
        )
        
        # Toggle statut
        notification.is_read = not notification.is_read
        if notification.is_read:
            notification.read_at = timezone.now()
        else:
            notification.read_at = None
        
        notification.save(update_fields=['is_read', 'read_at'])
        
        return JsonResponse({
            'success': True,
            'is_read': notification.is_read,
            'time_ago': notification.time_ago,
            'type': 'toggle_read'
        })
    except Notification.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Notification not found',
            'type': 'toggle_read'
        }, status=404)


@login_required
def notifications_api_pin(request, notification_id):
    """API POST: Épingle/Désépingle une notification"""
    try:
        notification = Notification.objects.get(
            id=notification_id,
            destinateur=request.user
        )
        
        notification.is_pinned = not notification.is_pinned
        notification.save(update_fields=['is_pinned'])
        
        return JsonResponse({
            'success': True,
            'is_pinned': notification.is_pinned,
            'type': 'pin'
        })
    except Notification.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Notification not found',
            'type': 'pin'
        }, status=404)


@login_required
def notifications_api_delete(request, notification_id):
    """API DELETE: Supprimer une notification (soft delete)"""
    try:
        notification = Notification.objects.get(
            id=notification_id,
            destinateur=request.user
        )
        
        # Soft delete (marqué comme supprimé mais pas physiquement effacé)
        notification.is_deleted_for_user = True
        notification.save(update_fields=['is_deleted_for_user'])
        
        return JsonResponse({
            'success': True,
            'deleted_id': str(notification_id),
            'type': 'delete'
        })
    except Notification.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Notification not found',
            'type': 'delete'
        }, status=404)


@login_required
def notifications_api_bulk_mark_read(request):
    """API POST: Marquer plusieurs notifications comme lues en un coup"""
    try:
        data = json.loads(request.body or '{}')
        notification_ids = data.get('ids', [])
        
        count_updated = Notification.objects.filter(
            id__in=notification_ids,
            destinateur=request.user,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )
        
        return JsonResponse({
            'success': True,
            'updated_count': count_updated,
            'type': 'bulk_mark_read'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'type': 'bulk_mark_read'
        }, status=400)


@login_required
def notifications_api_filter(request):
    """API GET: Filtrer et trier les notifications avec pagination"""
    notification_type = request.GET.get('type', 'all')
    priority = request.GET.get('priority', 'all')
    sort_order = request.GET.get('sort', '-created_at')
    page = int(request.GET.get('page', 1))
    per_page = 30
    
    # Base query
    queryset = Notification.objects.filter(
        destinateur=request.user,
        is_deleted_for_user=False
    )
    
    # Filtres
    if notification_type != 'all':
        queryset = queryset.filter(type_notif=notification_type)
    
    if priority != 'all':
        queryset = queryset.filter(priorite=priority)
    
    # Trier
    ordering_map = {
        '-created_at': ['-created_at'],
        'created_at': ['created_at'],
        'priority': ['-priorite', '-created_at']
    }
    queryset = queryset.order_by(*ordering_map.get(sort_order, ['-created_at']))
    
    # Pagination
    total = queryset.count()
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated = queryset[start_idx:end_idx]
    
    # Serialiser
    notifications_list = []
    for notif in paginated:
        notifications_list.append({
            'id': str(notif.id),
            'titre': notif.titre,
            'message': notif.message,
            'description_longue': notif.description_longue,
            'type_notif': notif.type_notif,
            'priority': notif.priorite,
            'image_url': notif.image_url,
            'action_url': notif.action_url,
            'is_read': notif.is_read,
            'is_pinned': notif.is_pinned,
            'time_ago': notif.time_ago,
            'created_at': notif.created_at.isoformat()
        })
    
    return JsonResponse({
        'success': True,
        'notifications': notifications_list,
        'pagination': {
            'current_page': page,
            'total_pages': (total + per_page - 1) // per_page,
            'total_items': total,
            'has_next': end_idx < total,
            'has_prev': page > 1
        },
        'type': 'filter'
    })


# ===========================================================================
# PUSH NOTIFICATIONS SUBSCRIPTION
# ===========================================================================

from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def push_subscribe_endpoint(request):
    """Endpoint pour souscription aux push notifications (service worker)"""
    if request.method == 'POST':
        user = request.user if request.user.is_authenticated else None
        
        if not user:
            return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=401)
        
        try:
            data = json.loads(request.body or '{}')
            
            # Créer ou mettre à jour setting
            setting, _ = NotificationSetting.objects.get_or_create(user=user)
            
            # Sauvegarder subscription
            setting.push_subscription = json.dumps(data)
            setting.push_enabled = True
            setting.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Successfully subscribed to push notifications'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)


@login_required
def push_unsubscribe_endpoint(request):
    """Désinscription notifications push"""
    try:
        setting = NotificationSetting.objects.get(user=request.user)
        setting.push_enabled = False
        setting.push_subscription = None
        setting.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Unsubscribed successfully'
        })
    except NotificationSetting.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Setting not found'
        }, status=404)


# ===========================================================================
# PREVIEW TEMPLATE
# ===========================================================================

@login_required
def preview_template_view(request, template_id):
    """Preview rendering d'un template de notification"""
    from .models import NotificationTemplate
    
    template = get_object_or_404(NotificationTemplate, id=template_id)
    
    # Variables par défaut
    default_vars = {
        'user_name': request.user.username,
        'platform_name': 'Plateforme Éducative',
        'date': timezone.now().strftime('%d %B %Y'),
    }
    
    # Rendu
    titre_rendered = template.titre_template.format(**default_vars)
    message_rendered = template.message_template.format(**default_vars)
    
    context = {
        'template': template,
        'rendered_titre': titre_rendered,
        'rendered_message': message_rendered,
        'test_variables': default_vars
    }
    
    return render(request, 'notifications/preview_discord.html', context)
