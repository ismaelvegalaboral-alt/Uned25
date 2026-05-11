# Parte personal diario

Añade una sección para que los trabajadores rellenen el parte personal diario desde la plataforma.

## Flujo

1. El trabajador entra en `Parte personal`.
2. Rellena los campos del parte.
3. La plataforma genera el PDF usando la plantilla oficial.
4. Se guarda el parte.
5. Se envía email automático a administración/RRHH/Dirección.
6. Queda disponible en histórico y admin.

## URLs

- `/partes/`
- `/partes/nuevo/`
- `/partes/<id>/`
- `/partes/<id>/pdf/`

## Variables opcionales

```env
DAILY_REPORT_RECIPIENT_EMAILS=rrhh@empresa.com,direccion@empresa.com
```

Si no se configura, usa `HR_NOTIFICATION_EMAIL`.

## Plantilla PDF

La plantilla se guarda en:

`vacations/static/vacations/pdf_templates/parte_personal_diario_en_blanco.pdf`

## Nota

La primera versión usa firma textual. Más adelante se puede añadir firma táctil desde móvil.
