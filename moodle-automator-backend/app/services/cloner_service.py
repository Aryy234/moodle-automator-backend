"""
Cloner Service - Course Duplication & Customization Orchestration

Servicio principal que orquesta:
1. Clonación de cursos vía API de Moodle
2. Lectura del contenido HTML de la sección General
3. Personalización del HTML (placeholders, título, horario, bibliografía)
4. Escritura del HTML modificado de vuelta a Moodle
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

from app.integration.moodle_client import MoodleClient, get_moodle_client, MoodleAPIError
from app.services.html_processor import HTMLProcessor, get_html_processor
from app.schemas.course import (
    CourseDuplicateRequest,
    CourseDuplicateResponse,
    CourseFromMoodle,
)
from app.schemas.editor import (
    CourseCustomizationRequest,
    CourseCustomizationResponse,
    ReplacementDetail,
    PlaceholderScanResponse,
)
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
    Servicio de clonación y personalización de cursos.
    """

    def __init__(
        self,
        moodle_client: Optional[MoodleClient] = None,
        html_processor: Optional[HTMLProcessor] = None,
    ):
        self.moodle = moodle_client or get_moodle_client()
        self.html_processor = html_processor or get_html_processor()
        self.progress = CloneProgress()

    def _update_progress(self, step: str, progress: int, message: str):
        self.progress.step = step
        self.progress.progress = progress
        self.progress.message = message

    # ==================================================================
    # COURSE QUERIES
    # ==================================================================

    async def get_available_courses(self) -> List[CourseFromMoodle]:
        """Obtiene la lista de cursos disponibles (excluyendo id=1)."""
        try:
            courses_data = await self.moodle.get_courses()
            return [
                CourseFromMoodle(**c)
                for c in courses_data
                if c.get("id", 0) != 1
            ]
        except MoodleAPIError as e:
            raise Exception(f"Error al obtener cursos: {e.message}")

    async def get_course_by_id(self, course_id: int) -> Optional[CourseFromMoodle]:
        try:
            courses = await self.moodle.get_courses([course_id])
            if courses:
                return CourseFromMoodle(**courses[0])
            return None
        except MoodleAPIError:
            return None

    # ==================================================================
    # OBTENER HTML DE LA SECCIÓN GENERAL (section 0)
    # ==================================================================

    TEMPLATE_MARKERS = [
        "video-introductorio", "perfil-docente", "cronograma", "biblio",
        "unirse-clases", "url-grabaciones", "silabo", "pea",
    ]

    def _html_has_template(self, html: str) -> bool:
        """Verifica si un HTML contiene marcadores del template del curso base."""
        return any(marker in html for marker in self.TEMPLATE_MARKERS)

    async def _get_general_section_html(self, course_id: int) -> tuple:
        """
        Obtiene el HTML del template de la sección General (section 0).

        Estrategia de búsqueda (en orden de prioridad):
        1. Summary de la sección 0
           → Se actualiza vía core_courseformat_update_course (Moodle 4.0+)
        2. Label (Text and media area) en sección 0 con los placeholders
           → Fallback para cursos donde el template está en un label

        Retorna: (html_content, section_info) donde section_info tiene
        los datos necesarios para luego actualizar.
        """
        contents = await self.moodle.get_course_contents(course_id)

        if not contents:
            raise Exception("El curso no tiene contenido")

        general_section = contents[0]

        # --- Prioridad 1: Summary de la sección ---
        summary = general_section.get("summary", "")
        if summary and self._html_has_template(summary):
            print(f"✅ Template encontrado en section summary (section_id={general_section.get('id')})")
            return summary, {
                "section_id": general_section.get("id"),
                "section_number": general_section.get("section", 0),
                "section_name": general_section.get("name", "General"),
                "source": "section_summary",
            }

        # --- Prioridad 2: Buscar en labels de la sección 0 ---
        for module in general_section.get("modules", []):
            if module.get("modname") == "label":
                desc = module.get("description", "")
                if desc and self._html_has_template(desc):
                    print(f"✅ Template encontrado en label: id={module['id']} instance={module.get('instance')}")
                    return desc, {
                        "section_id": general_section.get("id"),
                        "section_number": general_section.get("section", 0),
                        "section_name": general_section.get("name", "General"),
                        "source": "label",
                        "label_instance_id": module.get("instance"),
                        "label_cmid": module.get("id"),
                    }

        # --- No se encontró el template ---
        raise Exception(
            "No se encontró el template HTML del curso base. "
            "Verifica que la sección General contiene el template HTML "
            "en su resumen (summary) o en un label con los placeholders del template."
        )

    # ==================================================================
    # ESCANEO DE PLACEHOLDERS
    # ==================================================================

    async def scan_course_placeholders(self, course_id: int) -> PlaceholderScanResponse:
        """
        Escanea la sección General del curso para encontrar placeholders editables.
        """
        html, section_info = await self._get_general_section_html(course_id)
        scan = self.html_processor.scan_placeholders(html)

        source = section_info.get("source", "unknown")
        can_save = source in ("section_summary", "label")
        save_hint = None if can_save else (
            "No se encontró una fuente editable para el template."
        )

        return PlaceholderScanResponse(
            course_id=course_id,
            section_name=section_info.get("section_name", "General"),
            module_id=section_info.get("section_id"),
            module_name=f"Sección: {section_info.get('section_name', 'General')}",
            total_placeholders=scan["total_placeholders"],
            placeholders=scan["placeholders"],
            schedule_found=scan["schedule_found"],
            bibliography_found=scan["bibliography_found"],
            course_title=scan["course_title"],
            course_description=scan["course_description"],
            template_source=source,
            can_save=can_save,
            save_hint=save_hint,
        )

    # ==================================================================
    # PERSONALIZACIÓN DEL HTML
    # ==================================================================

    async def customize_course(
        self,
        request: CourseCustomizationRequest,
        preview_only: bool = False,
    ) -> CourseCustomizationResponse:
        """
        Personaliza el HTML de una o varias secciones del curso.
        Si se envía 'sections', personaliza cada sección indicada.
        Si no, usa el modo legacy (solo General).
        """
        try:
            all_details = []
            processed_htmls = {}
            total_replacements = 0
            # Si se envía 'sections', procesar cada sección
            if request.sections:
                # Obtener contenidos de todas las secciones
                contents = await self.moodle.get_course_contents(request.course_id)
                section_map = {s["id"]: s for s in contents}
                for section_req in request.sections:
                    section_id = section_req.section_id
                    section = section_map.get(section_id)
                    if not section:
                        all_details.append(ReplacementDetail(
                            field=f"section_{section_id}",
                            old_value="",
                            new_value="No se encontró la sección en el curso"
                        ))
                        continue
                    html = section.get("summary", "")

                    # --- Construir placeholders ---
                    placeholders = {}
                    if section_req.video_introductorio:
                        placeholders["video-introductorio"] = section_req.video_introductorio
                    if section_req.unirse_clases:
                        placeholders["unirse-clases"] = section_req.unirse_clases
                    if section_req.url_grabaciones:
                        placeholders["url-grabaciones"] = section_req.url_grabaciones
                    if section_req.perfil_docente:
                        placeholders["perfil-docente"] = section_req.perfil_docente
                    if section_req.silabo:
                        placeholders["silabo"] = section_req.silabo
                    if section_req.pea:
                        placeholders["pea"] = section_req.pea
                    if section_req.bibliografia_url:
                        placeholders["bibliografia"] = section_req.bibliografia_url

                    # --- Personalizar SOLO el summary de la sección (sin bloques avanzados) ---
                    new_html, details = self.html_processor.customize_html(
                        html=html,
                        placeholders=placeholders if placeholders else None,
                        course_title=section_req.course_title,
                        course_description=section_req.course_description,
                        schedule=section_req.schedule,
                        bibliography=section_req.bibliography,
                        # Los bloques avanzados se crean como labels SEPARADOS (ver abajo)
                        presentations=None,
                        presentation_objective=None,
                        main_reading=None,
                        suggested_readings=None,
                        videos=None,
                        videos_summary=None,
                    )
                    all_details.extend(details)
                    total_replacements += len(details)

                    # --- Guardar summary en Moodle si corresponde ---
                    section_blocks_preview: dict = {}
                    if not preview_only and details:
                        await self.moodle.update_section_summary(
                            course_id=request.course_id,
                            section_id=section_id,
                            section_number=section_req.section_number or 0,
                            summary=new_html,
                        )

                    # =======================================================
                    # BLOQUES AVANZADOS — cada uno como un label separado
                    # =======================================================
                    presentations = getattr(section_req, "presentations", None)
                    presentation_objective = getattr(section_req, "presentation_objective", None)
                    main_reading = getattr(section_req, "main_reading", None)
                    suggested_readings = getattr(section_req, "suggested_readings", None)
                    videos = getattr(section_req, "videos", None)
                    videos_summary = getattr(section_req, "videos_summary", None)

                    # -- Bloque de presentaciones --
                    if presentations:
                        pres_html = self.html_processor.render_presentations_block(
                            presentations, presentation_objective
                        )
                        if not preview_only:
                            await self.moodle.create_label_in_section(
                                course_id=request.course_id,
                                section_id=section_id,
                                content=pres_html,
                                name="Presentación",
                            )
                            print(f"📊 Label 'Presentación' creado en sección {section_id}")
                        else:
                            section_blocks_preview["presentations_block"] = pres_html
                        all_details.append(ReplacementDetail(
                            field="presentations_block",
                            old_value="",
                            new_value="Bloque de presentaciones creado como label independiente",
                        ))
                        total_replacements += 1

                    # -- Bloque de lecturas --
                    if main_reading:
                        reading_html = self.html_processor.render_main_reading_block(
                            main_reading,
                            suggested_readings,
                            collapse_label=getattr(section_req, "reading_collapse_label", None) or "Lectura",
                            reading_section_title=getattr(section_req, "reading_section_title", None) or "Lectura principal",
                            main_button_text=getattr(section_req, "reading_button_text", None) or "Ver lectura",
                            suggested_title=getattr(section_req, "reading_suggested_title", None) or "Lecturas sugeridas",
                        )
                        if not preview_only:
                            await self.moodle.create_label_in_section(
                                course_id=request.course_id,
                                section_id=section_id,
                                content=reading_html,
                                name="Lectura",
                            )
                            print(f"📖 Label 'Lectura' creado en sección {section_id}")
                        else:
                            section_blocks_preview["reading_block"] = reading_html
                        all_details.append(ReplacementDetail(
                            field="reading_block",
                            old_value="",
                            new_value="Bloque de lectura creado como label independiente",
                        ))
                        total_replacements += 1

                    # -- Bloque de videos --
                    if videos:
                        videos_html = self.html_processor.render_videos_block(
                            videos, videos_summary
                        )
                        if not preview_only:
                            await self.moodle.create_label_in_section(
                                course_id=request.course_id,
                                section_id=section_id,
                                content=videos_html,
                                name="Video",
                            )
                            print(f"🎥 Label 'Video' creado en sección {section_id}")
                        else:
                            section_blocks_preview["videos_block"] = videos_html
                        all_details.append(ReplacementDetail(
                            field="videos_block",
                            old_value="",
                            new_value="Bloque de video creado como label independiente",
                        ))
                        total_replacements += 1

                    # Registrar el preview de esta sección
                    processed_htmls[section_id] = {
                        "summary": new_html,
                        **section_blocks_preview,
                    }

                msg = f"Se personalizaron {len(request.sections)} secciones. Total de cambios: {total_replacements}"
                processed_html_str = None
                if preview_only:
                    import json
                    processed_html_str = json.dumps(processed_htmls, ensure_ascii=False, indent=2)
                return CourseCustomizationResponse(
                    success=True,
                    course_id=request.course_id,
                    message=msg + (" (preview, no guardados)" if preview_only else " exitosamente"),
                    total_replacements=total_replacements,
                    details=all_details,
                    processed_html=processed_html_str if preview_only else None,
                )
            # Legacy: solo General
            # 1. Obtener HTML actual
            html, section_info = await self._get_general_section_html(request.course_id)
            # 2. Construir mapa de placeholders
            placeholders: Dict[str, str] = {}
            if request.video_introductorio:
                placeholders["video-introductorio"] = request.video_introductorio
            if request.unirse_clases:
                placeholders["unirse-clases"] = request.unirse_clases
            if request.url_grabaciones:
                placeholders["url-grabaciones"] = request.url_grabaciones
            if request.perfil_docente:
                placeholders["perfil-docente"] = request.perfil_docente
            if request.silabo:
                placeholders["silabo"] = request.silabo
            if request.pea:
                placeholders["pea"] = request.pea
            if request.bibliografia_url:
                placeholders["bibliografia"] = request.bibliografia_url
            # 3. Aplicar personalizaciones
            new_html, details = self.html_processor.customize_html(
                html=html,
                placeholders=placeholders if placeholders else None,
                course_title=request.course_title,
                course_description=request.course_description,
                schedule=request.schedule,
                bibliography=request.bibliography,
            )
            if not details:
                return CourseCustomizationResponse(
                    success=True,
                    course_id=request.course_id,
                    message="No se encontraron elementos para actualizar con los datos proporcionados.",
                    total_replacements=0,
                    details=[],
                    processed_html=new_html if preview_only else None,
                )
            # 4. Guardar en Moodle (si no es preview)
            if not preview_only:
                await self._update_html_in_moodle(
                    course_id=request.course_id,
                    section_info=section_info,
                    new_html=new_html,
                )
            return CourseCustomizationResponse(
                success=True,
                course_id=request.course_id,
                message=f"Se realizaron {len(details)} cambios" + 
                        (" (preview, no guardados)" if preview_only else " exitosamente"),
                total_replacements=len(details),
                details=details,
                processed_html=new_html if preview_only else None,
            )
        except MoodleAPIError as e:
            return CourseCustomizationResponse(
                success=False,
                course_id=request.course_id,
                message=f"Error de Moodle: {e.message}",
            )
        except Exception as e:
            return CourseCustomizationResponse(
                success=False,
                course_id=request.course_id,
                message=f"Error: {str(e)}",
            )

    # ==================================================================
    # ACTUALIZACIÓN EN MOODLE
    # ==================================================================

    async def _update_html_in_moodle(
        self, course_id: int, section_info: dict, new_html: str
    ):
        """
        Actualiza el HTML del template en Moodle según la fuente detectada.

        - source='section_summary' → usa core_courseformat_update_course
        - source='label' → usa mod_label_update_labels (fallback)
        """
        source = section_info.get("source")

        if source == "section_summary":
            section_id = section_info["section_id"]
            section_number = section_info.get("section_number", 0)
            print(f"📝 Actualizando section summary (section_id={section_id}) vía core_courseformat_update_course")
            await self.moodle.update_section_summary(
                course_id=course_id,
                section_id=section_id,
                section_number=section_number,
                summary=new_html,
            )
            return

        if source == "label":
            instance_id = section_info["label_instance_id"]
            print(f"📝 Actualizando label instance_id={instance_id} vía mod_label_update_labels")
            await self.moodle.update_label(instance_id, new_html)
            print("✅ Label actualizado correctamente en Moodle")
            return

        raise Exception(
            "No se puede guardar: fuente del template no reconocida. "
            f"source='{source}'"
        )

    # ==================================================================
    # ESCANEO DE LINKS (LEGACY - mantener compatibilidad)
    # ==================================================================

    async def scan_course_links(self, course_id: int) -> Dict[str, Any]:
        """Escanea un curso para encontrar todos los enlaces."""
        try:
            course_contents = await self.moodle.get_course_contents(course_id)
            all_links = []
            teacher_links = []

            for section in course_contents:
                section_name = section.get("name", "Sin nombre")

                if section.get("summary"):
                    links = self._extract_links_from_html(
                        section["summary"], f"Sección: {section_name}"
                    )
                    all_links.extend(links)

                for module in section.get("modules", []):
                    description = module.get("description", "")
                    if description:
                        loc = f"{module.get('modname', '')}: {module.get('name', '')}"
                        links = self._extract_links_from_html(description, loc)
                        for link in links:
                            link["module_id"] = module.get("id")
                        all_links.extend(links)

            return {
                "course_id": course_id,
                "total_links": len(all_links),
                "all_links": all_links,
                "teacher_profile_links": teacher_links,
                "teacher_links_count": len(teacher_links),
            }
        except MoodleAPIError as e:
            raise Exception(f"Error al escanear curso: {e.message}")

    def _extract_links_from_html(self, html: str, location: str) -> list:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        links = []
        for tag in soup.find_all(["a", "iframe"]):
            attr = "href" if tag.name == "a" else "src"
            value = tag.get(attr, "")
            if value:
                links.append({
                    "href": value,
                    "text": tag.get_text(strip=True) if tag.name == "a" else "",
                    "element_type": tag.name,
                    "location": location,
                })
        return links

    # ==================================================================
    # DUPLICACIÓN DE CURSOS
    # ==================================================================

    async def duplicate_course(
        self, request: CourseDuplicateRequest
    ) -> CourseDuplicateResponse:
        """Duplica un curso completo."""
        links_updated = 0

        try:
            self._update_progress("validating", 10, "Validando curso origen...")
            source_course = await self.get_course_by_id(request.source_course_id)

            if not source_course:
                return CourseDuplicateResponse(
                    success=False,
                    new_course_id=0,
                    new_course_url="",
                    message=f"Curso origen con ID {request.source_course_id} no encontrado",
                    links_updated=0,
                )

            # Forzar duplicación en category_id=1 si no se especifica explícitamente
            if request.category_id is not None:
                target_category = request.category_id
            else:
                target_category = 1

            self._update_progress("duplicating", 30, "Duplicando curso en Moodle...")
            duplicate_result = await self.moodle.duplicate_course(
                course_id=request.source_course_id,
                fullname=request.new_fullname,
                shortname=request.new_shortname,
                category_id=target_category,
                visible=request.visible,
                idnumber=request.new_idnumber,
            )

            new_course_id = duplicate_result.get("id")
            if not new_course_id:
                return CourseDuplicateResponse(
                    success=False,
                    new_course_id=0,
                    new_course_url="",
                    message="Error: Moodle no retornó el ID del nuevo curso",
                    links_updated=0,
                )

            self._update_progress("completed", 100, "Clonación completada")
            base_url = settings.moodle_url.rstrip("/")
            new_course_url = f"{base_url}/course/view.php?id={new_course_id}"

            return CourseDuplicateResponse(
                success=True,
                new_course_id=new_course_id,
                new_course_url=new_course_url,
                message=f"Curso '{request.new_fullname}' creado exitosamente",
                links_updated=links_updated,
            )

        except MoodleAPIError as e:
            self.progress.errors.append(str(e.message))
            return CourseDuplicateResponse(
                success=False,
                new_course_id=0,
                new_course_url="",
                message=f"Error de Moodle: {e.message}",
                links_updated=links_updated,
            )
        except Exception as e:
            self.progress.errors.append(str(e))
            return CourseDuplicateResponse(
                success=False,
                new_course_id=0,
                new_course_url="",
                message=f"Error inesperado: {str(e)}",
                links_updated=links_updated,
            )


# Singleton
_cloner_service: Optional[ClonerService] = None


def get_cloner_service() -> ClonerService:
    global _cloner_service
    if _cloner_service is None:
        _cloner_service = ClonerService()
    return _cloner_service
