"""
Editor Schemas

Modelos Pydantic para la validación de datos del procesador de HTML y editor de links.
"""

from typing import Optional, List, Dict
from pydantic import BaseModel, Field


# ==================== SCHEDULE / HORARIO ====================

class ScheduleEntry(BaseModel):
    """Schema para una fila del horario"""
    subject_name: str = Field(..., description="Nombre de la asignatura")
    days: Dict[str, str] = Field(
        ..., 
        description="Horarios por día. Ej: {'Lunes': '18h30 – 19h30', 'Martes': '18h30 – 19h30'}"
    )


class ScheduleUpdateRequest(BaseModel):
    """Schema para actualizar el horario dentro del HTML"""
    entries: List[ScheduleEntry] = Field(..., description="Filas del horario")
    days_columns: List[str] = Field(
        default=["Lunes", "Martes", "Miércoles", "Jueves"],
        description="Columnas de días a mostrar en la cabecera"
    )


# ==================== BIBLIOGRAPHY ====================

class BibliographyEntry(BaseModel):
    """Schema para una entrada de bibliografía"""
    text: str = Field(..., description="Texto visible de la referencia bibliográfica (puede incluir HTML)")
    url: str = Field(..., description="URL del recurso bibliográfico")


class BibliographyUpdateRequest(BaseModel):
    """Schema para actualizar la bibliografía"""
    entries: List[BibliographyEntry] = Field(..., description="Lista de entradas bibliográficas")


# ==================== COURSE CUSTOMIZATION (ALL-IN-ONE) ====================

class CourseCustomizationRequest(BaseModel):
    """
    Schema principal para personalizar todo el contenido de la sección General.
    
    Permite actualizar en una sola llamada:
    - Links/placeholders (video, clases, grabaciones, perfil, silabo, PEA)
    - Nombre y descripción del curso (en el HTML)
    - Horario completo
    - Bibliografía
    """
    course_id: int = Field(..., description="ID del curso a personalizar")
    
    # Links / Placeholders
    video_introductorio: Optional[str] = Field(None, description="URL del video introductorio (iframe src)")
    unirse_clases: Optional[str] = Field(None, description="URL para unirse a clases")
    url_grabaciones: Optional[str] = Field(None, description="URL de grabaciones")
    perfil_docente: Optional[str] = Field(None, description="URL del perfil del docente (iframe src)")
    silabo: Optional[str] = Field(None, description="URL del sílabo (iframe src)")
    pea: Optional[str] = Field(None, description="URL del PEA (iframe src)")
    bibliografia_url: Optional[str] = Field(None, description="URL de la bibliografía (si es un solo link)")
    
    # Contenido de texto
    course_title: Optional[str] = Field(None, description="Nuevo título del curso (reemplaza en <h1>)")
    course_description: Optional[str] = Field(None, description="Nueva descripción del curso (reemplaza en <p>)")
    
    # Horario
    schedule: Optional[ScheduleUpdateRequest] = Field(None, description="Datos del horario a actualizar")
    
    # Bibliografía
    bibliography: Optional[BibliographyUpdateRequest] = Field(None, description="Datos de bibliografía a actualizar")


class ReplacementDetail(BaseModel):
    """Detalle de un reemplazo realizado"""
    field: str = Field(..., description="Campo que fue actualizado")
    old_value: str = Field(..., description="Valor anterior")
    new_value: str = Field(..., description="Nuevo valor")


class CourseCustomizationResponse(BaseModel):
    """Schema de respuesta para personalización del curso"""
    success: bool
    course_id: int
    message: str
    total_replacements: int = 0
    details: List[ReplacementDetail] = Field(default_factory=list)
    processed_html: Optional[str] = Field(None, description="HTML resultante (para preview)")


# ==================== SCAN / PREVIEW ====================

class PlaceholderFound(BaseModel):
    """Schema para un placeholder encontrado durante el escaneo"""
    element_type: str = Field(..., description="Tipo de elemento (a, iframe, etc.)")
    attribute: str = Field(..., description="Atributo donde se encontró (href, src)")
    placeholder_key: str = Field(..., description="Clave del placeholder (ej: video-introductorio)")
    context_text: Optional[str] = Field(None, description="Texto o contexto cercano")


class PlaceholderScanResponse(BaseModel):
    """Schema para el resultado del escaneo de placeholders"""
    course_id: int
    section_name: str = ""
    module_id: Optional[int] = None
    module_name: Optional[str] = None
    total_placeholders: int = 0    
    placeholders: List[PlaceholderFound] = Field(default_factory=list)
    schedule_found: bool = Field(False, description="Si se encontró un horario en el HTML")
    bibliography_found: bool = Field(False, description="Si se encontró bibliografía en el HTML")
    course_title: Optional[str] = Field(None, description="Título del curso encontrado en <h1>")
    course_description: Optional[str] = Field(None, description="Descripción del curso encontrada")
    template_source: str = Field(
        "unknown",
        description="Fuente del template: 'label' (editable vía API) o 'section_summary' (solo lectura)"
    )
    can_save: bool = Field(
        False,
        description="True si el template está en un label y se puede guardar vía API"
    )
    save_hint: Optional[str] = Field(
        None,
        description="Mensaje para el frontend si can_save=False"
    )


# ==================== LEGACY SCHEMAS (mantener compatibilidad) ====================

class LinkFound(BaseModel):
    """Schema para un link encontrado durante el escaneo"""
    module_id: int = Field(0, description="ID del módulo donde se encontró")
    module_name: str = Field("", description="Nombre del módulo")
    module_type: str = Field("", description="Tipo de módulo")
    original_url: str = Field(..., description="URL encontrada")
    link_text: Optional[str] = Field(None, description="Texto del enlace")
    context: Optional[str] = Field(None, description="Contexto HTML alrededor del link")


class LinkUpdateResult(BaseModel):
    """Schema para el resultado de una actualización de link"""
    module_id: int
    module_name: str
    old_url: str
    new_url: str
    success: bool
    error_message: Optional[str] = None


class LinkUpdateResponse(BaseModel):
    """Schema para respuesta de actualización de links"""
    success: bool
    course_id: int
    total_processed: int = 0
    total_updated: int = 0
    total_errors: int = 0
    results: List[LinkUpdateResult] = Field(default_factory=list)
    message: str = ""


class HtmlProcessRequest(BaseModel):
    """Schema para procesar HTML directamente (útil para testing)"""
    html_content: str = Field(..., description="Contenido HTML a procesar")
    old_url: str = Field(..., description="URL a buscar")
    new_url: str = Field(..., description="URL de reemplazo")


class HtmlProcessResponse(BaseModel):
    """Schema para respuesta de procesamiento de HTML"""
    original_html: str
    processed_html: str
    links_replaced: int = 0
    changes_made: bool = False


class TeacherLinkUpdateRequest(BaseModel):
    """Schema para actualizar links del perfil docente"""
    course_id: int = Field(..., description="ID del curso a procesar")
    old_teacher_url: Optional[str] = Field(None)
    new_teacher_url: str = Field(..., description="URL del nuevo perfil del docente")
