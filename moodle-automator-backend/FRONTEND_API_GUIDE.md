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

1. **Verificar conexión** → `GET /api/v1/courses/health/check`
2. **Listar cursos** → `GET /api/v1/courses/`
3. **Escanear curso seleccionado** → `GET /api/v1/editor/scan/{course_id}`
4. **Llenar formulario** con los datos editables detectados
5. **Previsualizar cambios** → `POST /api/v1/editor/preview`
6. **Aplicar cambios** → `POST /api/v1/editor/customize`

---

## Endpoints

### 1. Health Check

**`GET /api/v1/courses/health/check`**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `status` | string | `"connected"` o `"error"` |
| `site_name` | string | Nombre del sitio Moodle |
| `username` | string | Usuario del token configurado |
| `user_id` | int | ID del usuario |
| `moodle_version` | string | Versión de Moodle |

---

### 2. Listar Cursos

**`GET /api/v1/courses/`**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `courses` | array | Lista de cursos |
| `total` | int | Total de cursos |

Cada curso:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | int | ID único del curso |
| `fullname` | string | Nombre completo |
| `shortname` | string | Nombre corto |
| `categoryid` | int \| null | ID de categoría |
| `summary` | string \| null | Resumen HTML |
| `visible` | int | 1 = visible, 0 = oculto |

---

### 3. Obtener Curso por ID

**`GET /api/v1/courses/{course_id}`**

Mismo objeto de curso que en el listado. `404` si no existe.

---

### 4. Escanear Placeholders del Curso

**`GET /api/v1/editor/scan/{course_id}`**

Analiza el HTML de la sección General y detecta todos los elementos editables.

