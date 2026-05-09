import logging

from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse

logger = logging.getLogger(__name__)


def _absolute_url(path: str) -> str:
    site_url = getattr(settings, 'SITE_URL', '').rstrip('/')
    return f'{site_url}{path}' if site_url else path


def _format_date(value) -> str:
    return value.strftime('%d/%m/%Y') if value else '—'


def send_new_request_notification(vacation_request) -> bool:
    recipient = getattr(settings, 'HR_NOTIFICATION_EMAIL', '')
    if not recipient:
        logger.info('HR_NOTIFICATION_EMAIL no configurado; no se envía aviso.')
        return False

    employee = vacation_request.employee
    detail_url = _absolute_url(reverse('request_detail', args=[vacation_request.pk]))

    subject = f'Nueva solicitud pendiente · {employee.full_name}'
    plain_message = (
        'Se ha registrado una nueva solicitud en Kalpae Gestión de Ausencias.\n\n'
        f'Trabajador: {employee.full_name}\n'
        f'Departamento: {employee.department or "—"}\n'
        f'Puesto: {employee.position or "—"}\n'
        f'Periodo: {_format_date(vacation_request.start_date)} - {_format_date(vacation_request.end_date)}\n'
        f'Días solicitados: {vacation_request.requested_days:g}\n'
        f'Estado: {vacation_request.get_status_display()}\n\n'
        f'Observaciones:\n{vacation_request.notes or "Sin observaciones."}\n\n'
        f'Revisar solicitud:\n{detail_url}\n'
    )

    html_message = f"""
    <div style="font-family:Arial,sans-serif;max-width:680px;margin:auto;border:1px solid #e2e8f0;border-radius:18px;overflow:hidden">
      <div style="background:#1d2a57;color:white;padding:24px 28px">
        <h1 style="margin:0;font-size:22px">Nueva solicitud pendiente</h1>
        <p style="margin:8px 0 0;color:#cbd5e1">Kalpae Gestión de Ausencias</p>
      </div>
      <div style="padding:24px 28px;color:#0f172a">
        <p>Se ha registrado una nueva solicitud y queda pendiente de revisión.</p>
        <table style="width:100%;border-collapse:collapse;margin:18px 0">
          <tr><td style="padding:10px;border-bottom:1px solid #e2e8f0;color:#64748b">Trabajador</td><td style="padding:10px;border-bottom:1px solid #e2e8f0"><strong>{employee.full_name}</strong></td></tr>
          <tr><td style="padding:10px;border-bottom:1px solid #e2e8f0;color:#64748b">Departamento</td><td style="padding:10px;border-bottom:1px solid #e2e8f0">{employee.department or "—"}</td></tr>
          <tr><td style="padding:10px;border-bottom:1px solid #e2e8f0;color:#64748b">Periodo</td><td style="padding:10px;border-bottom:1px solid #e2e8f0">{_format_date(vacation_request.start_date)} - {_format_date(vacation_request.end_date)}</td></tr>
          <tr><td style="padding:10px;border-bottom:1px solid #e2e8f0;color:#64748b">Días</td><td style="padding:10px;border-bottom:1px solid #e2e8f0">{vacation_request.requested_days:g}</td></tr>
          <tr><td style="padding:10px;border-bottom:1px solid #e2e8f0;color:#64748b">Estado</td><td style="padding:10px;border-bottom:1px solid #e2e8f0">{vacation_request.get_status_display()}</td></tr>
        </table>
        <p style="color:#64748b"><strong>Observaciones:</strong><br>{vacation_request.notes or "Sin observaciones."}</p>
        <p style="margin-top:24px">
          <a href="{detail_url}" style="display:inline-block;background:#1d2a57;color:white;text-decoration:none;padding:12px 18px;border-radius:12px;font-weight:bold">
            Revisar solicitud
          </a>
        </p>
      </div>
    </div>
    """

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception:
        logger.exception('No se pudo enviar el aviso de nueva solicitud.')
        return False
