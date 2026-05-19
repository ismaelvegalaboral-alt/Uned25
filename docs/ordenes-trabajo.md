# Órdenes de trabajo

Primera versión del módulo de órdenes de trabajo.

## Qué permite

- Crear una orden ligada al usuario que ha iniciado sesión.
- Guardar automáticamente el nombre del trabajador.
- Indicar vehículo o máquina.
- Seleccionar mantenimiento o reparación.
- Describir la tarea realizada.
- Añadir horas por día.
- Subir fotos o PDF de albaranes, tickets o facturas.
- RRHH/Dirección/Admin pueden revisar todas las órdenes.
- Los trabajadores solo ven sus propias órdenes.

## URLs

- `/ordenes-trabajo/`
- `/ordenes-trabajo/nueva/`
- `/ordenes-trabajo/<id>/`
- `/ordenes-trabajo/<id>/horas/`
- `/ordenes-trabajo/<id>/albaran/`
- `/ordenes-trabajo/<id>/cerrar/`

## Permisos por función

Se añade el modelo `PlatformFeaturePermission` para que desde Django Admin se puedan activar o desactivar funciones por usuario:

- Vacaciones/ausencias.
- Partes personales.
- Albaranes de cliente.
- Faena diaria.
- Órdenes de trabajo.

Si un usuario no tiene ficha de permisos creada, mantiene acceso por defecto. Para restringirlo, se crea su registro de permisos en Admin y se desmarcan las funciones que no debe usar.
