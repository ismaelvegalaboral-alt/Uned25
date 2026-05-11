from io import BytesIO
from pathlib import Path
import textwrap

from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone
from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import HexColor
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


PAGE_WIDTH = 595.2756
PAGE_HEIGHT = 841.8898

TEMPLATE_PATH = (
    Path(settings.BASE_DIR)
    / "vacations"
    / "static"
    / "vacations"
    / "pdf_templates"
    / "parte_personal_diario_en_blanco.pdf"
)

BLUE = HexColor("#173a8a")
SIGN_FILL = HexColor("#eef3ff")
SIGN_BORDER = HexColor("#91a8dc")


def _clean(value):
    return "" if value is None else str(value).strip()


def _fit_size(text, max_width, font="Helvetica", start=9, minimum=6.5):
    text = _clean(text)
    size = start
    while size > minimum and stringWidth(text, font, size) > max_width:
        size -= 0.25
    return size


def _draw(c, text, x, y, width, size=9, font="Helvetica", align="left"):
    text = _clean(text)
    if not text:
        return

    size = _fit_size(text, width, font=font, start=size)
    c.setFillColor(BLUE)
    c.setFont(font, size)

    tw = stringWidth(text, font, size)

    if align == "center":
        x = x + ((width - tw) / 2)
    elif align == "right":
        x = x + width - tw

    c.drawString(x, y, text)


def _wrap_lines(text, width, font="Helvetica", size=8.5):
    text = _clean(text)
    if not text:
        return []

    raw_lines = text.replace("\r", "").split("\n")
    final = []

    for raw in raw_lines:
        words = raw.split()
        if not words:
            final.append("")
            continue

        current = words[0]
        for word in words[1:]:
            candidate = f"{current} {word}"
            if stringWidth(candidate, font, size) <= width:
                current = candidate
            else:
                final.append(current)
                current = word
        final.append(current)

    return final


def _draw_multiline(c, text, x, y, width, max_lines, size=8.5, leading=18):
    text = _clean(text)
    if not text:
        return

    font = "Helvetica"
    lines = _wrap_lines(text, width, font=font, size=size)

    while len(lines) > max_lines and size > 6.8:
        size -= 0.25
        lines = _wrap_lines(text, width, font=font, size=size)

    if len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while last and stringWidth(last + "...", font, size) > width:
            last = last[:-1]
        lines[-1] = last + "..."

    c.setFillColor(BLUE)
    c.setFont(font, size)

    for i, line in enumerate(lines):
        c.drawString(x, y - (i * leading), line)


def _date_parts(value):
    if not value:
        value = timezone.localdate()

    months = [
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
    ]

    return f"{value.day:02d}", months[value.month - 1], str(value.year)[-2:]


def _employee_name(report):
    if getattr(report, "worker_name", ""):
        return _clean(report.worker_name)

    employee = getattr(report, "employee", None)
    if employee:
        full_name = getattr(employee, "full_name", "")
        if callable(full_name):
            full_name = full_name()
        if full_name:
            return _clean(full_name)

        first = _clean(getattr(employee, "first_name", ""))
        last = _clean(getattr(employee, "last_name", ""))
        return f"{first} {last}".strip()

    return ""


def _draw_signature(c, worker_name, created_at=None):
    worker_name = _clean(worker_name)
    created_at = created_at or timezone.now()

    try:
        created_at = timezone.localtime(created_at)
    except Exception:
        pass

    stamp = created_at.strftime("%d/%m/%Y %H:%M")

    # Caja más pequeña y colocada debajo del texto FIRMA.
    x = 322
    y = 84
    w = 155
    h = 30

    c.setFillColor(SIGN_FILL)
    c.setStrokeColor(SIGN_BORDER)
    c.roundRect(x, y, w, h, 5, fill=1, stroke=1)

    c.setFillColor(BLUE)
    c.setFont("Helvetica-Bold", 6.6)
    c.drawCentredString(x + w / 2, y + 19, "FIRMADO ELECTRÓNICAMENTE")

    c.setFont("Helvetica", 6.4)
    c.drawCentredString(x + w / 2, y + 10, worker_name[:40])
    c.drawCentredString(x + w / 2, y + 2.5, stamp)


def _build_pdf(report):
    packet = BytesIO()
    c = canvas.Canvas(packet, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))

    day, month, year = _date_parts(getattr(report, "report_date", None))
    worker_name = _employee_name(report)

    # FECHA: bajada para que caiga en la línea correcta.
    _draw(c, day, 104, 704, 32, size=8.8, align="center")
    _draw(c, month, 185, 704, 88, size=8.8, align="center")
    _draw(c, year, 331, 704, 30, size=8.8, align="center")

    # CABECERA
    _draw(c, getattr(report, "machine_number", ""), 148, 674, 115, size=8.6, align="center")
    _draw(c, getattr(report, "truck_number", ""), 386, 674, 160, size=8.6, align="center")
    _draw(c, getattr(report, "other_equipment", ""), 116, 646, 430, size=8.4)

    # CLIENTES
    _draw(c, getattr(report, "client_1", ""), 113, 617, 160, size=8.4)
    _draw(c, getattr(report, "client_2", ""), 354, 617, 175, size=8.4)
    _draw(c, getattr(report, "client_3", ""), 113, 587, 160, size=8.4)
    _draw(c, getattr(report, "client_4", ""), 354, 587, 175, size=8.4)

    # OBRAS
    _draw(c, getattr(report, "worksite_1", ""), 103, 556, 170, size=8.4)
    _draw(c, getattr(report, "worksite_2", ""), 344, 556, 185, size=8.4)
    _draw(c, getattr(report, "worksite_3", ""), 103, 526, 170, size=8.4)
    _draw(c, getattr(report, "worksite_4", ""), 344, 526, 185, size=8.4)

    # HORAS / OTROS / VIAJES
    _draw(c, getattr(report, "hours", ""), 101, 496, 170, size=8.4)
    _draw(c, getattr(report, "other_notes", ""), 344, 496, 185, size=8.4)
    _draw(c, getattr(report, "trips", ""), 101, 466, 170, size=8.4)

    # MATERIAL SUMINISTRADO
    _draw_multiline(
        c,
        getattr(report, "supplied_material", ""),
        222,
        437,
        325,
        max_lines=2,
        size=8.2,
        leading=14,
    )

    # TRABAJOS REALIZADOS
    _draw_multiline(
        c,
        getattr(report, "work_performed", ""),
        66,
        407,
        485,
        max_lines=12,
        size=8.1,
        leading=19,
    )

    # FIRMA Y NOMBRE
    _draw_signature(c, worker_name, getattr(report, "created_at", None))

    # Nombre del trabajador en su línea inferior, más ajustado.
    _draw(c, worker_name, 198, 45, 340, size=8.2)

    c.save()
    packet.seek(0)

    template_reader = PdfReader(str(TEMPLATE_PATH))
    overlay_reader = PdfReader(packet)

    page = template_reader.pages[0]
    page.merge_page(overlay_reader.pages[0])

    output = BytesIO()
    writer = PdfWriter()
    writer.add_page(page)
    writer.write(output)
    output.seek(0)

    return output


def build_daily_work_report_pdf(report):
    pdf_io = _build_pdf(report)

    report_date = getattr(report, "report_date", None)
    date_part = report_date.strftime("%Y%m%d") if report_date else "sin_fecha"
    employee_id = getattr(report, "employee_id", "empleado")
    pk = getattr(report, "pk", None) or "nuevo"

    filename = f"parte_personal_{employee_id}_{date_part}_{pk}.pdf"
    return filename, ContentFile(pdf_io.read())
