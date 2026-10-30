# UnCalificado — Dirección estética

**Concepto: Taller editorial.** La interfaz es una hoja de obra hecha por un maestro que explica con claridad: papel de plano, tinta azul-negra, ladrillo, luz de trabajo. Sobria, local, de oficio. Tres palabras de marca: **confianza, taller, vecindario**.

Fuente de verdad del contexto: `AGENTS.md` → *Design Context*. Este documento lo traduce a decisiones visuales; no lo reemplaza.

---

## 1. Tono

| Eje | Decisión |
|---|---|
| Registro | Editorial de taller: titulares de rótulo en condensada pesada, texto de lectura humanista y muy legible. |
| Temperatura | Cálida (papel crema, ladrillo, ocre). El único frío es la tinta, que es azul-negra de plano, no cian. |
| Modo | **Claro**. Se usa de día, en casa o en obra, con sol en la pantalla. No hay modo oscuro en v1. |
| Voz | Mexicana, de tú, concreta. Un maestro de obra, no un SaaS (ver `COPY.md`). |
| Densidad | Varía por rol (§3). |

## 2. Qué lo hace inolvidable (la idea que se recuerda)

1. **La escuadra que dice “sí”.** El símbolo es una escuadra de carpintero con marcas de regla, girada hasta leerse como palomita (*calificado*). Es la única forma de marca; se repite a gran escala recortada en portadas y en vacíos.
2. **Lenguaje de plano, usado con disciplina.** Tres recursos y no más:
   - **Cuadrícula de plano** (24 / 120 px) solo en portadas, login y vacíos.
   - **Cota** (línea de acotación con topes) para encabezar secciones. Es el único adorno recurrente.
   - **Sello** estampado, doble anillo e inclinación de −2.5°, **solo** donde hay una verificación real.
3. **Rótulo de barda.** Archivo condensada en 800/900 y mayúsculas para H1/H2: letrero pintado, legible a distancia.
4. **Zona sí, calle no.** El domicilio tiene tres estados visuales distintos (trama + círculo punteado / cruz de topógrafo / oculto). La privacidad se *ve*, no se esconde en un texto legal.
5. **Anillo de avance.** Los 6 estados del proyecto se dibujan como un anillo que se llena (0 → 100 %), más una regla de avance estilo cinta métrica.

## 3. Cómo se distinguen los tres roles

Misma familia visual (papel, tipografía, reglas, componentes). Cambian **cuatro** cosas, controladas con `data-role="cliente|proveedor|admin"` en `<html>` o en cualquier contenedor:

| | **Cliente** | **Proveedor** | **Administrador** |
|---|---|---|---|
| Color de rol | Ladrillo `oklch(49% 0.145 42)` | Luz de obra / ocre `oklch(82% 0.16 86)` | Azul de plano `oklch(40% 0.11 258)` |
| Cinta superior (6 px en `.nav`) | ladrillo | ocre | azul de plano |
| Glifo en `.role-tag` | ■ cuadro (muro) | ▲ escuadra | ● sello |
| Texto sobre el botón primario | papel | **tinta** (ocre es claro) | papel |
| Densidad (`--density`) | 1 — espacioso, una acción principal | 0.88 — listas para una mano, celular | 0.66 (0.9 en táctil) — tablas densas |
| Layout típico | Proyecto grande, pasos claros | Bandeja de solicitudes, acciones en fila | Tablas con cifras tabulares |

Reglas:
- El color de rol **no es el único** diferenciador (glifo + palabra en `.role-tag`).
- El nombre de la marca siempre va en tinta, nunca en color de rol.
- Nunca mezclar dos colores de rol en la misma vista, salvo en documentación.
- `--color-accent` y todos los componentes leen el rol; **no** hardcodear ladrillo en componentes.

## 4. Sistema

### Tipografía
- **Display: Archivo** (variable, eje de ancho `wdth` 62–125 → se usa 70–82 %, condensada). Pesos 500 / 700 / 800 / 900. H1/H2 en MAYÚSCULAS; H3/H4 en caja normal para leerse rápido.
- **Cuerpo: Atkinson Hyperlegible Next** (Braille Institute). Letras diseñadas para no confundirse: sol directo, pantallas baratas, vista cansada. Cuerpo 17 px, pesos 400 / 600 / 800.
- Dos familias, contraste en ancho y estructura (condensada de rótulo + humanista legible). Sin Inter, Roboto, Arial, Open Sans ni system-ui.
- Escala modular ≈1.25–1.33. `xs`–`md` en `rem` fijo (UI de app); `lg`–`display` fluidos con `clamp()`.
- Cifras tabulares en tablas y precios (`font-variant-numeric: tabular-nums`).

### Color (todo `oklch`)
Neutros **teñidos**: papel cálido (matiz 80–88) y tinta azul de plano (matiz 258). Sin `#000` ni `#fff`.
Proporción 60 papel / 30 tinta / 10 rol y estados. Los estados (ok nopal, warn ocre, danger rojo sello, pending tinta con borde punteado) **siempre** llevan símbolo y texto.
Contraste verificado (WCAG AA mínimo, la mayoría AAA): tinta/papel 17:1 · secundario 7.6:1 · terciario 5.4:1 · papel/ladrillo 6.4:1 · tinta/ocre 10:1 · papel/azul 8.9:1.

