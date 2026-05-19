from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import FieldError
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .feature_access import can_use_feature, is_feature_manager
from .forms import WorkOrderForm, WorkOrderHourEntryForm, WorkOrderReceiptForm
from .models import Employee, WorkOrder

try:
    from .audit import log_action
except Exception:
    def log_action(*args, **kwargs):
        return None


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


def _employee_name(employee, user):
    if employee:
        full_name = getattr(employee, 'full_name', '')
        if callable(full_name):
            full_name = full_name()
        if full_name:
            return str(full_name).strip()

    if user.get_full_name():
        return user.get_full_name()

    return user.get_username()


def _require_work_orders(user):
    if not can_use_feature(user, 'work_orders'):
        raise Http404('Orden de trabajo no encontrada.')


def _can_access(user, order):
    if is_feature_manager(user):
        return True

    employee = _employee_for_user(user)

    if employee and order.employee_id == employee.id:
        return True

    return order.created_by_id == user.id


@login_required
def work_order_list(request):
    _require_work_orders(request.user)

    qs = WorkOrder.objects.select_related('employee', 'created_by').prefetch_related('hour_entries', 'receipts')

    if not is_feature_manager(request.user):
        employee = _employee_for_user(request.user)
        if employee:
            qs = qs.filter(employee=employee)
        else:
            qs = qs.filter(created_by=request.user)

    status = (request.GET.get('status') or '').strip()
    if status:
        qs = qs.filter(status=status)

    q = (request.GET.get('q') or '').strip()
    if q:
        qs = qs.filter(
            Q(vehicle_machine__icontains=q)
            | Q(worker_name__icontains=q)
            | Q(task_description__icontains=q)
        )

    return render(
        request,
        'vacations/work_order_list.html',
        {
            'orders': qs.distinct(),
            'is_reviewer': is_feature_manager(request.user),
            'q': q,
            'status': status,
        },
    )


@login_required
def work_order_create(request):
    _require_work_orders(request.user)

    employee = _employee_for_user(request.user)
    worker_name = _employee_name(employee, request.user)

    if request.method == 'POST':
        form = WorkOrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.employee = employee
            order.worker_name = worker_name
            order.created_by = request.user
            order.save()

            log_action(request.user, 'work_order_created', order, request=request, metadata={'vehicle_machine': order.vehicle_machine})

            messages.success(request, 'Orden de trabajo creada correctamente. Ahora puedes añadir horas y albaranes/tickets.')
            return redirect('work_order_detail', pk=order.pk)
    else:
        form = WorkOrderForm()

    return render(request, 'vacations/work_order_form.html', {'form': form, 'worker_name': worker_name})


@login_required
def work_order_detail(request, pk):
    _require_work_orders(request.user)

    order = get_object_or_404(
        WorkOrder.objects.select_related('employee', 'created_by').prefetch_related('hour_entries', 'receipts'),
        pk=pk,
    )

    if not _can_access(request.user, order):
        raise Http404('Orden de trabajo no encontrada.')

    return render(
        request,
        'vacations/work_order_detail.html',
        {
            'order': order,
            'hour_entries': order.hour_entries.all(),
            'receipts': order.receipts.all(),
            'is_reviewer': is_feature_manager(request.user),
        },
    )


@login_required
def work_order_add_hours(request, pk):
    _require_work_orders(request.user)

    order = get_object_or_404(WorkOrder, pk=pk)

    if not _can_access(request.user, order):
        raise Http404('Orden de trabajo no encontrada.')

    if request.method == 'POST':
        form = WorkOrderHourEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.work_order = order
            entry.created_by = request.user
            entry.save()

            log_action(request.user, 'work_order_hours_added', order, request=request, metadata={'hours': str(entry.hours)})

            messages.success(request, 'Horas añadidas a la orden.')
            return redirect('work_order_detail', pk=order.pk)
    else:
        form = WorkOrderHourEntryForm(initial={'work_date': timezone.localdate()})

    return render(request, 'vacations/work_order_hours_form.html', {'form': form, 'order': order})


@login_required
def work_order_add_receipt(request, pk):
    _require_work_orders(request.user)

    order = get_object_or_404(WorkOrder, pk=pk)

    if not _can_access(request.user, order):
        raise Http404('Orden de trabajo no encontrada.')

    if request.method == 'POST':
        form = WorkOrderReceiptForm(request.POST, request.FILES)
        if form.is_valid():
            receipt = form.save(commit=False)
            receipt.work_order = order
            receipt.uploaded_by = request.user
            receipt.save()

            log_action(request.user, 'work_order_receipt_uploaded', order, request=request, metadata={'receipt_id': receipt.pk})

            messages.success(request, 'Albarán/ticket subido correctamente.')
            return redirect('work_order_detail', pk=order.pk)
    else:
        form = WorkOrderReceiptForm(initial={'receipt_date': timezone.localdate()})

    return render(request, 'vacations/work_order_receipt_form.html', {'form': form, 'order': order})


@login_required
def work_order_close(request, pk):
    _require_work_orders(request.user)

    order = get_object_or_404(WorkOrder, pk=pk)

    if not _can_access(request.user, order):
        raise Http404('Orden de trabajo no encontrada.')

    order.status = WorkOrder.STATUS_CLOSED
    order.closed_at = timezone.now()
    order.save(update_fields=['status', 'closed_at', 'updated_at'])

    log_action(request.user, 'work_order_closed', order, request=request, metadata={'order_id': order.pk})

    messages.success(request, 'Orden de trabajo cerrada.')
    return redirect('work_order_detail', pk=order.pk)
