from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

from .models import WebhookEndpoint, WebhookDelivery


@login_required
def webhook_list_view(request):
    webhooks = WebhookEndpoint.objects.filter(proprietaire=request.user)
    return render(request, 'webhooks/list.html', {'webhooks': webhooks})


@login_required
def webhook_create_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    data = json.loads(request.body)
    wh = WebhookEndpoint.objects.create(
        proprietaire=request.user,
        url=data.get('url', ''),
        events=data.get('events', []),
        description=data.get('description', ''),
    )
    wh.generate_secret()
    wh.save()
    return JsonResponse({'id': str(wh.id), 'secret': wh.secret, 'url': wh.url})


@login_required
def webhook_deliveries_view(request, webhook_id):
    webhook = get_object_or_404(WebhookEndpoint, id=webhook_id, proprietaire=request.user)
    deliveries = webhook.deliveries.all()[:50]
    return render(request, 'webhooks/deliveries.html', {'webhook': webhook, 'deliveries': deliveries})


@csrf_exempt
@require_http_methods(["POST"])
def public_webhook_test(request):
    """Endpoint de test pour vérifier que les webhooks fonctionnent."""
    payload = {
        'event': 'webhook.test',
        'message': 'Test de webhook réussi',
        'headers_received': dict(request.headers),
    }
    return JsonResponse(payload)
