<script setup>
import { onMounted, onUnmounted, watch } from 'vue';

const props = defineProps({
  message: {
    type: String,
    required: true
  },
  type: {
    type: String, // 'success', 'error', 'info', 'warning'
    default: 'success'
  },
  duration: {
    type: Number,
    default: 1500
  },
  visible: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['close']);

const bgColor = {
  success: 'bg-[#283593]',
  error: 'bg-red-500',
  info: 'bg-gray-800',
  warning: 'bg-orange-500',
  'light-success': 'bg-white'
};

const textColor = {
  success: 'text-white',
  error: 'text-white',
  info: 'text-white',
  warning: 'text-white',
  'light-success': 'text-[#283593]'
};

const icon = {
  success: '✓',
  error: '!',
  info: 'i',
  warning: '⚠',
  'light-success': '✓'
};

let timer = null;

const startTimer = () => {
  if (timer) clearTimeout(timer);
  if (props.duration > 0) {
    timer = setTimeout(() => {
      emit('close');
    }, props.duration);
  }
};

watch([() => props.visible, () => props.message], ([newVisible, newMessage]) => {
  if (newVisible) {
    startTimer();
  } else {
    if (timer) clearTimeout(timer);
  }
});

onMounted(() => {
  if (props.visible) {
    startTimer();
  }
});

onUnmounted(() => {
  if (timer) clearTimeout(timer);
});
</script>

<template>
  <Transition name="toast">
    <div
      v-if="visible"
      class="fixed top-24 left-1/2 transform -translate-x-1/2 z-[9999] flex items-center gap-3 px-6 py-3.5 rounded-full shadow-lg font-medium min-w-[300px] justify-center bg-opacity-95 border border-white/20"
      :class="[bgColor[type] || bgColor.success, textColor[type] || textColor.success]"
    >
      <span class="rounded-full w-5 h-5 flex items-center justify-center text-xs font-bold"
        :class="type === 'light-success' ? 'bg-[#283593]/10 text-[#283593]' : 'bg-white/20 text-white'"
      >
        {{ icon[type] || icon.success }}
      </span>
      <span>{{ message }}</span>
    </div>
  </Transition>
</template>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: opacity 0.3s cubic-bezier(0.18, 0.89, 0.32, 1.28), transform 0.3s cubic-bezier(0.18, 0.89, 0.32, 1.28);
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translate(-50%, -20px) scale(0.9);
}

.toast-enter-to,
.toast-leave-from {
  opacity: 1;
  transform: translate(-50%, 0) scale(1);
}
</style>
