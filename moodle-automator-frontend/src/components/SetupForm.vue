<template>
  <div class="space-y-6">
    <!-- Número ID del curso -->
    <div class="bg-surface-card rounded-2xl border border-border-soft p-6">
      <h3 class="text-sm font-semibold text-text-primary mb-4 flex items-center gap-2">
        <span class="w-6 h-6 rounded-lg bg-pastel-peach flex items-center justify-center">
          <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5 text-warning-dark" viewBox="0 0 24 24" fill="none"
               stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/>
            <line x1="7" y1="7" x2="7.01" y2="7"/>
          </svg>
        </span>
        Número ID del Curso
      </h3>
      <input
        type="text"
        v-model="form.idnumber"
        class="w-full px-4 py-2.5 rounded-xl border border-border-soft bg-surface text-sm text-text-primary
               placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary
               transition-all duration-200"
        placeholder="Ej: MAT-2025-A"
      />
      <p class="mt-1.5 text-[11px] text-text-muted">
        Identificador interno del curso en Moodle (Administración del curso → Número ID del curso).
        Se aplicará al guardar. Déjalo vacío si no deseas modificarlo.
      </p>
    </div>


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

        <div v-for="(entry, idx) in scheduleEntries" :key="idx"
             class="p-4 rounded-xl bg-surface border border-border-soft space-y-2">
          <div class="flex items-center justify-between">
            <label class="text-xs font-medium text-text-secondary">Asignatura {{ idx + 1 }}</label>
            <button @click="removeScheduleEntry(idx)" class="text-danger-dark hover:text-danger-dark/80 transition-colors p-1">
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
            <button @click="removeBibliographyEntry(idx)" class="text-danger-dark hover:text-danger-dark/80 transition-colors p-1">
              <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none"
                   stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
              </svg>
            </button>
          </div>
          <input type="text" v-model="entry.text"
            class="w-full px-3 py-2 rounded-lg border border-border-soft bg-surface-card text-sm
                   focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
            placeholder="Texto de la referencia bibliográfica" />
          <input type="url" v-model="entry.url"
            class="w-full px-3 py-2 rounded-lg border border-border-soft bg-surface-card text-sm
                   focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
            placeholder="https://url-del-recurso.com" />
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

    <!-- ====================================================== -->
    <!--  SEMANA 1 — BLOQUES DE CONTENIDO                       -->
    <!-- ====================================================== -->
    <div class="bg-surface-card rounded-2xl border border-border-soft overflow-hidden">
      <!-- Header de la sección -->
      <div class="px-6 py-4 bg-gradient-to-r from-primary/10 to-accent/5 border-b border-border-soft">
        <div class="flex items-center gap-3 mb-3">
          <div class="w-8 h-8 rounded-xl bg-primary/20 flex items-center justify-center shrink-0">
            <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 text-primary" viewBox="0 0 24 24" fill="none"
                 stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/>
            </svg>
          </div>
          <div>
            <h3 class="text-sm font-bold text-text-primary">Bloques de Contenido</h3>
            <p class="text-[11px] text-text-muted">Crea labels independientes en Moodle para cada bloque</p>
          </div>
        </div>

        <!-- Selector de sección destino -->
        <div>
          <label class="block text-xs font-semibold text-text-secondary mb-1.5 flex items-center gap-1">
            <svg xmlns="http://www.w3.org/2000/svg" class="w-3 h-3" viewBox="0 0 24 24" fill="none"
                 stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
            </svg>
            Sección de Moodle donde se crearán los bloques
            <span class="text-danger-dark font-bold">*</span>
          </label>
          <select
            v-model="selectedSectionId"
            @change="onSectionChange"
            class="w-full px-3 py-2 rounded-xl border border-border-soft bg-surface text-sm text-text-primary
                   focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
          >
            <option value="" disabled>— Selecciona una sección —</option>
            <option v-for="sec in store.courseSections" :key="sec.id" :value="sec.id">
              {{ sec.section === 0 ? '📋 General' : `📅 Semana ${sec.section}` }}
              {{ sec.name && sec.name !== `Sección ${sec.section}` ? `— ${sec.name}` : '' }}
            </option>
          </select>
          <p v-if="!selectedSectionId" class="text-[11px] text-danger-dark mt-1">
            Requerido para crear los bloques de Presentaciones, Lectura y Videos.
          </p>
        </div>
      </div>

      <div class="p-6 space-y-8">

        <!-- ========== BLOQUE PRESENTACIONES ========== -->
        <div>
          <div class="flex items-center gap-2 mb-4">
            <span class="w-7 h-7 rounded-lg bg-pastel-blue flex items-center justify-center text-base">📊</span>
            <div>
              <h4 class="text-sm font-semibold text-text-primary">Presentaciones</h4>
              <p class="text-[11px] text-text-muted">Cada presentación genera su propio iframe en Moodle</p>
            </div>
          </div>

          <div class="space-y-3">
            <div
              v-for="(pres, idx) in presentations" :key="idx"
              class="p-4 rounded-xl bg-surface border border-border-soft"
            >
              <div class="flex items-center justify-between mb-3">
                <span class="text-xs font-semibold text-text-secondary">Presentación {{ idx + 1 }}</span>
                <button @click="removePresentation(idx)"
                  class="text-xs text-danger-dark hover:text-danger-dark/70 transition-colors flex items-center gap-1 p-1">
                  <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none"
                       stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
                  </svg>
                  Eliminar
                </button>
              </div>
              <div class="space-y-2">
                <input type="text" v-model="pres.title"
                  class="w-full px-3 py-2 rounded-lg border border-border-soft bg-surface-card text-sm
                         focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
                  placeholder="Título de la presentación" />
                <input type="url" v-model="pres.url"
                  class="w-full px-3 py-2 rounded-lg border border-border-soft bg-surface-card text-sm
                         focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
                  placeholder="Link de la presentación (Canva, Slides, etc.)" />
              </div>
            </div>

            <button @click="addPresentation"
              class="w-full py-2.5 rounded-xl border-2 border-dashed border-border-soft text-text-muted text-xs font-medium
                     hover:border-primary hover:text-primary transition-all duration-200 flex items-center justify-center gap-1">
              <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none"
                   stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/>
              </svg>
              Agregar presentación
            </button>
          </div>

          <!-- Objetivo de aprendizaje (opcional) -->
          <div class="mt-3">
            <label class="block text-xs font-medium text-text-secondary mb-1.5">
              Objetivo de aprendizaje <span class="text-text-muted font-normal">(opcional)</span>
            </label>
            <textarea v-model="form.presentation_objective" rows="2"
              class="w-full px-3 py-2 rounded-xl border border-border-soft bg-surface text-sm text-text-primary
                     placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary
                     transition-all duration-200 resize-none"
              placeholder="Objetivo de aprendizaje de esta semana...">
            </textarea>
          </div>
        </div>

        <hr class="border-border-soft" />

        <!-- ========== BLOQUE LECTURA ========== -->
        <div>
          <div class="flex items-center gap-2 mb-4">
            <span class="w-7 h-7 rounded-lg bg-pastel-mint flex items-center justify-center text-base">📖</span>
            <div>
              <h4 class="text-sm font-semibold text-text-primary">Lectura</h4>
              <p class="text-[11px] text-text-muted">Una lectura principal + lecturas sugeridas adicionales</p>
            </div>
          </div>

          <!-- Lectura Principal -->
          <div class="mb-4">
            <p class="text-xs font-semibold text-text-secondary mb-2 uppercase tracking-wider">Lectura Principal</p>
            <div class="p-4 rounded-xl bg-surface border border-border-soft space-y-2">
              <input type="text" v-model="mainReading.title"
                class="w-full px-3 py-2 rounded-lg border border-border-soft bg-surface-card text-sm
                       focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
                placeholder="Título del libro" />
              <input type="text" v-model="mainReading.author"
                class="w-full px-3 py-2 rounded-lg border border-border-soft bg-surface-card text-sm
                       focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
                placeholder="Autor" />
              <input type="url" v-model="mainReading.url"
                class="w-full px-3 py-2 rounded-lg border border-border-soft bg-surface-card text-sm
                       focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
                placeholder="Link del libro" />
              <textarea v-model="mainReading.summary" rows="2"
                class="w-full px-3 py-2 rounded-lg border border-border-soft bg-surface-card text-sm resize-none
                       focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
                placeholder="Resumen breve del libro...">
              </textarea>
            </div>
          </div>

          <!-- Lecturas Sugeridas -->
          <div class="mb-4">
            <p class="text-xs font-semibold text-text-secondary mb-2 uppercase tracking-wider">Lecturas Sugeridas</p>
            <div class="space-y-3">
              <div v-for="(book, idx) in suggestedReadings" :key="idx"
                   class="p-4 rounded-xl bg-surface border border-border-soft">
                <div class="flex items-center justify-between mb-3">
                  <span class="text-xs font-semibold text-text-secondary">Libro sugerido {{ idx + 1 }}</span>
                  <button @click="removeSuggestedReading(idx)"
                    class="text-xs text-danger-dark hover:text-danger-dark/70 transition-colors flex items-center gap-1 p-1">
                    <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none"
                         stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
                    </svg>
                    Eliminar
                  </button>
                </div>
                <div class="space-y-2">
                  <input type="text" v-model="book.title"
                    class="w-full px-3 py-2 rounded-lg border border-border-soft bg-surface-card text-sm
                           focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
                    placeholder="Título del libro sugerido" />
                  <input type="text" v-model="book.author"
                    class="w-full px-3 py-2 rounded-lg border border-border-soft bg-surface-card text-sm
                           focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
                    placeholder="Autor" />
                  <input type="url" v-model="book.url"
                    class="w-full px-3 py-2 rounded-lg border border-border-soft bg-surface-card text-sm
                           focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
                    placeholder="Link del libro sugerido" />
                </div>
              </div>

              <button @click="addSuggestedReading"
                class="w-full py-2.5 rounded-xl border-2 border-dashed border-border-soft text-text-muted text-xs font-medium
                       hover:border-primary hover:text-primary transition-all duration-200 flex items-center justify-center gap-1">
                <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none"
                     stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/>
                </svg>
                Agregar lectura sugerida
              </button>
            </div>
          </div>

          <!-- Personalización de etiquetas (colapsable) -->
          <div class="border border-border-soft rounded-xl overflow-hidden">
            <button @click="showReadingLabels = !showReadingLabels"
              class="w-full px-4 py-3 flex items-center justify-between text-xs font-medium text-text-secondary
                     bg-surface hover:bg-surface-alt transition-colors">
              <span class="flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none"
                     stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <line x1="4" y1="9" x2="20" y2="9"/><line x1="4" y1="15" x2="20" y2="15"/>
                  <line x1="10" y1="3" x2="8" y2="21"/><line x1="16" y1="3" x2="14" y2="21"/>
                </svg>
                Personalizar etiquetas del bloque
              </span>
              <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5 transition-transform"
                   :class="showReadingLabels ? 'rotate-180' : ''" viewBox="0 0 24 24" fill="none"
                   stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="6 9 12 15 18 9"/>
              </svg>
            </button>
            <div v-if="showReadingLabels" class="p-4 bg-surface-card grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label class="block text-[10px] font-medium text-text-muted mb-1">Texto botón collapse</label>
                <input type="text" v-model="form.reading_collapse_label"
                  class="w-full px-3 py-1.5 rounded-lg border border-border-soft bg-surface text-xs
                         focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
                  placeholder='Default: "Lectura"' />
              </div>
              <div>
                <label class="block text-[10px] font-medium text-text-muted mb-1">Título interno (h4)</label>
                <input type="text" v-model="form.reading_section_title"
                  class="w-full px-3 py-1.5 rounded-lg border border-border-soft bg-surface text-xs
                         focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
                  placeholder='Default: "Lectura principal"' />
              </div>
              <div>
                <label class="block text-[10px] font-medium text-text-muted mb-1">Texto botón ver lectura</label>
                <input type="text" v-model="form.reading_button_text"
                  class="w-full px-3 py-1.5 rounded-lg border border-border-soft bg-surface text-xs
                         focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
                  placeholder='Default: "Ver lectura"' />
              </div>
              <div>
                <label class="block text-[10px] font-medium text-text-muted mb-1">Título lecturas sugeridas</label>
                <input type="text" v-model="form.reading_suggested_title"
                  class="w-full px-3 py-1.5 rounded-lg border border-border-soft bg-surface text-xs
                         focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
                  placeholder='Default: "Lecturas sugeridas"' />
              </div>
            </div>
          </div>
        </div>

        <hr class="border-border-soft" />

        <!-- ========== BLOQUE VIDEOS ========== -->
        <div>
          <div class="flex items-center gap-2 mb-4">
            <span class="w-7 h-7 rounded-lg bg-pastel-pink flex items-center justify-center text-base">🎥</span>
            <div>
              <h4 class="text-sm font-semibold text-text-primary">Videos</h4>
              <p class="text-[11px] text-text-muted">Cada video genera su propio iframe en Moodle</p>
            </div>
          </div>

          <div class="space-y-3">
            <div v-for="(vid, idx) in videos" :key="idx"
                 class="p-4 rounded-xl bg-surface border border-border-soft">
              <div class="flex items-center justify-between mb-3">
                <span class="text-xs font-semibold text-text-secondary">Video {{ idx + 1 }}</span>
                <button @click="removeVideo(idx)"
                  class="text-xs text-danger-dark hover:text-danger-dark/70 transition-colors flex items-center gap-1 p-1">
                  <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none"
                       stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
                  </svg>
                  Eliminar
                </button>
              </div>
              <div class="space-y-2">
                <input type="text" v-model="vid.title"
                  class="w-full px-3 py-2 rounded-lg border border-border-soft bg-surface-card text-sm
                         focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
                  placeholder="Título del video" />
                <input type="url" v-model="vid.url"
                  class="w-full px-3 py-2 rounded-lg border border-border-soft bg-surface-card text-sm
                         focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
                  placeholder="Link del video (Drive, YouTube, etc.)" />
              </div>
            </div>

            <button @click="addVideo"
              class="w-full py-2.5 rounded-xl border-2 border-dashed border-border-soft text-text-muted text-xs font-medium
                     hover:border-primary hover:text-primary transition-all duration-200 flex items-center justify-center gap-1">
              <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none"
                   stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/>
              </svg>
              Agregar video
            </button>
          </div>

          <!-- Resumen de videos (opcional) -->
          <div class="mt-3">
            <label class="block text-xs font-medium text-text-secondary mb-1.5">
              Texto resumen de videos <span class="text-text-muted font-normal">(opcional)</span>
            </label>
            <textarea v-model="form.videos_summary" rows="2"
              class="w-full px-3 py-2 rounded-xl border border-border-soft bg-surface text-sm text-text-primary
                     placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary
                     transition-all duration-200 resize-none"
              placeholder="Descripción breve de los videos de esta semana...">
            </textarea>
          </div>
        </div>

      </div><!-- /p-6 -->
    </div><!-- /card Semana 1 -->

  </div>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useCourseStore } from '../stores/useCourseStore.js'

