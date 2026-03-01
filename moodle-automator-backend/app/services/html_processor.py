"""
HTML Processor — Service Layer

Responsabilidades:
  1. Escanear el HTML de una sección para detectar placeholders editables.
  2. Reemplazar placeholders (href / src), título, descripción, horario y bibliografía.
  3. Renderizar bloques HTML independientes (presentación, lectura, video)
     que se crean como labels separados en Moodle.
"""

from typing import List, Dict, Tuple, Optional
from bs4 import BeautifulSoup, NavigableString

# Importar los modelos Pydantic reales (evita duplicar definiciones dummy)
from app.schemas.editor import (
    PlaceholderFound,
    ReplacementDetail,
    ScheduleUpdateRequest,
    BibliographyUpdateRequest,
)

# ---------------------------------------------------------------------------
# Placeholders conocidos del template HTML del curso base.
# Clave  → texto descriptivo para el frontend.
# ---------------------------------------------------------------------------
KNOWN_PLACEHOLDERS: Dict[str, str] = {
    "video-introductorio": "Video introductorio (iframe src)",
    "unirse-clases":       "Enlace para unirse a clases (href)",
    "url-grabaciones":     "Enlace de grabaciones (href)",
    "perfil-docente":      "Perfil del docente (iframe src)",
    "silabo":              "Sílabo del curso (iframe src)",
    "pea":                 "PEA del curso (iframe src)",
    "bibliografia":        "Enlace de bibliografía (href)",
}

# URL de la imagen decorativa usada en todos los bloques de contenido
_SUPPORT_IMG = "https://intec.edu.ec/wp-content/uploads/2023/08/Letras-04.png"


# ---------------------------------------------------------------------------
# Fragmento HTML reutilizable: columna con imagen decorativa
# ---------------------------------------------------------------------------
def _img_col() -> str:
    return (
        f'<div class="col-12 col-md-2 text-center">'
        f'<img class="img-fluid" style="border-radius: 10px; max-width: 90px;" '
        f'src="{_SUPPORT_IMG}" alt="Imagen de apoyo"></div>'
    )


