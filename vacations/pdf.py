from io import BytesIO

from django.core.files.base import ContentFile
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

BRAND = colors.HexColor('#2563eb')
INK = colors.HexColor('#0f172a')
MUTED = colors.HexColor('#64748b')
SOFT = colors.HexColor('#eff6ff')
SUCCESS = colors.HexColor('#16a34a')
DANGER = colors.HexColor('#dc2626')


def _draw_header(pdf: canvas.Canvas, title: str, subtitle: str) -> None:
    width, height = A4
    pdf.setFillColor(BRAND)
    pdf.roundRect(15 * mm, height - 45 * mm, width - 30 * mm, 30 * mm, 8 * mm, fill=True, stroke=False)
    pdf.setFillColor(colors.white)
    pdf.setFont('Helvetica-Bold', 22)
    pdf.drawString(25 * mm, height - 27 * mm, title)
    pdf.setFont('Helvetica', 10)
    pdf.drawString(25 * mm, height - 36 * mm, subtitle)
    pdf.setFont('Helvetica-Bold', 13)
    pdf.drawRightString(width - 25 * mm, height - 29 * mm, 'VACACIONES')


def _label_value(pdf: canvas.Canvas, x: float, y: float, label: str, value: str) -> None:
    pdf.setFillColor(MUTED)
    pdf.setFont('Helvetica-Bold', 8)
    pdf.drawString(x, y, label.upper())
    pdf.setFillColor(INK)
    pdf.setFont('Helvetica', 11)
    pdf.drawString(x, y - 6 * mm, value or '—')


def _signature_box(pdf: canvas.Canvas, x: float, y: float, label: str) -> None:
    pdf.setStrokeColor(colors.HexColor('#cbd5e1'))
    pdf.setFillColor(colors.white)
    pdf.roundRect(x, y, 75 * mm, 28 * mm, 4 * mm, fill=True, stroke=True)
    pdf.setFillColor(MUTED)
    pdf.setFont('Helvetica', 9)
    pdf.drawCentredString(x + 37.5 * mm, y + 5 * mm, label)


def build_request_pdf(vacation_request) -> ContentFile:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    employee = vacation_request.employee

    _draw_header(pdf, 'Solicitud de vacaciones', 'Documento para firma del trabajador y registro interno')

    pdf.setFillColor(SOFT)
    pdf.roundRect(15 * mm, height - 82 * mm, width - 30 * mm, 26 * mm, 5 * mm, fill=True, stroke=False)
    _label_value(pdf, 25 * mm, height - 65 * mm, 'Trabajador', employee.full_name)
    _label_value(pdf, 105 * mm, height - 65 * mm, 'DNI/NIE', employee.national_id)
    _label_value(pdf, 25 * mm, height - 78 * mm, 'Departamento', employee.department)
    _label_value(pdf, 105 * mm, height - 78 * mm, 'Puesto', employee.position)

    y = height - 110 * mm
    pdf.setFillColor(INK)
    pdf.setFont('Helvetica-Bold', 16)
    pdf.drawString(20 * mm, y, 'Periodo solicitado')
    y -= 15 * mm
    _label_value(pdf, 25 * mm, y, 'Inicio', vacation_request.start_date.strftime('%d/%m/%Y'))
    _label_value(pdf, 80 * mm, y, 'Fin', vacation_request.end_date.strftime('%d/%m/%Y'))
    _label_value(pdf, 135 * mm, y, 'Días', f'{vacation_request.requested_days:g}')

    y -= 32 * mm
    pdf.setFillColor(INK)
    pdf.setFont('Helvetica-Bold', 12)
    pdf.drawString(20 * mm, y, 'Observaciones')
    pdf.setFillColor(MUTED)
    pdf.setFont('Helvetica', 10)
    text = pdf.beginText(20 * mm, y - 8 * mm)
    for line in (vacation_request.notes or 'Sin observaciones.').splitlines()[:7]:
        text.textLine(line[:105])
    pdf.drawText(text)

    _signature_box(pdf, 20 * mm, 35 * mm, 'Firma del trabajador')
    _signature_box(pdf, 115 * mm, 35 * mm, 'Recepción empresa')

    pdf.setFillColor(MUTED)
    pdf.setFont('Helvetica', 8)
    pdf.drawString(20 * mm, 18 * mm, f'Generado automáticamente el {timezone.localtime().strftime("%d/%m/%Y %H:%M")}.')
    pdf.showPage()
    pdf.save()

    filename = f'solicitud_vacaciones_{vacation_request.pk}.pdf'
    return ContentFile(buffer.getvalue(), name=filename)


def build_decision_pdf(decision) -> ContentFile:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    request = decision.request
    employee = request.employee
    approved = decision.decision == decision.Decision.APPROVED
    accent = SUCCESS if approved else DANGER

    _draw_header(pdf, 'Resolución de vacaciones', 'Documento oficial con la decisión de dirección')

    pdf.setFillColor(accent)
    pdf.roundRect(20 * mm, height - 80 * mm, width - 40 * mm, 22 * mm, 5 * mm, fill=True, stroke=False)
    pdf.setFillColor(colors.white)
    pdf.setFont('Helvetica-Bold', 20)
    pdf.drawCentredString(width / 2, height - 72 * mm, decision.get_decision_display().upper())

    y = height - 105 * mm
    _label_value(pdf, 25 * mm, y, 'Trabajador', employee.full_name)
    _label_value(pdf, 115 * mm, y, 'Departamento', employee.department)
    y -= 18 * mm
    _label_value(pdf, 25 * mm, y, 'Periodo', f'{request.start_date:%d/%m/%Y} - {request.end_date:%d/%m/%Y}')
    _label_value(pdf, 115 * mm, y, 'Días solicitados', f'{request.requested_days:g}')
    y -= 28 * mm

    pdf.setFillColor(INK)
    pdf.setFont('Helvetica-Bold', 12)
    pdf.drawString(20 * mm, y, 'Motivación / condiciones')
    pdf.setFillColor(MUTED)
    pdf.setFont('Helvetica', 10)
    text = pdf.beginText(20 * mm, y - 9 * mm)
    for line in (decision.company_notes or 'Dirección no añade observaciones adicionales.').splitlines()[:9]:
        text.textLine(line[:105])
    pdf.drawText(text)

    _signature_box(pdf, 20 * mm, 35 * mm, 'Firma dirección')
    _signature_box(pdf, 115 * mm, 35 * mm, 'Recibí trabajador')
    pdf.setFillColor(MUTED)
    pdf.setFont('Helvetica', 8)
    pdf.drawString(20 * mm, 18 * mm, f'Resuelto el {timezone.localtime(decision.decided_at).strftime("%d/%m/%Y %H:%M")}.')
    pdf.showPage()
    pdf.save()

    filename = f'resolucion_vacaciones_{request.pk}.pdf'
    return ContentFile(buffer.getvalue(), name=filename)