const store = useCourseStore()

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

// ========== Selector de sección ==========
const selectedSectionId = ref('')

function onSectionChange() {
  const sec = store.courseSections.find((s) => s.id === selectedSectionId.value)
  if (sec) {
    props.form.section_id = sec.id
    props.form.section_number = sec.section
  }
}

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

// ========== Presentaciones ==========
const presentations = ref([])

function addPresentation() {
  presentations.value.push({ title: '', url: '' })
}

function removePresentation(idx) {
  presentations.value.splice(idx, 1)
}

watch(presentations, () => {
  props.form.presentations = presentations.value.filter((p) => p.title || p.url)
}, { deep: true })

// ========== Lectura ==========
const mainReading = reactive({ title: '', author: '', url: '', summary: '' })
const suggestedReadings = ref([])
const showReadingLabels = ref(false)

function addSuggestedReading() {
  suggestedReadings.value.push({ title: '', author: '', url: '' })
}

function removeSuggestedReading(idx) {
  suggestedReadings.value.splice(idx, 1)
}

watch(
  [() => ({ ...mainReading }), suggestedReadings],
  () => {
    const hasMain = mainReading.title || mainReading.author || mainReading.url
    props.form.main_reading = hasMain ? { ...mainReading } : null
    props.form.suggested_readings = suggestedReadings.value.filter((b) => b.title || b.url)
  },
  { deep: true }
)

// ========== Videos ==========
const videos = ref([])

function addVideo() {
  videos.value.push({ title: '', url: '' })
}

function removeVideo(idx) {
  videos.value.splice(idx, 1)
}

watch(videos, () => {
  props.form.videos = videos.value.filter((v) => v.title || v.url)
}, { deep: true })
</script>
