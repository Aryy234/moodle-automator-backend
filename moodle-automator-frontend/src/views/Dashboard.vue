<template>
  <div class="min-h-screen">
    <!-- Header -->
    <header class="sticky top-0 z-30 bg-surface/80 backdrop-blur-md border-b border-border-soft">
      <div class="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 rounded-xl bg-primary flex items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none"
                 stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
              <polyline points="3.29 7 12 12 20.71 7" /><line x1="12" y1="22" x2="12" y2="12" />
            </svg>
          </div>
          <div>
            <h1 class="text-base font-bold text-text-primary">Moodle Automator</h1>
            <p class="text-[11px] text-text-muted">Gestión inteligente de cursos</p>
          </div>
        </div>

        <!-- Connection status -->
        <StatusBadge
          :status="store.loading.health ? 'loading' : (store.isConnected ? 'connected' : 'error')"
          :title="store.isConnected ? store.siteInfo?.site_name || 'Conectado' : 'Sin conexión'"
          :subtitle="store.isConnected ? store.siteInfo?.username : 'Verificando...'"
        />
      </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-6xl mx-auto px-6 py-8">
      <!-- Error de conexión -->
      <div v-if="store.connectionStatus === 'error'" class="mb-8">
        <div class="bg-pastel-pink/50 border border-danger/30 rounded-2xl p-6 text-center">
          <div class="w-12 h-12 rounded-full bg-danger/20 flex items-center justify-center mx-auto mb-3">
            <svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6 text-danger-dark" viewBox="0 0 24 24" fill="none"
                 stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
          </div>
          <h3 class="text-sm font-semibold text-danger-dark mb-1">No se pudo conectar al backend</h3>
          <p class="text-xs text-text-muted mb-4">Asegúrate de que el servidor FastAPI esté corriendo en localhost:8000</p>
          <button
            @click="store.verifyConnection()"
            class="px-4 py-2 rounded-xl bg-primary text-white text-sm font-medium hover:bg-primary-dark transition-colors"
          >
            Reintentar
          </button>
        </div>
      </div>

      <!-- Tabs -->
      <div class="flex gap-1 mb-8 bg-surface-alt rounded-xl p-1 w-fit">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          @click="activeTab = tab.id"
          class="px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200"
          :class="activeTab === tab.id
            ? 'bg-surface-card text-primary shadow-sm'
            : 'text-text-muted hover:text-text-secondary'"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- Tab: Personalizar -->
      <div v-if="activeTab === 'customize'">
        <!-- Buscador -->
        <div class="mb-6">
          <div class="relative">
            <svg xmlns="http://www.w3.org/2000/svg" class="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted"
                 viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Buscar curso por nombre o ID..."
              class="w-full pl-11 pr-4 py-3 rounded-xl border border-border-soft bg-surface-card text-sm text-text-primary
                     placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary
                     transition-all duration-200"
            />
          </div>
        </div>

        <!-- Lista de cursos -->
        <div v-if="store.loading.courses" class="flex items-center justify-center py-16">
          <div class="flex items-center gap-3 text-text-muted">
            <svg class="animate-spin w-5 h-5" viewBox="0 0 24 24" fill="none">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            <span class="text-sm">Cargando cursos...</span>
          </div>
        </div>

        <div v-else>
          <div class="flex items-center justify-between mb-4">
            <p class="text-xs text-text-muted">
              {{ filteredCourses.length }} curso{{ filteredCourses.length !== 1 ? 's' : '' }} encontrado{{ filteredCourses.length !== 1 ? 's' : '' }}
            </p>
            <button
              @click="store.fetchCourses()"
              class="text-xs text-primary hover:text-primary-dark font-medium transition-colors flex items-center gap-1"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none"
                   stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="23 4 23 10 17 10" /><polyline points="1 20 1 14 7 14" />
                <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
              </svg>
              Actualizar
            </button>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            <CourseCard
              v-for="course in filteredCourses"
              :key="course.id"
              :course="course"
              :isSelected="store.selectedCourse?.id === course.id"
              @select="handleSelectCourse"
            />
          </div>

          <div v-if="filteredCourses.length === 0 && !store.loading.courses"
               class="text-center py-12">
            <div class="w-16 h-16 rounded-2xl bg-surface-alt flex items-center justify-center mx-auto mb-3">
              <svg xmlns="http://www.w3.org/2000/svg" class="w-8 h-8 text-text-muted" viewBox="0 0 24 24" fill="none"
                   stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
            </div>
            <p class="text-sm text-text-muted">No se encontraron cursos</p>
          </div>
        </div>

        <!-- Botón continuar -->
        <div v-if="store.selectedCourse" class="mt-8 flex justify-end">
          <button
            @click="goToCustomizer"
            class="px-6 py-3 rounded-xl bg-primary text-white text-sm font-semibold
                   hover:bg-primary-dark transition-all duration-200 shadow-lg shadow-primary/20
                   flex items-center gap-2"
          >
            Personalizar curso
            <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none"
                 stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="5" y1="12" x2="19" y2="12" /><polyline points="12 5 19 12 12 19" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Tab: Duplicar -->
      <div v-if="activeTab === 'duplicate'">
        <div class="max-w-xl mx-auto">
          <div class="bg-surface-card rounded-2xl border border-border-soft p-6 space-y-5">
            <div class="flex items-center gap-3 mb-2">
              <div class="w-10 h-10 rounded-xl bg-pastel-peach flex items-center justify-center">
                <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 text-warning-dark" viewBox="0 0 24 24" fill="none"
                     stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="8" y="2" width="13" height="13" rx="2" ry="2" /><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                </svg>
              </div>
              <div>
                <h2 class="text-base font-semibold text-text-primary">Duplicar Curso</h2>
                <p class="text-xs text-text-muted">Crea una copia completa de un curso existente</p>
              </div>
            </div>

            <!-- Buscador de curso origen -->
            <div>
              <label class="block text-xs font-medium text-text-secondary mb-1.5">Buscar curso origen</label>
              <div class="relative mb-3">
                <svg xmlns="http://www.w3.org/2000/svg" class="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted"
                     viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
                </svg>
                <input
                  v-model="searchQuery"
                  type="text"
                  placeholder="Buscar curso por nombre o ID..."
                  class="w-full pl-11 pr-4 py-3 rounded-xl border border-border-soft bg-surface text-sm text-text-primary
                         placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary
                         transition-all duration-200"
                />
              </div>
              <div class="max-h-60 overflow-y-auto rounded-xl border border-border-soft bg-surface-alt">
                <ul>
                  <li v-for="c in filteredCourses" :key="c.id">
                    <button
                      @click="store.duplicateForm.source_course_id = c.id"
                      :class="store.duplicateForm.source_course_id === c.id
                        ? 'bg-primary text-white' : 'bg-transparent text-text-primary hover:bg-primary/10'"
                      class="w-full text-left px-4 py-2 transition-all rounded-xl"
                    >
                      {{ c.fullname }} <span class="text-xs text-text-muted">(ID: {{ c.id }})</span>
                    </button>
                  </li>
                  <li v-if="filteredCourses.length === 0" class="px-4 py-2 text-text-muted text-xs">
                    No se encontraron cursos
                  </li>
                </ul>
              </div>
            </div>

            <!-- Nombre completo -->
            <div>
              <label class="block text-xs font-medium text-text-secondary mb-1.5">Nombre completo del nuevo curso</label>
              <input
                type="text"
                v-model="store.duplicateForm.new_fullname"
                class="w-full px-4 py-2.5 rounded-xl border border-border-soft bg-surface text-sm text-text-primary
                       placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary
                       transition-all"
                placeholder="Ej: Matemáticas 101 - Periodo 2026-1"
              />
            </div>

            <!-- Nombre corto -->
            <div>
              <label class="block text-xs font-medium text-text-secondary mb-1.5">Nombre corto</label>
              <input
                type="text"
                v-model="store.duplicateForm.new_shortname"
                class="w-full px-4 py-2.5 rounded-xl border border-border-soft bg-surface text-sm text-text-primary
                       placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary
                       transition-all"
                placeholder="Ej: MAT101-2026-1"
              />
            </div>

            <!-- Número ID del curso -->
            <div>
              <label class="block text-xs font-medium text-text-secondary mb-1.5">Número ID del curso (opcional)</label>
              <input
                type="text"
                v-model="store.duplicateForm.new_idnumber"
                class="w-full px-4 py-2.5 rounded-xl border border-border-soft bg-surface text-sm text-text-primary
                       placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary
                       transition-all"
                placeholder="Ej: MAT-2025-A"
              />
              <p class="mt-1 text-[11px] text-text-muted">Identificador interno en Moodle (Administración del curso → Número ID). Déjalo vacío si no lo necesitas.</p>
            </div>

            <!-- URL perfil docente -->
            <div>
              <label class="block text-xs font-medium text-text-secondary mb-1.5">URL del Perfil del Docente (opcional)</label>
              <input
                type="url"
                v-model="store.duplicateForm.new_teacher_profile_url"
                class="w-full px-4 py-2.5 rounded-xl border border-border-soft bg-surface text-sm text-text-primary
                       placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary
                       transition-all"
                placeholder="https://perfil-del-docente.com"
              />
            </div>

            <!-- Visibilidad -->
            <div class="flex items-center justify-between p-3 rounded-xl bg-surface border border-border-soft">
              <div>
                <p class="text-sm font-medium text-text-primary">Curso visible</p>
                <p class="text-xs text-text-muted">Visible para los estudiantes al crearse</p>
              </div>
              <button
                @click="store.duplicateForm.visible = store.duplicateForm.visible === 1 ? 0 : 1"
                class="relative w-11 h-6 rounded-full transition-colors duration-200"
                :class="store.duplicateForm.visible === 1 ? 'bg-primary' : 'bg-border-soft'"
              >
                <span
                  class="absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform duration-200"
                  :class="store.duplicateForm.visible === 1 ? 'translate-x-5' : ''"
                ></span>
              </button>
            </div>

            <!-- Botón duplicar -->
            <button
              @click="handleDuplicate"
              :disabled="!canDuplicate || store.loading.duplicate"
              class="w-full py-3 rounded-xl text-white text-sm font-semibold transition-all duration-200
                     flex items-center justify-center gap-2"
              :class="canDuplicate && !store.loading.duplicate
                ? 'bg-primary hover:bg-primary-dark shadow-lg shadow-primary/20 cursor-pointer'
                : 'bg-border-soft text-text-muted cursor-not-allowed'"
            >
              <svg v-if="store.loading.duplicate" class="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              <span>{{ store.loading.duplicate ? 'Duplicando curso...' : 'Duplicar Curso' }}</span>
            </button>

            <!-- Resultado -->
            <div v-if="duplicateResult" class="p-4 rounded-xl border"
                 :class="duplicateResult.success ? 'bg-pastel-mint/50 border-success/30' : 'bg-pastel-pink/50 border-danger/30'">
              <p class="text-sm font-medium" :class="duplicateResult.success ? 'text-success-dark' : 'text-danger-dark'">
                {{ duplicateResult.message }}
              </p>
              <div v-if="duplicateResult.success" class="mt-2 space-y-1">
                <p class="text-xs text-text-secondary">ID nuevo: {{ duplicateResult.new_course_id }}</p>
                <a :href="duplicateResult.new_course_url" target="_blank"
                   class="inline-flex items-center gap-1 text-xs text-primary hover:text-primary-dark font-medium">
                  Abrir en Moodle
                  <svg xmlns="http://www.w3.org/2000/svg" class="w-3 h-3" viewBox="0 0 24 24" fill="none"
                       stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                    <polyline points="15 3 21 3 21 9" /><line x1="10" y1="14" x2="21" y2="3" />
                  </svg>
                </a>
                <button
                  @click="goToCustomizeNewCourse(duplicateResult.new_course_id)"
                  class="mt-2 px-4 py-2 rounded-lg bg-primary/10 text-primary text-xs font-medium
                         hover:bg-primary/20 transition-colors"
                >
                  Personalizar este curso
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useCourseStore } from '../stores/useCourseStore.js'
import CourseCard from '../components/CourseCard.vue'
import StatusBadge from '../components/StatusBadge.vue'

