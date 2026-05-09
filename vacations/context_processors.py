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
