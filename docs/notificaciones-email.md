# Notificaciones automáticas por email

Esta actualización envía un correo automático a administración cada vez que se crea una nueva solicitud.

## Seguridad

No guardes la contraseña de Gmail en `settings.py`.
No subas el archivo `.env` real a GitHub.
Si una contraseña de aplicación se ha compartido por error, revócala y genera una nueva.

## Configuración en el servidor

Crear `/home/kalpae/ausencias/.env` con:

```env
SITE_URL=https://ausencias.kalpae.es
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=ivegamkalpae@gmail.com
EMAIL_HOST_PASSWORD=contraseña-de-aplicación-nueva
DEFAULT_FROM_EMAIL=Kalpae Gestión de Ausencias <ivegamkalpae@gmail.com>
HR_NOTIFICATION_EMAIL=ivegamkalpae@gmail.com
```

Después:

```bash
pip install -r requirements.txt
sudo systemctl restart kalpae-ausencias
```
