from .permissions import (
    can_create_request,
    can_decide_requests,
    can_manage_employees,
    can_view_all_requests,
    can_view_calendar,
    role_label,
)


def role_flags(request):
    user = getattr(request, 'user', None)
    return {
        'role_label': role_label(user),
        'can_manage_employees': can_manage_employees(user),
        'can_view_all_requests': can_view_all_requests(user),
        'can_view_calendar': can_view_calendar(user),
        'can_decide_requests': can_decide_requests(user),
        'can_create_request': can_create_request(user),
    }

def feature_flags(request):
    try:
        from .feature_access import can_use_feature, is_feature_manager
    except Exception:
        return {}

    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {
            'is_feature_manager': False,
            'can_use_vacations': False,
            'can_use_daily_reports': False,
            'can_use_customer_delivery_notes': False,
            'can_use_daily_jobs': False,
            'can_use_work_orders': False,
        }

    return {
        'is_feature_manager': is_feature_manager(user),
        'can_use_vacations': can_use_feature(user, 'vacations'),
        'can_use_daily_reports': can_use_feature(user, 'daily_reports'),
        'can_use_customer_delivery_notes': can_use_feature(user, 'customer_delivery_notes'),
        'can_use_daily_jobs': can_use_feature(user, 'daily_jobs'),
        'can_use_work_orders': can_use_feature(user, 'work_orders'),
    }