<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth'; // Auth Store
import DefaultLayout from '@/layouts/DefaultLayout.vue';
import UserProfileCard from '@/components/user/UserProfileCard.vue';
import MyPortfolioStatus from '@/components/user/MyPortfolioStatus.vue';
import MyPropensity from '@/components/user/MyPropensity.vue';
import MyAccountSettings from '@/components/user/MyAccountSettings.vue';
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

// activeTab 기본값을 'dashboard'로 설정하여 처음엔 포트폴리오 현황이 보이게 함
const activeTab = ref('dashboard'); 

onMounted(async () => {
  try {
    await authStore.fetchUser();
  } catch (error) {
    // 인증 실패 시 로그인 페이지로 이동 (선택적)
    // router.push('/auth/login');
  }
});

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
  <DefaultLayout>
    <div class="max-w-6xl mx-auto px-6 py-12">
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-8 items-stretch">
        
        <!-- 왼쪽: 프로필 사이드바 -->
        <div class="lg:col-span-4 h-full">
          <UserProfileCard 
            v-model:activeTab="activeTab" 
            @logout="handleLogout"
          />
        </div>

        <!-- 오른쪽: 컨텐츠 영역 -->
        <div class="lg:col-span-8 h-full">
          
          <!-- 1. 투자 성향 설정 -->
          <div v-if="activeTab === 'propensity'" class="fade-in h-full">
            <MyPropensity />
          </div>

          <!-- 2. 계정 설정 (✅ 추가됨) -->
          <div v-else-if="activeTab === 'account'" class="fade-in h-full">
            <MyAccountSettings />
          </div>

          <!-- 3. 기본 화면 (포트폴리오 현황) -->
          <div v-else class="fade-in h-full">
            <MyPortfolioStatus />
          </div>

        </div>

      </div>
    </div>
    <!-- Logout Confirm Dialog -->
    <BaseConfirm
      :visible="confirmDialog.visible"
      :title="confirmDialog.title"
      :message="confirmDialog.message"
      :type="confirmDialog.type"
      confirm-text="로그아웃"
      @confirm="handleConfirmAction"
      @cancel="confirmDialog.visible = false"
    />
  </DefaultLayout>
</template>

<style scoped>
/* 부드러운 전환 효과 */
.fade-in {
  animation: fadeIn 0.3s ease-out;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(5px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>