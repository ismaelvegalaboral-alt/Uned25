# Resolución de conflictos del PR de vacaciones

El PR antiguo puede seguir mostrando conflictos si se abrió antes de que `main` incorporase la primera versión de la plataforma Django. En ese caso GitHub compara dos historiales distintos que contienen los mismos archivos añadidos y marca conflictos en `README.md`, `vacations/pdf.py`, `app.css`, plantillas, tests, URLs y vistas.

Para evitar esos conflictos, el PR correcto debe partir de la versión de `main` que ya contiene la plataforma base y aplicar únicamente los cambios incrementales posteriores:

1. Mejora profesional del diseño de PDFs en `vacations/pdf.py`.
2. Calendario mensual de vacaciones con detección de solapes.
3. Aviso al crear solicitudes que coinciden con otras solicitudes activas.

También se ha comprobado que el árbol de trabajo local no contiene marcadores de conflicto estándar de Git.
