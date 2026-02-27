<template>
  <div class="space-y-6">
    <!-- Título y Descripción del curso -->
    <div v-if="scanResult?.course_title !== undefined || scanResult?.course_description !== undefined"
         class="bg-surface-card rounded-2xl border border-border-soft p-6">
      <h3 class="text-sm font-semibold text-text-primary mb-4 flex items-center gap-2">
        <span class="w-6 h-6 rounded-lg bg-pastel-blue flex items-center justify-center">
          <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5 text-accent" viewBox="0 0 24 24" fill="none"
               stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 20h9"/><path d="M16.376 3.622a1 1 0 0 1 3.002 3.002L7.368 18.635a2 2 0 0 1-.855.506l-2.872.838a.5.5 0 0 1-.62-.62l.838-2.872a2 2 0 0 1 .506-.854z"/>
          </svg>
        </span>
        Información del Curso
      </h3>

      <div class="space-y-4">
        <div v-if="scanResult?.course_title !== undefined">
          <label class="block text-xs font-medium text-text-secondary mb-1.5">Título del Curso</label>
          <input
            type="text"
            v-model="form.course_title"
            class="w-full px-4 py-2.5 rounded-xl border border-border-soft bg-surface text-sm text-text-primary
                   placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary
                   transition-all duration-200"
            placeholder="Nuevo título del curso"
          />
        </div>

        <div v-if="scanResult?.course_description !== undefined">
          <label class="block text-xs font-medium text-text-secondary mb-1.5">Descripción</label>
          <textarea
            v-model="form.course_description"
            rows="3"
            class="w-full px-4 py-2.5 rounded-xl border border-border-soft bg-surface text-sm text-text-primary
                   placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary
                   transition-all duration-200 resize-none"
            placeholder="Descripción del curso"
          ></textarea>
        </div>
      </div>
    </div>

    <!-- Placeholders (URLs editables) -->
    <div v-if="scanResult?.placeholders?.length > 0"
         class="bg-surface-card rounded-2xl border border-border-soft p-6">
      <h3 class="text-sm font-semibold text-text-primary mb-4 flex items-center gap-2">
        <span class="w-6 h-6 rounded-lg bg-pastel-purple flex items-center justify-center">
          <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5 text-primary" viewBox="0 0 24 24" fill="none"
               stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
            <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
          </svg>
        </span>
        Enlaces y Recursos
        <span class="ml-auto text-xs text-text-muted font-normal">
          {{ scanResult.total_placeholders }} encontrados
        </span>
      </h3>

      <div class="space-y-4">
        <div v-for="ph in scanResult.placeholders" :key="ph.placeholder_key">
          <label class="block text-xs font-medium text-text-secondary mb-1.5 flex items-center gap-2">
            <span
              class="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono uppercase tracking-wider"
              :class="ph.element_type === 'iframe' ? 'bg-pastel-sky text-accent' : 'bg-pastel-pink text-secondary'"
            >
              {{ ph.element_type === 'iframe' ? 'embed' : 'link' }}
            </span>
            {{ placeholderLabel(ph.placeholder_key) }}
          </label>
          <div class="relative">
            <input
              type="url"
              v-model="form[formKey(ph.placeholder_key)]"
              class="w-full px-4 py-2.5 rounded-xl border border-border-soft bg-surface text-sm text-text-primary
                     placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary
                     transition-all duration-200 pr-10"
              :placeholder="'https://...'"
            />
            <div class="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted">
              <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none"
                   stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"/><path d="M2 12h20"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
              </svg>
            </div>
          </div>
          <p v-if="ph.context_text" class="mt-1 text-[11px] text-text-muted">
            Texto visible: "{{ ph.context_text }}"
          </p>
        </div>
      </div>
    </div>

    <!-- Horario -->
    <div v-if="scanResult?.schedule_found"
         class="bg-surface-card rounded-2xl border border-border-soft p-6">
      <h3 class="text-sm font-semibold text-text-primary mb-4 flex items-center gap-2">
        <span class="w-6 h-6 rounded-lg bg-pastel-yellow flex items-center justify-center">
          <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5 text-warning-dark" viewBox="0 0 24 24" fill="none"
               stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
          </svg>
        </span>
        Cronograma / Horario
      </h3>

      <div class="space-y-3">
        <!-- Días -->
        <div>
          <label class="block text-xs font-medium text-text-secondary mb-1.5">Columnas de días (separar por coma)</label>
          <input
            type="text"
            v-model="scheduleDaysInput"
            class="w-full px-4 py-2.5 rounded-xl border border-border-soft bg-surface text-sm text-text-primary
                   placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary
                   transition-all duration-200"
            placeholder="Lunes, Martes, Miércoles, Jueves, Viernes"
          />
        </div>

        <!-- Entradas del horario -->
        <div v-for="(entry, idx) in scheduleEntries" :key="idx"
             class="p-4 rounded-xl bg-surface border border-border-soft space-y-2">
          <div class="flex items-center justify-between">
            <label class="text-xs font-medium text-text-secondary">Asignatura {{ idx + 1 }}</label>
            <button
              @click="removeScheduleEntry(idx)"
              class="text-danger-dark hover:text-danger-dark/80 transition-colors p-1"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none"
                   stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
              </svg>
            </button>
          </div>
          <input
            type="text"
            v-model="entry.subject_name"
            class="w-full px-3 py-2 rounded-lg border border-border-soft bg-surface-card text-sm
                   focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
            placeholder="Nombre de la asignatura"
          />
          <div class="grid grid-cols-2 gap-2">
            <div v-for="day in scheduleDays" :key="day">
              <label class="text-[10px] text-text-muted">{{ day }}</label>
              <input
                type="text"
                v-model="entry.days[day]"
                class="w-full px-2 py-1.5 rounded-lg border border-border-soft bg-surface-card text-xs
                       focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
                placeholder="18h00 – 19h00"
              />
            </div>
          </div>
        </div>

        <button
          @click="addScheduleEntry"
          class="w-full py-2 rounded-xl border-2 border-dashed border-border-soft text-text-muted text-xs font-medium
                 hover:border-primary hover:text-primary transition-all duration-200"
        >
          + Agregar asignatura
        </button>
      </div>
    </div>

    <!-- Bibliografía -->
    <div v-if="scanResult?.bibliography_found"
         class="bg-surface-card rounded-2xl border border-border-soft p-6">
      <h3 class="text-sm font-semibold text-text-primary mb-4 flex items-center gap-2">
        <span class="w-6 h-6 rounded-lg bg-pastel-mint flex items-center justify-center">
          <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5 text-success-dark" viewBox="0 0 24 24" fill="none"
               stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H19a1 1 0 0 1 1 1v18a1 1 0 0 1-1 1H6.5a1 1 0 0 1 0-5H20"/>
          </svg>
        </span>
        Bibliografía
      </h3>

      <div class="space-y-3">
        <div v-for="(entry, idx) in bibliographyEntries" :key="idx"
             class="p-4 rounded-xl bg-surface border border-border-soft space-y-2">
          <div class="flex items-center justify-between">
            <label class="text-xs font-medium text-text-secondary">Referencia {{ idx + 1 }}</label>
            <button
              @click="removeBibliographyEntry(idx)"
              class="text-danger-dark hover:text-danger-dark/80 transition-colors p-1"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none"
                   stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
              </svg>
            </button>
          </div>
          <input
            type="text"
            v-model="entry.text"
            class="w-full px-3 py-2 rounded-lg border border-border-soft bg-surface-card text-sm
                   focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
            placeholder="Texto de la referencia bibliográfica"
          />
          <input
            type="url"
            v-model="entry.url"
            class="w-full px-3 py-2 rounded-lg border border-border-soft bg-surface-card text-sm
                   focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
            placeholder="https://url-del-recurso.com"
          />
        </div>

        <button
          @click="addBibliographyEntry"
          class="w-full py-2 rounded-xl border-2 border-dashed border-border-soft text-text-muted text-xs font-medium
                 hover:border-primary hover:text-primary transition-all duration-200"
        >
          + Agregar referencia
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  form: {
    type: Object,
    required: true,
  },
  scanResult: {
    type: Object,
    default: null,
  },
})

