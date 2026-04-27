from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # ===========================================================================
    # ADMIN - GESTION NOTIFICATIONS
    # ===========================================================================
    
    # Liste notifications utilisateur
    path('', views.notification_list_view, name='list_notifications'),
    
    # Création notification admin
    path('create/', views.notification_create_view, name='create_notification'),
    
    # Preview notification
    path('preview/<uuid:notification_id>/', views.notification_preview_view, name='preview_notification'),
    
    # Preview template
    path('template-preview/<uuid:template_id>/', views.preview_template_view, name='preview_template'),
    
    # ===========================================================================
    # UTILISATEUR - CONSULTATION & ACTIONS
    # ===========================================================================
    
    # Marquer comme lu une notification individuelle
    path('<uuid:notification_id>/read/', views.notification_read_one_view, name='read_notification'),
    
    # Tout marquer comme lu
    path('mark-all-read/', views.mark_all_read_view, name='mark_all_read'),
    
    # ===========================================================================
    # PARAMÈTRES UTILISATEUR
    # ===========================================================================
    
    # Paramètres notifications
    path('settings/', views.notification_settings_view, name='list_settings'),
    
    # ===========================================================================
    # API POUR TEMPS RÉEL & AJAX
    # ===========================================================================
    
    # Compte notifications non-lues (polling)
    path('api/unread-count/', views.notifications_api_unread_count, name='api_unread_count'),
    
    # Toggle statut LU/NON-LU
    path('api/<uuid:notification_id>/toggle-read/', views.notifications_api_toggle_read, name='api_toggle_read'),
    
    # Épingle/Désépingle notification
    path('api/<uuid:notification_id>/pin/', views.notifications_api_pin, name='api_pin'),
    
    # Supprimer notification
    path('api/<uuid:notification_id>/', views.notifications_api_delete, name='api_delete'),
    
    # Marquer plusieurs comme lues en un coup
    path('api/bulk-mark-read/', views.notifications_api_bulk_mark_read, name='api_bulk_mark_read'),
    
    # Filtrer et trier avec pagination
    path('api/filter/', views.notifications_api_filter, name='api_filter'),
    
    # ===========================================================================
    # PUSH NOTIFICATIONS
    # ===========================================================================
    
    # Souscription service worker
    path('push/subscribe/', views.push_subscribe_endpoint, name='push_subscribe'),
    
    # Désinscription
    path('push/unsubscribe/', views.push_unsubscribe_endpoint, name='push_unsubscribe'),
    
    # Toggle push enabled
    path('push/toggle/', views.toggle_push_notifications, name='toggle_push'),
    
    # ===========================================================================
    # NOTIFICATIONS PUBLIQUES
    # ===========================================================================
    
    # Notifications publiques
    path('public/', views.public_notifications_view, name='public_notifications'),
]
