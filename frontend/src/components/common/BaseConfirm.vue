<script setup>
import { computed } from 'vue';

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  title: {
    type: String,
    default: '확인'
  },
  message: {
    type: String,
    default: ''
  },
  confirmText: {
    type: String,
    default: '확인'
  },
  cancelText: {
    type: String,
    default: '취소'
  },
  type: {
    type: String, // 'danger', 'info'
    default: 'info'
  }
});

const emit = defineEmits(['confirm', 'cancel']);

const confirmButtonClass = computed(() => {
  if (props.type === 'danger') {
    return 'bg-red-500 hover:bg-red-600 text-white';
  }
  return 'bg-[#283593] hover:bg-[#1a237e] text-white';
});
</script>

<template>
  <Transition name="fade">
    <div v-if="visible" class="fixed inset-0 z-[10000] flex items-center justify-center p-4">
      <!-- Backdrop -->
      <div 
        class="absolute inset-0 bg-black/40 transition-opacity" 
        @click="emit('cancel')"
      ></div>

      <!-- Modal -->
      <div class="relative bg-white w-full max-w-sm rounded-2xl shadow-2xl p-6 transform transition-all scale-100">
        <h3 class="text-lg font-bold text-gray-900 mb-2">{{ title }}</h3>
        <p class="text-gray-600 mb-6 text-sm whitespace-pre-line">{{ message }}</p>
        
        <div class="flex gap-3 justify-end">
          <button 
            @click="emit('cancel')"
            class="px-4 py-2 border border-gray-200 rounded-lg text-gray-600 font-bold text-sm hover:bg-gray-50 transition-colors"
          >
            {{ cancelText }}
          </button>
          <button 
            @click="emit('confirm')"
            class="px-4 py-2 rounded-lg font-bold text-sm shadow-sm transition-colors"
            :class="confirmButtonClass"
          >
            {{ confirmText }}
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
