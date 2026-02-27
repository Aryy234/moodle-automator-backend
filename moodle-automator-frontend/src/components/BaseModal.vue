<template>
  <div v-if="visible"
       class="fixed inset-0 z-50 flex items-center justify-center p-4"
       @click.self="$emit('close')">
    <!-- Backdrop -->
    <div class="absolute inset-0 bg-text-primary/20 backdrop-blur-sm"></div>

    <!-- Modal content -->
    <div class="relative bg-surface-card rounded-2xl border border-border-soft shadow-2xl shadow-primary/10
                w-full max-w-2xl max-h-[85vh] overflow-hidden flex flex-col animate-in">
      <!-- Header -->
      <div class="flex items-center justify-between px-6 py-4 border-b border-border-soft">
        <h2 class="text-base font-semibold text-text-primary">{{ title }}</h2>
        <button
          @click="$emit('close')"
          class="w-8 h-8 rounded-lg flex items-center justify-center text-text-muted
                 hover:bg-surface-alt hover:text-text-primary transition-all"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none"
               stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>

      <!-- Body -->
      <div class="flex-1 overflow-y-auto p-6">
        <slot />
      </div>

      <!-- Footer -->
      <div v-if="$slots.footer" class="px-6 py-4 border-t border-border-soft bg-surface-alt/50">
        <slot name="footer" />
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  title: {
    type: String,
    default: '',
  },
})

defineEmits(['close'])
</script>

<style scoped>
.animate-in {
  animation: slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(16px) scale(0.98);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}
</style>
