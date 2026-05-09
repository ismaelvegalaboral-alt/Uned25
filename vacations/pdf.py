from __future__ import annotations

from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    Flowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

try:
    from .services import evaluate_request
except Exception:  # pragma: no cover - fallback for older deployments without services.py
    evaluate_request = None

PAGE_W, PAGE_H = A4
MARGIN_X = 16 * mm
TOP_MARGIN = 31 * mm
BOTTOM_MARGIN = 12 * mm
CONTENT_W = PAGE_W - (2 * MARGIN_X)

NAVY = colors.HexColor('#1f2a55')
GOLD = colors.HexColor('#f7ad00')
INK = colors.HexColor('#0f172a')
SLATE = colors.HexColor('#475569')
MUTED = colors.HexColor('#94a3b8')
LINE = colors.HexColor('#d9e2ef')
PAPER = colors.HexColor('#f8fafc')
SOFT_BLUE = colors.HexColor('#eff6ff')
BLUE = colors.HexColor('#1d4ed8')
GREEN = colors.HexColor('#15803d')
GREEN_SOFT = colors.HexColor('#ecfdf3')
RED = colors.HexColor('#b91c1c')
RED_SOFT = colors.HexColor('#fef2f2')
AMBER = colors.HexColor('#b45309')
AMBER_SOFT = colors.HexColor('#fff7ed')
WHITE = colors.white

_styles = getSampleStyleSheet()

TITLE = ParagraphStyle(
    'KalpaeTitle',
    parent=_styles['Title'],
    fontName='Helvetica-Bold',
    fontSize=18,
    leading=21,
    textColor=INK,
    alignment=TA_LEFT,
    spaceAfter=5,
)
SUBTITLE = ParagraphStyle(
    'KalpaeSubtitle',
    parent=_styles['BodyText'],
    fontName='Helvetica',
    fontSize=8.5,
    leading=11,
    textColor=SLATE,
)
SECTION_TITLE = ParagraphStyle(
    'KalpaeSectionTitle',
    parent=_styles['Heading2'],
    fontName='Helvetica-Bold',
    fontSize=10.5,
    leading=12.5,
    textColor=NAVY,
    spaceBefore=2,
    spaceAfter=5,
)
LABEL = ParagraphStyle(
    'KalpaeLabel',
    parent=_styles['BodyText'],
    fontName='Helvetica-Bold',
    fontSize=6.8,
    leading=8,
    textColor=MUTED,
)
VALUE = ParagraphStyle(
    'KalpaeValue',
    parent=_styles['BodyText'],
    fontName='Helvetica-Bold',
    fontSize=9.3,
    leading=12,
    textColor=INK,
)
VALUE_NORMAL = ParagraphStyle(
    'KalpaeValueNormal',
    parent=_styles['BodyText'],
    fontName='Helvetica',
    fontSize=9,
    leading=12,
    textColor=INK,
)
SMALL = ParagraphStyle(
    'KalpaeSmall',
    parent=_styles['BodyText'],
    fontName='Helvetica',
    fontSize=7.2,
    leading=9,
    textColor=SLATE,
)
SMALL_RIGHT = ParagraphStyle(
    'KalpaeSmallRight',
    parent=SMALL,
    alignment=TA_RIGHT,
)
CENTER_BIG = ParagraphStyle(
    'KalpaeCenterBig',
    parent=_styles['Heading1'],
    fontName='Helvetica-Bold',
    fontSize=17,
    leading=20,
    textColor=NAVY,
    alignment=TA_CENTER,
)
CENTER_TEXT = ParagraphStyle(
    'KalpaeCenterText',
    parent=VALUE_NORMAL,
    alignment=TA_CENTER,
)


def _e(value) -> str:
    return escape(str(value if value not in [None, ''] else '—'))


def _p(value, style=VALUE_NORMAL) -> Paragraph:
    return Paragraph(_e(value), style)


def _date(value) -> str:
    return value.strftime('%d/%m/%Y') if value else '—'


def _number(value) -> str:
    try:
        return f'{value:g}'
    except Exception:
        return str(value or '—')


def _logo_path() -> Path:
    return Path(settings.MEDIA_ROOT) / 'branding' / 'kalpae-logo.png'


def _logo_size(path: Path, width: float) -> tuple[float, float]:
    image = ImageReader(str(path))
    img_w, img_h = image.getSize()
    return width, width * img_h / img_w


