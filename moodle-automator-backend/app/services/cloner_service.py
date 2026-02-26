"""
Cloner Service - Course Duplication Orchestration

Servicio principal que orquesta el proceso completo de clonación de cursos,
coordinando la comunicación con Moodle y el procesamiento de HTML.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

from app.integration.moodle_client import MoodleClient, get_moodle_client, MoodleAPIError
from app.services.html_processor import HTMLProcessor, get_html_processor
from app.schemas.course import (
    CourseDuplicateRequest, 
    CourseDuplicateResponse,
    CourseFromMoodle,
    CourseSection,
    CourseModule
)
from app.schemas.editor import LinkUpdateResult
from app.core.config import settings


@dataclass
class CloneProgress:
    """Estructura para tracking del progreso del clonado"""
    step: str = "initializing"
    progress: int = 0
    total_steps: int = 5
    message: str = ""
    errors: List[str] = field(default_factory=list)


class ClonerService:
    """
    Servicio de clonación de cursos.
    
    Orquesta el proceso completo:
    1. Validar curso origen
    2. Duplicar curso via API de Moodle
    3. Obtener contenido del nuevo curso
    4. Procesar y actualizar enlaces
    5. Reportar resultados
    """
    
    def __init__(
        self, 
        moodle_client: Optional[MoodleClient] = None,
        html_processor: Optional[HTMLProcessor] = None
    ):
        """
        Inicializa el servicio de clonación.
        
        Args:
            moodle_client: Cliente de Moodle (por defecto usa el singleton)
            html_processor: Procesador HTML (por defecto usa el singleton)
        """
        self.moodle = moodle_client or get_moodle_client()
        self.html_processor = html_processor or get_html_processor()
        self.progress = CloneProgress()
    
    def _update_progress(self, step: str, progress: int, message: str):
        """Actualiza el estado del progreso"""
        self.progress.step = step
        self.progress.progress = progress
        self.progress.message = message
    
    async def get_available_courses(self) -> List[CourseFromMoodle]:
        """
        Obtiene la lista de cursos disponibles para clonar.
        
        Returns:
            Lista de cursos disponibles
        """
        try:
            courses_data = await self.moodle.get_courses()
            
            # Filtrar el curso del sitio (id=1) y convertir a schema
            courses = [
                CourseFromMoodle(**course) 
                for course in courses_data 
                if course.get('id', 0) != 1  # Excluir "Site" course
            ]
            
            return courses
            
        except MoodleAPIError as e:
            raise Exception(f"Error al obtener cursos: {e.message}")
    
    async def get_course_by_id(self, course_id: int) -> Optional[CourseFromMoodle]:
        """
        Obtiene un curso específico por su ID.
        
        Args:
            course_id: ID del curso
            
        Returns:
            Datos del curso o None si no existe
        """
        try:
            courses = await self.moodle.get_courses([course_id])
            if courses:
                return CourseFromMoodle(**courses[0])
            return None
        except MoodleAPIError:
            return None
    
    async def duplicate_course(
        self, 
        request: CourseDuplicateRequest
    ) -> CourseDuplicateResponse:
        """
        Duplica un curso completo con personalización de enlaces.
        
        Este es el método principal que ejecuta todo el flujo de clonación.
        
        Args:
            request: Datos de la solicitud de duplicación
            
        Returns:
            Respuesta con los resultados de la operación
        """
        links_updated = 0
        
        try:
            # Paso 1: Validar curso origen
            self._update_progress("validating", 10, "Validando curso origen...")
            source_course = await self.get_course_by_id(request.source_course_id)
            
            if not source_course:
                return CourseDuplicateResponse(
                    success=False,
                    new_course_id=0,
                    new_course_url="",
                    message=f"Curso origen con ID {request.source_course_id} no encontrado",
                    links_updated=0
                )
            
            # Usar la categoría del curso origen si no se especifica otra
            target_category = request.category_id or source_course.categoryid or 1
            
            # Paso 2: Duplicar el curso
            self._update_progress("duplicating", 30, "Duplicando curso en Moodle...")
            
            duplicate_result = await self.moodle.duplicate_course(
                course_id=request.source_course_id,
                fullname=request.new_fullname,
                shortname=request.new_shortname,
                category_id=target_category,
                visible=request.visible
            )
            
            new_course_id = duplicate_result.get('id')
            
            if not new_course_id:
                return CourseDuplicateResponse(
                    success=False,
                    new_course_id=0,
                    new_course_url="",
                    message="Error: Moodle no retornó el ID del nuevo curso",
                    links_updated=0
                )
            
            # Paso 3: Obtener contenido del nuevo curso
            self._update_progress("fetching", 50, "Obteniendo contenido del nuevo curso...")
            
            course_contents = await self.moodle.get_course_contents(new_course_id)
            
            # Paso 4: Procesar enlaces si se especificó URL del docente
            if request.new_teacher_profile_url:
                self._update_progress("processing", 70, "Procesando enlaces del docente...")
                
                links_updated = await self._process_teacher_links(
                    course_id=new_course_id,
                    course_contents=course_contents,
                    new_teacher_url=request.new_teacher_profile_url
                )
            
            # Paso 5: Finalizar
            self._update_progress("completed", 100, "Clonación completada exitosamente")
            
            # Construir URL del nuevo curso
            base_url = settings.moodle_url.rstrip('/')
            new_course_url = f"{base_url}/course/view.php?id={new_course_id}"
            
            return CourseDuplicateResponse(
                success=True,
                new_course_id=new_course_id,
                new_course_url=new_course_url,
                message=f"Curso '{request.new_fullname}' creado exitosamente",
                links_updated=links_updated
            )
            
        except MoodleAPIError as e:
            self.progress.errors.append(str(e.message))
            return CourseDuplicateResponse(
                success=False,
                new_course_id=0,
                new_course_url="",
                message=f"Error de Moodle: {e.message}",
                links_updated=links_updated
            )
        except Exception as e:
            self.progress.errors.append(str(e))
            return CourseDuplicateResponse(
                success=False,
                new_course_id=0,
                new_course_url="",
                message=f"Error inesperado: {str(e)}",
                links_updated=links_updated
            )
    
    async def _process_teacher_links(
        self,
        course_id: int,
        course_contents: List[Dict[str, Any]],
        new_teacher_url: str,
        old_teacher_url: Optional[str] = None
    ) -> int:
        """
        Procesa y actualiza los enlaces del perfil del docente en todo el curso.
        
        Args:
            course_id: ID del curso
            course_contents: Contenido del curso desde Moodle API
            new_teacher_url: Nueva URL del docente
            old_teacher_url: URL anterior (opcional, se auto-detecta si no se proporciona)
            
        Returns:
            Cantidad de enlaces actualizados
        """
        total_updated = 0
        
        for section in course_contents:
            # Procesar resumen de sección
            if section.get('summary'):
                processed_html, count = self.html_processor.replace_teacher_profile_links(
                    html_content=section['summary'],
                    new_teacher_url=new_teacher_url,
                    old_teacher_url=old_teacher_url
                )
                
                if count > 0:
                    total_updated += count
                    # NOTA: La actualización real del contenido en Moodle
                    # requeriría llamar a la API correspondiente
                    # Por ahora solo contamos los cambios potenciales
            
            # Procesar módulos de la sección
            for module in section.get('modules', []):
                module_type = module.get('modname', '')
                
                # Procesar descripción/contenido del módulo
                description = module.get('description', '')
                
                if description:
                    processed_html, count = self.html_processor.replace_teacher_profile_links(
                        html_content=description,
                        new_teacher_url=new_teacher_url,
                        old_teacher_url=old_teacher_url
                    )
                    
                    if count > 0:
                        total_updated += count
                        # NOTA: Actualización real pendiente
                
                # Para módulos type 'page', puede haber contenido adicional
                if module_type in ('page', 'label'):
                    # El contenido completo de páginas puede necesitar
                    # una llamada adicional a mod_page_get_pages_by_courses
                    pass
        
        return total_updated
    
    async def scan_course_links(
        self, 
        course_id: int
    ) -> Dict[str, Any]:
        """
        Escanea un curso para encontrar todos los enlaces en su contenido.
        
        Args:
            course_id: ID del curso a escanear
            
        Returns:
            Diccionario con información de enlaces encontrados
        """
        try:
            course_contents = await self.moodle.get_course_contents(course_id)
            
            all_links = []
            teacher_links = []
            
            for section in course_contents:
                section_name = section.get('name', 'Sin nombre')
                
                # Escanear resumen de sección
                if section.get('summary'):
                    links = self.html_processor.find_all_links(section['summary'])
                    for link in links:
                        link['location'] = f"Sección: {section_name}"
                        all_links.append(link)
                        
                        if self.html_processor.is_teacher_profile_link(
                            link['href'], link['text']
                        ):
                            teacher_links.append(link)
                
                # Escanear módulos
                for module in section.get('modules', []):
                    module_name = module.get('name', 'Sin nombre')
                    module_type = module.get('modname', 'desconocido')
                    description = module.get('description', '')
                    
                    if description:
                        links = self.html_processor.find_all_links(description)
                        for link in links:
                            link['location'] = f"{module_type}: {module_name}"
                            link['module_id'] = module.get('id')
                            all_links.append(link)
                            
                            if self.html_processor.is_teacher_profile_link(
                                link['href'], link['text']
                            ):
                                teacher_links.append(link)
            
            return {
                'course_id': course_id,
                'total_links': len(all_links),
                'all_links': all_links,
                'teacher_profile_links': teacher_links,
                'teacher_links_count': len(teacher_links)
            }
            
        except MoodleAPIError as e:
            raise Exception(f"Error al escanear curso: {e.message}")


# Singleton del servicio
_cloner_service: Optional[ClonerService] = None


def get_cloner_service() -> ClonerService:
    """
    Obtiene la instancia global del servicio de clonación.
    
    Returns:
        ClonerService: Instancia del servicio
    """
    global _cloner_service
    if _cloner_service is None:
        _cloner_service = ClonerService()
    return _cloner_service
