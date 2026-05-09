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
INK = colors.HexColor('#0f172a')
SLATE = colors.HexColor('#475569')
MUTED = colors.HexColor('#94a3b8')
LINE = colors.HexColor('#dbe3ef')
PAPER = colors.HexColor('#f8fafc')
WHITE = colors.white
NAVY = colors.HexColor('#0b1220')
INDIGO = colors.HexColor('#4f46e5')
VIOLET = colors.HexColor('#7c3aed')
CYAN = colors.HexColor('#06b6d4')
ORANGE = colors.HexColor('#f97316')
GREEN = colors.HexColor('#15803d')
GREEN_SOFT = colors.HexColor('#dcfce7')
RED = colors.HexColor('#b91c1c')
RED_SOFT = colors.HexColor('#fee2e2')
GRAPHITE = colors.HexColor('#1e293b')


def _set_doc_info(pdf: canvas.Canvas, title: str) -> None:
    pdf.setTitle(title)
    pdf.setAuthor('Vacaciones Pro')
    pdf.setSubject('Gestión documental de vacaciones')
    pdf.setCreator('Vacaciones Pro · Django + ReportLab')


def _txt(pdf: canvas.Canvas, x: float, y: float, value: str, size: float = 9, color=INK, font: str = 'Helvetica') -> None:
    pdf.setFillColor(color)
    pdf.setFont(font, size)
    pdf.drawString(x, y, value or '—')


def _right(pdf: canvas.Canvas, x: float, y: float, value: str, size: float = 9, color=INK, font: str = 'Helvetica') -> None:
    pdf.setFillColor(color)
    pdf.setFont(font, size)
    pdf.drawRightString(x, y, value or '—')


def _center(pdf: canvas.Canvas, x: float, y: float, value: str, size: float = 9, color=INK, font: str = 'Helvetica') -> None:
    pdf.setFillColor(color)
    pdf.setFont(font, size)
    pdf.drawCentredString(x, y, value or '—')


def _rounded(pdf: canvas.Canvas, x: float, y: float, w: float, h: float, fill=WHITE, stroke=LINE, radius: float = 4 * mm, width: float = 0.8) -> None:
    pdf.setFillColor(fill)
    pdf.setStrokeColor(stroke)
    pdf.setLineWidth(width)
    pdf.roundRect(x, y, w, h, radius, fill=True, stroke=True)


def _shadow_card(pdf: canvas.Canvas, x: float, y: float, w: float, h: float, fill=WHITE, stroke=LINE) -> None:
    pdf.setFillColor(colors.Color(0, 0, 0, alpha=0.08))
    pdf.roundRect(x + 1.6 * mm, y - 1.6 * mm, w, h, 5 * mm, fill=True, stroke=False)
    _rounded(pdf, x, y, w, h, fill, stroke, 5 * mm)


def _wrapped(pdf: canvas.Canvas, x: float, y: float, value: str, chars: int = 90, lines: int = 4, size: float = 8.5, color=SLATE, leading: float = 4.8 * mm) -> float:
    text = value or 'Sin observaciones.'
    pdf.setFillColor(color)
    pdf.setFont('Helvetica', size)
    rows = []
    for raw in text.splitlines() or ['']:
        rows.extend(wrap(raw, chars) or [''])
    for row in rows[:lines]:
        pdf.drawString(x, y, row)
        y -= leading
    return y


def _footer(pdf: canvas.Canvas, reference: str) -> None:
    pdf.setStrokeColor(LINE)
    pdf.setLineWidth(0.7)
    pdf.line(MARGIN, 14 * mm, PAGE_W - MARGIN, 14 * mm)
    _txt(pdf, MARGIN, 8.5 * mm, 'Vacaciones Pro · Documento generado automáticamente y archivado en la plataforma.', 7, MUTED)
    _right(pdf, PAGE_W - MARGIN, 8.5 * mm, reference, 7, SLATE, 'Helvetica-Bold')


def _field_box(pdf: canvas.Canvas, x: float, y: float, w: float, h: float, label: str, value: str, accent=INDIGO) -> None:
    _rounded(pdf, x, y, w, h, colors.HexColor('#f8fafc'), colors.HexColor('#e2e8f0'), 3 * mm)
    _txt(pdf, x + 4 * mm, y + h - 7 * mm, label.upper(), 6.5, accent, 'Helvetica-Bold')
    _wrapped(pdf, x + 4 * mm, y + h - 15 * mm, value or '—', max(18, int(w / mm * 1.1)), 2, 9.5, INK, 4.2 * mm)


