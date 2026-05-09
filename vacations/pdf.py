from io import BytesIO
from textwrap import wrap

from django.core.files.base import ContentFile
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

PAGE_W, PAGE_H = A4
MARGIN = 18 * mm
CONTENT_W = PAGE_W - 2 * MARGIN
NAVY = colors.HexColor('#1d2a57')
GOLD = colors.HexColor('#ffb000')
BLUE = colors.HexColor('#1d4ed8')
BLUE_SOFT = colors.HexColor('#eff6ff')
INK = colors.HexColor('#111827')
SLATE = colors.HexColor('#475569')
MUTED = colors.HexColor('#94a3b8')
LINE = colors.HexColor('#dbe4f0')
PAPER = colors.HexColor('#f8fafc')
WHITE = colors.white
GREEN = colors.HexColor('#15803d')
GREEN_SOFT = colors.HexColor('#ecfdf3')
RED = colors.HexColor('#b91c1c')
RED_SOFT = colors.HexColor('#fef2f2')
AMBER_SOFT = colors.HexColor('#fff7ed')


def _set_doc_info(pdf: canvas.Canvas, title: str) -> None:
    pdf.setTitle(title)
    pdf.setAuthor('Kalpae Ibérica')
    pdf.setSubject('Gestión documental de vacaciones')
    pdf.setCreator('Vacaciones Pro · Django + ReportLab')


def _txt(pdf: canvas.Canvas, x: float, y: float, value: str, size: float = 9, color=INK, font: str = 'Helvetica') -> None:
    pdf.setFillColor(color)
    pdf.setFont(font, size)
    pdf.drawString(x, y, str(value or '—'))


def _right(pdf: canvas.Canvas, x: float, y: float, value: str, size: float = 9, color=INK, font: str = 'Helvetica') -> None:
    pdf.setFillColor(color)
    pdf.setFont(font, size)
    pdf.drawRightString(x, y, str(value or '—'))


def _center(pdf: canvas.Canvas, x: float, y: float, value: str, size: float = 9, color=INK, font: str = 'Helvetica') -> None:
    pdf.setFillColor(color)
    pdf.setFont(font, size)
    pdf.drawCentredString(x, y, str(value or '—'))


def _rounded(pdf: canvas.Canvas, x: float, y: float, w: float, h: float, fill=WHITE, stroke=LINE, radius: float = 4 * mm, width: float = 0.7) -> None:
    pdf.setFillColor(fill)
    pdf.setStrokeColor(stroke)
    pdf.setLineWidth(width)
    pdf.roundRect(x, y, w, h, radius, fill=True, stroke=True)


def _line(pdf: canvas.Canvas, x: float, y: float, w: float, color=LINE, width: float = 0.6) -> None:
    pdf.setStrokeColor(color)
    pdf.setLineWidth(width)
    pdf.line(x, y, x + w, y)


def _wrap_lines(value: str, chars: int, max_lines: int) -> list[str]:
    rows = []
    for raw in (value or '—').splitlines() or ['—']:
        rows.extend(wrap(raw, chars) or [''])
    return rows[:max_lines]


def _wrapped(pdf: canvas.Canvas, x: float, y: float, value: str, chars: int, max_lines: int, size: float = 8.5, color=SLATE, leading: float = 4.6 * mm) -> None:
    pdf.setFillColor(color)
    pdf.setFont('Helvetica', size)
    for row in _wrap_lines(value, chars, max_lines):
        pdf.drawString(x, y, row)
        y -= leading


def _draw_kalpae_logo(pdf: canvas.Canvas, x: float, y: float, width: float) -> None:
    """Draw a compact vector version of the Kalpae Ibérica logo for PDFs."""
    icon = width * 0.18
    height = icon * 0.84
    pdf.saveState()
    pdf.setFillColor(NAVY)
    pdf.rect(x, y, icon * 0.20, height, fill=True, stroke=False)
    pdf.setFillColor(GOLD)
    pdf.rect(x + icon * 0.72, y + height * 0.18, icon * 0.20, height * 0.64, fill=True, stroke=False)
    pdf.setFillColor(GOLD)
    pdf.roundRect(x + icon * 0.31, y + height * 0.55, icon * 0.48, height * 0.34, 1.2 * mm, fill=True, stroke=False)
    pdf.setFillColor(NAVY)
    pdf.roundRect(x + icon * 0.28, y + height * 0.36, icon * 0.54, height * 0.20, 1.2 * mm, fill=True, stroke=False)
    pdf.roundRect(x + icon * 0.30, y + height * 0.02, icon * 0.50, height * 0.22, 1.2 * mm, fill=True, stroke=False)
    pdf.setStrokeColor(WHITE)
    pdf.setLineWidth(2.2)
    pdf.line(x + icon * 0.20, y + height * 0.06, x + icon * 0.86, y + height * 0.86)

    text_x = x + icon + width * 0.04
    pdf.setFillColor(NAVY)
    pdf.setFont('Helvetica-Bold', max(13, width / mm * 0.55))
    pdf.drawString(text_x, y + height * 0.37, 'KALPAE')
    pdf.setFillColor(GOLD)
    pdf.setFont('Helvetica-Bold', max(6.5, width / mm * 0.22))
    pdf.drawString(text_x + width * 0.02, y + height * 0.10, 'IBÉRICA')
    pdf.restoreState()


