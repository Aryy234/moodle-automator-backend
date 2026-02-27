<template>
  <div
    class="group relative bg-surface-card rounded-2xl border border-border-soft p-5 cursor-pointer
           transition-all duration-300 hover:shadow-lg hover:shadow-primary/10 hover:-translate-y-1"
    :class="{ 'ring-2 ring-primary border-primary': isSelected }"
    @click="$emit('select', course)"
  >
    <!-- Badge de estado -->
    <div class="absolute top-3 right-3">
      <span
        v-if="course.visible === 1"
        class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-pastel-mint text-success-dark"
      >
        <span class="w-1.5 h-1.5 rounded-full bg-success-dark"></span>
        Visible
      </span>
      <span
        v-else
        class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-pastel-peach text-warning-dark"
      >
        <span class="w-1.5 h-1.5 rounded-full bg-warning-dark"></span>
        Oculto
      </span>
    </div>

    <!-- Icono decorativo -->
    <div class="w-10 h-10 rounded-xl flex items-center justify-center mb-3"
         :class="isSelected ? 'bg-primary text-white' : 'bg-pastel-purple text-primary'">
      <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 24 24" fill="none"
           stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H19a1 1 0 0 1 1 1v18a1 1 0 0 1-1 1H6.5a1 1 0 0 1 0-5H20" />
      </svg>
    </div>

    <!-- Info -->
    <h3 class="text-sm font-semibold text-text-primary leading-snug mb-1 pr-14 line-clamp-2">
      {{ course.fullname }}
    </h3>
    <p class="text-xs text-text-muted font-mono">
      ID: {{ course.id }} · {{ course.shortname }}
    </p>

    <!-- Indicador de selección -->
    <div
      v-if="isSelected"
      class="absolute bottom-3 right-3 w-6 h-6 rounded-full bg-primary flex items-center justify-center"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5 text-white" viewBox="0 0 24 24"
           fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="20 6 9 17 4 12" />
      </svg>
    </div>
  </div>
</template>

<script setup>
defineProps({
  course: {
    type: Object,
    required: true,
  },
  isSelected: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['select'])
</script>