def _draw_logo_fallback(canvas, x: float, y: float) -> None:
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.setFont('Helvetica-Bold', 25)
    canvas.drawString(x, y + 8 * mm, 'KALPAE')
    canvas.setFillColor(GOLD)
    canvas.setFont('Helvetica-Bold', 9)
    canvas.drawString(x, y + 3 * mm, 'IBERICA')
    canvas.restoreState()


def _draw_header(canvas, doc, reference: str, generated_at: str, title: str | None = None) -> None:
    canvas.saveState()
    canvas.setFillColor(WHITE)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=True, stroke=False)

    logo = _logo_path()
    logo_w = 72 * mm
    logo_y = PAGE_H - 22 * mm
    if logo.exists():
        w, h = _logo_size(logo, logo_w)
        canvas.drawImage(str(logo), MARGIN_X, logo_y, width=w, height=h, preserveAspectRatio=True, mask='auto')
    else:
        _draw_logo_fallback(canvas, MARGIN_X, logo_y)

    canvas.setFont('Helvetica-Bold', 8.8)
    canvas.setFillColor(NAVY)
    canvas.drawRightString(PAGE_W - MARGIN_X, PAGE_H - 17 * mm, reference)
    canvas.setFont('Helvetica', 7.2)
    canvas.setFillColor(SLATE)
    canvas.drawRightString(PAGE_W - MARGIN_X, PAGE_H - 23 * mm, generated_at)

    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.6)
    canvas.line(MARGIN_X, PAGE_H - 27 * mm, PAGE_W - MARGIN_X, PAGE_H - 27 * mm)

    canvas.setFont('Helvetica', 6.8)
    canvas.setFillColor(MUTED)
    canvas.drawString(MARGIN_X, 10 * mm, 'Documento generado automáticamente y archivado en Kalpae Gestión de Ausencias.')
    canvas.setFont('Helvetica-Bold', 6.8)
    canvas.setFillColor(SLATE)
    canvas.drawRightString(PAGE_W - MARGIN_X, 10 * mm, reference)
    canvas.restoreState()


def _doc(buffer: BytesIO, reference: str, generated_at: str) -> SimpleDocTemplate:
    return SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=MARGIN_X,
        leftMargin=MARGIN_X,
        topMargin=TOP_MARGIN,
        bottomMargin=BOTTOM_MARGIN,
        title=reference,
        author='Kalpae Ibérica',
    )


def _build_doc(buffer: BytesIO, story: list, reference: str, generated_at: str) -> None:
    doc = _doc(buffer, reference, generated_at)
    doc.build(
        story,
        onFirstPage=lambda canvas, d: _draw_header(canvas, d, reference, generated_at),
        onLaterPages=lambda canvas, d: _draw_header(canvas, d, reference, generated_at),
    )


def _status_chip(text: str, color=BLUE, fill=SOFT_BLUE) -> Table:
    table = Table([[Paragraph(f'<b>{_e(text).upper()}</b>', CENTER_TEXT)]], colWidths=[CONTENT_W])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), fill),
        ('BOX', (0, 0), (-1, -1), 0.7, colors.HexColor('#cfe0f7')),
        ('TEXTCOLOR', (0, 0), (-1, -1), color),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    return table


def _field(label: str, value: str) -> list:
    return [Paragraph(_e(label).upper(), LABEL), Paragraph(_e(value), VALUE)]


def _info_grid(items: list[tuple[str, str]], columns: int = 2) -> Table:
    rows = []
    row = []
    for label, value in items:
        row.append(_field(label, value))
        if len(row) == columns:
            rows.append(row)
            row = []
    if row:
        while len(row) < columns:
            row.append([Paragraph('', LABEL), Paragraph('', VALUE)])
        rows.append(row)

    col_width = CONTENT_W / columns
    table = Table(rows, colWidths=[col_width] * columns, hAlign='LEFT')
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), WHITE),
        ('BOX', (0, 0), (-1, -1), 0.7, LINE),
        ('INNERGRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#edf2f7')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    return table


def _section(title: str, body, accent=NAVY, keep=True):
    flowables = [Paragraph(_e(title), SECTION_TITLE)]
    if isinstance(body, list):
        flowables.extend(body)
    else:
        flowables.append(body)
    flowables.append(Spacer(1, 3.5 * mm))
    return KeepTogether(flowables) if keep else flowables


