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

        <!-- Formulario con guardados inline -->
        <SetupForm :form="store.formData" :scanResult="store.scanResult" />
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useCourseStore } from '../stores/useCourseStore.js'
import SetupForm from '../components/SetupForm.vue'

const route = useRoute()
const router = useRouter()
const store = useCourseStore()

const courseId = ref(Number(route.params.id))

function goBack() {
  store.resetForm()
  router.push({ name: 'dashboard' })
}

onMounted(async () => {
  store.formData.course_id = courseId.value
  store.setStep(1)
  await store.scanSelectedCourse(courseId.value)
})
</script>
