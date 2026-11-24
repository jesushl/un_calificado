# Revisión — Matriz de trazabilidad vs SRS / código / pruebas

**Revisor:** ingeniería de requisitos (IEEE 830 / IEEE 29148) y trazabilidad V&V  
**Objeto:** [`matriz_trazabilidad.md`](../matriz_trazabilidad.md)  
**Alcance:** feedback; **no** se reescribe la matriz.  
**Evidencia contrastada:** `SRS_equipo.md` (RF-01…55), `backlog_completo.md` (HU-01…15), `contracts/openapi.yaml` (`x-acceptance-criteria`), `app/projects.py`, `app/contracting.py`, nombres en `tests/`, `TC5062-14/S09_A1_jesus/`.

---

## 1. Veredicto

La matriz es **usable como inventario de cobertura** (55 RF sin huecos de ID, mapeo HU coherente con el backlog, leyenda Completo/Parcial/No implementado y una nota honesta sobre captura manual vs IA). **No está lista para auditoría académica estricta de V&V** sin corrección: el conteo **40 Completo / 11 Parcial / 4 No implementado** **sobreestima** el cumplimiento frente al código; varias celdas de **Prueba** citan evidencia que **no existe** en `tests/`; y el OpenAPI sigue etiquetando AC de agente/IA/notificaciones que el backend **no implementa**, lo que la matriz reconoce en prosa pero **reproduce** al listar esos endpoints como si trazaran el RF.

**Veredicto:** **Aprobado condicional** — sirve como borrador de trazabilidad; **no** como evidencia de verificación completa del SRS.

---

## 2. Fortalezas

1. **Cobertura de IDs:** aparecen los 55 RF (RF-01…RF-55); no hay RF omitidos ni duplicados.
2. **Mapeo HU alineado al backlog S03-A1:** RF↔HU coincide con las épicas y “RF cubiertos” de `backlog_completo.md` (p. ej. HU-05 → RF-13/14/15/19/22/25; HU-08 → RF-26…30; HU-12/13 → cambios y RF-42/55).
3. **Honestidad explícita en el bloque IA/manual:** el resumen y las notas admiten que el camino real es captura manual y que contrato ≠ intención del SRS; RF-14, RF-19, RF-25 y RF-36 como **No implementado** van en la dirección correcta.
4. **Parciales bien motivados en varios RF críticos de código:** RF-06 (sin franjas finas de API frente a `AvailabilitySlot` solo en seed), RF-23 (`visual-representations` guarda descripción/referencia sin generar imagen), RF-28 (`similarExperience` ≈ “tiene evaluaciones”, no semántica de trabajos similares), RF-30 (tope 4 + explicación fija de reglas), RF-42 (plantilla en `/changes/{id}/analysis`), RF-48 (cierre/roles sí; timeout 72 h no).
5. **Uso correcto de S09-A1 como no-UAT:** la carpeta `S09_A1_jesus/` es lint/code review/refactor/deuda técnica; la matriz acierta al decir que **no** documenta UAT funcional.
6. **Separación de artefactos** (SRS, backlog, OpenAPI, `app/`, `tests/`) cumple la expectativa IEEE 29148 de fuentes trazables.

---

## 3. Hallazgos

### Blocker

