# Moodle Course Automator — Guía de API para Frontend

## Información General

| Dato | Valor |
|------|-------|
| Base URL | `http://localhost:8000` |
| Prefijo API | `/api/v1` |
| Documentación interactiva | `/docs` (Swagger UI) |
| Formato | JSON |
| CORS habilitado para | `http://localhost:5173`, `http://127.0.0.1:5173` |

---

## Flujo Principal de Uso

El flujo que debe seguir el frontend para personalizar un curso es:

1. **Verificar conexión** → `GET /api/v1/courses/health/check`
2. **Listar cursos** → `GET /api/v1/courses/`
3. **Escanear curso seleccionado** → `GET /api/v1/editor/scan/{course_id}`
4. **Llenar formulario** con los datos que el escaneo indica que son editables
5. **Previsualizar cambios** → `POST /api/v1/editor/preview`
6. **Aplicar cambios** → `POST /api/v1/editor/customize`

---

## Endpoints

### 1. Health Check — Verificar conexión con Moodle

**`GET /api/v1/courses/health/check`**

Verifica que el backend puede conectarse al servidor Moodle. Útil para mostrar un indicador de estado en la UI.

**Respuesta exitosa:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `status` | string | `"connected"` o `"error"` |
| `site_name` | string | Nombre del sitio Moodle |
| `username` | string | Usuario del token configurado |
| `user_id` | int | ID del usuario en Moodle |
| `moodle_version` | string | Versión de Moodle |

---

### 2. Listar Cursos

**`GET /api/v1/courses/`**

Retorna todos los cursos disponibles en la plataforma (excluye el curso del sitio ID=1).

**Respuesta:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `courses` | array | Lista de cursos |
| `total` | int | Total de cursos |

Cada curso contiene:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | int | ID único del curso en Moodle |
| `fullname` | string | Nombre completo del curso |
| `shortname` | string | Nombre corto |
| `categoryid` | int \| null | ID de categoría |
| `summary` | string \| null | Resumen HTML |
| `visible` | int | 1 = visible, 0 = oculto |

---

### 3. Obtener Curso por ID

**`GET /api/v1/courses/{course_id}`**

Retorna los datos de un curso específico. Útil para mostrar el detalle antes de editar.

**Parámetros de ruta:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `course_id` | int | ID del curso |

**Respuesta:** Mismo objeto de curso que en el listado.

**Errores:** `404` si el curso no existe.

---

### 4. Escanear Placeholders del Curso

**`GET /api/v1/editor/scan/{course_id}`**

**Este es el endpoint clave.** Analiza el HTML de la sección General del curso y detecta todos los elementos editables: placeholders (links/iframes), título, descripción, horario y bibliografía.

El frontend debe llamar a este endpoint para saber **qué campos mostrar** en el formulario de personalización.

**Parámetros de ruta:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `course_id` | int | ID del curso a escanear |

**Respuesta:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `course_id` | int | ID del curso escaneado |
| `section_name` | string | Nombre de la sección (generalmente "General") |
| `total_placeholders` | int | Cantidad de placeholders encontrados |
| `placeholders` | array | Lista detallada de placeholders |
| `schedule_found` | bool | Si existe una tabla de horario editable |
| `bibliography_found` | bool | Si existe una sección de bibliografía editable |
| `course_title` | string \| null | Título actual del curso dentro del HTML |
| `course_description` | string \| null | Descripción actual dentro del HTML |

Cada placeholder en el array contiene:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `element_type` | string | Tipo de elemento HTML (`"a"` o `"iframe"`) |
| `attribute` | string | Atributo donde está (`"href"` o `"src"`) |
| `placeholder_key` | string | Clave identificadora (ver tabla abajo) |
| `context_text` | string \| null | Texto visible del enlace (solo para `<a>`) |

**Placeholders conocidos del template:**

| Clave (`placeholder_key`) | Descripción | Elemento | Campo del formulario |
|---------------------------|-------------|----------|---------------------|
| `video-introductorio` | Video introductorio | iframe (src) | URL del video |
| `unirse-clases` | Enlace para unirse a clases | a (href) | URL de la sala de clases |
| `url-grabaciones` | Enlace de grabaciones | a (href) | URL de grabaciones |
| `perfil-docente` | Perfil del docente | iframe (src) | URL del perfil |
| `silabo` | Sílabo del curso | iframe (src) | URL del sílabo |
| `pea` | PEA del curso | iframe (src) | URL del PEA |
| `bibliografia` | Enlace de bibliografía | a (href) | URL de bibliografía |

