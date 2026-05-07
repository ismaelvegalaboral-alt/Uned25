from io import BytesIO
from textwrap import wrap

from django.core.files.base import ContentFile
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

PAGE_W, PAGE_H = A4
BRAND = colors.HexColor('#1d4ed8')
BRAND_DARK = colors.HexColor('#0f172a')
BRAND_LIGHT = colors.HexColor('#dbeafe')
ACCENT = colors.HexColor('#7c3aed')
INK = colors.HexColor('#0f172a')
MUTED = colors.HexColor('#64748b')
LINE = colors.HexColor('#dbe3ef')
PAPER = colors.HexColor('#f8fafc')
SUCCESS = colors.HexColor('#16a34a')
SUCCESS_SOFT = colors.HexColor('#dcfce7')
DANGER = colors.HexColor('#dc2626')
DANGER_SOFT = colors.HexColor('#fee2e2')
WARNING = colors.HexColor('#f59e0b')
WARNING_SOFT = colors.HexColor('#fef3c7')

LEFT = 18 * mm
RIGHT = PAGE_W - 18 * mm
CONTENT_W = RIGHT - LEFT


def _set_doc_info(pdf: canvas.Canvas, title: str) -> None:
    pdf.setTitle(title)
    pdf.setAuthor('Vacaciones Pro')
    pdf.setSubject('Gestión documental de vacaciones')
    pdf.setCreator('Vacaciones Pro · Django + ReportLab')


def _text(pdf: canvas.Canvas, x: float, y: float, value: str, size: int = 10, color=INK, font: str = 'Helvetica') -> None:
    pdf.setFillColor(color)
    pdf.setFont(font, size)
    pdf.drawString(x, y, value)


def _right_text(pdf: canvas.Canvas, x: float, y: float, value: str, size: int = 10, color=INK, font: str = 'Helvetica') -> None:
    pdf.setFillColor(color)
    pdf.setFont(font, size)
    pdf.drawRightString(x, y, value)


def _wrapped_text(pdf: canvas.Canvas, x: float, y: float, value: str, max_chars: int, line_height: float, max_lines: int, size: int = 10, color=MUTED) -> float:
    pdf.setFillColor(color)
    pdf.setFont('Helvetica', size)
    lines = []
    for raw_line in (value or '').splitlines() or ['']:
        lines.extend(wrap(raw_line, max_chars) or [''])
    for line in lines[:max_lines]:
        pdf.drawString(x, y, line)
        y -= line_height
    return y


def _pill(pdf: canvas.Canvas, x: float, y: float, text: str, fill, stroke=None, color=INK, width: float = 42 * mm) -> None:
    pdf.setFillColor(fill)
    pdf.setStrokeColor(stroke or fill)
    pdf.roundRect(x, y, width, 9 * mm, 4.5 * mm, fill=True, stroke=True)
    pdf.setFillColor(color)
    pdf.setFont('Helvetica-Bold', 8)
    pdf.drawCentredString(x + width / 2, y + 3 * mm, text.upper())


def _background(pdf: canvas.Canvas, accent=BRAND) -> None:
    pdf.setFillColor(PAPER)
    pdf.rect(0, 0, PAGE_W, PAGE_H, fill=True, stroke=False)
    pdf.setFillColor(BRAND_DARK)
    pdf.rect(0, PAGE_H - 56 * mm, PAGE_W, 56 * mm, fill=True, stroke=False)
    pdf.setFillColor(accent)
    pdf.circle(PAGE_W - 22 * mm, PAGE_H - 11 * mm, 42 * mm, fill=True, stroke=False)
    pdf.setFillColor(colors.HexColor('#243047'))
    pdf.circle(PAGE_W - 55 * mm, PAGE_H - 45 * mm, 30 * mm, fill=True, stroke=False)
    pdf.setFillColor(colors.white)
    pdf.roundRect(LEFT, 18 * mm, CONTENT_W, PAGE_H - 54 * mm, 8 * mm, fill=True, stroke=False)


def _header(pdf: canvas.Canvas, title: str, subtitle: str, reference: str, accent=BRAND) -> None:
    _background(pdf, accent)
    _text(pdf, LEFT, PAGE_H - 24 * mm, 'VACACIONES PRO', 9, BRAND_LIGHT, 'Helvetica-Bold')
    _text(pdf, LEFT, PAGE_H - 36 * mm, title, 24, colors.white, 'Helvetica-Bold')
    _text(pdf, LEFT, PAGE_H - 44 * mm, subtitle, 9, colors.HexColor('#cbd5e1'))
    _right_text(pdf, RIGHT, PAGE_H - 25 * mm, reference, 10, colors.white, 'Helvetica-Bold')
    _right_text(pdf, RIGHT, PAGE_H - 33 * mm, timezone.localtime().strftime('%d/%m/%Y · %H:%M'), 8, colors.HexColor('#cbd5e1'))


