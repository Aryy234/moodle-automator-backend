"""
Quiz Schemas

Modelos Pydantic para el sistema de importación de cuestionarios.
Define las estructuras de datos para preguntas, cuestionarios y operaciones de importación.
"""

from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


# ==================== ENUMS ====================

class QuestionType(str, Enum):
    """Tipos de preguntas soportados"""
    MULTICHOICE = "multichoice"
    TRUEFALSE = "truefalse"
    SHORTANSWER = "shortanswer"
    ESSAY = "essay"
    NUMERICAL = "numerical"
    MATCHING = "matching"


class ImportFormat(str, Enum):
    """Formatos de importación soportados"""
    AIKEN = "aiken"
    XML = "xml"


# ==================== PARSED QUESTIONS ====================

class ParsedOption(BaseModel):
    """Una opción de respuesta parseada del archivo"""
    text: str = Field(..., description="Texto de la opción")
    is_correct: bool = Field(False, description="Si esta opción es la respuesta correcta")
    feedback: Optional[str] = Field(None, description="Retroalimentación para esta opción")


class ParsedQuestion(BaseModel):
    """Pregunta parseada del archivo de importación (representación interna)"""
    question_text: str = Field(..., description="Enunciado de la pregunta")
    question_type: QuestionType = Field(..., description="Tipo de pregunta")
    options: List[ParsedOption] = Field(default_factory=list, description="Opciones de respuesta")
    correct_answer: Optional[str] = Field(None, description="Respuesta correcta (texto)")
    default_grade: float = Field(1.0, description="Puntuación por defecto")
    penalty: float = Field(0.3333333, description="Penalización por intento incorrecto")
    general_feedback: Optional[str] = Field(None, description="Retroalimentación general")
    name: Optional[str] = Field(None, description="Nombre/título de la pregunta")


# ==================== MOODLE QUIZ ACTIVITIES ====================

class QuizActivity(BaseModel):
    """Actividad cuestionario obtenida desde Moodle"""
    id: int = Field(..., description="ID de la instancia del quiz en Moodle")
    coursemodule: int = Field(..., description="ID del módulo de curso (cmid)")
    course: int = Field(..., description="ID del curso")
    name: str = Field(..., description="Nombre del cuestionario")
    intro: Optional[str] = Field(None, description="Descripción/introducción del cuestionario")
    timelimit: int = Field(0, description="Tiempo límite en segundos (0 = sin límite)")
    attempts: int = Field(0, description="Número máximo de intentos (0 = ilimitado)")
    grade: float = Field(0.0, description="Calificación máxima")


class QuizActivitiesResponse(BaseModel):
    """Respuesta al listar cuestionarios de un curso"""
    course_id: int
    quizzes: List[QuizActivity] = Field(default_factory=list)
    total: int = 0


# ==================== QUESTION CATEGORIES ====================

class QuestionCategory(BaseModel):
    """Categoría de preguntas en Moodle"""
    id: int = Field(..., description="ID de la categoría")
    name: str = Field(..., description="Nombre de la categoría")
    contextid: int = Field(..., description="ID del contexto")
    contextlevel: Optional[str] = Field(None, description="Nivel del contexto: 'course' o 'module'")
    info: Optional[str] = Field(None, description="Descripción de la categoría")
    questioncount: int = Field(0, description="Cantidad de preguntas en la categoría")


class QuestionCategoriesResponse(BaseModel):
    """Respuesta al listar categorías de preguntas"""
    course_id: int
    categories: List[QuestionCategory] = Field(default_factory=list)
    total: int = 0


class CreateCategoryRequest(BaseModel):
    """Request para crear una categoría de preguntas"""
    name: str = Field(..., description="Nombre de la nueva categoría")
    info: Optional[str] = Field("", description="Descripción de la categoría")
    cmid: Optional[int] = Field(
        None,
        description="Course Module ID de un quiz. Si se envía, la categoría se crea en el contexto de ese quiz. Si no, en el contexto del curso."
    )


class CreateCategoryResponse(BaseModel):
    """Respuesta al crear una categoría"""
    success: bool
    category_id: int = Field(..., description="ID de la categoría creada")
    name: str
    message: str = ""


# ==================== IMPORT ====================

class QuizImportResponse(BaseModel):
    """Respuesta de importación de preguntas"""
    success: bool
    course_id: int
    quiz_name: Optional[str] = Field(None, description="Nombre del cuestionario destino")
    category_name: Optional[str] = Field(None, description="Categoría donde se importaron")
    format_used: str = Field(..., description="Formato del archivo procesado")
    total_questions_parsed: int = Field(0, description="Total de preguntas parseadas del archivo")
    total_questions_imported: int = Field(0, description="Total importadas exitosamente a Moodle")
    questions: List[ParsedQuestion] = Field(
        default_factory=list,
        description="Lista de preguntas parseadas (presente en preview, vacío en import real)"
    )
    message: str = ""
    errors: List[str] = Field(default_factory=list, description="Errores durante la importación")


# ==================== SUPPORTED FORMATS ====================

class FormatInfo(BaseModel):
    """Información sobre un formato soportado"""
    format: ImportFormat
    name: str
    extension: str
    description: str
    example: str


class SupportedFormatsResponse(BaseModel):
    """Respuesta con los formatos soportados"""
    formats: List[FormatInfo]


# ==================== CONFIGURE QUIZ QUESTIONS ====================

class QuizQuestionMode(str, Enum):
    """Modo de carga de preguntas al cuestionario"""
    ALL = "all"
    RANDOM = "random"


class ConfigureQuizQuestionsRequest(BaseModel):
    """Request para agregar preguntas de una categoría a un cuestionario"""
    quiz_cmid: int = Field(..., description="Course Module ID del cuestionario")
    category_id: int = Field(..., description="ID de la categoría de preguntas a cargar")
    mode: QuizQuestionMode = Field(
        QuizQuestionMode.ALL,
        description="Modo: 'all' (todas las preguntas) o 'random' (preguntas aleatorias)"
    )
    num_questions: int = Field(
        10,
        ge=1,
        description="Cantidad de preguntas aleatorias (solo aplica en modo 'random')"
    )
    include_subcategories: bool = Field(
        False,
        description="Incluir subcategorías al seleccionar preguntas aleatorias"
    )


class ConfigureQuizQuestionsResponse(BaseModel):
    """Respuesta al configurar preguntas de un cuestionario"""
    success: bool
    quiz_name: str = Field("", description="Nombre del cuestionario")
    mode: str = Field("", description="Modo utilizado: 'all' o 'random'")
    questions_added: int = Field(0, description="Cantidad de preguntas/referencias agregadas")
    message: str = ""


# ==================== UPDATE QUIZ SETTINGS ====================

class UpdateQuizSettingsRequest(BaseModel):
    """Request para actualizar configuraciones del cuestionario"""
    quiz_cmid: int = Field(..., description="Course Module ID del cuestionario")
    time_limit: int = Field(
        0,
        ge=0,
        description="Tiempo límite en segundos (0 = sin límite). Ej: 3600 = 1 hora"
    )


class UpdateQuizSettingsResponse(BaseModel):
    """Respuesta al actualizar configuraciones del cuestionario"""
    success: bool
    quiz_name: str = Field("", description="Nombre del cuestionario")
    time_limit: int = Field(0, description="Tiempo límite en segundos")
    time_limit_display: str = Field("", description="Tiempo límite legible (ej: '1h 30m')")
    message: str = ""
