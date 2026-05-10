import json
import logging

from django.conf import settings
from django.urls import reverse
from pywebpush import WebPushException, webpush

from .models import PushSubscription
from .permissions import GROUP_ADMIN, GROUP_DIRECTION, GROUP_HR

logger = logging.getLogger(__name__)


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
        return 0

    user_ids = [user.id for user in users if user and getattr(user, 'id', None)]
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
    return sent


def notify_current_user(user, title: str, body: str, url: str = '/') -> int:
    return notify_users([user], title, body, url)


def _users_in_groups(group_names):
    from django.contrib.auth import get_user_model

    User = get_user_model()
    return User.objects.filter(
        is_active=True,
        groups__name__in=group_names,
    ).distinct()


def notify_new_request(vacation_request) -> int:
    users = _users_in_groups([GROUP_HR, GROUP_DIRECTION, GROUP_ADMIN])
    url = reverse('request_detail', args=[vacation_request.pk])
    return notify_users(
        users,
        title='Nueva solicitud de ausencia',
        body=f'{vacation_request.employee.full_name} ha enviado una solicitud de {vacation_request.absence_type_label.lower()}.',
        url=url,
    )


def notify_request_decision(vacation_request) -> int:
    employee_user = getattr(vacation_request.employee, 'user', None)
    if not employee_user:
        return 0

    status = vacation_request.get_status_display()
    url = reverse('request_detail', args=[vacation_request.pk])
    return notify_current_user(
        employee_user,
        title=f'Solicitud {status.lower()}',
        body=f'Tu solicitud de ausencia ha sido {status.lower()}.',
        url=url,
    )
