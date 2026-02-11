<script setup>
import { computed, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import BaseConfirm from '@/components/common/BaseConfirm.vue';

const router = useRouter();
const authStore = useAuthStore();

// Confirm State
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

// 프로필 매핑 정보
const profileMap = {
  CONSERVATIVE: {
    label: '안정형',
    icon: '�',
    desc: '원금 보존을 최우선으로 하며, 예금 수준의 안정적인 수익을 추구합니다.',
    features: ['낮은 위험 선호', '원금 보존 중심', '안전 자산(예금/채권) 위주', '단기 유동성 중시']
  },
  MODERATE_CONSERVATIVE: {
    label: '안정추구형',
    icon: '�',
    desc: '원금 손실을 최소화하면서 은행 이자보다 조금 높은 수익을 기대합니다.',
    features: ['제한적인 위험 수용', '채권/혼합형 펀드 선호', '중단기 자금 운용', '안정적 배당 수익 추구']
  },
  BALANCED: {
    label: '중립형',
    icon: '🦓',
    desc: '위험과 수익의 균형을 중요시하며, 적절한 자산 배분을 통해 안정적인 성장을 목표로 합니다.',
    features: ['위험/수익 밸런스 중시', '주식/채권 분산 투자', '시장 평균 수익 추구', '중장기 투자 시각']
  },
  GROWTH: {
    label: '적극투자형',
    icon: '�',
    desc: '시장의 변동성을 감내하면서 높은 수익을 추구하며, 주식형 자산 비중이 높습니다.',
    features: ['적극적인 수익 추구', '주식 위주 포트폴리오', '시장 변동성 수용', '장기 자본 이득 목표']
  },
  AGGRESSIVE: {
    label: '공격투자형',
    icon: '🦁',
    desc: '원금 손실 위험을 감수하더라도 시장 평균을 크게 상회하는 고수익을 지향합니다.',
    features: ['매우 높은 위험 수용', '고위험/고수익 자산 선호', '레버리지/파생상품 관심', '단기 고수익/장기 대박 추구']
  }
};

const hasSurvey = computed(() => !!authStore.user?.survey_profile);
const currentProfile = computed(() => {
  const code = authStore.user?.survey_profile; // e.g., 'BALANCED'
  return profileMap[code] || profileMap.BALANCED; // fallback
});

// 프로필 라벨 (백엔드 데이터 우선, 없으면 매핑값)
const profileLabel = computed(() => authStore.user?.survey_profile_label || currentProfile.value.label);

const retakeSurvey = () => {
  showConfirm({
    title: '투자 성향 재진단',
    message: '기존 성향 정보가 초기화됩니다.\n다시 진행하시겠습니까?',
    type: 'info',
    onConfirm: () => {
      router.push('/survey');
    }
  });
};
</script>

<template>
  <div class="space-y-6">
    <h2 class="text-xl font-bold text-gray-900">투자 성향 설정</h2>

    <!-- 설문 결과가 있는 경우 -->
    <div v-if="hasSurvey">
      <!-- 현재 성향 카드 -->
      <div class="bg-white rounded-2xl shadow-sm border border-gray-200 p-8">
        <h3 class="text-sm font-bold text-gray-500 mb-6">현재 투자 성향</h3>
        
        <div class="flex items-center gap-6">
          <div class="w-16 h-16 bg-blue-50 rounded-2xl flex items-center justify-center text-3xl">
            {{ currentProfile.icon }}
          </div>
          <div>
            <span class="inline-block px-3 py-1 bg-[#283593] text-white text-xs font-bold rounded-full mb-2">
              {{ profileLabel }}
            </span>
            <p class="text-gray-600 text-sm">
              {{ currentProfile.desc }}
            </p>
          </div>
        </div>
      </div>

      <!-- 성향 특징 리스트 -->
      <div class="bg-white rounded-2xl shadow-sm border border-gray-200 p-8">
        <h3 class="text-sm font-bold text-gray-500 mb-6">투자 성향 특징</h3>
        <ul class="space-y-3">
          <li v-for="(feat, idx) in currentProfile.features" :key="idx" class="flex items-center text-sm text-gray-700">
            <span class="w-5 h-5 bg-green-100 text-green-600 rounded-full flex items-center justify-center text-xs mr-3">✔</span>
            {{ feat }}
          </li>
        </ul>

        <!-- 재진단 버튼 -->
        <button 
          @click="retakeSurvey"
          class="w-full mt-8 py-4 bg-[#283593] text-white font-bold rounded-xl hover:bg-[#1a237e] transition-colors shadow-md"
        >
          투자 성향 재진단하기
        </button>
      </div>
    </div>

    <!-- 설문 결과가 없는 경우 -->
    <div v-else class="bg-white rounded-2xl shadow-sm border border-gray-200 p-12 text-center">
      <div class="text-5xl mb-6">📝</div>
      <h3 class="text-lg font-bold text-gray-900 mb-2">아직 투자 성향 진단을 하지 않으셨네요!</h3>
      <p class="text-gray-500 mb-8">나에게 딱 맞는 포트폴리오를 받으려면 먼저 투자 성향을 진단해야 합니다.</p>
      <button 
        @click="router.push('/survey')"
        class="px-8 py-4 bg-[#283593] text-white font-bold rounded-xl hover:bg-[#1a237e] transition-colors shadow-md"
      >
        투자 성향 진단 시작하기
      </button>
    </div>
    <!-- Confirm Dialog -->
    <BaseConfirm
      :visible="confirmDialog.visible"
      :title="confirmDialog.title"
      :message="confirmDialog.message"
      :type="confirmDialog.type"
      confirm-text="재진단 시작"
      @confirm="handleConfirmAction"
      @cancel="confirmDialog.visible = false"
    />
  </div>
</template>