# Solicitudes Backend para el Frontend

> Estas son las funcionalidades que el frontend necesita del backend para pre-llenar el formulario de personalización y para actualizar metadatos del curso.

---

## 1. Endpoint: `PUT /api/v1/courses/{course_id}`

### Problema

El frontend necesita actualizar el **Número ID** (`idnumber`) del curso en Moodle. Actualmente solo existe `GET /courses/{id}` y no hay método para modificar campos del curso.

El `idnumber` es un **metadato del curso** (no es HTML), por lo que no se puede enviar en `/editor/customize`.

### Endpoint esperado

```
PUT /api/v1/courses/{course_id}
Content-Type: application/json

{
  "idnumber": "MAT-2026-A"
}
```

### Response esperada

```json
{
  "success": true,
  "course_id": 138
}
```

### Implementación sugerida

Internamente debe llamar a `core_course_update_courses` de Moodle:

```python
# app/api/v1/courses.py
from pydantic import BaseModel

class UpdateCourseRequest(BaseModel):
    idnumber: str | None = None
    fullname: str | None = None
    shortname: str | None = None

@router.put("/{course_id}")
async def update_course(course_id: int, data: UpdateCourseRequest):
    """Actualiza campos del curso en Moodle via core_course_update_courses."""
    update_fields = {k: v for k, v in data.dict().items() if v is not None}
    if not update_fields:
        raise HTTPException(400, "No hay campos para actualizar")
    
    await moodle_client.call("core_course_update_courses", {
        "courses": [{"id": course_id, **update_fields}]
    })
    return {"success": True, "course_id": course_id}
```

### Permisos Moodle requeridos

El token ya tiene estos permisos (según `contexto.md`):
- `moodle/course:update`
- `moodle/course:changeidnumber`
- `moodle/course:changefullname`
- `moodle/course:changeshortname`

### Frontend

El frontend ya está preparado:
- `api/index.js`: `updateCourse(courseId, data)` → `PUT /courses/{courseId}`
- `useCourseStore.js`: `tryUpdateIdnumber()` lo llama con fallo silencioso (no bloquea el guardado)
- Cuando el endpoint exista, funcionará automáticamente

---

## 2. Campo `current_value` en placeholders del scan ✅ YA IMPLEMENTADO

> Este cambio ya fue realizado. Se documenta para referencia.

Cada placeholder en el scan ahora incluye `current_value` con el valor literal del `src`/`href`.

El frontend lo usa para:
- Pre-llenar inputs con URLs ya configuradas
- Mostrar badge "Configurado" (verde) / "Pendiente" (naranja)

---

## 3. Datos del horario existente en el scan: `existing_schedule`

### Problema

Cuando `schedule_found === true`, el frontend muestra el editor de horario pero **vacío**, porque el scan no devuelve los datos actuales de la tabla de horario. Si el usuario ya configuró un horario previamente, no puede verlo ni editarlo.

### Respuesta actual del scan

```json
{
  "schedule_found": true
}
```

### Respuesta esperada (agregar `existing_schedule`)

```json
{
  "schedule_found": true,
  "existing_schedule": {
    "days_columns": ["Lunes", "Martes", "Miércoles"],
    "entries": [
      {
        "subject_name": "Estadística Aplicada",
        "days": {
          "Lunes": "18h30 - 19h30",
          "Martes": "18h30 - 19h30",
          "Miércoles": "18h30 - 19h30"
        }
      }
    ]
  }
}
```

Si el horario está vacío o es solo el template base, `existing_schedule` puede ser `null`.

### Cómo extraerlo con BeautifulSoup

El HTML del modal `#cronograma` tiene esta estructura:

```html
<table aria-label="Horario">
  <thead>
    <tr>...</tr>  <!-- Título "Horario" con colspan -->
    <tr>          <!-- Cabecera de días -->
      <th>Asignatura</th>
      <th>Lunes</th>
      <th>Martes</th>
      <th>Miércoles</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Estadística Aplicada</td>   <!-- subject_name -->
      <td>18h30 - 19h30</td>          <!-- Lunes -->
      <td>18h30 - 19h30</td>          <!-- Martes -->
      <td>18h30 - 19h30</td>          <!-- Miércoles -->
    </tr>
  </tbody>
</table>
```

Pseudocódigo de extracción:

```python
def extract_schedule(soup):
    table = soup.select_one('#cronograma table[aria-label="Horario"]')
    if not table:
        return None
    
    # Extraer columnas de días del segundo <tr> del thead
    header_rows = table.select('thead tr')
    if len(header_rows) < 2:
        return None
    
    headers = [th.get_text(strip=True) for th in header_rows[1].select('th')]
    # headers = ["Asignatura", "Lunes", "Martes", "Miércoles"]
    days_columns = headers[1:]  # Quitar "Asignatura"
    
    entries = []
    for row in table.select('tbody tr'):
        cells = [td.get_text(strip=True) for td in row.select('td')]
        if not cells:
            continue
        subject_name = cells[0]
        days = {}
        for i, day in enumerate(days_columns):
            days[day] = cells[i + 1] if i + 1 < len(cells) else ""
        entries.append({"subject_name": subject_name, "days": days})
    
    if not entries:
        return None
    
    return {"days_columns": days_columns, "entries": entries}
```