| ID | Hallazgo | Evidencia |
|---|---|---|
| B1 | **Conteo Completo inflado.** Varios RF marcados Completo no cumplen AC esenciales del SRS frente al código. | RF-12: existe `RETIRADA` admin en `review_verification`, pero **no** hay job de vencimiento automático ni aviso al proveedor (RF-12-AC-1/AC-2). RF-17: hay `POST .../attachments` con tope 5 MB, pero la matriz cita `tests/test_projects.py (adjuntos en flujo)` y **ese archivo no prueba adjuntos**. RF-37: cancelación/reprogramación en API, pero el SRS exige notificación a la contraparte; `app/contracting.py` **no** implementa canal de notificación (consistente con RF-36 No implementado). |
| B2 | **Columna Prueba con evidencia falsa o engañosa.** | RF-17 → adjuntos inexistentes en tests. RF-18 → “límites de archivo en portafolio” en `test_providers.py`: el test sube un PNG de 2048 bytes; **no** afirma límite 5 MB ni máximo 10. RF-42 → “`test_contracting.py` (flujo de cambio)”: la variable `analysis` en ese test es un `POST /changes` de creación, **no** `POST /changes/{id}/analysis`. RF-13/14/15/19/22/23/25/36/48 → celda “Prueba” rellena con párrafo S09-A1 en lugar de “sin evidencia” / “—”. |
| B3 | **Confusión contrato ≠ implementación no cerrada en la matriz.** | `POST /requests` en OpenAPI declara `x-acceptance-criteria` con RF-13…25, RF-19, RF-22, RF-23, RF-25, RF-30, etc. El handler real crea solicitud (manual/`manualCapture`); **no** hay motor de diálogo. La matriz lista `POST /requests` como endpoint de RF-13/14/15/19/22/23/25, lo que **reifica** la etiqueta del contrato. Igual: `POST /appointments` etiqueta RF-36-AC-\*; estado de matriz **No implementado** es correcto, pero la columna Endpoint sigue sugiriendo cobertura. |
| B4 | **RF-13 como Parcial por campos `aiConversationId`/`manualCapture` es sobreclaim.** | SRS RF-13 exige mensaje del agente identificándose como asistente. En código no hay turnos ni primer mensaje de agente; solo metadatos/flags. Eso es **No implementado** (o a lo sumo “stub de datos”), no Parcial de comportamiento. |

### Should-fix

| ID | Hallazgo | RF |
|---|---|---|
| S1 | Bajar o matizar estados sobreestimados. | **RF-12 → Parcial** (retiro admin sí; vencimiento automático y avisos no). **RF-17 → Completo solo si se añaden tests de adjunto, o Parcial** hasta demostrar AC. **RF-18:** además del multi-proyecto, `add_attachment` **no** aplica tope de 10 imágenes por proyecto (RF-18-AC-3) — Parcial debe decirlo. **RF-20 → Parcial** si se audita contra AC del agente (“el agente presenta resumen”); el PATCH `summaryConfirmed` cubre confirmación manual, no RF-20-AC-1 tal cual. **RF-29 → Parcial:** orden `proximity` distingue zona exacta vs resto; **no** implementa “colonia vs colonias vecinas” (RF-29-AC-4). **RF-37 → Parcial** mientras no haya notificación a la otra parte. |
| S2 | Separar en la matriz **“endpoint con AC etiquetado”** vs **“comportamiento que satisface el RF”.** | RF-13…25, RF-36, RF-42: OpenAPI ≠ implementación (visual sin IA, analysis plantilla, appointments sin notify). |
| S3 | Columna Prueba: solo nombres de tests que **ejercen** el RF; si no hay, “sin evidencia automatizada”. | No usar S09-A1 como sustituto de prueba funcional. |
| S4 | Recalcular resumen tras reclasificar. | Tras S1+B4, Completo cae claramente por debajo de 40 (orden de magnitud esperado: ~33–36 Completo, más Parcial/No implementado). Publicar 40 Completo ante un auditor es riesgoso. |
| S5 | RF-22: Parcial es correcto, pero justificar con precisión. | `create_support` registra `reason` + `SupportStatus.REGISTRADA`; **no** adjunta resumen de conversación, **no** ofrece soporte tras 2 fallos del agente, **no** hay listado/cola admin de casos en la API revisada. |
| S6 | RF-48: distinguir AC. | RF-48-AC-2 (admin no cambia cierre) **sí** está en `update_status` (`FORBIDDEN` al administrador). RF-48-AC-1 (aviso a las 72 h) **no**. El estado Parcial es válido; la justificación debe separar ambos AC. |
| S7 | RF-06: afinar justificación. | `unavailableDates` en PUT de proveedor **sí** se considera en `_search_providers`; `AvailabilitySlot` existe en modelo/seed pero **no** como API de franjas. Parcial OK; no decir solo “generalAvailability”. |
| S8 | Orden documental IEEE. | En la tabla, RF-55 aparece **antes** de RF-45…54. Los 55 IDs están, pero el orden de lectura no sigue la numeración del SRS. |

