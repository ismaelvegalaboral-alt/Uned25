# Exportación Excel de faena con plantilla oficial

Esta mejora añade exportación `.xlsx` usando la plantilla real de faena diaria.

## Qué hace

- Usa `plantilla_faena.xlsx` como base.
- Mantiene colores, anchuras, bordes y estructura de la plantilla.
- Rellena:
  - día de la semana
  - día
  - mes
  - año
  - bloques de cliente/obra
  - máquinas/camiones
  - trabajadores
  - horas/viajes/notas
  - estados de disponibilidad en la zona derecha

## URL

- `/faena/<id>/excel/`

## Dependencia

Añade `openpyxl` a `requirements.txt`.
