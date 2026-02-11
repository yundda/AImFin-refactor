<script setup>
import { ref, onMounted, watch } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { authApi } from '@/services/auth.api';
import BaseInput from '@/components/common/BaseInput.vue';
import BaseToast from '@/components/common/BaseToast.vue'; // Import BaseToast

const authStore = useAuthStore();

// 프로필 수정 폼 데이터
const profile = ref({
  name: '',
  email: ''
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

// 초기 데이터 로드 및 변경 감지
const initProfile = () => {
  if (authStore.user) {
    profile.value.name = authStore.user.nickname || '';
    profile.value.email = authStore.user.email || '';
  }
};

onMounted(initProfile);

// Auth Store의 user가 변경(새로고침 등)될 때 갱신
watch(() => authStore.user, initProfile, { deep: true });

// 비밀번호 수정 폼 데이터
const password = ref({
  current: '',
  new: '',
  confirm: ''
});

const updateProfile = async () => {
  try {
    const newNickname = profile.value.name.trim();
    if (!newNickname) return showToast('이름(닉네임)을 입력해주세요.', 'warning');

    await authApi.updateNickname(newNickname);
    
    // 스토어 상태 업데이트
    await authStore.fetchUser(); 
    
    showToast('프로필 정보가 수정되었습니다.', 'success');
  } catch (error) {
    console.error('Update failed:', error);
    showToast('수정 실패: ' + (error.response?.data?.detail || error.message), 'error');
  }
};

const updatePassword = () => {
  showToast('현재 비밀번호 변경 기능은 제공되지 않습니다 (Social Login User 등).', 'info');
  password.value = { current: '', new: '', confirm: '' };
};
</script>

<template>
  <div class="flex flex-col">
    <h2 class="text-xl font-bold text-[#283593] mb-6">계정 설정</h2>

    <!-- 
      ✅ 변경 1: items-start 제거 
      Grid의 기본 동작(stretch) 덕분에 두 카드의 높이가 자동으로 맞춰집니다.
      h-full을 제거하여 불필요하게 화면 끝까지 늘어나는 것을 방지했습니다.
    -->
    <div class="grid grid-cols-1 xl:grid-cols-2 gap-6">
      
      <!-- 1. 기본 정보 설정 -->
      <div class="bg-white rounded-2xl shadow-sm border border-gray-200 p-8 flex flex-col">
        <div class="flex items-center gap-3 mb-6 border-b border-gray-100 pb-4">
          <div class="w-8 h-8 bg-blue-50 rounded-lg flex items-center justify-center text-sm">👤</div>
          <h3 class="text-sm font-bold text-gray-600">기본 정보 수정</h3>
        </div>
        
        <!-- ✅ 변경 2: flex-1 제거 -->
        <form @submit.prevent="updateProfile" class="flex flex-col">
          <BaseInput 
            id="profile-name"
            label="이름 (닉네임)" 
            v-model="profile.name" 
            placeholder="이름을 입력하세요"
          />
          <BaseInput 
            id="profile-email"
            label="이메일" 
            type="email"
            v-model="profile.email" 
            placeholder="이메일을 입력하세요"
            readonly
            class="bg-gray-100 cursor-not-allowed text-gray-500"
          />
          
          <!-- ✅ 변경 3: mt-auto -> mt-8 (버튼을 바닥이 아닌 입력창 근처로) -->
          <div class="mt-8 text-right">
            <button type="submit" class="px-6 py-2.5 bg-[#283593] text-white text-sm font-bold rounded-lg hover:bg-[#1a237e] transition-colors shadow-md w-full sm:w-auto">
              정보 저장
            </button>
          </div>
        </form>
      </div>

      <!-- 2. 비밀번호 변경 -->
      <div class="bg-white rounded-2xl shadow-sm border border-gray-200 p-8 flex flex-col opacity-50 relative">
        <!-- Disabled Overlay -->
        <div class="absolute inset-0 z-10 bg-white/10 cursor-not-allowed" title="비밀번호 변경 미지원"></div>
        
        <div class="flex items-center gap-3 mb-6 border-b border-gray-100 pb-4">
          <div class="w-8 h-8 bg-purple-50 rounded-lg flex items-center justify-center text-sm">🔒</div>
          <h3 class="text-sm font-bold text-gray-600">비밀번호 보안</h3>
        </div>
        
        <form @submit.prevent="updatePassword" class="flex flex-col gap-1">
          <BaseInput 
            id="pw-current"
            label="현재 비밀번호" 
            type="password"
            v-model="password.current" 
            placeholder="현재 비밀번호"
            disabled
          />
          
          <BaseInput 
            id="pw-new"
            label="새 비밀번호" 
            type="password"
            v-model="password.new" 
            placeholder="영문, 숫자 포함 8자 이상"
            disabled
          />
          <BaseInput 
            id="pw-confirm"
            label="새 비밀번호 확인" 
            type="password"
            v-model="password.confirm" 
            placeholder="한 번 더 입력하세요"
            disabled
          />

          <!-- 버튼 위치 조정 -->
          <div class="mt-8 text-right">
            <button disabled type="submit" class="px-6 py-2.5 bg-[#283593] text-white text-sm font-bold rounded-lg hover:bg-[#1a237e] transition-colors shadow-md w-full sm:w-auto cursor-not-allowed">
              비밀번호 변경
            </button>
          </div>
        </form>
      </div>

    </div>
    <BaseToast
      :visible="toast.visible"
      :message="toast.message"
      :type="toast.type"
      @close="toast.visible = false"
    />
  </div>
</template>