# Revisión de seguridad del módulo de autenticación

## Alcance

Se implementó el módulo inicial de autenticación con Flask usando `S04_A2/openapi.yaml` como fuente de verdad. El contrato disponible se llama `openapi.yaml`, no `openapi_equipo.yaml`; la implementación conserva el contrato `/api/v1` y ofrece aliases compatibles `/api`.

La persistencia usa SQLAlchemy y puede ejecutarse con SQLite local o PostgreSQL mediante `DATABASE_URL`. Las contraseñas se almacenan con bcrypt. Los tokens son JWT firmados con un secreto tomado de variables de entorno.

## Controles implementados

- `POST /api/v1/auth/register` y `POST /api/auth/register`: públicos; no permiten el rol `ADMINISTRADOR`.
- `POST /api/v1/auth/login` y `POST /api/auth/login`: públicos; devuelven `401` con credenciales inválidas.
- `GET /api/v1/auth/me` y `GET /api/auth/me`: requieren JWT válido.
- `GET /api/v1/users/me` y `GET /api/users/me`: requieren JWT válido.
- `GET /api/v1/auth/admin/ping` y alias `/api/auth/admin/ping`: requieren JWT válido y rol `ADMINISTRADOR`; se usa como ruta de verificación del control RBAC y no se publica como operación de negocio.
- Las rutas de negocio protegidas derivadas del OpenAPI son `/auth/consents`, `/auth/logout`, `/users/me`, `/providers`, `/requests`, `/appointments`, `/proposals`, `/changes`, `/messages`, `/evaluations`, `/privacy` y `/admin/availability-reports`. El middleware exige autenticación para rutas `/api/**`; la matriz de roles restringe capacidades como proveedores, contratación, privacidad y administración.

## Protección de rutas

| Caso | Nivel de acceso | Resultado esperado |
|---|---|---|
| Registro y login | Público | Solo validación de esquema y reglas de cuenta |
| `/auth/me` y `/users/me` | Cualquier usuario activo autenticado | `401` sin JWT válido; `200` con JWT válido |
| `/providers` creación/actualización | `PROVEEDOR`; administración según operación | `403` para roles no autorizados |
| `/requests` de cliente | `CLIENTE` y propiedad del recurso | `401` o `403` según la causa |
| Citas, propuestas y cambios | Participantes del proyecto y propiedad | `401`, `403` o `409` por estado |
| Evaluaciones | Participantes autorizados de proyecto concluido | `401` o `403` |
| Verificaciones, privacidad administrativa y reportes | `ADMINISTRADOR` | `403` para otros roles |
| Archivos y domicilio | Propiedad, rol y estado del proyecto | Nunca se entrega acceso directo al storage |

La protección se ejecuta en `app/auth_middleware.py` y se refuerza en las dependencias de ruta `get_current_user` y `require_roles`. El middleware valida el esquema Bearer, firma, algoritmo permitido, `sub`, `role`, `iat`, `exp`, existencia del usuario, estado activo y coincidencia entre el rol del token y el rol persistido.

## Resultados de pruebas manuales

Pruebas ejecutadas contra un servidor temporal con `JWT_SECRET` y `DATABASE_URL` definidos por entorno:

| Prueba | Resultado |
|---|---:|
| Petición a `/api/v1/auth/me` sin token | `401` |
| Petición con un carácter del token modificado | `401` |
| Petición con token expirado | `401` |
| Cliente `CLIENTE` accede a `/api/v1/auth/admin/ping` | `403` |
| Cliente autenticado accede a `/api/v1/auth/me` | `200` |
| Registro válido | `201` |

También se ejecutaron cinco pruebas automatizadas: todas pasaron. Se comprobó que el registro no devuelve `password` ni `password_hash`.

## Hallazgos y correcciones

1. **Expiración JWT:** el token incluye `iat` y `exp`; `JWT_EXPIRATION` se interpreta en minutos y no existe una opción de token sin expiración.
2. **Secreto configurable:** `JWT_SECRET` se obtiene de `.env`/variables de entorno y no está escrito en el código. `.env.example` contiene únicamente un valor de reemplazo.
3. **Contraseñas:** solo se persiste `password_hash` generado con bcrypt; los esquemas de respuesta no contienen contraseña ni hash.
4. **Tokens inválidos:** la firma, algoritmo, claims obligatorios y estado del usuario se validan antes de ejecutar la ruta.
5. **Roles:** el middleware devuelve `403` cuando el JWT es válido pero el rol no tiene permiso para la ruta.
6. **Filtración de información:** login usa el mismo mensaje para correo inexistente y contraseña incorrecta; no se registran contraseñas ni tokens completos.

### Revisión final

La revisión final identificó tres puntos adicionales:

- **RBAC desalineado:** las políticas futuras estaban escritas sin `/api/v1`, por lo que una ruta de negocio podía quedar autenticada pero sin autorización por rol. Se corrigieron las claves para `/api/v1` y `/api`, y el middleware ahora aplica *deny by default*: una ruta `/api/**` sin política explícita devuelve `403`.
- **Cuentas deshabilitadas:** el login podía emitir un token para una cuenta `DISABLED`, aunque después el middleware lo rechazaba. Ahora el login rechaza esas cuentas con `401` antes de emitir el token.
- **Enumeración en registro:** el contrato actual exige `201` con `UserResponse` para un alta exitosa y `409` para correo duplicado. Esa diferencia permite inferir si existe una cuenta. Se conserva temporalmente por compatibilidad con el contrato; antes de producción se debe cambiar el contrato a un flujo de alta asíncrono con respuesta genérica y rate limiting.

La política de roles quedó alineada con las rutas del contrato, incluyendo ambos prefijos soportados. Las pruebas automatizadas y manuales se ejecutaron nuevamente después de las correcciones.

## Pendientes antes de producción

- Sustituir el secreto de ejemplo por un secreto aleatorio gestionado por Secret Manager.
- Añadir rotación de claves JWT y, si el modelo de sesión lo requiere, revocación mediante `jti`.
- Completar las rutas de negocio y sus permisos específicos antes de exponerlas; la matriz actual define la política inicial.
- Ejecutar pruebas de carga RNF-08 y configurar límites de conexión de PostgreSQL para Lambda.
