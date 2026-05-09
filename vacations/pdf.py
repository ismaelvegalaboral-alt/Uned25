from io import BytesIO
from textwrap import wrap

from django.core.files.base import ContentFile
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

PAGE_W, PAGE_H = A4
NAVY = colors.HexColor('#111827')
BLUE = colors.HexColor('#2563eb')
BLUE_DARK = colors.HexColor('#1e40af')
SKY = colors.HexColor('#e0f2fe')
INK = colors.HexColor('#172033')
MUTED = colors.HexColor('#667085')
LINE = colors.HexColor('#d0d5dd')
PAPER = colors.HexColor('#fbfcff')
SOFT = colors.HexColor('#f3f6fb')
GOLD = colors.HexColor('#d99a25')
GREEN = colors.HexColor('#129448')
GREEN_SOFT = colors.HexColor('#e8f8ee')
RED = colors.HexColor('#c92828')
RED_SOFT = colors.HexColor('#fdecec')

MARGIN = 18 * mm
CONTENT_LEFT = 43 * mm
CONTENT_RIGHT = PAGE_W - MARGIN
CONTENT_W = CONTENT_RIGHT - CONTENT_LEFT


def _set_doc_info(pdf: canvas.Canvas, title: str) -> None:
    pdf.setTitle(title)
    pdf.setAuthor('Vacaciones Pro')
    pdf.setSubject('Gestión documental de vacaciones')
    pdf.setCreator('Vacaciones Pro · Django + ReportLab')


def _text(pdf: canvas.Canvas, x: float, y: float, value: str, size: int = 10, color=INK, font: str = 'Helvetica') -> None:
    pdf.setFillColor(color)
    pdf.setFont(font, size)
    pdf.drawString(x, y, value)


def _center(pdf: canvas.Canvas, x: float, y: float, value: str, size: int = 10, color=INK, font: str = 'Helvetica') -> None:
    pdf.setFillColor(color)
    pdf.setFont(font, size)
    pdf.drawCentredString(x, y, value)


def _right(pdf: canvas.Canvas, x: float, y: float, value: str, size: int = 10, color=INK, font: str = 'Helvetica') -> None:
    pdf.setFillColor(color)
    pdf.setFont(font, size)
    pdf.drawRightString(x, y, value)


def _wrapped(pdf: canvas.Canvas, x: float, y: float, value: str, chars: int, max_lines: int, size: int = 9, color=MUTED) -> float:
    pdf.setFont('Helvetica', size)
    pdf.setFillColor(color)
    lines = []
    for raw_line in (value or '').splitlines() or ['']:
        lines.extend(wrap(raw_line, chars) or [''])
    for line in lines[:max_lines]:
        pdf.drawString(x, y, line)
        y -= 5 * mm
    return y


def _rule(pdf: canvas.Canvas, x: float, y: float, w: float, color=LINE) -> None:
    pdf.setStrokeColor(color)
    pdf.setLineWidth(0.6)
    pdf.line(x, y, x + w, y)


def _page_base(pdf: canvas.Canvas, reference: str, document_type: str, accent=BLUE) -> None:
    pdf.setFillColor(PAPER)
    pdf.rect(0, 0, PAGE_W, PAGE_H, fill=True, stroke=False)
    pdf.setFillColor(NAVY)
    pdf.rect(0, 0, 31 * mm, PAGE_H, fill=True, stroke=False)
    pdf.setFillColor(accent)
    pdf.rect(31 * mm, 0, 2.5 * mm, PAGE_H, fill=True, stroke=False)

    pdf.setFillColor(colors.white)
    pdf.circle(15.5 * mm, PAGE_H - 26 * mm, 9 * mm, fill=True, stroke=False)
    _center(pdf, 15.5 * mm, PAGE_H - 29 * mm, 'VP', 12, NAVY, 'Helvetica-Bold')

    pdf.saveState()
    pdf.translate(14 * mm, PAGE_H / 2)
    pdf.rotate(90)
    _center(pdf, 0, 0, 'VACACIONES PRO', 8, colors.HexColor('#dbeafe'), 'Helvetica-Bold')
    pdf.restoreState()

    _text(pdf, CONTENT_LEFT, PAGE_H - 25 * mm, document_type.upper(), 8, accent, 'Helvetica-Bold')
    _right(pdf, CONTENT_RIGHT, PAGE_H - 25 * mm, reference, 9, MUTED, 'Helvetica-Bold')
    _rule(pdf, CONTENT_LEFT, PAGE_H - 30 * mm, CONTENT_W)


