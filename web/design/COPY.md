# UnCalificado — Microcopy canónico (es-MX)

Español de México · pesos MXN · **hora del centro** · de **tú**. Voz: un maestro de obra que explica con claridad. Concreto, breve, sin adornos.

## 0. Reglas

1. **Verbo + objeto** en botones. Nunca “OK”, “Aceptar” suelto, “Enviar”, “Sí/No”.
2. **Errores**: qué pasó → por qué → cómo arreglarlo. Sin culpar a la persona. Sin humor.
3. **Vacíos**: qué falta → por qué conviene llenarlo → acción.
4. Fechas: `sáb 7 nov, 9:00 a. m.` (hora del centro cuando importe: “9:00 a. m. (hora del centro)”). Dinero: `$1,250.00 MXN`.
5. Un término por concepto (glosario abajo). No alternar sinónimos.
6. Prohibido: “empoderar”, “soluciones integrales”, “experiencia”, “ecosistema”, “¡Oops!”, “Lo sentimos mucho”, signos de exclamación en errores.
7. Mayúsculas de sentencia. MAYÚSCULAS solo las aplica el CSS (H1/H2, etiquetas, estados): **escribe el copy en caja normal**.
8. Cuando hay un número, va separado del texto (`3 propuestas`, no “Tienes 3 nuevas propuestas” si se traduce o cambia).

## 1. Glosario (usar siempre estos términos)

| Concepto | Usa | No uses |
|---|---|---|
| Quien contrata | **cliente** | usuario, comprador |
| Quien presta el servicio | **proveedor** (trabajador independiente u organización) | técnico, contratista, vendor |
| Trabajo a realizar | **proyecto** (antes de confirmar, “borrador”) | ticket, pedido, orden, solicitud* |
| Giro | **oficio** | categoría, servicio |
| Oferta del proveedor | **propuesta** | cotización formal, bid |
| Pedir precio | **cotización** (acción del cliente: “Solicitar cotización”) | presupuesto |
| Lugar aproximado | **zona aproximada** | ubicación general |
| Dirección | **domicilio** | dirección completa (al hablar de privacidad) |
| Revisión de documentos | **verificación** / **verificado** | aprobado, KYC |
| Opinión tras concluir | **calificación** | review, rating, estrellas |
| Duración de la garantía | **garantía** (en días) | warranty |
| Datos personales | **ARCO**: acceso, rectificación, cancelación y oposición | GDPR, “borrar mis datos” |

\* “Solicitud” se acepta solo como “solicitud de cotización” y en los datos técnicos del API (`service_requests`); en pantalla el objeto es **proyecto**.

## 2. Marca y eslogan

- **Eslogan:** Quien sí sabe, a la vuelta de tu casa.
- **Descriptor corto (meta/descripción):** Contrata oficios de confianza en México. Tú decides qué dato compartes; tu domicilio exacto solo lo ve quien autorices.
- **Aviso de pagos** (visible en registro, propuesta y pie): UnCalificado no cobra ni procesa pagos. El pago lo acuerdas directamente con el proveedor.

## 2b. Índice público

| Elemento | Copy |
|---|---|
| Titular | Quien sí sabe, a la vuelta de tu casa. |
| Apoyo | Mira calificados y fotos de obra terminada sin crear cuenta. El domicilio exacto no se publica. Para escribirle a alguien, entra. |
| Sección fotos | Fotos de proyectos realizados |
| Sección populares | Los más populares |
| Contacto sin cuenta | Entra para contactar |
| Contacto con cuenta | Solicitar cotización |
| Zona en foto | Zona aproximada: {colonia} |
| Pie | Tu domicilio exacto nunca se publica. |

## 2c. Zona de descubrimiento (cuenta)

| Elemento | Copy |
|---|---|
| Nav | Cuenta |
| Título | A quién ves cerca |
| Apoyo | El índice solo muestra calificados dentro de esta distancia. Puedes cambiarla cuando quieras. Tu calle y número se quedan contigo. |
| Radar con zona | Hasta {n} km de {alcaldía} |
| Radar vacío | Elige alcaldía y distancia |
| Explicación | Así te mostramos calificados cerca, como en una app de citas: tú fijas el punto y hasta dónde te mueves. Usamos la alcaldía, no tu calle. |
| Campo alcaldía | ¿En qué alcaldía te mueves? · ayuda: El domicilio exacto nunca se publica. |
| Campo distancia | Distancia máxima · ayuda: {n} km desde el centro de la alcaldía |
| Botón | Guardar zona |
| Cargando | Guardando cambios… |
| Éxito | Cambios guardados. |
| Enlace al índice | Ver calificados de tu zona |
| Índice con zona | Hasta {n} km de {alcaldía}. Cambiar zona |
| Índice sin zona (sesión) | Elige tu alcaldía y distancia para ver calificados cerca. Definir mi zona |
| Vista previa invitado | Vista previa a {n} km de {alcaldía}. Guárdala en tu cuenta |
| Error sin alcaldía | Elige una alcaldía para ver calificados cerca. |
| Vacío con radio | No hay calificados a menos de {n} km de {alcaldía}. |

