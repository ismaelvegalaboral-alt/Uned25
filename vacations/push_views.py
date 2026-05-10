import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from .models import PushSubscription
from .push import notify_current_user, push_is_configured


@login_required
def notification_settings(request):
    return render(
        request,
        'vacations/notification_settings.html',
        {
            'push_configured': push_is_configured(),
            'public_key': getattr(settings, 'WEBPUSH_VAPID_PUBLIC_KEY', ''),
        },
    )


@login_required
@require_GET
def public_key(request):
    return JsonResponse({
        'enabled': push_is_configured(),
        'publicKey': getattr(settings, 'WEBPUSH_VAPID_PUBLIC_KEY', ''),
    })


@login_required
@require_POST
def subscribe(request):
    if not push_is_configured():
        return JsonResponse({'ok': False, 'error': 'Push no configurado en servidor.'}, status=400)

    try:
        data = json.loads(request.body.decode('utf-8'))
        keys = data.get('keys', {})
        endpoint = data['endpoint']
        p256dh = keys['p256dh']
        auth = keys['auth']
    except Exception:
        return JsonResponse({'ok': False, 'error': 'Suscripción no válida.'}, status=400)

    PushSubscription.objects.update_or_create(
        endpoint=endpoint,
        defaults={
            'user': request.user,
            'p256dh': p256dh,
            'auth': auth,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'is_active': True,
        },
    )

    return JsonResponse({'ok': True})


@login_required
@require_POST
def test_notification(request):
    sent = notify_current_user(
        request.user,
        title='Notificación de prueba',
        body='Las notificaciones de Kalpae Ausencias funcionan correctamente.',
        url='/',
    )
    return JsonResponse({'ok': sent > 0, 'sent': sent})
