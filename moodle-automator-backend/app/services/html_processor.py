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
    ExistingBlockInfo,
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

    def _collapse_wrapper(self, collapse_id: str, icon: str, label: str, content: str, block_type: str = "") -> str:
        """
        Genera el envoltorio curcollapse estándar reutilizable.

        Args:
            collapse_id: ID del div colapsable (ej. 'curs1pres1')
            icon:        Clase del ícono Font Awesome (ej. 'fa-person-chalkboard')
            label:       Texto del botón/título
            content:     HTML interior del card body
            block_type:  Tipo de bloque para marcado (presentations, reading, videos)
        """
        bt_attr = f' data-block-type="{block_type}"' if block_type else ""
        return f'''<div class="curcollapse"{bt_attr}>
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
        summary: Optional[str] = None,
    ) -> str:
        """
        Genera el HTML del bloque de presentación.
        Soporta múltiples presentaciones; cada una genera su propio iframe.

        Args:
            presentations: Lista de dicts con 'title' y 'url'.
            objective:     Objetivo de aprendizaje (opcional, se muestra al final).
            tips:          Lista de tips (opcional, se muestra antes del objetivo).
            summary:       Resumen de la presentación (opcional, se muestra antes del objetivo).
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

        summary_section = ""
        if summary:
            summary_section = f'''
      <!-- RESUMEN -->
      <div class="row pt-4 g-2">
        <div class="col-12 col-md-10 offset-md-2">
          <h4 class="mb-2">Resumen</h4>
          <p style="margin-bottom: 0; line-height: 1.7;">{summary}</p>
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

        content = iframes + summary_section + sidebar
        return self._collapse_wrapper("curs1pres1", "fa-person-chalkboard", collapse_label, content, block_type="presentations")

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
        return self._collapse_wrapper("curs1lect1", "fa-book-open-reader", "  Lectura", content, block_type="reading")

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
        return self._collapse_wrapper("curs1vid1", "fa-play", "Video", content, block_type="videos")

    # -----------------------------------------------------------------------
    # ESCANEO DE PLACEHOLDERS
    # -----------------------------------------------------------------------

    def scan_placeholders(self, html: str) -> dict:
        """
        Escanea el HTML y retorna placeholders conocidos, título, descripción,
        y si hay horario/bibliografía.

        Detecta tanto placeholders vírgenes (valor == clave conocida) como
        elementos ya reemplazados que llevan ``data-placeholder``.
        """
        soup = self._parse(html)
        found: List[PlaceholderFound] = []
        seen_keys: set = set()

        for tag in soup.find_all(["a", "iframe"]):
            attr  = "href" if tag.name == "a" else "src"
            value = tag.get(attr, "")

            # Caso 1: placeholder original sin reemplazar
            if value in KNOWN_PLACEHOLDERS:
                context = tag.get_text(strip=True) if tag.name == "a" else ""
                found.append(PlaceholderFound(
                    element_type=tag.name,
                    attribute=attr,
                    placeholder_key=value,
                    context_text=context or None,
                    current_value=value,
                ))
                seen_keys.add(value)
                continue

            # Caso 2: elemento ya reemplazado (tiene data-placeholder)
            dp_key = tag.get("data-placeholder", "")
            if dp_key and dp_key in KNOWN_PLACEHOLDERS and dp_key not in seen_keys:
                context = tag.get_text(strip=True) if tag.name == "a" else ""
                found.append(PlaceholderFound(
                    element_type=tag.name,
                    attribute=attr,
                    placeholder_key=dp_key,
                    context_text=context or None,
                    current_value=value,  # URL real actual
                ))
                seen_keys.add(dp_key)

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
            "existing_schedule":    self._extract_schedule(soup),
            "existing_bibliography": self._extract_bibliography(soup),
        }

    # -----------------------------------------------------------------------
    # EXTRACCIÓN DE DATOS EXISTENTES (horario y bibliografía)
    # -----------------------------------------------------------------------

    def _extract_schedule(self, soup: BeautifulSoup) -> Optional[dict]:
        """
        Extrae los datos actuales del horario del HTML (#cronograma).

        Retorna ``{days_columns: [...], entries: [...]}`` o ``None``.
        """
        modal = soup.find("div", id="cronograma")
        if not modal:
            return None

        table = modal.find("table")
        if not table:
            return None

        # Extraer las columnas de días del segundo <tr> del thead
        thead = table.find("thead")
        if not thead:
            return None
        header_rows = thead.find_all("tr")
        if len(header_rows) < 2:
            return None

        headers = [th.get_text(strip=True) for th in header_rows[1].find_all("th")]
        if len(headers) < 2:
            return None
        days_columns = headers[1:]  # Quitar "Asignatura"

        # Extraer las filas del tbody
        tbody = table.find("tbody")
        if not tbody:
            return None

        entries = []
        for row in tbody.find_all("tr"):
            cells = [td.get_text(strip=True) for td in row.find_all("td")]
            if not cells:
                continue
            subject_name = cells[0]
            days = {}
            for i, day in enumerate(days_columns):
                days[day] = cells[i + 1] if i + 1 < len(cells) else ""
            # Ignorar filas de template vacías
            if subject_name and any(v and v != "—" for v in days.values()):
                entries.append({"subject_name": subject_name, "days": days})

        if not entries:
            return None

        return {"days_columns": days_columns, "entries": entries}

    def _extract_bibliography(self, soup: BeautifulSoup) -> Optional[dict]:
        """
        Extrae los datos actuales de bibliografía del HTML (#biblio).

        Retorna ``{entries: [{text, url}]}`` o ``None``.
        """
        modal = soup.find("div", id="biblio")
        if not modal:
            return None

        entries = []
        for link in modal.find_all("a", href=True):
            href = link.get("href", "")
            text = link.get_text(strip=True).lstrip("•").strip()

            # Ignorar placeholders sin configurar o textos vacíos
            if href == "bibliografia" or not text or not href:
                continue
            # Ignorar links del modal mismo (botón cerrar, etc.)
            if href.startswith("#"):
                continue

            entries.append({"text": text, "url": href})

        if not entries:
            return None

        return {"entries": entries}

    # -----------------------------------------------------------------------
    # ESCANEO DE BLOQUES AVANZADOS (labels independientes)
    # -----------------------------------------------------------------------

    # Mapa de IDs de collapse → tipo de bloque (fallback para labels sin data-block-type)
    _COLLAPSE_ID_MAP = {
        "curs1pres1": "presentations",
        "curs1lect1": "reading",
        "curs1vid1":  "videos",
    }

    def scan_block_label(self, html: str) -> Optional[ExistingBlockInfo]:
        """
        Analiza el HTML de un label buscando un bloque avanzado.

        Estrategia de detección (en orden):
        1. Atributo ``data-block-type`` (labels creados con la versión actual)
        2. ID de collapse conocido (``curs1pres1``, ``curs1lect1``, ``curs1vid1``)
           para labels creados antes de que se añadiera ``data-block-type``.

        Retorna un ``ExistingBlockInfo`` si detecta un bloque, o ``None``.
        """
        soup = self._parse(html)

        # --- Estrategia 1: data-block-type ---
        wrapper = soup.find(attrs={"data-block-type": True})
        block_type: Optional[str] = None

        if wrapper:
            block_type = wrapper["data-block-type"]
        else:
            # --- Estrategia 2: fallback por IDs de collapse ---
            for collapse_id, btype in self._COLLAPSE_ID_MAP.items():
                el = soup.find(id=collapse_id)
                if el:
                    wrapper = el.find_parent("div", class_="curcollapse") or soup
                    block_type = btype
                    break

        if not wrapper or not block_type:
            return None

        # --- Extraer collapse_label del h5 del encabezado ---
        collapse_label: Optional[str] = None
        h5_el = wrapper.find("h5")
        if h5_el:
            # Obtener texto sin el ícono <i>
            raw = h5_el.get_text(strip=True)
            collapse_label = raw.strip()

        items: list = []
        summary_text: Optional[str] = None

        # Campos específicos por tipo
        presentations_list: Optional[list] = None
        presentation_objective: Optional[str] = None
        presentation_summary_val: Optional[str] = None
        videos_list: Optional[list] = None
        videos_summary_val: Optional[str] = None
        main_reading_val: Optional[dict] = None
        suggested_readings_val: Optional[list] = None
        reading_section_title: Optional[str] = None
        reading_button_text: Optional[str] = None
        reading_suggested_title: Optional[str] = None

        if block_type in ("presentations", "videos"):
            # Extraer cada iframe + su título h4
            extracted = []
            for iframe in wrapper.find_all("iframe"):
                url = iframe.get("src", "")
                # Buscar el h4 más cercano anterior (dentro del mismo row)
                row = iframe.find_parent("div", class_="row")
                title = ""
                if row:
                    h4 = row.find("h4")
                    if h4:
                        title = h4.get_text(strip=True)
                extracted.append({"title": title, "url": url})
            items = extracted

            # Resumen
            resumen_div = wrapper.find("h4", string=lambda t: t and "Resumen" in t)
            if resumen_div:
                p = resumen_div.find_next("p")
                if p:
                    summary_text = p.get_text(strip=True)

            # Objetivo de aprendizaje (solo presentaciones)
            objetivo_h5 = wrapper.find("h5", string=lambda t: t and "Objetivo" in t)
            if objetivo_h5:
                li = objetivo_h5.find_next("li")
                if li:
                    obj_text = li.get_text(strip=True)
                    if block_type == "presentations":
                        presentation_objective = obj_text
                    else:
                        summary_text = obj_text

            if block_type == "presentations":
                presentations_list = extracted
                presentation_summary_val = summary_text
            else:
                videos_list = extracted
                videos_summary_val = summary_text

        elif block_type == "reading":
            # --- Lectura principal: btn-primary ---
            main_btn = wrapper.find("a", class_=lambda c: c and "btn-primary" in c and "btn-outline" not in c)
            if main_btn:
                url = main_btn.get("href", "")
                reading_button_text = main_btn.get_text(strip=True)
                item_div = main_btn.find_parent("div", class_="list-group-item")
                title = ""
                author = ""
                if item_div:
                    inner = item_div.find("div")
                    if inner:
                        strong = inner.find("strong")
                        em = inner.find("em")
                        if strong:
                            title = strong.get_text(strip=True).lstrip("📘").strip()
                        if em:
                            author = em.get_text(strip=True)

                # Resumen de lectura
                summary_val = ""
                resumen_h4 = wrapper.find("h4", string=lambda t: t and "Resumen" in t)
                if resumen_h4:
                    p = resumen_h4.find_next("p")
                    if p:
                        summary_val = p.get_text(strip=True)
                        summary_text = summary_val

                main_reading_val = {
                    "title": title,
                    "author": author,
                    "url": url,
                    "summary": summary_val,
                }
                items.append({"title": title, "author": author, "url": url})

            # --- Título h4 de la sección (el primer h4 que no sea "Resumen") ---
            for h4 in wrapper.find_all("h4"):
                txt = h4.get_text(strip=True)
                if txt and "Resumen" not in txt:
                    reading_section_title = txt
                    break

            # --- Lecturas sugeridas: btn-outline-primary ---
            suggested = []
            for a_tag in wrapper.find_all("a", class_=lambda c: c and "btn-outline-primary" in c):
                url = a_tag.get("href", "")
                item_div = a_tag.find_parent("div", class_="list-group-item")
                title = ""
                author = ""
                if item_div:
                    inner = item_div.find("div")
                    if inner:
                        strong = inner.find("strong")
                        em = inner.find("em")
                        if strong:
                            title = strong.get_text(strip=True).lstrip("📘").strip()
                        if em:
                            author = em.get_text(strip=True)
                suggested.append({"title": title, "author": author, "url": url})
                items.append({"title": title, "author": author, "url": url})
            suggested_readings_val = suggested if suggested else None

            # --- Título de la sección de sugeridas (h5 antes del list-group de sugeridas) ---
            for h5 in wrapper.find_all("h5"):
                txt = h5.get_text(strip=True)
                if txt and txt != collapse_label and "Objetivo" not in txt:
                    reading_suggested_title = txt
                    break

        return ExistingBlockInfo(
            block_type=block_type,
            collapse_label=collapse_label,
            # Presentaciones
            presentations=presentations_list,
            presentation_objective=presentation_objective,
            presentation_summary=presentation_summary_val,
            # Lectura
            main_reading=main_reading_val,
            suggested_readings=suggested_readings_val,
            reading_section_title=reading_section_title,
            reading_button_text=reading_button_text,
            reading_suggested_title=reading_suggested_title,
            # Videos
            videos=videos_list,
            videos_summary=videos_summary_val,
            # Legacy
            items=items,
            summary_text=summary_text,
        )

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
        """
        Reemplaza múltiples placeholders en una sola pasada.

        Marca cada elemento con ``data-placeholder="<key>"`` para que
        futuros escaneos sigan encontrándolo incluso después de que el
        valor original haya sido sustituido por una URL real.
        """
        soup    = self._parse(html)
        details: List[ReplacementDetail] = []

        for tag in soup.find_all(["a", "iframe"]):
            attr  = "href" if tag.name == "a" else "src"
            value = tag.get(attr, "")

            # Caso 1: valor original sigue siendo un placeholder conocido
            if value in replacements:
                placeholder_key = value
                new_val = replacements[value]
                tag[attr] = new_val
                tag["data-placeholder"] = placeholder_key
                details.append(ReplacementDetail(
                    field=f"{tag.name}[{attr}]={placeholder_key}",
                    old_value=placeholder_key,
                    new_value=new_val,
                ))
                continue

            # Caso 2: el elemento ya fue reemplazado antes (tiene data-placeholder)
            existing_key = tag.get("data-placeholder", "")
            if existing_key and existing_key in replacements:
                new_val = replacements[existing_key]
                old_val = value
                tag[attr] = new_val
                details.append(ReplacementDetail(
                    field=f"{tag.name}[{attr}]={existing_key}",
                    old_value=old_val,
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
        presentation_summary: Optional[str] = None,
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