## 3. Entrar (login)

| Elemento | Copy |
|---|---|
| Título | Entrar |
| Titular del panel | Entra y sigue con tu proyecto. |
| Apoyo del panel | Tu domicilio exacto solo lo ve quien tú autorices. |
| Campo correo | Correo electrónico · placeholder `nombre@correo.mx` |
| Campo contraseña | Contraseña |
| Mostrar/ocultar | Mostrar · Ocultar |
| Botón | Entrar |
| Enlace | Olvidé mi contraseña |
| Alta | ¿Primera vez en UnCalificado? Crea tu cuenta |
| OAuth | Continuar con Google · Continuar con Facebook · Continuar con TikTok |
| OAuth apoyo | Al continuar con Google, Facebook o TikTok aceptas el aviso de privacidad y declaras ser mayor de edad. |
| OAuth divisor | o con tu cuenta de siempre |
| OAuth no listo | El acceso con {red} aún no está listo. Entra con correo y contraseña. |
| Cargando | Entrando… |
| Sesión cerrada | Cerraste sesión. Vuelve cuando quieras. |
| Sesión vencida | Tu sesión venció. Entra de nuevo para seguir donde ibas. |

**Errores de login**
- Credenciales: **Correo o contraseña incorrectos.** Revísalos e intenta de nuevo. Si no recuerdas tu contraseña, puedes cambiarla.
- Correo vacío: Escribe tu correo electrónico.
- Contraseña vacía: Escribe tu contraseña.
- Cuenta bloqueada temporalmente *(solo si el backend lo implementa)*: Demasiados intentos. Espera unos minutos y vuelve a intentar.
- Red: No pudimos conectar. Revisa tu internet y vuelve a intentar.

## 4. Crear cuenta (registro)

| Elemento | Copy |
|---|---|
| Título | Crea tu cuenta |
| Pregunta de rol | ¿Qué vienes a hacer? |
| Opción cliente | **Necesito un oficio** · Cuento qué hace falta y elijo a quién contratar. |
| Opción proveedor | **Ofrezco un oficio** · Como trabajador independiente o con mi organización. |
| Nombre | Nombre completo · ayuda: Como aparece en tu INE |
| Correo | Correo electrónico · ayuda: Aquí te avisamos de citas y propuestas. |
| Contraseña | Contraseña · ayuda: Mínimo 10 caracteres. Una frase larga funciona mejor que un símbolo raro. |
| Estado | Estado |
| Aviso de privacidad | Leí el [aviso de privacidad] · apoyo: Tu domicilio exacto nunca se publica. |
| Botón | Crear cuenta |
| Cargando | Creando tu cuenta… |
| Éxito | Listo, ya tienes cuenta. |
| Alta de proveedor, paso 2 | ¿Trabajas solo o con una organización? → **Trabajo por mi cuenta** / **Represento a una organización** |
| Oficios del proveedor | Elige tus oficios. Puedes cambiarlos después. |

**Errores de registro**
- Correo repetido: Ese correo ya tiene una cuenta. Entra o cambia tu contraseña.
- Correo inválido: Falta el dominio del correo. Ejemplo: ramon@correo.mx
- Contraseña corta: Tu contraseña necesita al menos 10 caracteres. Te faltan {n}.
- Aviso sin marcar: Marca que leíste el aviso de privacidad para crear tu cuenta.
- Nombre vacío: Escribe tu nombre completo.

## 5. Capturar un proyecto

| Elemento | Copy |
|---|---|
| Título | Cuéntanos qué necesitas |
| Resultado esperado | ¿Qué quieres que quede listo? · ayuda: Ej. “Que no gotee el lavabo del baño de visitas.” |
| Oficio | ¿Qué oficio necesitas? |
| Zona | ¿En qué colonia estás? · ayuda: Con la colonia basta. Tu calle y número se quedan contigo. |
| Fecha deseada | ¿Para cuándo lo quieres? · opcional · ayuda: Si no tienes fecha, déjalo vacío. |
| Descripción | Detalles · opcional · ayuda: Medidas, materiales, desde cuándo pasa. No pongas teléfonos: los quitamos. |
| Fotos | Agregar fotos o video · ayuda: JPG, PNG o MP4. Cuida que no salga tu número de casa. |
| Opción asistente | Ayúdame a armarlo |
| Opción manual | Prefiero llenarlo yo |
| Resumen | Revisa tu proyecto antes de confirmarlo |
| Botón confirmar | Confirmar proyecto |
| Botón borrador | Guardar borrador |
| Aviso del asistente | El asistente solo orienta: resume lo que contaste, avisa qué datos faltan y qué riesgos ver. **No decide por ti** ni elige proveedor. |
| Teléfono detectado | Quitamos un número de teléfono de tu texto. Para hablar con el proveedor usa los mensajes de UnCalificado. |

