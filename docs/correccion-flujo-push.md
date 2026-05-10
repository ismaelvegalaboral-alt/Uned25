# Corrección flujo push

Esta corrección hace que las nuevas solicitudes notifiquen también a:

- usuarios en grupos RRHH, Dirección y Administrador,
- superusuarios,
- usuarios staff.

También evita que una falta de grupo en el superusuario impida recibir avisos.

## Prueba recomendada

1. Entrar con usuario admin/RRHH.
2. Ir a `/notificaciones/`.
3. Activar notificaciones.
4. Enviar prueba.
5. Crear solicitud con usuario trabajador.
6. Comprobar que llega push de nueva solicitud.