def _header(pdf: canvas.Canvas, reference: str, title: str, subtitle: str, accent=BLUE) -> None:
    pdf.setFillColor(PAPER)
    pdf.rect(0, 0, PAGE_W, PAGE_H, fill=True, stroke=False)
    pdf.setFillColor(WHITE)
    pdf.rect(0, PAGE_H - 42 * mm, PAGE_W, 42 * mm, fill=True, stroke=False)
    _draw_kalpae_logo(pdf, MARGIN, PAGE_H - 32 * mm, 74 * mm)
    _right(pdf, PAGE_W - MARGIN, PAGE_H - 22 * mm, reference, 8.5, SLATE, 'Helvetica-Bold')
    _right(pdf, PAGE_W - MARGIN, PAGE_H - 29 * mm, 'Vacaciones Pro', 7.2, MUTED)
    _line(pdf, MARGIN, PAGE_H - 44 * mm, CONTENT_W)
    _txt(pdf, MARGIN, PAGE_H - 59 * mm, title, 19, INK, 'Helvetica-Bold')
    _wrapped(pdf, MARGIN, PAGE_H - 68 * mm, subtitle, 118, 2, 8.2, SLATE, 4 * mm)
    pdf.setFillColor(accent)
    pdf.rect(MARGIN, PAGE_H - 75 * mm, 26 * mm, 1.4 * mm, fill=True, stroke=False)


def _section_title(pdf: canvas.Canvas, x: float, y: float, number: str, title: str, accent=BLUE) -> None:
    pdf.setFillColor(accent)
    pdf.circle(x + 3 * mm, y + 1 * mm, 3.4 * mm, fill=True, stroke=False)
    _center(pdf, x + 3 * mm, y - 1.2 * mm, number, 6.2, WHITE, 'Helvetica-Bold')
    _txt(pdf, x + 10 * mm, y - 1.4 * mm, title, 11.2, INK, 'Helvetica-Bold')


def _field(pdf: canvas.Canvas, x: float, y: float, w: float, label: str, value: str, accent=BLUE) -> None:
    _txt(pdf, x, y + 7 * mm, label.upper(), 6.2, accent, 'Helvetica-Bold')
    _wrapped(pdf, x, y, value or '—', max(16, int(w / mm * 0.9)), 2, 8.6, INK, 3.7 * mm)
    _line(pdf, x, y - 5 * mm, w, colors.HexColor('#e7edf5'))


def _metric(pdf: canvas.Canvas, x: float, y: float, w: float, label: str, value: str, accent=BLUE) -> None:
    _rounded(pdf, x, y, w, 25 * mm, WHITE, colors.HexColor('#cfe0f7'), 3.5 * mm)
    _txt(pdf, x + 5 * mm, y + 16.3 * mm, label.upper(), 6.2, SLATE, 'Helvetica-Bold')
    _txt(pdf, x + 5 * mm, y + 7 * mm, value, 13, accent, 'Helvetica-Bold')


def _signature(pdf: canvas.Canvas, x: float, y: float, w: float, title: str) -> None:
    _rounded(pdf, x, y, w, 28 * mm, WHITE, colors.HexColor('#d5deeb'), 3.5 * mm)
    _line(pdf, x + 8 * mm, y + 15 * mm, w - 16 * mm, colors.HexColor('#9aa8ba'), 0.7)
    _center(pdf, x + w / 2, y + 8 * mm, title, 8, INK, 'Helvetica-Bold')
    _center(pdf, x + w / 2, y + 4 * mm, 'Firma y fecha', 6.6, SLATE)


def _compact_signature(pdf: canvas.Canvas, x: float, y: float, w: float, title: str) -> None:
    _rounded(pdf, x, y, w, 22 * mm, WHITE, colors.HexColor('#d5deeb'), 3.5 * mm)
    _line(pdf, x + 8 * mm, y + 12 * mm, w - 16 * mm, colors.HexColor('#9aa8ba'), 0.7)
    _center(pdf, x + w / 2, y + 6.8 * mm, title, 7.8, INK, 'Helvetica-Bold')
    _center(pdf, x + w / 2, y + 3.2 * mm, 'Firma y fecha', 6.2, SLATE)


