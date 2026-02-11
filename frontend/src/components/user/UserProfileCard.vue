<script setup>
import { computed } from 'vue';
import { useAuthStore } from '@/stores/auth';

const props = defineProps({
  activeTab: {
    type: String,
    required: true
  }
});

const emit = defineEmits(['update:activeTab', 'logout']);
const authStore = useAuthStore();

// 메뉴 목록
const menus = [
  { id: 'account', icon: '⚙️', label: '계정 설정' },
  { id: 'propensity', icon: '📝', label: '투자 성향 설정' },
];

const userInitial = computed(() => {
  const name = authStore.user?.nickname || authStore.user?.email || 'U';
  return name.charAt(0).toUpperCase();
});

const userName = computed(() => {
  return authStore.user?.nickname || '닉네임 미설정';
});

const userEmail = computed(() => {
  return authStore.user?.email || '';
});
</script>

<template>
  <div class="bg-white rounded-2xl shadow-sm border border-gray-200 p-8 text-center h-full">
    <!-- 프로필 이미지 -->
    <div class="w-24 h-24 mx-auto bg-[#283593] rounded-full flex items-center justify-center text-white text-3xl font-bold mb-4 shadow-md">
      {{ userInitial }}
    </div>
    
    <!-- 이름 & 이메일 -->
    <h2 class="text-xl font-bold text-gray-900 mb-1">{{ userName }}</h2>
    <div v-if="authStore.user?.survey_profile_label" class="mb-2">
      <span class="inline-block px-2.5 py-0.5 bg-blue-50 text-[#283593] text-xs font-bold rounded-lg border border-blue-100">
        {{ authStore.user.survey_profile_label }}
      </span>
    </div>
    <p class="text-sm text-gray-400 mb-8">{{ userEmail }}</p>

    <!-- 메뉴 리스트 -->
    <div class="space-y-2 text-left">
      <button 
        v-for="menu in menus"
        :key="menu.id"
        @click="emit('update:activeTab', menu.id)"
        class="w-full flex items-center px-4 py-3 rounded-xl transition-all duration-200 text-sm font-medium"
        :class="activeTab === menu.id ? 'bg-gray-50 text-[#283593] font-bold' : 'text-gray-600 hover:bg-gray-50'"
      >
        <span class="mr-3">{{ menu.icon }}</span>
        {{ menu.label }}
      </button>

      <!-- 로그아웃 (빨간색 강조) -->
      <button 
        @click="emit('logout')"
        class="w-full flex items-center px-4 py-3 rounded-xl transition-all duration-200 text-sm font-medium text-red-400 hover:bg-red-50 hover:text-red-500 mt-4"
      >
        <span class="mr-3">👋</span>
        로그아웃
      </button>
    </div>
  </div>
</template>