### Schema Pydantic

```python
class ScheduleEntry(BaseModel):
    subject_name: str
    days: dict[str, str]

class ExistingSchedule(BaseModel):
    days_columns: list[str]
    entries: list[ScheduleEntry]

# En PlaceholderScanResponse agregar:
class PlaceholderScanResponse(BaseModel):
    # ... campos existentes ...
    existing_schedule: ExistingSchedule | None = None
```

### Uso en el frontend

El frontend ya tiene `scheduleDaysInput` y `scheduleEntries` como refs locales. Se pre-llenarán así:

```js
if (scanData.existing_schedule) {
  scheduleDaysInput.value = scanData.existing_schedule.days_columns.join(', ')
  scheduleEntries.value = scanData.existing_schedule.entries
}
```

---

## 4. Datos de bibliografía existente en el scan: `existing_bibliography`

### Problema

Cuando `bibliography_found === true`, el frontend muestra el editor de bibliografía pero **vacío**. Si ya se guardaron referencias previamente, el usuario no las ve.

### Respuesta actual del scan

```json
{
  "bibliography_found": true
}
```

### Respuesta esperada (agregar `existing_bibliography`)

```json
{
  "bibliography_found": true,
  "existing_bibliography": {
    "entries": [
      {
        "text": "Clean Code - Robert C. Martin",
        "url": "https://biblioteca.edu.ec/cleancode"
      },
      {
        "text": "Design Patterns - Gang of Four",
        "url": "https://biblioteca.edu.ec/gof"
      }
    ]
  }
}
```

Si la bibliografía está vacía o no tiene entradas reales, `existing_bibliography` puede ser `null`.

### Cómo extraerlo con BeautifulSoup

El HTML del modal `#biblio` tiene esta estructura (después de personalizarse):

```html
<div id="biblio">
  ...
  <div class="modal-body">
    <ul class="list-unstyled">
      <li class="mb-2">
        <a href="https://biblioteca.edu.ec/cleancode" target="_blank">
          Clean Code - Robert C. Martin
        </a>
      </li>
    </ul>
  </div>
  ...
</div>
```

Pseudocódigo de extracción:

```python
def extract_bibliography(soup):
    biblio_modal = soup.select_one('#biblio .modal-body')
    if not biblio_modal:
        return None
    
    entries = []
    for link in biblio_modal.select('a[href]'):
        href = link.get('href', '')
        text = link.get_text(strip=True)
        
        # Ignorar si es un placeholder sin configurar
        if href == 'bibliografia' or not text:
            continue
        
        entries.append({"text": text, "url": href})
    
    if not entries:
        return None
    
    return {"entries": entries}
```

### Schema Pydantic

```python
class BibliographyEntry(BaseModel):
    text: str
    url: str

class ExistingBibliography(BaseModel):
    entries: list[BibliographyEntry]

# En PlaceholderScanResponse agregar:
class PlaceholderScanResponse(BaseModel):
    # ... campos existentes ...
    existing_bibliography: ExistingBibliography | None = None
```

### Uso en el frontend

El frontend ya tiene `bibliographyEntries` como ref local. Se pre-llenará así:

```js
if (scanData.existing_bibliography?.entries?.length > 0) {
  bibliographyEntries.value = scanData.existing_bibliography.entries
}
```

---

## Resumen de cambios requeridos

| # | Cambio | Prioridad | Complejidad |
|---|--------|-----------|-------------|
| 1 | `PUT /courses/{id}` — actualizar idnumber | Media | Baja (~10 líneas) |
| 2 | `current_value` en placeholders | ✅ Hecho | — |
| 3 | `existing_schedule` en scan | Alta | Media (~30 líneas) |
| 4 | `existing_bibliography` en scan | Alta | Baja (~15 líneas) |

Los cambios 3 y 4 son los más importantes para la experiencia de usuario: sin ellos, cada vez que se abre el formulario de un curso ya configurado, el horario y bibliografía aparecen vacíos y el usuario pierde el contexto de lo que ya había guardado.
placeholder = {
    "element_type": element.name,
    "attribute": attr,
    "placeholder_key": key,
    "context_text": element.get_text(strip=True) or None,
    "current_value": element.get(attr),  # ← NUEVO: valor actual del src/href
}
```

`element.get(attr)` ya devuelve el valor del atributo — sea el placeholder key o una URL real.

## Uso en el frontend

- Si `current_value` empieza con `http://`, `https://` o `//` → se pre-llena el input y se marca como **"Configurado"** (badge verde)
- Caso contrario → input vacío, badge **"Pendiente"** (naranja)

El frontend ya tiene esta lógica implementada y lista para consumir el campo.
