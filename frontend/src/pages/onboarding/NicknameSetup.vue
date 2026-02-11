<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { authApi } from '@/services/auth.api';
import { useAuthStore } from '@/stores/auth'; // Auth Store 추가

const router = useRouter();
const authStore = useAuthStore();
const nickname = ref('');
const error = ref('');
const loading = ref(false);

const submitNickname = async () => {
  if (!nickname.value.trim()) {
    error.value = '닉네임을 입력해주세요.';
    return;
  }
  
  loading.value = true;
  error.value = '';

  try {
    // API call to set nickname
    await authApi.updateNickname(nickname.value);
    
    // 닉네임 설정 후 최신 유저 정보 다시 로드 (스토어 업데이트)
    await authStore.fetchUser();

    // Redirect to home on success
    router.push('/');
  } catch (err) {
    console.error('Failed to set nickname:', err);
    if (err.response && err.response.data && err.response.data.detail) { // detail로 수정
      error.value = err.response.data.detail;
    } else {
      error.value = '닉네임 설정 중 오류가 발생했습니다. 다시 시도해주세요.';
    }
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div class="min-h-screen flex flex-col justify-center items-center bg-gray-50 px-4">
    <div class="max-w-md w-full bg-white rounded-xl shadow-lg p-8">
      <div class="text-center mb-8">
        <h1 class="text-2xl font-bold text-gray-900 mb-2">환영합니다! 👋</h1>
        <p class="text-gray-600">AImFin에서 사용하실 닉네임을 설정해주세요.</p>
      </div>

      <form @submit.prevent="submitNickname" class="space-y-6">
        <div>
          <label for="nickname" class="block text-sm font-medium text-gray-700 mb-1">
            닉네임
          </label>
          <input
            id="nickname"
            v-model="nickname"
            type="text"
            placeholder="닉네임을 입력해주세요"
            class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-[#536dfe] focus:border-transparent outline-none transition-all"
            :class="{ 'border-red-500': error }"
            :disabled="loading"
          />
          <p v-if="error" class="mt-2 text-sm text-red-600 font-medium">
            {{ error }}
          </p>
        </div>

        <button
          type="submit"
          class="w-full bg-[#1a1a1a] text-white font-bold py-4 rounded-lg hover:bg-gray-800 transition-colors shadow-md disabled:opacity-50 disabled:cursor-not-allowed flex justify-center items-center"
          :disabled="loading"
        >
          <span v-if="loading" class="inline-block animate-spin rounded-full h-5 w-5 border-t-2 border-b-2 border-white mr-2"></span>
          {{ loading ? '처리중...' : '시작하기' }}
        </button>
      </form>
    </div>
  </div>
</template>
