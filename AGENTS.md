# UnCalificado

Backend Flask + PostgreSQL. Cliente web React en `web/`.

## Referencia del curso

Desarrollo formal del backend. El material del curso (SRS, ADR, OpenAPI original y diagramas) permanece en:

`/home/j3su5/tec_de_monterrey/TC5062-A01840340`

## Design Context

### Users
Clientes en México que necesitan un oficio (albañilería, plomería, electricidad, etc.) y quieren contratar con confianza, sin pagar dentro de la app. Proveedores — trabajadores u organizaciones — que reciben solicitudes entre un trabajo y otro, a menudo en el celular. Administradores que verifican documentos y atienden ARCO. El uso es diurno, en casa o en obra, no en un dashboard de oficina.

### Brand Personality
Sobrio, local, de oficio. Tres palabras: **confianza, taller, vecindario**. Debe sentirse como un maestro de obra que explica con claridad, no como un marketplace de descuentos ni un SaaS de Silicon Valley. Español de México, MXN, hora del centro.

### Aesthetic Direction
Taller editorial: papel de plano, ocre de ladrillo, metal oxidado, luz de trabajo. Modo claro como default. Tipografía con carácter (no Inter, Roboto, Open Sans ni system UI). Anti-referencias: Uber, Homedepot.com genérico, dashboards indigo/cyan, glassmorphism, gradientes púrpura.

### Design Principles
1. La confianza se ve antes que la conversión: estados, verificación y privacidad del domicilio son visibles, no escondidos.
2. Cada rol (cliente, proveedor, admin) comparte familia visual pero se distingue por acento y densidad.
3. El domicilio exacto nunca se trata como dato público en la interfaz.
4. Contraste, foco de teclado y `prefers-reduced-motion` no son opcionales.
5. El copy es concreto y mexicano; nada de “empower” ni de “soluciones end-to-end”.
