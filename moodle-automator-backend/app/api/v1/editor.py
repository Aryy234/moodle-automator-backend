"""
Editor Routes

Endpoints para el procesamiento y edición de contenido HTML y enlaces.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends

from app.schemas.editor import (
    HtmlProcessRequest,
    HtmlProcessResponse,
    TeacherLinkUpdateRequest,
    LinkUpdateResponse
)
from app.services.html_processor import HTMLProcessor, get_html_processor
from app.services.cloner_service import ClonerService, get_cloner_service

router = APIRouter()


@router.post(
    "/process-html",
    response_model=HtmlProcessResponse,
    summary="Procesar HTML",
    description="Procesa contenido HTML y reemplaza enlaces especificados. Útil para testing."
)
async def process_html(
    request: HtmlProcessRequest,
    processor: HTMLProcessor = Depends(get_html_processor)
):
    """
    Procesa un fragmento de HTML y reemplaza un enlace específico.
    
    Este endpoint es útil para:
    - Testing del procesador HTML
    - Previsualización de cambios antes de aplicarlos
    - Validación de que los reemplazos funcionan correctamente
    """
    processed_html, count = processor.replace_link(
        html_content=request.html_content,
        old_url=request.old_url,
        new_url=request.new_url,
        exact_match=False  # Permitir coincidencias parciales
    )
    
    return HtmlProcessResponse(
        original_html=request.html_content,
        processed_html=processed_html,
        links_replaced=count,
        changes_made=count > 0
    )


@router.post(
    "/find-links",
    summary="Encontrar enlaces en HTML",
    description="Analiza contenido HTML y retorna todos los enlaces encontrados."
)
async def find_links_in_html(
    html_content: str,
    processor: HTMLProcessor = Depends(get_html_processor)
):
    """
    Encuentra todos los enlaces en un fragmento de HTML.
    
    Retorna información detallada de cada enlace incluyendo:
    - URL (href)
    - Texto del enlace
    - Atributos adicionales
    - Contexto HTML
    """
    links = processor.find_all_links(html_content)
    teacher_links = processor.find_teacher_profile_links(html_content)
    
    return {
        "total_links": len(links),
        "links": links,
        "teacher_profile_links": teacher_links,
        "teacher_links_count": len(teacher_links)
    }


@router.post(
    "/find-teacher-links",
    summary="Encontrar enlaces de perfil docente",
    description="Analiza HTML y encuentra específicamente enlaces que parecen ser perfiles de docentes."
)
async def find_teacher_links(
    html_content: str,
    processor: HTMLProcessor = Depends(get_html_processor)
):
    """
    Encuentra enlaces que coinciden con patrones de perfiles de docentes.
    
    Utiliza heurísticas para identificar enlaces que probablemente
    apunten a perfiles de usuario/docente en Moodle.
    """
    teacher_links = processor.find_teacher_profile_links(html_content)
    
    return {
        "found": len(teacher_links) > 0,
        "count": len(teacher_links),
        "links": teacher_links
    }


@router.post(
    "/replace-teacher-links",
    summary="Reemplazar enlaces de docente en HTML",
    description="Reemplaza todos los enlaces de perfil de docente en contenido HTML."
)
async def replace_teacher_links_in_html(
    html_content: str,
    new_teacher_url: str,
    old_teacher_url: Optional[str] = None,
    processor: HTMLProcessor = Depends(get_html_processor)
):
    """
    Reemplaza los enlaces de perfil de docente en un fragmento de HTML.
    
    Si no se especifica old_teacher_url, se detectan automáticamente
    los enlaces que parecen ser perfiles de docentes.
    """
    processed_html, count = processor.replace_teacher_profile_links(
        html_content=html_content,
        new_teacher_url=new_teacher_url,
        old_teacher_url=old_teacher_url
    )
    
    return {
        "processed_html": processed_html,
        "links_replaced": count,
        "changes_made": count > 0
    }


@router.post(
    "/update-course-links",
    response_model=LinkUpdateResponse,
    summary="Actualizar enlaces de un curso",
    description="Actualiza los enlaces del perfil docente en todo el contenido de un curso existente."
)
async def update_course_teacher_links(
    request: TeacherLinkUpdateRequest,
    cloner: ClonerService = Depends(get_cloner_service)
):
    """
    Actualiza los enlaces del perfil docente en un curso existente.
    
    Este endpoint permite:
    - Escanear todo el contenido del curso
    - Identificar enlaces de perfil de docente
    - Reemplazarlos con la nueva URL
    
    NOTA: La actualización real en Moodle puede requerir
    funciones de Web Service adicionales.
    """
    try:
        # Primero escanear para encontrar qué se actualizaría
        scan_result = await cloner.scan_course_links(request.course_id)
        
        # Por ahora retornamos un preview de lo que se actualizaría
        # La actualización real requiere funciones adicionales de Moodle
        
        teacher_links = scan_result.get('teacher_profile_links', [])
        
        return LinkUpdateResponse(
            success=True,
            course_id=request.course_id,
            total_processed=scan_result.get('total_links', 0),
            total_updated=len(teacher_links),
            total_errors=0,
            results=[],
            message=f"Se encontraron {len(teacher_links)} enlaces de docente que se actualizarían. "
                    "Nota: La actualización directa de módulos requiere funciones adicionales de Moodle."
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/patterns",
    summary="Obtener patrones de detección",
    description="Retorna los patrones de regex utilizados para detectar enlaces de docentes."
)
async def get_detection_patterns(
    processor: HTMLProcessor = Depends(get_html_processor)
):
    """
    Retorna los patrones de detección de enlaces de perfil de docente.
    
    Útil para entender qué tipos de enlaces serán detectados
    automáticamente durante el procesamiento.
    """
    return {
        "patterns": processor.TEACHER_PROFILE_PATTERNS,
        "description": "Expresiones regulares utilizadas para identificar enlaces de perfiles de docentes"
    }