### Forma y profundidad
- Radios casi rectos (2 / 4 / 8 px). Nada de píldoras.
- Jerarquía por **reglas** (1.5 px tinta) y por tono de papel, no por sombras difusas.
- Botón = **tecla**: canto inferior de 2 px del color oscuro del rol; se hunde 2 px al presionar.
- Hoja (`.sheet`) en lugar de modal: sube del borde en móvil, entra por la derecha en escritorio (`<dialog>` nativo).

### Movimiento
Una sola secuencia de entrada escalonada por página (`.reveal`, ≤ 6 elementos). Feedback con `transform`/`opacity`, curvas exponenciales (ease-out-quart/expo), sin rebote. `prefers-reduced-motion` colapsa duraciones y retira los desplazamientos; los estados y el foco siguen funcionando.

### Accesibilidad (no negociable)
- Foco visible global: anillo de 3 px, tinta, separación 3 px (ocre sobre fondos oscuros con `.on-dark`).
- Objetivo táctil ≥ 44 px (`pointer: coarse`).
- Campos con etiqueta visible, ayuda ligada con `aria-describedby`, errores con símbolo + texto.
- Estado nunca solo por color. Texto ≥ 17 px, `rem`, zoom permitido.
- El color de rol no transmite información que el texto no diga.

## 5. Anti-referencias

| No | Por qué |
|---|---|
| **Uber / apps de movilidad** | Negro + verde + mapa a pantalla completa y tono corporativo. Nosotros: papel, oficio, vecindario. |
| **HomeDepot.com genérico** | Naranja de retail, rejilla de tarjetas idénticas, descuentos. Aquí no hay precios en vitrina ni urgencia. |
| **Dashboards indigo/cyan** | Es el uniforme de “SaaS”. La tinta es azul-negra y el azul de plano solo vive en el rol Admin. |
| **Glassmorphism, blur decorativo, glow** | Ninguna superficie translúcida. Solo papel opaco y reglas. |
| **Gradientes púrpura / azul-violeta, texto en degradado** | Cero gradientes de color. Los únicos degradados son la cuadrícula y la trama. |
| **Dark mode neón** | Modo claro por diseño: es de día y hay sol. |
| **Tarjetas dentro de tarjetas, rejillas idénticas icono+título+texto** | Se usan filas con reglas y una ficha destacada; la jerarquía rompe la simetría. |
| **Íconos redondeados sobre cada título** | La clave de oficio de 3 letras (ALB, PLO, ELE…) sustituye al clip-art. |
| **Humor o “empoderamiento”** | El copy es concreto y mexicano (ver `COPY.md`). |

## 6. Prueba “¿lo hizo una IA?”

Antes de dar por bueno cualquier pantalla nueva, que pase estas cinco:
1. ¿Hay un titular de rótulo en condensada que podría estar en una barda? (sí/no)
2. ¿El color de rol aparece en ≤ 10 % de la pantalla?
3. ¿Hay algún lugar donde un sello, una cota o la cuadrícula se usan sin significado? (debe ser no)
4. ¿Se ve la privacidad del domicilio sin leer? (sí)
5. ¿Podrías cambiar de rol (`data-role`) y que la pantalla siga siendo la misma familia pero claramente otra? (sí)

## 7. Cómo consumirlo desde React

```html
<link rel="stylesheet" href="/design/tokens.css">
<link rel="stylesheet" href="/design/components.css">
<html lang="es-MX" data-role="cliente">
```
- Importar `tokens.css` y luego `components.css` una sola vez (p. ej. en `main.tsx`). Los componentes usan clases (`.btn`, `.btn-primary`, `.field`, `.chip`, `.status[data-status]`, `.zone--aprox|autorizado|oculto`, `.ficha`, `.sheet`, `.empty`, `.table`, `.nav`).
- Cambiar rol = cambiar `data-role` en el contenedor raíz de esa sección de la app.
- Estados de proyecto: `<span class="status" data-status="EN_PROCESO">En proceso</span>` (valores del enum `ProjectStatus`).
- Domicilio: la clase de zona se elige con `PrivateLocation.visibility` (`ZONA_APROXIMADA` → `zone--aprox`, `DOMICILIO_AUTORIZADO` → `zone--autorizado`, `OCULTO` → `zone--oculto`). **Nunca** renderizar `exactAddress` si `visibility` no es `DOMICILIO_AUTORIZADO`.
- Oficios: claves `ALB PLO ELE CAR HER PIN PIS VID TAB IMP` ↔ `albanileria plomeria electricidad carpinteria herreria pintura pisos_azulejos vidrieria_canceleria tablaroca impermeabilizacion`.
- `.ruler` y `.zone`, `.ficha`, `.empty` responden a su **contenedor**: envolver `.ruler` en `.ruler-wrap`, `.zone` en `.zone-inner`, `.empty` en `.empty-inner` (ver `styleguide.html`).
