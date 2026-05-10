import logging

from .models import AuditLog

logger = logging.getLogger(__name__)


def get_client_ip(request):
    if not request:
        return None
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def log_action(actor=None, action='', obj=None, request=None, metadata=None):
    try:
        AuditLog.objects.create(
            actor=actor if getattr(actor, 'is_authenticated', False) else None,
            action=action,
            model_name=obj.__class__.__name__ if obj is not None else '',
            object_id=str(getattr(obj, 'pk', '') or ''),
            object_repr=str(obj)[:255] if obj is not None else '',
            metadata=metadata or {},
            ip_address=get_client_ip(request),
            user_agent=(request.META.get('HTTP_USER_AGENT', '')[:1000] if request else ''),
        )
    except Exception:
        logger.exception('No se pudo guardar auditoría: %s', action)