// ========== Mapeador de labels ==========
const labels = {
  'video-introductorio': 'Video Introductorio',
  'unirse-clases': 'Enlace para Unirse a Clases',
  'url-grabaciones': 'URL de Grabaciones',
  'perfil-docente': 'Perfil del Docente',
  'silabo': 'Sílabo del Curso',
  'pea': 'PEA del Curso',
  'bibliografia': 'Bibliografía',
}

function placeholderLabel(key) {
  return labels[key] || key
}

function formKey(placeholderKey) {
  // Convertir placeholder_key a form key: 'video-introductorio' -> 'video_introductorio'
  return placeholderKey.replace(/-/g, '_')
}

// ========== Schedule ==========
const scheduleDaysInput = ref('Lunes, Martes, Miércoles, Jueves, Viernes')
const scheduleEntries = ref([])

const scheduleDays = computed(() =>
  scheduleDaysInput.value.split(',').map((d) => d.trim()).filter(Boolean)
)

function addScheduleEntry() {
  const days = {}
  scheduleDays.value.forEach((d) => (days[d] = ''))
  scheduleEntries.value.push({ subject_name: '', days })
}

function removeScheduleEntry(idx) {
  scheduleEntries.value.splice(idx, 1)
}

// Sincronizar con el form
watch(
  [scheduleEntries, scheduleDays],
  () => {
    if (scheduleEntries.value.length > 0) {
      props.form.schedule = {
        days_columns: scheduleDays.value,
        entries: scheduleEntries.value,
      }
    } else {
      props.form.schedule = null
    }
  },
  { deep: true }
)

// ========== Bibliography ==========
const bibliographyEntries = ref([])

function addBibliographyEntry() {
  bibliographyEntries.value.push({ text: '', url: '' })
}

function removeBibliographyEntry(idx) {
  bibliographyEntries.value.splice(idx, 1)
}

watch(
  bibliographyEntries,
  () => {
    if (bibliographyEntries.value.length > 0) {
      props.form.bibliography = { entries: bibliographyEntries.value }
    } else {
      props.form.bibliography = null
    }
  },
  { deep: true }
)
</script>
