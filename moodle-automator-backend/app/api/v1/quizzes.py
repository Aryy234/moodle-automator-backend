"""
Quizzes Routes

Endpoints para el sistema de cuestionarios:
- Listar actividades cuestionario de un curso
- Listar y crear categorías de preguntas
- Importar preguntas desde archivos Aiken o Moodle XML
- Preview de importación
- Formatos soportados
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form

from app.schemas.quiz import (
    QuizActivitiesResponse,
    QuizActivity,
    QuestionCategoriesResponse,
    QuestionCategory,
    CreateCategoryRequest,
    CreateCategoryResponse,
    QuizImportResponse,
    ImportFormat,
    FormatInfo,
    SupportedFormatsResponse,
    ConfigureQuizQuestionsRequest,
    ConfigureQuizQuestionsResponse,
    UpdateQuizSettingsRequest,
    UpdateQuizSettingsResponse,
)
from app.services.quiz_service import QuizService, get_quiz_service
from app.integration.moodle_client import MoodleAPIError

router = APIRouter()


# ==================== AIKEN & XML EXAMPLES ====================

AIKEN_EXAMPLE = """What is the capital of France?
A. London
B. Paris
C. Berlin
D. Madrid
ANSWER: B

What color is the sky on a clear day?
A. Green
B. Red
C. Blue
D. Yellow
ANSWER: C"""

XML_EXAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<quiz>
  <question type="multichoice">
    <name><text>Capital of France</text></name>
    <questiontext format="html">
      <text><![CDATA[What is the capital of France?]]></text>
    </questiontext>
    <defaultgrade>1</defaultgrade>
    <single>true</single>
    <answer fraction="0" format="html">
      <text>London</text>
    </answer>
    <answer fraction="100" format="html">
      <text>Paris</text>
    </answer>
    <answer fraction="0" format="html">
      <text>Berlin</text>
    </answer>
  </question>
</quiz>"""


# ==================== QUIZ ACTIVITIES ====================


@router.get(
    "/{course_id}/activities",
    response_model=QuizActivitiesResponse,
    summary="Listar cuestionarios del curso",
    description="Obtiene las actividades tipo cuestionario (quiz) de un curso desde Moodle.",
)
async def list_quiz_activities(
    course_id: int,
    service: QuizService = Depends(get_quiz_service),
):
    """
    Retorna todos los cuestionarios (quiz activities) del curso indicado.
    Útil para que el usuario seleccione dónde importar las preguntas.
    """
    try:
        quizzes_raw = await service.get_quiz_activities(course_id)

        quizzes = []
        for q in quizzes_raw:
            quizzes.append(QuizActivity(
                id=q.get("id", 0),
                coursemodule=q.get("coursemodule", 0),
                course=q.get("course", course_id),
                name=q.get("name", ""),
                intro=q.get("intro"),
                timelimit=q.get("timelimit", 0),
                attempts=q.get("attempts", 0),
                grade=q.get("grade", 0.0),
            ))

        return QuizActivitiesResponse(
            course_id=course_id,
            quizzes=quizzes,
            total=len(quizzes),
        )
    except MoodleAPIError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "message": e.message,
                "error_code": e.error_code,
                "hint": (
                    "Asegúrate de que el token tenga habilitada la función "
                    "mod_quiz_get_quizzes_by_courses en el servicio web de Moodle."
                ),
            },
        )


# ==================== QUESTION CATEGORIES ====================


@router.get(
    "/{course_id}/categories",
    response_model=QuestionCategoriesResponse,
    summary="Listar categorías de preguntas",
    description=(
        "Obtiene las categorías de preguntas del banco de preguntas. "
        "Sin parámetros extra: categorías del curso. "
        "Con cmid: categorías del quiz específico. "
        "Con include_all=true: todas las categorías (curso + quizzes)."
    ),
)
async def list_question_categories(
    course_id: int,
    cmid: int = 0,
    include_all: bool = False,
    service: QuizService = Depends(get_quiz_service),
):
    """Retorna las categorías de preguntas del curso o de un quiz específico."""
    try:
        cats_raw = await service.get_question_categories(
            course_id, cmid=cmid, include_all=include_all
        )

        categories = []
        for c in cats_raw:
            categories.append(QuestionCategory(
                id=c.get("id", 0),
                name=c.get("name", ""),
                contextid=c.get("contextid", 0),
                contextlevel=c.get("contextlevel"),
                info=c.get("info"),
                questioncount=c.get("questioncount", 0),
            ))

        return QuestionCategoriesResponse(
            course_id=course_id,
            categories=categories,
            total=len(categories),
        )
    except MoodleAPIError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "message": e.message,
                "error_code": e.error_code,
            },
        )


