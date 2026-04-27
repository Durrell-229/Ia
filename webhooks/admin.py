from django.contrib import admin
from .models import WebhookEndpoint, WebhookDelivery


@admin.register(WebhookEndpoint)
class WebhookEndpointAdmin(admin.ModelAdmin):
    list_display = ['url', 'proprietaire', 'est_actif', 'nb_echecs', 'derniere_reponse']
    list_filter = ['est_actif']


@admin.register(WebhookDelivery)
class WebhookDeliveryAdmin(admin.ModelAdmin):
    list_display = ['webhook', 'event', 'response_status', 'succes', 'delivered_at']
    list_filter = ['event', 'succes']
