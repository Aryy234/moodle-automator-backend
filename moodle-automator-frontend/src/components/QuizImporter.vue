<template>
  <div class="bg-surface-card rounded-2xl border border-border-soft overflow-hidden">
    <!-- Header -->
    <div class="px-6 py-4 bg-linear-to-r from-accent/10 to-primary/5 border-b border-border-soft">
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 rounded-xl bg-accent/20 flex items-center justify-center shrink-0">
          <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 text-accent" viewBox="0 0 24 24" fill="none"
               stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
          </svg>
        </div>
        <div class="flex-1">
          <h3 class="text-sm font-bold text-text-primary">Importar Cuestionario</h3>
          <p class="text-[11px] text-text-muted">Sube preguntas a un quiz de Moodle en formato Aiken o XML</p>
        </div>
        <!-- Toggle -->
        <button @click="expanded = !expanded"
          class="w-8 h-8 rounded-lg flex items-center justify-center text-text-muted hover:text-text-primary hover:bg-surface-alt transition-all">
          <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 transition-transform duration-200"
               :class="expanded ? 'rotate-180' : ''" viewBox="0 0 24 24" fill="none"
               stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </button>
      </div>

      <!-- Mini progress -->
      <div v-if="expanded" class="mt-3 flex gap-1">
        <div v-for="s in totalSteps" :key="s"
          class="h-1 flex-1 rounded-full transition-colors duration-300"
          :class="s <= quizStep ? 'bg-accent' : 'bg-border-soft'" />
      </div>
    </div>

    <!-- Content -->
    <div v-if="expanded" class="p-6 space-y-6">

      <!-- ======== PASO 1: Seleccionar Cuestionario ======== -->
      <section v-if="quizStep >= 1">
        <StepHeader :step="1" :current="quizStep" title="Seleccionar cuestionario" @go="goToStep(1)" />

        <div v-if="quizStep === 1">
          <!-- Loading -->
          <div v-if="qStore.loading.quizzes" class="flex items-center gap-2 text-xs text-text-muted py-4">
            <Spinner class="w-4 h-4" /> Cargando cuestionarios...
          </div>

          <!-- Error -->
          <ErrorMsg v-else-if="qStore.errors.quizzes" :msg="qStore.errors.quizzes" @retry="loadQuizzes" />

          <!-- Lista -->
          <div v-else-if="qStore.hasQuizzes" class="space-y-2">
            <button
              v-for="q in qStore.quizzes" :key="q.coursemodule"
              @click="onSelectQuiz(q)"
              class="w-full text-left p-3 rounded-xl border transition-all duration-200"
              :class="qStore.selectedQuiz?.coursemodule === q.coursemodule
                ? 'border-accent bg-accent/5 ring-1 ring-accent/30'
                : 'border-border-soft hover:border-accent/40 hover:bg-surface-alt'"
            >
              <div class="flex items-center justify-between">
                <div class="min-w-0">
                  <p class="text-sm font-medium text-text-primary truncate">{{ q.name }}</p>
                  <p class="text-[11px] text-text-muted mt-0.5">
                    cmid: {{ q.coursemodule }}
                    <span v-if="q.timelimit"> · Tiempo: {{ formatSeconds(q.timelimit) }}</span>
                    <span v-if="q.grade"> · Nota máx: {{ q.grade }}</span>
                  </p>
                </div>
                <div v-if="qStore.selectedQuiz?.coursemodule === q.coursemodule"
                  class="w-5 h-5 rounded-full bg-accent flex items-center justify-center shrink-0">
                  <svg xmlns="http://www.w3.org/2000/svg" class="w-3 h-3 text-white" viewBox="0 0 24 24" fill="none"
                       stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                </div>
              </div>
            </button>
          </div>

          <!-- Vacío -->
          <p v-else class="text-xs text-text-muted py-4 text-center">
            No se encontraron cuestionarios en este curso.
          </p>

          <div v-if="qStore.selectedQuiz" class="flex justify-end mt-4">
            <BtnNext @click="advanceTo(2)" />
          </div>
        </div>

        <!-- Resumen colapsado -->
        <CompletedBadge v-else-if="qStore.selectedQuiz" :text="qStore.selectedQuizName" />
      </section>

      <!-- ======== PASO 2: Categoría de Preguntas ======== -->
      <section v-if="quizStep >= 2">
        <StepHeader :step="2" :current="quizStep" title="Categoría de preguntas" @go="goToStep(2)" />

        <div v-if="quizStep === 2">
          <!-- Loading -->
          <div v-if="qStore.loading.categories" class="flex items-center gap-2 text-xs text-text-muted py-4">
            <Spinner class="w-4 h-4" /> Cargando categorías...
          </div>

          <ErrorMsg v-else-if="qStore.errors.categories" :msg="qStore.errors.categories" @retry="loadCategories" />

          <div v-else>
            <!-- Listado existente -->
            <div v-if="qStore.hasCategories" class="space-y-2 mb-4">
              <button
                v-for="cat in qStore.categories" :key="cat.id"
                @click="qStore.selectCategory(cat)"
                class="w-full text-left p-3 rounded-xl border transition-all duration-200"
                :class="qStore.selectedCategory?.id === cat.id
                  ? 'border-accent bg-accent/5 ring-1 ring-accent/30'
                  : 'border-border-soft hover:border-accent/40 hover:bg-surface-alt'"
              >
                <div class="flex items-center justify-between">
                  <div class="min-w-0">
                    <p class="text-sm font-medium text-text-primary truncate">{{ cat.name }}</p>
                    <p class="text-[11px] text-text-muted">
                      {{ cat.questioncount }} preguntas · {{ cat.contextlevel === 'module' ? 'Quiz' : 'Curso' }}
                    </p>
                  </div>
                  <div v-if="qStore.selectedCategory?.id === cat.id"
                    class="w-5 h-5 rounded-full bg-accent flex items-center justify-center shrink-0">
                    <svg xmlns="http://www.w3.org/2000/svg" class="w-3 h-3 text-white" viewBox="0 0 24 24" fill="none"
                         stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                      <polyline points="20 6 9 17 4 12"/>
                    </svg>
                  </div>
                </div>
              </button>
            </div>

            <p v-else class="text-xs text-text-muted py-2">No hay categorías. Crea una nueva.</p>

            <!-- Crear nueva categoría -->
            <div class="p-4 rounded-xl border border-dashed border-border-soft bg-surface space-y-2">
              <p class="text-xs font-semibold text-text-secondary">Crear nueva categoría</p>
              <div class="flex gap-2">
                <input v-model="newCategoryName" type="text"
                  class="flex-1 px-3 py-2 rounded-lg border border-border-soft bg-surface-card text-sm
                         focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent transition-all"
                  placeholder="Nombre de la categoría" />
                <button @click="handleCreateCategory"
                  :disabled="!newCategoryName.trim() || qStore.loading.createCategory"
                  class="px-4 py-2 rounded-lg bg-accent text-white text-sm font-medium
                         hover:bg-accent/90 transition-all disabled:opacity-50 disabled:cursor-not-allowed
                         flex items-center gap-1.5 shrink-0">
                  <Spinner v-if="qStore.loading.createCategory" class="w-3.5 h-3.5" />
                  Crear
                </button>
              </div>
              <ErrorMsg v-if="qStore.errors.createCategory" :msg="qStore.errors.createCategory" compact />
            </div>

            <div v-if="qStore.selectedCategory" class="flex justify-end mt-4">
              <BtnNext @click="advanceTo(3)" />
            </div>
          </div>
        </div>

        <CompletedBadge v-else-if="qStore.selectedCategory" :text="qStore.selectedCategoryName" />
      </section>

      <!-- ======== PASO 3: Subir archivo y Preview ======== -->
      <section v-if="quizStep >= 3">
        <StepHeader :step="3" :current="quizStep" title="Subir preguntas" @go="goToStep(3)" />

        <div v-if="quizStep === 3">
          <!-- Formato -->
          <div class="flex gap-3 mb-4">
            <label v-for="fmt in ['aiken', 'xml']" :key="fmt"
              class="flex-1 flex items-center gap-2 p-3 rounded-xl border cursor-pointer transition-all"
              :class="qStore.fileFormat === fmt
                ? 'border-accent bg-accent/5 ring-1 ring-accent/30'
                : 'border-border-soft hover:border-accent/40'">
              <input type="radio" :value="fmt" v-model="qStore.fileFormat" class="accent-accent" />
              <div>
                <p class="text-sm font-medium text-text-primary">{{ fmt === 'aiken' ? 'Aiken (.txt)' : 'Moodle XML (.xml)' }}</p>
                <p class="text-[10px] text-text-muted">{{ fmt === 'aiken' ? 'Formato simple de texto plano' : 'Formato XML nativo de Moodle' }}</p>
              </div>
            </label>
          </div>

          <!-- File input -->
          <div class="relative">
            <input ref="fileInputRef" type="file"
              :accept="qStore.fileFormat === 'aiken' ? '.txt' : '.xml'"
              @change="onFileChange"
              class="hidden" />
            <button @click="$refs.fileInputRef.click()"
              class="w-full py-8 rounded-xl border-2 border-dashed transition-all duration-200 flex flex-col items-center gap-2"
              :class="qStore.file
                ? 'border-accent/40 bg-accent/5'
                : 'border-border-soft hover:border-accent/40 hover:bg-surface-alt'">
              <svg xmlns="http://www.w3.org/2000/svg" class="w-8 h-8 text-text-muted" viewBox="0 0 24 24" fill="none"
                   stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
              </svg>
              <p v-if="qStore.file" class="text-sm text-accent font-medium">{{ qStore.file.name }}</p>
              <p v-else class="text-sm text-text-muted">Haz clic para seleccionar archivo</p>
              <p class="text-[10px] text-text-muted">{{ qStore.fileFormat === 'aiken' ? '.txt' : '.xml' }}</p>
            </button>
          </div>

          <!-- Preview button -->
          <div v-if="qStore.file" class="mt-4">
            <button @click="handlePreviewFile"
              :disabled="qStore.loading.preview"
              class="w-full py-3 rounded-xl bg-pastel-blue text-accent text-sm font-semibold
                     hover:bg-pastel-blue/80 transition-all flex items-center justify-center gap-2
                     disabled:opacity-50 disabled:cursor-not-allowed">
              <Spinner v-if="qStore.loading.preview" class="w-4 h-4" />
              <svg v-else xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none"
                   stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
              </svg>
              {{ qStore.loading.preview ? 'Parseando...' : 'Previsualizar preguntas' }}
            </button>
            <ErrorMsg v-if="qStore.errors.preview" :msg="qStore.errors.preview" class="mt-2" />
          </div>

          <!-- Preview resultado -->
          <div v-if="qStore.hasPreview" class="mt-4 space-y-3">
            <div class="flex items-center gap-2 px-3 py-2 rounded-lg bg-pastel-mint">
              <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 text-success-dark" viewBox="0 0 24 24" fill="none"
                   stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
              <p class="text-xs font-semibold text-success-dark">
                {{ qStore.previewResult.total_questions_parsed }} preguntas detectadas
              </p>
            </div>

            <!-- Tabla de preguntas -->
            <div class="max-h-64 overflow-y-auto rounded-xl border border-border-soft">
              <table class="w-full text-xs">
                <thead class="bg-surface-alt sticky top-0">
                  <tr>
                    <th class="text-left px-3 py-2 font-semibold text-text-secondary">#</th>
                    <th class="text-left px-3 py-2 font-semibold text-text-secondary">Pregunta</th>
                    <th class="text-left px-3 py-2 font-semibold text-text-secondary">Tipo</th>
                    <th class="text-center px-3 py-2 font-semibold text-text-secondary">Opciones</th>
                    <th class="text-left px-3 py-2 font-semibold text-text-secondary">Respuesta</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(q, idx) in qStore.previewResult.questions" :key="idx"
                      class="border-t border-border-soft hover:bg-surface-alt/50">
                    <td class="px-3 py-2 text-text-muted">{{ idx + 1 }}</td>
                    <td class="px-3 py-2 text-text-primary max-w-50 truncate">{{ q.question_text }}</td>
                    <td class="px-3 py-2">
                      <span class="inline-flex px-1.5 py-0.5 rounded text-[10px] font-mono bg-pastel-purple text-primary">
                        {{ q.question_type }}
                      </span>
                    </td>
                    <td class="px-3 py-2 text-center text-text-muted">{{ q.options?.length || 0 }}</td>
                    <td class="px-3 py-2 text-success-dark font-medium truncate max-w-30">{{ q.correct_answer }}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div class="flex justify-end">
              <BtnNext @click="advanceTo(4)" label="Continuar" />
            </div>
          </div>
        </div>

        <CompletedBadge v-else-if="qStore.hasPreview"
          :text="`${qStore.previewResult.total_questions_parsed} preguntas`" />
      </section>

      <!-- ======== PASO 4: Configurar carga + tiempo ======== -->
      <section v-if="quizStep >= 4">
        <StepHeader :step="4" :current="quizStep" title="Configurar y guardar" @go="goToStep(4)" />

        <div v-if="quizStep === 4" class="space-y-5">
          <!-- Modo de carga -->
          <div>
            <p class="text-xs font-semibold text-text-secondary mb-2">Modo de carga de preguntas</p>
            <div class="flex gap-3">
              <label v-for="m in modeOptions" :key="m.value"
                class="flex-1 p-3 rounded-xl border cursor-pointer transition-all"
                :class="qStore.loadMode === m.value
                  ? 'border-accent bg-accent/5 ring-1 ring-accent/30'
                  : 'border-border-soft hover:border-accent/40'">
                <div class="flex items-center gap-2">
                  <input type="radio" :value="m.value" v-model="qStore.loadMode" class="accent-accent" />
                  <div>
                    <p class="text-sm font-medium text-text-primary">{{ m.label }}</p>
                    <p class="text-[10px] text-text-muted">{{ m.desc }}</p>
                  </div>
                </div>
              </label>
            </div>
          </div>

          <!-- Cantidad de preguntas aleatorias -->
          <div v-if="qStore.loadMode === 'random'"
            class="p-4 rounded-xl bg-surface border border-border-soft space-y-2">
            <label class="text-xs font-semibold text-text-secondary">Cantidad de preguntas aleatorias</label>
            <div class="flex items-center gap-3">
              <input type="range" v-model.number="qStore.numRandomQuestions"
                :min="1" :max="maxRandom"
                class="flex-1 accent-accent" />
              <span class="text-sm font-bold text-accent min-w-[3ch] text-right">{{ qStore.numRandomQuestions }}</span>
            </div>
            <p class="text-[10px] text-text-muted">
              De {{ maxRandom }} disponibles. Cada estudiante recibirá un subconjunto diferente.
            </p>
          </div>

          <!-- Tiempo límite -->
          <div>
            <p class="text-xs font-semibold text-text-secondary mb-2">Tiempo límite del cuestionario</p>
            <div class="grid grid-cols-3 sm:grid-cols-6 gap-2">
              <button v-for="opt in timeOptions" :key="opt.value"
                @click="qStore.timeLimit = opt.value"
                class="px-3 py-2 rounded-lg border text-xs font-medium transition-all"
                :class="qStore.timeLimit === opt.value
                  ? 'border-accent bg-accent/10 text-accent'
                  : 'border-border-soft text-text-muted hover:border-accent/40'">
                {{ opt.label }}
              </button>
            </div>
            <!-- Custom -->
            <div class="mt-2 flex items-center gap-2">
              <label class="text-[11px] text-text-muted shrink-0">Personalizado (min):</label>
              <input type="number" :value="Math.round(qStore.timeLimit / 60)"
                @input="qStore.timeLimit = ($event.target.value || 0) * 60"
                min="0" step="5"
                class="w-20 px-2 py-1.5 rounded-lg border border-border-soft bg-surface text-xs text-text-primary
                       focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent transition-all" />
              <span class="text-[11px] text-text-muted">= {{ formatSeconds(qStore.timeLimit) }}</span>
            </div>
          </div>

          <!-- Resumen final -->
          <div class="p-4 rounded-xl bg-pastel-blue/50 border border-accent/20 space-y-1">
            <p class="text-xs font-bold text-accent">Resumen</p>
            <ul class="text-[11px] text-text-secondary space-y-0.5">
              <li>Quiz: <strong>{{ qStore.selectedQuizName }}</strong></li>
              <li>Categoría: <strong>{{ qStore.selectedCategoryName }}</strong></li>
              <li>Preguntas: <strong>{{ qStore.previewResult?.total_questions_parsed || 0 }}</strong></li>
              <li>Modo: <strong>{{ qStore.loadMode === 'all' ? 'Todas' : `${qStore.numRandomQuestions} aleatorias` }}</strong></li>
              <li>Tiempo: <strong>{{ qStore.timeLimit > 0 ? formatSeconds(qStore.timeLimit) : 'Sin límite' }}</strong></li>
            </ul>
          </div>

          <!-- Errores -->
          <ErrorMsg v-if="qStore.errors.import" :msg="qStore.errors.import" />
          <ErrorMsg v-if="qStore.errors.configure" :msg="qStore.errors.configure" />
          <ErrorMsg v-if="qStore.errors.settings" :msg="qStore.errors.settings" />

          <!-- Resultado exitoso -->
          <div v-if="saveCompleted" class="p-4 rounded-xl bg-pastel-mint border border-success-dark/20">
            <div class="flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 text-success-dark" viewBox="0 0 24 24" fill="none"
                   stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
              </svg>
              <p class="text-sm font-semibold text-success-dark">¡Cuestionario configurado exitosamente!</p>
            </div>
            <p class="text-[11px] text-text-muted mt-1">
              {{ qStore.importResult?.total_questions_imported }} preguntas importadas
              <span v-if="qStore.configureResult?.questions_added">
                · {{ qStore.configureResult.questions_added }} cargadas al quiz
              </span>
              <span v-if="qStore.settingsResult?.time_limit_display">
                · Tiempo: {{ qStore.settingsResult.time_limit_display }}
              </span>
            </p>
          </div>

          <!-- Botón guardar -->
          <div class="flex justify-end">
            <button v-if="!saveCompleted"
              @click="handleSave"
              :disabled="qStore.isAnyLoading"
              class="px-6 py-3 rounded-xl bg-success-dark text-white text-sm font-semibold
                     hover:bg-success-dark/90 transition-all duration-200 shadow-lg shadow-success-dark/20
                     flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed">
              <Spinner v-if="qStore.isAnyLoading" class="w-4 h-4" />
              <svg v-else xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none"
                   stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>
                <polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/>
              </svg>
              {{ qStore.isAnyLoading ? 'Guardando...' : 'Guardar cuestionario' }}
            </button>
          </div>
        </div>

        <CompletedBadge v-else-if="saveCompleted" text="Cuestionario guardado" />
      </section>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, defineComponent, h, watch } from 'vue'
