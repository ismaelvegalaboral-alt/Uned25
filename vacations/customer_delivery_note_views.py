import base64
import binascii

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import FieldError
from django.core.files.base import ContentFile
from django.core.mail import EmailMessage
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .customer_delivery_note_pdf import build_customer_delivery_note_pdf
from .forms import CustomerDeliveryNoteForm
from .models import CustomerDeliveryNote, Employee

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


def _can_access(user, note):
    if _is_reviewer(user):
        return True
    return getattr(note.employee, 'user_id', None) == user.id


def _recipients():
    raw = getattr(settings, 'CUSTOMER_DELIVERY_NOTE_RECIPIENT_EMAILS', '')
    recipients = [item.strip() for item in raw.split(',') if item.strip()]

    hr_email = getattr(settings, 'HR_NOTIFICATION_EMAIL', '')
    if hr_email:
        recipients.append(hr_email)

    return list(dict.fromkeys(recipients))


def _save_signature(note, signature_data):
    header = 'data:image/png;base64,'
    if not signature_data.startswith(header):
        return

    raw = signature_data[len(header):]
    try:
        decoded = base64.b64decode(raw)
    except (binascii.Error, ValueError):
        return

    filename = f'firma_albaran_cliente_{note.pk}.png'
    note.signature_image.save(filename, ContentFile(decoded), save=True)


def _notify(request, note):
    recipients = _recipients()
    if not recipients:
        return False

    detail_url = request.build_absolute_uri(reverse('customer_delivery_note_detail', args=[note.pk]))

    subject = f'Nuevo albarán de cliente - {note.customer_name} - {note.note_date:%d/%m/%Y}'
    body = (
        f'Se ha registrado un nuevo albarán de cliente.\\n\\n'
        f'Cliente: {note.customer_name}\\n'
        f'Obra: {note.worksite or "-"}\\n'
        f'Fecha: {note.note_date:%d/%m/%Y}\\n'
        f'Recibí conforme: {note.received_by or "-"}\\n\\n'
        f'Ver detalle: {detail_url}\\n'
    )

    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
        to=recipients,
    )

    if note.pdf:
        email.attach_file(note.pdf.path)

    email.send(fail_silently=False)
    return True


@login_required
def customer_delivery_note_list(request):
    qs = CustomerDeliveryNote.objects.select_related('employee', 'created_by')

    if not _is_reviewer(request.user):
        employee = _employee_for_user(request.user)
        qs = qs.filter(employee=employee) if employee else qs.none()

    return render(request, 'vacations/customer_delivery_note_list.html', {'notes': qs})


@login_required
def customer_delivery_note_create(request):
    employee = _employee_for_user(request.user)
    if employee is None and not _is_reviewer(request.user):
        messages.error(request, 'Tu usuario no tiene una ficha de trabajador asociada. Contacta con administración.')
        return redirect('dashboard')

    if employee is None:
        employee = Employee.objects.first()

    if employee is None:
        messages.error(request, 'No hay trabajadores dados de alta para crear el albarán.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = CustomerDeliveryNoteForm(request.POST, employee=employee)
        if form.is_valid():
            note = form.save(commit=False)
            note.created_by = request.user
            note.save()

            _save_signature(note, form.cleaned_data['signature_data'])

            filename, pdf_file = build_customer_delivery_note_pdf(note)
            note.pdf.save(filename, pdf_file, save=True)

            log_action(request.user, 'customer_delivery_note_created', note, request=request, metadata={'customer': note.customer_name})

            try:
                sent = _notify(request, note)
            except Exception as exc:
                sent = False
                messages.warning(request, f'Albarán guardado, pero no se pudo enviar el email automático: {exc}')

            if sent:
                messages.success(request, 'Albarán de cliente generado y enviado correctamente.')
            else:
                messages.success(request, 'Albarán de cliente generado correctamente.')

            return redirect('customer_delivery_note_detail', pk=note.pk)
    else:
        form = CustomerDeliveryNoteForm(employee=employee)

    return render(request, 'vacations/customer_delivery_note_form.html', {'form': form})


@login_required
def customer_delivery_note_detail(request, pk):
    note = get_object_or_404(CustomerDeliveryNote.objects.select_related('employee', 'created_by'), pk=pk)

    if not _can_access(request.user, note):
        raise Http404('Albarán no encontrado.')

    return render(request, 'vacations/customer_delivery_note_detail.html', {'note': note})


@login_required
def customer_delivery_note_pdf(request, pk):
    note = get_object_or_404(CustomerDeliveryNote.objects.select_related('employee'), pk=pk)

    if not _can_access(request.user, note):
        raise Http404('PDF no encontrado.')

    if not note.pdf:
        raise Http404('Este albarán no tiene PDF generado.')

    return FileResponse(note.pdf.open('rb'), as_attachment=True, filename=note.pdf.name.split('/')[-1])
