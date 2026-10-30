# Plan de acciones restantes — UnCalificado

**Ubicación de desarrollo:** `/home/j3su5/projects/uncalificado`  
**Referencia documental:** `/home/j3su5/tec_de_monterrey/TC5062-A01840340`  
**Contrato:** `contracts/openapi.yaml` (copia de `S04_A2/openapi.yaml`)

Este archivo es la lista de trabajo del desarrollo formal. El repositorio del curso ya no es el lugar para implementar código.

## Estado actual

Cerrado y usable:

- Flask, Gunicorn, Docker Compose y PostgreSQL 16.
- Registro, login, `/auth/me`, `/users/me` y ping de administrador.
- JWT con `iat`/`exp`, bcrypt, RBAC deny-by-default.
- Modelos relacionales y datos demo.
- Pruebas del módulo de autenticación.

Aún no hay handlers de negocio. Las rutas del contrato distintas de auth/health quedan bloqueadas por la política de acceso.

## Principios que no se negocian

1. Spec-first: cada endpoint se implementa desde `contracts/openapi.yaml` y se rastrea a criterios `x-acceptance-criteria`.
2. PostgreSQL es la fuente transaccional; las imágenes y videos viven en object storage.
3. El despliegue objetivo agrupa Lambdas por capacidad, no por tabla, para mantener bajo coste.
4. Autorización por rol y propiedad en cada operación, no solo un JWT válido.
5. Sin pagos. La IA no decide citas, propuestas, cambios ni revela domicilios.

## Fase 1 — Plataforma mínima para crecer

- Introducir Alembic y dejar de usar `create_all` como esquema de desarrollo.
- Completar la matriz RBAC para todas las rutas del contrato (`/api/v1` y alias `/api`).
- Añadir `POST /auth/consents` y `POST /auth/logout`.
- Añadir `PATCH /users/me`.
- Rate limiting en registro y login; conservar `409` solo mientras el contrato lo exija.
- Quitar o aislar cuentas demo antes de cualquier entorno compartido.

## Fase 2 — Proveedores

- `GET/POST /providers`
- `GET/PUT /providers/{providerId}`
- Portafolio: metadata en PostgreSQL y binario en object storage con URL temporal.
- Verificaciones: envío por proveedor y revisión por administrador.

## Fase 3 — Solicitudes

- `GET/POST /requests` y `GET/PATCH /requests/{requestId}`
- Adjuntos y representaciones visuales.
- Búsqueda, selección de proveedor y decisión del proveedor.
- Transiciones de estado y solicitudes de soporte.
- Domicilio visible solo cuando RF-52 lo autorice.

## Fase 4 — Contratación

- Citas: alta, consulta, actualización y cancelación.
- Propuestas y decisión del cliente.
- Cambios de presupuesto, decisión y análisis informativo de IA.
- Mensajes sin teléfonos y bitácora append-only.

## Fase 5 — Cierre, privacidad y operación

- Evaluaciones al concluir un proyecto.
- Solicitudes ARCO y su cumplimiento.
- Reporte mensual de disponibilidad para administrador.
- Secretos en un gestor, rotación JWT y revocación por `jti` si hay logout real.
- Proxy/pool de PostgreSQL para Lambda.
- Pruebas de carga RNF-08.

## Orden recomendado para el siguiente commit de código

1. Alembic y esquema versionado.
2. Consentimientos, logout y `PATCH /users/me`.
3. Módulo de proveedores.
4. Módulo de solicitudes.

No implementar microservicios ni colas en esta etapa. Cada capacidad puede empaquetarse después como una Lambda que reutilice el mismo dominio y la misma base.