import { useQuizStore } from '../stores/useQuizStore.js'

const props = defineProps({
  courseId: { type: Number, required: true },
})

const qStore = useQuizStore()
const expanded = ref(false)
const quizStep = ref(1)
const newCategoryName = ref('')
const saveCompleted = ref(false)
const totalSteps = 4

// Mode options
const modeOptions = [
  { value: 'all', label: 'Todas', desc: 'Todos ven las mismas preguntas' },
  { value: 'random', label: 'Aleatorias', desc: 'Subconjunto distinto por alumno' },
]

// Time options
const timeOptions = [
  { value: 0, label: 'Sin límite' },
  { value: 900, label: '15 min' },
  { value: 1800, label: '30 min' },
  { value: 3600, label: '1 hora' },
  { value: 5400, label: '1h 30m' },
  { value: 7200, label: '2 horas' },
]

const maxRandom = computed(() => {
  return qStore.previewResult?.total_questions_parsed || 50
})

// ========== Sub-componentes inline ==========

const Spinner = defineComponent({
  setup() {
    return () => h('svg', {
      class: 'animate-spin text-current', viewBox: '0 0 24 24', fill: 'none',
    }, [
      h('circle', { class: 'opacity-25', cx: '12', cy: '12', r: '10', stroke: 'currentColor', 'stroke-width': '4' }),
      h('path', { class: 'opacity-75', fill: 'currentColor', d: 'M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z' }),
    ])
  },
})

