from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import FieldError
from django.core.mail import EmailMessage
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .daily_report_pdf import build_daily_work_report_pdf
from .forms import DailyWorkReportForm
from .models import DailyJobAssignment, DailyWorkReport, Employee

try:
    from .audit import log_action
except Exception:
    def log_action(*args, **kwargs):
        return None


REVIEWER_GROUPS = {'RRHH', 'Dirección', 'Administrador'}


def _is_reviewer(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    return user.groups.filter(name__in=REVIEWER_GROUPS).exists()


def _employee_for_user(user):
    employee = Employee.objects.filter(user=user).first()
    if employee:
        return employee

    email = (getattr(user, 'email', '') or '').strip()
    if email:
        try:
            return Employee.objects.filter(email__iexact=email).first()
        except FieldError:
            pass

    return None


def _can_access_report(user, report):
    if _is_reviewer(user):
        return True
    return getattr(report.employee, 'user_id', None) == user.id


def _daily_report_recipients():
    raw = getattr(settings, 'DAILY_REPORT_RECIPIENT_EMAILS', '')
    recipients = [item.strip() for item in raw.split(',') if item.strip()]

    hr_email = getattr(settings, 'HR_NOTIFICATION_EMAIL', '')
    if hr_email:
        recipients.append(hr_email)

    return list(dict.fromkeys(recipients))


def _notify_daily_report(request, report):
    recipients = _daily_report_recipients()
    if not recipients:
        return False

    detail_url = request.build_absolute_uri(reverse('daily_report_detail', args=[report.pk]))

    subject = f'Nuevo parte personal diario - {report.worker_name} - {report.report_date:%d/%m/%Y}'
    body = (
        f'Se ha registrado un nuevo parte personal diario.\\n\\n'
        f'Trabajador: {report.worker_name}\\n'
        f'Fecha: {report.report_date:%d/%m/%Y}\\n'
        f'Horas: {report.hours or "-"}\\n'
        f'Viajes: {report.trips or "-"}\\n\\n'
        f'Ver detalle: {detail_url}\\n'
    )

    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
        to=recipients,
    )

    if report.pdf:
        email.attach_file(report.pdf.path)

    email.send(fail_silently=False)
    return True


@login_required
def daily_report_list(request):
    qs = DailyWorkReport.objects.select_related('employee', 'created_by')

    if not _is_reviewer(request.user):
        employee = _employee_for_user(request.user)
        qs = qs.filter(employee=employee) if employee else qs.none()

    return render(request, 'vacations/daily_report_list.html', {'reports': qs})


def _daily_job_assignment_initial(request):
    assignment_id = request.GET.get('assignment')
    if not assignment_id:
        return {}

    try:
        assignment = DailyJobAssignment.objects.select_related('plan').get(pk=assignment_id)
    except Exception:
        return {}

    return {
        'report_date': assignment.plan.plan_date,
        'client_1': assignment.client,
        'worksite_1': assignment.worksite,
        'machine_number': assignment.machine,
        'truck_number': assignment.truck,
        'hours': assignment.hours,
        'trips': assignment.trips,
        'work_performed': assignment.notes,
    }

@login_required
def daily_report_create(request):
    employee = _employee_for_user(request.user)
    if employee is None and not _is_reviewer(request.user):
        messages.error(request, 'Tu usuario no tiene una ficha de trabajador asociada. Contacta con administración.')
        return redirect('dashboard')

    if employee is None:
        # Si un admin crea un parte y no tiene ficha, usamos la primera ficha solo para evitar bloqueo.
        # Lo normal será usar esta vista como trabajador.
        employee = Employee.objects.first()

    if employee is None:
        messages.error(request, 'No hay trabajadores dados de alta para crear el parte.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = DailyWorkReportForm(request.POST, employee=employee)
        if form.is_valid():
            report = form.save(commit=False)
            report.created_by = request.user
            report.save()

            filename, pdf_file = build_daily_work_report_pdf(report)
            report.pdf.save(filename, pdf_file, save=True)

            log_action(request.user, 'daily_report_created', report, request=request, metadata={'report_date': str(report.report_date)})

            try:
                sent = _notify_daily_report(request, report)
            except Exception as exc:
                sent = False
                messages.warning(request, f'Parte guardado, pero no se pudo enviar el email automático: {exc}')

            if sent:
                messages.success(request, 'Parte personal enviado correctamente a administración.')
            else:
                messages.success(request, 'Parte personal guardado correctamente.')

            return redirect('daily_report_detail', pk=report.pk)
    else:
        initial = {'worker_name': employee.full_name}
        initial.update(_daily_job_assignment_initial(request))
        form = DailyWorkReportForm(employee=employee, initial=initial)

    return render(request, 'vacations/daily_report_form.html', {'form': form, 'employee': employee})


@login_required
def daily_report_detail(request, pk):
    report = get_object_or_404(DailyWorkReport.objects.select_related('employee', 'created_by'), pk=pk)

    if not _can_access_report(request.user, report):
        raise Http404('Parte no encontrado.')

    return render(request, 'vacations/daily_report_detail.html', {'report': report})


@login_required
def daily_report_pdf(request, pk):
    report = get_object_or_404(DailyWorkReport.objects.select_related('employee'), pk=pk)

    if not _can_access_report(request.user, report):
        raise Http404('PDF no encontrado.')

    if not report.pdf:
        raise Http404('Este parte no tiene PDF generado.')

    return FileResponse(report.pdf.open('rb'), as_attachment=True, filename=report.pdf.name.split('/')[-1])
