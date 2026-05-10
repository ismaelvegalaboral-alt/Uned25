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
    def __init__(self, get_response):
        self.get_response = get_response
        self.max_attempts = int(getattr(settings, 'LOGIN_RATE_LIMIT_ATTEMPTS', 5))
        self.window_minutes = int(getattr(settings, 'LOGIN_RATE_LIMIT_WINDOW_MINUTES', 10))

    def __call__(self, request):
        is_login_post = (
            request.method == 'POST'
            and request.path.rstrip('/').endswith('/login')
            and not getattr(request.user, 'is_authenticated', False)
        )

        if not is_login_post:
            return self.get_response(request)

        ip = get_client_ip(request)
        username = get_login_username(request)
        window_start = timezone.now() - timedelta(minutes=self.window_minutes)

        ip_failures = LoginAttempt.objects.filter(
            ip_address=ip,
            success=False,
            created_at__gte=window_start,
        ).count()

        user_failures = 0
        if username:
            user_failures = LoginAttempt.objects.filter(
                username=username,
                success=False,
                created_at__gte=window_start,
            ).count()

        if ip_failures >= self.max_attempts or user_failures >= self.max_attempts:
            LoginAttempt.objects.create(
                ip_address=ip,
                username=username,
                path=request.path,
                success=False,
                blocked=True,
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:1000],
            )
            return HttpResponse(
                'Demasiados intentos de inicio de sesión. Espera unos minutos antes de volver a intentarlo.',
                status=429,
                content_type='text/plain; charset=utf-8',
            )

        response = self.get_response(request)

        success = bool(getattr(request.user, 'is_authenticated', False))

        LoginAttempt.objects.create(
            ip_address=ip,
            username=username,
            path=request.path,
            success=success,
            blocked=False,
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:1000],
        )

        return response
