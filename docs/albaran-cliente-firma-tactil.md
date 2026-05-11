# Albarán de cliente con firma táctil

Añade una sección para generar albaranes de cliente desde la plataforma.

## Flujo

1. El trabajador entra en `Albarán de cliente`.
2. Rellena cliente, teléfono, CIF, obra, dirección, máquinas, camiones, trabajos, materiales y observaciones.
3. El cliente firma en pantalla en el bloque `Recibí conforme`.
4. Se genera un PDF usando la plantilla oficial.
5. Se guarda el albarán y se envía por email a administración.

## URLs

- `/albaranes/`
- `/albaranes/nuevo/`
- `/albaranes/<id>/`
- `/albaranes/<id>/pdf/`

## Variable opcional

```env
CUSTOMER_DELIVERY_NOTE_RECIPIENT_EMAILS=rrhh@empresa.com,direccion@empresa.com
```

Si no se configura, usa `HR_NOTIFICATION_EMAIL`.

## Plantilla PDF

`vacations/static/vacations/pdf_templates/parte_cliente_kalpae_en_blanco.pdf`
