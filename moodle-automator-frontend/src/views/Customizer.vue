<template>
  <div class="min-h-screen">
    <!-- Header -->
    <header class="sticky top-0 z-30 bg-surface/80 backdrop-blur-md border-b border-border-soft">
      <div class="max-w-5xl mx-auto px-6 py-4">
        <div class="flex items-center gap-4">
          <button
            @click="goBack"
            class="w-9 h-9 rounded-xl bg-surface-alt flex items-center justify-center text-text-muted
                   hover:text-text-primary hover:bg-border-soft transition-all"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none"
                 stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="19" y1="12" x2="5" y2="12" /><polyline points="12 19 5 12 12 5" />
            </svg>
          </button>

          <div class="flex-1 min-w-0">
            <h1 class="text-base font-bold text-text-primary truncate">
              {{ store.selectedCourse?.fullname || 'Personalizar Curso' }}
            </h1>
            <p class="text-[11px] text-text-muted">
              ID: {{ courseId }} · Personalización de contenido
            </p>
          </div>
        </div>

        <!-- Steps -->
        <div class="mt-4">
          <StepProgress :steps="stepLabels" :current="store.currentStep" />
        </div>
      </div>
    </header>

    <!-- Main -->
    <main class="max-w-5xl mx-auto px-6 py-8">
      <!-- Loading scan -->
      <div v-if="store.loading.scan" class="flex flex-col items-center justify-center py-20">
        <div class="w-16 h-16 rounded-2xl bg-pastel-purple flex items-center justify-center mb-4">
          <svg class="animate-spin w-7 h-7 text-primary" viewBox="0 0 24 24" fill="none">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
        </div>
        <p class="text-sm font-medium text-text-primary">Escaneando curso...</p>
        <p class="text-xs text-text-muted mt-1">Analizando contenido HTML del template</p>
      </div>

      <!-- Scan error -->
      <div v-else-if="store.errors.scan" class="max-w-md mx-auto text-center py-16">
        <div class="w-14 h-14 rounded-2xl bg-pastel-pink flex items-center justify-center mx-auto mb-4">
          <svg xmlns="http://www.w3.org/2000/svg" class="w-7 h-7 text-danger-dark" viewBox="0 0 24 24" fill="none"
               stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
        </div>
        <p class="text-sm font-semibold text-danger-dark mb-1">Error al escanear</p>
        <p class="text-xs text-text-muted mb-4">{{ store.errors.scan }}</p>
        <button @click="store.scanSelectedCourse(courseId)"
                class="px-4 py-2 rounded-xl bg-primary text-white text-sm font-medium hover:bg-primary-dark transition-colors">
          Reintentar
        </button>
      </div>

      <!-- Content -->
      <div v-else-if="store.scanResult" class="space-y-8">
        <!-- Scan summary -->
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div class="bg-surface-card rounded-xl border border-border-soft p-4 text-center">
            <p class="text-2xl font-bold text-primary">{{ store.scanResult.total_placeholders }}</p>
            <p class="text-[11px] text-text-muted mt-1">Placeholders</p>
          </div>
          <div class="bg-surface-card rounded-xl border border-border-soft p-4 text-center">
            <p class="text-2xl font-bold text-accent">{{ store.scanResult.schedule_found ? 'Sí' : 'No' }}</p>
            <p class="text-[11px] text-text-muted mt-1">Horario</p>
          </div>
          <div class="bg-surface-card rounded-xl border border-border-soft p-4 text-center">
            <p class="text-2xl font-bold text-success-dark">{{ store.scanResult.bibliography_found ? 'Sí' : 'No' }}</p>
            <p class="text-[11px] text-text-muted mt-1">Bibliografía</p>
          </div>
          <div class="bg-surface-card rounded-xl border border-border-soft p-4 text-center">
            <p class="text-2xl font-bold text-secondary">{{ store.scanResult.section_name }}</p>
            <p class="text-[11px] text-text-muted mt-1">Sección</p>
          </div>
        </div>

        <!-- Step 1: Form -->
        <div v-if="store.currentStep === 1">
          <SetupForm :form="store.formData" :scanResult="store.scanResult" />

          <div class="flex justify-end gap-3 mt-8">
            <button
              @click="handlePreview"
              :disabled="store.loading.preview"
              class="px-6 py-3 rounded-xl bg-primary text-white text-sm font-semibold
                     hover:bg-primary-dark transition-all duration-200 shadow-lg shadow-primary/20
                     flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg v-if="store.loading.preview" class="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none"
                   stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" /><circle cx="12" cy="12" r="3" />
              </svg>
              {{ store.loading.preview ? 'Procesando...' : 'Previsualizar' }}
            </button>
          </div>
        </div>

        <!-- Step 2: Preview -->
        <div v-if="store.currentStep === 2 && store.previewResult">
          <!-- Changes summary -->
          <div class="bg-surface-card rounded-2xl border border-border-soft p-6 mb-6">
            <div class="flex items-center gap-2 mb-4">
              <div class="w-8 h-8 rounded-lg bg-pastel-mint flex items-center justify-center">
                <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 text-success-dark" viewBox="0 0 24 24" fill="none"
                     stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="9 11 12 14 22 4" /><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
                </svg>
              </div>
              <div>
                <h3 class="text-sm font-semibold text-text-primary">Resumen de Cambios</h3>
                <p class="text-xs text-text-muted">{{ store.previewResult.total_replacements }} modificaciones detectadas</p>
              </div>
            </div>

            <div class="space-y-2 max-h-60 overflow-y-auto">
              <div v-for="(detail, idx) in store.previewResult.details" :key="idx"
                   class="flex items-start gap-3 p-3 rounded-xl bg-surface text-xs">
                <span class="inline-flex items-center px-2 py-0.5 rounded-full bg-pastel-blue text-accent font-mono text-[10px] shrink-0">
                  {{ detail.field }}
                </span>
                <div class="min-w-0">
                  <p class="text-text-muted truncate">
                    <span class="line-through">{{ truncate(detail.old_value, 60) }}</span>
                  </p>
                  <p class="text-success-dark truncate font-medium">
                    {{ truncate(detail.new_value, 60) }}
                  </p>
                </div>
              </div>
            </div>
          </div>

          <!-- HTML Preview -->
          <div class="bg-surface-card rounded-2xl border border-border-soft overflow-hidden mb-6">
            <div class="px-6 py-3 border-b border-border-soft flex items-center gap-2">
              <div class="flex gap-1.5">
                <span class="w-3 h-3 rounded-full bg-danger"></span>
                <span class="w-3 h-3 rounded-full bg-warning"></span>
                <span class="w-3 h-3 rounded-full bg-success"></span>
              </div>
              <span class="text-xs text-text-muted ml-2">Vista previa del HTML procesado</span>
            </div>
            <div class="p-6 max-h-125 overflow-y-auto">
              <div v-html="store.previewResult.processed_html" class="prose prose-sm max-w-none"></div>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex justify-between gap-3">
            <button
              @click="store.setStep(1)"
              class="px-5 py-3 rounded-xl border border-border-soft text-text-secondary text-sm font-medium
                     hover:bg-surface-alt transition-all"
            >
              Volver a editar
            </button>

            <button
              @click="handleApply"
              :disabled="store.loading.apply"
              class="px-6 py-3 rounded-xl bg-success-dark text-white text-sm font-semibold
                     hover:bg-success-dark/90 transition-all duration-200 shadow-lg shadow-success-dark/20
                     flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg v-if="store.loading.apply" class="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              {{ store.loading.apply ? 'Guardando en Moodle...' : 'Guardar en Moodle' }}
            </button>
          </div>
        </div>

        <!-- Step 3: Done -->
        <div v-if="store.currentStep === 3" class="max-w-md mx-auto text-center py-8">
          <div class="w-20 h-20 rounded-full bg-pastel-mint flex items-center justify-center mx-auto mb-5">
            <svg xmlns="http://www.w3.org/2000/svg" class="w-10 h-10 text-success-dark" viewBox="0 0 24 24" fill="none"
                 stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
              <polyline points="22 4 12 14.01 9 11.01" />
            </svg>
          </div>
          <h2 class="text-xl font-bold text-text-primary mb-2">¡Cambios aplicados!</h2>
          <p class="text-sm text-text-muted mb-6">
            {{ applyResult?.total_replacements || 0 }} cambios fueron guardados exitosamente en Moodle.
          </p>
          <div class="flex justify-center gap-3">
            <button
              @click="goBack"
              class="px-5 py-2.5 rounded-xl border border-border-soft text-text-secondary text-sm font-medium
                     hover:bg-surface-alt transition-all"
            >
              Volver al Dashboard
            </button>
            <button
              @click="resetAndStay"
              class="px-5 py-2.5 rounded-xl bg-primary text-white text-sm font-medium
                     hover:bg-primary-dark transition-all"
            >
              Personalizar otro curso
            </button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useCourseStore } from '../stores/useCourseStore.js'
import StepProgress from '../components/StepProgress.vue'
import SetupForm from '../components/SetupForm.vue'

const route = useRoute()
const router = useRouter()
const store = useCourseStore()

const courseId = ref(Number(route.params.id))
const applyResult = ref(null)

const stepLabels = ['Configurar', 'Previsualizar', 'Completado']

function goBack() {
  store.resetForm()
  router.push({ name: 'dashboard' })
}

function truncate(str, len) {
  if (!str) return ''
  return str.length > len ? str.slice(0, len) + '...' : str
}

async function handlePreview() {
  const result = await store.requestPreview()
  if (result) {
    store.setStep(2)
  }
}

async function handleApply() {
  const result = await store.applyCustomization()
  if (result?.success) {
    applyResult.value = result
    store.setStep(3)
  }
}

function resetAndStay() {
  store.resetForm()
  router.push({ name: 'dashboard' })
}

onMounted(async () => {
  store.formData.course_id = courseId.value
  store.setStep(1)
  await store.scanSelectedCourse(courseId.value)
})
</script>
