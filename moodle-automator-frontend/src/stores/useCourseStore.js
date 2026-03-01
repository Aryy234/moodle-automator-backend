import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  checkHealth,
  getCourses,
  getCourseContents,
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

  const loading = ref({
    health: false,
    courses: false,
    scan: false,
    preview: false,
    apply: false,
    duplicate: false,
  })

  const errors = ref({
    health: null,
    courses: null,
    scan: null,
    preview: null,
    apply: null,
    duplicate: null,
  })

  // Formulario de personalización
  const formData = ref({
    course_id: null,
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

      // Pre-llenar título y descripción si existen
      if (scanData.course_title) formData.value.course_title = scanData.course_title
      if (scanData.course_description) formData.value.course_description = scanData.course_description

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
      const payload = buildPayload()
      const { data } = await applyChanges(payload)
      return data
    } catch (err) {
      errors.value.apply = err.response?.data?.detail || 'Error al aplicar los cambios'
    } finally {
      loading.value.apply = false
    }
  }

  async function duplicateSelectedCourse() {
    loading.value.duplicate = true
    errors.value.duplicate = null
    try {
      const { data } = await duplicateCourse(duplicateForm.value)
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

    return {
      course_id: fd.course_id,
      sections: [section],
    }
  }

  function resetForm() {
    formData.value = {
      course_id: null,
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
    duplicateSelectedCourse, resetForm, setStep,
  }
})
