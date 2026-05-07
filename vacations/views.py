import calendar
from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import EmployeeForm, VacationDecisionForm, VacationRequestForm
from .models import Employee, VacationDecision, VacationRequest
from .pdf import build_decision_pdf, build_request_pdf

MONTH_NAMES = [
    '', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
]


def _month_bounds(request):
    today = timezone.localdate()
    try:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))
        current = date(year, month, 1)
    except (TypeError, ValueError):
        current = today.replace(day=1)
    previous_month = current.month - 1 or 12
    previous_year = current.year - 1 if current.month == 1 else current.year
    next_month = current.month + 1 if current.month < 12 else 1
    next_year = current.year + 1 if current.month == 12 else current.year
    _, last_day = calendar.monthrange(current.year, current.month)
    return {
        'current': current,
        'start': current,
        'end': date(current.year, current.month, last_day),
        'previous': {'year': previous_year, 'month': previous_month},
        'next': {'year': next_year, 'month': next_month},
    }


def _active_overlaps(start_date, end_date):
    return VacationRequest.objects.select_related('employee').filter(
        start_date__lte=end_date,
        end_date__gte=start_date,
    ).exclude(status__in=[VacationRequest.Status.REJECTED, VacationRequest.Status.CANCELLED])


def _calendar_weeks(month_info, requests):
    requests_by_day = {}
    for vacation_request in requests:
        day = max(vacation_request.start_date, month_info['start'])
        end = min(vacation_request.end_date, month_info['end'])
        while day <= end:
            requests_by_day.setdefault(day, []).append(vacation_request)
            day = date.fromordinal(day.toordinal() + 1)

    weeks = []
    month_calendar = calendar.Calendar(firstweekday=0).monthdatescalendar(
        month_info['current'].year,
        month_info['current'].month,
    )
    for week in month_calendar:
        weeks.append([
            {
                'date': day,
                'in_month': day.month == month_info['current'].month,
                'requests': requests_by_day.get(day, []),
                'has_overlap': len(requests_by_day.get(day, [])) > 1,
            }
            for day in week
        ])
    return weeks


@login_required
def dashboard(request):
    requests = VacationRequest.objects.select_related('employee')[:8]
    stats = {
        'employees': Employee.objects.count(),
        'pending': VacationRequest.objects.filter(status=VacationRequest.Status.PENDING).count(),
        'approved': VacationRequest.objects.filter(status=VacationRequest.Status.APPROVED).count(),
        'days': VacationRequest.objects.exclude(
            status=VacationRequest.Status.REJECTED,
        ).aggregate(total=Sum('requested_days'))['total'] or 0,
    }
    by_department = Employee.objects.values('department').annotate(total=Count('id')).order_by('-total')[:6]
    return render(
        request,
        'vacations/dashboard.html',
        {'requests': requests, 'stats': stats, 'by_department': by_department},
    )


@login_required
def employee_list(request):
    q = request.GET.get('q', '').strip()
    employees = Employee.objects.all()
    if q:
        employees = employees.filter(
            Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(department__icontains=q)
        )
    return render(request, 'vacations/employee_list.html', {'employees': employees, 'q': q})


@login_required
def employee_create(request):
    form = EmployeeForm(request.POST or None)
    if form.is_valid():
        employee = form.save()
        messages.success(request, 'Ficha de trabajador creada.')
        return redirect(employee)
    return render(
        request,
        'vacations/form.html',
        {'form': form, 'title': 'Nueva ficha de trabajador', 'submit_label': 'Guardar ficha'},
    )


@login_required
def employee_detail(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    history = employee.requests.select_related('decision').all()
    return render(request, 'vacations/employee_detail.html', {'employee': employee, 'history': history})


@login_required
def request_list(request):
    status = request.GET.get('status', '')
    requests = VacationRequest.objects.select_related('employee').all()
    if status:
        requests = requests.filter(status=status)
    return render(
        request,
        'vacations/request_list.html',
        {'requests': requests, 'status': status, 'statuses': VacationRequest.Status.choices},
    )


@login_required
def request_create(request):
    form = VacationRequestForm(request.POST or None)
    if form.is_valid():
        vacation_request = form.save(commit=False)
        vacation_request.created_by = request.user
        vacation_request.status = VacationRequest.Status.PENDING
        vacation_request.save()
        overlap_count = _active_overlaps(
            vacation_request.start_date,
            vacation_request.end_date,
        ).exclude(pk=vacation_request.pk).count()
        pdf_file = build_request_pdf(vacation_request)
        vacation_request.request_pdf.save(pdf_file.name, pdf_file, save=True)
        if overlap_count:
            messages.warning(
                request,
                f'Atención: hay {overlap_count} solicitud(es) activas que se solapan con este periodo. '
                'Revísalo en el calendario.',
            )
        messages.success(request, 'Solicitud registrada y PDF generado para firma.')
        return redirect(vacation_request)
    return render(
        request,
        'vacations/form.html',
        {'form': form, 'title': 'Nueva solicitud de vacaciones', 'submit_label': 'Generar solicitud PDF'},
    )


@login_required
def request_detail(request, pk):
    vacation_request = get_object_or_404(
        VacationRequest.objects.select_related('employee', 'created_by'),
        pk=pk,
    )
    return render(request, 'vacations/request_detail.html', {'vacation_request': vacation_request})


@login_required
def request_decide(request, pk):
    vacation_request = get_object_or_404(VacationRequest, pk=pk)
    if hasattr(vacation_request, 'decision'):
        messages.info(request, 'Esta solicitud ya tiene una resolución.')
        return redirect(vacation_request)
    form = VacationDecisionForm(request.POST or None)
    if form.is_valid():
        decision = form.save(commit=False)
        decision.request = vacation_request
        decision.decided_by = request.user
        decision.save()
        vacation_request.status = (
            VacationRequest.Status.APPROVED
            if decision.decision == VacationDecision.Decision.APPROVED
            else VacationRequest.Status.REJECTED
        )
        vacation_request.save(update_fields=['status', 'updated_at'])
        pdf_file = build_decision_pdf(decision)
        decision.decision_pdf.save(pdf_file.name, pdf_file, save=True)
        messages.success(request, 'Resolución registrada y PDF de empresa generado.')
        return redirect(vacation_request)
    return render(
        request,
        'vacations/form.html',
        {'form': form, 'title': 'Resolver solicitud', 'submit_label': 'Generar resolución PDF'},
    )


@login_required
def vacation_calendar(request):
    month_info = _month_bounds(request)
    visible_requests = _active_overlaps(month_info['start'], month_info['end'])
    weeks = _calendar_weeks(month_info, visible_requests)
    overlap_days = sum(1 for week in weeks for day in week if day['has_overlap'])
    return render(
        request,
        'vacations/calendar.html',
        {
            'weeks': weeks,
            'month_info': month_info,
            'month_name': f"{MONTH_NAMES[month_info['current'].month]} {month_info['current'].year}",
            'weekdays': ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'],
            'overlap_days': overlap_days,
            'visible_requests': visible_requests,
        },
    )
