from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from django.utils import timezone

from .models import VacationRequest


ACTIVE_STATUSES = [
    VacationRequest.Status.DRAFT,
    VacationRequest.Status.PENDING,
    VacationRequest.Status.APPROVED,
]


@dataclass(frozen=True)
class PolicyFlag:
    severity: str
    title: str
    detail: str


@dataclass(frozen=True)
class PolicyReview:
    flags: list[PolicyFlag]
    overlap_count: int
    approved_overlap_count: int
    business_days: int
    notice_days: int
    already_committed_days: Decimal
    remaining_after_request: Decimal

    @property
    def has_flags(self) -> bool:
        return bool(self.flags)

    @property
    def has_blocking_flags(self) -> bool:
        return any(flag.severity == 'critical' for flag in self.flags)

    @property
    def severity(self) -> str:
        if any(flag.severity == 'critical' for flag in self.flags):
            return 'critical'
        if any(flag.severity == 'warning' for flag in self.flags):
            return 'warning'
        return 'ok'

    @property
    def label(self) -> str:
        return {
            'critical': 'Revisión obligatoria',
            'warning': 'Revisar antes de aprobar',
            'ok': 'Sin incidencias aparentes',
        }[self.severity]


def business_days_between(start: date, end: date) -> int:
    """Counts Monday-Friday days, inclusive. Public holidays are not included yet."""
    if not start or not end or end < start:
        return 0
    total = 0
    current = start
    while current <= end:
        if current.weekday() < 5:
            total += 1
        current = date.fromordinal(current.toordinal() + 1)
    return total


def committed_days_for_employee(vacation_request: VacationRequest) -> Decimal:
    qs = VacationRequest.objects.filter(
        employee=vacation_request.employee,
        start_date__year=vacation_request.start_date.year,
    ).exclude(status__in=[VacationRequest.Status.REJECTED, VacationRequest.Status.CANCELLED])

    if vacation_request.pk:
        qs = qs.exclude(pk=vacation_request.pk)

    return sum((item.requested_days for item in qs), Decimal('0'))


def overlapping_requests(vacation_request: VacationRequest):
    qs = VacationRequest.objects.select_related('employee').filter(
        employee=vacation_request.employee,
        start_date__lte=vacation_request.end_date,
        end_date__gte=vacation_request.start_date,
    ).exclude(status__in=[VacationRequest.Status.REJECTED, VacationRequest.Status.CANCELLED])

    if vacation_request.pk:
        qs = qs.exclude(pk=vacation_request.pk)

    return qs


def department_overlaps(vacation_request: VacationRequest):
    department = vacation_request.employee.department
    if not department:
        return VacationRequest.objects.none()

    qs = VacationRequest.objects.select_related('employee').filter(
        employee__department=department,
        start_date__lte=vacation_request.end_date,
        end_date__gte=vacation_request.start_date,
    ).exclude(status__in=[VacationRequest.Status.REJECTED, VacationRequest.Status.CANCELLED])

    if vacation_request.pk:
        qs = qs.exclude(pk=vacation_request.pk)

    return qs


def evaluate_request(vacation_request: VacationRequest, today: date | None = None) -> PolicyReview:
    today = today or timezone.localdate()
    flags: list[PolicyFlag] = []

    business_days = business_days_between(vacation_request.start_date, vacation_request.end_date)
    notice_days = (vacation_request.start_date - today).days
    already_committed = committed_days_for_employee(vacation_request)
    remaining_after = Decimal(vacation_request.employee.annual_days) - already_committed - vacation_request.requested_days

    same_employee_overlaps = overlapping_requests(vacation_request)
    department_conflicts = department_overlaps(vacation_request)
    approved_department_conflicts = department_conflicts.filter(status=VacationRequest.Status.APPROVED)

    if vacation_request.end_date < vacation_request.start_date:
        flags.append(PolicyFlag(
            'critical',
            'Fechas incoherentes',
            'La fecha de fin no puede ser anterior a la fecha de inicio.',
        ))

    if vacation_request.requested_days <= 0:
        flags.append(PolicyFlag(
            'critical',
            'Días solicitados no válidos',
            'La solicitud debe tener al menos un día de vacaciones.',
        ))

    if business_days and vacation_request.requested_days > Decimal(business_days):
        flags.append(PolicyFlag(
            'critical',
            'Días superiores a laborables',
            f'Se piden {vacation_request.requested_days:g} días, pero el periodo contiene {business_days} laborables de lunes a viernes.',
        ))

    if remaining_after < 0:
        flags.append(PolicyFlag(
            'critical',
            'Saldo anual insuficiente',
            f'Tras esta solicitud el saldo quedaría en {remaining_after:g} días.',
        ))

    if same_employee_overlaps.exists():
        flags.append(PolicyFlag(
            'critical',
            'Duplicidad del trabajador',
            f'El trabajador ya tiene {same_employee_overlaps.count()} solicitud(es) activa(s) que coinciden con estas fechas.',
        ))

    if approved_department_conflicts.exists():
        flags.append(PolicyFlag(
            'warning',
            'Solape departamental aprobado',
            f'Hay {approved_department_conflicts.count()} solicitud(es) aprobada(s) del mismo departamento en el periodo.',
        ))
    elif department_conflicts.exists():
        flags.append(PolicyFlag(
            'warning',
            'Solape departamental pendiente',
            f'Hay {department_conflicts.count()} solicitud(es) activa(s) del mismo departamento que conviene revisar.',
        ))

    if notice_days < 0:
        flags.append(PolicyFlag(
            'warning',
            'Solicitud retroactiva',
            'La fecha de inicio ya ha pasado. Conviene documentar autorización excepcional.',
        ))
    elif notice_days < 7:
        flags.append(PolicyFlag(
            'warning',
            'Preaviso inferior a 7 días',
            f'La solicitud se presenta con {notice_days} día(s) de margen.',
        ))

    if not vacation_request.employee.national_id:
        flags.append(PolicyFlag(
            'warning',
            'Ficha incompleta',
            'Falta DNI/NIE en la ficha del trabajador. Recomendable completarlo antes de archivar el PDF.',
        ))

    if not vacation_request.employee.department:
        flags.append(PolicyFlag(
            'warning',
            'Departamento no informado',
            'Sin departamento no se puede valorar correctamente el impacto organizativo del solape.',
        ))

    return PolicyReview(
        flags=flags,
        overlap_count=department_conflicts.count(),
        approved_overlap_count=approved_department_conflicts.count(),
        business_days=business_days,
        notice_days=notice_days,
        already_committed_days=already_committed,
        remaining_after_request=remaining_after,
    )
