"""
Editor Routes

Endpoints para personalización del contenido HTML de cursos:
- Escaneo de placeholders
- Personalización completa (links, título, horario, bibliografía)
- Preview de cambios
- Procesamiento directo de HTML (testing)
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query

from app.schemas.editor import (
    CourseCustomizationRequest,
    CourseCustomizationResponse,
    PlaceholderScanResponse,
    HtmlProcessRequest,
    HtmlProcessResponse,
    TeacherLinkUpdateRequest,
    LinkUpdateResponse,
)
from app.services.html_processor import HTMLProcessor, get_html_processor, KNOWN_PLACEHOLDERS
from app.services.cloner_service import ClonerService, get_cloner_service

router = APIRouter()


# ==================================================================
# ESCANEO
# ==================================================================


@router.get(
    "/scan/{course_id}",
    response_model=PlaceholderScanResponse,
    summary="Escanear placeholders del curso",
    description="Analiza la sección General del curso y muestra todos los placeholders editables, "
                "título, descripción, horario y bibliografía detectados.",
)
async def scan_course_placeholders(
    course_id: int,
    cloner: ClonerService = Depends(get_cloner_service),
):
    """
    Escanea el curso y retorna qué elementos se pueden personalizar.
    Útil para mostrar al usuario qué campos llenar en el formulario.
    """
    try:
        return await cloner.scan_course_placeholders(course_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================================================================
# PERSONALIZACIÓN COMPLETA (ALL-IN-ONE)
# ==================================================================


@router.post(
    "/customize",
    response_model=CourseCustomizationResponse,
    summary="Personalizar curso (soporta varias secciones)",
    description="Aplica personalizaciones al HTML de una o varias secciones del curso. "
                "Si se envía 'sections', personaliza cada sección indicada (por semana, etc). "
                "Si no, solo la sección General (modo legacy).",
)
async def customize_course(
    request: CourseCustomizationRequest,
    cloner: ClonerService = Depends(get_cloner_service),
):
    """
    Endpoint principal de personalización.
    
    Recibe todos los campos a actualizar y los aplica sobre el HTML
    del label de la sección General del curso.
    """
    try:
        result = await cloner.customize_course(request, preview_only=False)
        if not result.success:
            raise HTTPException(status_code=400, detail=result.message)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/preview",
    response_model=CourseCustomizationResponse,
    summary="Preview de personalización (soporta varias secciones)",
    description="Muestra cómo quedarían los HTML de una o varias secciones sin guardar cambios en Moodle. "
                "Si se envía 'sections', retorna un dict con el HTML de cada sección.",
)
async def preview_customization(
    request: CourseCustomizationRequest,
    cloner: ClonerService = Depends(get_cloner_service),
):
    """
    Igual que /customize pero sin guardar. Retorna el HTML resultante
    para que el frontend lo muestre como preview.
    """
    try:
        result = await cloner.customize_course(request, preview_only=True)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================================================================
# INFORMACIÓN
# ==================================================================


@router.get(
    "/placeholders",
    summary="Listar placeholders conocidos",
    description="Retorna la lista de placeholders que el procesador busca en el HTML.",
)
async def list_known_placeholders():
    """
    Retorna todos los placeholders conocidos del template y su descripción.
    Útil para que el frontend construya el formulario dinámicamente.
    """
    return {
        "placeholders": [
            {"key": k, "description": v}
            for k, v in KNOWN_PLACEHOLDERS.items()
        ],
        "editable_text_fields": [
            {"key": "course_title", "description": "Título del curso (contenido del <h1>)"},
            {"key": "course_description", "description": "Descripción del curso (contenido del <p>)"},
        ],
        "editable_sections": [
            {"key": "schedule", "description": "Horario (tabla dentro del modal #cronograma)"},
            {"key": "bibliography", "description": "Bibliografía (lista dentro del modal #biblio)"},
        ],
    }


# ==================================================================
# TESTING / UTILIDADES
# ==================================================================


@router.post(
    "/process-html",
    response_model=HtmlProcessResponse,
    summary="Procesar HTML directamente",
    description="Útil para testing: procesa un fragmento de HTML y reemplaza un placeholder.",
)
async def process_html(
    request: HtmlProcessRequest,
    processor: HTMLProcessor = Depends(get_html_processor),
):
    """Procesa un fragmento de HTML para testing."""
    processed, details = processor.replace_placeholder(
        html=request.html_content,
        placeholder=request.old_url,
        new_value=request.new_url,
    )

    return HtmlProcessResponse(
        original_html=request.html_content,
        processed_html=processed,
        links_replaced=len(details),
        changes_made=len(details) > 0,
    )


# ==================================================================
# LEGACY ENDPOINTS (mantener compatibilidad)
# ==================================================================


@router.post(
    "/update-course-links",
    response_model=LinkUpdateResponse,
    summary="[Legacy] Actualizar enlaces de un curso",
)
async def update_course_teacher_links(
    request: TeacherLinkUpdateRequest,
    cloner: ClonerService = Depends(get_cloner_service),
):
    """Legacy: Escanea y reporta links de docente."""
    try:
        scan_result = await cloner.scan_course_links(request.course_id)
        teacher_links = scan_result.get("teacher_profile_links", [])

        return LinkUpdateResponse(
            success=True,
            course_id=request.course_id,
            total_processed=scan_result.get("total_links", 0),
            total_updated=len(teacher_links),
            message=f"Se encontraron {len(teacher_links)} enlaces. "
                    "Usa /editor/customize para aplicar cambios.",
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
