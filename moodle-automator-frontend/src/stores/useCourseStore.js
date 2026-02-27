import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  checkHealth,
  getCourses,
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
  const scanResult = ref(null)
  const previewResult = ref(null)

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
  }

  async function scanSelectedCourse(courseId = null) {
    const id = courseId || selectedCourse.value?.id
    if (!id) return
    loading.value.scan = true
    errors.value.scan = null
    try {
      const { data } = await scanCourse(id)
      scanResult.value = data
      formData.value.course_id = id

      // Pre-llenar título y descripción si existen
      if (data.course_title) {
        formData.value.course_title = data.course_title
      }
      if (data.course_description) {
        formData.value.course_description = data.course_description
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
    const payload = { course_id: formData.value.course_id }
    // Solo incluir campos con valor
    const fields = [
      'video_introductorio', 'unirse_clases', 'url_grabaciones',
      'perfil_docente', 'silabo', 'pea', 'bibliografia_url',
      'course_title', 'course_description', 'schedule', 'bibliography',
    ]
    fields.forEach((key) => {
      if (formData.value[key] !== null && formData.value[key] !== '') {
        payload[key] = formData.value[key]
      }
    })
    return payload
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
    }
    scanResult.value = null
    previewResult.value = null
    currentStep.value = 1
  }

  function setStep(step) {
    currentStep.value = step
  }

  return {
    // State
    connectionStatus, siteInfo, courses, selectedCourse,
    scanResult, previewResult, loading, errors,
    formData, duplicateForm, currentStep,
    // Getters
    isConnected, isLoading, hasPlaceholders, hasSchedule, hasBibliography,
    // Actions
    verifyConnection, fetchCourses, selectCourse,
    scanSelectedCourse, requestPreview, applyCustomization,
    duplicateSelectedCourse, resetForm, setStep,
  }
})
