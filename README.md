# UnCalificado

Desarrollo formal del backend. El material del curso (SRS, ADR, OpenAPI original y diagramas) permanece en:

`/home/j3su5/tec_de_monterrey/TC5062-A01840340`

El contrato que gobierna este código está en `contracts/openapi.yaml`. El trabajo pendiente está en `PLAN.md`.

## Qué hay hoy

Flask, PostgreSQL, JWT, bcrypt y el módulo de autenticación. El resto del contrato todavía no tiene handlers.

## Arranque local

1. Copia `.env.example` como `.env` y cambia `JWT_SECRET`.
2. Inicia PostgreSQL:

```bash
docker compose up -d db
```

3. Construye e inicia la API:

```bash
docker compose up -d --build api
```

4. Carga datos de demostración:

```bash
docker compose --profile seed run --rm seed
```

La API queda en `http://localhost:8000`. PostgreSQL en `5432`.

Cuentas demo (`DemoPass123!`):

- `demo.cliente@example.com`
- `demo.proveedor@example.com`
- `demo.admin@example.com`

Deben eliminarse antes de un entorno compartido.

## Persistencia

PostgreSQL guarda usuarios, perfiles, solicitudes, citas, propuestas, cambios, mensajes, evaluaciones, verificaciones y bitácora. Los archivos solo guardan metadata y `object_key`; el binario va a object storage.
