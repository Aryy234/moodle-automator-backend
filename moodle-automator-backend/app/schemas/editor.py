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


# ==================== NUEVO: PERSONALIZACIÓN POR SECCIÓN ====================


class ExistingLabelRef(BaseModel):
    """Referencia a un label existente en Moodle (proveniente del scan)."""
    label_cmid: Optional[int] = Field(None, description="Course module ID del label")
    label_instance_id: Optional[int] = Field(None, description="Instance ID del label (necesario para update_label)")


class SectionCustomizationData(BaseModel):
    """
    Datos de personalización para UNA sección específica (por ejemplo, una semana).
    Todos los campos son opcionales y solo se aplican si se envían.
    """
    section_id: int = Field(..., description="ID de la sección a personalizar")
    section_number: Optional[int] = Field(None, description="Número de la sección (0=General, 1=Semana 1, etc.)")
    video_introductorio: Optional[str] = Field(None, description="URL del video introductorio (iframe src)")
    unirse_clases: Optional[str] = Field(None, description="URL para unirse a clases")
    url_grabaciones: Optional[str] = Field(None, description="URL de grabaciones")
    perfil_docente: Optional[str] = Field(None, description="URL del perfil del docente (iframe src)")
    silabo: Optional[str] = Field(None, description="URL del sílabo (iframe src)")
    pea: Optional[str] = Field(None, description="URL del PEA (iframe src)")
    bibliografia_url: Optional[str] = Field(None, description="URL de la bibliografía (si es un solo link)")
    course_title: Optional[str] = Field(None, description="Nuevo título del curso (reemplaza en <h1>)")
    course_description: Optional[str] = Field(None, description="Nueva descripción del curso (reemplaza en <p>)")
    schedule: Optional[ScheduleUpdateRequest] = Field(None, description="Datos del horario a actualizar")
    bibliography: Optional[BibliographyUpdateRequest] = Field(None, description="Datos de bibliografía a actualizar")
    # Bloques avanzados para presentaciones, lecturas y videos
    presentations: Optional[List[dict]] = Field(None, description="Lista de presentaciones: [{title, url}]. Soporta múltiples.")
    presentation_objective: Optional[str] = Field(None, description="Objetivo de aprendizaje de la(s) presentación(es)")
    presentation_summary: Optional[str] = Field(None, description="Resumen de la(s) presentación(es)")
    main_reading: Optional[dict] = Field(None, description="Lectura principal: {title, author, url, summary}")
    suggested_readings: Optional[List[dict]] = Field(None, description="Lecturas sugeridas: [{title, author, url}]")
    videos: Optional[List[dict]] = Field(None, description="Lista de videos: [{title, url}]. Soporta múltiples.")
    videos_summary: Optional[str] = Field(None, description="Resumen de los videos")
    # Personalización del bloque de lectura
    reading_collapse_label: Optional[str] = Field(None, description="Texto del botón collapse del bloque de lectura. Ej: 'Lectura', 'Guia de apoyo'")
    reading_section_title: Optional[str] = Field(None, description="Título h4 interno del bloque de lectura. Ej: 'Lectura principal', 'Guia para la POO'")
    reading_button_text: Optional[str] = Field(None, description="Texto del botón de la lectura principal. Ej: 'Ver lectura', 'Ver Guia de apoyo'")
    reading_suggested_title: Optional[str] = Field(None, description="Título de la sección de lecturas sugeridas. Ej: 'Lecturas sugeridas', 'Libro de apoyo para mejorar el conocimiento'")
    # IDs de labels existentes (para actualizar en vez de crear nuevos)
    existing_labels: Optional[Dict[str, ExistingLabelRef]] = Field(
        None,
        description=(
            "IDs de labels existentes por tipo de bloque, provenientes del scan. "
            "Ej: {\"presentations\": {label_cmid: 123, label_instance_id: 45}, ...}. "
            "Si se envían, el backend actualiza esos labels en vez de crear nuevos."
        ),
    )


