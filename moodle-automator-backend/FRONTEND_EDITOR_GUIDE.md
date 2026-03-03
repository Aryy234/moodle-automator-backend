# Guía de Integración Frontend — Editor / Personalización de Cursos

> **Base URL**: `http://localhost:8000/api/v1/editor`

Este documento explica cómo el frontend debe consumir los endpoints de escaneo y personalización de cursos, y cómo pre-llenar el formulario de edición cuando un curso ya fue configurado previamente.

---

## Tabla de contenidos

1. [Flujo general](#1-flujo-general)
2. [Endpoint: Scan](#2-endpoint-scan)
3. [Cómo pre-llenar el formulario con datos existentes](#3-cómo-pre-llenar-el-formulario-con-datos-existentes)
4. [Endpoint: Customize](#4-endpoint-customize)
5. [Endpoint: Preview](#5-endpoint-preview)
6. [Schemas de referencia](#6-schemas-de-referencia)
7. [Ejemplo completo (React/TS pseudocódigo)](#7-ejemplo-completo-reactts-pseudocódigo)

---

## 1. Flujo general

```
┌─────────────┐     GET /scan/{id}      ┌──────────────┐
│  Seleccionar │ ─────────────────────► │  Backend      │
│  Curso       │                        │  escanea HTML │
└─────────────┘                        └──────┬───────┘
                                              │
                                    PlaceholderScanResponse
                                              │
                                    ┌─────────▼──────────┐
                                    │  Frontend pre-llena │
                                    │  el formulario      │
                                    └─────────┬──────────┘
                                              │
                                    Usuario edita campos
                                              │
                                    ┌─────────▼──────────┐
                                    │  POST /customize    │
                                    │  (guardar)          │
                                    └────────────────────┘
```

**Puntos clave:**
- El scan retorna **tanto** lo que falta configurar **como** lo que ya fue configurado.
- El campo `current_value` de cada placeholder indica el valor actual en Moodle.
- El array `existing_blocks` contiene los bloques avanzados (presentación, lectura, video) ya existentes.

---

## 2. Endpoint: Scan

```
GET /editor/scan/{course_id}
```

### Response: `PlaceholderScanResponse`

```jsonc
{
  "course_id": 138,
  "section_name": "General",
  "module_id": 1797,
  "module_name": "Sección: General",
  "total_placeholders": 6,
  
  // 🔑 Array de placeholders (links e iframes del template)
  "placeholders": [
    {
      "element_type": "iframe",        // "iframe" o "a"
      "attribute": "src",              // "src" o "href"
      "placeholder_key": "video-introductorio",  // Clave fija para mapear al campo del form
      "context_text": null,            // Texto del enlace (solo para <a>)
      "current_value": "video-introductorio"     // ⬅️ Esto es CLAVE
    },
    {
      "element_type": "a",
      "attribute": "href",
      "placeholder_key": "unirse-clases",
      "context_text": "Enlace de clases",
      "current_value": "https://zoom.us/j/123456"  // ⬅️ Ya fue configurado
    }
    // ... más placeholders
  ],
  
  // 🔑 Campos de texto
  "course_title": "NOMBRE CURSO",           // Valor actual del <h1>
  "course_description": "Descripción...",    // Valor actual del <p>
  
  // 🔑 Secciones estructuradas
  "schedule_found": true,
  "bibliography_found": true,
  
  // 🔑 Bloques avanzados ya creados como labels en Moodle
  "existing_blocks": [
    {
      "block_type": "presentations",         // "presentations" | "reading" | "videos"
      "label_cmid": 9901,                    // ID del módulo label en Moodle
      "label_instance_id": 4521,             // ID de instancia (para actualizar)
      "items": [                             // Contenido extraído del bloque
        { "title": "Semana 1 - Intro", "url": "https://canva.com/abc" }
      ],
      "summary_text": "Objetivo de aprendizaje..."  // Resumen/objetivo si existe
    },
    {
      "block_type": "reading",
      "label_cmid": 9902,
      "label_instance_id": 4522,
      "items": [
        { "title": "Mi Libro", "author": "J. Autor", "url": "https://lib.com/book" }
      ],
      "summary_text": "Resumen del libro..."
    },
    {
      "block_type": "videos",
      "label_cmid": 9903,
      "label_instance_id": 4523,
      "items": [
        { "title": "Video Intro", "url": "https://youtube.com/watch?v=xyz" }
      ],
      "summary_text": null
    }
  ],
  
  "template_source": "section_summary",
  "can_save": true,
  "save_hint": null
}
```

---

## 3. Cómo pre-llenar el formulario con datos existentes

### 3.1 Placeholders (7 campos de URL)

Cada placeholder tiene:
- `placeholder_key`: clave fija que identifica el campo (ej: `"video-introductorio"`)
- `current_value`: valor actual del atributo `src`/`href` en el HTML de Moodle

**Regla para detectar si ya fue configurado:**

```ts
// Un placeholder está configurado si su current_value es diferente de su placeholder_key
const isConfigured = (p: PlaceholderFound) => p.current_value !== p.placeholder_key;

// Alternativa: verificar si empieza con http
const isConfigured = (p: PlaceholderFound) => 
  p.current_value?.startsWith('http://') || p.current_value?.startsWith('https://');
```

**Mapeo `placeholder_key` → campo del formulario:**

| `placeholder_key`     | Campo del formulario     | Tipo      |
|----------------------|--------------------------|-----------|
| `video-introductorio` | `video_introductorio`    | iframe src |
| `unirse-clases`       | `unirse_clases`          | href       |
| `url-grabaciones`     | `url_grabaciones`        | href       |
| `perfil-docente`      | `perfil_docente`         | iframe src |
| `silabo`              | `silabo`                 | iframe src |
| `pea`                 | `pea`                    | iframe src |
| `bibliografia`        | `bibliografia_url`       | href       |

**Código para pre-llenar:**

```ts
// Mapeo de placeholder_key → nombre del campo en el form
const PLACEHOLDER_TO_FIELD: Record<string, string> = {
  'video-introductorio': 'video_introductorio',
  'unirse-clases':       'unirse_clases',
  'url-grabaciones':     'url_grabaciones',
  'perfil-docente':      'perfil_docente',
  'silabo':              'silabo',
  'pea':                 'pea',
  'bibliografia':        'bibliografia_url',
};

scanResponse.placeholders.forEach(p => {
  const fieldName = PLACEHOLDER_TO_FIELD[p.placeholder_key];
  if (!fieldName) return;
  
  const isConfigured = p.current_value !== p.placeholder_key;
  if (isConfigured && p.current_value) {
    form[fieldName] = p.current_value;   // ← Pre-llenar con la URL actual
  }
});
```

### 3.2 Título y Descripción

```ts
if (scanResponse.course_title) {
  form.course_title = scanResponse.course_title;
}
if (scanResponse.course_description) {
  form.course_description = scanResponse.course_description;
}
```

> **Nota:** `course_title` y `course_description` siempre retornan el texto actual del `<h1>` y `<p>` del HTML. Si el curso no ha sido personalizado, retornarán el texto del template base (ej: `"NOMBRE CURSO"`).

### 3.3 Bloques avanzados (presentación, lectura, video)

Los bloques se crean como **labels independientes** en Moodle. El scan los detecta y retorna su contenido en `existing_blocks`.

```ts
scanResponse.existing_blocks.forEach(block => {
  switch (block.block_type) {
    
    case 'presentations':
      // items: [{ title: string, url: string }]
      form.presentations = block.items;
      form.presentation_objective = block.summary_text || '';
      break;
    
    case 'reading':
      // items[0] = lectura principal: { title, author, url }
      // items[1..n] = lecturas sugeridas
      if (block.items.length > 0) {
        form.main_reading = block.items[0];          // { title, author, url }
        form.suggested_readings = block.items.slice(1);
      }
      form.reading_summary = block.summary_text || '';
      break;
    
    case 'videos':
      // items: [{ title: string, url: string }]
      form.videos = block.items;
      form.videos_summary = block.summary_text || '';
      break;
  }
});
```

### 3.4 Horario y Bibliografía

Los campos `schedule_found` y `bibliography_found` indican si ya existen en el HTML. El backend **no retorna los datos parseados** del horario/bibliografía en el scan (solo indica si existen). El frontend debería:

- Si `schedule_found === true`: mostrar el editor de horario (puede estar vacío o con datos previos)
- Si `bibliography_found === true`: mostrar el editor de bibliografía

> Si en el futuro se necesita retornar los datos actuales del horario/bibliografía, se puede extender el backend.

---

## 4. Endpoint: Customize

```
POST /editor/customize
```

### Request Body: `CourseCustomizationRequest`

**Modo por secciones (recomendado):**

```jsonc
{
  "course_id": 138,
  "sections": [
    {
      "section_id": 1797,        // ID de la sección (viene del scan: module_id)
      "section_number": 0,       // 0 = General
      
      // Placeholders (solo enviar los que se quieran actualizar)
      "video_introductorio": "https://youtube.com/embed/abc123",
      "unirse_clases": "https://zoom.us/j/999888",
      "url_grabaciones": "https://drive.google.com/grabaciones",
      "perfil_docente": "https://canva.com/design/perfil-docente",
      "silabo": "https://docs.google.com/silabo",
      "pea": "https://docs.google.com/pea",
      "bibliografia_url": "https://biblioteca.edu.ec/ref123",
      
      // Texto
      "course_title": "Programación Orientada a Objetos - NRC 1234",
      "course_description": "Curso de POO para el período 2026-A",
      
      // Horario
      "schedule": {
        "entries": [
          {
            "subject_name": "POO",
            "days": {
              "Lunes": "18h30 – 20h00",
              "Miércoles": "18h30 – 20h00"
            }
          }
        ],
        "days_columns": ["Lunes", "Martes", "Miércoles", "Jueves"]
      },
      
      // Bibliografía
      "bibliography": {
        "entries": [
          {
            "text": "Clean Code - Robert C. Martin",
            "url": "https://biblioteca.edu.ec/cleancode"
          }
        ]
      },
      
      // Bloques avanzados (se crean/actualizan como labels separados)
      "presentations": [
        { "title": "Semana 1 - Introducción a POO", "url": "https://canva.com/pres1" },
        { "title": "Semana 1 - Clases y Objetos", "url": "https://canva.com/pres2" }
      ],
      "presentation_objective": "Comprender los fundamentos de la POO",
      
      "main_reading": {
        "title": "Thinking in Java",
        "author": "Bruce Eckel",
        "url": "https://lib.com/thinking-java",
        "summary": "Libro fundamental sobre Java y POO"
      },
      "suggested_readings": [
        { "title": "Head First Java", "author": "K. Sierra", "url": "https://lib.com/hfj" }
      ],
      
      "videos": [
        { "title": "¿Qué es la POO?", "url": "https://youtube.com/embed/vid1" },
        { "title": "Herencia y Polimorfismo", "url": "https://youtube.com/embed/vid2" }
      ],
      "videos_summary": "Videos introductorios sobre los conceptos fundamentales de POO",
      
      // Personalización del bloque de lectura (opcionales)
      "reading_collapse_label": "Lectura",
      "reading_section_title": "Lectura principal",
      "reading_button_text": "Ver lectura",
      "reading_suggested_title": "Lecturas sugeridas"
    }
  ]
}
```

**Modo legacy (solo sección General, campos planos):**

```jsonc
{
  "course_id": 138,
  "video_introductorio": "https://youtube.com/embed/abc123",
  "unirse_clases": "https://zoom.us/j/999888",
  "course_title": "Mi Curso"
  // ... demás campos planos
}
```

### Response: `CourseCustomizationResponse`

```jsonc
{
  "success": true,
  "course_id": 138,
  "message": "Se personalizaron 1 secciones. Total de cambios: 10 exitosamente",
  "total_replacements": 10,
  "details": [
    {
      "field": "iframe[src]=video-introductorio",
      "old_value": "video-introductorio",
      "new_value": "https://youtube.com/embed/abc123"
    },
    {
      "field": "presentations_block",
      "old_value": "",
      "new_value": "Bloque de presentación actualizado"   // o "creado como label independiente"
    }
    // ... más detalles
  ],
  "processed_html": null   // Solo se llena en /preview
}
```

---

## 5. Endpoint: Preview

```
POST /editor/preview
```

Mismo body que `/customize` pero **no guarda** en Moodle. Retorna el HTML resultante en `processed_html`.

Útil para mostrar una vista previa antes de confirmar.

---

## 6. Schemas de referencia

### PlaceholderFound

| Campo            | Tipo     | Descripción |
|-----------------|----------|-------------|
| `element_type`   | string   | `"iframe"` o `"a"` |
| `attribute`      | string   | `"src"` o `"href"` |
| `placeholder_key`| string   | Clave fija: `video-introductorio`, `unirse-clases`, etc. |
| `context_text`   | string?  | Texto del enlace (solo `<a>`) |
| `current_value`  | string?  | **Valor actual.** Si es igual a `placeholder_key` → no configurado. Si es una URL → ya configurado. |

### ExistingBlockInfo

| Campo              | Tipo     | Descripción |
|-------------------|----------|-------------|
| `block_type`       | string   | `"presentations"`, `"reading"` o `"videos"` |
| `label_cmid`       | int?     | Course module ID del label |
| `label_instance_id`| int?     | Instance ID (para updates internos) |
| `items`            | list     | Contenido: `[{title, url}]` o `[{title, author, url}]` |
| `summary_text`     | string?  | Resumen/objetivo si existe |

### SectionCustomizationData (campos del form)

| Campo                    | Tipo     | Descripción |
|-------------------------|----------|-------------|
| `section_id`             | int      | **Obligatorio.** ID de la sección (`module_id` del scan) |
| `section_number`         | int?     | Número de sección (0=General) |
| `video_introductorio`    | string?  | URL iframe video intro |
| `unirse_clases`          | string?  | URL enlace zoom/teams |
| `url_grabaciones`        | string?  | URL grabaciones |
| `perfil_docente`         | string?  | URL iframe perfil docente |
| `silabo`                 | string?  | URL iframe sílabo |
| `pea`                    | string?  | URL iframe PEA |
| `bibliografia_url`       | string?  | URL bibliografía |
| `course_title`           | string?  | Título del curso |
| `course_description`     | string?  | Descripción del curso |
| `schedule`               | object?  | `{ entries: [...], days_columns: [...] }` |
| `bibliography`           | object?  | `{ entries: [{ text, url }] }` |
| `presentations`          | list?    | `[{ title, url }]` |
| `presentation_objective` | string?  | Objetivo de la presentación |
| `main_reading`           | object?  | `{ title, author, url, summary }` |
| `suggested_readings`     | list?    | `[{ title, author, url }]` |
| `videos`                 | list?    | `[{ title, url }]` |
| `videos_summary`         | string?  | Resumen de videos |

---

## 7. Ejemplo completo (React/TS pseudocódigo)

```tsx
// === Tipos ===
interface PlaceholderFound {
  element_type: string;
  attribute: string;
  placeholder_key: string;
  context_text: string | null;
  current_value: string | null;
}

interface ExistingBlockInfo {
  block_type: 'presentations' | 'reading' | 'videos';
  label_cmid: number | null;
  label_instance_id: number | null;
  items: Record<string, string>[];
  summary_text: string | null;
}

interface ScanResponse {
  course_id: number;
  module_id: number;
  placeholders: PlaceholderFound[];
  course_title: string | null;
  course_description: string | null;
  schedule_found: boolean;
  bibliography_found: boolean;
  existing_blocks: ExistingBlockInfo[];
  can_save: boolean;
}

// === Mapeo placeholder_key → campo del form ===
const PLACEHOLDER_FIELD_MAP: Record<string, string> = {
  'video-introductorio': 'video_introductorio',
  'unirse-clases':       'unirse_clases',
  'url-grabaciones':     'url_grabaciones',
  'perfil-docente':      'perfil_docente',
  'silabo':              'silabo',
  'pea':                 'pea',
  'bibliografia':        'bibliografia_url',
};

// === Función para cargar el formulario ===
async function loadCourseEditor(courseId: number) {
  const res = await fetch(`/api/v1/editor/scan/${courseId}`);
  const scan: ScanResponse = await res.json();
  
  const form: Record<string, any> = {
    course_id: scan.course_id,
    section_id: scan.module_id,
    // Inicializar campos vacíos
    video_introductorio: '',
    unirse_clases: '',
    url_grabaciones: '',
    perfil_docente: '',
    silabo: '',
    pea: '',
    bibliografia_url: '',
    course_title: '',
    course_description: '',
    presentations: [],
    presentation_objective: '',
    main_reading: null,
    suggested_readings: [],
    videos: [],
    videos_summary: '',
  };
  
  // ── 1. Pre-llenar placeholders ──
  scan.placeholders.forEach(p => {
    const fieldName = PLACEHOLDER_FIELD_MAP[p.placeholder_key];
    if (!fieldName) return;
    
    // Si current_value es distinto del placeholder_key, ya fue configurado
    if (p.current_value && p.current_value !== p.placeholder_key) {
      form[fieldName] = p.current_value;
    }
  });
  
  // ── 2. Pre-llenar título y descripción ──
  if (scan.course_title) {
    form.course_title = scan.course_title;
  }
  if (scan.course_description) {
    form.course_description = scan.course_description;
  }
  
  // ── 3. Pre-llenar bloques avanzados ──
  scan.existing_blocks.forEach(block => {
    switch (block.block_type) {
      case 'presentations':
        form.presentations = block.items;  // [{ title, url }]
        form.presentation_objective = block.summary_text || '';
        break;
        
      case 'reading':
        if (block.items.length > 0) {
          form.main_reading = block.items[0];  // { title, author, url }
          form.suggested_readings = block.items.slice(1);
        }
        form.reading_summary = block.summary_text || '';
        break;
        
      case 'videos':
        form.videos = block.items;  // [{ title, url }]
        form.videos_summary = block.summary_text || '';
        break;
    }
  });
  
  return form;
}

// === Función para guardar ===
async function saveCustomization(form: Record<string, any>) {
  const body = {
    course_id: form.course_id,
    sections: [{
      section_id: form.section_id,
      section_number: 0,
      // Solo enviar campos no vacíos
      ...(form.video_introductorio && { video_introductorio: form.video_introductorio }),
      ...(form.unirse_clases && { unirse_clases: form.unirse_clases }),
      ...(form.url_grabaciones && { url_grabaciones: form.url_grabaciones }),
      ...(form.perfil_docente && { perfil_docente: form.perfil_docente }),
      ...(form.silabo && { silabo: form.silabo }),
      ...(form.pea && { pea: form.pea }),
      ...(form.bibliografia_url && { bibliografia_url: form.bibliografia_url }),
      ...(form.course_title && { course_title: form.course_title }),
      ...(form.course_description && { course_description: form.course_description }),
      ...(form.presentations?.length && { 
        presentations: form.presentations,
        presentation_objective: form.presentation_objective 
      }),
      ...(form.main_reading && { 
        main_reading: form.main_reading,
        suggested_readings: form.suggested_readings 
      }),
      ...(form.videos?.length && { 
        videos: form.videos,
        videos_summary: form.videos_summary 
      }),
    }]
  };
  
  const res = await fetch('/api/v1/editor/customize', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  
  return await res.json();
}
```

---

## Notas importantes

1. **Persistencia de placeholders**: El backend marca cada elemento reemplazado con `data-placeholder="clave"` en el HTML. Esto permite que futuros scans sigan detectando esos campos aunque la URL ya no sea el placeholder original.

2. **Bloques duplicados**: Si un bloque (presentación, lectura, video) ya existe como label en Moodle, el backend lo **actualiza** en lugar de crear uno duplicado.

3. **`section_id` es obligatorio** en el modo por secciones. Viene del campo `module_id` del scan response.

4. **Solo enviar campos que se quieran actualizar**. Los campos `null` o ausentes se ignoran.

5. **`can_save`**: Si es `false`, el frontend debería deshabilitar el botón de guardar y mostrar `save_hint` como mensaje informativo.
