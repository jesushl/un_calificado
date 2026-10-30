"""Matriz de acceso derivada de S04_A2/openapi.yaml.

Las rutas de negocio se conectarán a estas dependencias cuando se implementen
sus módulos. La autenticación se aplica en `security.py`; una ruta que no
aparece como pública requiere un usuario autenticado.
"""

from .models import UserRole

PUBLIC_ROUTES = {
    ("POST", "/api/v1/auth/register"),
    ("POST", "/api/v1/auth/login"),
    ("POST", "/api/auth/register"),
    ("POST", "/api/auth/login"),
}

ROLE_POLICY = {
    "GET /api/v1/auth/me": set(UserRole),
    "GET /api/auth/me": set(UserRole),
    "GET /api/v1/users/me": set(UserRole),
    "GET /api/users/me": set(UserRole),
    "GET /api/v1/auth/admin/ping": {UserRole.ADMINISTRADOR},
    "GET /api/auth/admin/ping": {UserRole.ADMINISTRADOR},
    "GET /api/v1/providers": {
        UserRole.CLIENTE,
        UserRole.PROVEEDOR,
        UserRole.ADMINISTRADOR,
    },
    "GET /api/providers": {
        UserRole.CLIENTE,
        UserRole.PROVEEDOR,
        UserRole.ADMINISTRADOR,
    },
    "POST /api/v1/providers": {UserRole.PROVEEDOR},
    "POST /api/providers": {UserRole.PROVEEDOR},
    "PUT /api/v1/providers/{providerId}": {UserRole.PROVEEDOR},
    "PUT /api/providers/{providerId}": {UserRole.PROVEEDOR},
    "POST /api/v1/requests": {UserRole.CLIENTE},
    "POST /api/requests": {UserRole.CLIENTE},
    "GET /api/v1/requests/{requestId}": set(UserRole),
    "GET /api/requests/{requestId}": set(UserRole),
    "POST /api/v1/appointments": {UserRole.CLIENTE, UserRole.PROVEEDOR},
    "POST /api/appointments": {UserRole.CLIENTE, UserRole.PROVEEDOR},
    "POST /api/v1/proposals": {UserRole.PROVEEDOR},
    "POST /api/proposals": {UserRole.PROVEEDOR},
    "POST /api/v1/changes": {UserRole.CLIENTE, UserRole.PROVEEDOR},
    "POST /api/changes": {UserRole.CLIENTE, UserRole.PROVEEDOR},
    "POST /api/v1/privacy/requests": set(UserRole),
    "POST /api/privacy/requests": set(UserRole),
    "GET /api/v1/admin/availability-reports": {UserRole.ADMINISTRADOR},
    "GET /api/admin/availability-reports": {UserRole.ADMINISTRADOR},
}