const ErrorMsg = defineComponent({
  props: { msg: String, compact: Boolean },
  emits: ['retry'],
  setup(props, { emit }) {
    return () => h('div', {
      class: `flex items-center gap-2 px-3 py-2 rounded-xl text-xs text-danger-dark ${
        props.compact ? 'bg-transparent' : 'bg-pastel-pink border border-danger/20'
      }`,
    }, [
      h('svg', {
        xmlns: 'http://www.w3.org/2000/svg', class: 'w-3.5 h-3.5 shrink-0', viewBox: '0 0 24 24',
        fill: 'none', stroke: 'currentColor', 'stroke-width': '2',
        'stroke-linecap': 'round', 'stroke-linejoin': 'round',
      }, [
        h('circle', { cx: '12', cy: '12', r: '10' }),
        h('line', { x1: '12', y1: '8', x2: '12', y2: '12' }),
        h('line', { x1: '12', y1: '16', x2: '12.01', y2: '16' }),
      ]),
      h('span', { class: 'flex-1' }, props.msg),
    ])
  },
})

const StepHeader = defineComponent({
  props: { step: Number, current: Number, title: String },
  emits: ['go'],
  setup(props, { emit }) {
    return () => {
      const isDone = props.current > props.step
      const isCurrent = props.current === props.step
      return h('button', {
        class: `flex items-center gap-2.5 mb-3 w-full text-left group ${isDone ? 'cursor-pointer' : 'cursor-default'}`,
        onClick: () => isDone && emit('go'),
      }, [
        h('div', {
          class: `w-6 h-6 rounded-full flex items-center justify-center text-[11px] font-bold shrink-0 transition-colors ${
            isDone ? 'bg-accent text-white'
                   : isCurrent ? 'bg-accent/20 text-accent'
                               : 'bg-border-soft text-text-muted'
          }`,
        }, isDone
          ? h('svg', {
              xmlns: 'http://www.w3.org/2000/svg', class: 'w-3 h-3', viewBox: '0 0 24 24',
              fill: 'none', stroke: 'currentColor', 'stroke-width': '2.5',
              'stroke-linecap': 'round', 'stroke-linejoin': 'round',
            }, [h('polyline', { points: '20 6 9 17 4 12' })])
          : String(props.step)
        ),
        h('span', {
          class: `text-xs font-semibold transition-colors ${
            isCurrent ? 'text-text-primary' : isDone ? 'text-accent group-hover:underline' : 'text-text-muted'
          }`,
        }, props.title),
      ])
    }
  },
})