### Polish

| ID | Hallazgo |
|---|---|
| P1 | Unificar títulos RF con el SRS (ya están cerca); evitar justificación genérica “operan en API” sin AC citables. |
| P2 | En notas de trazabilidad, añadir regla: *“x-acceptance-criteria en OpenAPI no cuenta como Completo sin handler + prueba”*. |
| P3 | Referenciar rutas de S09-A1 por archivo (`code_review-jesus.md`, `output_linter-jesus.txt`, etc.) cuando se cite, para no parecer UAT. |
| P4 | Indicar versión/commit o fecha de la rama en el encabezado (la nota 4 ya lo sugiere; falta ancla reproducible). |
| P5 | HU-05/HU-07 quedan casi sin evidencia de aceptación: coherente con No implementado/Parcial, pero conviene una fila de “deuda de épica EP-02” en el resumen por épica. |

---

## 4. Tabla RF | problema | cambio propuesto

| RF | Problema | Cambio propuesto |
|---|---|---|
| RF-06 | Justificación incompleta (sí hay `unavailableDates` en búsqueda). | Mantener **Parcial**; citar fechas no disponibles vs ausencia de API de franjas/`AvailabilitySlot`. |
| RF-12 | Marcado Completo; falta vencimiento automático y aviso. | **Parcial**; prueba: caso admin `RETIRADA` + gap AC-1. |
| RF-13 | Parcial por flags; no hay identificación del agente. | **No implementado**; quitar `POST /requests` como “cobertura” del RF o etiquetarlo “solo AC de contrato”. |
| RF-14 | Correcto No implementado; Prueba = S09-A1. | Mantener estado; Prueba → “sin evidencia”. |
| RF-15 | Parcial OK (oficio manual, sin clasificador 90 %). | Explicitar ausencia de umbral/conjunto de 50 casos (RF-15-AC-1). |
| RF-17 | Completo + prueba de adjuntos inexistente. | Corregir Prueba; añadir test o bajar a **Parcial**. |
| RF-18 | Parcial por multi-proyecto; omite tope 10 imágenes no aplicado en `add_attachment`. | Ampliar justificación; verificar también tipos JPG/PNG en prueba. |
| RF-19 | No implementado OK; celda Prueba engañosa. | Prueba → “sin evidencia”. |
| RF-20 | Completo frente a AC centrados en el agente. | **Parcial** (confirmación manual vía `summaryConfirmed`) o Completo con nota “solo camino RF-21”. |
| RF-21 | Completo razonable (camino real). | Mantener; asegurar que la justificación diga “fallback es el camino primario”. |
| RF-22 | Parcial OK pero incompleto en justificación. | Detallar: alta de caso sí; cola admin / resumen conversación / oferta automática no. |
| RF-23 | Parcial OK (`create_visual` sin generación IA). | Mantener; Prueba → sin evidencia (no hay test de `visual-representations`). |
| RF-24 | Parcial OK (acciones HTTP explícitas ≠ marco de agente). | Mantener; no listar `POST /requests` como si autorizara “acciones sensibles del agente”. |
| RF-25 | No implementado OK (UI/latencia). | No atribuir a `POST /requests`; Prueba → sin evidencia. |
| RF-28 | Parcial OK (`similarExperience` ≠ trabajos similares). | Mantener. |
| RF-29 | Completo pese a RF-29-AC-4 (vecinas) ausente. | **Parcial** o Completo con excepción documentada del AC-4. |
| RF-30 | Parcial OK (reglas, ≤4). | Mantener; no depender del tagging en `POST /requests`. |
| RF-36 | No implementado OK; OpenAPI y endpoints de citas confunden. | Mantener estado; Endpoint → “ninguno que notifique” o “AC solo en contrato”. |
| RF-37 | Completo sin notificación a contraparte. | **Parcial** (mutación de cita sí; notify no). |
| RF-42 | Parcial OK; prueba citada no llama `/analysis`. | Corregir Prueba a “sin test del endpoint analysis” o añadir uno. |
| RF-48 | Parcial OK; AC-2 implementado, AC-1 no. | Separar AC en la justificación; Prueba no-S09. |
| RF-55 | Fuera de orden en la tabla (antes de RF-45). | Reordenar tras RF-44 o agrupar con nota épica EP-04. |
| RF-01…11, 16, 26–27, 31–35, 38–41, 43–47, 49–54 | En general alineados; riesgo menor de prueba “indirecta”. | Revisar que cada Completo tenga al menos un assert que toque el AC (p. ej. RF-08/09–11: el test de providers aprueba verificación, no retira ni distingue todos los tipos con igual rigor). |

