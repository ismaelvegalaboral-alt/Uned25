# Roles y permisos

La plataforma usa grupos estándar de Django:

- `Trabajador`
- `RRHH`
- `Dirección`
- `Administrador`

## Trabajador

Puede:

- ver su panel personal,
- crear solicitudes para sí mismo si su usuario está vinculado a una ficha,
- ver sus propias solicitudes,
- descargar sus propios PDFs de solicitud y resolución.

No puede:

- ver fichas de otros trabajadores,
- ver calendario global,
- ver Radar RRHH,
- aprobar o denegar solicitudes,
- descargar documentos de otros empleados.

## RRHH

Puede:

- gestionar fichas de trabajadores,
- vincular usuarios a fichas,
- crear solicitudes para cualquier trabajador,
- ver histórico completo,
- ver calendario global,
- ver Radar RRHH,
- descargar PDFs.

No puede aprobar o denegar por defecto. La aprobación queda separada en Dirección.

## Dirección

Puede:

- ver histórico completo,
- ver detalle de solicitudes,
- ver alertas RRHH,
- ver calendario global,
- aprobar o denegar solicitudes,
- generar PDFs de resolución.

No puede gestionar fichas salvo que también tenga rol de RRHH o Administrador.

## Administrador

Puede todo dentro de la plataforma. Además, si el usuario tiene `is_staff=True`, puede entrar al admin de Django.

## Crear grupos

```bash
python manage.py bootstrap_roles
```

## Asignar roles

```bash
python manage.py bootstrap_roles --username ismael --role Trabajador
python manage.py bootstrap_roles --username rrhh --role RRHH
python manage.py bootstrap_roles --username direccion --role Dirección
python manage.py bootstrap_roles --username admin --role Administrador
```

Para sustituir otros roles de plataforma del usuario:

```bash
python manage.py bootstrap_roles --username ismael --role Trabajador --clear-existing
```

## Vincular trabajador con usuario

1. Entra con un usuario de RRHH o administrador.
2. Ve a Fichas.
3. Crea o edita la ficha del trabajador desde el admin.
4. Selecciona el campo `usuario vinculado`.

Sin esa vinculación, un trabajador no podrá crear solicitudes propias ni ver su información.
