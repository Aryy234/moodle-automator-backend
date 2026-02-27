# 🚀 Moodle Course Automator (MCA) - Plan de Proyecto

## 📝 Visión General
El objetivo es desarrollar una aplicación web de ejecución local que automatice el proceso de duplicación y personalización de cursos en Moodle. La herramienta permitirá a los docentes o administradores clonar un curso base y actualizar automáticamente elementos específicos del diseño (como links de perfiles) sin entrar manualmente al código fuente de Moodle.

---

## 🛠️ Stack Tecnológico
Para garantizar velocidad, minimalismo y facilidad de desarrollo, utilizaremos:

| Capa | Tecnología | Razón de elección |
| :--- | :--- | :--- |
| **Backend** | Python (FastAPI) | Ligero, asíncrono y excelente para manipulación de strings. |
| **Frontend** | Vue.js 3 + Vite | Reactividad rápida y estructura de componentes limpia. |
| **Procesamiento** | BeautifulSoup4 | Estándar de la industria para parsear y editar HTML de forma segura. |
| **Comunicación** | Axios + REST API | Protocolo estándar para la integración entre capas y con Moodle. |

---

## 🏗️ Arquitectura del Sistema

### 1. Backend (Arquitectura en Capas)
* **API Layer (FastAPI):** Define los endpoints que el frontend consumirá.
* **Service Layer:** Contiene la lógica de negocio (clonación y edición de HTML).
* **Integration Layer (Gateway):** Encargado exclusivo de hablar con la API de Moodle mediante Tokens.
* **Schemas (Pydantic):** Validación de datos de entrada y salida.

### 2. Frontend (Arquitectura Modular)
* **Views:** Interfaz minimalista (Dashboard y Editor).
* **Store (Pinia):** Manejo del estado global (curso seleccionado, tokens temporales).
* **Services:** Funciones de llamada a la API local.

---

## ⚙️ Flujo de Funcionamiento (El "Clonador Inteligente")

1.  **Conexión:** La App se conecta a Moodle usando un Token de Web Service.
2.  **Selección:** El usuario elige un curso de la lista obtenida vía API.
3.  **Configuración de Personalización:**
    * Se ingresa el nuevo nombre del curso.
    * Se ingresa el **Nuevo Link del Docente** en un input específico.
4.  **Procesamiento (Cerebro):**
    * El backend clona el curso mediante `core_course_duplicate_course`.
    * El script recorre los módulos (páginas, etiquetas) del curso nuevo.
    * **BeautifulSoup** escanea el código fuente buscando etiquetas `<a>` relacionadas al perfil docente y reemplaza el atributo `href`.
5.  **Finalización:** Se notifican los cambios realizados y se entrega el link del nuevo curso listo.

---

## 🎨 Diseño y UX (Minimalista)
* **Estética:** Uso de Tailwind CSS para un diseño limpio con mucho espacio en blanco.
* **Feedback:** Barras de progreso reales para procesos largos de Moodle.
* **Seguridad:** Ejecución en `localhost`, manteniendo los tokens de acceso seguros en la máquina local.

---

## 📅 Roadmap de Desarrollo

1.  **Fase 1 (Core):** Configuración de FastAPI y cliente de conexión a Moodle.
2.  **Fase 2 (Procesador):** Implementación del servicio de edición de HTML con BeautifulSoup.
3.  **Fase 3 (Frontend):** Creación de la interfaz en Vue.js y conexión con el backend.
4.  **Fase 4 (Pruebas):** Testeo con cursos reales y validación de links.

---

> **Nota para el desarrollador:** Este proyecto prioriza la mantenibilidad. Cada módulo debe tener una sola responsabilidad para facilitar futuras expansiones (como edición de archivos CSS o cambio masivo de fechas).

# 🚀 Moodle Course Automator (MCA) - Plan de Proyecto

## 📝 Visión General
Desarrollo de una herramienta local para la duplicación y personalización automatizada de cursos en Moodle, enfocada en la edición masiva de enlaces (links) dentro del contenido HTML.

---

## 🏗️ Estructura del Proyecto (Estructura de Carpetas)

El proyecto se divide en dos grandes contenedores: `backend` (Lógica y API) y `frontend` (Interfaz de usuario).

### 📁 Backend (FastAPI)
```text
moodle-automator-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Punto de entrada y configuración de CORS
│   ├── api/                    # Definición de rutas (Endpoints)
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── courses.py      # Rutas para listar y duplicar cursos
│   │   │   └── editor.py       # Rutas para procesar links HTML
│   ├── core/                   # Configuración global
│   │   └── config.py           # Gestión de variables .env (Tokens, URLs)
│   ├── integration/            # Comunicación con Moodle (Gateways)
│   │   └── moodle_client.py    # Cliente HTTP para Web Services de Moodle
│   ├── services/               # Lógica de Negocio (Service Layer)
│   │   ├── cloner_service.py   # Orquestación de clonado
│   │   └── html_processor.py   # Procesamiento con BeautifulSoup4
│   └── schemas/                # Modelos de datos y validación (Pydantic)
│       ├── course.py
│       └── editor.py
├── .env                        # Variables de entorno (Token Moodle)
├── .gitignore
└── requirements.txt            # Dependencias (fastapi, uvicorn, httpx, bs4)


### 📁 Frontend (Vue.js + Vite)
moodle-automator-frontend/
├── src/
│   ├── api/                    # Funciones para llamar al Backend local
│   │   └── index.js            # Instancia de Axios y llamadas API
│   ├── assets/                 # Estilos (Tailwind) e imágenes
│   ├── components/             # Componentes reutilizables (UI)
│   │   ├── CourseCard.vue      # Tarjeta visual del curso
│   │   ├── StepProgress.vue    # Barra de estado del proceso
│   │   └── SetupForm.vue       # Formulario de personalización de links
│   ├── layouts/                # Estructura visual base
│   ├── stores/                 # Gestión de estado (Pinia)
│   │   └── useCourseStore.js   # Almacén de cursos y datos seleccionados
│   ├── views/                  # Páginas principales
│   │   ├── Dashboard.vue       # Selección de curso original
│   │   └── Customizer.vue      # Interfaz de edición de links
│   ├── App.vue                 # Componente raíz
│   └── main.js                 # Configuración inicial de Vue
├── index.html
├── package.json
├── tailwind.config.js          # Configuración de diseño minimalista
└── vite.config.js


Configuración del api y token de mooldle

Clonador de cursos: ea9f53597f093e668549a4c4ec892d19

Usuario ARIEL ELIZALDE
correo electrónico: pasante.sistemas2@intec.edu.ce


funcionalidades de la api aplicadas:


| Función                       | Descripción                                   | Permisos requeridos                                                                                                        |
|-------------------------------|-----------------------------------------------|----------------------------------------------------------------------------------------------------------------------------|
| core_course_duplicate_course  | Duplicate an existing course (creating a new one). | moodle/backup:backupcourse, moodle/restore:restorecourse, moodle/course:create                                              |
| core_course_get_contents      | Get course contents                           | moodle/course:update, moodle/course:viewhiddencourses                                                                      |
| core_course_update_courses    | Update courses                                | moodle/course:update, moodle/course:changecategory, moodle/course:changefullname, moodle/course:changeshortname, moodle/course:changeidnumber, moodle/course:changesummary, moodle/course:visibility |