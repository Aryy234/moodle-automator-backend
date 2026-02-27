"""
HTML Processor Service

Servicio especializado en el procesamiento y edición de contenido HTML
del curso base de Moodle. Maneja:
- Reemplazo de placeholders en href y src (links, iframes)
- Edición de texto (título, descripción del curso)
- Reconstrucción del horario (tabla HTML)
- Reconstrucción de la bibliografía (lista HTML)

Utiliza BeautifulSoup4 para parsear y modificar de forma segura.
"""

import re
from typing import List, Tuple, Optional, Dict
from bs4 import BeautifulSoup, Tag

from app.schemas.editor import (
    PlaceholderFound,
    ScheduleUpdateRequest,
    BibliographyUpdateRequest,
    ReplacementDetail,
)


# Placeholders conocidos del template de Moodle
KNOWN_PLACEHOLDERS: Dict[str, str] = {
    "video-introductorio": "Video introductorio (iframe src)",
    "unirse-clases": "Enlace de clases (href)",
    "url-grabaciones": "Grabaciones (href)",
    "perfil-docente": "Perfil del docente (iframe src)",
    "silabo": "Sílabo (iframe src)",
    "pea": "PEA (iframe src)",
    "bibliografia": "Bibliografía (href)",
}


class HTMLProcessor:
    """
    Procesador de HTML para el template del curso base de Moodle.
    """

    def __init__(self, parser: str = "html.parser"):
        self.parser = parser

    # ------------------------------------------------------------------
    # UTILIDADES
    # ------------------------------------------------------------------

    def parse(self, html: str) -> BeautifulSoup:
        return BeautifulSoup(html, self.parser)

    def _serialize(self, soup: BeautifulSoup) -> str:
        """Serializa el soup sin agregar <html><body> wrappers."""
        # html.parser no agrega wrappers, pero por seguridad:
        if soup.body:
            # Si hay un body wrapper, extraer solo su contenido
            return "".join(str(child) for child in soup.body.children)
        return str(soup)

    # ------------------------------------------------------------------
    # ESCANEO DE PLACEHOLDERS
    # ------------------------------------------------------------------

    def scan_placeholders(self, html: str) -> dict:
        """
        Escanea el HTML y retorna todos los placeholders conocidos,
        el título del curso, descripción, si hay horario y bibliografía.
        """
        soup = self.parse(html)
        found: List[PlaceholderFound] = []

        # Buscar en <a href="..."> y <iframe src="...">
        for tag in soup.find_all(["a", "iframe"]):
            attr = "href" if tag.name == "a" else "src"
            value = tag.get(attr, "")
            if value in KNOWN_PLACEHOLDERS:
                context = tag.get_text(strip=True) if tag.name == "a" else ""
                found.append(PlaceholderFound(
                    element_type=tag.name,
                    attribute=attr,
                    placeholder_key=value,
                    context_text=context or None,
                ))

        # Título del curso (<h1> dentro de .texto)
        title_tag = soup.select_one(".texto h1") or soup.find("h1")
        course_title = title_tag.get_text(strip=True) if title_tag else None

        # Descripción (<p> debajo de ese <h1>)
        course_desc = None
        if title_tag:
            next_p = title_tag.find_next_sibling("p")
            if next_p:
                course_desc = next_p.get_text(strip=True)

        # Horario
        schedule_found = soup.find("div", id="cronograma") is not None

        # Bibliografía
        bib_found = soup.find("div", id="biblio") is not None

        return {
            "placeholders": found,
            "total_placeholders": len(found),
            "course_title": course_title,
            "course_description": course_desc,
            "schedule_found": schedule_found,
            "bibliography_found": bib_found,
        }

    # ------------------------------------------------------------------
    # REEMPLAZO DE PLACEHOLDERS (href / src)
    # ------------------------------------------------------------------

    def replace_placeholder(
        self, html: str, placeholder: str, new_value: str
    ) -> Tuple[str, List[ReplacementDetail]]:
        """
        Reemplaza un placeholder en href o src por un nuevo valor.
        Retorna (html_modificado, lista_de_detalles).
        """
        soup = self.parse(html)
        details: List[ReplacementDetail] = []

        for tag in soup.find_all(["a", "iframe"]):
            attr = "href" if tag.name == "a" else "src"
            if tag.get(attr) == placeholder:
                tag[attr] = new_value
                details.append(ReplacementDetail(
                    field=f"{tag.name}[{attr}]={placeholder}",
                    old_value=placeholder,
                    new_value=new_value,
                ))

        return self._serialize(soup), details

    def replace_placeholders_batch(
        self, html: str, replacements: Dict[str, str]
    ) -> Tuple[str, List[ReplacementDetail]]:
        """
        Reemplaza múltiples placeholders en una sola pasada.
        replacements: {placeholder: new_value}
        """
        soup = self.parse(html)
        details: List[ReplacementDetail] = []

        for tag in soup.find_all(["a", "iframe"]):
            attr = "href" if tag.name == "a" else "src"
            value = tag.get(attr, "")
            if value in replacements:
                new_val = replacements[value]
                tag[attr] = new_val
                details.append(ReplacementDetail(
                    field=f"{tag.name}[{attr}]={value}",
                    old_value=value,
                    new_value=new_val,
                ))

        return self._serialize(soup), details

    # ------------------------------------------------------------------
    # EDICIÓN DE TEXTO: TÍTULO Y DESCRIPCIÓN
    # ------------------------------------------------------------------

    def replace_course_title(
        self, html: str, new_title: str
    ) -> Tuple[str, List[ReplacementDetail]]:
        """Reemplaza el contenido del <h1> del curso."""
        soup = self.parse(html)
        details: List[ReplacementDetail] = []

        h1 = soup.select_one(".texto h1") or soup.find("h1")
        if h1:
            old = h1.get_text(strip=True)
            h1.string = new_title
            details.append(ReplacementDetail(
                field="course_title",
                old_value=old,
                new_value=new_title,
            ))

        return self._serialize(soup), details

    def replace_course_description(
        self, html: str, new_desc: str
    ) -> Tuple[str, List[ReplacementDetail]]:
        """Reemplaza la descripción (<p> que sigue al <h1>)."""
        soup = self.parse(html)
        details: List[ReplacementDetail] = []

        h1 = soup.select_one(".texto h1") or soup.find("h1")
        if h1:
            p = h1.find_next_sibling("p")
            if p:
                old = p.get_text(strip=True)
                p.string = new_desc
                details.append(ReplacementDetail(
                    field="course_description",
                    old_value=old,
                    new_value=new_desc,
                ))

        return self._serialize(soup), details

    # ------------------------------------------------------------------
    # HORARIO
    # ------------------------------------------------------------------

    def replace_schedule(
        self, html: str, schedule: ScheduleUpdateRequest
    ) -> Tuple[str, List[ReplacementDetail]]:
        """
        Reconstruye el <tbody> de la tabla de horario dentro del
        modal #cronograma, y actualiza las cabeceras de días.
        """
        soup = self.parse(html)
        details: List[ReplacementDetail] = []

        modal = soup.find("div", id="cronograma")
        if not modal:
            return self._serialize(soup), details

        table = modal.find("table")
        if not table:
            return self._serialize(soup), details

        # --- Actualizar cabecera de días ---
        thead = table.find("thead")
        if thead:
            header_rows = thead.find_all("tr")
            # La segunda fila del thead contiene los días
            if len(header_rows) >= 2:
                day_row = header_rows[1]
                ths = day_row.find_all("th")
                # El primer th es "Asignatura", los demás son días
                new_days = schedule.days_columns
                # Actualizar colspan del título
                title_row = header_rows[0]
                title_th = title_row.find("th")
                if title_th:
                    title_th["colspan"] = str(1 + len(new_days))

                # Reconstruir fila de cabecera
                day_row.clear()
                # Asignatura
                asig_th = soup.new_tag("th", style="border: 2px solid #c7c6c6;")
                asig_th.string = "Asignatura"
                day_row.append(asig_th)
                for day_name in new_days:
                    th = soup.new_tag("th", style="border: 2px solid #c7c6c6;")
                    th.string = day_name
                    day_row.append(th)

        # --- Reconstruir tbody ---
        tbody = table.find("tbody")
        if not tbody:
            tbody = soup.new_tag("tbody")
            table.append(tbody)

        old_text = tbody.get_text(strip=True)
        tbody.clear()

        for entry in schedule.entries:
            tr = soup.new_tag("tr")

            # Celda asignatura
            td_subj = soup.new_tag(
                "td",
                **{
                    "class": "fw-bold fs-6",
                    "style": "border: 2px solid #c7c6c6; background: #ffffff; color: #931913;",
                },
            )
            td_subj.string = entry.subject_name
            tr.append(td_subj)

            # Celdas de horarios por día
            for day in schedule.days_columns:
                td = soup.new_tag(
                    "td",
                    **{
                        "class": "fw-semibold",
                        "style": "border: 2px solid #c7c6c6;",
                    },
                )
                td.string = entry.days.get(day, "—")
                tr.append(td)

            tbody.append(tr)

        new_text = tbody.get_text(strip=True)
        details.append(ReplacementDetail(
            field="schedule",
            old_value=old_text[:100] + ("..." if len(old_text) > 100 else ""),
            new_value=new_text[:100] + ("..." if len(new_text) > 100 else ""),
        ))

        return self._serialize(soup), details

    # ------------------------------------------------------------------
    # BIBLIOGRAFÍA
    # ------------------------------------------------------------------

    def replace_bibliography(
        self, html: str, bibliography: BibliographyUpdateRequest
    ) -> Tuple[str, List[ReplacementDetail]]:
        """
        Reconstruye la lista <ul> del modal #biblio con las nuevas entradas.
        """
        soup = self.parse(html)
        details: List[ReplacementDetail] = []

        modal = soup.find("div", id="biblio")
        if not modal:
            return self._serialize(soup), details

        ul = modal.find("ul")
        if not ul:
            return self._serialize(soup), details

        old_text = ul.get_text(strip=True)
        ul.clear()

        for entry in bibliography.entries:
            li = soup.new_tag("li", **{"class": "list-group-item"})
            a = soup.new_tag(
                "a",
                href=entry.url,
                target="_blank",
                rel="noopener noreferrer",
                **{"class": "text-decoration-none"},
            )
            # Usar NavigableString para el texto
            from bs4 import NavigableString
            a.append(NavigableString(f" • {entry.text} "))
            li.append(a)
            ul.append(li)

        new_text = ul.get_text(strip=True)
        details.append(ReplacementDetail(
            field="bibliography",
            old_value=old_text[:100] + ("..." if len(old_text) > 100 else ""),
            new_value=new_text[:100] + ("..." if len(new_text) > 100 else ""),
        ))

        return self._serialize(soup), details

    # ------------------------------------------------------------------
    # MÉTODO ALL-IN-ONE
    # ------------------------------------------------------------------

    def customize_html(
        self,
        html: str,
        placeholders: Optional[Dict[str, str]] = None,
        course_title: Optional[str] = None,
        course_description: Optional[str] = None,
        schedule: Optional[ScheduleUpdateRequest] = None,
        bibliography: Optional[BibliographyUpdateRequest] = None,
    ) -> Tuple[str, List[ReplacementDetail]]:
        """
        Aplica todas las personalizaciones sobre el HTML en una sola pasada.
        Retorna (html_final, lista_de_detalles).
        """
        all_details: List[ReplacementDetail] = []

        # 1. Placeholders (links / iframes)
        if placeholders:
            html, details = self.replace_placeholders_batch(html, placeholders)
            all_details.extend(details)

        # 2. Título
        if course_title:
            html, details = self.replace_course_title(html, course_title)
            all_details.extend(details)

        # 3. Descripción
        if course_description:
            html, details = self.replace_course_description(html, course_description)
            all_details.extend(details)

        # 4. Horario
        if schedule:
            html, details = self.replace_schedule(html, schedule)
            all_details.extend(details)

        # 5. Bibliografía
        if bibliography:
            html, details = self.replace_bibliography(html, bibliography)
            all_details.extend(details)

        return html, all_details


# Instancia singleton
_html_processor: Optional[HTMLProcessor] = None


def get_html_processor() -> HTMLProcessor:
    global _html_processor
    if _html_processor is None:
        _html_processor = HTMLProcessor()
    return _html_processor
