from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone
from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

try:
    from PIL import Image
except Exception:
    Image = None


PAGE_WIDTH = 841.8898
PAGE_HEIGHT = 595.2756

TEMPLATE_PATH = (
    Path(settings.BASE_DIR)
    / "vacations"
    / "static"
    / "vacations"
    / "pdf_templates"
    / "parte_cliente_kalpae_en_blanco.pdf"
)

BLUE = HexColor("#123581")


def _clean(value):
    return "" if value is None else str(value).strip()


def _fit_size(text, max_width, font="Helvetica", start=11, minimum=8):
    text = _clean(text)
    size = start
    while size > minimum and stringWidth(text, font, size) > max_width:
        size -= 0.25
    return size


def _draw(c, text, x, y, width, size=11, font="Helvetica", align="left"):
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


def _wrap_lines(text, width, font="Helvetica", size=10):
    text = _clean(text)
    if not text:
        return []

    final = []
    for raw in text.replace("\r", "").split("\n"):
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


def _draw_multiline(c, text, x, y, width, max_lines, size=10, leading=16):
    text = _clean(text)
    if not text:
        return

    font = "Helvetica"
    lines = _wrap_lines(text, width, font=font, size=size)

    while len(lines) > max_lines and size > 8:
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


def _cropped_signature_reader(path):
    if Image is None:
        return ImageReader(path)

    img = Image.open(path).convert("RGBA")
    pixels = img.load()
    width, height = img.size

    min_x, min_y = width, height
    max_x, max_y = 0, 0

    # Detecta trazos no blancos/no transparentes.
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            if a > 10 and not (r > 245 and g > 245 and b > 245):
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)

    if max_x <= min_x or max_y <= min_y:
        return ImageReader(path)

    pad = 14
    min_x = max(0, min_x - pad)
    min_y = max(0, min_y - pad)
    max_x = min(width, max_x + pad)
    max_y = min(height, max_y + pad)

    crop = img.crop((min_x, min_y, max_x, max_y)).convert("RGBA")

    # Convierte fondo blanco en transparente para que solo se vea la firma.
    data = []
    for r, g, b, a in crop.getdata():
        if r > 245 and g > 245 and b > 245:
            data.append((255, 255, 255, 0))
        else:
            data.append((r, g, b, a))
    crop.putdata(data)

    out = BytesIO()
    crop.save(out, format="PNG")
    out.seek(0)
    return ImageReader(out)


def _draw_signature(c, report):
    if not report.signature_image:
        return

    try:
        image = _cropped_signature_reader(report.signature_image.path)
    except Exception:
        return

    # Recuadro "Recibí Conforme" inferior derecho.
    # El título del PDF está arriba del recuadro, así que la firma va debajo.
    box_x = 520
    box_y = 18
    box_w = 278
    box_h = 82

    sig_w = 245
    sig_h = 60
    sig_x = box_x + ((box_w - sig_w) / 2)
    sig_y = box_y + 18

    c.drawImage(
        image,
        sig_x,
        sig_y,
        width=sig_w,
        height=sig_h,
        mask="auto",
        preserveAspectRatio=True,
        anchor="c",
    )

    received_by = _clean(getattr(report, "received_by", ""))
    if received_by:
        _draw(c, received_by, box_x + 18, box_y + 6, box_w - 36, size=9.5, align="center")


def build_customer_delivery_note_pdf(report):
    packet = BytesIO()
    c = canvas.Canvas(packet, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))

    day, month, year = _date_parts(getattr(report, "note_date", None))

    # FECHA: sobre la línea superior de fecha.
    _draw(c, day, 492, 526, 58, size=11, align="center")
    _draw(c, month, 585, 526, 105, size=11, align="center")
    _draw(c, year, 735, 526, 42, size=11, align="center")

    # DATOS DEL CLIENTE
    _draw(c, report.customer_name, 116, 451, 380, size=11)
    _draw(c, report.phone, 548, 451, 112, size=11)
    _draw(c, report.tax_id, 710, 451, 110, size=11)

    _draw(c, report.worksite, 96, 422, 360, size=11)
    _draw(c, report.address, 485, 422, 330, size=11)

    # MÁQUINAS: se colocan después de la palabra MÁQUINA, no encima del rótulo.
    _draw(c, report.machine_1, 155, 392, 365, size=10.8)
    _draw(c, report.machine_1_hours, 635, 392, 95, size=10.8, align="center")
    _draw(c, report.machine_2, 155, 363, 365, size=10.8)
    _draw(c, report.machine_2_hours, 635, 363, 95, size=10.8, align="center")

    # CAMIONES
    truck_y = [307, 279, 251, 223, 195]
    for idx, y in enumerate(truck_y, start=1):
        _draw(c, getattr(report, f"truck_{idx}", ""), 150, y, 235, size=10.8)
        _draw(c, getattr(report, f"truck_{idx}_hours", ""), 430, y, 85, size=10.8, align="center")
        _draw(c, getattr(report, f"truck_{idx}_trips", ""), 665, y, 80, size=10.8, align="center")

    # CAJAS INFERIORES
    _draw_multiline(
        c,
        report.work_description,
        68,
        163,
        380,
        max_lines=6,
        size=10,
        leading=15,
    )
    _draw_multiline(
        c,
        report.materials,
        482,
        163,
        305,
        max_lines=6,
        size=10,
        leading=15,
    )
    _draw_multiline(
        c,
        report.observations,
        68,
        73,
        455,
        max_lines=3,
        size=9.5,
        leading=14,
    )

    _draw_signature(c, report)

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

    note_date = getattr(report, "note_date", None)
    date_part = note_date.strftime("%Y%m%d") if note_date else "sin_fecha"
    pk = getattr(report, "pk", None) or "nuevo"
    filename = f"albaran_cliente_{date_part}_{pk}.pdf"

    return filename, ContentFile(output.read())