@router.post(
    "/{course_id}/categories",
    response_model=CreateCategoryResponse,
    summary="Crear categoría de preguntas",
    description=(
        "Crea una nueva categoría en el banco de preguntas. "
        "Si se envía cmid, se crea en el contexto de ese quiz específico. "
        "Si no, se crea en el contexto general del curso."
    ),
)
async def create_question_category(
    course_id: int,
    request: CreateCategoryRequest,
    service: QuizService = Depends(get_quiz_service),
):
    """Crea una nueva categoría de preguntas en el curso o quiz específico."""
    try:
        result = await service.create_category(
            course_id=course_id,
            name=request.name,
            info=request.info or "",
            cmid=request.cmid or 0,
        )

        cat_id = result.get("id", 0) if isinstance(result, dict) else 0

        return CreateCategoryResponse(
            success=True,
            category_id=cat_id,
            name=request.name,
            message=f"Categoría '{request.name}' creada correctamente.",
        )
    except MoodleAPIError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "message": e.message,
                "error_code": e.error_code,
                "debug_info": e.debug_info,
            },
        )


# ==================== IMPORT / PREVIEW ====================


@router.post(
    "/preview-import",
    response_model=QuizImportResponse,
    summary="Preview de importación",
    description="Parsea un archivo de preguntas y muestra lo que se importaría, sin enviar nada a Moodle.",
)
async def preview_import(
    file: UploadFile = File(..., description="Archivo con preguntas (Aiken .txt o Moodle .xml)"),
    format: ImportFormat = Form(..., description="Formato del archivo: 'aiken' o 'xml'"),
    service: QuizService = Depends(get_quiz_service),
):
    """
    Parsea el archivo y retorna las preguntas encontradas sin enviarlas a Moodle.
    Útil para que el usuario revise antes de confirmar la importación.
    """
    try:
        content = (await file.read()).decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="El archivo no es un archivo de texto válido (UTF-8).",
        )

    result = await service.preview_import(content, format)

    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)

    return result


@router.post(
    "/import",
    response_model=QuizImportResponse,
    summary="Importar preguntas a Moodle",
    description="Importa preguntas desde un archivo al banco de preguntas de un curso en Moodle.",
)
async def import_questions(
    file: UploadFile = File(..., description="Archivo con preguntas (Aiken .txt o Moodle .xml)"),
    format: ImportFormat = Form(..., description="Formato del archivo: 'aiken' o 'xml'"),
    course_id: int = Form(..., description="ID del curso destino en Moodle"),
    category_id: int = Form(..., description="ID de la categoría destino en el banco de preguntas"),
    category_name: str = Form("", description="Nombre de la categoría (para metadata)"),
    service: QuizService = Depends(get_quiz_service),
):
    """
    Importa preguntas al banco de preguntas de Moodle.

    Flujo:
    1. Lee y parsea el archivo según el formato
    2. Convierte a Moodle XML (si es Aiken)
    3. Envía al banco de preguntas de Moodle vía API

    Los formatos soportados son:
    - **Aiken** (.txt): formato simple de opción múltiple
    - **Moodle XML** (.xml): formato completo que soporta múltiples tipos de preguntas
    """
    try:
        content = (await file.read()).decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="El archivo no es un archivo de texto válido (UTF-8).",
        )

    result = await service.import_questions(
        course_id=course_id,
        category_id=category_id,
        content=content,
        format=format,
        category_name=category_name or None,
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)

    return result


