# Ajuste del rate limiting de login

El bloqueo queda ajustado para no bloquear a todos los usuarios por unos pocos fallos.

## Nuevo criterio

- 5 fallos de la misma IP contra el mismo usuario en 10 minutos:
  bloquea esa combinación IP + usuario.

- 20 fallos totales desde la misma IP en 10 minutos:
  bloquea esa IP temporalmente.

## Variables

```env
LOGIN_RATE_LIMIT_ATTEMPTS=5
LOGIN_RATE_LIMIT_IP_ATTEMPTS=20
LOGIN_RATE_LIMIT_WINDOW_MINUTES=10
```

## Resultado

Si alguien se equivoca varias veces con su usuario, no bloquea automáticamente a otros usuarios desde otro dispositivo o con otra cuenta.

Solo se bloquea toda la IP cuando hay muchos fallos generales, que ya parece más un ataque.