const router = useRouter()
const store = useCourseStore()

const activeTab = ref('customize')
const searchQuery = ref('')
const duplicateResult = ref(null)

const tabs = [
  { id: 'customize', label: 'Personalizar' },
  { id: 'duplicate', label: 'Duplicar' },
]

const filteredCourses = computed(() => {
  if (!searchQuery.value) return store.courses
  const q = searchQuery.value.toLowerCase()
  return store.courses.filter(
    (c) =>
      c.fullname.toLowerCase().includes(q) ||
      c.shortname.toLowerCase().includes(q) ||
      String(c.id).includes(q)
  )
})

const canDuplicate = computed(() =>
  store.duplicateForm.source_course_id &&
  store.duplicateForm.new_fullname.trim() &&
  store.duplicateForm.new_shortname.trim()
)

function handleSelectCourse(course) {
  store.selectCourse(course)
}

function goToCustomizer() {
  if (store.selectedCourse) {
    router.push({ name: 'customizer', params: { id: store.selectedCourse.id } })
  }
}

async function handleDuplicate() {
  duplicateResult.value = null
  const result = await store.duplicateSelectedCourse()
  if (result) {
    duplicateResult.value = result
  } else if (store.errors.duplicate) {
    duplicateResult.value = { success: false, message: store.errors.duplicate }
  }
}

function goToCustomizeNewCourse(courseId) {
  // Seleccionar el nuevo curso
  store.selectCourse({ id: courseId, fullname: `Curso ${courseId}`, shortname: '' })
  router.push({ name: 'customizer', params: { id: courseId } })
}

onMounted(async () => {
  await store.verifyConnection()
  if (store.isConnected) {
    await store.fetchCourses()
  }
})
</script>