def _field(pdf: canvas.Canvas, x: float, y: float, label: str, value: str, w: float) -> None:
    _text(pdf, x, y + 5 * mm, label.upper(), 6.5, MUTED, 'Helvetica-Bold')
    _text(pdf, x, y - 1 * mm, value or '—', 10, INK, 'Helvetica-Bold')
    _rule(pdf, x, y - 4 * mm, w, colors.HexColor('#e5e7eb'))


def _section(pdf: canvas.Canvas, y: float, number: str, title: str, accent=BLUE) -> float:
    pdf.setFillColor(accent)
    pdf.circle(CONTENT_LEFT + 4 * mm, y + 1.5 * mm, 4 * mm, fill=True, stroke=False)
    _center(pdf, CONTENT_LEFT + 4 * mm, y - 1 * mm, number, 7, colors.white, 'Helvetica-Bold')
    _text(pdf, CONTENT_LEFT + 12 * mm, y - 1 * mm, title, 13, INK, 'Helvetica-Bold')
    return y - 12 * mm


def _soft_box(pdf: canvas.Canvas, x: float, y: float, w: float, h: float, fill=SOFT, stroke=LINE, radius=4 * mm) -> None:
    pdf.setFillColor(fill)
    pdf.setStrokeColor(stroke)
    pdf.setLineWidth(0.8)
    pdf.roundRect(x, y, w, h, radius, fill=True, stroke=True)


def _signature(pdf: canvas.Canvas, x: float, y: float, title: str, subtitle: str, w: float = 62 * mm) -> None:
    _soft_box(pdf, x, y, w, 28 * mm, colors.white, LINE)
    _rule(pdf, x + 8 * mm, y + 16 * mm, w - 16 * mm, colors.HexColor('#98a2b3'))
    _center(pdf, x + w / 2, y + 8 * mm, title, 8.5, INK, 'Helvetica-Bold')
    _center(pdf, x + w / 2, y + 4 * mm, subtitle, 6.5, MUTED)


def _footer(pdf: canvas.Canvas, reference: str) -> None:
    _rule(pdf, CONTENT_LEFT, 17 * mm, CONTENT_W, colors.HexColor('#e5e7eb'))
    _text(pdf, CONTENT_LEFT, 11 * mm, 'Documento generado automáticamente y archivado en Vacaciones Pro.', 7, MUTED)
    _right(pdf, CONTENT_RIGHT, 11 * mm, reference, 7, MUTED, 'Helvetica-Bold')


def _period_tile(pdf: canvas.Canvas, x: float, y: float, label: str, value: str, accent=BLUE) -> None:
    _soft_box(pdf, x, y, 44 * mm, 29 * mm, colors.white, colors.HexColor('#dbeafe'))
    _text(pdf, x + 5 * mm, y + 19 * mm, label.upper(), 7, MUTED, 'Helvetica-Bold')
    _text(pdf, x + 5 * mm, y + 8 * mm, value, 15, accent, 'Helvetica-Bold')


