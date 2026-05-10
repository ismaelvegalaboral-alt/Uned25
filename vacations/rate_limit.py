from datetime import timedelta

from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone

from .models import LoginAttempt


def get_client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def get_login_username(request):
    for key in ('username', 'email', 'login'):
        value = request.POST.get(key)
        if value:
            return value.strip().lower()
    return ''


class LoginRateLimitMiddleware:
    """Protección del login web.

    Bloquea:
    - misma IP + mismo usuario tras varios fallos;
    - una IP completa solo si acumula muchos fallos totales.

    Así evitamos que una persona bloquee a todos por equivocarse unas veces.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.max_pair_attempts = int(getattr(settings, 'LOGIN_RATE_LIMIT_ATTEMPTS', 5))
        self.max_ip_attempts = int(getattr(settings, 'LOGIN_RATE_LIMIT_IP_ATTEMPTS', 20))
        self.window_minutes = int(getattr(settings, 'LOGIN_RATE_LIMIT_WINDOW_MINUTES', 10))

    def __call__(self, request):
        is_login_post = (
            request.method == 'POST'
            and request.path.rstrip('/').endswith('/login')
        )

        if not is_login_post:
            return self.get_response(request)

        ip = get_client_ip(request)
        username = get_login_username(request)
        window_start = timezone.now() - timedelta(minutes=self.window_minutes)

        # Fallos generales desde esta IP. Solo bloquea si son muchos.
        ip_failures = LoginAttempt.objects.filter(
            ip_address=ip,
            success=False,
            blocked=False,
            created_at__gte=window_start,
        ).count()

        # Fallos de esta IP contra este usuario concreto.
        pair_failures = 0
        if username:
            pair_failures = LoginAttempt.objects.filter(
                ip_address=ip,
                username=username,
                success=False,
                blocked=False,
                created_at__gte=window_start,
            ).count()

        blocked_by_pair = bool(username and pair_failures >= self.max_pair_attempts)
        blocked_by_ip = ip_failures >= self.max_ip_attempts

        if blocked_by_pair or blocked_by_ip:
            LoginAttempt.objects.create(
                ip_address=ip,
                username=username,
                path=request.path,
                success=False,
                blocked=True,
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:1000],
            )

            if blocked_by_ip:
                message = 'Demasiados intentos de inicio de sesión desde esta conexión. Espera unos minutos antes de volver a intentarlo.'
            else:
                message = 'Demasiados intentos para este usuario desde esta conexión. Espera unos minutos antes de volver a intentarlo.'

            return HttpResponse(
                message,
                status=429,
                content_type='text/plain; charset=utf-8',
            )

        response = self.get_response(request)

        success = bool(getattr(request, 'user', None) and request.user.is_authenticated)

        LoginAttempt.objects.create(
            ip_address=ip,
            username=username,
            path=request.path,
            success=success,
            blocked=False,
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:1000],
        )

        return response