**Respuesta:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `course_id` | int | ID del curso escaneado |
| `section_name` | string | Nombre de la sección |
| `total_placeholders` | int | Cantidad de placeholders encontrados |
| `placeholders` | array | Lista detallada de placeholders |
| `schedule_found` | bool | Si existe tabla de horario editable |
| `bibliography_found` | bool | Si existe sección de bibliografía editable |
| `course_title` | string \| null | Título actual del curso dentro del HTML |
| `course_description` | string \| null | Descripción actual dentro del HTML |
| `existing_blocks` | array | **Bloques de contenido ya existentes** (presentaciones, lectura, videos) con su contenido extraído. Ver [sección detallada](#existing_blocks). |
| `existing_schedule` | object \| null | **Datos actuales del horario** ya configurado (si existe). Ver [estructura](#existing_schedule). |
| `existing_bibliography` | object \| null | **Datos actuales de bibliografía** ya configurada (si existe). Ver [estructura](#existing_bibliography). |
| `template_source` | string | `"label"` o `"section_summary"` — dónde vive el template |
| `can_save` | bool | `true` si el template se puede editar vía API |
| `save_hint` | string \| null | Mensaje si `can_save` es `false` |

Cada placeholder:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `element_type` | string | `"a"` o `"iframe"` |
| `attribute` | string | `"href"` o `"src"` |
| `placeholder_key` | string | Clave identificadora (ver tabla abajo) |
| `context_text` | string \| null | Texto visible del enlace (solo para `<a>`) |
| `current_value` | string \| null | **Valor actual** del atributo. Si empieza con `http`, ya fue configurado previamente. Si coincide con `placeholder_key`, aún no se ha reemplazado. |

**Placeholders conocidos del template:**

| Clave (`placeholder_key`) | Descripción | Elemento |
|---------------------------|-------------|----------|
| `video-introductorio` | Video introductorio | iframe (src) |
| `unirse-clases` | Enlace para unirse a clases | a (href) |
| `url-grabaciones` | Enlace de grabaciones | a (href) |
| `perfil-docente` | Perfil del docente | iframe (src) |
| `silabo` | Sílabo del curso | iframe (src) |
| `pea` | PEA del curso | iframe (src) |
| `bibliografia` | Enlace de bibliografía | a (href) |

#### <a id="existing_blocks"></a> Estructura de `existing_blocks`

Cada elemento del array describe un bloque de contenido detectado en **cualquier sección** del curso:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `block_type` | string | `"presentations"`, `"reading"` o `"videos"` |
| `label_cmid` | int | Course module ID del label |
| `label_instance_id` | int | Instance ID del label (para update) |
| `section_id` | int | ID de la sección donde vive el bloque |
| `section_number` | int | Número de sección (0=General, 1=Semana 1, …) |
| `collapse_label` | string | Texto del botón collapse del bloque |

**Campos específicos por tipo de bloque:**

**Presentaciones** (`block_type == "presentations"`):

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `presentations` | array | `[{title, url}]` — cada presentación con su iframe |
| `presentation_objective` | string \| null | Objetivo de aprendizaje del bloque |

**Lectura** (`block_type == "reading"`):

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `main_reading` | object | `{title, author, url, summary}` — lectura principal |
| `suggested_readings` | array \| null | `[{title, author, url}]` — lecturas sugeridas |
| `reading_section_title` | string \| null | Título h4 (ej. "Lectura principal") |
| `reading_button_text` | string \| null | Texto del botón (ej. "Ver lectura") |
| `reading_suggested_title` | string \| null | Título de sugeridas (ej. "Lecturas sugeridas") |

**Videos** (`block_type == "videos"`):

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `videos` | array | `[{title, url}]` — cada video con su iframe |
| `videos_summary` | string \| null | Texto resumen de los videos |

**Ejemplo de respuesta `existing_blocks`:**

```json
[
  {
    "block_type": "presentations",
    "label_cmid": 4521,
    "label_instance_id": 891,
    "section_id": 1692,
    "section_number": 1,
    "collapse_label": "Introducción a Python",
    "presentations": [
      { "title": "Introducción a Python", "url": "https://canva.com/slide1" },
      { "title": "POO en Python", "url": "https://canva.com/slide2" }
    ],
    "presentation_objective": "Comprender las bases de Python"
  },
  {
    "block_type": "reading",
    "label_cmid": 4522,
    "label_instance_id": 892,
    "section_id": 1692,
    "section_number": 1,
    "collapse_label": "Lectura",
    "main_reading": {
      "title": "Clean Code",
      "author": "Robert C. Martin",
      "url": "https://example.com/clean-code",
      "summary": "Un libro sobre código limpio."
    },
    "suggested_readings": [
      { "title": "Refactoring", "author": "Martin Fowler", "url": "https://example.com/refactoring" }
    ],
    "reading_section_title": "Lectura principal",
    "reading_button_text": "Ver lectura",
    "reading_suggested_title": "Lecturas sugeridas"
  },
  {
    "block_type": "videos",
    "label_cmid": 4523,
    "label_instance_id": 893,
    "section_id": 1692,
    "section_number": 1,
    "collapse_label": "Video",
    "videos": [
      { "title": "Tutorial Django", "url": "https://youtube.com/django" }
    ],
    "videos_summary": "Videos introductorios sobre frameworks web"
  }
]
```

#### <a id="existing_schedule"></a> Estructura de `existing_schedule`

Si el horario ya fue configurado, devuelve los datos actuales:

```json
{
  "days_columns": ["Lunes", "Martes", "Miércoles", "Jueves"],
  "entries": [
    {
      "subject_name": "Programación I",
      "days": { "Lunes": "18h30 – 19h30", "Martes": "20h00 – 21h00" }
    }
  ]
}
```

> Si es `null`, el horario no ha sido configurado. Usar las columnas por defecto.

#### <a id="existing_bibliography"></a> Estructura de `existing_bibliography`

Si la bibliografía ya fue configurada:

```json
{
  "entries": [
    { "text": "Clean Code - Robert C. Martin", "url": "https://example.com/clean-code" },
    { "text": "Refactoring - Martin Fowler", "url": "https://example.com/refactoring" }
  ]
}
```

> Si es `null`, la bibliografía no ha sido configurada.

---

### 4b. Actualizar Metadatos del Curso

**`PUT /api/v1/courses/{course_id}`**

Actualiza campos del curso en Moodle (idnumber, fullname, shortname).

#### Body (JSON)

```json
{
  "idnumber": "PROG-2026-A",
  "fullname": "Programación I - 2026",
  "shortname": "prog1-2026a"
}
```

> Todos los campos son opcionales. Solo se actualizan los enviados.

#### Respuesta

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `success` | bool | `true` si se actualizó correctamente |
| `course_id` | int | ID del curso actualizado |
| `updated_fields` | array | Lista de campos que se actualizaron |

---

### 5. Listar Placeholders Conocidos

**`GET /api/v1/editor/placeholders`**

Retorna todos los placeholders y campos editables. Útil para construir el formulario dinámicamente.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `placeholders` | array | Cada uno con `key` y `description` |
| `editable_text_fields` | array | Campos de texto (`course_title`, `course_description`) |
| `editable_sections` | array | Secciones complejas (`schedule`, `bibliography`) |

---

### 6. Preview — Previsualizar Cambios

**`POST /api/v1/editor/preview`**

Aplica las personalizaciones **sin guardar en Moodle**. Retorna el HTML resultante por sección.

#### Body (JSON)

```json
{
  "course_id": 125,
  "sections": [
    {
      "section_id": 1692,
      "section_number": 1,

      "video_introductorio": "https://...",
      "unirse_clases": "https://...",
      "url_grabaciones": "https://...",
      "perfil_docente": "https://...",
      "silabo": "https://...",
      "pea": "https://...",
      "bibliografia_url": "https://...",

      "course_title": "Nuevo título",
      "course_description": "Nueva descripción",
      "schedule": { ... },
      "bibliography": { ... },

      "presentations": [
        { "title": "Presentación 1", "url": "https://canva.com/..." },
        { "title": "Presentación 2", "url": "https://canva.com/..." }
      ],
      "presentation_objective": "Objetivo de aprendizaje...",

      "main_reading": {
        "title": "Título del libro",
        "author": "Nombre del autor",
        "url": "https://...",
        "summary": "Resumen del libro..."
      },
      "suggested_readings": [
        { "title": "Libro sugerido 1", "author": "Autor", "url": "https://..." },
        { "title": "Libro sugerido 2", "author": "Autor", "url": "https://..." }
      ],
      "reading_collapse_label": "Lectura",
      "reading_section_title": "Lectura principal",
      "reading_button_text": "Ver lectura",
      "reading_suggested_title": "Lecturas sugeridas",

      "videos": [
        { "title": "Video 1", "url": "https://drive.google.com/..." },
        { "title": "Video 2", "url": "https://drive.google.com/..." }
      ],
      "videos_summary": "Resumen de los videos...",

      "existing_labels": {
        "presentations": { "label_cmid": 4521, "label_instance_id": 891 },
        "reading": { "label_cmid": 4522, "label_instance_id": 892 },
        "videos": { "label_cmid": 4523, "label_instance_id": 893 }
      }
    }
  ]
}
```

> Solo enviar los campos que se quieran modificar. Los campos `null` o ausentes se ignoran.

#### Campos del objeto `section`

**Placeholders del summary (reemplazos en el HTML de la sección):**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `section_id` | int | **Requerido.** ID de la sección en Moodle |
| `section_number` | int | Número de sección (default: 0) |
| `video_introductorio` | string | URL del video introductorio (iframe) |
| `unirse_clases` | string | URL de la sala de clases virtual (link) |
| `url_grabaciones` | string | URL de grabaciones (link) |
| `perfil_docente` | string | URL del perfil del docente (iframe) |
| `silabo` | string | URL del sílabo (iframe) |
| `pea` | string | URL del PEA (iframe) |
| `bibliografia_url` | string | URL simple de bibliografía (link) |
| `course_title` | string | Nuevo texto del `<h1>` dentro del HTML |
| `course_description` | string | Nuevo texto del `<p>` bajo el título |
| `schedule` | objeto | Datos del horario (ver abajo) |
| `bibliography` | objeto | Datos de bibliografía detallada (ver abajo) |

**Bloque de Presentaciones** — se crea como label independiente en Moodle:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `presentations` | array | Lista de dicts `{title, url}`. **Soporta múltiples.** Cada uno genera su propio iframe dentro del bloque. |
| `presentation_objective` | string | Objetivo de aprendizaje (aparece al pie del bloque) |

**Bloque de Lectura** — se crea como label independiente en Moodle:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `main_reading` | dict | Lectura principal: `{title, author, url, summary}` |
| `suggested_readings` | array | Lecturas sugeridas: lista de `{title, author, url}`. **Soporta múltiples.** |
| `reading_collapse_label` | string | Texto del botón collapse. Default: `"Lectura"`. Ej: `"Guia de apoyo"` |
| `reading_section_title` | string | Título `<h4>` interno. Default: `"Lectura principal"`. Ej: `"Guia para la POO"` |
| `reading_button_text` | string | Texto del botón de la lectura principal. Default: `"Ver lectura"`. Ej: `"Ver Guia de apoyo"` |
| `reading_suggested_title` | string | Título de la sección de sugeridas. Default: `"Lecturas sugeridas"`. Ej: `"Libro de apoyo para mejorar el conocimiento"` |

**Bloque de Videos** — se crea como label independiente en Moodle:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `videos` | array | Lista de dicts `{title, url}`. **Soporta múltiples.** Cada uno genera su propio iframe dentro del bloque. |
| `videos_summary` | string | Texto resumen de los videos (aparece al pie del bloque) |

**IDs de labels existentes** — para actualizar en vez de crear nuevos:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `existing_labels` | objeto \| null | Dict con IDs de labels existentes por tipo de bloque. Las claves son `"presentations"`, `"reading"` y/o `"videos"`. Cada valor tiene `label_cmid` y `label_instance_id`. |

> **¿De dónde saco estos IDs?** Del scan (`GET /scan/{course_id}`): cada elemento de `existing_blocks` tiene `label_cmid` y `label_instance_id`. El frontend debe guardarlos y enviarlos de vuelta al personalizar.
>
> **¿Es obligatorio?** No. Si no se envían, el backend intenta detectar labels existentes automáticamente. Pero enviarlos es **más confiable** y evita duplicados en todos los casos.
>
> **¿Qué pasa si envío IDs parciales?** Se fusionan: los IDs del frontend tienen prioridad, el backend rellena lo que falte con detección automática.

#### Estructura del campo `schedule`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `days_columns` | array de strings | Nombres de columnas. Ej: `["Lunes", "Martes", "Miércoles"]` |
| `entries` | array | Filas del horario |

Cada entrada de `entries`:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `subject_name` | string | Nombre de la asignatura |
| `days` | objeto | Horarios por día. Ej: `{"Lunes": "18h30 – 19h30"}` |

#### Estructura del campo `bibliography`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `entries` | array | Lista de referencias bibliográficas |

Cada entrada:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `text` | string | Texto visible de la referencia |
| `url` | string | URL del recurso |

#### Respuesta del Preview

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `success` | bool | Si se procesó correctamente |
| `course_id` | int | ID del curso |
| `message` | string | Mensaje descriptivo |
| `total_replacements` | int | Cantidad total de cambios |
| `details` | array | Detalle de cada cambio |
| `processed_html` | string (JSON) | **JSON con el HTML por sección y por bloque** |

El campo `processed_html` es un **JSON serializado** con esta estructura:

```json
{
  "1692": {
    "summary": "<html del summary de la sección>",
    "presentations_block": "<html del bloque de presentaciones>",
    "reading_block": "<html del bloque de lectura>",
    "videos_block": "<html del bloque de videos>"
  }
}
```

> Solo aparecen las claves de los bloques que se enviaron en el request. Si no se enviaron `videos`, no habrá `videos_block` en la respuesta.

---

### 7. Customize — Aplicar Cambios en Moodle

**`POST /api/v1/editor/customize`**

**Mismo body que `/preview`**, pero guarda los cambios en Moodle:
- El summary de la sección se actualiza con los placeholders/título/descripción/horario/bibliografía.
- Se crean **hasta 3 labels independientes** dentro de la sección (uno por cada bloque de contenido enviado):
  - 📊 `Presentación` — con todos los iframes de presentación
  - 📖 `Lectura` (o el label personalizado) — con lectura principal + sugeridas
  - 🎥 `Video` — con todos los iframes de video

**Respuesta:** Igual que `/preview` pero:
- `processed_html` es `null` (ya guardado en Moodle).
- `message` confirma que los cambios fueron guardados.

**Errores posibles:**
- `400`: Moodle rechaza la actualización (permisos, token incorrecto, etc.)
- `500`: Error interno del servidor

---

### 8. Duplicar Curso

**`POST /api/v1/courses/duplicate`**

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `source_course_id` | int | **Sí** | ID del curso origen |
| `new_fullname` | string | **Sí** | Nombre completo del nuevo curso |
| `new_shortname` | string | **Sí** | Nombre corto del nuevo curso |
| `category_id` | int | No | ID de la categoría destino |
| `visible` | int | No | Visibilidad (0 = oculto, 1 = visible). Default: 0 |
| `new_teacher_profile_url` | string | No | URL del perfil del docente a reemplazar |

**Respuesta:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `success` | bool | Si la duplicación fue exitosa |
| `new_course_id` | int | ID del nuevo curso |
| `new_course_url` | string | URL del nuevo curso en Moodle |
| `message` | string | Mensaje descriptivo |
| `links_updated` | int | Links actualizados durante la duplicación |

---

### 9. Obtener Contenido del Curso

**`GET /api/v1/courses/{course_id}/contents`**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `course_id` | int | ID del curso |
| `sections` | array | Secciones con sus módulos y HTML |

---

## Flujo Recomendado para la Vista Principal

### Paso 1: Selector de curso
1. `GET /api/v1/courses/` → lista de cursos.
2. Al seleccionar uno → `GET /api/v1/editor/scan/{id}`.

### Paso 2: Formulario de personalización
Con la respuesta del scan, construir el formulario:

- `placeholders` tiene elementos → input de URL por cada uno.
  - **Pre-llenar** cada input con `current_value` si empieza con `http` (ya fue configurado).
- `course_title` existe → input prellenado con el título actual.
- `course_description` existe → textarea prellenado.
- `schedule_found === true` → sección de horario con inputs por asignatura/día.
  - **Pre-llenar** con `existing_schedule.entries` y `existing_schedule.days_columns` si no es `null`.
- `bibliography_found === true` → sección de bibliografía.
  - **Pre-llenar** con `existing_bibliography.entries` si no es `null`.

**Bloques de contenido** — pre-llenar si ya existen:

```typescript
// Pseudocódigo para pre-llenar bloques
const scanResponse = await fetch(`/api/v1/editor/scan/${courseId}`);
const { existing_blocks } = scanResponse;

for (const block of existing_blocks) {
  switch (block.block_type) {
    case 'presentations':
      // Pre-llenar array de presentaciones
      form.presentations = block.presentations; // [{title, url}]
      form.presentation_objective = block.presentation_objective;
      break;

    case 'reading':
      // Pre-llenar lectura principal
      form.main_reading = block.main_reading; // {title, author, url, summary}
      form.suggested_readings = block.suggested_readings; // [{title, author, url}]
      // Pre-llenar etiquetas configurables
      form.reading_collapse_label = block.collapse_label;
      form.reading_section_title = block.reading_section_title;
      form.reading_button_text = block.reading_button_text;
      form.reading_suggested_title = block.reading_suggested_title;
      break;

    case 'videos':
      // Pre-llenar array de videos
      form.videos = block.videos; // [{title, url}]
      form.videos_summary = block.videos_summary;
      break;
  }
}
```

- **Presentaciones**: botón "Agregar presentación" → array dinámico de `{title, url}`.
- **Lectura principal**: campos `title`, `author`, `url`, `summary` + etiquetas configurables.
- **Lecturas sugeridas**: botón "Agregar lectura sugerida" → array dinámico de `{title, author, url}`.
- **Videos**: botón "Agregar video" → array dinámico de `{title, url}`.

> **Importante:** Si `existing_blocks` contiene datos, el formulario debe iniciar con esos valores y el usuario puede modificarlos. Al guardar, los bloques se **actualizan** (no se duplican) siempre que se envíen los `existing_labels`.

**Cómo construir `existing_labels` desde el scan:**

```typescript
// Construir existing_labels a partir de existing_blocks del scan
const existingLabels: Record<string, { label_cmid: number; label_instance_id: number }> = {};
for (const block of scanResponse.existing_blocks) {
  existingLabels[block.block_type] = {
    label_cmid: block.label_cmid,
    label_instance_id: block.label_instance_id,
  };
}

// Incluir en el request de customize
const customizeRequest = {
  course_id: 138,
  sections: [{
    section_id: 1692,
    section_number: 1,
    presentations: form.presentations,
    videos: form.videos,
    main_reading: form.main_reading,
    existing_labels: existingLabels,  // ← esto evita duplicados
  }]
};
await fetch('/api/v1/editor/customize', { method: 'POST', body: JSON.stringify(customizeRequest) });
```

### Paso 3: Preview
1. Armar el JSON con los campos que el usuario llenó, dentro de `sections[].`.
2. `POST /api/v1/editor/preview`.
3. Parsear `JSON.parse(response.processed_html)` → mostrar cada bloque (`summary`, `presentations_block`, `reading_block`, `videos_block`) en su propio iframe/div.

### Paso 4: Aplicar
1. Mismo JSON a `POST /api/v1/editor/customize`.
2. Verificar `success === true`.
3. Mostrar mensaje de confirmación con `total_replacements` cambios.

---

## Flujo de Duplicación + Personalización

1. `POST /api/v1/courses/duplicate` → obtener `new_course_id`.
2. `GET /api/v1/editor/scan/{new_course_id}`.
3. El usuario llena el formulario.
4. `POST /api/v1/editor/preview` → vista previa.
5. `POST /api/v1/editor/customize` → guardar.

---

## Notas Importantes

- **Todos los campos de personalización son opcionales.** Solo se modifican los que se envíen con valor.
- **Los 3 bloques de contenido (Presentaciones, Lectura, Videos) crean labels SEPARADOS** en Moodle — no se concatenan al summary de la sección.
- **Los labels se crean en orden**: primero Presentación, luego Lectura, luego Video. Si ya existen labels de ejecuciones anteriores, **se actualizan en lugar de duplicarse** (detección por `data-block-type` o ID de collapse).
- **Los placeholders** son valores fijos en el HTML (`video-introductorio`, `unirse-clases`, etc.) que se reemplazan por URLs reales en el summary de la sección. Una vez reemplazados, el backend los marca con `data-placeholder` para que futuros escaneos sigan detectándolos.
- **El campo `processed_html`** del preview es un JSON string (`JSON.parse()` para usarlo). Contiene las claves `summary`, `presentations_block`, `reading_block`, `videos_block` según los bloques enviados.
- **CORS** configurado para `localhost:5173`. Agregar otros orígenes en la configuración del backend si es necesario.

---

## Changelog

### v1.3 — Extracción de contenido existente + Pre-llenado (Marzo 2026)

#### 🆕 Nuevas funcionalidades
- **`existing_blocks` enriquecido**: El scan ahora extrae el contenido completo de cada bloque detectado (presentaciones, lectura, videos) con campos específicos por tipo:
  - `presentations` / `presentation_objective` para bloques de presentación
  - `main_reading` / `suggested_readings` / `reading_section_title` / `reading_button_text` / `reading_suggested_title` para bloques de lectura
  - `videos` / `videos_summary` para bloques de video
  - `collapse_label` — texto del botón collapse
  - `section_id` / `section_number` — ubicación del bloque en el curso
- **`existing_schedule`**: El scan devuelve los datos actuales del horario en formato `{days_columns, entries}` para pre-llenar el formulario.
- **`existing_bibliography`**: El scan devuelve los datos actuales de bibliografía en formato `{entries: [{text, url}]}` para pre-llenar el formulario.
- **`current_value` en placeholders**: Cada placeholder escaneado incluye su valor actual. Si empieza con `http`, ya fue configurado previamente.
- **`PUT /api/v1/courses/{course_id}`**: Nuevo endpoint para actualizar metadatos del curso (idnumber, fullname, shortname).
- **Bloques se actualizan, no se duplican**: Al re-personalizar un curso, los labels existentes se actualizan en lugar de crear nuevos. **Doble detección**: el backend detecta automáticamente (por `data-block-type` y por IDs de collapse), Y acepta `existing_labels` del frontend para mayor confiabilidad.
- **`existing_labels` en customize/preview**: El frontend puede enviar los IDs de labels existentes (del scan) para garantizar la actualización. Se fusionan con la detección server-side: frontend tiene prioridad.
- **Persistencia de placeholders**: Los elementos reemplazados se marcan con `data-placeholder` para que futuros escaneos los sigan detectando.

#### ⚠️ Cambios en la respuesta del Scan
- `existing_blocks[].items` y `existing_blocks[].summary_text` ahora son campos legacy (deprecados). Usar los campos específicos por tipo (`presentations`, `main_reading`, `videos`, etc.).
- Nuevos campos en la respuesta raíz: `existing_schedule`, `existing_bibliography`, `template_source`, `can_save`, `save_hint`.

### v1.3.1 — Fix: bloques se duplicaban en vez de actualizarse (Marzo 2026)

#### 🐛 Bug fix crítico
- **Los bloques ya NO se duplican.** El `update_label` ahora usa `local_sectionedit_update_label` (plugin propio) como método principal, con `mod_label_update_labels` como fallback. Antes solo usaba `mod_label_update_labels` que no estaba habilitado en el servicio web.
- **Eliminado el silent fallthrough**: Si el update falla, el error se propaga al frontend en vez de crear un label duplicado silenciosamente.
- **Debug logging**: El backend ahora imprime logs claros (`🔍 UPDATE instance_id=...` o `🔍 CREATE nuevo label`) para diagnosticar problemas.

#### 🔧 Plugin Moodle actualizado (v1.2.7)
- **Nueva función**: `local_sectionedit_update_label` — actualiza el contenido HTML de un label existente por su instance ID.
- **⚠️ REQUIERE upgrade del plugin** en Moodle: Ir a Administración del sitio → Notificaciones para aplicar la actualización.

### v1.1 — Bloques separados + mayor flexibilidad (Feb 2026)

#### 🆕 Nuevas funcionalidades
- **Bloques de contenido independientes en Moodle**: Presentaciones, Lectura y Videos ahora se crean como **labels separados** dentro de la sección, en lugar de concatenarse en un solo bloque HTML.
- **Múltiples presentaciones por bloque**: el campo `presentations` acepta un array con cualquier cantidad de entradas; cada una genera su propio iframe dentro del mismo label de presentación.
- **Múltiples videos por bloque**: igual que presentaciones, `videos` acepta múltiples entradas.
- **Etiquetas de lectura configurables**: 4 nuevos campos opcionales para personalizar el bloque de lectura:
  - `reading_collapse_label` — texto del botón collapse
  - `reading_section_title` — título `<h4>` interno
  - `reading_button_text` — texto del botón de la lectura principal
  - `reading_suggested_title` — título de la sección de lecturas sugeridas

#### 🔧 Plugin Moodle actualizado (v1.1.0)
- Nueva función de Web Service: `local_sectionedit_add_label_to_section`
- Permite crear módulos label directamente en una sección via API

#### 📋 Cambios en la respuesta del Preview
- `processed_html` ahora es un **JSON string** (usar `JSON.parse()`) con la estructura:
  ```json
  { "section_id": { "summary": "...", "presentations_block": "...", "reading_block": "...", "videos_block": "..." } }
  ```
  En lugar del HTML plano de versiones anteriores.

#### ⚠️ Breaking Changes
- `processed_html` cambió de formato: era HTML plano, ahora es un JSON string. El frontend debe hacer `JSON.parse(response.processed_html)` para procesarlo.