---

### 5. Listar Placeholders Conocidos

**`GET /api/v1/editor/placeholders`**

Retorna la lista completa de placeholders, campos de texto y secciones editables que el sistema reconoce. Útil para construir el formulario de manera dinámica sin hardcodear las claves.

**Respuesta:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `placeholders` | array | Cada uno con `key` y `description` |
| `editable_text_fields` | array | Campos de texto editables (`course_title`, `course_description`) |
| `editable_sections` | array | Secciones complejas (`schedule`, `bibliography`) |

---

### 6. Preview — Previsualizar Cambios

**`POST /api/v1/editor/preview`**

Aplica las personalizaciones sobre el HTML **sin guardarlo en Moodle**. Retorna el HTML resultante para que el frontend lo muestre como vista previa.

**Body (JSON):**

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `course_id` | int | **Sí** | ID del curso |
| `video_introductorio` | string | No | URL del video introductorio |
| `unirse_clases` | string | No | URL para unirse a clases |
| `url_grabaciones` | string | No | URL de grabaciones |
| `perfil_docente` | string | No | URL del perfil del docente |
| `silabo` | string | No | URL del sílabo |
| `pea` | string | No | URL del PEA |
| `bibliografia_url` | string | No | URL de bibliografía (link simple) |
| `course_title` | string | No | Nuevo título del curso |
| `course_description` | string | No | Nueva descripción del curso |
| `schedule` | objeto | No | Datos del horario (ver estructura abajo) |
| `bibliography` | objeto | No | Datos de bibliografía (ver estructura abajo) |

> Solo enviar los campos que se quieran modificar. Los campos `null` o ausentes se ignoran.

**Estructura del campo `schedule`:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `days_columns` | array de strings | Columnas de días. Ej: `["Lunes", "Martes", "Miércoles", "Jueves"]` |
| `entries` | array | Filas del horario |

Cada entrada de `entries`:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `subject_name` | string | Nombre de la asignatura |
| `days` | objeto | Horarios por día. Ej: `{"Lunes": "18h30 – 19h30", "Martes": "20h00 – 21h00"}` |

**Estructura del campo `bibliography`:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `entries` | array | Lista de entradas bibliográficas |

Cada entrada de `entries`:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `text` | string | Texto visible de la referencia |
| `url` | string | URL del recurso bibliográfico |

**Respuesta:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `success` | bool | Si se procesó correctamente |
| `course_id` | int | ID del curso |
| `message` | string | Mensaje descriptivo |
| `total_replacements` | int | Cantidad de cambios aplicados |
| `details` | array | Detalle de cada cambio realizado |
| `processed_html` | string | **El HTML resultante completo** (para renderizar como preview) |

Cada detalle en `details`:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `field` | string | Qué campo se modificó |
| `old_value` | string | Valor anterior |
| `new_value` | string | Nuevo valor |

---

### 7. Customize — Aplicar Cambios en Moodle

**`POST /api/v1/editor/customize`**

**Mismo body y estructura que `/preview`**, pero este endpoint **sí guarda los cambios** en Moodle. Actualiza el HTML de la sección General del curso directamente en la plataforma.

**Body:** Idéntico al de `/preview` (ver sección anterior).

**Respuesta:** Idéntica estructura que `/preview`, pero:
- El campo `processed_html` viene en `null` (ya que se guardó en Moodle).
- El campo `message` confirma que los cambios fueron guardados.

**Errores posibles:**
- `400`: Si Moodle rechaza la actualización (permisos, curso no existe, etc.)
- `500`: Error interno del servidor

---

### 8. Duplicar Curso

**`POST /api/v1/courses/duplicate`**

Crea una copia completa de un curso existente en Moodle.