def _big_metric(pdf: canvas.Canvas, x: float, y: float, w: float, label: str, value: str, accent=INDIGO) -> None:
    _shadow_card(pdf, x, y, w, 31 * mm, WHITE, colors.HexColor('#e2e8f0'))
    pdf.setFillColor(accent)
    pdf.roundRect(x, y + 24 * mm, w, 7 * mm, 4 * mm, fill=True, stroke=False)
    _center(pdf, x + w / 2, y + 26 * mm, label.upper(), 6.8, WHITE, 'Helvetica-Bold')
    _center(pdf, x + w / 2, y + 9.5 * mm, value, 15, INK, 'Helvetica-Bold')


def _signature_panel(pdf: canvas.Canvas, x: float, y: float, w: float, title: str, caption: str) -> None:
    _rounded(pdf, x, y, w, 34 * mm, colors.HexColor('#f8fafc'), colors.HexColor('#cbd5e1'), 4 * mm)
    _txt(pdf, x + 5 * mm, y + 24 * mm, title, 9, INK, 'Helvetica-Bold')
    pdf.setStrokeColor(colors.HexColor('#64748b'))
    pdf.setLineWidth(0.9)
    pdf.line(x + 8 * mm, y + 14 * mm, x + w - 8 * mm, y + 14 * mm)
    _center(pdf, x + w / 2, y + 6.5 * mm, caption, 7.2, SLATE)


def _request_background(pdf: canvas.Canvas, reference: str, generated_at: str) -> None:
    pdf.setFillColor(PAPER)
    pdf.rect(0, 0, PAGE_W, PAGE_H, fill=True, stroke=False)
    pdf.setFillColor(NAVY)
    pdf.rect(0, PAGE_H - 58 * mm, PAGE_W, 58 * mm, fill=True, stroke=False)
    pdf.setFillColor(INDIGO)
    pdf.rect(0, 0, 12 * mm, PAGE_H, fill=True, stroke=False)
    pdf.setFillColor(VIOLET)
    pdf.circle(PAGE_W - 20 * mm, PAGE_H - 15 * mm, 37 * mm, fill=True, stroke=False)
    pdf.setFillColor(CYAN)
    pdf.circle(PAGE_W - 54 * mm, PAGE_H - 62 * mm, 21 * mm, fill=True, stroke=False)
    pdf.saveState()
    pdf.setFillColor(colors.Color(1, 1, 1, alpha=0.07))
    pdf.rotate(32)
    pdf.rect(135 * mm, 110 * mm, 92 * mm, 13 * mm, fill=True, stroke=False)
    pdf.rect(142 * mm, 92 * mm, 82 * mm, 8 * mm, fill=True, stroke=False)
    pdf.restoreState()

    _txt(pdf, MARGIN + 7 * mm, PAGE_H - 20 * mm, 'VACACIONES PRO', 8.5, colors.HexColor('#a5b4fc'), 'Helvetica-Bold')
    _txt(pdf, MARGIN + 7 * mm, PAGE_H - 34 * mm, 'Orden de solicitud', 25, WHITE, 'Helvetica-Bold')
    _txt(pdf, MARGIN + 7 * mm, PAGE_H - 44 * mm, 'Documento para firma del trabajador y registro en RR. HH.', 9.2, colors.HexColor('#cbd5e1'))
    _right(pdf, PAGE_W - MARGIN, PAGE_H - 22 * mm, reference, 12, WHITE, 'Helvetica-Bold')
    _right(pdf, PAGE_W - MARGIN, PAGE_H - 32 * mm, generated_at, 8.2, colors.HexColor('#cbd5e1'))

    pdf.setFillColor(ORANGE)
    pdf.roundRect(MARGIN + 7 * mm, PAGE_H - 69 * mm, 54 * mm, 11 * mm, 5.5 * mm, fill=True, stroke=False)
    _center(pdf, MARGIN + 34 * mm, PAGE_H - 65.4 * mm, 'PENDIENTE DE FIRMA', 7.5, WHITE, 'Helvetica-Bold')


def _section_label(pdf: canvas.Canvas, y: float, number: str, title: str, accent=INDIGO) -> None:
    pdf.setFillColor(accent)
    pdf.roundRect(MARGIN + 7 * mm, y - 4 * mm, 16 * mm, 8 * mm, 4 * mm, fill=True, stroke=False)
    _center(pdf, MARGIN + 15 * mm, y - 1.1 * mm, number, 7.2, WHITE, 'Helvetica-Bold')
    _txt(pdf, MARGIN + 28 * mm, y - 1.8 * mm, title, 12.5, INK, 'Helvetica-Bold')