def _section_title(pdf: canvas.Canvas, y: float, title: str, accent=BRAND) -> float:
    pdf.setFillColor(accent)
    pdf.roundRect(LEFT + 8 * mm, y - 1 * mm, 3 * mm, 8 * mm, 1.5 * mm, fill=True, stroke=False)
    _text(pdf, LEFT + 15 * mm, y, title, 12, INK, 'Helvetica-Bold')
    return y - 11 * mm


def _card(pdf: canvas.Canvas, x: float, y: float, w: float, h: float, fill=colors.white, stroke=LINE) -> None:
    pdf.setFillColor(fill)
    pdf.setStrokeColor(stroke)
    pdf.roundRect(x, y, w, h, 5 * mm, fill=True, stroke=True)


def _metric_card(pdf: canvas.Canvas, x: float, y: float, w: float, label: str, value: str, accent=BRAND) -> None:
    _card(pdf, x, y, w, 24 * mm, colors.HexColor('#f8fbff'), colors.HexColor('#dbeafe'))
    _text(pdf, x + 6 * mm, y + 15 * mm, label.upper(), 7, MUTED, 'Helvetica-Bold')
    _text(pdf, x + 6 * mm, y + 6 * mm, value, 16, accent, 'Helvetica-Bold')


def _field(pdf: canvas.Canvas, x: float, y: float, label: str, value: str, w: float = 70 * mm) -> None:
    pdf.setStrokeColor(colors.HexColor('#edf2f7'))
    pdf.line(x, y - 2 * mm, x + w, y - 2 * mm)
    _text(pdf, x, y + 5 * mm, label.upper(), 7, MUTED, 'Helvetica-Bold')
    _text(pdf, x, y - 1 * mm, value or '—', 10, INK)


def _signature_box(pdf: canvas.Canvas, x: float, y: float, w: float, label: str, caption: str) -> None:
    _card(pdf, x, y, w, 31 * mm)
    pdf.setStrokeColor(colors.HexColor('#94a3b8'))
    pdf.setDash(1, 3)
    pdf.line(x + 8 * mm, y + 17 * mm, x + w - 8 * mm, y + 17 * mm)
    pdf.setDash()
    _text(pdf, x + 8 * mm, y + 8 * mm, label, 9, INK, 'Helvetica-Bold')
    _text(pdf, x + 8 * mm, y + 4 * mm, caption, 7, MUTED)


def _footer(pdf: canvas.Canvas, reference: str) -> None:
    pdf.setFillColor(colors.HexColor('#f1f5f9'))
    pdf.roundRect(LEFT, 8 * mm, CONTENT_W, 7 * mm, 3 * mm, fill=True, stroke=False)
    _text(pdf, LEFT + 4 * mm, 10.5 * mm, 'Documento generado automáticamente y archivado en la plataforma.', 7, MUTED)
    _right_text(pdf, RIGHT - 4 * mm, 10.5 * mm, reference, 7, MUTED, 'Helvetica-Bold')


def _approval_strip(pdf: canvas.Canvas, y: float, label: str, fill, color) -> float:
    pdf.setFillColor(fill)
    pdf.setStrokeColor(fill)
    pdf.roundRect(LEFT + 8 * mm, y, CONTENT_W - 16 * mm, 18 * mm, 5 * mm, fill=True, stroke=True)
    pdf.setFillColor(color)
    pdf.setFont('Helvetica-Bold', 18)
    pdf.drawCentredString(PAGE_W / 2, y + 6 * mm, label.upper())
    return y - 14 * mm


