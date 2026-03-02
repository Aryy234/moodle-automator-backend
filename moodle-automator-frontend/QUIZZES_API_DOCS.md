# Sistema de Cuestionarios — Documentación para Frontend

> **Base URL**: `http://localhost:8000`
> **Prefijo de endpoints**: `/api/v1/quizzes`
> **Swagger UI**: `http://localhost:8000/docs`

---

## Tabla de Contenidos

1. [Conceptos Clave](#conceptos-clave)
2. [Flujo de Trabajo Completo](#flujo-de-trabajo-completo)
3. [Endpoints](#endpoints)
   - [Listar cuestionarios](#1-listar-cuestionarios-de-un-curso)
   - [Listar categorías](#2-listar-categorías-de-preguntas)
   - [Crear categoría](#3-crear-categoría-de-preguntas)
   - [Preview de importación](#4-preview-de-importación)
   - [Importar preguntas](#5-importar-preguntas-a-moodle)
   - [Cargar preguntas al quiz](#6-cargar-preguntas-al-cuestionario)
   - [Configurar tiempo límite](#7-configurar-tiempo-límite-del-cuestionario)
   - [Formatos soportados](#8-formatos-de-importación-soportados)
4. [Modelos de Datos](#modelos-de-datos)
5. [Manejo de Errores](#manejo-de-errores)
6. [Ejemplo de Flujo Completo (Código)](#ejemplo-de-flujo-completo-código)

---

## Conceptos Clave

### IDs importantes en Moodle

| Concepto | Campo | Descripción |
|---|---|---|
| **Course ID** | `course_id` | Identificador único del curso en Moodle |
| **Course Module ID** | `cmid` / `coursemodule` | Identificador del módulo de actividad dentro del curso. Cada cuestionario tiene uno distinto. Es el ID que se usa para operar sobre un quiz específico. |
| **Quiz Instance ID** | `id` | ID interno de la instancia del quiz (tabla `quiz`). Se usa poco desde el frontend. |
| **Category ID** | `category_id` | ID de la categoría en el banco de preguntas donde se almacenan las preguntas. |

### Banco de Preguntas vs Cuestionario

Moodle separa los conceptos:

- **Banco de preguntas**: repositorio donde se almacenan todas las preguntas, organizadas en **categorías**.
- **Cuestionario (quiz)**: actividad que muestra preguntas a los estudiantes. Las preguntas se cargan **desde** el banco.

El flujo es: **Subir archivo → Importar al banco → Cargar del banco al quiz**.

### Modos de carga de preguntas

| Modo | Descripción | Uso típico |
|---|---|---|
| `all` | Agrega **todas** las preguntas de la categoría como slots fijos. Cada estudiante ve las mismas preguntas. | Exámenes con preguntas fijas |
| `random` | Agrega **N referencias aleatorias**. Cada estudiante recibe un subconjunto diferente de la categoría en cada intento. | Simuladores, exámenes anti-copia |

### Contexto de categorías

Las categorías de preguntas pueden vivir en dos contextos:

| Contexto | `contextlevel` | Descripción |
|---|---|---|
| Curso | `"course"` | Categorías disponibles para todo el curso |
| Módulo quiz | `"module"` | Categorías exclusivas de un cuestionario específico |

---

## Flujo de Trabajo Completo

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FLUJO DE TRABAJO DEL FRONTEND                    │
└─────────────────────────────────────────────────────────────────────┘

    ┌──────────────┐
    │  1. LISTAR   │    GET /api/v1/quizzes/{course_id}/activities
    │  CUESTIONARIOS│
    └──────┬───────┘
           │ El usuario selecciona un quiz (obtiene coursemodule = cmid)
           ▼
    ┌──────────────┐
    │  2. LISTAR   │    GET /api/v1/quizzes/{course_id}/categories?cmid={cmid}
    │  CATEGORÍAS  │
    └──────┬───────┘
           │ ¿Existe una categoría adecuada?
           │
     ┌─────┴─────┐
     │ SÍ        │ NO ──────────────────────┐
     │           │                          ▼
     │           │                   ┌──────────────┐
     │           │                   │  3. CREAR    │  POST /api/v1/quizzes/{course_id}/categories
     │           │                   │  CATEGORÍA   │  Body: { name, cmid }
     │           │                   └──────┬───────┘
     │           │                          │ Obtiene category_id
     └─────┬─────┘◄─────────────────────────┘
           │
           ▼
    ┌──────────────┐
    │ 4. PREVIEW   │    POST /api/v1/quizzes/preview-import
    │ IMPORTACIÓN  │    FormData: { file, format }
    └──────┬───────┘
           │ El usuario ve las preguntas parseadas y confirma
           ▼
    ┌──────────────┐
    │ 5. IMPORTAR  │    POST /api/v1/quizzes/import
    │ AL BANCO     │    FormData: { file, format, course_id, category_id }
    └──────┬───────┘
           │ Preguntas están ahora en el banco de preguntas de Moodle
           ▼
    ┌──────────────┐
    │ 6. CARGAR    │    POST /api/v1/quizzes/{course_id}/configure-questions
    │ AL QUIZ      │    Body: { quiz_cmid, category_id, mode, num_questions }
    └──────┬───────┘
           │ ¿Modo 'all' o 'random'?
           │ • all: todas las preguntas como slots fijos
           │ • random: N preguntas aleatorias por intento
           ▼
    ┌──────────────┐
    │ 7. CONFIGURAR│    POST /api/v1/quizzes/{course_id}/settings
    │ TIEMPO LÍMITE│    Body: { quiz_cmid, time_limit }
    └──────────────┘
           │
           ▼
      ✅ ¡Quiz configurado y listo!
```

### Flujo mínimo (3 pasos si la categoría ya existe)

Si ya conoces el `course_id`, `cmid` y `category_id`:

```
1. POST /import          → Subir preguntas al banco
2. POST /configure-questions → Cargar al quiz (all o random)
3. POST /settings        → Configurar tiempo
```

---

## Endpoints

### 1. Listar cuestionarios de un curso

Obtiene todos los cuestionarios (quiz activities) de un curso. Primer paso para saber dónde importar.

```
GET /api/v1/quizzes/{course_id}/activities
```

**Parámetros de ruta:**
| Param | Tipo | Descripción |
|---|---|---|
| `course_id` | int | ID del curso en Moodle |

**Respuesta `200 OK`:**
```json
{
  "course_id": 129,
  "quizzes": [
    {
      "id": 456,
      "coursemodule": 9873,
      "course": 129,
      "name": "Evaluación teórica Primer Parcial",
      "intro": "<p>Descripción del quiz</p>",
      "timelimit": 3600,
      "attempts": 0,
      "grade": 10.0
    }
  ],
  "total": 1
}
```

**Campos importantes de cada quiz:**
| Campo | Descripción | Nota |
|---|---|---|
| `coursemodule` | **Este es el `cmid`** que usarás en los demás endpoints | ⭐ ID principal |
| `id` | ID de instancia del quiz | Uso interno |
| `timelimit` | Tiempo límite actual (segundos) | 0 = sin límite |

---

### 2. Listar categorías de preguntas

Obtiene las categorías del banco de preguntas. Necesitas una categoría para importar preguntas.

```
GET /api/v1/quizzes/{course_id}/categories
```

**Query parameters:**
| Param | Tipo | Default | Descripción |
|---|---|---|---|
| `cmid` | int | `0` | Si se envía, retorna categorías del quiz específico |
| `include_all` | bool | `false` | Si `true`, retorna categorías de todos los contextos (curso + todos los quizzes) |

**Ejemplos de llamadas:**
```
# Categorías del curso
GET /api/v1/quizzes/129/categories

# Categorías de un quiz específico
GET /api/v1/quizzes/129/categories?cmid=9873

# Todas las categorías (curso + quizzes)
GET /api/v1/quizzes/129/categories?include_all=true
```

**Respuesta `200 OK`:**
```json
{
  "course_id": 129,
  "categories": [
    {
      "id": 3349,
      "name": "Default for Simulador",
      "contextid": 12345,
      "contextlevel": "module",
      "info": "",
      "questioncount": 0
    },
    {
      "id": 3440,
      "name": "visualizacion",
      "contextid": 12345,
      "contextlevel": "module",
      "info": "Preguntas de visualización",
      "questioncount": 45
    }
  ],
  "total": 2
}
```

**Nota:** `questioncount` indica cuántas preguntas tiene cada categoría. Útil para mostrar al usuario antes de cargarlas al quiz.

---

### 3. Crear categoría de preguntas

Crea una nueva categoría en el banco de preguntas.

```
POST /api/v1/quizzes/{course_id}/categories
```

**Body (JSON):**
```json
{
  "name": "Mi categoría",
  "info": "Descripción opcional",
  "cmid": 9873
}
```

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `name` | string | ✅ | Nombre de la categoría |
| `info` | string | ❌ | Descripción (default: `""`) |
| `cmid` | int | ❌ | Si se envía, la categoría se crea en el contexto del quiz. Si no, en el contexto del curso. |

**Respuesta `200 OK`:**
```json
{
  "success": true,
  "category_id": 3440,
  "name": "Mi categoría",
  "message": "Categoría 'Mi categoría' creada correctamente."
}
```

---

### 4. Preview de importación

Parsea un archivo de preguntas y muestra lo que se importaría **sin enviar nada a Moodle**. Útil para que el usuario revise antes de confirmar.

```
POST /api/v1/quizzes/preview-import
```

**Body: `multipart/form-data`**
| Campo | Tipo | Descripción |
|---|---|---|
| `file` | File | Archivo `.txt` (Aiken) o `.xml` (Moodle XML) |
| `format` | string | `"aiken"` o `"xml"` |

**Ejemplo con fetch:**
```javascript
const formData = new FormData();
formData.append('file', selectedFile);
formData.append('format', 'aiken');

const response = await fetch('/api/v1/quizzes/preview-import', {
  method: 'POST',
  body: formData,
});
const result = await response.json();
```

**Respuesta `200 OK`:**
```json
{
  "success": true,
  "course_id": 0,
  "quiz_name": null,
  "category_name": null,
  "format_used": "aiken",
  "total_questions_parsed": 45,
  "total_questions_imported": 0,
  "questions": [
    {
      "question_text": "¿Cuál es la capital de Francia?",
      "question_type": "multichoice",
      "options": [
        { "text": "Londres", "is_correct": false, "feedback": null },
        { "text": "París", "is_correct": true, "feedback": null },
        { "text": "Berlín", "is_correct": false, "feedback": null },
        { "text": "Madrid", "is_correct": false, "feedback": null }
      ],
      "correct_answer": "París",
      "default_grade": 1.0,
      "penalty": 0.3333333,
      "general_feedback": null,
      "name": "¿Cuál es la capital de Francia?"
    }
  ],
  "message": "Preview: 45 preguntas parseadas del archivo (aiken)",
  "errors": []
}
```

**Nota:** El array `questions` contiene todas las preguntas parseadas. Puedes usarlo para mostrar una tabla/lista de preview en el frontend.

---

### 5. Importar preguntas a Moodle

Importa las preguntas del archivo al banco de preguntas de Moodle.

```
POST /api/v1/quizzes/import
```

**Body: `multipart/form-data`**
| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `file` | File | ✅ | Archivo con preguntas |
| `format` | string | ✅ | `"aiken"` o `"xml"` |
| `course_id` | int | ✅ | ID del curso |
| `category_id` | int | ✅ | ID de la categoría destino |
| `category_name` | string | ❌ | Nombre de la categoría (metadata) |

**Ejemplo con fetch:**
```javascript
const formData = new FormData();
formData.append('file', selectedFile);
formData.append('format', 'aiken');
formData.append('course_id', '129');
formData.append('category_id', '3440');
formData.append('category_name', 'visualizacion');

const response = await fetch('/api/v1/quizzes/import', {
  method: 'POST',
  body: formData,
});
const result = await response.json();
```

**Respuesta `200 OK`:**
```json
{
  "success": true,
  "course_id": 129,
  "quiz_name": null,
  "category_name": "visualizacion",
  "format_used": "aiken",
  "total_questions_parsed": 45,
  "total_questions_imported": 45,
  "questions": [],
  "message": "Se importaron 45 preguntas correctamente al banco de preguntas.",
  "errors": []
}
```

**Nota:** En la importación real, el array `questions` viene vacío (a diferencia del preview).

---

### 6. Cargar preguntas al cuestionario

Agrega preguntas desde una categoría del banco al cuestionario. **Este es el paso que conecta el banco de preguntas con el quiz visible para los alumnos.**

```
POST /api/v1/quizzes/{course_id}/configure-questions
```

**Body (JSON):**

#### Modo "all" — Todas las preguntas:
```json
{
  "quiz_cmid": 9873,
  "category_id": 3440,
  "mode": "all"
}
```

#### Modo "random" — Preguntas aleatorias:
```json
{
  "quiz_cmid": 9873,
  "category_id": 3440,
  "mode": "random",
  "num_questions": 20,
  "include_subcategories": false
}
```

**Campos del body:**
| Campo | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|
| `quiz_cmid` | int | ✅ | — | Course Module ID del cuestionario |
| `category_id` | int | ✅ | — | ID de la categoría de preguntas |
| `mode` | string | ❌ | `"all"` | `"all"` o `"random"` |
| `num_questions` | int | ❌ | `10` | Cantidad de preguntas aleatorias (solo para `random`) |
| `include_subcategories` | bool | ❌ | `false` | Incluir subcategorías en modo `random` |

**Respuesta `200 OK`:**
```json
{
  "success": true,
  "quiz_name": "Evaluación teórica Primer Parcial",
  "mode": "all",
  "questions_added": 45,
  "message": "Added 45 question(s) from category 'visualizacion' to quiz 'Evaluación teórica Primer Parcial'."
}
```

**Diferencia entre modos:**

| | Modo `all` | Modo `random` |
|---|---|---|
| Preguntas en el quiz | Todas las de la categoría | N referencias aleatorias |
| Cada estudiante ve | Las mismas preguntas | Subconjunto diferente |
| Control de cantidad | Automático (todas) | `num_questions` define cuántas |
| Intentos múltiples | Mismas preguntas | Preguntas diferentes cada vez |

---

### 7. Configurar tiempo límite del cuestionario

Establece el tiempo límite del quiz.

```
POST /api/v1/quizzes/{course_id}/settings
```

**Body (JSON):**
```json
{
  "quiz_cmid": 9873,
  "time_limit": 3600
}
```

| Campo | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|
| `quiz_cmid` | int | ✅ | — | Course Module ID del cuestionario |
| `time_limit` | int | ❌ | `0` | Tiempo en segundos. `0` = sin límite |

**Tabla de conversión de tiempos:**
| Valor | Tiempo |
|---|---|
| `0` | Sin límite |
| `900` | 15 minutos |
| `1800` | 30 minutos |
| `3600` | 1 hora |
| `5400` | 1 hora 30 minutos |
| `7200` | 2 horas |

**Respuesta `200 OK`:**
```json
{
  "success": true,
  "quiz_name": "Evaluación teórica Primer Parcial",
  "time_limit": 3600,
  "time_limit_display": "1h",
  "message": "Quiz 'Evaluación teórica Primer Parcial' updated. Time limit: 1h."
}
```

---

### 8. Formatos de importación soportados

Retorna los formatos de importación disponibles con ejemplos.

```
GET /api/v1/quizzes/supported-formats
```

**Respuesta `200 OK`:**
```json
{
  "formats": [
    {
      "format": "aiken",
      "name": "Aiken",
      "extension": ".txt",
      "description": "Formato simple de texto plano para preguntas de opción múltiple...",
      "example": "What is the capital of France?\nA. London\nB. Paris\n..."
    },
    {
      "format": "xml",
      "name": "Moodle XML",
      "extension": ".xml",
      "description": "Formato XML nativo de Moodle...",
      "example": "<?xml version=\"1.0\"?>..."
    }
  ]
}
```

---

## Modelos de Datos

### QuizActivity
```typescript
interface QuizActivity {
  id: number;              // ID instancia del quiz
  coursemodule: number;     // ⭐ cmid — usar este para los demás endpoints
  course: number;          // ID del curso
  name: string;            // Nombre del cuestionario
  intro: string | null;    // Descripción HTML
  timelimit: number;       // Tiempo límite en segundos (0 = sin límite)
  attempts: number;        // Máximo de intentos (0 = ilimitado)
  grade: number;           // Calificación máxima
}
```

### QuestionCategory
```typescript
interface QuestionCategory {
  id: number;                        // ⭐ category_id — usar para importar/cargar
  name: string;                      // Nombre de la categoría
  contextid: number;                 // ID del contexto Moodle
  contextlevel: "course" | "module"; // A qué nivel pertenece
  info: string | null;               // Descripción
  questioncount: number;             // Cantidad de preguntas en esta categoría
}
```

### ParsedQuestion (preview)
```typescript
interface ParsedQuestion {
  question_text: string;
  question_type: "multichoice" | "truefalse" | "shortanswer" | "essay" | "numerical" | "matching";
  options: ParsedOption[];
  correct_answer: string | null;
  default_grade: number;
  penalty: number;
  general_feedback: string | null;
  name: string | null;
}

interface ParsedOption {
  text: string;
  is_correct: boolean;
  feedback: string | null;
}
```

---

## Manejo de Errores

Todos los endpoints retornan errores con HTTP `400` y este formato:

```json
{
  "detail": {
    "message": "Descripción del error",
    "error_code": "codigo_moodle",
    "debug_info": "Información técnica adicional (o null)"
  }
}
```

### Errores comunes

| Código | Causa | Solución |
|---|---|---|
| `invalidparameter` | Parámetro incorrecto (cmid, category_id, etc.) | Verificar que los IDs existen |
| `accessexception` | El token no tiene permisos | Agregar las funciones al servicio web en Moodle |
| `codingerror` | Error interno del plugin Moodle | Actualizar el plugin a la última versión |
| `invalidrecord` | Registro no encontrado en la BD | Verificar que el curso/quiz/categoría existe |

---

## Ejemplo de Flujo Completo (Código)

### JavaScript/TypeScript — Flujo completo

```typescript
const API_BASE = 'http://localhost:8000/api/v1/quizzes';

// ═══════════════════════════════════════════════════
// PASO 1: Listar quizzes del curso
// ═══════════════════════════════════════════════════
const quizzesRes = await fetch(`${API_BASE}/129/activities`);
const quizzes = await quizzesRes.json();
// quizzes.quizzes[0].coursemodule → 9873 (cmid)

// ═══════════════════════════════════════════════════
// PASO 2: Listar categorías del quiz
// ═══════════════════════════════════════════════════
const catsRes = await fetch(`${API_BASE}/129/categories?cmid=9873`);
const categories = await catsRes.json();
// categories.categories → [{ id: 3440, name: "visualizacion", questioncount: 0 }, ...]

// ═══════════════════════════════════════════════════
// PASO 3 (Opcional): Crear categoría si no existe
// ═══════════════════════════════════════════════════
const newCatRes = await fetch(`${API_BASE}/129/categories`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    name: 'Preguntas Parcial 1',
    cmid: 9873,
  }),
});
const newCat = await newCatRes.json();
// newCat.category_id → 3500

// ═══════════════════════════════════════════════════
// PASO 4: Preview del archivo
// ═══════════════════════════════════════════════════
const previewForm = new FormData();
previewForm.append('file', fileInput.files[0]);
previewForm.append('format', 'aiken');

const previewRes = await fetch(`${API_BASE}/preview-import`, {
  method: 'POST',
  body: previewForm,
});
const preview = await previewRes.json();
// preview.total_questions_parsed → 45
// preview.questions → [ ... ] ← mostrar al usuario para confirmar

// ═══════════════════════════════════════════════════
// PASO 5: Importar al banco de preguntas
// ═══════════════════════════════════════════════════
const importForm = new FormData();
importForm.append('file', fileInput.files[0]);
importForm.append('format', 'aiken');
importForm.append('course_id', '129');
importForm.append('category_id', '3440');

const importRes = await fetch(`${API_BASE}/import`, {
  method: 'POST',
  body: importForm,
});
const importResult = await importRes.json();
// importResult.total_questions_imported → 45

// ═══════════════════════════════════════════════════
// PASO 6: Cargar preguntas al quiz
// ═══════════════════════════════════════════════════

// Opción A: Todas las preguntas
const configResAll = await fetch(`${API_BASE}/129/configure-questions`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    quiz_cmid: 9873,
    category_id: 3440,
    mode: 'all',
  }),
});

// Opción B: 20 preguntas aleatorias
const configResRandom = await fetch(`${API_BASE}/129/configure-questions`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    quiz_cmid: 9873,
    category_id: 3440,
    mode: 'random',
    num_questions: 20,
  }),
});

// ═══════════════════════════════════════════════════
// PASO 7: Configurar tiempo límite (1 hora)
// ═══════════════════════════════════════════════════
const settingsRes = await fetch(`${API_BASE}/129/settings`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    quiz_cmid: 9873,
    time_limit: 3600,
  }),
});
const settings = await settingsRes.json();
// settings.time_limit_display → "1h"
// ✅ ¡Quiz listo!
```

---

## Resumen rápido de endpoints

| # | Método | Endpoint | Descripción |
|---|---|---|---|
| 1 | `GET` | `/{course_id}/activities` | Listar quizzes del curso |
| 2 | `GET` | `/{course_id}/categories` | Listar categorías de preguntas |
| 3 | `POST` | `/{course_id}/categories` | Crear categoría de preguntas |
| 4 | `POST` | `/preview-import` | Preview sin importar (multipart) |
| 5 | `POST` | `/import` | Importar preguntas al banco (multipart) |
| 6 | `POST` | `/{course_id}/configure-questions` | Cargar preguntas al quiz (JSON) |
| 7 | `POST` | `/{course_id}/settings` | Configurar tiempo límite (JSON) |
| 8 | `GET` | `/supported-formats` | Formatos soportados con ejemplos |

> **Nota sobre Content-Type:** Los endpoints 4 y 5 usan `multipart/form-data` porque reciben archivos. El resto usa `application/json`.