def build_request_pdf(vacation_request) -> ContentFile:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    employee = vacation_request.employee
    reference = f'SOL-{vacation_request.pk:05d}'
    generated_at = timezone.localtime().strftime('%d/%m/%Y · %H:%M')

    _set_doc_info(pdf, f'Solicitud de vacaciones {reference}')
    _request_background(pdf, reference, generated_at)

    x = MARGIN + 7 * mm
    w = PAGE_W - x - MARGIN
    y = PAGE_H - 85 * mm

    _section_label(pdf, y, '01', 'Identificación del trabajador')
    _shadow_card(pdf, x, y - 51 * mm, w, 39 * mm)
    _field_box(pdf, x + 6 * mm, y - 43 * mm, 69 * mm, 25 * mm, 'Trabajador', employee.full_name)
    _field_box(pdf, x + 80 * mm, y - 43 * mm, 35 * mm, 25 * mm, 'DNI/NIE', employee.national_id)
    _field_box(pdf, x + 120 * mm, y - 43 * mm, 43 * mm, 25 * mm, 'Departamento', employee.department)

    y -= 67 * mm
    _section_label(pdf, y, '02', 'Periodo solicitado')
    gap = 8 * mm
    metric_w = (w - 2 * gap) / 3
    _big_metric(pdf, x, y - 44 * mm, metric_w, 'Fecha inicio', vacation_request.start_date.strftime('%d/%m/%Y'))
    _big_metric(pdf, x + metric_w + gap, y - 44 * mm, metric_w, 'Fecha fin', vacation_request.end_date.strftime('%d/%m/%Y'))
    _big_metric(pdf, x + 2 * (metric_w + gap), y - 44 * mm, metric_w, 'Días', f'{vacation_request.requested_days:g}')

    y -= 61 * mm
    _section_label(pdf, y, '03', 'Declaración y observaciones')
    _shadow_card(pdf, x, y - 58 * mm, w, 45 * mm)
    pdf.setFillColor(INDIGO)
    pdf.rect(x, y - 58 * mm, 4 * mm, 45 * mm, fill=True, stroke=False)
    _txt(pdf, x + 10 * mm, y - 25 * mm, 'El trabajador solicita el disfrute del periodo indicado y declara que los datos son correctos.', 9.2, INK, 'Helvetica-Bold')
    _txt(pdf, x + 10 * mm, y - 36 * mm, 'Observaciones', 8, INDIGO, 'Helvetica-Bold')
    _wrapped(pdf, x + 39 * mm, y - 36 * mm, vacation_request.notes or 'Sin observaciones.', 80, 3, 8.6, SLATE)

    y -= 74 * mm
    _section_label(pdf, y, '04', 'Firmas de conformidad')
    _signature_panel(pdf, x, y - 48 * mm, 72 * mm, 'Trabajador/a', 'Firma y fecha')
    _signature_panel(pdf, x + w - 72 * mm, y - 48 * mm, 72 * mm, 'Recepción empresa', 'Sello / firma y fecha')

    _footer(pdf, reference)
    pdf.showPage()
    pdf.save()

    return ContentFile(buffer.getvalue(), name=f'solicitud_vacaciones_{vacation_request.pk}.pdf')


def _decision_background(pdf: canvas.Canvas, reference: str, status_label: str, accent, soft, decided_at: str) -> None:
    pdf.setFillColor(colors.HexColor('#fffaf0'))
    pdf.rect(0, 0, PAGE_W, PAGE_H, fill=True, stroke=False)
    pdf.setStrokeColor(accent)
    pdf.setLineWidth(2.3)
    pdf.roundRect(14 * mm, 14 * mm, PAGE_W - 28 * mm, PAGE_H - 28 * mm, 7 * mm, stroke=True, fill=False)
    pdf.setStrokeColor(colors.HexColor('#e7d8b8'))
    pdf.setLineWidth(0.8)
    pdf.roundRect(19 * mm, 19 * mm, PAGE_W - 38 * mm, PAGE_H - 38 * mm, 4 * mm, stroke=True, fill=False)

    pdf.setFillColor(GRAPHITE)
    pdf.roundRect(28 * mm, PAGE_H - 46 * mm, PAGE_W - 56 * mm, 18 * mm, 9 * mm, fill=True, stroke=False)
    _txt(pdf, 37 * mm, PAGE_H - 38 * mm, 'VACACIONES PRO · DIRECCIÓN', 8, colors.HexColor('#fde68a'), 'Helvetica-Bold')
    _right(pdf, PAGE_W - 37 * mm, PAGE_H - 38 * mm, reference, 8.5, WHITE, 'Helvetica-Bold')

    pdf.setFillColor(soft)
    pdf.roundRect(28 * mm, PAGE_H - 87 * mm, PAGE_W - 56 * mm, 29 * mm, 5 * mm, fill=True, stroke=False)
    _center(pdf, PAGE_W / 2, PAGE_H - 70 * mm, f'RESOLUCIÓN {status_label.upper()}', 22, accent, 'Helvetica-Bold')
    _center(pdf, PAGE_W / 2, PAGE_H - 80 * mm, f'Emitida el {decided_at}', 8.8, SLATE)


