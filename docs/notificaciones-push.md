# Notificaciones push PWA

La plataforma queda preparada para enviar notificaciones push web.

## Notificaciones iniciales

- Nueva solicitud → RRHH, Dirección y Administrador.
- Solicitud aprobada/denegada → trabajador vinculado.
- Notificación de prueba → usuario actual.

## Activación

Cada usuario debe entrar en:

`https://ausencias.kalpae.es/notificaciones/`

Y pulsar:

`Activar notificaciones`

Después puede usar:

`Enviar notificación de prueba`

## Servidor

Generar claves:

```bash
python manage.py generate_vapid_keys
```

Copiar las líneas que imprime al archivo `.env`.

Después:

```bash
sudo systemctl restart kalpae-ausencias
```