def _paragraph_box(text: str, fill=WHITE, stroke=LINE, style=VALUE_NORMAL) -> Table:
    table = Table([[Paragraph(_e(text), style)]], colWidths=[CONTENT_W])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), fill),
        ('BOX', (0, 0), (-1, -1), 0.7, stroke),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    return table


def _signature_table(left_title: str, right_title: str) -> Table:
    line = Paragraph('____________________________________', CENTER_TEXT)
    small = Paragraph('Firma y fecha', ParagraphStyle('SigSmall', parent=SMALL, alignment=TA_CENTER))
    left = [Spacer(1, 4 * mm), line, Paragraph(f'<b>{_e(left_title)}</b>', CENTER_TEXT), small]
    right = [Spacer(1, 4 * mm), line, Paragraph(f'<b>{_e(right_title)}</b>', CENTER_TEXT), small]
    gap = 10 * mm
    col = (CONTENT_W - gap) / 2
    table = Table([[left, '', right]], colWidths=[col, gap, col])
    table.setStyle(TableStyle([
        ('BOX', (0, 0), (0, 0), 0.7, LINE),
        ('BOX', (2, 0), (2, 0), 0.7, LINE),
        ('BACKGROUND', (0, 0), (0, 0), WHITE),
        ('BACKGROUND', (2, 0), (2, 0), WHITE),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    return table


class SeverityBar(Flowable):
    def __init__(self, text: str, severity='ok'):
        super().__init__()
        self.text = text
        self.severity = severity
        self.width = CONTENT_W
        self.height = 10 * mm

    def draw(self):
        fill = {'critical': RED_SOFT, 'warning': AMBER_SOFT, 'ok': GREEN_SOFT}.get(self.severity, SOFT_BLUE)
        stroke = {'critical': RED, 'warning': AMBER, 'ok': GREEN}.get(self.severity, BLUE)
        self.canv.setFillColor(fill)
        self.canv.setStrokeColor(stroke)
        self.canv.setLineWidth(0.7)
        self.canv.roundRect(0, 0, self.width, self.height, 4 * mm, fill=1, stroke=1)
        self.canv.setFillColor(stroke)
        self.canv.setFont('Helvetica-Bold', 8.5)
        self.canv.drawCentredString(self.width / 2, 3.2 * mm, self.text.upper())


def _empty_review():
    class EmptyReview:
        flags = []
        severity = 'ok'
        label = 'Sin incidencias aparentes'
        business_days = '—'
        notice_days = '—'
        overlap_count = 0
        approved_overlap_count = 0
        already_committed_days = '—'
        remaining_after_request = '—'
        has_flags = False
        has_blocking_flags = False
    return EmptyReview()


def _review_for(vacation_request):
    if evaluate_request is None:
        return _empty_review()
    try:
        return evaluate_request(vacation_request)
    except Exception:
        return _empty_review()


def _review_flowables(vacation_request) -> list:
    review = _review_for(vacation_request)
    rows = [
        ('Días laborables del periodo', _number(review.business_days)),
        ('Preaviso', f'{_number(review.notice_days)} día(s)'),
        ('Solapes departamento', f'{_number(review.overlap_count)} activo(s), {_number(review.approved_overlap_count)} aprobado(s)'),
        ('Saldo posterior estimado', f'{_number(review.remaining_after_request)} día(s)'),
    ]
    flow = [SeverityBar(f'Revisión RRHH - {review.label}', review.severity), Spacer(1, 4 * mm), _info_grid(rows, columns=2)]
    if review.flags:
        flag_rows = []
        for flag in review.flags[:6]:
            flag_rows.append([
                Paragraph(f'<b>{_e(flag.title)}</b><br/><font color="#475569">{_e(flag.detail)}</font>', VALUE_NORMAL)
            ])
        table = Table(flag_rows, colWidths=[CONTENT_W])
        table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.7, colors.HexColor('#fed7aa')),
            ('INNERGRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#ffedd5')),
            ('BACKGROUND', (0, 0), (-1, -1), AMBER_SOFT if review.severity != 'critical' else RED_SOFT),
            ('TOPPADDING', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
            ('LEFTPADDING', (0, 0), (-1, -1), 9),
            ('RIGHTPADDING', (0, 0), (-1, -1), 9),
        ]))
        flow.extend([Spacer(1, 3 * mm), table])
    return flow


def _title_block(title: str, subtitle: str) -> list:
    return [Paragraph(_e(title), TITLE), Paragraph(_e(subtitle), SUBTITLE), Spacer(1, 2.5 * mm)]


