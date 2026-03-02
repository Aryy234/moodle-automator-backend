Sistema de Cuestionarios — Análisis y Plan de Implementación
Análisis del documento 
sistema_cuestionarios.md
He analizado tu documento junto con toda la base de código existente. A continuación presento observaciones, mejoras propuestas y un plan de implementación que se integra correctamente con tu arquitectura actual.

Problemas detectados en el diseño original
1. Introduce una base de datos innecesariamente
Tu proyecto actual no usa base de datos — todo es comunicación directa con la API de Moodle a través de 
MoodleClient
. El documento propone tablas para cursos, categorias, cuestionarios y preguntas, lo cual:

Duplica datos que ya existen en Moodle
Requiere agregar SQLAlchemy/Alembic como dependencias nuevas
Introduce problemas de sincronización (tu base local vs Moodle)
IMPORTANT

Propuesta: Mantener la filosofía actual del proyecto — sin base de datos local. Usar Moodle como fuente de verdad y solo parsear/transformar los archivos de importación en memoria antes de enviarlos a Moodle.

2. Los formatos de importación no coinciden con la implementación propuesta
El documento dice soportar Aiken (.txt) y Moodle XML, pero toda la lógica de importación está escrita para JSON personalizado. Esto es contradictorio.

IMPORTANT

Propuesta: Implementar parsers reales para los formatos estándar de Moodle:

Formato Aiken (.txt) — formato simple de opción múltiple
Moodle XML (.xml) — formato completo que soporta todos los tipos de preguntas
Adicionalmente, se puede soportar JSON como un tercer formato conveniente para integraciones.

3. La publicación intenta reinventar funciones de Moodle
Tu Moodle ya tiene funciones Web Service para manejar cuestionarios. En vez de replicar lógica localmente (mezclar, limitar preguntas), es mejor:

Usar las funciones nativas de Moodle para crear preguntas en el banco de preguntas
Usar las funciones de Moodle para importar cuestionarios directamente
4. Endpoint design no sigue el patrón existente
Los endpoints del documento usan prefijos como /cursos/ en español, mientras tu API actual usa /api/v1/courses/ en inglés. Debemos mantener consistencia.

Diseño Mejorado
Flujo propuesto (simplificado)
1. Seleccionar curso (ya existente en tu app)  →  GET /api/v1/courses/
         ↓
2. Obtener cuestionarios del curso en Moodle   →  GET /api/v1/quizzes/{course_id}/activities
         ↓
3. Subir archivo con preguntas (Aiken/XML)     →  POST /api/v1/quizzes/import
   → El backend parsea el archivo
   → Crea las preguntas en el banco de preguntas de Moodle
   → Las vincula al cuestionario seleccionado
         ↓
4. Respuesta con resumen de lo importado
NOTE

Este flujo elimina la necesidad de base de datos, estados intermedios (borrador/publicado), y mantiene a Moodle como fuente de verdad.

Endpoints propuestos
Método	Endpoint	Descripción
GET	/api/v1/quizzes/{course_id}/activities	Lista cuestionarios (quiz activities) de un curso en Moodle
GET	/api/v1/quizzes/{course_id}/categories	Lista categorías de preguntas del curso
POST	/api/v1/quizzes/{course_id}/categories	Crear nueva categoría de preguntas
POST	/api/v1/quizzes/import	Importar preguntas desde archivo (Aiken/XML/JSON)
POST	/api/v1/quizzes/preview-import	Preview: parsea el archivo y muestra las preguntas sin enviar a Moodle
GET	/api/v1/quizzes/supported-formats	Devuelve los formatos soportados con ejemplos
Proposed Changes
Funciones de Moodle Web Service necesarias
Antes de implementar, necesitas agregar estas funciones al servicio web de tu token en Moodle:

Función	Propósito
mod_quiz_get_quizzes_by_courses	Listar cuestionarios de un curso
core_question_get_categories	Listar categorías de preguntas (custom o via DB)
qbank_importquestions_import_questions	Importar preguntas (Moodle 4.x)
WARNING

