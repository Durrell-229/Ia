from django.conf import settings


def global_settings(request):
    return {
        'SITE_NAME': 'Académie Numérique',
        'SITE_SLOGAN': 'La plateforme mondiale de composition et d\'évaluation intelligente',
        'PRIMARY_COLOR': '#6366F1',
        'SECONDARY_COLOR': '#8B5CF6',
        'ACCENT_COLOR': '#06B6D4',
        'AI_PROVIDER': getattr(settings, 'AI_PROVIDER', 'gemini'),
    }