const CompletedBadge = defineComponent({
  props: { text: String },
  setup(props) {
    return () => h('div', {
      class: 'flex items-center gap-2 px-3 py-1.5 rounded-lg bg-accent/5 border border-accent/20 mb-1',
    }, [
      h('span', { class: 'text-[11px] text-accent font-medium truncate' }, props.text),
    ])
  },
})

const BtnNext = defineComponent({
  props: { label: { type: String, default: 'Siguiente' } },
  emits: ['click'],
  setup(props, { emit }) {
    return () => h('button', {
      class: 'px-5 py-2.5 rounded-xl bg-accent text-white text-sm font-semibold hover:bg-accent/90 transition-all flex items-center gap-1.5',
      onClick: () => emit('click'),
    }, [
      props.label,
      h('svg', {
        xmlns: 'http://www.w3.org/2000/svg', class: 'w-3.5 h-3.5', viewBox: '0 0 24 24',
        fill: 'none', stroke: 'currentColor', 'stroke-width': '2.5',
        'stroke-linecap': 'round', 'stroke-linejoin': 'round',
      }, [h('polyline', { points: '9 18 15 12 9 6' })]),
    ])
  },
})

// ========== Lógica ==========

function formatSeconds(s) {
  if (!s || s === 0) return 'Sin límite'
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  if (h > 0 && m > 0) return `${h}h ${m}m`
  if (h > 0) return `${h}h`
  return `${m}min`
}

