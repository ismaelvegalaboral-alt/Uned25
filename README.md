# Vacaciones Pro

Plataforma Django para cuadrar vacaciones de empresa con login, panel moderno, fichas de trabajadores, histórico de solicitudes, calendario de solapes, administración y PDFs integrados.

## Funcionalidades

- Login con el sistema de autenticación de Django.
- Panel con métricas de trabajadores, pendientes, aprobadas y días gestionados.
- Fichas de trabajador con departamento, puesto, email, DNI/NIE y días anuales.
- Solicitud de vacaciones con validación de fechas y generación automática de PDF para firma del trabajador.
- Calendario mensual para ver de un vistazo quién está de vacaciones y qué días tienen solapes.
- Aviso automático al crear una solicitud si ya hay otras solicitudes activas en las mismas fechas.
- Histórico filtrable por estado.
- Resolución por dirección con PDF llamativo de decisión aprobada o denegada.
- Admin de Django para gestión avanzada.
- Documentos guardados en `media/vacation_documents/`; la carpeta queda versionada para poder subir a GitHub PDFs/documentos que quieras conservar en el repositorio. Los botones de descarga regeneran el PDF con la plantilla profesional vigente para evitar servir diseños antiguos en caché.

## Puesta en marcha

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Después entra en `http://127.0.0.1:8000/` e inicia sesión con el superusuario.

## Flujo recomendado

1. Crear fichas en **Fichas > Nueva ficha**.
2. Registrar una solicitud en **Nueva solicitud**; la plataforma genera el PDF de solicitud para firma.
3. Revisar **Calendario** para comprobar visualmente si el periodo coincide con otros trabajadores.
4. Revisar la solicitud en dirección y pulsar **Resolver solicitud**.
5. Descargar el PDF de solicitud o resolución desde el detalle; cada descarga reconstruye el documento y actualiza el archivo archivado en `media/vacation_documents/`. Si quieres que esos PDFs suban a GitHub, añádelos con `git add media/vacation_documents/*.pdf` antes de hacer commit.

## Notas

El proyecto conserva `definitiva9.py` como herramienta previa del repositorio, pero la nueva plataforma de vacaciones se ejecuta mediante Django con `manage.py`.
