"""Matriz de acceso derivada de contracts/openapi.yaml."""

from .models import UserRole

ALL_ROLES = set(UserRole)
CLIENT_PROVIDER = {UserRole.CLIENTE, UserRole.PROVEEDOR}

PUBLIC_ROUTES = {
    ("POST", "/api/v1/auth/register"),
    ("POST", "/api/v1/auth/login"),
    ("POST", "/api/auth/register"),
    ("POST", "/api/auth/login"),
}

_BASE_POLICY = {
    "GET /auth/me": ALL_ROLES,
    "POST /auth/consents": ALL_ROLES,
    "POST /auth/logout": ALL_ROLES,
    "GET /auth/admin/ping": {UserRole.ADMINISTRADOR},
    "GET /users/me": ALL_ROLES,
    "PATCH /users/me": ALL_ROLES,
    "GET /providers": ALL_ROLES,
    "POST /providers": {UserRole.PROVEEDOR},
    "GET /providers/{providerId}": ALL_ROLES,
    "PUT /providers/{providerId}": {UserRole.PROVEEDOR},
    "GET /providers/{providerId}/portfolio": ALL_ROLES,
    "POST /providers/{providerId}/portfolio": {UserRole.PROVEEDOR},
    "POST /providers/{providerId}/verifications": {UserRole.PROVEEDOR},
    "PATCH /providers/{providerId}/verifications/{verificationId}": {
        UserRole.ADMINISTRADOR
    },
    "GET /requests": ALL_ROLES,
    "POST /requests": {UserRole.CLIENTE},
    "GET /requests/{requestId}": ALL_ROLES,
    "PATCH /requests/{requestId}": {UserRole.CLIENTE},
    "POST /requests/{requestId}/attachments": {UserRole.CLIENTE},
    "POST /requests/{requestId}/visual-representations": {UserRole.CLIENTE},
    "POST /requests/{requestId}/search": {UserRole.CLIENTE},
    "PUT /requests/{requestId}/selection": {UserRole.CLIENTE},
    "POST /requests/{requestId}/provider-decision": {UserRole.PROVEEDOR},
    "POST /requests/{requestId}/support-requests": {UserRole.CLIENTE},
    "PATCH /requests/{requestId}/status": CLIENT_PROVIDER,
    "GET /requests/{requestId}/messages": ALL_ROLES,
    "POST /requests/{requestId}/messages": CLIENT_PROVIDER,
    "GET /requests/{requestId}/audit-log": ALL_ROLES,
    "POST /requests/{requestId}/evaluations": CLIENT_PROVIDER,
    "GET /requests/{requestId}/privacy": CLIENT_PROVIDER,
    "POST /appointments": CLIENT_PROVIDER,
    "GET /appointments/{appointmentId}": CLIENT_PROVIDER,
    "PATCH /appointments/{appointmentId}": CLIENT_PROVIDER,
    "DELETE /appointments/{appointmentId}": CLIENT_PROVIDER,
    "POST /proposals": {UserRole.PROVEEDOR},
    "POST /proposals/{proposalId}/decision": {UserRole.CLIENTE},
    "POST /changes": CLIENT_PROVIDER,
    "PATCH /changes/{changeId}/decision": CLIENT_PROVIDER,
    "POST /changes/{changeId}/analysis": CLIENT_PROVIDER,
    "POST /privacy/requests": ALL_ROLES,
    "POST /privacy/requests/{folio}/fulfillment": {UserRole.ADMINISTRADOR},
    "GET /admin/availability-reports": {UserRole.ADMINISTRADOR},
    "GET /files/{fileId}/content": ALL_ROLES,
}


def _with_prefixes(policy: dict[str, set[UserRole]]) -> dict[str, set[UserRole]]:
    expanded = {}
    for key, roles in policy.items():
        method, path = key.split(" ", 1)
        expanded[f"{method} /api/v1{path}"] = roles
        expanded[f"{method} /api{path}"] = roles
    return expanded


ROLE_POLICY = _with_prefixes(_BASE_POLICY)