## 6. Estados de proyecto (etiquetas y explicación)

| Código | Etiqueta | Explicación |
|---|---|---|
| `BORRADOR` | Borrador | Lo estás armando. Solo tú lo ves. |
| `CONFIRMADA` | Confirmada | Revisaste el resumen. Ya puede recibir propuestas. |
| `PROGRAMADO` | Programado | Cliente y proveedor confirmaron la cita. |
| `EN_PROCESO` | En proceso | El proveedor está trabajando en el sitio. |
| `TERMINADO` | Terminado | El proveedor avisó que acabó. Falta tu visto bueno. |
| `CONCLUIDO` | Concluido | Cerrado. Ya puedes dejar tu calificación. |

**Verificación de proveedor:** `DECLARADA` Declarada · `PENDIENTE` En revisión · `VERIFICADA` Verificada · `RECHAZADA` Rechazada · `RETIRADA` Retirada.
**Cita:** `PENDIENTE` Falta confirmar · `CONFIRMADA` Confirmada · `EXPIRADA` Venció · `CANCELADA` Cancelada.
**Propuesta:** `ENVIADA` Enviada · `ACEPTADA` Aceptada · `NEGOCIACION` En negociación · `RECHAZADA` Rechazada · `EXPIRADA` Venció.

## 7. Vacíos

| Dónde | Título | Texto | Botón |
|---|---|---|---|
| Proyectos (cliente) | Aún no tienes proyectos | Cuéntanos qué hace falta en tu casa. Con tu colonia y un par de datos, los proveedores verificados de tu zona pueden mandarte propuesta. | Crear mi primer proyecto · *Ver oficios disponibles* |
| Búsqueda sin resultados | No hay proveedores con esos filtros | Prueba quitando “Solo verificados” o ampliando la zona. | Limpiar filtros |
| Propuestas (cliente) | Todavía no llegan propuestas | Los proveedores de tu zona van a ver tu proyecto. Te avisamos por correo cuando llegue una. | Ver mi proyecto |
| Solicitudes (proveedor) | No tienes solicitudes nuevas | Cuando un cliente de tu zona pida tu oficio, te aparece aquí. Mientras, mantén tu agenda al día. | Revisar mi agenda |
| Agenda | No hay citas esta semana | Cuando cliente y proveedor confirmen una cita, se anota aquí. | Ver proyectos |
| Mensajes | Aún no hay mensajes | Los mensajes se abren cuando hay una propuesta en el proyecto. | — |
| Calificaciones (proveedor) | Todavía no tienes calificaciones | Aparecen cuando un cliente concluye un proyecto contigo. | Ver mis proyectos |
| Documentos por verificar (admin) | No hay documentos pendientes | Todo lo recibido ya tiene respuesta. | Ver historial |
| Solicitudes ARCO (admin) | Sin solicitudes ARCO abiertas | Aquí llegan las solicitudes de acceso, rectificación, cancelación y oposición. | — |

## 8. Privacidad del domicilio (RF-52)

| Contexto | Copy |
|---|---|
| Etiqueta zona | Zona aproximada |
| Etiqueta domicilio | Domicilio exacto |
| Etiqueta oculto | Sin ubicación visible |
| Estado | Privado · Autorizado por ti |
| Zona aproximada (cliente) | Esto es lo que ven los proveedores mientras revisan tu solicitud. Tu calle y número se quedan contigo. |
| Zona aproximada (proveedor) | Zona aproximada del cliente. El domicilio exacto se comparte solo si el cliente lo autoriza. |
| Domicilio autorizado (cliente) | Compartido solo con **{proveedor}** para el proyecto **{folio}**. |
| Domicilio autorizado (proveedor) | El cliente autorizó que veas su domicilio para este proyecto. Úsalo solo para llegar a la cita. |
| Oculto | Todavía no hay zona para mostrar. Cuando captures tu colonia, aparecerá aquí como zona aproximada. |
| Antes de autorizar (pregunta) | ¿Compartir tu domicilio exacto con **{proveedor}**? |
| Antes de autorizar (explicación) | Lo verá solo para este proyecto. Nadie más lo ve. |
| Botón autorizar | Compartir mi domicilio |
| Botón rechazar | No compartir todavía |
| Pie de formularios con dirección | Tu domicilio exacto nunca se publica. |
| Mensaje con teléfono | Quitamos el número de teléfono. Mantén la conversación dentro de UnCalificado. → el texto guardado muestra `[teléfono omitido]`. |
| Admin: dato oculto | Dato privado. Solo se muestra con autorización del cliente. |

