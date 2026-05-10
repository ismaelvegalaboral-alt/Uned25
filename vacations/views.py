import calendar
from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q, Sum
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import EmployeeForm, VacationDecisionForm, VacationRequestForm
from .models import Employee, VacationDecision, VacationRequest
from .notifications import send_new_request_notification
from .pdf import build_decision_pdf, build_request_pdf
from .push import notify_new_request, notify_request_decision
from .permissions import (
    can_access_employee,
    can_access_request,
    can_create_request,
    can_decide_requests,
    can_manage_employees,
    can_view_all_requests,
    can_view_calendar,
    get_employee_for_user,
)
from .services import evaluate_request


def _pdf_response(pdf_file, filename):
    response = HttpResponse(pdf_file.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response['Cache-Control'] = 'no-store'
    return response


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


def _requests_requiring_attention(limit=8):
    candidates = VacationRequest.objects.select_related('employee').filter(
        status=VacationRequest.Status.PENDING,
    ).order_by('start_date')[:50]

    attention = []
    for vacation_request in candidates:
        review = evaluate_request(vacation_request)
        if review.has_flags:
            attention.append({'request': vacation_request, 'review': review})
        if len(attention) >= limit:
            break
    return attention


@login_required
def dashboard(request):
    if can_view_all_requests(request.user):
        requests = VacationRequest.objects.select_related('employee')[:8]
        attention_requests = _requests_requiring_attention()
        stats = {
            'employees': Employee.objects.count(),
            'pending': VacationRequest.objects.filter(status=VacationRequest.Status.PENDING).count(),
            'approved': VacationRequest.objects.filter(status=VacationRequest.Status.APPROVED).count(),
            'attention': len(attention_requests),
            'days': VacationRequest.objects.exclude(
                status__in=[VacationRequest.Status.REJECTED, VacationRequest.Status.CANCELLED],
            ).aggregate(total=Sum('requested_days'))['total'] or 0,
        }
        by_department = Employee.objects.values('department').annotate(total=Count('id')).order_by('-total')[:6]
        return render(
            request,
            'vacations/dashboard.html',
            {
                'requests': requests,
                'stats': stats,
                'by_department': by_department,
                'attention_requests': attention_requests,
                'worker_dashboard': False,
            },
        )

    employee = get_employee_for_user(request.user)

    # Important: keep the unsliced queryset for counts/filters.
    # Django raises "Cannot filter a query once a slice has been taken" if we do
    # employee.requests.all()[:8].filter(...).
    all_my_requests = (
        VacationRequest.objects.select_related('employee')
        .filter(employee=employee)
        .order_by('-created_at')
        if employee
        else VacationRequest.objects.none()
    )
    recent_requests = all_my_requests[:8]

    stats = {
        'my_requests': all_my_requests.count(),
        'pending': all_my_requests.filter(status=VacationRequest.Status.PENDING).count(),
        'approved': all_my_requests.filter(status=VacationRequest.Status.APPROVED).count(),
        'rejected': all_my_requests.filter(status=VacationRequest.Status.REJECTED).count(),
    }
    return render(
        request,
        'vacations/dashboard.html',
        {
            'requests': recent_requests,
            'stats': stats,
            'worker_dashboard': True,
            'linked_employee': employee,
        },
    )


@login_required
def employee_list(request):
    if not can_manage_employees(request.user):
        raise PermissionDenied
    q = request.GET.get('q', '').strip()
    employees = Employee.objects.select_related('user').all()
    if q:
        employees = employees.filter(
            Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(department__icontains=q)
            | Q(national_id__icontains=q)
            | Q(user__username__icontains=q)
        )
    return render(request, 'vacations/employee_list.html', {'employees': employees, 'q': q})


@login_required
def employee_create(request):
    if not can_manage_employees(request.user):
        raise PermissionDenied
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
    employee = get_object_or_404(Employee.objects.select_related('user'), pk=pk)
    if not can_access_employee(request.user, employee):
        raise PermissionDenied
    history = employee.requests.select_related('decision').all()
    return render(request, 'vacations/employee_detail.html', {'employee': employee, 'history': history})


@login_required
def request_list(request):
    status = request.GET.get('status', '')
    requests = VacationRequest.objects.select_related('employee', 'employee__user').all()

    if not can_view_all_requests(request.user):
        employee = get_employee_for_user(request.user)
        requests = requests.filter(employee=employee) if employee else VacationRequest.objects.none()

    if status:
        requests = requests.filter(status=status)
    return render(
        request,
        'vacations/request_list.html',
        {
            'requests': requests,
            'status': status,
            'statuses': VacationRequest.Status.choices,
            'all_requests_view': can_view_all_requests(request.user),
        },
    )


@login_required
def request_create(request):
    if not can_create_request(request.user):
        messages.error(
            request,
            'Tu usuario no tiene permisos para crear solicitudes o no está vinculado a una ficha de trabajador.',
        )
        return redirect('dashboard')

    form = VacationRequestForm(request.POST or None, request.FILES or None, user=request.user)
    if form.is_valid():
        vacation_request = form.save(commit=False)
        vacation_request.created_by = request.user
        vacation_request.status = VacationRequest.Status.PENDING
        vacation_request.save()

        review = evaluate_request(vacation_request)
        pdf_file = build_request_pdf(vacation_request)
        vacation_request.request_pdf.save(pdf_file.name, pdf_file, save=True)

        notification_sent = send_new_request_notification(vacation_request)
        notify_new_request(vacation_request)

        if review.has_blocking_flags:
            messages.error(
                request,
                'Solicitud registrada, pero requiere revisión obligatoria de RRHH antes de aprobarse.',
            )
        elif review.has_flags:
            messages.warning(
                request,
                'Solicitud registrada con alertas de RRHH. Revísala antes de resolver.',
            )
        else:
            messages.success(request, 'Solicitud registrada y PDF generado para firma.')

        if notification_sent:
            messages.info(request, 'Administración ha recibido un aviso automático por email.')
        else:
            messages.warning(
                request,
                'La solicitud se guardó correctamente, pero no se pudo enviar el aviso automático por email.',
            )

        return redirect(vacation_request)
    return render(
        request,
        'vacations/form.html',
        {'form': form, 'title': 'Nueva solicitud de ausencia', 'submit_label': 'Generar solicitud PDF'},
    )


@login_required
def request_detail(request, pk):
    vacation_request = get_object_or_404(
        VacationRequest.objects.select_related('employee', 'employee__user', 'created_by'),
        pk=pk,
    )
    if not can_access_request(request.user, vacation_request):
        raise PermissionDenied
    return render(
        request,
        'vacations/request_detail.html',
        {
            'vacation_request': vacation_request,
            'hr_review': evaluate_request(vacation_request),
            'can_resolve_this_request': can_decide_requests(request.user),
        },
    )


@login_required
def request_pdf_download(request, pk):
    vacation_request = get_object_or_404(
        VacationRequest.objects.select_related('employee', 'employee__user', 'created_by'),
        pk=pk,
    )
    if not can_access_request(request.user, vacation_request):
        raise PermissionDenied
    pdf_file = build_request_pdf(vacation_request)
    vacation_request.request_pdf.save(pdf_file.name, pdf_file, save=True)
    pdf_file.seek(0)
    return _pdf_response(pdf_file, pdf_file.name)


@login_required
def decision_pdf_download(request, pk):
    vacation_request = get_object_or_404(
        VacationRequest.objects.select_related('employee', 'employee__user', 'decision__decided_by'),
        pk=pk,
    )
    if not can_access_request(request.user, vacation_request):
        raise PermissionDenied
    if not hasattr(vacation_request, 'decision'):
        raise Http404('La solicitud todavía no tiene resolución.')
    pdf_file = build_decision_pdf(vacation_request.decision)
    vacation_request.decision.decision_pdf.save(pdf_file.name, pdf_file, save=True)
    pdf_file.seek(0)
    return _pdf_response(pdf_file, pdf_file.name)


@login_required
def request_decide(request, pk):
    if not can_decide_requests(request.user):
        raise PermissionDenied

    vacation_request = get_object_or_404(
        VacationRequest.objects.select_related('employee', 'employee__user'),
        pk=pk,
    )
    if hasattr(vacation_request, 'decision'):
        messages.info(request, 'Esta solicitud ya tiene una resolución.')
        return redirect(vacation_request)

    review = evaluate_request(vacation_request)
    form = VacationDecisionForm(request.POST or None, hr_review=review)
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

        notify_request_decision(vacation_request)

        if decision.decision == VacationDecision.Decision.APPROVED and review.has_blocking_flags:
            messages.warning(
                request,
                'Resolución aprobada con alertas críticas. La justificación debe quedar reflejada en observaciones.',
            )
        else:
            messages.success(request, 'Resolución registrada y PDF de empresa generado.')
        return redirect(vacation_request)
    return render(
        request,
        'vacations/form.html',
        {
            'form': form,
            'title': 'Resolver solicitud',
            'submit_label': 'Generar resolución PDF',
            'hr_review': review,
        },
    )


@login_required
def vacation_calendar(request):
    if not can_view_calendar(request.user):
        raise PermissionDenied

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
