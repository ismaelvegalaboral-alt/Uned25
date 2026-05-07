from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render

from .forms import EmployeeForm, VacationDecisionForm, VacationRequestForm
from .models import Employee, VacationDecision, VacationRequest
from .pdf import build_decision_pdf, build_request_pdf


@login_required
def dashboard(request):
    requests = VacationRequest.objects.select_related('employee')[:8]
    stats = {
        'employees': Employee.objects.count(),
        'pending': VacationRequest.objects.filter(status=VacationRequest.Status.PENDING).count(),
        'approved': VacationRequest.objects.filter(status=VacationRequest.Status.APPROVED).count(),
        'days': VacationRequest.objects.exclude(status=VacationRequest.Status.REJECTED).aggregate(total=Sum('requested_days'))['total'] or 0,
    }
    by_department = Employee.objects.values('department').annotate(total=Count('id')).order_by('-total')[:6]
    return render(request, 'vacations/dashboard.html', {'requests': requests, 'stats': stats, 'by_department': by_department})


@login_required
def employee_list(request):
    q = request.GET.get('q', '').strip()
    employees = Employee.objects.all()
    if q:
        employees = employees.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(department__icontains=q))
    return render(request, 'vacations/employee_list.html', {'employees': employees, 'q': q})


@login_required
def employee_create(request):
    form = EmployeeForm(request.POST or None)
    if form.is_valid():
        employee = form.save()
        messages.success(request, 'Ficha de trabajador creada.')
        return redirect(employee)
    return render(request, 'vacations/form.html', {'form': form, 'title': 'Nueva ficha de trabajador', 'submit_label': 'Guardar ficha'})


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
    return render(request, 'vacations/request_list.html', {'requests': requests, 'status': status, 'statuses': VacationRequest.Status.choices})


@login_required
def request_create(request):
    form = VacationRequestForm(request.POST or None)
    if form.is_valid():
        vacation_request = form.save(commit=False)
        vacation_request.created_by = request.user
        vacation_request.status = VacationRequest.Status.PENDING
        vacation_request.save()
        pdf_file = build_request_pdf(vacation_request)
        vacation_request.request_pdf.save(pdf_file.name, pdf_file, save=True)
        messages.success(request, 'Solicitud registrada y PDF generado para firma.')
        return redirect(vacation_request)
    return render(request, 'vacations/form.html', {'form': form, 'title': 'Nueva solicitud de vacaciones', 'submit_label': 'Generar solicitud PDF'})


@login_required
def request_detail(request, pk):
    vacation_request = get_object_or_404(VacationRequest.objects.select_related('employee', 'created_by'), pk=pk)
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
        vacation_request.status = VacationRequest.Status.APPROVED if decision.decision == VacationDecision.Decision.APPROVED else VacationRequest.Status.REJECTED
        vacation_request.save(update_fields=['status', 'updated_at'])
        pdf_file = build_decision_pdf(decision)
        decision.decision_pdf.save(pdf_file.name, pdf_file, save=True)
        messages.success(request, 'Resolución registrada y PDF de empresa generado.')
        return redirect(vacation_request)
    return render(request, 'vacations/form.html', {'form': form, 'title': 'Resolver solicitud', 'submit_label': 'Generar resolución PDF'})
