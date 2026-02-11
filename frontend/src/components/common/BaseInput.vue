<script setup>
import { ref, computed } from 'vue';

// 이미지 파일 import (경로가 정확해야 합니다!)
import iconEyeOpen from '@/assets/images/eye-open.png';
import iconEyeClose from '@/assets/images/eye-close.png';

const props = defineProps({
  modelValue: { type: String, default: '' },
  label: { type: String, required: true },
  type: { type: String, default: 'text' },
  placeholder: { type: String, default: '' },
  id: { type: String, required: true }
});

const emit = defineEmits(['update:modelValue']);

const showPassword = ref(false);

const togglePassword = () => {
  showPassword.value = !showPassword.value;
};

// 비밀번호 보이기 여부에 따라 type 변경
const inputType = computed(() => {
  if (props.type === 'password' && showPassword.value) return 'text';
  return props.type;
});
</script>

<template>
  <div class="mb-5">
    <label :for="id" class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">
      {{ label }}
    </label>
    <div class="relative">
      <input
        :id="id"
        :type="inputType"
        :value="modelValue"
        @input="$emit('update:modelValue', $event.target.value)"
        :placeholder="placeholder"
        class="w-full border-b-2 border-gray-200 py-2 text-gray-900 placeholder-gray-300 focus:outline-none focus:border-[#536dfe] transition-colors bg-transparent pr-10"
      />
      
      <!-- 비밀번호 토글 버튼 -->
      <button
        v-if="type === 'password'"
        type="button"
        @click="togglePassword"
        class="absolute right-0 top-1/2 transform -translate-y-1/2 p-1 focus:outline-none opacity-50 hover:opacity-100 transition-opacity"
      >
        <!-- 보내주신 이미지 적용 -->
        <img 
          :src="showPassword ? iconEyeOpen : iconEyeClose" 
          alt="toggle password visibility" 
          class="w-6 h-6 object-contain"
        />
      </button>
    </div>
  </div>
</template>