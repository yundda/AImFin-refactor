<script setup>
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { ref } from 'vue';
import BaseConfirm from '@/components/common/BaseConfirm.vue';

const router = useRouter();
const authStore = useAuthStore();

const confirmDialog = ref({
  visible: false,
  title: '',
  message: '',
  type: 'info',
  onConfirm: null
});

const showConfirm = ({ title, message, type = 'info', onConfirm }) => {
  confirmDialog.value = {
    visible: true,
    title,
    message,
    type,
    onConfirm
  };
};

const handleConfirmAction = () => {
  if (confirmDialog.value.onConfirm) {
    confirmDialog.value.onConfirm();
  }
  confirmDialog.value.visible = false;
};

const handleLogout = () => {
  showConfirm({
    title: '로그아웃',
    message: '로그아웃 하시겠습니까?',
    type: 'danger',
    onConfirm: async () => {
      await authStore.logout();
      router.push('/auth/login');
    }
  });
};
</script>

<template>
  <div class="min-h-screen bg-[#F5F7FA] flex flex-col font-sans">
    <!-- 헤더 (네비게이션) -->
    <nav class="bg-[#283593] border-b border-[#1a237e] h-16 flex items-center justify-between px-6 sticky top-0 z-50 shadow-md">
      <!-- 1. 로고: 클릭 시 메인('/')으로 이동 -->
      <router-link to="/" class="text-xl font-bold text-white tracking-wide">AImFIN</router-link>
      
      <!-- 우측 메뉴 -->
      <div class="flex items-center gap-6">

        
        <!-- 3. 마이페이지: 클릭 시 '/user/mypage'로 이동 -->
        <router-link to="/user/mypage" class="text-sm font-medium text-blue-100 hover:text-white transition-colors">
          마이페이지
        </router-link>
        
        <button @click="handleLogout" class="text-sm text-blue-200 hover:text-white transition-colors">
          로그아웃
        </button>
      </div>
    </nav>

    <!-- 페이지 컨텐츠 -->
    <main class="flex-1 w-full relative">
      <slot></slot>
    </main>

    <!-- 푸터 -->
    <footer class="py-6 text-center text-[10px] text-gray-400 mt-auto">
      &copy; 2025 - All Rights Reserved. AImFIN
    </footer>
    <BaseConfirm
      :visible="confirmDialog.visible"
      :title="confirmDialog.title"
      :message="confirmDialog.message"
      :type="confirmDialog.type"
      confirm-text="로그아웃"
      @confirm="handleConfirmAction"
      @cancel="confirmDialog.visible = false"
    />
  </div>
</template>