---

## 5. Riesgos de auditoría académica

1. **Trazabilidad bidireccional débil (IEEE 29148):** el vínculo RF → endpoint se basa en `x-acceptance-criteria` del OpenAPI, no en satisfacción demostrada. Un revisor puede acusar **trazabilidad ornamental** (el contrato “cumple” en papel).
2. **Falsos positivos de verificación:** citar tests que no ejercen el RF (adjuntos, analysis, límites) invalida la columna de evidencia V&V; es el hallazgo más fácil de señalar en defensa oral o rúbrica.
3. **S09-A1 malinterpretado como UAT:** aunque el texto lo niega, usarlo en la columna Prueba invita a que un evaluador cuente “prueba hecha” donde solo hay lint/refactor de otro entregable.
4. **Épica EP-02 (agente) vs métrica 40 Completo:** el SRS y el backlog centran valor en conversación/IA (RF-13…25). Reportar ~73 % Completo mientras el núcleo del agente está ausente es **inconsistente** con el propio resumen por épica de la matriz y con HU-05/HU-07.
5. **Doble estándar notificaciones:** RF-36 No implementado vs RF-37 Completo, ambos con “notifica” en el SRS, muestra **inconsistencia de criterio** de estado.
6. **Orden RF-55 intercalado:** detalle menor, pero en revisiones IEEE/830 se interpreta como falta de control documental.
7. **Riesgo de “definition of done” del curso:** si el criterio del entregable es “matriz honestamente alineada a implementación”, el documento actual **casi** llega; si el criterio es “evidencia de que cada RF Completo está verificado”, **no** llega sin reclasificar y sin tests faltantes (`attachments`, `visual-representations`, `support-requests`, `.../analysis`, filtros `verifiedOnly`/`similarExperience`, unavailable dates).

---

## Apéndice — Hechos de código usados (no inventados)

| Área | Qué hay | Qué no hay |
|---|---|---|
| Búsqueda | `POST /requests/{id}/search` en `projects.py`: oficio, zona, `unavailable_dates`, `verified_only`, `similar_experience` (conteo de evaluaciones), sort rating/price/availability/guarantee/proximity, recomendaciones `[:4]` con texto fijo | Ranking/explicación IA; experiencia “similar” semántica; colonias vecinas |
| Visual | `POST .../visual-representations`: persiste descripción + `reference_file_id`, `isTechnicalPlan=False` | Generación de imagen IA |
| Soporte | `POST .../support-requests`: `SupportCase` con `reason` | Resumen de conversación; cola admin; disparo por RF-15/19 |
| Analysis | `POST /changes/{id}/analysis`: plantilla + `isDecision: false` | Modelo de IA |
| Notificaciones | — | Canal email/push/SMS, job 24 h, aviso 72 h cierre |
| Tests presentes (nombres) | `test_auth`, `test_oauth`, `test_platform`, `test_providers`, `test_explore`, `test_geo`, `test_projects`, `test_contracting`, `test_privacy` | Tests dedicados a visual, support, attachments, analysis, unavailable dates, notificaciones |
| S09-A1 | `code_review-jesus.md`, `clasificacion_problemas-jesus.md`, `deuda_tecnica-jesus.md`, `refactorizacion-jesus.md`, `output_linter-jesus.txt` | UAT funcional de RF |

---

*Fin del feedback. No se modificó `matriz_trazabilidad.md`.*