## 9. CTA canónicos

| Acción | Etiqueta |
|---|---|
| Iniciar | Crear mi primer proyecto · Crear cuenta · Entrar |
| Buscar | Buscar proveedores · Ver proveedores de tu zona |
| Pedir precio | Solicitar cotización |
| Proveedor responde | Aceptar proyecto · Pedir cambios · Rechazar proyecto |
| Cliente decide | Aceptar propuesta · Pedir cambios · Rechazar propuesta |
| Cita | Confirmar cita · Proponer otra hora |
| Avance | Marcar como terminado · Volver a “En proceso” · Concluir proyecto |
| Opinión | Dejar mi calificación |
| Guardar | Guardar cambios · Guardar borrador |
| Cancelar edición | Seguir editando (no “Cancelar”) |
| Admin | Revisar documento · Verificar documento · Rechazar documento · Responder solicitud ARCO |
| Destructivo | Eliminar mi cuenta · Eliminar borrador (siempre nombrar el objeto) |
| Navegar | Ver detalle · Ver historial · Volver a mis proyectos |
| Cargando | Enviando solicitud… · Guardando cambios… · Buscando proveedores… |

## 10. Errores (plantillas)

| Situación | Copy |
|---|---|
| Campo obligatorio | Escribe {qué falta}. |
| Formato | {Campo} necesita {formato}. Ejemplo: {ejemplo} |
| Red | No pudimos conectar. Revisa tu internet y vuelve a intentar. |
| Servidor (500) | Algo falló de nuestro lado. Ya lo estamos revisando. Intenta de nuevo en unos minutos. |
| Sin permiso (403) | No tienes acceso a {cosa}. Si crees que es un error, escríbenos desde Ayuda. |
| No existe (404) | No encontramos {cosa}. Puede que ya no esté disponible. · Volver a mis proyectos |
| Conflicto de horario (409) | Esa hora ya está ocupada. Elige otra y vuelve a confirmar. |
| Transición inválida | Este proyecto no puede pasar a “{estado}” todavía. Primero debe estar “{estado previo}”. |
| Archivo | Ese archivo no se puede subir. Usa JPG, PNG o MP4. |
| Archivo grande | El archivo pesa más de {n} MB. Reduce su tamaño y vuelve a subirlo. |
| Sesión | Tu sesión venció. Entra de nuevo para seguir. |
| Duplicado de calificación | Ya calificaste este proyecto. |

## 11. Confirmaciones y éxito (breves)

- Proyecto confirmado → **Proyecto confirmado.** Los proveedores de tu zona ya pueden mandarte propuesta.
- Cita confirmada → **Cita confirmada** para el {fecha} (hora del centro).
- Propuesta aceptada → **Propuesta aceptada.** Ahora agenden la cita.
- Cambios guardados → **Cambios guardados.**
- Documento enviado → **Recibimos tu documento.** Lo revisamos y te avisamos por correo.
- Verificado → **Documento verificado.**
- Calificación enviada → **Gracias. Tu calificación ya cuenta.**
- Solicitud ARCO registrada → **Registramos tu solicitud.** Folio {folio}. Te respondemos por correo.

## 12. Privacidad, ARCO y aviso legal (pie)

- Pie: UnCalificado no cobra ni procesa pagos. · Tu domicilio exacto nunca se publica. · Aviso de privacidad · Derechos ARCO
- Enlace de ARCO: **Ejercer mis derechos ARCO**
- Texto de ARCO: Puedes pedir **acceso**, **rectificación**, **cancelación** u **oposición** sobre tus datos. Tu solicitud se registra con folio y te respondemos por correo.
- Tipos: Acceso (Quiero ver mis datos) · Rectificación (Quiero corregir un dato) · Cancelación (Quiero que borren mis datos) · Oposición (No quiero que usen mis datos para esto)
- Confirmación antes de eliminar cuenta: **¿Eliminar tu cuenta?** Se borran tus datos personales y no se puede deshacer. *[Texto legal sobre qué se conserva: pendiente de definir con el equipo de privacidad.]* → **Eliminar mi cuenta** · *Conservar mi cuenta*

## 13. Accesibilidad del copy

- Enlaces con sentido propio: “Ver precios de plomería”, no “Haz clic aquí”.
- Botones de ícono: `aria-label` con verbo (“Cerrar”, “Mostrar contraseña”).
- Textos alternativos describen información: “Zona aproximada de 1 km en Col. Narvarte”, no “mapa”.
- Estados dichos con palabras, además del color y la forma: “Estado: Programado”.
- Rutas de paso: “Paso actual: En proceso”, “Completado: Programado”.
