import csv
from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import FieldError
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import DailyJobAssignmentForm, DailyJobPlanForm, DailyJobStatusEntryForm
from .models import DailyJobAssignment, DailyJobPlan, DailyJobStatusEntry, Employee
from .daily_job_excel_export import build_daily_job_plan_excel_response

try:
    from .audit import log_action
except Exception:
    def log_action(*args, **kwargs):
        return None


MANAGER_GROUPS = {'RRHH', 'Dirección', 'Administrador'}


def _can_manage(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    return user.groups.filter(name__in=MANAGER_GROUPS).exists()


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


def _manager_required(user):
    if not _can_manage(user):
        raise Http404('Faena no encontrada.')


def _group_assignments(assignments):
    groups = {}

    for item in assignments:
        key = (
            item.client or 'Sin cliente',
            item.worksite or 'Sin obra/zona',
        )
        groups.setdefault(key, []).append(item)

    return [
        {
            'client': key[0],
            'worksite': key[1],
            'items': value,
        }
        for key, value in groups.items()
    ]


@login_required
def daily_job_plan_list(request):
    if not _can_manage(request.user):
        return redirect('daily_job_my_assignments')

    plans = DailyJobPlan.objects.select_related('created_by').prefetch_related('assignments', 'status_entries')

    q = (request.GET.get('q') or '').strip()
    if q:
        plans = plans.filter(
            Q(title__icontains=q)
            | Q(notes__icontains=q)
            | Q(assignments__client__icontains=q)
            | Q(assignments__worksite__icontains=q)
            | Q(assignments__machine__icontains=q)
            | Q(assignments__truck__icontains=q)
            | Q(assignments__worker_name__icontains=q)
        ).distinct()

    return render(request, 'vacations/daily_job_plan_list.html', {'plans': plans, 'can_manage': True, 'q': q})


@login_required
def daily_job_panel(request):
    _manager_required(request.user)

    selected_date = request.GET.get('date') or ''
    plan = None

    if selected_date:
        plan = DailyJobPlan.objects.filter(plan_date=selected_date).first()

    if plan is None:
        plan = DailyJobPlan.objects.order_by('-plan_date').first()

    assignments = []
    status_entries = []
    groups = []

    if plan:
        assignments = list(plan.assignments.select_related('employee').all())
        status_entries = list(plan.status_entries.all())
        groups = _group_assignments(assignments)

    status_groups = []
    if plan:
        for value, label in DailyJobStatusEntry.STATUS_CHOICES:
            entries = [entry for entry in status_entries if entry.status_type == value]
            if entries:
                status_groups.append((label, entries))

    return render(
        request,
        'vacations/daily_job_panel.html',
        {
            'plan': plan,
            'groups': groups,
            'status_groups': status_groups,
            'selected_date': selected_date,
        },
    )


@login_required
def daily_job_plan_create(request):
    _manager_required(request.user)

    if request.method == 'POST':
        form = DailyJobPlanForm(request.POST)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.created_by = request.user
            plan.save()
            log_action(request.user, 'daily_job_plan_created', plan, request=request, metadata={'plan_date': str(plan.plan_date)})
            messages.success(request, 'Faena diaria creada correctamente.')
            return redirect('daily_job_plan_detail', pk=plan.pk)
    else:
        form = DailyJobPlanForm()

    return render(request, 'vacations/daily_job_plan_form.html', {'form': form})


@login_required
def daily_job_plan_copy(request, pk):
    _manager_required(request.user)

    source = get_object_or_404(DailyJobPlan.objects.prefetch_related('assignments', 'status_entries'), pk=pk)

    if request.method == 'POST':
        new_date = request.POST.get('plan_date')

        if not new_date:
            messages.error(request, 'Debes indicar la nueva fecha.')
            return redirect('daily_job_plan_copy', pk=source.pk)

        if DailyJobPlan.objects.filter(plan_date=new_date).exists():
            messages.error(request, 'Ya existe una faena para esa fecha.')
            return redirect('daily_job_plan_copy', pk=source.pk)

        new_plan = DailyJobPlan.objects.create(
            plan_date=new_date,
            title=request.POST.get('title') or f'Copia de {source}',
            notes=source.notes,
            is_published=False,
            created_by=request.user,
        )

        for item in source.assignments.all():
            DailyJobAssignment.objects.create(
                plan=new_plan,
                category=item.category,
                client=item.client,
                worksite=item.worksite,
                machine=item.machine,
                truck=item.truck,
                employee=item.employee,
                worker_name=item.worker_name,
                hours=item.hours,
                trips=item.trips,
                notes=item.notes,
                sort_order=item.sort_order,
            )

        for entry in source.status_entries.all():
            DailyJobStatusEntry.objects.create(
                plan=new_plan,
                status_type=entry.status_type,
                text=entry.text,
                sort_order=entry.sort_order,
            )

        log_action(request.user, 'daily_job_plan_copied', new_plan, request=request, metadata={'source_plan_id': source.pk})
        messages.success(request, 'Faena copiada correctamente.')
        return redirect('daily_job_plan_detail', pk=new_plan.pk)

    return render(request, 'vacations/daily_job_plan_copy.html', {'source': source})


@login_required
def daily_job_plan_detail(request, pk):
    plan = get_object_or_404(DailyJobPlan.objects.prefetch_related('assignments__employee', 'status_entries'), pk=pk)

    if not _can_manage(request.user):
        if not plan.is_published:
            raise Http404('Faena no encontrada.')

        employee = _employee_for_user(request.user)
        has_assignment = bool(employee and plan.assignments.filter(employee=employee).exists())
        name = employee.full_name if employee else ''

        if not has_assignment and name and plan.assignments.filter(worker_name__iexact=name).exists():
            has_assignment = True

        if not has_assignment:
            raise Http404('Faena no encontrada.')

    assignments = plan.assignments.select_related('employee').all()
    status_entries = list(plan.status_entries.all())
    grouped_assignments = _group_assignments(assignments)

    status_groups = []
    for value, label in DailyJobStatusEntry.STATUS_CHOICES:
        entries = [entry for entry in status_entries if entry.status_type == value]
        if entries:
            status_groups.append((label, entries))

    return render(
        request,
        'vacations/daily_job_plan_detail.html',
        {
            'plan': plan,
            'assignments': assignments,
            'grouped_assignments': grouped_assignments,
            'status_groups': status_groups,
            'can_manage': _can_manage(request.user),
        },
    )


@login_required
def daily_job_plan_publish(request, pk):
    _manager_required(request.user)

    plan = get_object_or_404(DailyJobPlan, pk=pk)
    plan.is_published = True
    plan.save(update_fields=['is_published', 'updated_at'])
    log_action(request.user, 'daily_job_plan_published', plan, request=request, metadata={'plan_date': str(plan.plan_date)})
    messages.success(request, 'Faena publicada para los trabajadores.')
    return redirect('daily_job_plan_detail', pk=plan.pk)


@login_required
def daily_job_plan_unpublish(request, pk):
    _manager_required(request.user)

    plan = get_object_or_404(DailyJobPlan, pk=pk)
    plan.is_published = False
    plan.save(update_fields=['is_published', 'updated_at'])
    log_action(request.user, 'daily_job_plan_unpublished', plan, request=request, metadata={'plan_date': str(plan.plan_date)})
    messages.success(request, 'Faena ocultada para trabajadores.')
    return redirect('daily_job_plan_detail', pk=plan.pk)


@login_required
def daily_job_plan_csv(request, pk):
    _manager_required(request.user)

    plan = get_object_or_404(DailyJobPlan.objects.prefetch_related('assignments'), pk=pk)

    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="faena_{plan.plan_date:%Y%m%d}.csv"'

    response.write('\ufeff')
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Fecha', 'Tipo', 'Cliente', 'Obra/Zona', 'Máquina', 'Camión', 'Trabajador', 'Horas', 'Viajes', 'Observaciones'])

    for item in plan.assignments.select_related('employee').all():
        writer.writerow([
            plan.plan_date.strftime('%d/%m/%Y'),
            item.get_category_display(),
            item.client,
            item.worksite,
            item.machine,
            item.truck,
            item.worker_name or (item.employee.full_name if item.employee else ''),
            item.hours,
            item.trips,
            item.notes,
        ])

    return response


@login_required
def daily_job_assignment_create(request, plan_pk):
    _manager_required(request.user)

    plan = get_object_or_404(DailyJobPlan, pk=plan_pk)

    if request.method == 'POST':
        form = DailyJobAssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.plan = plan
            assignment.save()
            log_action(request.user, 'daily_job_assignment_created', assignment, request=request, metadata={'plan_id': plan.pk})
            messages.success(request, 'Línea de faena añadida.')
            return redirect('daily_job_plan_detail', pk=plan.pk)
    else:
        form = DailyJobAssignmentForm(initial={'sort_order': plan.assignments.count() + 1})

    return render(request, 'vacations/daily_job_assignment_form.html', {'form': form, 'plan': plan, 'mode': 'create'})


@login_required
def daily_job_assignment_edit(request, pk):
    _manager_required(request.user)

    assignment = get_object_or_404(DailyJobAssignment.objects.select_related('plan'), pk=pk)
    plan = assignment.plan

    if request.method == 'POST':
        form = DailyJobAssignmentForm(request.POST, instance=assignment)
        if form.is_valid():
            assignment = form.save()
            log_action(request.user, 'daily_job_assignment_updated', assignment, request=request, metadata={'plan_id': plan.pk})
            messages.success(request, 'Línea de faena actualizada.')
            return redirect('daily_job_plan_detail', pk=plan.pk)
    else:
        form = DailyJobAssignmentForm(instance=assignment)

    return render(request, 'vacations/daily_job_assignment_form.html', {'form': form, 'plan': plan, 'assignment': assignment, 'mode': 'edit'})


@login_required
def daily_job_assignment_delete(request, pk):
    _manager_required(request.user)

    assignment = get_object_or_404(DailyJobAssignment.objects.select_related('plan'), pk=pk)
    plan = assignment.plan

    if request.method == 'POST':
        assignment.delete()
        log_action(request.user, 'daily_job_assignment_deleted', plan, request=request, metadata={'plan_id': plan.pk})
        messages.success(request, 'Línea de faena eliminada.')
        return redirect('daily_job_plan_detail', pk=plan.pk)

    return render(request, 'vacations/daily_job_confirm_delete.html', {'object': assignment, 'cancel_url': 'daily_job_plan_detail', 'plan': plan})


@login_required
def daily_job_status_create(request, plan_pk):
    _manager_required(request.user)

    plan = get_object_or_404(DailyJobPlan, pk=plan_pk)

    if request.method == 'POST':
        form = DailyJobStatusEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.plan = plan
            entry.save()
            log_action(request.user, 'daily_job_status_created', entry, request=request, metadata={'plan_id': plan.pk})
            messages.success(request, 'Estado añadido a la faena.')
            return redirect('daily_job_plan_detail', pk=plan.pk)
    else:
        form = DailyJobStatusEntryForm()

    return render(request, 'vacations/daily_job_status_form.html', {'form': form, 'plan': plan, 'mode': 'create'})


@login_required
def daily_job_status_edit(request, pk):
    _manager_required(request.user)

    entry = get_object_or_404(DailyJobStatusEntry.objects.select_related('plan'), pk=pk)
    plan = entry.plan

    if request.method == 'POST':
        form = DailyJobStatusEntryForm(request.POST, instance=entry)
        if form.is_valid():
            entry = form.save()
            log_action(request.user, 'daily_job_status_updated', entry, request=request, metadata={'plan_id': plan.pk})
            messages.success(request, 'Estado actualizado.')
            return redirect('daily_job_plan_detail', pk=plan.pk)
    else:
        form = DailyJobStatusEntryForm(instance=entry)

    return render(request, 'vacations/daily_job_status_form.html', {'form': form, 'plan': plan, 'entry': entry, 'mode': 'edit'})


@login_required
def daily_job_status_delete(request, pk):
    _manager_required(request.user)

    entry = get_object_or_404(DailyJobStatusEntry.objects.select_related('plan'), pk=pk)
    plan = entry.plan

    if request.method == 'POST':
        entry.delete()
        log_action(request.user, 'daily_job_status_deleted', plan, request=request, metadata={'plan_id': plan.pk})
        messages.success(request, 'Estado eliminado.')
        return redirect('daily_job_plan_detail', pk=plan.pk)

    return render(request, 'vacations/daily_job_confirm_delete.html', {'object': entry, 'cancel_url': 'daily_job_plan_detail', 'plan': plan})


@login_required
def daily_job_my_assignments(request):
    employee = _employee_for_user(request.user)

    assignments = DailyJobAssignment.objects.none()
    if employee:
        assignments = DailyJobAssignment.objects.select_related('plan', 'employee').filter(plan__is_published=True, employee=employee)

        name = employee.full_name
        if name:
            by_name = DailyJobAssignment.objects.select_related('plan', 'employee').filter(plan__is_published=True, worker_name__iexact=name)
            assignments = (assignments | by_name).distinct()

        assignments = assignments.order_by('-plan__plan_date', 'sort_order')

    return render(request, 'vacations/daily_job_my_assignments.html', {'employee': employee, 'assignments': assignments})

@login_required
def daily_job_plan_excel(request, pk):
    _manager_required(request.user)

    plan = get_object_or_404(
        DailyJobPlan.objects.prefetch_related('assignments__employee', 'status_entries'),
        pk=pk,
    )

    return build_daily_job_plan_excel_response(plan)
