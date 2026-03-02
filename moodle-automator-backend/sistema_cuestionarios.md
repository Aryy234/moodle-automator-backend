# Sistema de Cuestionarios con FastAPI + Moodle

## Visión General

Sistema de importación de preguntas al banco de preguntas de Moodle desde archivos
en formato **Aiken** (.txt) y **Moodle XML** (.xml). No utiliza base de datos local —
Moodle es la **fuente de verdad** para cursos, cuestionarios, categorías y preguntas.

---

## Flujo completo

```
1. Seleccionar el curso (existente en Moodle)
   → GET /api/v1/courses/
         ↓
2. Ver cuestionarios del curso en Moodle
   → GET /api/v1/quizzes/{course_id}/activities
         ↓
3. Ver / crear categoría de preguntas
   → GET  /api/v1/quizzes/{course_id}/categories
   → POST /api/v1/quizzes/{course_id}/categories
         ↓
4. Subir archivo con preguntas (Aiken o XML)
   → POST /api/v1/quizzes/preview-import   (solo parseo, sin enviar)
   → POST /api/v1/quizzes/import           (parseo + envío a Moodle)
         ↓
5. Las preguntas aparecen en el banco de preguntas de Moodle
```

---

## Endpoints

```
# QUIZZES — actividades cuestionario de un curso
GET   /api/v1/quizzes/{course_id}/activities         # Listar cuestionarios del curso

# CATEGORÍAS DE PREGUNTAS
GET   /api/v1/quizzes/{course_id}/categories         # Ver categorías del banco de preguntas
POST  /api/v1/quizzes/{course_id}/categories         # Crear nueva categoría

# IMPORTACIÓN DE PREGUNTAS
POST  /api/v1/quizzes/preview-import                 # Preview: parsea sin enviar
POST  /api/v1/quizzes/import                         # Importar preguntas a Moodle

# INFORMACIÓN
GET   /api/v1/quizzes/supported-formats              # Formatos soportados con ejemplos
```

---

## Formatos de importación soportados

### Formato Aiken (.txt)

Formato simple de texto plano, solo para preguntas de **opción múltiple**.

```
¿En qué año comenzó la Segunda Guerra Mundial?
A. 1935
B. 1939
C. 1941
D. 1945
ANSWER: B

La Tierra gira alrededor del Sol
A. Verdadero
B. Falso
ANSWER: A
```

**Reglas del formato Aiken:**
- El enunciado ocupa una o más líneas antes de las opciones
- Las opciones van con letra seguida de `.` o `)` y un espacio
- La respuesta correcta es `ANSWER: X` donde X es la letra
- Una línea en blanco separa las preguntas (opcional)

### Formato Moodle XML (.xml)

Formato nativo de Moodle. Soporta múltiples tipos de preguntas:
`multichoice`, `truefalse`, `shortanswer`, `essay`, `numerical`, `matching`.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<quiz>
  <question type="multichoice">
    <name><text>Inicio de la WWII</text></name>
    <questiontext format="html">
      <text><![CDATA[¿En qué año comenzó la Segunda Guerra Mundial?]]></text>
    </questiontext>
    <defaultgrade>1</defaultgrade>
    <single>true</single>
    <answer fraction="0" format="html">
      <text>1935</text>
    </answer>
    <answer fraction="100" format="html">
      <text>1939</text>
    </answer>
    <answer fraction="0" format="html">
      <text>1941</text>
    </answer>
    <answer fraction="0" format="html">
      <text>1945</text>
    </answer>
  </question>

  <question type="truefalse">
    <name><text>Tierra plana</text></name>
    <questiontext format="html">
      <text><![CDATA[La Tierra es plana]]></text>
    </questiontext>
    <answer fraction="0" format="moodle_auto_format">
      <text>true</text>
    </answer>
    <answer fraction="100" format="moodle_auto_format">
      <text>false</text>
    </answer>
  </question>
