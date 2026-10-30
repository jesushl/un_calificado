# Plan de acciones restantes — UnCalificado

**Ubicación de desarrollo:** `/home/j3su5/projects/uncalificado`  
**Referencia documental:** `/home/j3su5/tec_de_monterrey/TC5062-A01840340`  
**Contrato:** `contracts/openapi.yaml` (copia de `S04_A2/openapi.yaml`)

Este archivo es la lista de trabajo del desarrollo formal. El repositorio del curso ya no es el lugar para implementar código.

## Estado actual

Cerrado y usable:

- Flask, Gunicorn, Docker Compose, Alembic y PostgreSQL 16.
- Registro, login, consentimientos, logout con `jti`, `/users/me` y ping de administrador.
- JWT con `iat`/`exp`/`jti`, secreto previo opcional, bcrypt y RBAC deny-by-default.
- Handlers de proveedores, solicitudes, contratación, evaluaciones, privacidad ARCO y reporte de disponibilidad.
- Modelos relacionales, URLs temporales de archivos y datos demo aislados a development/test.
- Pruebas de autenticación, plataforma, proveedores, solicitudes, contratación y privacidad.
- Radio de descubrimiento por alcaldía y distancia máxima en la cuenta (filtra índice y listados). El domicilio exacto no se usa como origen.

Pendiente operativo, no de contrato:

- Gestor de secretos real y pruebas de carga RNF-08.
- Proxy/pool de PostgreSQL para Lambda.
- Quitar cuentas demo antes de un entorno compartido.

## Principios que no se negocian

1. Spec-first: cada endpoint se implementa desde `contracts/openapi.yaml` y se rastrea a criterios `x-acceptance-criteria`.
2. PostgreSQL es la fuente transaccional; las imágenes y videos viven en object storage.
3. El despliegue objetivo agrupa Lambdas por capacidad, no por tabla, para mantener bajo coste.
4. Autorización por rol y propiedad en cada operación, no solo un JWT válido.
5. Sin pagos. La IA no decide citas, propuestas, cambios ni revela domicilios.

## Fase 1 — Plataforma mínima para crecer

Hecho, salvo el retiro de cuentas demo en un entorno compartido:

- Alembic versiona el esquema; `create_all` queda solo para SQLite/pruebas.
- Matriz RBAC completa para `/api/v1` y alias `/api`.
- `POST /auth/consents`, `POST /auth/logout` y `PATCH /users/me`.
- Rate limiting en registro y login; `409` se conserva por contrato.
- Seed demo bloqueado fuera de `development`/`test`.

## Fase 2 — Proveedores

Hecho: alta/consulta/reemplazo de perfil, portafolio con URL temporal, envío y revisión de verificaciones.

## Fase 3 — Solicitudes

Hecho: alta/consulta/edición, adjuntos, representación visual, búsqueda, selección, decisión del proveedor, soporte, transiciones y RF-52.

## Fase 4 — Contratación

Hecho: citas con doble confirmación, propuestas, cambios, análisis informativo de IA, mensajes sin teléfonos y bitácora append-only.

## Fase 5 — Cierre, privacidad y operación

Hecho en API: evaluaciones, ARCO y reporte mensual. Logout revoca `jti`; el secreto previo permite rotación simple.

Sigue fuera de este repo:

- Secretos en un gestor dedicado.
- Proxy/pool de PostgreSQL para Lambda.
- Pruebas de carga RNF-08.

## Siguiente trabajo operativo

1. Quitar o rotar cuentas demo antes de un entorno compartido.
2. Conectar object storage real y un gestor de secretos.
3. Pruebas de carga RNF-08 y pool de PostgreSQL para Lambda.

## Siguiente trabajo de producto

### Mapa y radio (reemplaza la alcaldía como origen)

La distancia no se fija por alcaldía. El usuario ve un mapa con un círculo cuyo radio es el alcance de búsqueda. Puede arrastrar el centro del círculo; ese punto (aproximado, nunca un domicilio publicado) y el radio son la configuración de descubrimiento.

RF-52 se mantiene: el mapa no muestra ni guarda calle y número como dato público.

### Menú de cuenta

La configuración de búsqueda y la de usuario viven siempre en un menú desplegable de opciones (no como un enlace suelto en la barra). Desde ahí se entra a zona, radio, perfil y cierre de sesión.

### Ficha del calificado

- Si el perfil está etiquetado con oficios (p. ej. albañilería), no preguntar qué servicio busca quien contacta: se usa el oficio del calificado. Si tiene más de uno, se elige entre esos, no del catálogo completo.
- Al pie de la ficha, perfiles similares en el área. Si hay pocos, se amplía el radio hasta completar una tira útil.

### Analítica (submódulo)

Base de interacciones de usuarios, no un dashboard de marketing. Registrar y consultar:

- Número de visitas (índice, fichas, autenticación).
- Origen de la visita: Facebook, Google, TikTok, directo, etc.
- Perfiles de calificados más visitados.
- Zonas con más usuarios (clientes).
- Zonas con más calificados.
- Oficios más populares (vistas, contactos, proyectos).

El dato de zona sigue siendo aproximado. No persistir domicilio exacto ni identificadores de anuncio que no hayamos declarado en privacidad.

No implementar microservicios ni colas en esta etapa. Cada capacidad puede empaquetarse después como una Lambda que reutilice el mismo dominio y la misma base.