function goToStep(step) {
  if (step < quizStep.value) quizStep.value = step
}

function advanceTo(step) {
  quizStep.value = step
}

async function loadQuizzes() {
  await qStore.fetchQuizzes(props.courseId)
}

async function loadCategories() {
  const cmid = qStore.selectedQuiz?.coursemodule
  await qStore.fetchCategories(props.courseId, cmid)
}

function onSelectQuiz(quiz) {
  qStore.selectQuiz(quiz)
}

async function handleCreateCategory() {
  const name = newCategoryName.value.trim()
  if (!name) return
  const cmid = qStore.selectedQuiz?.coursemodule
  await qStore.createCategory(props.courseId, name, cmid)
  if (!qStore.errors.createCategory) newCategoryName.value = ''
}

function onFileChange(e) {
  const f = e.target.files?.[0]
  if (f) {
    // Auto-detect format
    const ext = f.name.split('.').pop()?.toLowerCase()
    const format = ext === 'xml' ? 'xml' : 'aiken'
    qStore.setFile(f, format)
  }
}

async function handlePreviewFile() {
  await qStore.previewFile()
}

async function handleSave() {
  const result = await qStore.saveQuiz(props.courseId)
  if (result) saveCompleted.value = true
}

// Cargar quizzes al expandir por primera vez
const loaded = ref(false)

watch(expanded, async (val) => {
  if (val && !loaded.value) {
    loaded.value = true
    await loadQuizzes()
  }
})

// Cuando selecciona un quiz, cargar categorías
watch(() => qStore.selectedQuiz, async (quiz) => {
  if (quiz) {
    await loadCategories()
  }
})
</script>