class HTMLProcessor:
    """Procesa y personaliza el HTML de secciones de cursos Moodle."""

    def __init__(self, parser: str = "html.parser"):
        self.parser = parser

    # -----------------------------------------------------------------------
    # Helpers privados
    # -----------------------------------------------------------------------

    def _parse(self, html: str) -> BeautifulSoup:
        return BeautifulSoup(html, self.parser)

    def _serialize(self, soup: BeautifulSoup) -> str:
        """Serializa el soup a string sin agregar wrappers html/body."""
        return soup.decode_contents()

    def _collapse_wrapper(self, collapse_id: str, icon: str, label: str, content: str) -> str:
        """
        Genera el envoltorio curcollapse estándar reutilizable.

        Args:
            collapse_id: ID del div colapsable (ej. 'curs1pres1')
            icon:        Clase del ícono Font Awesome (ej. 'fa-person-chalkboard')
            label:       Texto del botón/título
            content:     HTML interior del card body
        """
        return f'''<div class="curcollapse">
  <div class="collapsed titcur presscollapse" data-bs-toggle="collapse"
    data-bs-target="#{collapse_id}" aria-expanded="false"
    aria-controls="{collapse_id}">
    <h5><i class="fa-solid {icon} fa-bounce"></i> {label}</h5>
  </div>
  <div id="{collapse_id}" class="collapse">
    <div class="card card-body p-5">
{content}
    </div>
  </div>
</div>'''

    # -----------------------------------------------------------------------
    # RENDERIZADO DE BLOQUES AVANZADOS (labels independientes en Moodle)
    # -----------------------------------------------------------------------

    def render_presentations_block(
        self,
        presentations: list,
        objective: Optional[str] = None,
        tips: Optional[List[str]] = None,
    ) -> str:
        """
        Genera el HTML del bloque de presentación.
        Soporta múltiples presentaciones; cada una genera su propio iframe.

        Args:
            presentations: Lista de dicts con 'title' y 'url'.
            objective:     Objetivo de aprendizaje (opcional, se muestra al final).
            tips:          Lista de tips (opcional, se muestra antes del objetivo).
        """
        if not presentations:
            return ""

        # El título del botón collapse = título de la primera presentación
        collapse_label = presentations[0].get("title", "Presentación")

        # Generar un iframe por cada presentación de la lista
        iframes = ""
        for pres in presentations:
            title = pres.get("title", "")
            url   = pres.get("url", "")
            iframes += f'''
      <div class="row pb-4 justify-content-center">
        <div class="col-12 col-md-8 text-center">
          <h4 class="mb-3">{title}</h4>
          <div style="position: relative; width: 100%; padding-top: 56.25%; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(63,69,81,0.16);">
            <iframe
              style="position: absolute; inset: 0; width: 100%; height: 100%; border: 0;"
              src="{url}"
              allowfullscreen="allowfullscreen" loading="lazy">
            </iframe></div>
        </div>
      </div>'''

        sidebar = ""
        if tips or objective:
            inner = ""
            if tips:
                items = "".join(f"\n            <li>{t}</li>" for t in tips)
                inner += f'\n          <h4 class="mb-2">Tips Matemáticos</h4>\n          <ul>{items}\n          </ul>\n          <div> </div>'
            if objective:
                inner += f'\n          <h5>Objetivo de aprendizaje</h5>\n          <ul>\n            <li>{objective}</li>\n          </ul>'
            sidebar = f'''
      <!-- APOYO VISUAL + OBJETIVO -->
      <div class="row pt-4 align-items-center g-2">
        {_img_col()}
        <div class="col-12 col-md-10">{inner}
        </div>
      </div>'''

        content = iframes + sidebar
        return self._collapse_wrapper("curs1pres1", "fa-person-chalkboard", collapse_label, content)

    def render_main_reading_block(
        self,
        main_reading: dict,
        suggested_readings: Optional[List[dict]] = None,
        collapse_label: str = "Lectura",
        reading_section_title: str = "Lectura principal",
        main_button_text: str = "Ver lectura",
        suggested_title: str = "Lecturas sugeridas",
    ) -> str:
        """
        Genera el HTML del bloque de lectura.

        Args:
            main_reading:          Dict con 'title', 'author', 'url', 'summary'.
            suggested_readings:    Lista de dicts con 'title', 'author', 'url'.
            collapse_label:        Texto del botón collapse (ej. "Lectura", "Guia de apoyo").
            reading_section_title: Título h4 de la sección principal (ej. "Lectura principal").
            main_button_text:      Texto del botón principal (ej. "Ver lectura", "Ver Guia de apoyo").
            suggested_title:       Título del bloque de sugeridas (ej. "Lecturas sugeridas",
                                   "Libro de apoyo para mejorar el conocimiento").
        """
        if not main_reading:
            return ""

        title   = main_reading.get("title", "")
        author  = main_reading.get("author", "")
        url     = main_reading.get("url", "")
        summary = main_reading.get("summary", "")

        main_section = f'''\
      <!-- LECTURA PRINCIPAL -->
      <div class="row pb-4">
        <div class="col-12">
          <h4>{reading_section_title}</h4>
          <div class="list-group mt-3">
            <div class="list-group-item d-flex justify-content-between align-items-center">
              <div><strong>📘 {title}</strong> <br><em> {author}</em></div>
              <a class="btn btn-primary btn-sm"
                  href="{url}"
                  target="_blank" rel="noopener noreferrer"> {main_button_text} </a>
            </div>
          </div>
        </div>
      </div>'''

        summary_section = ""
        if summary:
            summary_section = f'''
      <!-- RESUMEN + IMAGEN -->
      <div class="row pt-4 align-items-center g-2">
        {_img_col()}
        <div class="col-12 col-md-10">
          <h4 class="mb-2">Resumen</h4>
          <p style="margin-bottom: 0; line-height: 1.7;">{summary}</p>
        </div>
      </div>'''

        suggested_section = ""
        if suggested_readings:
            items = ""
            for r in suggested_readings:
                items += f'''
            <div class="list-group-item d-flex justify-content-between align-items-center">
              <div><strong>📘 {r.get("title","")}</strong><br><em>{r.get("author","")}</em></div>
              <a class="btn btn-outline-primary btn-sm"
                href="{r.get("url","")}"
                target="_blank" rel="noopener noreferrer"> Ver lectura </a>
            </div>'''
            suggested_section = f'''
      <!-- LECTURAS SUGERIDAS -->
      <div class="row pt-4">
        <div class="col-12">
          <h5>{suggested_title}</h5>
          <div class="list-group mt-3">{items}
          </div>
        </div>
      </div>'''

        content = main_section + summary_section + suggested_section
        return self._collapse_wrapper("curs1lect1", "fa-book-open-reader", "  Lectura", content)

    def render_videos_block(
        self,
        videos: list,
        videos_summary: Optional[str] = None,
    ) -> str:
        """
        Genera el HTML del bloque de video.

        Args:
            videos:        Lista de dicts con 'title' y 'url'.
            videos_summary: Texto resumen de los videos (opcional).
        """
        if not videos:
            return ""

        video_items = ""
        for v in videos:
            t = v.get("title", "")
            u = v.get("url", "")
            video_items += f'''
      <!-- VIDEO -->
      <div class="row justify-content-center pb-4">
        <div class="col-12 col-md-8 text-center">
          <h4 class="mb-3">{t}</h4>
          <div style="position: relative; width: 100%; padding-top: 56.25%; border-radius: 12px; overflow: hidden; box-shadow: 0 6px 18px rgba(0,0,0,.15);">
            <iframe
              style="position: absolute; inset: 0; width: 100%; height: 100%; border: 0;"
              title="{t} - Video"
              src="{u}"
              allow="autoplay; fullscreen; clipboard-write"
              allowfullscreen="allowfullscreen" loading="lazy">
            </iframe></div>
        </div>
      </div>'''

        summary_section = ""
        if videos_summary:
            summary_section = f'''
      <!-- RESUMEN -->
      <div class="row pt-4 align-items-center g-2">
        {_img_col()}
        <div class="col-12 col-md-10">
          <h4 class="mb-2">Resumen</h4>
          <p>{videos_summary}</p>
        </div>
      </div>'''

        content = video_items + summary_section
        return self._collapse_wrapper("curs1vid1", "fa-play", "Video", content)

    # -----------------------------------------------------------------------
    # ESCANEO DE PLACEHOLDERS
    # -----------------------------------------------------------------------

    def scan_placeholders(self, html: str) -> dict:
        """
        Escanea el HTML y retorna placeholders conocidos, título, descripción,
        y si hay horario/bibliografía.
        """
        soup = self._parse(html)
        found: List[PlaceholderFound] = []

        for tag in soup.find_all(["a", "iframe"]):
            attr  = "href" if tag.name == "a" else "src"
            value = tag.get(attr, "")
            if value in KNOWN_PLACEHOLDERS:
                context = tag.get_text(strip=True) if tag.name == "a" else ""
                found.append(PlaceholderFound(
                    element_type=tag.name,
                    attribute=attr,
                    placeholder_key=value,
                    context_text=context or None,
                ))

        title_tag    = soup.select_one(".texto h1") or soup.find("h1")
        course_title = title_tag.get_text(strip=True) if title_tag else None

        course_desc = None
        if title_tag:
            next_p = title_tag.find_next_sibling("p")
            if next_p:
                course_desc = next_p.get_text(strip=True)

        return {
            "placeholders":      found,
            "total_placeholders": len(found),
            "course_title":      course_title,
            "course_description": course_desc,
            "schedule_found":    soup.find("div", id="cronograma") is not None,
            "bibliography_found": soup.find("div", id="biblio") is not None,
        }

    # -----------------------------------------------------------------------
    # REEMPLAZO DE PLACEHOLDERS
    # -----------------------------------------------------------------------

    def replace_placeholder(
        self, html: str, placeholder: str, new_value: str
    ) -> Tuple[str, List[ReplacementDetail]]:
        """Reemplaza un único placeholder en href o src."""
        return self.replace_placeholders_batch(html, {placeholder: new_value})

    def replace_placeholders_batch(
        self, html: str, replacements: Dict[str, str]
    ) -> Tuple[str, List[ReplacementDetail]]:
        """Reemplaza múltiples placeholders en una sola pasada."""
        soup    = self._parse(html)
        details: List[ReplacementDetail] = []

        for tag in soup.find_all(["a", "iframe"]):
            attr  = "href" if tag.name == "a" else "src"
            value = tag.get(attr, "")
            if value in replacements:
                new_val    = replacements[value]
                tag[attr]  = new_val
                details.append(ReplacementDetail(
                    field=f"{tag.name}[{attr}]={value}",
                    old_value=value,
                    new_value=new_val,
                ))

        return self._serialize(soup), details

    # -----------------------------------------------------------------------
    # EDICIÓN DE TEXTO: TÍTULO Y DESCRIPCIÓN
    # -----------------------------------------------------------------------

    def replace_course_title(
        self, html: str, new_title: str
    ) -> Tuple[str, List[ReplacementDetail]]:
        """Reemplaza el contenido del <h1> del curso."""
        soup    = self._parse(html)
        details: List[ReplacementDetail] = []

        h1 = soup.select_one(".texto h1") or soup.find("h1")
        if h1:
            details.append(ReplacementDetail(
                field="course_title",
                old_value=h1.get_text(strip=True),
                new_value=new_title,
            ))
            h1.string = new_title

        return self._serialize(soup), details

    def replace_course_description(
        self, html: str, new_desc: str
    ) -> Tuple[str, List[ReplacementDetail]]:
        """Reemplaza la descripción (<p> que sigue al <h1>)."""
        soup    = self._parse(html)
        details: List[ReplacementDetail] = []

        h1 = soup.select_one(".texto h1") or soup.find("h1")
        if h1:
            p = h1.find_next_sibling("p")
            if p:
                details.append(ReplacementDetail(
                    field="course_description",
                    old_value=p.get_text(strip=True),
                    new_value=new_desc,
                ))
                p.string = new_desc

        return self._serialize(soup), details

    # -----------------------------------------------------------------------
    # HORARIO
    # -----------------------------------------------------------------------

    def replace_schedule(
        self, html: str, schedule: ScheduleUpdateRequest
    ) -> Tuple[str, List[ReplacementDetail]]:
        """
        Reconstruye el <tbody> de la tabla de horario dentro de #cronograma
        y actualiza las cabeceras de días.
        """
        soup    = self._parse(html)
        details: List[ReplacementDetail] = []

        modal = soup.find("div", id="cronograma")
        if not modal:
            return self._serialize(soup), details

        table = modal.find("table")
        if not table:
            return self._serialize(soup), details

        # Actualizar cabecera de días
        thead = table.find("thead")
        if thead:
            header_rows = thead.find_all("tr")
            if len(header_rows) >= 2:
                day_row  = header_rows[1]
                new_days = schedule.days_columns

                # Actualizar colspan del título
                title_th = header_rows[0].find("th")
                if title_th:
                    title_th["colspan"] = str(1 + len(new_days))

                # Reconstruir fila de días
                day_row.clear()
                asig_th        = soup.new_tag("th", style="border: 2px solid #c7c6c6;")
                asig_th.string = "Asignatura"
                day_row.append(asig_th)
                for day_name in new_days:
                    th        = soup.new_tag("th", style="border: 2px solid #c7c6c6;")
                    th.string = day_name
                    day_row.append(th)

        # Reconstruir tbody
        tbody = table.find("tbody") or soup.new_tag("tbody")
        if not table.find("tbody"):
            table.append(tbody)

        old_text = tbody.get_text(strip=True)
        tbody.clear()

        for entry in schedule.entries:
            tr      = soup.new_tag("tr")
            td_subj = soup.new_tag(
                "td",
                **{"class": "fw-bold fs-6",
                   "style": "border: 2px solid #c7c6c6; background: #ffffff; color: #931913;"},
            )
            td_subj.string = entry.subject_name
            tr.append(td_subj)
            for day in schedule.days_columns:
                td        = soup.new_tag("td", **{"class": "fw-semibold", "style": "border: 2px solid #c7c6c6;"})
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

    # -----------------------------------------------------------------------
    # BIBLIOGRAFÍA
    # -----------------------------------------------------------------------

    def replace_bibliography(
        self, html: str, bibliography: BibliographyUpdateRequest
    ) -> Tuple[str, List[ReplacementDetail]]:
        """Reconstruye la lista <ul> del modal #biblio."""
        soup    = self._parse(html)
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
            a  = soup.new_tag(
                "a", href=entry.url, target="_blank",
                rel="noopener noreferrer", **{"class": "text-decoration-none"},
            )
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

    # -----------------------------------------------------------------------
    # ALL-IN-ONE: personalización del summary de sección
    # (los bloques avanzados se crean fuera como labels independientes)
    # -----------------------------------------------------------------------

    def customize_html(
        self,
        html: str,
        placeholders: Optional[Dict[str, str]] = None,
        course_title: Optional[str] = None,
        course_description: Optional[str] = None,
        schedule: Optional[ScheduleUpdateRequest] = None,
        bibliography: Optional[BibliographyUpdateRequest] = None,
        # Parámetros de bloques avanzados — ignorados aquí, se procesan en
        # cloner_service.py como labels separados en Moodle.
        presentations: Optional[list] = None,
        presentation_objective: Optional[str] = None,
        main_reading: Optional[dict] = None,
        suggested_readings: Optional[list] = None,
        videos: Optional[list] = None,
        videos_summary: Optional[str] = None,
    ) -> Tuple[str, List[ReplacementDetail]]:
        """
        Aplica todas las personalizaciones del summary en una sola pasada.
        Retorna (html_final, lista_de_detalles).

        Nota: presentations, main_reading y videos se ignoran aquí;
        se renderizan y crean como labels independientes en cloner_service.
        """
        all_details: List[ReplacementDetail] = []

        if placeholders:
            html, details = self.replace_placeholders_batch(html, placeholders)
            all_details.extend(details)

        if course_title:
            html, details = self.replace_course_title(html, course_title)
            all_details.extend(details)

        if course_description:
            html, details = self.replace_course_description(html, course_description)
            all_details.extend(details)

        if schedule:
            html, details = self.replace_schedule(html, schedule)
            all_details.extend(details)

        if bibliography:
            html, details = self.replace_bibliography(html, bibliography)
            all_details.extend(details)

        return html, all_details


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------
_html_processor: Optional[HTMLProcessor] = None


def get_html_processor() -> HTMLProcessor:
    global _html_processor
    if _html_processor is None:
        _html_processor = HTMLProcessor()
    return _html_processor
