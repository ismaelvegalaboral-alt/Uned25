# Visibilidad de funciones por usuario

Esta mejora hace que cada trabajador vea únicamente las funciones activadas para su usuario.

## Configuración

En Django Admin entra en:

`Permisos de funciones de plataforma`

Crea una ficha por usuario y marca/desmarca:

- Vacaciones/ausencias.
- Partes personales.
- Albaranes de cliente.
- Faena diaria.
- Órdenes de trabajo.

Si un usuario no tiene ficha de permisos, mantiene acceso completo por defecto.

RRHH, Dirección, Administrador, staff y superusuarios mantienen acceso completo.