**Body (JSON):**

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `source_course_id` | int | **Sí** | ID del curso origen |
| `new_fullname` | string | **Sí** | Nombre completo del nuevo curso |
| `new_shortname` | string | **Sí** | Nombre corto del nuevo curso |
| `category_id` | int | No | ID de la categoría destino |
| `visible` | int | No | Visibilidad inicial (0 = oculto, 1 = visible). Default: 0 |
| `new_teacher_profile_url` | string | No | URL del perfil del docente para reemplazar |

**Respuesta:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `success` | bool | Si la duplicación fue exitosa |
| `new_course_id` | int | ID del nuevo curso creado |
| `new_course_url` | string | URL directa para acceder al nuevo curso en Moodle |
| `message` | string | Mensaje descriptivo |
| `links_updated` | int | Cantidad de links actualizados durante la duplicación |

---

### 9. Obtener Contenido del Curso

**`GET /api/v1/courses/{course_id}/contents`**

Retorna las secciones y módulos completos de un curso. Útil para inspección o debugging.

**Respuesta:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `course_id` | int | ID del curso |
| `sections` | array | Lista de secciones con sus módulos |

---

## Endpoints de Utilidad

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/` | GET | Info básica de la API |
| `/health` | GET | Health check del backend (no verifica Moodle) |
| `/docs` | GET | Swagger UI interactivo |

---

## Flujo Recomendado para la Vista Principal

### Paso 1: Selector de curso
1. Llamar a `GET /api/v1/courses/` para obtener la lista.
2. Mostrar un dropdown o tabla con los cursos.
3. Al seleccionar uno, llamar a `GET /api/v1/editor/scan/{id}`.

### Paso 2: Formulario de personalización
Con la respuesta del scan, construir dinámicamente el formulario:

- **Si `placeholders` tiene elementos** → Mostrar un input de URL por cada placeholder encontrado.
- **Si `course_title` existe** → Mostrar un input de texto prellenado con el título actual.
- **Si `course_description` existe** → Mostrar un textarea prellenado con la descripción actual.
- **Si `schedule_found` es `true`** → Mostrar la sección de horario con inputs para asignaturas y días.
- **Si `bibliography_found` es `true`** → Mostrar la sección de bibliografía con inputs para texto + URL por cada entrada.

### Paso 3: Preview
Al hacer click en "Previsualizar":
1. Armar el JSON solo con los campos que el usuario llenó.
2. Enviar a `POST /api/v1/editor/preview`.
3. Renderizar `processed_html` en un iframe o div con `innerHTML`.
4. Mostrar la lista de `details` como resumen de cambios.

### Paso 4: Aplicar
Al hacer click en "Guardar en Moodle":
1. Enviar el mismo JSON a `POST /api/v1/editor/customize`.
2. Verificar `success === true`.
3. Mostrar mensaje de confirmación con `total_replacements` cambios aplicados.

---

## Flujo de Duplicación + Personalización

Caso de uso completo: duplicar un curso base y personalizarlo para un nuevo docente/período.

1. `POST /api/v1/courses/duplicate` → Obtener `new_course_id`.
2. `GET /api/v1/editor/scan/{new_course_id}` → Escanear el curso duplicado.
3. El usuario llena el formulario.
4. `POST /api/v1/editor/preview` → Vista previa.
5. `POST /api/v1/editor/customize` → Guardar cambios.

---

## Notas Importantes

- **Todos los campos de personalización son opcionales.** Solo se modificarán los campos que se envíen con valor (no null). Esto permite actualizaciones parciales.
- **El HTML del template está en la sección General** (sección 0) del curso, dentro del campo `summary` de la sección, no en un módulo independiente.
- **Los placeholders son textos fijos** (`video-introductorio`, `unirse-clases`, etc.) que se encuentran como valores de `href` o `src` en el HTML. Al personalizarlos, se reemplazan por URLs reales.
- **El horario es una tabla HTML** dentro de un modal con `id="cronograma"`. Se reconstruye completamente al actualizar (no se editan celdas individuales).
- **La bibliografía es una lista `<ul>`** dentro de un modal con `id="biblio"`. También se reconstruye por completo.
- **CORS** está configurado para `localhost:5173` (Vite default). Si el frontend corre en otro puerto, agregar el origen en la configuración del backend.
- **El campo `processed_html`** del preview contiene HTML limpio (sin wrappers `<html>` o `<body>`), listo para renderizar directamente.
