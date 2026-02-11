<script setup>
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { authApi } from '@/services/auth.api';
import { useAuthStore } from "@/stores/auth";

const router = useRouter();
const currentStep = ref(0);
const answers = ref({});

// 질문 데이터 (백엔드 코드 매핑)
const questions = [
  // 1. Products (List)
  {
    id: 1, field: 'products', category: '투자 경험', type: 'multi',
    question: '투자 경험이 있는 상품을 모두 선택해주세요.',
    options: [
      { label: '예·적금', value: 'deposit' },
      { label: '채권', value: 'bond' },
      { label: '주식·ETF', value: 'stock_etf' },
      { label: '펀드', value: 'fund' },
      { label: '파생상품(ELS 등)', value: 'derivatives' },
      { label: '해외상품', value: 'overseas' }
    ]
  },
  // 2. History (Period & Freq) -> Maps to two fields
  {
    id: 2, category: '투자 기간',
    question: '지금까지의 투자 기간은 어떻게 되시나요?',
    options: [
      { label: '1년 미만 ', value: { period: '<1y', freq: 'none' } },
      { label: '1~3년', value: { period: '1-3y', freq: 'year_1_3' } },
      { label: '3년 이상', value: { period: '>=3y', freq: 'month_1plus' } }
    ]
  },
  // 3. Income
  { id: 3, field: 'income', category: '연 소득', question: '연 소득 수준은 어떻게 되시나요?', options: [
    { label: '3천만 미만', value: '<30m' },
    { label: '3천~7천', value: '30_70m' },
    { label: '7천~1억', value: '70_100m' },
    { label: '1억 이상', value: '>=100m' }
  ]},
  // 4. Wealth
  { id: 4, field: 'wealth', category: '자산 규모', question: '총 금융자산 규모는 어떻게 되시나요?', options: [
    { label: '5백만원 미만', value: '<50m' },
    { label: '5백만원 ~ 1천만원', value: '50_100m' },
    { label: '1천만원 ~ 5천만원', value: '100m_500m' },
    { label: '5천만원 이상', value: '>=500m' }
  ]},
  // 5. Debt Ratio (Detailed %)
  { id: 5, field: 'debt_ratio', category: '부채 비중', question: '자산 대비 부채 비중은 어떻게 되시나요?', options: [
    { label: '50% 이상', value: 'gte_50pct' },
    { label: '30~50%', value: '30_50pct' },
    { label: '10~30%', value: '10_30pct' },
    { label: '10% 미만', value: 'lt_10pct' }
  ]},
  // 6. Invest Share
  { id: 6, field: 'invest_share', category: '투자 비중', question: '전체 자산 중 투자금 비중은 어떻게 되시나요?', options: [
    { label: '50% 이상', value: '>=50pct' },
    { label: '30~50%', value: '30_50pct' },
    { label: '10~30%', value: '10_30pct' },
    { label: '10% 미만', value: '<10pct' }
  ]},
  // 7. Purpose (Refined)
  { id: 7, field: 'purpose', category: '투자 목적', question: '이번 투자의 주된 목적은 무엇인가요?', options: [
    { label: '자산 보존 및 안정적 수익 (예금+α)', value: 'preservation' },
    { label: '중위험 중수익 (예금 금리 2배 목표)', value: 'moderate' },
    { label: '적극적 수익 (시장 수익률 초과 목표)', value: 'active' },
    { label: '고수익 추구 (단기 트레이딩 및 공격적 투자)', value: 'aggressive' }
  ]},
  // 8. Target Return
  { id: 8, field: 'target_return', category: '목표 수익률', question: '기대하는 연 수익률은 어떻게 되시나요?', options: [
    { label: '3% 이하', value: '<=3' },
    { label: '3~5%', value: '3_5' },
    { label: '5~10%', value: '5_10' },
    { label: '10% 이상', value: '>=10' }
  ]},
  // 9. Loss Response
  { id: 9, field: 'loss_response', category: '손실 대응', question: '-10% 손실 시 어떻게 대응하실 건가요?', options: [
    { label: '전량 매도', value: 'sell_all' },
    { label: '일부 매도', value: 'sell_partial' },
    { label: '보유', value: 'hold' },
    { label: '추가 매수', value: 'buy_more' }
  ]},
  // 10. Volatility Feel
  { id: 10, field: 'volatility_feel', category: '변동성', question: '변동성이 큰 상품에 대한 생각은 어떻게 되시나요?', options: [
    { label: '매우 불안', value: 'very_anxious' },
    { label: '다소 불안', value: 'somewhat_anxious' },
    { label: '괜찮음', value: 'ok' },
    { label: '기회라고 생각', value: 'opportunity' }
  ]},
  // 11. Loss for Return
  { id: 11, field: 'loss_for_return', category: '위험 선호', question: '원금 손실 감수하고 고수익을 기대하는 편이신가요?', options: [
    { label: '전혀 아님', value: 'never' },
    { label: '아님', value: 'no' },
    { label: '그렇다', value: 'yes' },
    { label: '매우 그렇다', value: 'strong_yes' }
  ]},
  // 12. Horizon
  { id: 12, field: 'horizon', category: '투자 기간', question: '투자 가능한 기간은 얼마나 되시나요?', options: [
    { label: '1년 미만', value: '<1y' },
    { label: '1~3년', value: '1_3y' },
    { label: '3~5년', value: '3_5y' },
    { label: '5년 이상', value: '>=5y' }
  ]}
];

