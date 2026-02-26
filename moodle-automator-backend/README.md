# 🚀 Moodle Course Automator - Backend

API REST construida con FastAPI para la automatización de duplicación y personalización de cursos en Moodle.

## 📋 Requisitos

- Python 3.10+
- Acceso a un servidor Moodle con Web Services habilitados
- Token de Web Service con permisos para:
  - `core_course_duplicate_course`
  - `core_course_get_contents`
  - `core_course_update_courses`

## 🛠️ Instalación

### 1. Crear entorno virtual

```bash
cd moodle-automator-backend
python -m venv venv

# Windows
.\venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

```bash
# Copiar plantilla y editar
cp .env.example .env
```

Edita el archivo `.env` con tu configuración:

```env
MOODLE_URL=https://tu-moodle.edu
MOODLE_TOKEN=tu_token_de_webservice
DEBUG=true
```

### 4. Ejecutar el servidor

```bash
# Desarrollo con recarga automática
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# O directamente
python -m app.main
```

## 📡 Endpoints Principales

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/courses/` | Lista todos los cursos disponibles |
| GET | `/api/v1/courses/{id}` | Obtiene un curso específico |
| GET | `/api/v1/courses/{id}/contents` | Obtiene contenido del curso |
| GET | `/api/v1/courses/{id}/scan-links` | Escanea enlaces en el curso |
| POST | `/api/v1/courses/duplicate` | Duplica un curso |
| GET | `/api/v1/courses/health/check` | Verifica conexión con Moodle |
| POST | `/api/v1/editor/process-html` | Procesa HTML y reemplaza enlaces |
| GET | `/api/v1/editor/patterns` | Muestra patrones de detección |

## 📚 Documentación API

Una vez ejecutando el servidor:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🏗️ Estructura del Proyecto

```
moodle-automator-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Punto de entrada FastAPI
│   ├── api/
│   │   ├── v1/
│   │   │   ├── courses.py      # Rutas de cursos
│   │   │   └── editor.py       # Rutas del editor HTML
│   ├── core/
│   │   └── config.py           # Configuración global
│   ├── integration/
│   │   └── moodle_client.py    # Cliente HTTP para Moodle
│   ├── services/
│   │   ├── cloner_service.py   # Lógica de clonación
│   │   └── html_processor.py   # Procesamiento con BeautifulSoup
│   └── schemas/
│       ├── course.py           # Modelos de curso
│       └── editor.py           # Modelos del editor
├── .env                        # Variables de entorno (no versionar)
├── .env.example                # Plantilla de configuración
├── .gitignore
├── requirements.txt
└── README.md
```

## 🔐 Permisos de Moodle Requeridos

El token debe tener las siguientes capacidades:

- `moodle/backup:backupcourse`
- `moodle/restore:restorecourse`
- `moodle/course:create`
- `moodle/course:update`
- `moodle/course:viewhiddencourses`

## 🧪 Ejemplo de Uso

### Duplicar un curso

```bash
curl -X POST "http://localhost:8000/api/v1/courses/duplicate" \
  -H "Content-Type: application/json" \
  -d '{
    "source_course_id": 2,
    "new_fullname": "Mi Nuevo Curso",
    "new_shortname": "MNC-2024",
    "new_teacher_profile_url": "https://moodle.edu/user/view.php?id=123"
  }'
```

### Escanear enlaces de un curso

```bash
curl "http://localhost:8000/api/v1/courses/2/scan-links"
```

## 📝 Notas de Desarrollo

- La API utiliza patrones singleton para cliente HTTP y servicios
- El procesador HTML usa BeautifulSoup4 con parser lxml
- Los errores de Moodle se capturan y transforman en respuestas HTTP apropiadas
- CORS está configurado para desarrollo local (puertos 5173)

## 📄 Licencia

Proyecto interno INTEC - Todos los derechos reservados.
