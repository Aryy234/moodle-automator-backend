# Plugin Moodle: `local_sectionedit`

Plugin minimalista que expone **una sola función de Web Service** para
actualizar el resumen (summary / HTML) de una sección de curso.

Moodle **no incluye** ninguna función estándar de Web Service que permita
editar `course_sections.summary`. Este plugin cubre esa carencia.

---

## Función expuesta

| Función WS | Tipo | Descripción |
|---|---|---|
| `local_sectionedit_update_section_summary` | `write` | Actualiza el HTML del summary de una sección |

### Parámetros

| Parámetro | Tipo | Requerido | Descripción |
|---|---|---|---|
| `sectionid` | int | sí | ID de la sección (`mdl_course_sections.id`) |
| `summary` | string | sí | Nuevo contenido HTML |
| `summaryformat` | int | no | Formato (1 = HTML por defecto) |

### Respuesta

```json
{
  "status": true,
  "message": "Section summary updated successfully."
}
```

---

## Instalación

### Opción A — Subir vía interfaz web (recomendada)

1. Comprime la carpeta `local_sectionedit/` en un ZIP:
   ```bash
   cd moodle-plugin
   zip -r local_sectionedit.zip local_sectionedit/
   ```
2. En Moodle, ve a **Administración del sitio → Plugins → Instalar plugins**.
3. Sube el archivo `local_sectionedit.zip`.
4. Sigue las indicaciones del instalador (actualizar BD, etc.).

### Opción B — Copiar al servidor

1. Copia la carpeta `local_sectionedit/` al directorio `local/` de tu
   instalación de Moodle:
   ```bash
   cp -r moodle-plugin/local_sectionedit /ruta/a/moodle/local/
   ```
2. Ve a **Administración del sitio → Notificaciones** para que Moodle
   detecte e instale el plugin.

---

## Configurar el Web Service

Después de instalar el plugin, agrega la función a tu servicio web existente:

1. **Administración del sitio → Servidor → Servicios externos**
2. Haz clic en **Funciones** del servicio que usa tu token.
3. Busca `local_sectionedit_update_section_summary` y agrégala.

> Si prefieres usar el servicio propio del plugin ("Section Edit Service"),
> crea un token nuevo para ese servicio y actualiza tu `.env`.

---

## Verificación rápida

```bash
curl -s "https://TU-MOODLE/webservice/rest/server.php" \
  -d "wstoken=TU_TOKEN" \
  -d "wsfunction=local_sectionedit_update_section_summary" \
  -d "moodlewsrestformat=json" \
  -d "sectionid=1606" \
  -d "summary=<p>Hola mundo</p>" \
  | python3 -m json.tool
```

Respuesta esperada:
```json
{ "status": true, "message": "Section summary updated successfully." }
```

---

## Requisitos

- Moodle 4.5+ (usa `core_external\external_api`, no la antigua `external_api`)
- El usuario del token debe tener la capacidad `moodle/course:update` en el
  curso afectado.

## Seguridad

- Valida contexto + capability `moodle/course:update`.
- Dispara el evento `course_section_updated` para que los logs y cachés
  se actualicen.
- Purga el caché de curso tras la actualización.

## Desinstalación

**Administración del sitio → Plugins → Plugins instalados →
local_sectionedit → Desinstalar**
