"""
Courses Routes

Endpoints para gestión de cursos: listado, duplicación y obtención de contenido.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends

from app.schemas.course import (
    CourseFromMoodle,
    CourseListResponse,
    CourseDuplicateRequest,
    CourseDuplicateResponse,
    CourseContentsResponse
)
from app.services.cloner_service import ClonerService, get_cloner_service
from app.integration.moodle_client import MoodleClient, get_moodle_client, MoodleAPIError

router = APIRouter()


@router.get(
    "/",
    response_model=CourseListResponse,
    summary="Listar cursos disponibles",
    description="Obtiene la lista de todos los cursos disponibles en Moodle para clonar."
)
async def list_courses(
    cloner: ClonerService = Depends(get_cloner_service)
):
    """
    Retorna todos los cursos disponibles en la plataforma Moodle.
    
    Excluye automáticamente el curso del sitio (ID=1).
    """
    try:
        courses = await cloner.get_available_courses()
        return CourseListResponse(
            courses=courses,
            total=len(courses)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{course_id}",
    response_model=CourseFromMoodle,
    summary="Obtener curso por ID",
    description="Obtiene los detalles de un curso específico."
)
async def get_course(
    course_id: int,
    cloner: ClonerService = Depends(get_cloner_service)
):
    """
    Retorna los datos de un curso específico por su ID.
    """
    course = await cloner.get_course_by_id(course_id)
    
    if not course:
        raise HTTPException(
            status_code=404, 
            detail=f"Curso con ID {course_id} no encontrado"
        )
    
    return course


@router.get(
    "/{course_id}/contents",
    summary="Obtener contenido del curso",
    description="Obtiene las secciones y módulos de un curso."
)
async def get_course_contents(
    course_id: int,
    moodle: MoodleClient = Depends(get_moodle_client)
):
    """
    Retorna el contenido completo de un curso (secciones y módulos).
    Útil para previsualizar el contenido antes de clonar.
    """
    try:
        contents = await moodle.get_course_contents(course_id)
        return {
            "course_id": course_id,
            "sections": contents
        }
    except MoodleAPIError as e:
        raise HTTPException(status_code=400, detail=e.message)


@router.get(
    "/{course_id}/scan-links",
    summary="Escanear enlaces del curso",
    description="Analiza el curso y encuentra todos los enlaces en su contenido HTML."
)
async def scan_course_links(
    course_id: int,
    cloner: ClonerService = Depends(get_cloner_service)
):
    """
    Escanea un curso para encontrar todos los enlaces, 
    identificando especialmente los que parecen ser perfiles de docentes.
    
    Útil para previsualizar qué enlaces se modificarán durante la clonación.
    """
    try:
        result = await cloner.scan_course_links(course_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/duplicate",
    response_model=CourseDuplicateResponse,
    summary="Duplicar curso",
    description="Crea una copia de un curso existente con personalización de enlaces."
)
async def duplicate_course(
    request: CourseDuplicateRequest,
    cloner: ClonerService = Depends(get_cloner_service)
):
    """
    Duplica un curso existente y opcionalmente actualiza los enlaces del docente.
    
    Este es el endpoint principal de la aplicación que:
    1. Duplica el curso usando la API de Moodle
    2. Procesa el contenido HTML del nuevo curso
    3. Reemplaza los enlaces del perfil del docente si se especifica
    4. Retorna información del nuevo curso
    """
    try:
        result = await cloner.duplicate_course(request)
        
        if not result.success:
            raise HTTPException(status_code=400, detail=result.message)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/health/check",
    summary="Verificar conexión con Moodle",
    description="Verifica que la conexión con Moodle esté funcionando correctamente."
)
async def health_check(
    moodle: MoodleClient = Depends(get_moodle_client)
):
    """
    Verifica la conectividad con Moodle usando el token configurado.
    Retorna información básica del sitio y usuario.
    """
    try:
        site_info = await moodle.get_site_info()
        return {
            "status": "connected",
            "site_name": site_info.get("sitename"),
            "username": site_info.get("username"),
            "user_id": site_info.get("userid"),
            "moodle_version": site_info.get("release")
        }
    except MoodleAPIError as e:
        return {
            "status": "error",
            "message": e.message,
            "error_code": e.error_code
        }
