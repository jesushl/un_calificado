# UnCalificado

Desarrollo formal del backend. El material del curso (SRS, ADR, OpenAPI original y diagramas) permanece en:

`/home/j3su5/tec_de_monterrey/TC5062-A01840340`

El contrato que gobierna este código está en `contracts/openapi.yaml`. El trabajo pendiente está en `PLAN.md`.

## Qué hay hoy

Flask, PostgreSQL, Alembic, JWT, bcrypt y los handlers del contrato: autenticación, proveedores, solicitudes, contratación, evaluaciones y privacidad. El binario de archivos no vive en la API; se entrega con URL temporal.

## Arranque local

1. Copia `.env.example` como `.env` y cambia `JWT_SECRET`.
2. Construye e inicia base, API y cliente web (solo la primera vez o si cambian Dockerfiles / dependencias). Los contenedores montan el código del repo y recargan al guardar:

```bash
docker compose up -d --build
```

En el día a día, sin rebuild:

```bash
docker compose up -d
```

3. Carga datos de demostración:

```bash
docker compose --profile seed run --rm seed
```

- Cliente web: `http://localhost:5173`
- API: `http://localhost:8000`
- PostgreSQL: `5432`

Guía visual en `web/design/styleguide.html`. Pruebas: `cd web && npm test` (unitarias) y `pytest web/e2e` (Selenium).

Cuentas demo (`DemoPass123!`):

- `demo.cliente@example.com`
- `demo.proveedor@example.com`
- `demo.admin@example.com`

Deben eliminarse antes de un entorno compartido.

## Persistencia

PostgreSQL guarda usuarios, perfiles, solicitudes, citas, propuestas, cambios, mensajes, evaluaciones, verificaciones y bitácora. Los archivos solo guardan metadata y `object_key`; el binario va a object storage.
