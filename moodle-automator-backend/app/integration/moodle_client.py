"""
Moodle Client - Integration Layer

Cliente HTTP asíncrono para comunicación con la API de Web Services de Moodle.
Encapsula todas las llamadas a la API de Moodle en un solo lugar.
"""

import httpx
import json
from typing import Any, Dict, List, Optional
from app.core.config import settings


class MoodleAPIError(Exception):
    """Excepción personalizada para errores de la API de Moodle"""
    def __init__(self, message: str, error_code: Optional[str] = None, debug_info: Optional[str] = None):
        self.message = message
        self.error_code = error_code
        self.debug_info = debug_info
        super().__init__(self.message)


class MoodleClient:
    """
    Cliente para la API de Web Services de Moodle.
    
    Implementa los métodos necesarios para:
    - Listar cursos
    - Duplicar cursos
    - Obtener contenido de cursos
    - Actualizar módulos
    """
    
    def __init__(self, moodle_url: Optional[str] = None, token: Optional[str] = None):
        """
        Inicializa el cliente de Moodle.
        
        Args:
            moodle_url: URL base de Moodle (por defecto de config)
            token: Token de Web Service (por defecto de config)
        """
        self.base_url = moodle_url or settings.moodle_webservice_url
        self.token = token or settings.moodle_token
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Obtiene o crea el cliente HTTP asíncrono"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=60.0)
        return self._client
    
    async def close(self):
        """Cierra el cliente HTTP"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
    
    async def _call_api(
        self, 
        wsfunction: str, 
        params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Realiza una llamada a la API de Moodle.
        
        Args:
            wsfunction: Nombre de la función de Web Service
            params: Parámetros adicionales para la llamada
            
        Returns:
            Respuesta JSON de Moodle
            
        Raises:
            MoodleAPIError: Si hay un error en la API
        """
        client = await self._get_client()
        
        # Parámetros base requeridos por Moodle
        data = {
            "wstoken": self.token,
            "wsfunction": wsfunction,
            "moodlewsrestformat": "json"
        }
        
        # Agregar parámetros adicionales
        if params:
            data.update(params)
        
        try:
            response = await client.post(self.base_url, data=data)
            response.raise_for_status()
            result = response.json()
            
            # Moodle retorna errores en el JSON, no como HTTP errors
            if isinstance(result, dict) and "exception" in result:
                # Log completo para depuración
                print(f"⚠️  Moodle API Error en '{wsfunction}':")
                print(f"   exception: {result.get('exception')}")
                print(f"   errorcode: {result.get('errorcode')}")
                print(f"   message: {result.get('message')}")
                print(f"   debuginfo: {result.get('debuginfo', 'N/A')}")
                
                raise MoodleAPIError(
                    message=result.get("message", "Error desconocido de Moodle"),
                    error_code=result.get("errorcode"),
                    debug_info=result.get("debuginfo")
                )
            
            return result
            
        except httpx.HTTPStatusError as e:
            raise MoodleAPIError(
                message=f"Error HTTP al conectar con Moodle: {e.response.status_code}",
                error_code="HTTP_ERROR"
            )
        except httpx.RequestError as e:
            raise MoodleAPIError(
                message=f"Error de conexión con Moodle: {str(e)}",
                error_code="CONNECTION_ERROR"
            )
    
    # ==================== COURSE OPERATIONS ====================
    
    async def get_courses(self, course_ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """
        Obtiene la lista de cursos.
        
        Args:
            course_ids: Lista opcional de IDs de cursos específicos
            
        Returns:
            Lista de cursos con sus datos
        """
        params = {}
        
        if course_ids:
            # Moodle espera los IDs en formato array: options[ids][0], options[ids][1], etc.
            for i, cid in enumerate(course_ids):
                params[f"options[ids][{i}]"] = cid
        
        return await self._call_api("core_course_get_courses", params)
    
    async def get_enrolled_courses(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene los cursos en los que está inscrito un usuario.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Lista de cursos donde el usuario está inscrito
        """
        return await self._call_api(
            "core_enrol_get_users_courses",
            {"userid": user_id}
        )
    
    async def duplicate_course(
        self,
        course_id: int,
        fullname: str,
        shortname: str,
        category_id: int,
        visible: int = 0,
        idnumber: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Duplica un curso existente.

        Args:
            course_id:   ID del curso origen
            fullname:    Nombre completo del nuevo curso
            shortname:   Nombre corto del nuevo curso
            category_id: ID de la categoría destino
            visible:     Visibilidad inicial (0=oculto, 1=visible)
            idnumber:    Número ID interno opcional (campo idnumber de Moodle)

        Returns:
            Datos del nuevo curso creado (incluyendo su ID)
        """
        params = {
            "courseid":   course_id,
            "fullname":   fullname,
            "shortname":  shortname,
            "categoryid": category_id,
            "visible":    visible,
        }

        result = await self._call_api("core_course_duplicate_course", params)

        # core_course_duplicate_course no acepta idnumber directamente,
        # así que lo actualizamos en un segundo paso si se especificó.
        if idnumber is not None:
            new_id = result.get("id")
            if new_id:
                await self._call_api(
                    "core_course_update_courses",
                    {"courses[0][id]": new_id, "courses[0][idnumber]": idnumber},
                )
                print(f"✅ idnumber='{idnumber}' asignado al curso {new_id}")

        return result
    
    async def get_course_contents(self, course_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene el contenido completo de un curso (secciones y módulos).
        
        Args:
            course_id: ID del curso
            
        Returns:
            Lista de secciones con sus módulos
        """
        return await self._call_api(
            "core_course_get_contents",
            {"courseid": course_id}
        )
    
    async def update_course(
        self,
        course_id: int,
        **kwargs
    ) -> None:
        """
        Actualiza datos de un curso.
        
        Args:
            course_id: ID del curso
            **kwargs: Campos a actualizar (fullname, shortname, summary, etc.)
        """
        params = {"courses[0][id]": course_id}
        
        for key, value in kwargs.items():
            params[f"courses[0][{key}]"] = value
        
        await self._call_api("core_course_update_courses", params)
    
    async def update_section_summary(
        self,
        course_id: int,
        section_id: int,
        section_number: int,
        summary: str,
    ) -> None:
        """
        Actualiza el summary (resumen HTML) de una sección del curso.

        Usa local_sectionedit_update_section_summary (plugin personalizado)
        que escribe directamente en mdl_course_sections.summary.

        Requiere instalar el plugin local_sectionedit en Moodle y agregar
        la función al servicio web del token.

        Args:
            course_id: ID del curso (solo para logs; el plugin lo resuelve desde section_id)
            section_id: ID de la sección (mdl_course_sections.id)
            section_number: Número de la sección (0 = General)
            summary: Nuevo contenido HTML del summary
        """
        params = {
            "sectionid": section_id,
            "summary": summary,
            "summaryformat": 1,  # FORMAT_HTML
        }

        try:
            result = await self._call_api(
                "local_sectionedit_update_section_summary", params
            )
            print(f"✅ Section summary actualizado (section_id={section_id})")
            return result
        except MoodleAPIError as e:
            if "accessexception" in str(e.error_code or "").lower():
                raise MoodleAPIError(
                    message=(
                        "No se pudo actualizar la sección: falta la función "
                        "local_sectionedit_update_section_summary en tu servicio web de Moodle. "
                        "Instala el plugin local_sectionedit y agrega la función desde: "
                        "Administración del sitio → Servidor → Servicios externos → "
                        "[tu servicio] → Funciones → Agregar."
                    ),
                    error_code=e.error_code,
                    debug_info=e.debug_info,
                )
            raise

    # ==================== LABEL OPERATIONS ====================

    async def create_label_in_section(
        self,
        course_id: int,
        section_id: int,
        content: str,
        name: str = "",
    ) -> dict:
        """
        Crea un nuevo módulo label (Text and media area) dentro de una sección.

        Llama a la función del plugin personalizado:
        local_sectionedit_add_label_to_section

        Args:
            course_id:  ID del curso
            section_id: ID de la sección (mdl_course_sections.id)
            content:    HTML del label
            name:       Nombre interno del label (opcional)

        Returns:
            Dict con 'status', 'cmid' y 'message'
        """
        params = {
            "courseid":  course_id,
            "sectionid": section_id,
            "content":   content,
            "name":      name,
        }

        try:
            result = await self._call_api(
                "local_sectionedit_add_label_to_section", params
            )
            print(
                f"✅ Label creado en sección {section_id} "
                f"(cmid={result.get('cmid')}, nombre='{name}')"
            )
            return result
        except MoodleAPIError as e:
            if "accessexception" in str(e.error_code or "").lower():
                raise MoodleAPIError(
                    message=(
                        "No se pudo crear el label: falta la función "
                        "local_sectionedit_add_label_to_section en tu servicio web de Moodle. "
                        "Actualiza el plugin local_sectionedit y agrega la función desde: "
                        "Administración del sitio → Servidor → Servicios externos → "
                        "[tu servicio] → Funciones → Agregar."
                    ),
                    error_code=e.error_code,
                    debug_info=e.debug_info,
                )
            raise

    async def update_label(self, instance_id: int, new_content: str) -> None:
        """
        Actualiza el contenido (intro) de un label en Moodle.
        
        Usa ``local_sectionedit_update_label`` (plugin propio, más confiable)
        como método principal. Si el plugin no está disponible, intenta
        ``mod_label_update_labels`` como fallback.
        
        Args:
            instance_id: ID de la instancia del label (mdl_label.id)
            new_content: Nuevo contenido HTML del label
        """
        # --- Método 1: Plugin propio (más confiable) ---
        try:
            params = {
                "labelid": instance_id,
                "content": new_content,
            }
            result = await self._call_api("local_sectionedit_update_label", params)
            print(f"✅ Label actualizado via local_sectionedit_update_label (instance={instance_id})")
            return
        except MoodleAPIError as e:
            print(f"⚠️ local_sectionedit_update_label falló: {e.message}. Intentando fallback...")

        # --- Método 2: Función core de Moodle (fallback) ---
        params = {
            "labels[0][id]": instance_id,
            "labels[0][intro]": new_content,
            "labels[0][introformat]": 1,  # HTML format
        }
        try:
            await self._call_api("mod_label_update_labels", params)
            print(f"✅ Label actualizado via mod_label_update_labels (instance={instance_id})")
        except MoodleAPIError as e:
            raise MoodleAPIError(
                message=(
                    f"No se pudo actualizar el label (instance={instance_id}): {e.message}. "
                    "Verifica que: 1) El plugin local_sectionedit v1.2.7+ esté instalado, "
                    "o 2) mod_label_update_labels esté habilitado en el servicio web."
                ),
                error_code=e.error_code,
                debug_info=e.debug_info,
            )

    # ==================== MODULE OPERATIONS ====================
    
    async def get_page_content(self, page_id: int) -> Dict[str, Any]:
        """
        Obtiene el contenido de un módulo tipo 'page'.
        
        Args:
            page_id: ID de la instancia de la página (no el cmid)
            
        Returns:
            Datos de la página incluyendo el contenido HTML
        """
        # Nota: Moodle no tiene una función directa para esto,
        # se obtiene a través de mod_page_get_pages_by_courses
        # pero necesitaremos course_id, así que esto es una simplificación
        raise NotImplementedError(
            "Para obtener contenido de páginas, usar get_course_contents"
        )
    
    async def update_module_content(
        self,
        cmid: int,
        content: str,
        module_type: str = "page"
    ) -> bool:
        """
        Actualiza el contenido de un módulo.
        
        NOTA: Esta operación puede requerir funciones de Web Service adicionales
        según el tipo de módulo. Moodle tiene limitaciones en la edición directa
        de contenido vía API.
        
        Args:
            cmid: Course Module ID
            content: Nuevo contenido HTML
            module_type: Tipo de módulo
            
        Returns:
            True si la actualización fue exitosa
        """
        # Para módulos tipo page
        if module_type == "page":
            # Moodle Web Services no tiene una función directa para esto
            # Se necesitaría usar core_course_edit_module o funciones personalizadas
            # Por ahora, documentamos la limitación
            pass
        
        # Para labels, es similar
        elif module_type == "label":
            pass
        
        # NOTA IMPORTANTE: La API de Moodle tiene limitaciones significativas
        # para la edición de contenido HTML de módulos. En una implementación
        # completa, se podría necesitar:
        # 1. Un plugin personalizado de Moodle
        # 2. Acceso directo a la base de datos (no recomendado)
        # 3. Uso de la función core_course_edit_module con los parámetros correctos
        
        raise NotImplementedError(
            "La actualización directa de contenido de módulos requiere "
            "funciones de Web Service adicionales o un plugin personalizado"
        )
    
    # ==================== QUIZ OPERATIONS ====================

    async def get_quizzes_by_course(self, course_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene las actividades cuestionario (quiz) de un curso.

        Args:
            course_id: ID del curso

        Returns:
            Lista de quizzes con sus datos
        """
        result = await self._call_api(
            "mod_quiz_get_quizzes_by_courses",
            {f"courseids[0]": course_id}
        )
        return result.get("quizzes", [])

    async def get_question_categories(
        self,
        course_id: int,
        cmid: int = 0,
        include_all: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Obtiene las categorías de preguntas de un curso.

        Usa local_sectionedit_get_question_categories (plugin personalizado).

        Args:
            course_id: ID del curso
            cmid: Course Module ID de un quiz específico (0 = contexto del curso)
            include_all: Si True, retorna categorías de TODOS los contextos
                         (curso + todas las actividades quiz)

        Returns:
            Lista de categorías de preguntas
        """
        try:
            params: Dict[str, Any] = {"courseid": course_id}
            if cmid > 0:
                params["cmid"] = cmid
            if include_all:
                params["includeall"] = 1

            result = await self._call_api(
                "local_sectionedit_get_question_categories",
                params
            )
            return result.get("categories", []) if isinstance(result, dict) else result
        except MoodleAPIError as e:
            if "accessexception" in str(e.error_code or "").lower():
                raise MoodleAPIError(
                    message=(
                        "No se pudieron obtener las categorías de preguntas: falta la función "
                        "local_sectionedit_get_question_categories en tu servicio web de Moodle. "
                        "Actualiza el plugin local_sectionedit a v1.2+ y agrega la función desde: "
                        "Administración del sitio → Servidor → Servicios externos → "
                        "[tu servicio] → Funciones → Agregar."
                    ),
                    error_code=e.error_code,
                    debug_info=e.debug_info,
                )
            raise

    async def create_question_category(
        self,
        course_id: int,
        name: str,
        info: str = "",
        cmid: int = 0,
    ) -> Dict[str, Any]:
        """
        Crea una nueva categoría de preguntas.

        Usa local_sectionedit_create_question_category (plugin personalizado).

        Args:
            course_id: ID del curso
            name: Nombre de la categoría
            info: Descripción de la categoría
            cmid: Course Module ID del quiz (0 = contexto del curso)

        Returns:
            Datos de la categoría creada (incluyendo ID)
        """
        try:
            params: Dict[str, Any] = {
                "courseid": course_id,
                "name": name,
                "info": info,
            }
            if cmid > 0:
                params["cmid"] = cmid

            result = await self._call_api(
                "local_sectionedit_create_question_category",
                params
            )
            print(f"✅ Categoría '{name}' creada (id={result.get('id')})")
            return result
        except MoodleAPIError as e:
            if "accessexception" in str(e.error_code or "").lower():
                raise MoodleAPIError(
                    message=(
                        "No se pudo crear la categoría de preguntas: falta la función "
                        "local_sectionedit_create_question_category en tu servicio web de Moodle. "
                        "Actualiza el plugin local_sectionedit a v1.2+ y agrega la función."
                    ),
                    error_code=e.error_code,
                    debug_info=e.debug_info,
                )
            raise

    async def import_questions_xml(
        self,
        course_id: int,
        category_id: int,
        xml_content: str,
    ) -> Dict[str, Any]:
        """
        Importa preguntas al banco de preguntas de Moodle usando formato XML.

        Usa local_sectionedit_import_questions (plugin personalizado) que internamente
        invoca las clases qformat_xml / qformat_aiken de Moodle.
        Reemplaza a qbank_importquestions_import_questions que no existe como WS.

        Args:
            course_id: ID del curso
            category_id: ID de la categoría destino
            xml_content: Contenido XML con las preguntas (formato Moodle XML)

        Returns:
            Resultado de la importación
        """
        import base64

        # La función del plugin espera el archivo como base64
        file_content_b64 = base64.b64encode(xml_content.encode("utf-8")).decode("utf-8")

        try:
            result = await self._call_api(
                "local_sectionedit_import_questions",
                {
                    "courseid": course_id,
                    "categoryid": category_id,
                    "format": "xml",
                    "filecontent": file_content_b64,
                }
            )
            print(
                f"✅ Importación exitosa: {result.get('total_imported', '?')} "
                f"preguntas al curso {course_id}"
            )
            return result
        except MoodleAPIError as e:
            if "accessexception" in str(e.error_code or "").lower():
                raise MoodleAPIError(
                    message=(
                        "No se pudo importar las preguntas: falta la función "
                        "local_sectionedit_import_questions en tu servicio web de Moodle. "
                        "Actualiza el plugin local_sectionedit a v1.2+ y agrega la función."
                    ),
                    error_code=e.error_code,
                    debug_info=e.debug_info,
                )
            raise

    async def configure_quiz_questions(
        self,
        course_id: int,
        cmid: int,
        category_id: int,
        mode: str = "all",
        num_questions: int = 10,
        include_subcategories: bool = False,
    ) -> Dict[str, Any]:
        """
        Agrega preguntas de una categoría a un cuestionario.

        Usa local_sectionedit_configure_quiz_questions (plugin personalizado).

        Args:
            course_id: ID del curso
            cmid: Course Module ID del quiz
            category_id: ID de la categoría de preguntas
            mode: 'all' (todas) o 'random' (aleatorias)
            num_questions: Cantidad de preguntas aleatorias (solo para mode='random')
            include_subcategories: Incluir subcategorías (solo para mode='random')

        Returns:
            Resultado de la operación
        """
        try:
            params: Dict[str, Any] = {
                "courseid": course_id,
                "cmid": cmid,
                "categoryid": category_id,
                "mode": mode,
                "numquestions": num_questions,
                "includesubcategories": 1 if include_subcategories else 0,
            }

            result = await self._call_api(
                "local_sectionedit_configure_quiz_questions",
                params,
            )
            print(
                f"✅ Quiz configurado: {result.get('questions_added', 0)} preguntas "
                f"agregadas al quiz (cmid={cmid}, modo={mode})"
            )
            return result
        except MoodleAPIError as e:
            if "accessexception" in str(e.error_code or "").lower():
                raise MoodleAPIError(
                    message=(
                        "No se pudieron agregar preguntas al quiz: falta la función "
                        "local_sectionedit_configure_quiz_questions en tu servicio web de Moodle. "
                        "Actualiza el plugin local_sectionedit a v1.2.4+ y agrega la función."
                    ),
                    error_code=e.error_code,
                    debug_info=e.debug_info,
                )
            raise

    async def update_quiz_settings(
        self,
        course_id: int,
        cmid: int,
        time_limit: int = 0,
    ) -> Dict[str, Any]:
        """
        Actualiza los ajustes de un cuestionario (tiempo límite, etc.).

        Usa local_sectionedit_update_quiz_settings (plugin personalizado).

        Args:
            course_id: ID del curso
            cmid: Course Module ID del quiz
            time_limit: Tiempo límite en segundos (0 = sin límite)

        Returns:
            Resultado de la operación
        """
        try:
            result = await self._call_api(
                "local_sectionedit_update_quiz_settings",
                {
                    "courseid": course_id,
                    "cmid": cmid,
                    "timelimit": time_limit,
                },
            )
            print(
                f"✅ Quiz settings actualizados (cmid={cmid}, "
                f"timelimit={result.get('timelimit_display', time_limit)})"
            )
            return result
        except MoodleAPIError as e:
            if "accessexception" in str(e.error_code or "").lower():
                raise MoodleAPIError(
                    message=(
                        "No se pudieron actualizar los ajustes del quiz: falta la función "
                        "local_sectionedit_update_quiz_settings en tu servicio web de Moodle. "
                        "Actualiza el plugin local_sectionedit a v1.2.4+ y agrega la función."
                    ),
                    error_code=e.error_code,
                    debug_info=e.debug_info,
                )
            raise

    # ==================== USER OPERATIONS ====================
    
    async def get_site_info(self) -> Dict[str, Any]:
        """
        Obtiene información del sitio y del usuario actual (autenticado con el token).
        
        Returns:
            Información del sitio incluyendo datos del usuario
        """
        return await self._call_api("core_webservice_get_site_info")
    
    async def get_user_by_field(
        self, 
        field: str, 
        value: str
    ) -> List[Dict[str, Any]]:
        """
        Busca usuarios por un campo específico.
        
        Args:
            field: Campo de búsqueda (username, email, id, etc.)
            value: Valor a buscar
            
        Returns:
            Lista de usuarios encontrados
        """
        return await self._call_api(
            "core_user_get_users_by_field",
            {"field": field, "values[0]": value}
        )


# Instancia global del cliente (singleton pattern)
_moodle_client: Optional[MoodleClient] = None


def get_moodle_client() -> MoodleClient:
    """
    Obtiene la instancia global del cliente de Moodle.
    
    Returns:
        MoodleClient: Instancia del cliente
    """
    global _moodle_client
    if _moodle_client is None:
        _moodle_client = MoodleClient()
    return _moodle_client


async def close_moodle_client():
    """Cierra el cliente global de Moodle"""
    global _moodle_client
    if _moodle_client:
        await _moodle_client.close()
        _moodle_client = None
