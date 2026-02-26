"""
HTML Processor Service

Servicio especializado en el procesamiento y edición de contenido HTML.
Utiliza BeautifulSoup4 para parsear y modificar enlaces de forma segura.
"""

import re
from typing import List, Tuple, Optional
from urllib.parse import urlparse
from bs4 import BeautifulSoup, Tag

from app.schemas.editor import LinkFound


class HTMLProcessor:
    """
    Procesador de HTML para edición de enlaces.
    
    Esta clase encapsula toda la lógica de manipulación de HTML,
    permitiendo buscar, analizar y reemplazar enlaces de forma segura.
    """
    
    # Patrones comunes para identificar links de perfiles de docentes
    TEACHER_PROFILE_PATTERNS = [
        r'/user/view\.php\?id=\d+',
        r'/user/profile\.php\?id=\d+',
        r'profile\.php',
        r'/mod/page/view\.php.*perfil',
        r'docente|profesor|teacher|instructor',
    ]
    
    def __init__(self, parser: str = "lxml"):
        """
        Inicializa el procesador.
        
        Args:
            parser: Parser de BeautifulSoup a utilizar ('lxml', 'html.parser', etc.)
        """
        self.parser = parser
    
    def parse_html(self, html_content: str) -> BeautifulSoup:
        """
        Parsea contenido HTML.
        
        Args:
            html_content: String con contenido HTML
            
        Returns:
            Objeto BeautifulSoup parseado
        """
        return BeautifulSoup(html_content, self.parser)
    
    def find_all_links(self, html_content: str) -> List[dict]:
        """
        Encuentra todos los enlaces en el contenido HTML.
        
        Args:
            html_content: Contenido HTML a analizar
            
        Returns:
            Lista de diccionarios con información de cada enlace
        """
        soup = self.parse_html(html_content)
        links = []
        
        for link in soup.find_all('a', href=True):
            link_info = {
                'href': link['href'],
                'text': link.get_text(strip=True),
                'attributes': dict(link.attrs),
                'context': self._get_link_context(link)
            }
            links.append(link_info)
        
        return links
    
    def _get_link_context(self, link_tag: Tag, chars: int = 100) -> str:
        """
        Obtiene el contexto HTML alrededor de un enlace.
        
        Args:
            link_tag: Tag del enlace
            chars: Cantidad de caracteres de contexto
            
        Returns:
            String con el contexto HTML
        """
        parent = link_tag.parent
        if parent:
            context = str(parent)
            if len(context) > chars * 2:
                # Truncar si es muy largo
                context = context[:chars] + "..." + context[-chars:]
            return context
        return str(link_tag)
    
    def is_teacher_profile_link(self, href: str, link_text: str = "") -> bool:
        """
        Determina si un enlace es probablemente un link de perfil de docente.
        
        Args:
            href: URL del enlace
            link_text: Texto del enlace
            
        Returns:
            True si parece ser un link de perfil de docente
        """
        combined = f"{href} {link_text}".lower()
        
        for pattern in self.TEACHER_PROFILE_PATTERNS:
            if re.search(pattern, combined, re.IGNORECASE):
                return True
        
        return False
    
    def find_teacher_profile_links(self, html_content: str) -> List[dict]:
        """
        Encuentra específicamente los enlaces que parecen ser perfiles de docentes.
        
        Args:
            html_content: Contenido HTML a analizar
            
        Returns:
            Lista de enlaces identificados como perfiles de docentes
        """
        all_links = self.find_all_links(html_content)
        teacher_links = []
        
        for link in all_links:
            if self.is_teacher_profile_link(link['href'], link['text']):
                teacher_links.append(link)
        
        return teacher_links
    
    def replace_link(
        self, 
        html_content: str, 
        old_url: str, 
        new_url: str,
        exact_match: bool = True
    ) -> Tuple[str, int]:
        """
        Reemplaza un enlace específico en el contenido HTML.
        
        Args:
            html_content: Contenido HTML original
            old_url: URL a buscar y reemplazar
            new_url: Nueva URL
            exact_match: Si True, busca coincidencia exacta; si False, usa contains
            
        Returns:
            Tupla con (HTML modificado, cantidad de reemplazos)
        """
        soup = self.parse_html(html_content)
        replacements = 0
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            if exact_match:
                should_replace = href == old_url
            else:
                should_replace = old_url in href
            
            if should_replace:
                link['href'] = new_url
                replacements += 1
        
        return str(soup), replacements
    
    def replace_links_batch(
        self,
        html_content: str,
        replacements: List[Tuple[str, str]],
        exact_match: bool = True
    ) -> Tuple[str, int]:
        """
        Reemplaza múltiples enlaces en una sola pasada.
        
        Args:
            html_content: Contenido HTML original
            replacements: Lista de tuplas (old_url, new_url)
            exact_match: Si True, busca coincidencia exacta
            
        Returns:
            Tupla con (HTML modificado, cantidad total de reemplazos)
        """
        soup = self.parse_html(html_content)
        total_replacements = 0
        
        # Crear diccionario para búsqueda rápida
        replacement_map = {old: new for old, new in replacements}
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            if exact_match:
                if href in replacement_map:
                    link['href'] = replacement_map[href]
                    total_replacements += 1
            else:
                for old_url, new_url in replacements:
                    if old_url in href:
                        link['href'] = href.replace(old_url, new_url)
                        total_replacements += 1
                        break
        
        return str(soup), total_replacements
    
    def replace_teacher_profile_links(
        self,
        html_content: str,
        new_teacher_url: str,
        old_teacher_url: Optional[str] = None
    ) -> Tuple[str, int]:
        """
        Reemplaza todos los enlaces de perfil de docente encontrados.
        
        Args:
            html_content: Contenido HTML original
            new_teacher_url: Nueva URL del perfil del docente
            old_teacher_url: URL específica a reemplazar (si se omite, reemplaza todos los detectados)
            
        Returns:
            Tupla con (HTML modificado, cantidad de reemplazos)
        """
        soup = self.parse_html(html_content)
        replacements = 0
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text(strip=True)
            
            if old_teacher_url:
                # Reemplazar URL específica
                if href == old_teacher_url or old_teacher_url in href:
                    link['href'] = new_teacher_url
                    replacements += 1
            else:
                # Detectar y reemplazar automáticamente
                if self.is_teacher_profile_link(href, text):
                    link['href'] = new_teacher_url
                    replacements += 1
        
        return str(soup), replacements
    
    def sanitize_html(self, html_content: str) -> str:
        """
        Limpia y normaliza el HTML.
        
        Args:
            html_content: HTML a limpiar
            
        Returns:
            HTML limpio y normalizado
        """
        soup = self.parse_html(html_content)
        # BeautifulSoup automáticamente corrige HTML malformado
        return str(soup)
    
    def extract_text(self, html_content: str) -> str:
        """
        Extrae solo el texto de contenido HTML.
        
        Args:
            html_content: HTML del cual extraer texto
            
        Returns:
            Texto plano sin tags HTML
        """
        soup = self.parse_html(html_content)
        return soup.get_text(separator=' ', strip=True)


# Instancia singleton del procesador
_html_processor: Optional[HTMLProcessor] = None


def get_html_processor() -> HTMLProcessor:
    """
    Obtiene la instancia global del procesador HTML.
    
    Returns:
        HTMLProcessor: Instancia del procesador
    """
    global _html_processor
    if _html_processor is None:
        _html_processor = HTMLProcessor()
    return _html_processor
