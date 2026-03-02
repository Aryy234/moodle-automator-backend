import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  getQuizActivities,
  getQuizCategories,
  createQuizCategory,
  previewImport,
  importQuestions,
  configureQuizQuestions,
  configureQuizSettings,
} from '../api/index.js'

export const useQuizStore = defineStore('quiz', () => {
  // ========== State ==========
  const quizzes = ref([])
  const categories = ref([])
  const selectedQuiz = ref(null)
  const selectedCategory = ref(null)

  // Archivo y preview
  const file = ref(null)
  const fileFormat = ref('aiken') // 'aiken' | 'xml'
  const previewResult = ref(null)

  // Configuración de carga
  const loadMode = ref('all') // 'all' | 'random'
  const numRandomQuestions = ref(10)

  // Tiempo límite
  const timeLimit = ref(0) // en segundos — 0 = sin límite

  // Loading / error por operación
  const loading = ref({
    quizzes: false,
    categories: false,
    createCategory: false,
    preview: false,
    import: false,
    configure: false,
    settings: false,
  })

  const errors = ref({
    quizzes: null,
    categories: null,
    createCategory: null,
    preview: null,
    import: null,
    configure: null,
    settings: null,
  })

  // Resultados
  const importResult = ref(null)
  const configureResult = ref(null)
  const settingsResult = ref(null)

  // ========== Getters ==========
  const hasQuizzes = computed(() => quizzes.value.length > 0)
  const hasCategories = computed(() => categories.value.length > 0)
  const hasPreview = computed(() => previewResult.value?.questions?.length > 0)
  const isAnyLoading = computed(() => Object.values(loading.value).some(Boolean))

  const selectedQuizName = computed(() => selectedQuiz.value?.name || '')
  const selectedCategoryName = computed(() => selectedCategory.value?.name || '')

  // ========== Actions ==========

  async function fetchQuizzes(courseId) {
    loading.value.quizzes = true
    errors.value.quizzes = null
    try {
      const { data } = await getQuizActivities(courseId)
      quizzes.value = data.quizzes || []
    } catch (err) {
      errors.value.quizzes = _extractError(err)
    } finally {
      loading.value.quizzes = false
    }
  }

  async function fetchCategories(courseId, cmid) {
    loading.value.categories = true
    errors.value.categories = null
    try {
      const params = cmid ? { cmid } : {}
      const { data } = await getQuizCategories(courseId, params)
      categories.value = data.categories || []
    } catch (err) {
      errors.value.categories = _extractError(err)
    } finally {
      loading.value.categories = false
    }
  }

  async function createCategory(courseId, name, cmid) {
    loading.value.createCategory = true
    errors.value.createCategory = null
    try {
      const body = { name }
      if (cmid) body.cmid = cmid
      const { data } = await createQuizCategory(courseId, body)
      // Añadir la nueva categoría a la lista
      if (data.category_id) {
        const newCat = {
          id: data.category_id,
          name: data.name || name,
          questioncount: 0,
          contextlevel: cmid ? 'module' : 'course',
        }
        categories.value.push(newCat)
        selectedCategory.value = newCat
      }
      return data
    } catch (err) {
      errors.value.createCategory = _extractError(err)
    } finally {
      loading.value.createCategory = false
    }
  }

  async function previewFile() {
    if (!file.value) return
    loading.value.preview = true
    errors.value.preview = null
    previewResult.value = null
    try {
      const formData = new FormData()
      formData.append('file', file.value)
      formData.append('format', fileFormat.value)
      const { data } = await previewImport(formData)
      previewResult.value = data
      return data
    } catch (err) {
      errors.value.preview = _extractError(err)
    } finally {
      loading.value.preview = false
    }
  }

  async function importToBank(courseId) {
    if (!file.value || !selectedCategory.value) return
    loading.value.import = true
    errors.value.import = null
    importResult.value = null
    try {
      const formData = new FormData()
      formData.append('file', file.value)
      formData.append('format', fileFormat.value)
      formData.append('course_id', String(courseId))
      formData.append('category_id', String(selectedCategory.value.id))
      formData.append('category_name', selectedCategory.value.name)
      const { data } = await importQuestions(formData)
      importResult.value = data

      // Actualizar questioncount de la categoría seleccionada
      if (data.total_questions_imported) {
        const cat = categories.value.find((c) => c.id === selectedCategory.value.id)
        if (cat) cat.questioncount += data.total_questions_imported
      }
      return data
    } catch (err) {
      errors.value.import = _extractError(err)
    } finally {
      loading.value.import = false
    }
  }

  async function configureQuestionsOnQuiz(courseId) {
    if (!selectedQuiz.value || !selectedCategory.value) return
    loading.value.configure = true
    errors.value.configure = null
    configureResult.value = null
    try {
      const body = {
        quiz_cmid: selectedQuiz.value.coursemodule,
        category_id: selectedCategory.value.id,
        mode: loadMode.value,
      }
      if (loadMode.value === 'random') {
        body.num_questions = numRandomQuestions.value
      }
      const { data } = await configureQuizQuestions(courseId, body)
      configureResult.value = data
      return data
    } catch (err) {
      errors.value.configure = _extractError(err)
    } finally {
      loading.value.configure = false
    }
  }

  async function applyTimeLimit(courseId) {
    if (!selectedQuiz.value) return
    loading.value.settings = true
    errors.value.settings = null
    settingsResult.value = null
    try {
      const body = {
        quiz_cmid: selectedQuiz.value.coursemodule,
        time_limit: timeLimit.value,
      }
      const { data } = await configureQuizSettings(courseId, body)
      settingsResult.value = data
      return data
    } catch (err) {
      errors.value.settings = _extractError(err)
    } finally {
      loading.value.settings = false
    }
  }

  /** Ejecuta todo el flujo: import → configure → settings */
  async function saveQuiz(courseId) {
    // 1. Importar al banco
    const imp = await importToBank(courseId)
    if (!imp?.success) return null

    // 2. Cargar al quiz
    const conf = await configureQuestionsOnQuiz(courseId)
    if (!conf?.success) return null

    // 3. Configurar tiempo (solo si > 0)
    if (timeLimit.value > 0) {
      const sett = await applyTimeLimit(courseId)
      if (!sett?.success) return null
    }

    return { import: imp, configure: conf, settings: settingsResult.value }
  }

  function selectQuiz(quiz) {
    selectedQuiz.value = quiz
    selectedCategory.value = null
    categories.value = []
  }

  function selectCategory(cat) {
    selectedCategory.value = cat
  }

  function setFile(f, format) {
    file.value = f
    if (format) fileFormat.value = format
    previewResult.value = null
  }

  function resetQuiz() {
    quizzes.value = []
    categories.value = []
    selectedQuiz.value = null
    selectedCategory.value = null
    file.value = null
    fileFormat.value = 'aiken'
    previewResult.value = null
    importResult.value = null
    configureResult.value = null
    settingsResult.value = null
    loadMode.value = 'all'
    numRandomQuestions.value = 10
    timeLimit.value = 0
    _resetErrors()
  }

  function _resetErrors() {
    Object.keys(errors.value).forEach((k) => (errors.value[k] = null))
  }

  function _extractError(err) {
    const detail = err.response?.data?.detail
    if (typeof detail === 'string') return detail
    if (detail?.message) return detail.message
    return err.message || 'Error desconocido'
  }

  return {
    // State
    quizzes, categories, selectedQuiz, selectedCategory,
    file, fileFormat, previewResult,
    loadMode, numRandomQuestions, timeLimit,
    loading, errors,
    importResult, configureResult, settingsResult,
    // Getters
    hasQuizzes, hasCategories, hasPreview, isAnyLoading,
    selectedQuizName, selectedCategoryName,
    // Actions
    fetchQuizzes, fetchCategories, createCategory,
    previewFile, importToBank, configureQuestionsOnQuiz,
    applyTimeLimit, saveQuiz,
    selectQuiz, selectCategory, setFile, resetQuiz,
  }
})