const progress = computed(() => ((currentStep.value + 1) / questions.length) * 100);
const currentQ = computed(() => questions[currentStep.value]);

const handleSelect = (option) => {
  if (currentQ.value.type === 'multi') {
    const currentAnswers = answers.value[currentQ.value.id] || [];
    // 옵션 자체가 아니라 옵션의 값(value)을 저장
    const idx = currentAnswers.findIndex(v => v === option.value);
    
    if (idx > -1) {
      currentAnswers.splice(idx, 1);
    } else {
      currentAnswers.push(option.value);
    }
    answers.value[currentQ.value.id] = currentAnswers;
  } else {
    // 단일 선택도 값(value)을 저장
    answers.value[currentQ.value.id] = option.value;
    nextStep();
  }
};

const isSelected = (option) => {
  const ans = answers.value[currentQ.value.id];
  if (currentQ.value.type === 'multi') {
    return Array.isArray(ans) && ans.includes(option.value);
  }
  // 객체(Q2)인 경우 참조 비교가 안될 수 있으므로 JSON 문자열 비교
  if (typeof option.value === 'object') {
     return JSON.stringify(ans) === JSON.stringify(option.value);
  }
  return ans === option.value;
};

const nextStep = () => {
  if (currentStep.value < questions.length - 1) currentStep.value++;
  else finishSurvey();
};

const prevStep = () => {
  if (currentStep.value > 0) currentStep.value--;
  else router.back();
};

const finishSurvey = async () => {
  try {
    // Payload 구성
    const payload = {};
    
    // 1. Products
    payload.products = answers.value[1] || [];
    
    // 2. History (Split field)
    const historyAns = answers.value[2];
    if (historyAns) {
      payload.history_period = historyAns.period;
      payload.history_freq = historyAns.freq;
    }
    
    // 3~12. Direct Mapping
    for (let i = 3; i <= 12; i++) {
       const q = questions[i-1]; // index is id-1
       if (q && q.field) {
         payload[q.field] = answers.value[q.id];
       }
    }
    
    // API Call
    const response = await authApi.saveSurvey(payload);
    const { profile, total_score } = response.data;
    
    // ✅ Store 상태 갱신 (전역 프로필 정보 업데이트)
    const authStore = useAuthStore();
    await authStore.fetchUser();
    
    // Map Backend Profile to Frontend Keys (Legacy Support for SurveyResult.vue)
    // Pass raw backend profile code to result page
    router.push({ 
      name: 'survey-result', 
      query: { type: profile, score: total_score } 
    });
    
  } catch (error) {
    console.error('Survey submission failed:', error);
    alert('설문 제출 중 오류가 발생했습니다: ' + (error.response?.data?.detail || error.message));
  }
};
</script>

<template>
  <div class="min-h-screen bg-white flex flex-col font-sans">
    <!-- 상단 진행바 -->
    <div class="px-6 py-6 sticky top-0 bg-white z-10">
      <div class="flex items-center mb-6">
        <button @click="prevStep" class="text-2xl text-gray-400 hover:text-black">←</button>
        <span class="ml-auto text-xs font-bold text-[#536dfe]">{{ currentStep + 1 }} / {{ questions.length }}</span>
      </div>
      <div class="h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div class="h-full bg-[#536dfe] transition-all duration-500 ease-out" :style="{ width: progress + '%' }"></div>
      </div>
    </div>

    <!-- 질문 컨텐츠 -->
    <div class="flex-1 px-6 pb-10 flex flex-col justify-center max-w-lg mx-auto w-full">
      <div class="mb-10">
        <span class="inline-block py-1 px-3 bg-blue-50 text-[#536dfe] text-xs font-bold rounded-full mb-4">Q{{ currentQ.id }}. {{ currentQ.category }}</span>
        <h2 class="text-2xl font-bold text-gray-900 leading-snug whitespace-pre-line">{{ currentQ.question }}</h2>
      </div>

      <div class="space-y-3">
        <button 
          v-for="(opt, idx) in currentQ.options" 
          :key="idx" 
          @click="handleSelect(opt)"
          class="w-full text-left p-5 rounded-2xl border transition-all active:scale-[0.98]"
          :class="[
            isSelected(opt)
              ? 'border-[#536dfe] bg-blue-50 text-[#536dfe] font-bold' 
              : 'border-gray-200 hover:border-[#536dfe] text-gray-700'
          ]"
        >
          {{ opt.label }}
        </button>
      </div>
      
      <button v-if="currentQ.type === 'multi'" @click="nextStep" class="mt-8 w-full py-4 bg-[#283593] text-white font-bold rounded-xl shadow-md hover:bg-[#4059e0]">
        다음
      </button>
    </div>
  </div>
</template>