def build_request_pdf(vacation_request) -> ContentFile:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    employee = vacation_request.employee
    reference = f'SOL-{vacation_request.pk:05d}'
    _set_doc_info(pdf, f'Solicitud de vacaciones {reference}')
    _header(pdf, 'Solicitud de vacaciones', 'Documento para firma del trabajador y registro interno', reference, BRAND)

    y = PAGE_H - 72 * mm
    y = _section_title(pdf, y, 'Datos del trabajador')
    _field(pdf, LEFT + 12 * mm, y, 'Trabajador', employee.full_name, 78 * mm)
    _field(pdf, LEFT + 103 * mm, y, 'DNI/NIE', employee.national_id, 55 * mm)
    y -= 20 * mm
    _field(pdf, LEFT + 12 * mm, y, 'Departamento', employee.department, 78 * mm)
    _field(pdf, LEFT + 103 * mm, y, 'Puesto', employee.position, 55 * mm)

    y -= 22 * mm
    y = _section_title(pdf, y, 'Periodo solicitado')
    card_w = (CONTENT_W - 36 * mm) / 3
    _metric_card(pdf, LEFT + 12 * mm, y - 18 * mm, card_w, 'Inicio', vacation_request.start_date.strftime('%d/%m/%Y'))
    _metric_card(pdf, LEFT + 18 * mm + card_w, y - 18 * mm, card_w, 'Fin', vacation_request.end_date.strftime('%d/%m/%Y'))
    _metric_card(pdf, LEFT + 24 * mm + card_w * 2, y - 18 * mm, card_w, 'Días solicitados', f'{vacation_request.requested_days:g}')
    _pill(pdf, RIGHT - 55 * mm, y + 2 * mm, 'Pendiente firma', WARNING_SOFT, color=colors.HexColor('#92400e'), width=44 * mm)

    y -= 51 * mm
    y = _section_title(pdf, y, 'Observaciones del trabajador')
    _card(pdf, LEFT + 12 * mm, y - 38 * mm, CONTENT_W - 24 * mm, 40 * mm, colors.HexColor('#fbfdff'))
    _wrapped_text(pdf, LEFT + 18 * mm, y - 8 * mm, vacation_request.notes or 'Sin observaciones indicadas por el trabajador.', 96, 5 * mm, 6)

    y -= 62 * mm
    y = _section_title(pdf, y, 'Firmas y conformidad')
    _signature_box(pdf, LEFT + 12 * mm, y - 32 * mm, 72 * mm, 'Firma del trabajador', 'Declaro que solicito el periodo indicado.')
    _signature_box(pdf, RIGHT - 84 * mm, y - 32 * mm, 72 * mm, 'Recepción empresa', 'Sello / firma de recepción.')

    _footer(pdf, reference)
    pdf.showPage()
    pdf.save()

    filename = f'solicitud_vacaciones_{vacation_request.pk}.pdf'
    return ContentFile(buffer.getvalue(), name=filename)


def build_decision_pdf(decision) -> ContentFile:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    request = decision.request
    employee = request.employee
    approved = decision.decision == decision.Decision.APPROVED
    accent = SUCCESS if approved else DANGER
    soft = SUCCESS_SOFT if approved else DANGER_SOFT
    reference = f'RES-{request.pk:05d}'
    _set_doc_info(pdf, f'Resolución de vacaciones {reference}')
    _header(pdf, 'Resolución de vacaciones', 'Documento oficial con la decisión de dirección', reference, accent)

    y = PAGE_H - 78 * mm
    y = _approval_strip(pdf, y, decision.get_decision_display(), soft, accent)

    y = _section_title(pdf, y, 'Resumen de la solicitud', accent)
    _field(pdf, LEFT + 12 * mm, y, 'Trabajador', employee.full_name, 78 * mm)
    _field(pdf, LEFT + 103 * mm, y, 'Departamento', employee.department, 55 * mm)
    y -= 20 * mm
    _field(pdf, LEFT + 12 * mm, y, 'Periodo', f'{request.start_date:%d/%m/%Y} - {request.end_date:%d/%m/%Y}', 78 * mm)
    _field(pdf, LEFT + 103 * mm, y, 'Días solicitados', f'{request.requested_days:g}', 55 * mm)

    y -= 24 * mm
    y = _section_title(pdf, y, 'Decisión de dirección', accent)
    _card(pdf, LEFT + 12 * mm, y - 43 * mm, CONTENT_W - 24 * mm, 45 * mm, colors.HexColor('#fbfdff'))
    headline = 'La solicitud queda autorizada para el periodo indicado.' if approved else 'La solicitud queda denegada para el periodo indicado.'
    _text(pdf, LEFT + 18 * mm, y - 8 * mm, headline, 11, accent, 'Helvetica-Bold')
    _wrapped_text(pdf, LEFT + 18 * mm, y - 17 * mm, decision.company_notes or 'Dirección no añade observaciones adicionales.', 96, 5 * mm, 5)

    y -= 67 * mm
    y = _section_title(pdf, y, 'Trazabilidad')
    _field(pdf, LEFT + 12 * mm, y, 'Responsable', str(decision.decided_by), 72 * mm)
    _field(pdf, LEFT + 100 * mm, y, 'Fecha de resolución', timezone.localtime(decision.decided_at).strftime('%d/%m/%Y · %H:%M'), 60 * mm)

    y -= 26 * mm
    y = _section_title(pdf, y, 'Firmas')
    _signature_box(pdf, LEFT + 12 * mm, y - 32 * mm, 72 * mm, 'Firma dirección', 'Valida la resolución de empresa.')
    _signature_box(pdf, RIGHT - 84 * mm, y - 32 * mm, 72 * mm, 'Recibí trabajador', 'Recibí y fecha de comunicación.')

    _footer(pdf, reference)
    pdf.showPage()
    pdf.save()

    filename = f'resolucion_vacaciones_{request.pk}.pdf'
    return ContentFile(buffer.getvalue(), name=filename)
