import json
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.urls import reverse
from pywebpush import WebPushException, webpush

from .models import PushSubscription

try:
    from .permissions import GROUP_ADMIN, GROUP_DIRECTION, GROUP_HR
except Exception:
    GROUP_ADMIN = 'Administrador'
    GROUP_DIRECTION = 'Dirección'
    GROUP_HR = 'RRHH'

logger = logging.getLogger(__name__)


REVIEWER_GROUPS = [GROUP_HR, GROUP_DIRECTION, GROUP_ADMIN]


def push_is_configured() -> bool:
    return bool(
        getattr(settings, 'WEBPUSH_ENABLED', False)
        and getattr(settings, 'WEBPUSH_VAPID_PUBLIC_KEY', '')
        and getattr(settings, 'WEBPUSH_VAPID_PRIVATE_KEY', '')
    )


def _absolute_url(path: str) -> str:
    site_url = getattr(settings, 'SITE_URL', '').rstrip('/')
    return f'{site_url}{path}' if site_url else path


def _send(subscription: PushSubscription, payload: dict) -> bool:
    if not push_is_configured():
        return False

    subscription_info = {
        'endpoint': subscription.endpoint,
        'keys': {
            'p256dh': subscription.p256dh,
            'auth': subscription.auth,
        },
    }

    claims = {'sub': getattr(settings, 'WEBPUSH_VAPID_SUB', 'mailto:admin@example.com')}

    try:
        webpush(
            subscription_info=subscription_info,
            data=json.dumps(payload),
            vapid_private_key=settings.WEBPUSH_VAPID_PRIVATE_KEY,
            vapid_claims=claims,
        )
        return True
    except WebPushException as exc:
        status_code = getattr(getattr(exc, 'response', None), 'status_code', None)
        if status_code in {404, 410}:
            subscription.is_active = False
            subscription.save(update_fields=['is_active', 'updated_at'])
        logger.exception('Error enviando push a %s', subscription.user)
        return False
    except Exception:
        logger.exception('Error inesperado enviando push a %s', subscription.user)
        return False


def notify_users(users, title: str, body: str, url: str = '/') -> int:
    if not push_is_configured():
        logger.info('Push no configurado; no se envía notificación.')
        return 0

    user_ids = []
    for user in users:
        if user and getattr(user, 'id', None) and user.id not in user_ids:
            user_ids.append(user.id)

    if not user_ids:
        logger.info('No hay usuarios destino para push: %s', title)
        return 0

    subscriptions = PushSubscription.objects.select_related('user').filter(
        user_id__in=user_ids,
        is_active=True,
    )

    payload = {
        'title': title,
        'body': body,
        'url': _absolute_url(url),
        'icon': '/static/vacations/pwa/kalpae-white-icon-192.png',
        'badge': '/static/vacations/pwa/kalpae-white-icon-192.png',
    }

    sent = 0
    for subscription in subscriptions:
        if _send(subscription, payload):
            sent += 1

    logger.info('Push "%s" enviado a %s dispositivo(s). Usuarios destino: %s', title, sent, user_ids)
    return sent


def notify_current_user(user, title: str, body: str, url: str = '/') -> int:
    return notify_users([user], title, body, url)


def reviewer_users():
    """Usuarios que deben recibir avisos de nuevas solicitudes.

    Además de RRHH/Dirección/Administrador, incluye superusuarios y staff.
    Esto evita que un superusuario se quede sin avisos por no tener grupo asignado.
    """
    User = get_user_model()
    return User.objects.filter(
        Q(groups__name__in=REVIEWER_GROUPS)
        | Q(is_superuser=True)
        | Q(is_staff=True),
        is_active=True,
    ).distinct()


def notify_new_request(vacation_request) -> int:
    users = reviewer_users()
    url = reverse('request_detail', args=[vacation_request.pk])
    absence_type = getattr(vacation_request, 'absence_type_label', None)
    if absence_type is None:
        absence_type = vacation_request.get_absence_type_display() if hasattr(vacation_request, 'get_absence_type_display') else 'ausencia'

    return notify_users(
        users,
        title='Nueva solicitud de ausencia',
        body=f'{vacation_request.employee.full_name} ha enviado una solicitud de {absence_type.lower()}.',
        url=url,
    )


def notify_request_decision(vacation_request) -> int:
    users = []

    employee_user = getattr(vacation_request.employee, 'user', None)
    if employee_user:
        users.append(employee_user)

    created_by = getattr(vacation_request, 'created_by', None)
    if created_by and created_by not in users:
        users.append(created_by)

    if not users:
        return 0

    status = vacation_request.get_status_display()
    url = reverse('request_detail', args=[vacation_request.pk])
    return notify_users(
        users,
        title=f'Solicitud {status.lower()}',
        body=f'Tu solicitud de ausencia ha sido {status.lower()}.',
        url=url,
    )