def _footer(pdf: canvas.Canvas, reference: str) -> None:
    _line(pdf, MARGIN, 18 * mm, CONTENT_W, colors.HexColor('#e7edf5'))
    _txt(pdf, MARGIN, 11.5 * mm, 'Documento generado automáticamente y archivado en Vacaciones Pro.', 6.5, MUTED)
    _right(pdf, PAGE_W - MARGIN, 11.5 * mm, reference, 6.5, SLATE, 'Helvetica-Bold')


def build_request_pdf(vacation_request) -> ContentFile:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    employee = vacation_request.employee
    reference = f'SOL-{vacation_request.pk:05d}'
    generated_at = timezone.localtime().strftime('%d/%m/%Y · %H:%M')

    _set_doc_info(pdf, f'Solicitud de vacaciones {reference}')
    _header(
        pdf,
        reference,
        'Solicitud formal de vacaciones',
        'Documento para revisión interna, firma del trabajador y archivo en Recursos Humanos.',
        BLUE,
    )

    y = PAGE_H - 91 * mm
    _section_title(pdf, MARGIN, y, '1', 'Identificación del trabajador')
    _rounded(pdf, MARGIN, y - 39 * mm, CONTENT_W, 30 * mm, WHITE, LINE, 4 * mm)
    _field(pdf, MARGIN + 7 * mm, y - 25 * mm, 58 * mm, 'Trabajador', employee.full_name)
    _field(pdf, MARGIN + 73 * mm, y - 25 * mm, 37 * mm, 'DNI/NIE', employee.national_id)
    _field(pdf, MARGIN + 118 * mm, y - 25 * mm, 40 * mm, 'Departamento', employee.department)

    y = PAGE_H - 143 * mm
    _section_title(pdf, MARGIN, y, '2', 'Periodo solicitado')
    gap = 10 * mm
    metric_w = (CONTENT_W - 2 * gap) / 3
    _metric(pdf, MARGIN, y - 36 * mm, metric_w, 'Inicio', vacation_request.start_date.strftime('%d/%m/%Y'))
    _metric(pdf, MARGIN + metric_w + gap, y - 36 * mm, metric_w, 'Fin', vacation_request.end_date.strftime('%d/%m/%Y'))
    _metric(pdf, MARGIN + 2 * (metric_w + gap), y - 36 * mm, metric_w, 'Días', f'{vacation_request.requested_days:g}')

    y = PAGE_H - 195 * mm
    _section_title(pdf, MARGIN, y, '3', 'Declaración y observaciones')
    _rounded(pdf, MARGIN, y - 48 * mm, CONTENT_W, 38 * mm, WHITE, LINE, 4 * mm)
    _txt(pdf, MARGIN + 7 * mm, y - 22 * mm, 'Declaración', 7.2, BLUE, 'Helvetica-Bold')
    _wrapped(
        pdf,
        MARGIN + 7 * mm,
        y - 31 * mm,
        'La persona trabajadora solicita disfrutar el periodo indicado y se compromete a firmar este documento para su tramitación interna.',
        112,
        2,
        8,
        INK,
        4 * mm,
    )
    _txt(pdf, MARGIN + 7 * mm, y - 42 * mm, 'Observaciones:', 7, SLATE, 'Helvetica-Bold')
    _wrapped(pdf, MARGIN + 36 * mm, y - 42 * mm, vacation_request.notes or 'Sin observaciones.', 82, 1, 7.8, SLATE)

    _txt(pdf, MARGIN, 62 * mm, 'Firmas', 11.2, INK, 'Helvetica-Bold')
    sig_w = 72 * mm
    _signature(pdf, MARGIN, 29 * mm, sig_w, 'Trabajador/a')
    _signature(pdf, PAGE_W - MARGIN - sig_w, 29 * mm, sig_w, 'Recepción empresa')

    _footer(pdf, reference)
    pdf.showPage()
    pdf.save()

    return ContentFile(buffer.getvalue(), name=f'solicitud_vacaciones_{vacation_request.pk}.pdf')


