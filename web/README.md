# Cliente web — UnCalificado

React + Vite. El sistema gráfico vive en `design/` (Taller editorial, Impeccable).

## Arranque

En una terminal, la API:

```bash
docker compose up -d db api
```

En otra, el cliente:

```bash
cd web
npm install
npm run dev
```

Abre `http://localhost:5173`. Vite proxifica `/api` a `http://127.0.0.1:8000`.

Cuentas demo (`DemoPass123!`):

- `demo.cliente@example.com`
- `demo.proveedor@example.com`
- `demo.admin@example.com`

## Pruebas

Unitarias (Vitest + Testing Library):

```bash
npm test
```

Funcionales (Selenium, Chrome headless). Con el cliente levantado:

```bash
# desde la raíz del repo, con el venv del backend
.venv/bin/pip install -r web/e2e/requirements.txt
UX_BASE_URL=http://127.0.0.1:5173 .venv/bin/pytest web/e2e -q
```

## Diseño

- Guía visual: `design/styleguide.html`
- Tokens: `design/tokens.css`
- Copy: `design/COPY.md`
- Dirección: `design/DIRECTION.md`
