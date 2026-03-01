"""
Course Schemas

Modelos Pydantic para la validación de datos relacionados con cursos de Moodle.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl


class CourseBase(BaseModel):
    """Schema base para datos de curso"""
    fullname: str = Field(..., description="Nombre completo del curso")
    shortname: str = Field(..., description="Nombre corto del curso")
    

class CourseFromMoodle(CourseBase):
    """Schema para cursos obtenidos desde Moodle"""
    id: int = Field(..., description="ID único del curso en Moodle")
    idnumber: Optional[str] = Field(None, description="Número ID interno del curso")
    categoryid: Optional[int] = Field(None, description="ID de la categoría del curso")
    summary: Optional[str] = Field(None, description="Resumen del curso")
    summaryformat: Optional[int] = Field(1, description="Formato del resumen")
    visible: Optional[int] = Field(1, description="Visibilidad del curso (1=visible, 0=oculto)")
    
    class Config:
        from_attributes = True


class CourseDuplicateRequest(BaseModel):
    """Schema para solicitud de duplicación de curso"""
    source_course_id: int = Field(..., description="ID del curso origen a duplicar")
    new_fullname: str = Field(..., description="Nombre completo del nuevo curso")
    new_shortname: str = Field(..., description="Nombre corto del nuevo curso")
    new_idnumber: Optional[str] = Field(
        None,
        description="Número ID interno del nuevo curso (campo 'idnumber' en Moodle). "
                    "Ej: 'MAT-2025-A'. Si no se especifica, queda vacío."
    )
    category_id: Optional[int] = Field(None, description="ID de la categoría destino (opcional)")
    visible: int = Field(0, description="Visibilidad inicial del nuevo curso")

    # Configuración de personalización de links
    new_teacher_profile_url: Optional[str] = Field(
        None,
        description="Nueva URL del perfil del docente para reemplazar en el contenido"
    )


class CourseDuplicateResponse(BaseModel):
    """Schema para respuesta de duplicación de curso"""
    success: bool = Field(..., description="Indica si la operación fue exitosa")
    new_course_id: int = Field(..., description="ID del nuevo curso creado")
    new_course_url: str = Field(..., description="URL directa al nuevo curso")
    message: str = Field(..., description="Mensaje descriptivo del resultado")
    links_updated: int = Field(0, description="Cantidad de links actualizados en el proceso")


class CourseListResponse(BaseModel):
    """Schema para respuesta de listado de cursos"""
    courses: List[CourseFromMoodle]
    total: int = Field(..., description="Total de cursos encontrados")


class CourseModule(BaseModel):
    """Schema para un módulo dentro de un curso"""
    id: int = Field(..., description="ID del módulo")
    name: str = Field(..., description="Nombre del módulo")
    modname: str = Field(..., description="Tipo de módulo (page, label, url, etc.)")
    modplural: Optional[str] = Field(None, description="Nombre plural del tipo de módulo")
    instance: int = Field(..., description="ID de la instancia del módulo")
    description: Optional[str] = Field(None, description="Descripción/contenido HTML del módulo")
    visible: Optional[int] = Field(1, description="Visibilidad del módulo")


class CourseSection(BaseModel):
    """Schema para una sección de curso"""
    id: int = Field(..., description="ID de la sección")
    name: str = Field(..., description="Nombre de la sección")
    summary: Optional[str] = Field(None, description="Resumen HTML de la sección")
    modules: List[CourseModule] = Field(default_factory=list, description="Módulos dentro de la sección")


class CourseContentsResponse(BaseModel):
    """Schema para el contenido completo de un curso"""
    course_id: int
    sections: List[CourseSection]