def _decision_status_box(pdf: canvas.Canvas, decision_label: str, approved: bool) -> tuple:
    accent = GREEN if approved else RED
    soft = GREEN_SOFT if approved else RED_SOFT
    pdf.setFillColor(soft)
    pdf.setStrokeColor(colors.HexColor('#d8e2ef'))
    pdf.setLineWidth(0.7)
    pdf.roundRect(MARGIN, PAGE_H - 91 * mm, CONTENT_W, 29 * mm, 5 * mm, fill=True, stroke=True)
    _center(pdf, PAGE_W / 2, PAGE_H - 75 * mm, f'RESOLUCIÓN {decision_label.upper()}', 19, accent, 'Helvetica-Bold')
    _center(pdf, PAGE_W / 2, PAGE_H - 84 * mm, 'Comunicación formal de la decisión de la empresa', 8.2, SLATE)
    return accent, soft


def _decision_field(pdf: canvas.Canvas, x: float, y: float, w: float, label: str, value: str, accent) -> None:
    _txt(pdf, x, y + 7 * mm, label.upper(), 6, accent, 'Helvetica-Bold')
    _wrapped(pdf, x, y, value or '—', max(16, int(w / mm * 0.9)), 2, 8.4, INK, 3.7 * mm)
    _line(pdf, x, y - 5 * mm, w, colors.HexColor('#e7edf5'))


def build_decision_pdf(decision) -> ContentFile:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    request = decision.request
    employee = request.employee
    approved = decision.decision == decision.Decision.APPROVED
    reference = f'RES-{request.pk:05d}'
    status_label = decision.get_decision_display()
    decided_at = timezone.localtime(decision.decided_at).strftime('%d/%m/%Y · %H:%M')

    _set_doc_info(pdf, f'Resolución de vacaciones {reference}')
    _header(
        pdf,
        reference,
        'Resolución de solicitud de vacaciones',
        'Documento de comunicación oficial emitido por la empresa tras la revisión de la solicitud.',
        GREEN if approved else RED,
    )
    accent, soft = _decision_status_box(pdf, status_label, approved)

    y = PAGE_H - 114 * mm
    _section_title(pdf, MARGIN, y, '1', 'Solicitud evaluada', accent)
    _rounded(pdf, MARGIN, y - 48 * mm, CONTENT_W, 39 * mm, WHITE, LINE, 4 * mm)
    _decision_field(pdf, MARGIN + 7 * mm, y - 25 * mm, 65 * mm, 'Trabajador', employee.full_name, accent)
    _decision_field(pdf, MARGIN + 82 * mm, y - 25 * mm, 50 * mm, 'Departamento', employee.department, accent)
    _decision_field(pdf, MARGIN + 7 * mm, y - 42 * mm, 65 * mm, 'Periodo', f'{request.start_date:%d/%m/%Y} - {request.end_date:%d/%m/%Y}', accent)
    _decision_field(pdf, MARGIN + 82 * mm, y - 42 * mm, 50 * mm, 'Días solicitados', f'{request.requested_days:g}', accent)

    y = PAGE_H - 167 * mm
    _section_title(pdf, MARGIN, y, '2', 'Resultado de dirección', accent)
    _rounded(pdf, MARGIN, y - 40 * mm, CONTENT_W, 30 * mm, soft, colors.HexColor('#d8e2ef'), 4 * mm)
    headline = 'La empresa autoriza el disfrute del periodo solicitado.' if approved else 'La empresa no autoriza el disfrute del periodo solicitado.'
    _wrapped(pdf, MARGIN + 8 * mm, y - 23 * mm, headline, 108, 2, 10.2, INK, 4.5 * mm)
    _txt(pdf, MARGIN + 8 * mm, y - 34 * mm, 'Observaciones:', 7, accent, 'Helvetica-Bold')
    _wrapped(pdf, MARGIN + 38 * mm, y - 34 * mm, decision.company_notes or 'Sin observaciones adicionales por parte de dirección.', 78, 1, 7.5, SLATE)

    y = PAGE_H - 219 * mm
    _section_title(pdf, MARGIN, y, '3', 'Trazabilidad y firmas', accent)
    _rounded(pdf, MARGIN, y - 27 * mm, CONTENT_W, 20 * mm, WHITE, LINE, 4 * mm)
    _decision_field(pdf, MARGIN + 7 * mm, y - 22 * mm, 65 * mm, 'Responsable', str(decision.decided_by), accent)
    _decision_field(pdf, MARGIN + 82 * mm, y - 22 * mm, 60 * mm, 'Fecha de resolución', decided_at, accent)
    sig_w = 72 * mm
    _compact_signature(pdf, MARGIN, 23 * mm, sig_w, 'Firma dirección')
    _compact_signature(pdf, PAGE_W - MARGIN - sig_w, 23 * mm, sig_w, 'Recibí trabajador/a')

    _footer(pdf, reference)
    pdf.showPage()
    pdf.save()

    return ContentFile(buffer.getvalue(), name=f'resolucion_vacaciones_{request.pk}.pdf')

