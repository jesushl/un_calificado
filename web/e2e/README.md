# Pruebas E2E (Selenium)

Corrigen el flujo visual del cliente web contra Compose + seed.

## Requisitos

- Stack arriba: `docker compose up` (api + web + db)
- Seed demo: `docker compose --profile seed run --rm seed`
- Chrome / Chromium disponible en el host
- Dependencias: `pip install -r web/e2e/requirements.txt`

Cuentas demo: `demo.cliente@example.com` / `demo.proveedor@example.com` — contraseña `DemoPass123!`.

El flujo feliz hace varios logins; en Compose el API usa `AUTH_RATE_LIMIT` alto (default 100) para no cortar la suite.

## Cómo correr

Desde la raíz del repo:

```bash
UX_BASE_URL=http://127.0.0.1:5173 pytest web/e2e -q
```

Specs de contratación:

- `test_flujo_cliente.py` — índice → contacto → presupuesto → cita → mensajes → cierre → evaluación
- `test_flujo_proveedor.py` — inbox, agenda y navegación del prestador
