from django.contrib import admin
from .models import Certificate, CertificateVerification


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ['code_verification', 'titre', 'eleve', 'type_certificat', 'statut', 'date_delivrance', 'nb_verifications']
    list_filter = ['type_certificat', 'statut', 'date_delivrance']
    search_fields = ['code_verification', 'titre', 'eleve__email', 'eleve__first_name']
    readonly_fields = ['code_verification', 'signature_numerique']


@admin.register(CertificateVerification)
class CertificateVerificationAdmin(admin.ModelAdmin):
    list_display = ['certificate', 'code_saisi', 'succes', 'ip_address', 'verified_at']
    list_filter = ['succes', 'verified_at']