def _decision_row(pdf: canvas.Canvas, x: float, y: float, label: str, value: str) -> None:
    _txt(pdf, x, y, label.upper(), 6.8, MUTED, 'Helvetica-Bold')
    _txt(pdf, x + 40 * mm, y, value or '—', 9.2, INK, 'Helvetica-Bold')
    pdf.setStrokeColor(colors.HexColor('#e2e8f0'))
    pdf.setLineWidth(0.6)
    pdf.line(x, y - 4 * mm, PAGE_W - x, y - 4 * mm)


def _seal(pdf: canvas.Canvas, text: str, accent) -> None:
    pdf.saveState()
    pdf.translate(PAGE_W - 53 * mm, 101 * mm)
    pdf.rotate(-12)
    pdf.setStrokeColor(accent)
    pdf.setLineWidth(1.8)
    pdf.circle(0, 0, 19 * mm, stroke=True, fill=False)
    pdf.circle(0, 0, 15 * mm, stroke=True, fill=False)
    _center(pdf, 0, 2 * mm, 'DIRECCIÓN', 7, accent, 'Helvetica-Bold')
    _center(pdf, 0, -5 * mm, text.upper(), 8.5, accent, 'Helvetica-Bold')
    pdf.restoreState()


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
    _decision_background(pdf, reference, status_label, accent, soft, decided_at)
    _seal(pdf, status_label, accent)

    x = 31 * mm
    y = PAGE_H - 106 * mm
    _txt(pdf, x, y, 'Acta formal de resolución', 15, INK, 'Helvetica-Bold')
    _txt(pdf, x, y - 8 * mm, 'La empresa comunica la decisión adoptada sobre la solicitud de vacaciones indicada.', 8.8, SLATE)

    _rounded(pdf, x, y - 63 * mm, PAGE_W - 62 * mm, 42 * mm, WHITE, colors.HexColor('#e2e8f0'), 4 * mm)
    _decision_row(pdf, x + 8 * mm, y - 34 * mm, 'Trabajador', employee.full_name)
    _decision_row(pdf, x + 8 * mm, y - 47 * mm, 'Departamento', employee.department)
    _decision_row(pdf, x + 8 * mm, y - 60 * mm, 'Periodo', f'{request.start_date:%d/%m/%Y} - {request.end_date:%d/%m/%Y} · {request.requested_days:g} días')

    y -= 85 * mm
    _rounded(pdf, x, y - 52 * mm, PAGE_W - 62 * mm, 42 * mm, soft, accent, 5 * mm, 1.1)
    headline = 'La empresa AUTORIZA el periodo solicitado.' if approved else 'La empresa NO AUTORIZA el periodo solicitado.'
    _txt(pdf, x + 9 * mm, y - 24 * mm, 'Resultado de dirección', 8, accent, 'Helvetica-Bold')
    _wrapped(pdf, x + 9 * mm, y - 35 * mm, headline, 82, 2, 13, INK)
    _txt(pdf, x + 9 * mm, y - 48 * mm, 'Observaciones:', 8, accent, 'Helvetica-Bold')
    _wrapped(pdf, x + 38 * mm, y - 48 * mm, decision.company_notes or 'Sin observaciones adicionales por parte de dirección.', 62, 2, 8.5, SLATE)

    y -= 74 * mm
    _txt(pdf, x, y, 'Trazabilidad y firmas', 13, INK, 'Helvetica-Bold')
    _field_box(pdf, x, y - 33 * mm, 70 * mm, 22 * mm, 'Responsable', str(decision.decided_by), accent)
    _field_box(pdf, x + 82 * mm, y - 33 * mm, 58 * mm, 22 * mm, 'Fecha resolución', decided_at, accent)
    _signature_panel(pdf, x, y - 76 * mm, 65 * mm, 'Firma dirección', 'Firma / sello')
    _signature_panel(pdf, PAGE_W - x - 65 * mm, y - 76 * mm, 65 * mm, 'Recibí trabajador/a', 'Firma y fecha')

    _footer(pdf, reference)
    pdf.showPage()
    pdf.save()

    return ContentFile(buffer.getvalue(), name=f'resolucion_vacaciones_{request.pk}.pdf')
