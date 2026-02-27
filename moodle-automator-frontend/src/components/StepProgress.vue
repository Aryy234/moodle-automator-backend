<template>
  <div class="flex items-center gap-2">
    <template v-for="(step, index) in steps" :key="index">
      <!-- Step circle -->
      <div class="flex items-center gap-2">
        <div
          class="flex items-center justify-center w-8 h-8 rounded-full text-xs font-bold transition-all duration-300"
          :class="{
            'bg-primary text-white': index + 1 < current,
            'bg-primary text-white ring-4 ring-primary/20': index + 1 === current,
            'bg-surface-alt text-text-muted border border-border-soft': index + 1 > current,
          }"
        >
          <!-- Check icon for completed -->
          <svg v-if="index + 1 < current" xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24"
               fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="20 6 9 17 4 12" />
          </svg>
          <span v-else>{{ index + 1 }}</span>
        </div>
        <span
          class="text-xs font-medium hidden sm:inline transition-colors duration-300"
          :class="index + 1 <= current ? 'text-text-primary' : 'text-text-muted'"
        >
          {{ step }}
        </span>
      </div>

      <!-- Connector line -->
      <div
        v-if="index < steps.length - 1"
        class="flex-1 h-0.5 rounded-full min-w-6 transition-colors duration-300"
        :class="index + 1 < current ? 'bg-primary' : 'bg-border-soft'"
      ></div>
    </template>
  </div>
</template>

<script setup>
defineProps({
  steps: {
    type: Array,
    required: true,
  },
  current: {
    type: Number,
    default: 1,
  },
})
</script>
