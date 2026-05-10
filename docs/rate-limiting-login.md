# Protección de login / rate limiting

Se añade protección contra intentos repetidos de inicio de sesión.

## Qué hace

- Controla los POST a `/login/`.
- Cuenta intentos fallidos por IP.
- Cuenta intentos fallidos por usuario/email.
- Bloquea temporalmente con HTTP 429 si se superan los intentos permitidos.
- Registra intentos en el admin de Django.

## Valores por defecto

```env
LOGIN_RATE_LIMIT_ATTEMPTS=5
LOGIN_RATE_LIMIT_WINDOW_MINUTES=10
```

Traducción:

- máximo 5 intentos fallidos,
- dentro de 10 minutos,
- si se supera, se bloquea temporalmente.

## Dónde verlo

En Django Admin:

`Intentos de login`

## Nota

Esto protege el login web de la plataforma. SSH ya queda protegido por UFW + fail2ban.