class CourseCustomizationRequest(BaseModel):
    """
    Schema principal para personalizar el contenido de una o varias secciones.
    
    - Si se envía 'sections', se personalizan varias secciones (por semana, etc.)
    - Si se envían los campos planos (legacy), solo se personaliza la sección General (0)
    """
    course_id: int = Field(..., description="ID del curso a personalizar")
    sections: Optional[List[SectionCustomizationData]] = Field(
        None,
        description="Lista de personalizaciones por sección. Si se omite, se usa el modo legacy (solo General)."
    )
    # Legacy: para compatibilidad con frontend actual (solo General)
    video_introductorio: Optional[str] = Field(None, description="URL del video introductorio (iframe src)")
    unirse_clases: Optional[str] = Field(None, description="URL para unirse a clases")
    url_grabaciones: Optional[str] = Field(None, description="URL de grabaciones")
    perfil_docente: Optional[str] = Field(None, description="URL del perfil del docente (iframe src)")
    silabo: Optional[str] = Field(None, description="URL del sílabo (iframe src)")
    pea: Optional[str] = Field(None, description="URL del PEA (iframe src)")
    bibliografia_url: Optional[str] = Field(None, description="URL de la bibliografía (si es un solo link)")
    course_title: Optional[str] = Field(None, description="Nuevo título del curso (reemplaza en <h1>)")
    course_description: Optional[str] = Field(None, description="Nueva descripción del curso (reemplaza en <p>)")
    schedule: Optional[ScheduleUpdateRequest] = Field(None, description="Datos del horario a actualizar")
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
    current_value: Optional[str] = Field(None, description="Valor actual del atributo src/href. Si empieza con http/https ya fue configurado.")


class ExistingBlockInfo(BaseModel):
    """Información de un bloque (presentación, lectura, video) ya existente en una sección."""
    block_type: str = Field(..., description="Tipo de bloque: presentations, reading, videos")
    label_cmid: Optional[int] = Field(None, description="Course module ID del label que contiene el bloque")
    label_instance_id: Optional[int] = Field(None, description="Instance ID del label (para update_label)")
    section_id: Optional[int] = Field(None, description="ID de la sección donde está el bloque")
    section_number: Optional[int] = Field(None, description="Número de sección (0=General, 1=Semana 1, etc.)")
    collapse_label: Optional[str] = Field(None, description="Texto del botón collapse del bloque")

    # --- Presentaciones (block_type == 'presentations') ---
    presentations: Optional[List[dict]] = Field(
        None,
        description="Lista de presentaciones detectadas: [{title, url}]"
    )
    presentation_objective: Optional[str] = Field(
        None, description="Objetivo de aprendizaje extraído del bloque"
    )
    presentation_summary: Optional[str] = Field(
        None, description="Resumen extraído del bloque de presentaciones"
    )

    # --- Lectura (block_type == 'reading') ---
    main_reading: Optional[dict] = Field(
        None,
        description="Lectura principal: {title, author, url, summary}"
    )
    suggested_readings: Optional[List[dict]] = Field(
        None,
        description="Lecturas sugeridas: [{title, author, url}]"
    )
    reading_section_title: Optional[str] = Field(
        None, description="Título h4 de la sección de lectura (ej. 'Lectura principal')"
    )
    reading_button_text: Optional[str] = Field(
        None, description="Texto del botón de la lectura principal (ej. 'Ver lectura')"
    )
    reading_suggested_title: Optional[str] = Field(
        None, description="Título de la sección de lecturas sugeridas"
    )

    # --- Videos (block_type == 'videos') ---
    videos: Optional[List[dict]] = Field(
        None,
        description="Lista de videos detectados: [{title, url}]"
    )
    videos_summary: Optional[str] = Field(
        None, description="Texto resumen de los videos"
    )

    # --- Legacy (compatibilidad) ---
    items: List[dict] = Field(
        default_factory=list,
        description="(Deprecado) Contenido genérico del bloque. Usar los campos específicos."
    )
    summary_text: Optional[str] = Field(None, description="(Deprecado) Texto resumen/objetivo")


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
    existing_blocks: List[ExistingBlockInfo] = Field(
        default_factory=list,
        description="Bloques avanzados (presentación, lectura, video) ya existentes en la sección"
    )
    existing_schedule: Optional[dict] = Field(
        None,
        description="Datos actuales del horario: {days_columns: [...], entries: [{subject_name, days: {Lunes: '...', ...}}]}"
    )
    existing_bibliography: Optional[dict] = Field(
        None,
        description="Datos actuales de bibliografía: {entries: [{text, url}]}"
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
