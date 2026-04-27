import io
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import segno
from django.core.files.base import ContentFile

from .models import Certificate, CertificateVerification


def verify_certificate_view(request, code):
    """Page publique de vérification de certificat."""
    certificate = get_object_or_404(Certificate, code_verification=code)
    succes = certificate.verify(code)

    CertificateVerification.objects.create(
        certificate=certificate,
        code_saisi=code,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:512],
        succes=succes,
    )

    if succes:
        certificate.nb_verifications += 1
        certificate.derniere_verification = timezone.now()
        certificate.save()

    return render(request, 'certifications/verify.html', {
        'certificate': certificate,
        'succes': succes,
    })


def verify_certificate_api(request):
    """API publique de vérification de certificat."""
    code = request.GET.get('code', '')
    if not code:
        return JsonResponse({'valid': False, 'error': 'Code manquant'}, status=400)

    try:
        cert = Certificate.objects.get(code_verification=code)
        valid = cert.verify(code)

        CertificateVerification.objects.create(
            certificate=cert,
            code_saisi=code,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:512],
            succes=valid,
        )

        if valid:
            cert.nb_verifications += 1
            cert.derniere_verification = timezone.now()
            cert.save()

        return JsonResponse({
            'valid': valid,
            'certificate': {
                'titre': cert.titre,
                'eleve': cert.eleve.full_name,
                'type': cert.get_type_certificat_display(),
                'date_delivrance': cert.date_delivrance.strftime('%d/%m/%Y'),
                'institution': cert.institution,
                'statut': cert.get_statut_display(),
            } if valid else None
        })
    except Certificate.DoesNotExist:
        return JsonResponse({'valid': False, 'error': 'Certificat introuvable'}, status=404)


@login_required
def my_certificates_view(request):
    certificates = Certificate.objects.filter(eleve=request.user).select_related('matiere')
    return render(request, 'certificates/my_certificates.html', {'certificates': certificates})
