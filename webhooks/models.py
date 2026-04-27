import uuid
import hmac
import hashlib
import json
import logging
import requests
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

logger = logging.getLogger(__name__)


class WebhookEndpoint(models.Model):
    """Webhook configurable pour les intégrations tierces."""
    class Event(models.TextChoices):
        EXAM_CREATED = 'exam.created', _('Examen créé')
        EXAM_STARTED = 'exam.started', _('Examen démarré')
        EXAM_COMPLETED = 'exam.completed', _('Examen terminé')
        COMPOSITION_SUBMITTED = 'composition.submitted', _('Composition soumise')
        RESULT_AVAILABLE = 'result.available', _('Résultat disponible')
        BULLETIN_GENERATED = 'bulletin.generated', _('Bulletin généré')
        CERTIFICATE_ISSUED = 'certificate.issued', _('Certificat délivré')
        USER_REGISTERED = 'user.registered', _('Utilisateur inscrit')
        CHEAT_DETECTED = 'cheat.detected', _('Triche détectée')
        PLAGIARISM_ALERT = 'plagiarism.alert', _('Alerte plagiat')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    proprietaire = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='webhooks')
    url = models.URLField(_('URL du webhook'))
    secret = models.CharField(_('secret'), max_length=128, blank=True)
    events = models.JSONField(_('événements'), default=list)
    est_actif = models.BooleanField(_('actif'), default=True)
    description = models.CharField(_('description'), max_length=255, blank=True)
    derniere_reponse = models.PositiveIntegerField(_('dernier code HTTP'), blank=True, null=True)
    nb_echecs = models.PositiveIntegerField(_('échecs consécutifs'), default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('webhook')
        verbose_name_plural = _('webhooks')
        ordering = ['-created_at']

    def __str__(self):
        return f"Webhook -> {self.url}"

    def generate_secret(self):
        raw = f"{self.id}{settings.SECRET_KEY}{timezone.now().timestamp()}"
        self.secret = hashlib.sha256(raw.encode()).hexdigest()[:32]
        return self.secret

    def deliver(self, event_type: str, payload: dict):
        if not self.est_actif:
            return
        if event_type not in self.events:
            return

        body = json.dumps({
            'event': event_type,
            'timestamp': timezone.now().isoformat(),
            'data': payload,
        })

        signature = ''
        if self.secret:
            signature = hmac.new(
                self.secret.encode(), body.encode(), hashlib.sha256
            ).hexdigest()

        headers = {
            'Content-Type': 'application/json',
            'X-Webhook-Event': event_type,
            'X-Webhook-Signature': signature,
            'X-Webhook-ID': str(self.id),
        }

        try:
            resp = requests.post(self.url, data=body, headers=headers, timeout=10)
            self.derniere_reponse = resp.status_code
            self.nb_echecs = 0 if resp.status_code < 400 else self.nb_echecs + 1
            if self.nb_echecs >= 10:
                self.est_actif = False
            self.save()
            WebhookDelivery.objects.create(
                webhook=self,
                event=event_type,
                payload=payload,
                response_status=resp.status_code,
                response_body=resp.text[:5000],
                succes=resp.status_code < 400,
            )
        except Exception as e:
            self.nb_echecs += 1
            self.save()
            WebhookDelivery.objects.create(
                webhook=self,
                event=event_type,
                payload=payload,
                response_status=0,
                response_body=str(e)[:5000],
                succes=False,
            )


class WebhookDelivery(models.Model):
    """Historique des livraisons de webhook."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    webhook = models.ForeignKey(WebhookEndpoint, on_delete=models.CASCADE, related_name='deliveries')
    event = models.CharField(_('événement'), max_length=50)
    payload = models.JSONField(_('payload'))
    response_status = models.PositiveIntegerField(_('code HTTP'), default=0)
    response_body = models.TextField(_('réponse'), blank=True)
    succes = models.BooleanField(_('succès'), default=False)
    delivered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('livraison webhook')
        verbose_name_plural = _('livraisons webhooks')
        ordering = ['-delivered_at']
