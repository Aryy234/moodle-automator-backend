"""
Editor Schemas

Modelos Pydantic para la validación de datos del procesador de HTML y editor de links.
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class LinkReplacement(BaseModel):
    """Schema para definir un reemplazo de link"""
    old_url: str = Field(..., description="URL original a buscar")
    new_url: str = Field(..., description="Nueva URL de reemplazo")
    

class LinkReplacementRequest(BaseModel):
    """Schema para solicitud de reemplazo de links en un curso"""
    course_id: int = Field(..., description="ID del curso a procesar")
    replacements: List[LinkReplacement] = Field(
        ..., 
        description="Lista de reemplazos de URL a aplicar"
    )
    # Opciones de procesamiento
    process_pages: bool = Field(True, description="Procesar módulos tipo 'page'")
    process_labels: bool = Field(True, description="Procesar módulos tipo 'label'")
    process_sections: bool = Field(True, description="Procesar resúmenes de secciones")


class TeacherLinkUpdateRequest(BaseModel):
    """
    Schema simplificado para actualizar links del perfil docente.
    
    Este es el caso de uso principal: cambiar el link del perfil
    del docente original al del nuevo docente.
    """
    course_id: int = Field(..., description="ID del curso a procesar")
    old_teacher_url: Optional[str] = Field(
        None, 
        description="URL del perfil del docente anterior (si se omite, se buscará automáticamente)"
    )
    new_teacher_url: str = Field(..., description="URL del nuevo perfil del docente")


class LinkFound(BaseModel):
    """Schema para un link encontrado durante el escaneo"""
    module_id: int = Field(..., description="ID del módulo donde se encontró")
    module_name: str = Field(..., description="Nombre del módulo")
    module_type: str = Field(..., description="Tipo de módulo (page, label, etc.)")
    original_url: str = Field(..., description="URL encontrada")
    link_text: Optional[str] = Field(None, description="Texto del enlace")
    context: Optional[str] = Field(None, description="Contexto HTML alrededor del link")


class LinkScanResponse(BaseModel):
    """Schema para respuesta de escaneo de links"""
    course_id: int
    total_links_found: int
    links: List[LinkFound]
    teacher_profile_links: List[LinkFound] = Field(
        default_factory=list,
        description="Links identificados como perfiles de docentes"
    )


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
    success: bool = Field(..., description="Indica si la operación general fue exitosa")
    course_id: int
    total_processed: int = Field(..., description="Total de módulos procesados")
    total_updated: int = Field(..., description="Total de links actualizados")
    total_errors: int = Field(0, description="Total de errores encontrados")
    results: List[LinkUpdateResult] = Field(
        default_factory=list, 
        description="Detalle de cada actualización"
    )
    message: str = Field(..., description="Mensaje descriptivo del resultado")


class HtmlProcessRequest(BaseModel):
    """Schema para procesar HTML directamente (útil para testing)"""
    html_content: str = Field(..., description="Contenido HTML a procesar")
    old_url: str = Field(..., description="URL a buscar")
    new_url: str = Field(..., description="URL de reemplazo")


class HtmlProcessResponse(BaseModel):
    """Schema para respuesta de procesamiento de HTML"""
    original_html: str
    processed_html: str
    links_replaced: int
    changes_made: bool
