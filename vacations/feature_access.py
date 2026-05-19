from django.contrib import messages
from django.shortcuts import redirect

from .models import PlatformFeaturePermission


MANAGER_GROUPS = {'RRHH', 'Dirección', 'Administrador'}


FEATURE_PATHS = [
    ('/partes/', 'daily_reports'),
    ('/albaranes/', 'customer_delivery_notes'),
    ('/faena/', 'daily_jobs'),
    ('/mi-faena/', 'daily_jobs'),
    ('/ordenes-trabajo/', 'work_orders'),
    ('/vacaciones/', 'vacations'),
    ('/solicitudes/', 'vacations'),
    ('/requests/', 'vacations'),
]


def is_feature_manager(user):
    if not user.is_authenticated:
        return False

    if user.is_superuser or user.is_staff:
        return True

    return user.groups.filter(name__in=MANAGER_GROUPS).exists()


def can_use_feature(user, feature):
    if not user.is_authenticated:
        return False

    if is_feature_manager(user):
        return True

    try:
        permissions = user.feature_permissions
    except PlatformFeaturePermission.DoesNotExist:
        return True

    field = f'can_use_{feature}'
    return bool(getattr(permissions, field, True))


class FeatureAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)

        if user and user.is_authenticated and not is_feature_manager(user):
            path = request.path or ''

            for prefix, feature in FEATURE_PATHS:
                if path.startswith(prefix) and not can_use_feature(user, feature):
                    messages.error(request, 'No tienes acceso a esta función de la plataforma.')
                    return redirect('dashboard')

        return self.get_response(request)
