<script setup lang="ts">
import { ref } from 'vue';
import AuthLayout from '@/layouts/AuthLayout.vue';
import BaseInput from '@/components/common/BaseInput.vue';
import SocialLoginButtons from '@/components/auth/SocialLoginButtons.vue';
import BaseToast from '@/components/common/BaseToast.vue'; // Import BaseToast

import { useRouter } from 'vue-router';
import { authApi } from '@/services/auth.api';

const router = useRouter();

const form = ref({
  email: '',
  password: '',
  agreeTerms: false
});

// Toast State
const toast = ref({
  visible: false,
  message: '',
  type: 'success'
});

const showToast = (message, type = 'success') => {
  toast.value = { visible: true, message, type };
};

const handleSignup = async () => {
  // 비밀번호 유효성 검사: 8자 이상, 영문자 및 숫자 포함
  const isValidPassword = form.value.password.length >= 8 && 
                          /[A-Za-z]/.test(form.value.password) && 
                          /\d/.test(form.value.password);

  if (!isValidPassword) {
    showToast('비밀번호는 영문자와 숫자를 모두 포함하여 8자 이상이어야 합니다.', 'warning');
    return;
  }

  if (!form.value.agreeTerms) {
    showToast('개인정보 수집에 동의해주세요.', 'warning');
    return;
  }
  
  try {
    await authApi.signup({
      email: form.value.email,
      password: form.value.password
    });
    
    showToast('회원가입이 완료되었습니다. 로그인 페이지로 이동합니다.', 'light-success');
    
    // 토스트를 보여준 뒤 이동
    setTimeout(() => {
      router.push('/auth/login');
    }, 1500);
    
  } catch (error) {
    console.error('Signup failed:', error);
    // DRF returns object with field errors
    const errorData = error.response?.data || {};
    let msg = '회원가입 실패';
    
    if (Object.keys(errorData).length > 0) {
      const details = Object.entries(errorData)
        .map(([key, msgs]) => `${key}: ${Array.isArray(msgs) ? msgs.join(', ') : msgs}`)
        .join('\n');
      msg += `:\n${details}`;
    } else {
      msg += `: ${error.message}`;
    }
    
    showToast(msg, 'error');
  }
};
</script>

<template>
  <AuthLayout>
    <div class="text-center mb-10">
      <h2 class="text-3xl font-bold text-gray-900 mb-2">계정 생성</h2>
      <p class="text-xs text-gray-400">스마트한 AI 포트폴리오 비교 분석 서비스 AImFIN</p>
    </div>

    <form @submit.prevent="handleSignup">
      <BaseInput
        id="signup-email"
        label="이메일"
        v-model="form.email"
        placeholder="johndoe@example.com"
      />

      <BaseInput
        id="signup-password"
        label="비밀번호"
        type="password"
        v-model="form.password"
        placeholder="**********"
      />

      <div class="mb-8 text-xs">
        <label class="flex items-center text-gray-500 cursor-pointer">
          <input type="checkbox" v-model="form.agreeTerms" class="mr-2 rounded text-[#536dfe] focus:ring-[#536dfe]" />
          <span class="border-b border-gray-400">AImFIN의 개인정보 수집에 동의합니다.</span>
        </label>
      </div>

      <button
        type="submit"
        class="w-full bg-[#1a1a1a] text-white font-bold py-4 rounded hover:bg-gray-800 transition-colors shadow-lg"
      >
        계정 생성하기
      </button>
    </form>

    <SocialLoginButtons mode="signup" />
    <BaseToast
      :visible="toast.visible"
      :message="toast.message"
      :type="toast.type"
      @close="toast.visible = false"
    />
  </AuthLayout>
</template>