La API de Moodle para importar preguntas (qbank_importquestions_import_questions) solo está disponible en Moodle 4.3+. Si tu versión es anterior, necesitaremos un enfoque alternativo usando el plugin local_sectionedit ampliado, o la función core_question_submit_question_data disponible desde Moodle 4.0.

Por favor confirma tu versión de Moodle para elegir la estrategia correcta.

Integration Layer
[MODIFY] 
moodle_client.py
Agregar nuevos métodos al 
MoodleClient
:

get_quizzes_by_course(course_id) — llama a mod_quiz_get_quizzes_by_courses
get_question_categories(course_id) — obtiene categorías de preguntas
create_question_category(course_id, name) — crea una categoría
import_questions(course_id, category_id, format, file_content) — importa preguntas al banco
Services Layer
[NEW] 
quiz_service.py
Servicio con la lógica de negocio:

parse_aiken_file(content: str) -> list[ParsedQuestion] — parser para formato Aiken
parse_moodle_xml(content: str) -> list[ParsedQuestion] — parser para Moodle XML
preview_import(file, format) -> PreviewResult — parsea sin enviar
import_questions(course_id, quiz_id, category_name, file, format) — flujo completo
Schemas
[NEW] 
quiz.py
ParsedQuestion — pregunta parseada del archivo
QuizActivity — actividad cuestionario de Moodle
QuestionCategory — categoría de preguntas
QuizImportRequest — request para importación
QuizImportResponse — respuesta con resumen
QuizPreviewResponse — preview de las preguntas parseadas
API Router
[NEW] 
quizzes.py
Los 6 endpoints listados arriba, siguiendo el mismo patrón de 
courses.py
 y 
editor.py
.

[MODIFY] 
init
.py
Registrar el nuevo router: api_router.include_router(quizzes.router, prefix="/quizzes", tags=["Quizzes"])

Dependencies
[MODIFY] 
requirements.txt
Agregar python-multipart>=0.0.9 para soportar UploadFile en FastAPI.

User Review Required
CAUTION

Necesito que confirmes estos puntos antes de proceder:

¿Cuál es tu versión de Moodle? — Esto determina qué funciones Web Service puedo usar para importar preguntas. Puedes verificarlo con el endpoint GET /api/v1/courses/health/check que ya tienes (campo moodle_version).

¿Estás de acuerdo con NO usar base de datos local? — Mantendríamos la filosofía actual del proyecto. Si prefieres tener persistencia local, puedo agregar SQLite + SQLAlchemy, pero recomiendo evitarlo.

¿Qué formatos de importación necesitas prioritariamente? — ¿Aiken + Moodle XML son suficientes? ¿O también necesitas el formato JSON personalizado que describiste en el documento?

¿Tu token de Moodle ya tiene habilitada la función mod_quiz_get_quizzes_by_courses? — Si no, necesitarás agregarla al servicio web.

Verification Plan
Manual Verification
Endpoint de formatos soportados: GET /api/v1/quizzes/supported-formats → debe retornar la lista de formatos
Listar quizzes de un curso: GET /api/v1/quizzes/{course_id}/activities → debe retornar las actividades cuestionario disponibles
Preview de importación: Subir un archivo Aiken de prueba a POST /api/v1/quizzes/preview-import → debe retornar las preguntas parseadas sin enviarlas a Moodle
Importación real: Subir el mismo archivo a POST /api/v1/quizzes/import con un quiz_id válido → verificar en Moodle que las preguntas aparecen en el banco de preguntas
NOTE

No existen tests automatizados en el proyecto actualmente. Dado que el proyecto depende de un Moodle externo, la verificación será principalmente manual a través de Swagger UI (/docs) y verificación directa en Moodle. Te pediré que pruebes los endpoints contra tu Moodle real.