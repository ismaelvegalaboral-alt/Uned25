from __future__ import annotations

from django.contrib.auth.models import Group

GROUP_WORKER = 'Trabajador'
GROUP_HR = 'RRHH'
GROUP_DIRECTION = 'Dirección'
GROUP_ADMIN = 'Administrador'

PLATFORM_GROUPS = [GROUP_WORKER, GROUP_HR, GROUP_DIRECTION, GROUP_ADMIN]


def ensure_platform_groups() -> None:
    for name in PLATFORM_GROUPS:
        Group.objects.get_or_create(name=name)


def user_in_group(user, group_name: str) -> bool:
    if not user or not user.is_authenticated:
        return False
    return user.groups.filter(name=group_name).exists()


def is_platform_admin(user) -> bool:
    return bool(
        user
        and user.is_authenticated
        and (user.is_superuser or user_in_group(user, GROUP_ADMIN))
    )


def is_hr(user) -> bool:
    return bool(user and user.is_authenticated and (is_platform_admin(user) or user_in_group(user, GROUP_HR)))


def is_direction(user) -> bool:
    return bool(user and user.is_authenticated and (is_platform_admin(user) or user_in_group(user, GROUP_DIRECTION)))


def is_worker(user) -> bool:
    return bool(user and user.is_authenticated and user_in_group(user, GROUP_WORKER))


def can_manage_employees(user) -> bool:
    return is_hr(user) or is_platform_admin(user)


def can_view_all_requests(user) -> bool:
    return is_hr(user) or is_direction(user) or is_platform_admin(user)


def can_view_calendar(user) -> bool:
    return can_view_all_requests(user)


def can_decide_requests(user) -> bool:
    return is_direction(user) or is_platform_admin(user)


def can_create_requests_for_others(user) -> bool:
    return is_hr(user) or is_platform_admin(user)


def get_employee_for_user(user):
    if not user or not user.is_authenticated:
        return None

    # Import inside the function to avoid circular imports during app loading.
    from .models import Employee

    return Employee.objects.filter(user=user).first()


def can_create_own_request(user) -> bool:
    return is_worker(user) and get_employee_for_user(user) is not None


def can_create_request(user) -> bool:
    return can_create_requests_for_others(user) or can_create_own_request(user)


def can_access_employee(user, employee) -> bool:
    if can_manage_employees(user):
        return True
    return bool(employee and employee.user_id == user.id)


def can_access_request(user, vacation_request) -> bool:
    if can_view_all_requests(user):
        return True
    return bool(vacation_request.employee.user_id == user.id)


def role_label(user) -> str:
    if is_platform_admin(user):
        return GROUP_ADMIN
    if is_hr(user):
        return GROUP_HR
    if is_direction(user):
        return GROUP_DIRECTION
    if is_worker(user):
        return GROUP_WORKER
    if user and user.is_authenticated:
        return 'Usuario sin rol'
    return 'No autenticado'