def build_request_pdf(vacation_request) -> ContentFile:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    employee = vacation_request.employee
    reference = f'SOL-{vacation_request.pk:05d}'
    generated = timezone.localtime().strftime('%d/%m/%Y · %H:%M')

    _set_doc_info(pdf, f'Solicitud de vacaciones {reference}')
    _page_base(pdf, reference, 'Solicitud de vacaciones', BLUE)

    _text(pdf, CONTENT_LEFT, PAGE_H - 48 * mm, 'Solicitud formal de vacaciones', 24, INK, 'Helvetica-Bold')
    _wrapped(
        pdf,
        CONTENT_LEFT,
        PAGE_H - 57 * mm,
        'Documento preparado para revisión interna, firma del trabajador y archivo de Recursos Humanos.',
        84,
        2,
        9,
        MUTED,
    )
    pdf.setFillColor(SKY)
    pdf.roundRect(CONTENT_RIGHT - 52 * mm, PAGE_H - 56 * mm, 52 * mm, 13 * mm, 6.5 * mm, fill=True, stroke=False)
    _center(pdf, CONTENT_RIGHT - 26 * mm, PAGE_H - 51 * mm, 'PENDIENTE DE FIRMA', 8, BLUE_DARK, 'Helvetica-Bold')

    y = PAGE_H - 84 * mm
    y = _section(pdf, y, '1', 'Identificación del trabajador')
    _soft_box(pdf, CONTENT_LEFT, y - 24 * mm, CONTENT_W, 31 * mm, colors.white, colors.HexColor('#e2e8f0'))
    _field(pdf, CONTENT_LEFT + 7 * mm, y - 5 * mm, 'Trabajador', employee.full_name, 63 * mm)
    _field(pdf, CONTENT_LEFT + 79 * mm, y - 5 * mm, 'DNI/NIE', employee.national_id, 40 * mm)
    _field(pdf, CONTENT_LEFT + 126 * mm, y - 5 * mm, 'Departamento', employee.department, 39 * mm)
    _field(pdf, CONTENT_LEFT + 7 * mm, y - 20 * mm, 'Puesto', employee.position, 74 * mm)
    _field(pdf, CONTENT_LEFT + 91 * mm, y - 20 * mm, 'Fecha de emisión', generated, 74 * mm)

    y -= 49 * mm
    y = _section(pdf, y, '2', 'Periodo solicitado')
    _period_tile(pdf, CONTENT_LEFT, y - 27 * mm, 'Inicio', vacation_request.start_date.strftime('%d/%m/%Y'))
    _period_tile(pdf, CONTENT_LEFT + 53 * mm, y - 27 * mm, 'Fin', vacation_request.end_date.strftime('%d/%m/%Y'))
    _period_tile(pdf, CONTENT_LEFT + 106 * mm, y - 27 * mm, 'Días', f'{vacation_request.requested_days:g}')

    y -= 54 * mm
    y = _section(pdf, y, '3', 'Declaración y observaciones')
    _soft_box(pdf, CONTENT_LEFT, y - 44 * mm, CONTENT_W, 48 * mm, colors.white, colors.HexColor('#e2e8f0'))
    _text(pdf, CONTENT_LEFT + 8 * mm, y - 8 * mm, 'Declaración', 9, BLUE_DARK, 'Helvetica-Bold')
    _wrapped(
        pdf,
        CONTENT_LEFT + 8 * mm,
        y - 16 * mm,
        'La persona trabajadora solicita disfrutar el periodo indicado y se compromete a firmar este documento para su tramitación interna.',
        100,
        3,
        8.5,
        INK,
    )
    _text(pdf, CONTENT_LEFT + 8 * mm, y - 33 * mm, 'Observaciones', 8.5, MUTED, 'Helvetica-Bold')
    _wrapped(pdf, CONTENT_LEFT + 38 * mm, y - 33 * mm, vacation_request.notes or 'Sin observaciones.', 77, 2, 8.5, MUTED)

    y -= 68 * mm
    y = _section(pdf, y, '4', 'Firmas')
    _signature(pdf, CONTENT_LEFT, y - 31 * mm, 'Firma del trabajador', 'Nombre, firma y fecha')
    _signature(pdf, CONTENT_RIGHT - 62 * mm, y - 31 * mm, 'Recepción empresa', 'Sello, firma y fecha')

    _footer(pdf, reference)
    pdf.showPage()
    pdf.save()

    filename = f'solicitud_vacaciones_{vacation_request.pk}.pdf'
    return ContentFile(buffer.getvalue(), name=filename)


def _decision_header(pdf: canvas.Canvas, reference: str, status_label: str, accent, soft) -> None:
    pdf.setFillColor(PAPER)
    pdf.rect(0, 0, PAGE_W, PAGE_H, fill=True, stroke=False)
    pdf.setStrokeColor(accent)
    pdf.setLineWidth(2)
    pdf.roundRect(MARGIN, MARGIN, PAGE_W - 2 * MARGIN, PAGE_H - 2 * MARGIN, 6 * mm, fill=False, stroke=True)
    pdf.setStrokeColor(colors.HexColor('#e5e7eb'))
    pdf.setLineWidth(0.8)
    pdf.roundRect(MARGIN + 4 * mm, MARGIN + 4 * mm, PAGE_W - 2 * MARGIN - 8 * mm, PAGE_H - 2 * MARGIN - 8 * mm, 4 * mm, fill=False, stroke=True)

    pdf.setFillColor(soft)
    pdf.roundRect(31 * mm, PAGE_H - 68 * mm, PAGE_W - 62 * mm, 33 * mm, 8 * mm, fill=True, stroke=False)
    _center(pdf, PAGE_W / 2, PAGE_H - 47 * mm, f'RESOLUCIÓN {status_label.upper()}', 23, accent, 'Helvetica-Bold')
    _center(pdf, PAGE_W / 2, PAGE_H - 57 * mm, 'Decisión de la empresa sobre la solicitud de vacaciones', 9, MUTED)
    _text(pdf, 31 * mm, PAGE_H - 28 * mm, 'VACACIONES PRO', 8, NAVY, 'Helvetica-Bold')
    _right(pdf, PAGE_W - 31 * mm, PAGE_H - 28 * mm, reference, 9, MUTED, 'Helvetica-Bold')


