import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000, // 2 min para operaciones largas como duplicar
})

export { API_BASE_URL }

// ========== Health ==========
export const checkHealth = () => api.get('/courses/health/check')

// ========== Courses ==========
export const getCourses = () => api.get('/courses/')

export const getCourseById = (courseId) => api.get(`/courses/${courseId}`)

export const getCourseContents = (courseId) => api.get(`/courses/${courseId}/contents`)

export const duplicateCourse = (data) => api.post('/courses/duplicate', data)

export const updateCourse = (courseId, data) => api.put(`/courses/${courseId}`, data)

// ========== Editor ==========
export const scanCourse = (courseId) => api.get(`/editor/scan/${courseId}`)

export const getPlaceholders = () => api.get('/editor/placeholders')

export const previewChanges = (data) => api.post('/editor/preview', data)

export const applyChanges = (data) => api.post('/editor/customize', data)

// ========== Quizzes ==========
export const getQuizActivities = (courseId) =>
  api.get(`/quizzes/${courseId}/activities`)

export const getQuizCategories = (courseId, params = {}) =>
  api.get(`/quizzes/${courseId}/categories`, { params })

export const createQuizCategory = (courseId, data) =>
  api.post(`/quizzes/${courseId}/categories`, data)

export const previewImport = (formData) =>
  api.post('/quizzes/preview-import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })

export const importQuestions = (formData) =>
  api.post('/quizzes/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })

export const configureQuizQuestions = (courseId, data) =>
  api.post(`/quizzes/${courseId}/configure-questions`, data)

export const configureQuizSettings = (courseId, data) =>
  api.post(`/quizzes/${courseId}/settings`, data)

export default api
