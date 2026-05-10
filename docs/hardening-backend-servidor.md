# Hardening backend y servidor

Este paquete añade:

- Configuración segura de Django por variables de entorno.
- Auditoría básica de acciones.
- Descarga protegida de justificantes.
- Script de backup local.
- Logging a archivo.
- Documentación de pasos de servidor.

## Variables recomendadas en `.env`

```env
DEBUG=False
ALLOWED_HOSTS=ausencias.kalpae.es,82.223.104.142
CSRF_TRUSTED_ORIGINS=https://ausencias.kalpae.es
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=86400
```

## Backup manual

```bash
bash scripts/backup_kalpae.sh
```

## Cron diario

```bash
crontab -e
```

Añadir:

```cron
15 2 * * * /bin/bash /home/kalpae/ausencias/scripts/backup_kalpae.sh >> /home/kalpae/backups/backup.log 2>&1
```

## Nginx: proteger justificantes

Si tienes una ubicación `/media/`, deja pública solo la parte necesaria y bloquea justificantes:

```nginx
location /media/absence_documents/ {
    deny all;
    return 404;
}

location /media/ {
    alias /home/kalpae/ausencias/media/;
}
```

La app sirve los justificantes desde una vista protegida con login y permisos.
