<template>
  <div class="flex items-center gap-3">
    <div class="relative flex items-center justify-center w-10 h-10 rounded-xl"
         :class="statusBg">
      <!-- Spinner -->
      <svg v-if="status === 'loading'" class="animate-spin w-5 h-5" :class="statusIcon" viewBox="0 0 24 24" fill="none">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
        <path class="opacity-75" fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
      </svg>
      <!-- Connected -->
      <svg v-else-if="status === 'connected'" xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" :class="statusIcon"
           viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
        <polyline points="22 4 12 14.01 9 11.01" />
      </svg>
      <!-- Error -->
      <svg v-else xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" :class="statusIcon"
           viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10" /><line x1="15" y1="9" x2="9" y2="15" /><line x1="9" y1="9" x2="15" y2="15" />
      </svg>
    </div>

    <div>
      <p class="text-sm font-semibold" :class="statusText">{{ title }}</p>
      <p v-if="subtitle" class="text-xs text-text-muted">{{ subtitle }}</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: {
    type: String,
    default: 'loading', // 'loading' | 'connected' | 'error'
  },
  title: {
    type: String,
    default: '',
  },
  subtitle: {
    type: String,
    default: '',
  },
})

const statusBg = computed(() => ({
  'bg-pastel-yellow': props.status === 'loading',
  'bg-pastel-mint': props.status === 'connected',
  'bg-pastel-pink': props.status === 'error',
}))

const statusIcon = computed(() => ({
  'text-warning-dark': props.status === 'loading',
  'text-success-dark': props.status === 'connected',
  'text-danger-dark': props.status === 'error',
}))

const statusText = computed(() => ({
  'text-warning-dark': props.status === 'loading',
  'text-success-dark': props.status === 'connected',
  'text-danger-dark': props.status === 'error',
}))
</script>
