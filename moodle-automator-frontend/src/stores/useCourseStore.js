import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  checkHealth,
  getCourses,
  getCourseContents,
  updateCourse,
  scanCourse,
  previewChanges,
  applyChanges,
  duplicateCourse,
} from '../api/index.js'

export const useCourseStore = defineStore('course', () => {
  // ========== State ==========
  const connectionStatus = ref(null) // null | 'connected' | 'error'
  const siteInfo = ref(null)
  const courses = ref([])
  const selectedCourse = ref(null)
  const courseSections = ref([]) // secciones del curso con sus IDs
  const scanResult = ref(null)
  const previewResult = ref(null)
  const previewBlocks = ref(null) // parsed JSON from processed_html

  // Metadata de bloques existentes (label_cmid, label_instance_id) para update sin duplicar
  const existingBlocksMeta = ref({})
  // Ej: { presentations: { label_cmid: 4521, label_instance_id: 891 }, reading: {...}, videos: {...} }

  const loading = ref({
    health: false,
    courses: false,
    scan: false,
    preview: false,
    apply: false,
    applyGeneral: false,
    applyBlocks: false,
    duplicate: false,
  })

  const errors = ref({
    health: null,
    courses: null,
    scan: null,
    preview: null,
    apply: null,
    applyGeneral: null,
    applyBlocks: null,
    duplicate: null,
  })

  // Formulario de personalización
  const formData = ref({
    course_id: null,
    idnumber: null,
    // Placeholders (sección General)
    video_introductorio: null,
    unirse_clases: null,
    url_grabaciones: null,
    perfil_docente: null,
    silabo: null,
    pea: null,
    bibliografia_url: null,
    course_title: null,
    course_description: null,
    schedule: null,
    bibliography: null,
    // Sección destino para los bloques de contenido
    section_id: null,
    section_number: null,
    // Semana 1 — Bloque Presentaciones
    presentations: [],
    presentation_objective: null,
    // Semana 1 — Bloque Lectura
    main_reading: null,
    suggested_readings: [],
    reading_collapse_label: null,
    reading_section_title: null,
    reading_button_text: null,
    reading_suggested_title: null,
    // Semana 1 — Bloque Videos
    videos: [],
    videos_summary: null,
  })

  // Formulario de duplicación
  const duplicateForm = ref({
    source_course_id: null,
    new_fullname: '',
    new_shortname: '',
    new_idnumber: '',
    category_id: null,
    visible: 0,
    new_teacher_profile_url: null,
  })

  // Paso actual del flujo
  const currentStep = ref(1)

  // ========== Getters ==========
  const isConnected = computed(() => connectionStatus.value === 'connected')
  const isLoading = computed(() => Object.values(loading.value).some(Boolean))
  const hasPlaceholders = computed(() => scanResult.value?.placeholders?.length > 0)
  const hasSchedule = computed(() => scanResult.value?.schedule_found === true)
  const hasBibliography = computed(() => scanResult.value?.bibliography_found === true)

  // ========== Actions ==========
  async function verifyConnection() {
    loading.value.health = true
    errors.value.health = null
    try {
      const { data } = await checkHealth()
      connectionStatus.value = data.status
      siteInfo.value = data
    } catch (err) {
      connectionStatus.value = 'error'
      errors.value.health = err.response?.data?.detail || 'No se pudo conectar al servidor'
    } finally {
      loading.value.health = false
    }
  }

  async function fetchCourses() {
    loading.value.courses = true
    errors.value.courses = null
    try {
      const { data } = await getCourses()
      courses.value = data.courses || []
    } catch (err) {
      errors.value.courses = err.response?.data?.detail || 'Error al obtener cursos'
    } finally {
      loading.value.courses = false
    }
  }

  function selectCourse(course) {
    selectedCourse.value = course
    formData.value.course_id = course.id
    duplicateForm.value.source_course_id = course.id
    scanResult.value = null
    previewResult.value = null
    previewBlocks.value = null
    courseSections.value = []
  }

  async function scanSelectedCourse(courseId = null) {
    const id = courseId || selectedCourse.value?.id
    if (!id) return
    loading.value.scan = true
    errors.value.scan = null
    try {
      // Scan placeholders + obtener secciones en paralelo
      const [scanData, contentsData] = await Promise.all([
        scanCourse(id).then((r) => r.data),
        getCourseContents(id).then((r) => r.data).catch(() => null),
      ])

      scanResult.value = scanData
      formData.value.course_id = id

      // Mapeo de placeholder_key → campo del formulario
      const PLACEHOLDER_TO_FIELD = {
        'video-introductorio': 'video_introductorio',
        'unirse-clases':       'unirse_clases',
        'url-grabaciones':     'url_grabaciones',
        'perfil-docente':      'perfil_docente',
        'silabo':              'silabo',
        'pea':                 'pea',
        'bibliografia':        'bibliografia_url',
      }

      // Pre-llenar título y descripción si existen
      if (scanData.course_title) formData.value.course_title = scanData.course_title
      if (scanData.course_description) formData.value.course_description = scanData.course_description

      // Pre-llenar placeholders con su valor actual
      if (scanData.placeholders?.length > 0) {
        scanData.placeholders.forEach((ph) => {
          const fieldName = PLACEHOLDER_TO_FIELD[ph.placeholder_key]
          if (!fieldName) return
          // Si current_value es distinto del placeholder_key, ya fue configurado
          if (ph.current_value && ph.current_value !== ph.placeholder_key) {
            formData.value[fieldName] = ph.current_value
          }
        })
      }

      // Pre-llenar bloques avanzados existentes (presentaciones, lectura, videos)
      existingBlocksMeta.value = {} // Reset metadata
      if (scanData.existing_blocks?.length > 0) {
        scanData.existing_blocks.forEach((block) => {
          // Pre-llenar sección destino desde el primer bloque detectado
          if (block.section_id && !formData.value.section_id) {
            formData.value.section_id = block.section_id
            formData.value.section_number = block.section_number ?? 1
          }

          // Guardar metadata del label para update (evita duplicar bloques)
          if (block.label_cmid || block.label_instance_id) {
            existingBlocksMeta.value[block.block_type] = {
              label_cmid: block.label_cmid,
              label_instance_id: block.label_instance_id,
            }
          }

          switch (block.block_type) {
            case 'presentations':
              if (block.presentations?.length > 0) formData.value.presentations = block.presentations
              if (block.presentation_objective) formData.value.presentation_objective = block.presentation_objective
              break
            case 'reading':
              if (block.main_reading) formData.value.main_reading = block.main_reading
              if (block.suggested_readings?.length > 0) formData.value.suggested_readings = block.suggested_readings
              if (block.collapse_label) formData.value.reading_collapse_label = block.collapse_label
              if (block.reading_section_title) formData.value.reading_section_title = block.reading_section_title
              if (block.reading_button_text) formData.value.reading_button_text = block.reading_button_text
              if (block.reading_suggested_title) formData.value.reading_suggested_title = block.reading_suggested_title
              break
            case 'videos':
              if (block.videos?.length > 0) formData.value.videos = block.videos
              if (block.videos_summary) formData.value.videos_summary = block.videos_summary
              break
          }
        })
      }

      // Pre-llenar horario existente
      if (scanData.existing_schedule) {
        formData.value.schedule = {
          days_columns: scanData.existing_schedule.days_columns,
          entries: scanData.existing_schedule.entries,
        }
      }

      // Pre-llenar bibliografía existente
      if (scanData.existing_bibliography?.entries?.length > 0) {
        formData.value.bibliography = {
          entries: scanData.existing_bibliography.entries,
        }
      }

      // Pre-llenar idnumber con el valor actual del curso (viene del listado de cursos)
      const existingIdnumber = selectedCourse.value?.idnumber
      if (existingIdnumber !== undefined && existingIdnumber !== null) {
        formData.value.idnumber = existingIdnumber
      }

      // Guardar secciones con id y nombre para el selector
      if (contentsData?.sections) {
        courseSections.value = contentsData.sections.map((s) => ({
          id: s.id,
          section: s.section,
          name: s.name || `Sección ${s.section}`,
        }))
      }
    } catch (err) {
      errors.value.scan = err.response?.data?.detail || 'Error al escanear el curso'
    } finally {
      loading.value.scan = false
    }
  }

  async function requestPreview() {
    loading.value.preview = true
    errors.value.preview = null
    try {
      const payload = buildPayload()
      const { data } = await previewChanges(payload)
      previewResult.value = data

      // Parsear el JSON de processed_html
      if (data.processed_html) {
        try {
          previewBlocks.value = JSON.parse(data.processed_html)
        } catch (_) {
          // Si no es JSON (versiones anteriores), guardarlo como HTML plano
          previewBlocks.value = null
        }
      }
      return data
    } catch (err) {
      errors.value.preview = err.response?.data?.detail || 'Error en la previsualización'
    } finally {
      loading.value.preview = false
    }
  }

  async function applyCustomization() {
    loading.value.apply = true
    errors.value.apply = null
    try {
      // Actualizar idnumber si se proporcionó (PUT /courses/{id}) — fallo silencioso
      await tryUpdateIdnumber()
      const payload = buildPayload()
      const { data } = await applyChanges(payload)
      return data
    } catch (err) {
      errors.value.apply = err.response?.data?.detail || err.message || 'Error al aplicar los cambios'
    } finally {
      loading.value.apply = false
    }
  }

  // ========== Guardado por partes ==========

  /** Intenta actualizar el idnumber del curso via PUT /courses/{id}. Fallo silencioso. */
  async function tryUpdateIdnumber() {
    const id = formData.value.idnumber
    if (id === null || id === undefined || id === '') return
    try {
      await updateCourse(formData.value.course_id, { idnumber: id.trim() })
    } catch (_) {
      // El endpoint puede no existir aún (405) — fallo silencioso
      console.warn('[MCA] No se pudo actualizar idnumber (endpoint no disponible):', _.message)
    }
  }

  /** Guarda solo: idnumber, título, descripción, placeholders, horario, bibliografía */
  async function applyGeneral() {
    loading.value.applyGeneral = true
    errors.value.applyGeneral = null
    try {
      // Actualizar idnumber (PUT /courses/{id}) — fallo silencioso
      await tryUpdateIdnumber()

      const payload = buildGeneralPayload()
      // Solo enviar si hay campos que modificar (más allá de course_id)
      if (Object.keys(payload).length <= 1) {
        return { success: true, total_replacements: 0, message: 'No hay campos generales que modificar.' }
      }
      const { data } = await applyChanges(payload)
      return data
    } catch (err) {
      errors.value.applyGeneral = err.response?.data?.detail || err.message || 'Error al guardar sección general'
    } finally {
      loading.value.applyGeneral = false
    }
  }

  /** Guarda solo: presentaciones, lectura, videos (como labels independientes en Moodle) */
  async function applyBlocks() {
    loading.value.applyBlocks = true
    errors.value.applyBlocks = null
    try {
      const payload = buildBlocksPayload()
      const { data } = await applyChanges(payload)
      return data
    } catch (err) {
      errors.value.applyBlocks = err.response?.data?.detail || err.message || 'Error al guardar bloques de contenido'
    } finally {
      loading.value.applyBlocks = false
    }
  }

  /** Payload solo con campos de la sección General (modo legacy, sin sections[]) */
  function buildGeneralPayload() {
    const fd = formData.value
    const payload = { course_id: fd.course_id }
    const fields = [
      'video_introductorio', 'unirse_clases', 'url_grabaciones',
      'perfil_docente', 'silabo', 'pea', 'bibliografia_url',
      'course_title', 'course_description',
    ]
    fields.forEach((key) => {
      if (fd[key] !== null && fd[key] !== '') payload[key] = fd[key]
    })
    if (fd.schedule) payload.schedule = fd.schedule
    if (fd.bibliography) payload.bibliography = fd.bibliography
    return payload
  }

  /** Payload solo con bloques de contenido (modo sections[]) */
  function buildBlocksPayload() {
    const fd = formData.value
    const sectionId = fd.section_id
    if (!sectionId) {
      throw new Error('Debes seleccionar en qué sección de Moodle crear los bloques de contenido.')
    }

    const section = {
      section_id: sectionId,
      section_number: fd.section_number ?? 1,
    }

    // Campos escalares de bloques
    const blockScalars = [
      'presentation_objective', 'videos_summary',
      'reading_collapse_label', 'reading_section_title',
      'reading_button_text', 'reading_suggested_title',
    ]
    blockScalars.forEach((key) => {
      if (fd[key] !== null && fd[key] !== '') section[key] = fd[key]
    })

    if (fd.main_reading) section.main_reading = fd.main_reading
    if (fd.presentations?.length > 0) section.presentations = fd.presentations
    if (fd.suggested_readings?.length > 0) section.suggested_readings = fd.suggested_readings
    if (fd.videos?.length > 0) section.videos = fd.videos

    // Incluir IDs de labels existentes para que el backend actualice en vez de crear duplicados
    attachBlockMeta(section)

    return {
      course_id: fd.course_id,
      sections: [section],
    }
  }

  async function duplicateSelectedCourse() {
    loading.value.duplicate = true
    errors.value.duplicate = null
    try {
      const df = duplicateForm.value
      const payload = {
        source_course_id: df.source_course_id,
        new_fullname: df.new_fullname,
        new_shortname: df.new_shortname,
        category_id: df.category_id ?? null,
        visible: df.visible ?? 0,
      }
      if (df.new_idnumber?.trim()) payload.new_idnumber = df.new_idnumber.trim()
      if (df.new_teacher_profile_url?.trim()) payload.new_teacher_profile_url = df.new_teacher_profile_url.trim()
      const { data } = await duplicateCourse(payload)
      return data
    } catch (err) {
      errors.value.duplicate = err.response?.data?.detail || 'Error al duplicar el curso'
    } finally {
      loading.value.duplicate = false
    }
  }

  function buildPayload() {
    const fd = formData.value

    // Separar campos de la sección General (placeholders + title/desc/schedule/bibliography)
    // de los bloques de contenido (presentations/reading/videos)
    const hasContentBlocks = (
      fd.presentations?.length > 0 ||
      fd.main_reading ||
      fd.suggested_readings?.length > 0 ||
      fd.videos?.length > 0
    )

    // Si no hay bloques de contenido, usar modo legacy (compatible con versión anterior)
    if (!hasContentBlocks) {
      const payload = { course_id: fd.course_id }
      const legacyFields = [
        'video_introductorio', 'unirse_clases', 'url_grabaciones',
        'perfil_docente', 'silabo', 'pea', 'bibliografia_url',
        'course_title', 'course_description',
      ]
      legacyFields.forEach((key) => {
        if (fd[key] !== null && fd[key] !== '') payload[key] = fd[key]
      })
      if (fd.schedule) payload.schedule = fd.schedule
      if (fd.bibliography) payload.bibliography = fd.bibliography
      return payload
    }

    // Modo sections: requiere section_id real
    const sectionId = fd.section_id
    if (!sectionId) {
      // Si aún no eligió sección, lanzar error descriptivo
      throw new Error('Debes seleccionar en qué sección de Moodle crear los bloques de contenido.')
    }

    const section = {
      section_id: sectionId,
      section_number: fd.section_number ?? 1,
    }

    // Escalares
    const scalarFields = [
      'video_introductorio', 'unirse_clases', 'url_grabaciones',
      'perfil_docente', 'silabo', 'pea', 'bibliografia_url',
      'course_title', 'course_description',
      'presentation_objective', 'videos_summary',
      'reading_collapse_label', 'reading_section_title',
      'reading_button_text', 'reading_suggested_title',
    ]
    scalarFields.forEach((key) => {
      if (fd[key] !== null && fd[key] !== '') section[key] = fd[key]
    })

    if (fd.schedule) section.schedule = fd.schedule
    if (fd.bibliography) section.bibliography = fd.bibliography
    if (fd.main_reading) section.main_reading = fd.main_reading
    if (fd.presentations?.length > 0) section.presentations = fd.presentations
    if (fd.suggested_readings?.length > 0) section.suggested_readings = fd.suggested_readings
    if (fd.videos?.length > 0) section.videos = fd.videos

    // Incluir IDs de labels existentes para que el backend actualice en vez de crear duplicados
    attachBlockMeta(section)

    return {
      course_id: fd.course_id,
      sections: [section],
    }
  }

  /**
   * Adjunta label_cmid y label_instance_id al section payload
   * para que el backend actualice bloques existentes en vez de crear nuevos.
   */
  function attachBlockMeta(section) {
    const meta = existingBlocksMeta.value
    if (!meta || Object.keys(meta).length === 0) return

    const existing_labels = {}
    for (const [blockType, ids] of Object.entries(meta)) {
      if (ids.label_cmid || ids.label_instance_id) {
        existing_labels[blockType] = ids
      }
    }
    if (Object.keys(existing_labels).length > 0) {
      section.existing_labels = existing_labels
    }
  }

  function resetForm() {
    formData.value = {
      course_id: null,
      idnumber: null,
      video_introductorio: null,
      unirse_clases: null,
      url_grabaciones: null,
      perfil_docente: null,
      silabo: null,
      pea: null,
      bibliografia_url: null,
      course_title: null,
      course_description: null,
      schedule: null,
      bibliography: null,
      section_id: null,
      section_number: null,
      presentations: [],
      presentation_objective: null,
      main_reading: null,
      suggested_readings: [],
      reading_collapse_label: null,
      reading_section_title: null,
      reading_button_text: null,
      reading_suggested_title: null,
      videos: [],
      videos_summary: null,
    }
    scanResult.value = null
    previewResult.value = null
    previewBlocks.value = null
    existingBlocksMeta.value = {}
    currentStep.value = 1
  }

  function setStep(step) {
    currentStep.value = step
  }

  return {
    // State
    connectionStatus, siteInfo, courses, selectedCourse, courseSections,
    scanResult, previewResult, previewBlocks, loading, errors,
    formData, duplicateForm, currentStep,
    // Getters
    isConnected, isLoading, hasPlaceholders, hasSchedule, hasBibliography,
    // Actions
    verifyConnection, fetchCourses, selectCourse,
    scanSelectedCourse, requestPreview, applyCustomization,
    applyGeneral, applyBlocks,
    duplicateSelectedCourse, resetForm, setStep,
  }
})
