from io import BytesIO
from pathlib import Path
import textwrap

from django.conf import settings
from django.core.files.base import ContentFile
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas


TEMPLATE_PATH = Path(settings.BASE_DIR) / 'vacations' / 'static' / 'vacations' / 'pdf_templates' / 'parte_personal_diario_en_blanco.pdf'


def _draw_text(c, x, y, text, size=10, max_width_chars=None, line_gap=4):
    if text is None:
        text = ''
    text = str(text)
    c.setFont('Helvetica', size)
    if max_width_chars:
        lines = textwrap.wrap(text, width=max_width_chars) or ['']
        for i, line in enumerate(lines):
            c.drawString(x, y - (i * (size + line_gap)), line)
    else:
        c.drawString(x, y, text)


def _date_parts(date_value):
    if not date_value:
        return '', '', ''
    months = [
        'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
        'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
    ]
    return f'{date_value.day:02d}', months[date_value.month - 1], str(date_value.year)[-2:]


def build_daily_work_report_pdf(report):
    packet = BytesIO()
    c = canvas.Canvas(packet, pagesize=(595.2756, 841.8898))

    day, month, year = _date_parts(report.report_date)

    # Coordenadas en puntos PDF para la plantilla A4 aportada.
    # Si tras la prueba visual quieres mover algún campo, se ajusta aquí.
    _draw_text(c, 108, 704, day, 10)
    _draw_text(c, 220, 704, month, 10)
    _draw_text(c, 345, 704, year, 10)

    _draw_text(c, 150, 676, report.machine_number, 10)
    _draw_text(c, 365, 676, report.truck_number, 10)
    _draw_text(c, 88, 653, report.other_equipment, 10, 85)

    _draw_text(c, 108, 624, report.client_1, 9)
    _draw_text(c, 350, 624, report.client_2, 9)
    _draw_text(c, 108, 601, report.client_3, 9)
    _draw_text(c, 350, 601, report.client_4, 9)

    _draw_text(c, 93, 579, report.worksite_1, 9)
    _draw_text(c, 335, 579, report.worksite_2, 9)
    _draw_text(c, 93, 556, report.worksite_3, 9)
    _draw_text(c, 335, 556, report.worksite_4, 9)

    _draw_text(c, 85, 535, report.hours, 9)
    _draw_text(c, 335, 535, report.other_notes, 9)
    _draw_text(c, 82, 512, report.trips, 9)

    _draw_text(c, 205, 486, report.supplied_material, 9, 75)
    _draw_text(c, 190, 460, report.work_performed, 9, 86, line_gap=5)

    _draw_text(c, 360, 88, report.signature_name or report.worker_name, 10)
    _draw_text(c, 190, 42, report.worker_name, 10)

    c.save()
    packet.seek(0)

    overlay_pdf = PdfReader(packet)
    template_pdf = PdfReader(str(TEMPLATE_PATH))
    writer = PdfWriter()

    page = template_pdf.pages[0]
    page.merge_page(overlay_pdf.pages[0])
    writer.add_page(page)

    output = BytesIO()
    writer.write(output)
    output.seek(0)

    pk = report.pk or 'nuevo'
    filename = f'parte_personal_{report.employee_id}_{report.report_date:%Y%m%d}_{pk}.pdf'
    return filename, ContentFile(output.read())