# ==================== CONFIGURE QUIZ QUESTIONS ====================


@router.post(
    "/{course_id}/configure-questions",
    response_model=ConfigureQuizQuestionsResponse,
    summary="Agregar preguntas al cuestionario",
    description=(
        "Agrega preguntas desde una categoría del banco de preguntas a un cuestionario. "
        "Dos modos disponibles:\n"
        "- **all**: agrega TODAS las preguntas de la categoría como slots fijos.\n"
        "- **random**: agrega N referencias aleatorias que seleccionan preguntas de la categoría al azar."
    ),
)
async def configure_quiz_questions(
    course_id: int,
    request: ConfigureQuizQuestionsRequest,
    service: QuizService = Depends(get_quiz_service),
):
    """
    Carga preguntas de una categoría al cuestionario.
    En modo 'all' añade cada pregunta como slot fijo.
    En modo 'random' añade referencias aleatorias (el alumno ve preguntas distintas cada intento).
    """
    try:
        result = await service.configure_quiz_questions(
            course_id=course_id,
            cmid=request.quiz_cmid,
            category_id=request.category_id,
            mode=request.mode.value,
            num_questions=request.num_questions,
            include_subcategories=request.include_subcategories,
        )

        return ConfigureQuizQuestionsResponse(
            success=result.get("success", False),
            quiz_name=result.get("quiz_name", ""),
            mode=result.get("mode", request.mode.value),
            questions_added=result.get("questions_added", 0),
            message=result.get("message", ""),
        )
    except MoodleAPIError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "message": e.message,
                "error_code": e.error_code,
                "debug_info": e.debug_info,
            },
        )


# ==================== UPDATE QUIZ SETTINGS ====================


@router.post(
    "/{course_id}/settings",
    response_model=UpdateQuizSettingsResponse,
    summary="Actualizar ajustes del cuestionario",
    description=(
        "Actualiza los ajustes de un cuestionario, como el tiempo límite. "
        "El tiempo se especifica en segundos. Ejemplo: 3600 = 1 hora, 1800 = 30 minutos."
    ),
)
async def update_quiz_settings(
    course_id: int,
    request: UpdateQuizSettingsRequest,
    service: QuizService = Depends(get_quiz_service),
):
    """
    Actualiza el tiempo límite y otros ajustes del cuestionario.
    time_limit en segundos (0 = sin límite).
    """
    try:
        result = await service.update_quiz_settings(
            course_id=course_id,
            cmid=request.quiz_cmid,
            time_limit=request.time_limit,
        )

        return UpdateQuizSettingsResponse(
            success=result.get("success", False),
            quiz_name=result.get("quiz_name", ""),
            time_limit=result.get("timelimit", request.time_limit),
            time_limit_display=result.get("timelimit_display", ""),
            message=result.get("message", ""),
        )
    except MoodleAPIError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "message": e.message,
                "error_code": e.error_code,
                "debug_info": e.debug_info,
            },
        )


# ==================== SUPPORTED FORMATS ====================


@router.get(
    "/supported-formats",
    response_model=SupportedFormatsResponse,
    summary="Formatos soportados",
    description="Retorna la lista de formatos soportados para importar preguntas, con ejemplos.",
)
async def get_supported_formats():
    """Retorna los formatos de importación soportados con ejemplos."""
    return SupportedFormatsResponse(
        formats=[
            FormatInfo(
                format=ImportFormat.AIKEN,
                name="Aiken",
                extension=".txt",
                description=(
                    "Formato simple de texto plano para preguntas de opción múltiple. "
                    "Cada pregunta tiene un enunciado, opciones (A-Z) y la respuesta correcta."
                ),
                example=AIKEN_EXAMPLE,
            ),
            FormatInfo(
                format=ImportFormat.XML,
                name="Moodle XML",
                extension=".xml",
                description=(
                    "Formato XML nativo de Moodle. Soporta múltiples tipos de preguntas: "
                    "opción múltiple, verdadero/falso, respuesta corta, ensayo, numérica y emparejamiento."
                ),
                example=XML_EXAMPLE,
            ),
        ]
    )
