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

Cada placeholder:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `element_type` | string | `"a"` o `"iframe"` |
| `attribute` | string | `"href"` o `"src"` |
| `placeholder_key` | string | Clave identificadora (ver tabla abajo) |
| `context_text` | string \| null | Texto visible del enlace (solo para `<a>`) |

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
      "videos_summary": "Resumen de los videos..."
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
- `course_title` existe → input prellenado con el título actual.
- `course_description` existe → textarea prellenado.
- `schedule_found === true` → sección de horario con inputs por asignatura/día.
- `bibliography_found === true` → sección de bibliografía.

**Además** (siempre disponibles, sans necesidad de scan):
- **Presentaciones**: botón "Agregar presentación" → array dinámico de `{title, url}`.
- **Lectura principal**: campos `title`, `author`, `url`, `summary` + etiquetas configurables.
- **Lecturas sugeridas**: botón "Agregar lectura sugerida" → array dinámico de `{title, author, url}`.
- **Videos**: botón "Agregar video" → array dinámico de `{title, url}`.

### Semana 1 — Bloques de Contenido

La sección **Semana 1** contiene **3 bloques independientes** que el usuario puede activar/desactivar. Cada bloque genera un **label separado en Moodle**.

---

#### 📊 Bloque: Presentaciones

El usuario puede agregar **N presentaciones**. Por cada presentación se duplica el siguiente grupo de campos en el formulario:

```html
<!-- Repetir este bloque por cada presentación -->
<div class="presentation-item">
  <input type="text"  name="presentations[i][title]" placeholder="Título de la presentación" />
  <input type="url"   name="presentations[i][url]"   placeholder="Link de la presentación (Canva, etc.)" />
  <button type="button" class="remove-btn">Eliminar</button>
</div>
```

- Botón **"Agregar presentación"** → clona el bloque anterior (incrementa el índice `i`).
- El array resultante se envía como `presentations: [ {title, url}, ... ]`.
- Cada entrada genera su propio `<iframe>` dentro del label del bloque en Moodle.

---

#### 📖 Bloque: Lectura

Este bloque tiene **estructura fija** (no se duplica como sección):

```html
<!-- Lectura Principal — solo 1 -->
<div class="main-reading">
  <input type="text" name="main_reading[title]"  placeholder="Título del libro" />
  <input type="text" name="main_reading[author]" placeholder="Autor" />
  <input type="url"  name="main_reading[url]"    placeholder="Link del libro" />
  <textarea          name="main_reading[summary]" placeholder="Resumen breve"></textarea>
</div>

<!-- Lecturas Sugeridas — se puede agregar N -->
<div class="suggested-readings">
  <!-- Repetir este bloque por cada lectura sugerida -->
  <div class="suggested-reading-item">
    <input type="text" name="suggested_readings[i][title]"  placeholder="Título del libro sugerido" />
    <input type="text" name="suggested_readings[i][author]" placeholder="Autor" />
    <input type="url"  name="suggested_readings[i][url]"    placeholder="Link del libro sugerido" />
    <button type="button" class="remove-btn">Eliminar</button>
  </div>
</div>
<button type="button" id="add-suggested">Agregar lectura sugerida</button>
```

**Campos opcionales de personalización de etiquetas:**

| Campo del form | Campo API | Default |
|---|---|---|
| Texto botón collapse | `reading_collapse_label` | `"Lectura"` |
| Título interno (`<h4>`) | `reading_section_title` | `"Lectura principal"` |
| Texto botón ver lectura | `reading_button_text` | `"Ver lectura"` |
| Título sección sugeridas | `reading_suggested_title` | `"Lecturas sugeridas"` |

---

#### 🎥 Bloque: Videos

Igual que Presentaciones: el usuario agrega **N videos**, cada uno con título y link.

```html
<!-- Repetir este bloque por cada video -->
<div class="video-item">
  <input type="text" name="videos[i][title]" placeholder="Título del video" />
  <input type="url"  name="videos[i][url]"   placeholder="Link del video (Drive, YouTube, etc.)" />
  <button type="button" class="remove-btn">Eliminar</button>
</div>
```

- Botón **"Agregar video"** → clona el bloque (incrementa `i`).
- El array resultante se envía como `videos: [ {title, url}, ... ]`.
- Campo adicional opcional: `videos_summary` → texto resumen que aparece al pie del bloque.

---

#### JSON resultante para Semana 1

```json
{
  "presentations": [
    { "title": "Presentación 1", "url": "https://canva.com/..." },
    { "title": "Presentación 2", "url": "https://canva.com/..." }
  ],
  "main_reading": {
    "title": "Título del libro",
    "author": "Nombre del autor",
    "url": "https://...",
    "summary": "Resumen del libro..."
  },
  "suggested_readings": [
    { "title": "Libro sugerido 1", "author": "Autor 1", "url": "https://..." },
    { "title": "Libro sugerido 2", "author": "Autor 2", "url": "https://..." }
  ],
  "videos": [
    { "title": "Video 1", "url": "https://drive.google.com/..." },
    { "title": "Video 2", "url": "https://drive.google.com/..." }
  ]
}
```

> Solo enviar los bloques que el usuario haya llenado. Bloques vacíos no deben enviarse (la API los ignora pero es mejor práctica omitirlos).

---

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
- **Los labels se crean en orden**: primero Presentación, luego Lectura, luego Video. Si ya existen labels de ejecuciones anteriores, se agregarán nuevos al final de la sección.
- **Los placeholders** son valores fijos en el HTML (`video-introductorio`, `unirse-clases`, etc.) que se reemplazan por URLs reales en el summary de la sección.
- **El campo `processed_html`** del preview es un JSON string (`JSON.parse()` para usarlo). Contiene las claves `summary`, `presentations_block`, `reading_block`, `videos_block` según los bloques enviados.
- **CORS** configurado para `localhost:5173`. Agregar otros orígenes en la configuración del backend si es necesario.

---

## Changelog

### v1.2 — Documentación de UI para Semana 1 (Feb 2026)

#### 📝 Actualización de documentación
- Agregada sección **"Semana 1 — Bloques de Contenido"** con detalle de implementación de formulario por bloque:
  - **Presentaciones**: estructura HTML del campo duplicable `{title, url}` por cada presentación.
  - **Lectura**: estructura fija para la lectura principal (`{title, author, url, summary}`) + campos `{title, author, url}` repetibles para lecturas sugeridas.
  - **Videos**: estructura HTML del campo duplicable `{title, url}` por cada video (+ campo opcional `videos_summary`).
- Agregado ejemplo de JSON resultante para el body completo de Semana 1.

---

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