</quiz>
```

---

## Detalle de endpoints

### `GET /api/v1/quizzes/{course_id}/activities`

Lista las actividades de tipo cuestionario (quiz) de un curso.

**Respuesta:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `course_id` | int | ID del curso |
| `quizzes` | array | Lista de quizzes |
| `total` | int | Total de quizzes |

Cada quiz:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | int | ID de la instancia del quiz |
| `coursemodule` | int | ID del módulo de curso (cmid) |
| `name` | string | Nombre del cuestionario |
| `intro` | string | Descripción/introducción |
| `timelimit` | int | Tiempo límite en segundos |
| `attempts` | int | Intentos máximos (0 = ilimitado) |
| `grade` | float | Calificación máxima |

---

### `GET /api/v1/quizzes/{course_id}/categories`

Lista las categorías de preguntas del banco de preguntas del curso.

**Respuesta:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `course_id` | int | ID del curso |
| `categories` | array | Lista de categorías |
| `total` | int | Total de categorías |

---

### `POST /api/v1/quizzes/{course_id}/categories`

Crea una nueva categoría en el banco de preguntas.

**Body (JSON):**

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `name` | string | Sí | Nombre de la categoría |
| `info` | string | No | Descripción |

---

### `POST /api/v1/quizzes/preview-import`

Parsea un archivo y muestra las preguntas encontradas **sin enviarlas a Moodle**.

**Body (multipart/form-data):**

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `file` | File | Sí | Archivo de preguntas (.txt o .xml) |
| `format` | string | Sí | `"aiken"` o `"xml"` |

**Respuesta:** Lista de preguntas parseadas con su tipo, opciones y respuesta correcta.

---

### `POST /api/v1/quizzes/import`

Importa preguntas al banco de preguntas de un curso en Moodle.

**Body (multipart/form-data):**

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `file` | File | Sí | Archivo de preguntas (.txt o .xml) |
| `format` | string | Sí | `"aiken"` o `"xml"` |
| `course_id` | int | Sí | ID del curso destino |
| `category_id` | int | Sí | ID de la categoría destino |
| `category_name` | string | No | Nombre de categoría (metadata) |

**Respuesta:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `success` | bool | Si la importación fue exitosa |
| `course_id` | int | ID del curso |
| `format_used` | string | Formato procesado |
| `total_questions_parsed` | int | Preguntas encontradas en el archivo |
| `total_questions_imported` | int | Preguntas importadas a Moodle |
| `message` | string | Mensaje descriptivo |
| `errors` | array | Lista de errores (si los hay) |

---

## Arquitectura (archivos del proyecto)

```
app/
├── api/v1/
│   └── quizzes.py              # Router con 6 endpoints
├── schemas/
│   └── quiz.py                 # Modelos Pydantic (ParsedQuestion, QuizActivity, etc.)
├── services/
│   └── quiz_service.py         # Parsers (Aiken, XML), generador XML, orquestación
└── integration/
    └── moodle_client.py        # Métodos: get_quizzes, get/create categories, import XML
```

---

## Funciones de Moodle Web Service requeridas

| Función | Para qué sirve | Origen |
|---------|----------------|--------|
| `mod_quiz_get_quizzes_by_courses` | Listar cuestionarios de un curso | Core Moodle |
| `local_sectionedit_get_question_categories` | Listar categorías de preguntas | Plugin local_sectionedit v1.2+ |
| `local_sectionedit_create_question_category` | Crear categoría de preguntas | Plugin local_sectionedit v1.2+ |
| `local_sectionedit_import_questions` | Importar preguntas (Aiken/XML) al banco | Plugin local_sectionedit v1.2+ |

> **¿Por qué funciones custom?** — Moodle no expone `core_question_get_categories`,
> `core_question_create_category` ni `qbank_importquestions_import_questions` como
> funciones de Web Service externas. El plugin `local_sectionedit` las implementa
> usando las APIs internas de PHP de Moodle (acceso directo a BD + clases `qformat_*`).
>
> **Instalación:** Actualizar el plugin `local_sectionedit` a v1.2.0 y agregar las
> 3 nuevas funciones al servicio web:
> Administración del sitio → Servidor → Servicios externos → [tu servicio] → Funciones → Agregar

---

## Flujo de importación (lógica interna)

```
1. El usuario sube un archivo (.txt o .xml)
2. El backend detecta el formato (aiken / xml)
3. El parser correspondiente extrae las preguntas
4. Si es Aiken → se convierte a Moodle XML internamente
5. Se envía el XML al banco de preguntas de Moodle vía Web Service
6. Moodle procesa e importa las preguntas
7. Se retorna el resultado al frontend
```

**Nota importante:** Si el archivo ya es Moodle XML, se envía directamente sin
transformaciones intermedias. Solo los archivos Aiken se convierten a XML.