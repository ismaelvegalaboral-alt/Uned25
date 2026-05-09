# PDF v2 - Kalpae Iberica

Sustituye `vacations/pdf.py` por esta version y copia el logo exacto a:

```bash
media/branding/kalpae-logo.png
```

La nueva plantilla usa ReportLab Platypus en vez de coordenadas manuales para que los bloques fluyan y salten de pagina si el texto es largo. Esto evita que se pisen secciones, firmas u observaciones.

## Cambios principales

- Logo real de Kalpae Iberica desde `media/branding/kalpae-logo.png`.
- Solicitud y resolucion con estructura limpia en secciones.
- Tablas automaticas con wrapping de texto.
- Bloques de decision y revision RRHH sin solaparse.
- Firmas colocadas como bloque independiente.
- Si el contenido crece, el PDF pagina automaticamente.

## Prueba

```bash
python manage.py test
python manage.py runserver
```

Luego descarga de nuevo una solicitud y una resolucion desde la app.
