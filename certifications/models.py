import uuid
import hashlib
import hmac
import os
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class Certificate(models.Model):
    class TypeCertificat(models.TextChoices):
        EXCELLENCE = 'excellence', _('Certificat d\'Excellence')
        MENTION = 'mention', _('Certificat de Mention')
        COMPLETION = 'completion', _('Certificat de Completion')
        PARTICIPATION = 'participation', _('Certificat de Participation')
        COMPETENCE = 'competence', _('Certificat de Compétence')

    class Statut(models.TextChoices):
        ACTIF = 'actif', _('Actif')
        REVOQUE = 'revoque', _('Révoqué')
        EXPIRE = 'expire', _('Expiré')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code_verification = models.CharField(_('code de vérification'), max_length=64, unique=True, db_index=True)
    eleve = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='certificates')
    type_certificat = models.CharField(_('type'), max_length=20, choices=TypeCertificat.choices, default=TypeCertificat.COMPLETION)
    titre = models.CharField(_('titre'), max_length=300)
    description = models.TextField(_('description'), blank=True)
    examen = models.ForeignKey('compositions.CompositionSession', on_delete=models.SET_NULL, null=True, blank=True, related_name='certificates')
    note_obtenue = models.DecimalField(_('note obtenue'), max_digits=5, decimal_places=2, blank=True, null=True)
    note_sur = models.DecimalField(_('note sur'), max_digits=5, decimal_places=2, blank=True, null=True)
    mention = models.CharField(_('mention'), max_length=50, blank=True)
    matiere = models.ForeignKey('core.Matiere', on_delete=models.SET_NULL, null=True, blank=True)
    delivre_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='certificates_delivres')
    institution = models.CharField(_('institution'), max_length=300, blank=True)
    date_delivrance = models.DateTimeField(_('date de délivrance'), default=timezone.now)
    date_expiration = models.DateTimeField(_('date d\'expiration'), blank=True, null=True)
    signature_numerique = models.CharField(_('signature numérique'), max_length=128, blank=True)
    qr_code = models.ImageField(_('QR Code'), upload_to='certificates/qr/', blank=True, null=True)
    pdf = models.FileField(_('PDF du certificat'), upload_to='certificates/pdf/', blank=True, null=True)
    statut = models.CharField(_('statut'), max_length=20, choices=Statut.choices, default=Statut.ACTIF)
    nb_verifications = models.PositiveIntegerField(_('nombre de vérifications'), default=0)
    derniere_verification = models.DateTimeField(_('dernière vérification'), blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('certificat')
        verbose_name_plural = _('certificats')
        ordering = ['-date_delivrance']

    def __str__(self):
        return f"{self.titre} - {self.eleve.full_name}"

    def generate_code_verification(self):
        raw = f"{self.id}{self.eleve.id}{timezone.now().timestamp()}"
        self.code_verification = hashlib.sha256(raw.encode()).hexdigest()[:16].upper()
        return self.code_verification

    def generate_signature(self):
        secret = settings.SECRET_KEY.encode()
        data = f"{self.id}{self.eleve.id}{self.note_obtenue}{self.date_delivrance}".encode()
        self.signature_numerique = hmac.new(secret, data, hashlib.sha256).hexdigest()[:64]
        return self.signature_numerique

    def verify(self, code: str) -> bool:
        return self.code_verification == code and self.statut == self.Statut.ACTIF


class CertificateVerification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    certificate = models.ForeignKey(Certificate, on_delete=models.CASCADE, related_name='verification_logs')
    code_saisi = models.CharField(_('code saisi'), max_length=64)
    ip_address = models.GenericIPAddressField(_('adresse IP'))
    user_agent = models.TextField(_('user agent'), blank=True)
    succes = models.BooleanField(_('succès'), default=False)
    verified_at = models.DateTimeField(_('date de vérification'), default=timezone.now)

    class Meta:
        verbose_name = _('vérification de certificat')
        verbose_name_plural = _('vérifications de certificats')
        ordering = ['-verified_at']

    def __str__(self):
        return f"Vérification {self.code_saisi} - {'OK' if self.succes else 'KO'}"
