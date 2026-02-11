<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();

// 현재 경로에 따라 상단 링크 텍스트와 이동 경로 결정
const navLink = computed(() => {
  if (route.path === '/auth/signup') {
    return { text: '로그인', to: '/auth/login' };
  }
  return { text: '계정 생성', to: '/auth/signup' };
});
</script>

<template>
  <div class="min-h-screen bg-gray-50 relative overflow-hidden flex flex-col">
    <!-- 1. 대각선 파란 배경 (CSS clip-path 활용) -->
    <div class="absolute top-0 left-0 w-full h-[60vh] bg-[#283593] z-0 custom-shape"></div>

    <!-- 2. 헤더 (로고 & 네비게이션) -->
    <header class="relative z-10 w-full max-w-6xl mx-auto px-6 py-6 flex justify-between items-center text-white">
      <h1 class="text-2xl font-bold tracking-wide">AImFIN</h1>
      <router-link :to="navLink.to" class="text-sm hover:underline opacity-90">
        {{ navLink.text }}
      </router-link>
    </header>

    <!-- 3. 메인 컨텐츠 (중앙 카드) -->
    <main class="relative z-10 flex-1 flex items-center justify-center px-4 py-10">
      <div class="bg-white rounded-lg shadow-xl w-full max-w-md p-8 md:p-12 fade-in-up">
        <!-- 슬롯을 통해 Login.vue 또는 Signup.vue 내용이 들어옴 -->
        <slot></slot>
      </div>
    </main>

    <!-- 4. 푸터 -->
    <footer class="relative z-10 py-6 text-center text-xs text-gray-400">
      &copy; 2025 - All Rights Reserved. AImFIN
    </footer>
  </div>
</template>

<style scoped>
/* 대각선 모양 만들기 */
.custom-shape {
  clip-path: polygon(0 0, 100% 0, 100% 70%, 0 85%);
}

/* 간단한 등장 애니메이션 */
.fade-in-up {
  animation: fadeInUp 0.5s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>