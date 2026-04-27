import logging
from django.utils import timezone

from .models import AuditLog

logger = logging.getLogger(__name__)


def log_audit(user, action, resource_type, description, resource_id='', details=None, severity='info', ip_address=None, user_agent='', session_id=''):
    """Enregistre une entrée dans le journal d'audit."""
    try:
        AuditLog.objects.create(
            user=user,
            action=action,
            severity=severity,
            resource_type=resource_type,
            resource_id=str(resource_id),
            description=description,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent[:512] if user_agent else '',
            session_id=session_id,
        )
    except Exception as e:
        logger.error(f"Erreur écriture audit log: {e}")