def build_request_pdf(vacation_request) -> ContentFile:
    buffer = BytesIO()
    employee = vacation_request.employee
    reference = f'SOL-{vacation_request.pk:05d}'
    generated_at = timezone.localtime().strftime('%d/%m/%Y - %H:%M')

    story = []
    story.extend(_title_block(
        'Solicitud de vacaciones',
        'Documento interno para validación, firma y archivo en Recursos Humanos.',
    ))
    story.append(_status_chip('Pendiente de firma', BLUE, SOFT_BLUE))
    story.append(Spacer(1, 3.5 * mm))

    story.append(_section('1. Datos del trabajador', _info_grid([
        ('Trabajador/a', employee.full_name),
        ('DNI/NIE', employee.national_id),
        ('Departamento', employee.department),
        ('Puesto', employee.position),
        ('Email', employee.email),
        ('Días anuales', _number(employee.annual_days)),
    ], columns=3)))

    story.append(_section('2. Periodo solicitado', _info_grid([
        ('Fecha de inicio', _date(vacation_request.start_date)),
        ('Fecha de fin', _date(vacation_request.end_date)),
        ('Días solicitados', _number(vacation_request.requested_days)),
    ], columns=3)))

    story.extend(_section('3. Revisión preventiva RRHH', _review_flowables(vacation_request), keep=False))

    story.append(_section(
        '4. Observaciones del trabajador',
        _paragraph_box(vacation_request.notes or 'Sin observaciones.', WHITE, LINE),
    ))

    story.append(_section('5. Firmas', _signature_table('Trabajador/a', 'Recepción empresa')))

    _build_doc(buffer, story, reference, generated_at)
    return ContentFile(buffer.getvalue(), name=f'solicitud_vacaciones_{vacation_request.pk}.pdf')


def _decision_label(decision) -> tuple[str, bool]:
    approved = decision.decision == decision.Decision.APPROVED
    label = decision.get_decision_display() if hasattr(decision, 'get_decision_display') else ('Aprobada' if approved else 'Denegada')
    return label, approved


def build_decision_pdf(decision) -> ContentFile:
    buffer = BytesIO()
    request = decision.request
    employee = request.employee
    label, approved = _decision_label(decision)
    reference = f'RES-{request.pk:05d}'
    generated_at = timezone.localtime(decision.decided_at).strftime('%d/%m/%Y - %H:%M')
    accent = GREEN if approved else RED
    fill = GREEN_SOFT if approved else RED_SOFT

    story = []
    story.extend(_title_block(
        'Resolución de solicitud de vacaciones',
        'Comunicación formal de la decisión de la empresa tras la revision de la solicitud.',
    ))
    story.append(_status_chip(f'Resolución {label}', accent, fill))
    story.append(Spacer(1, 3.5 * mm))

    story.append(_section('1. Solicitud evaluada', _info_grid([
        ('Trabajador/a', employee.full_name),
        ('DNI/NIE', employee.national_id),
        ('Departamento', employee.department),
        ('Periodo', f'{_date(request.start_date)} - {_date(request.end_date)}'),
        ('Días solicitados', _number(request.requested_days)),
        ('Estado final', label),
    ], columns=3)))

    headline = 'La empresa autoriza el disfrute del periodo solicitado.' if approved else 'La empresa no autoriza el disfrute del periodo solicitado.'
    decision_body = [
        _paragraph_box(headline, fill, colors.HexColor('#d8e2ef'), ParagraphStyle('DecisionHeadline', parent=VALUE, fontSize=11, leading=15)),
        Spacer(1, 3 * mm),
        _paragraph_box(f'Observaciones de dirección: {decision.company_notes or "Sin observaciones adicionales."}', WHITE, LINE),
    ]
    story.extend(_section('2. Resultado de dirección', decision_body, keep=False))

    story.extend(_section('3. Control preventivo RRHH', _review_flowables(request), keep=False))

    story.append(_section('4. Trazabilidad', _info_grid([
        ('Responsable', str(decision.decided_by)),
        ('Fecha de resolución', generated_at),
    ], columns=2)))

    story.append(_section('5. Firmas', _signature_table('Firma dirección', 'Recibí trabajador/a')))

    _build_doc(buffer, story, reference, generated_at)
    return ContentFile(buffer.getvalue(), name=f'resolucion_vacaciones_{request.pk}.pdf')