def _decision_row(pdf: canvas.Canvas, y: float, label: str, value: str, x: float, w: float) -> None:
    _text(pdf, x, y + 4 * mm, label.upper(), 6.5, MUTED, 'Helvetica-Bold')
    _text(pdf, x, y - 2 * mm, value or '—', 10, INK, 'Helvetica-Bold')
    _rule(pdf, x, y - 5 * mm, w, colors.HexColor('#e5e7eb'))


def build_decision_pdf(decision) -> ContentFile:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    request = decision.request
    employee = request.employee
    approved = decision.decision == decision.Decision.APPROVED
    accent = GREEN if approved else RED
    soft = GREEN_SOFT if approved else RED_SOFT
    reference = f'RES-{request.pk:05d}'
    status_label = decision.get_decision_display()
    decided_at = timezone.localtime(decision.decided_at).strftime('%d/%m/%Y · %H:%M')

    _set_doc_info(pdf, f'Resolución de vacaciones {reference}')
    _decision_header(pdf, reference, status_label, accent, soft)

    y = PAGE_H - 92 * mm
    _center(pdf, PAGE_W / 2, y + 8 * mm, 'ACTA DE RESOLUCIÓN', 10, GOLD, 'Helvetica-Bold')
    _text(pdf, 34 * mm, y - 2 * mm, 'Solicitud evaluada', 14, INK, 'Helvetica-Bold')
    _decision_row(pdf, y - 18 * mm, 'Trabajador', employee.full_name, 34 * mm, 68 * mm)
    _decision_row(pdf, y - 18 * mm, 'Departamento', employee.department, 112 * mm, 50 * mm)
    _decision_row(pdf, y - 35 * mm, 'Periodo', f'{request.start_date:%d/%m/%Y} - {request.end_date:%d/%m/%Y}', 34 * mm, 68 * mm)
    _decision_row(pdf, y - 35 * mm, 'Días solicitados', f'{request.requested_days:g}', 112 * mm, 50 * mm)

    y -= 62 * mm
    _soft_box(pdf, 34 * mm, y - 51 * mm, PAGE_W - 68 * mm, 54 * mm, colors.white, colors.HexColor('#e2e8f0'))
    _text(pdf, 43 * mm, y - 12 * mm, 'Resultado de dirección', 10, accent, 'Helvetica-Bold')
    headline = 'La empresa autoriza el disfrute del periodo solicitado.' if approved else 'La empresa no autoriza el disfrute del periodo solicitado.'
    _wrapped(pdf, 43 * mm, y - 23 * mm, headline, 92, 2, 13, INK)
    _text(pdf, 43 * mm, y - 38 * mm, 'Observaciones:', 8, MUTED, 'Helvetica-Bold')
    _wrapped(pdf, 70 * mm, y - 38 * mm, decision.company_notes or 'Sin observaciones adicionales por parte de dirección.', 71, 2, 8.5, MUTED)

    y -= 78 * mm
    _text(pdf, 34 * mm, y, 'Trazabilidad y firmas', 14, INK, 'Helvetica-Bold')
    _decision_row(pdf, y - 18 * mm, 'Responsable', str(decision.decided_by), 34 * mm, 62 * mm)
    _decision_row(pdf, y - 18 * mm, 'Fecha de resolución', decided_at, 108 * mm, 58 * mm)
    _signature(pdf, 34 * mm, y - 58 * mm, 'Firma dirección', 'Conforme a la resolución', 58 * mm)
    _signature(pdf, PAGE_W - 92 * mm, y - 58 * mm, 'Recibí trabajador', 'Comunicación recibida', 58 * mm)

    _footer(pdf, reference)
    pdf.showPage()
    pdf.save()

    filename = f'resolucion_vacaciones_{request.pk}.pdf'
    return ContentFile(buffer.getvalue(), name=filename)
