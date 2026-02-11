<script setup>
import { ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { authApi } from '@/services/auth.api'; // Import added
import DefaultLayout from '@/layouts/DefaultLayout.vue';

const route = useRoute();
const router = useRouter();
const type = route.query.type; 
// ✅ 금액 포맷팅을 위한 Computed Property
import { computed } from 'vue';

const amount = ref(''); // 초기값은 빈 문자열 (입력 유도)
const selectedAssets = ref([]);
const allowAiAdditions = ref(false); // [NEW] AI 자동 확장 허용 여부

const formattedAmount = computed({
  get: () => {
    if (!amount.value) return '';
    return Number(amount.value).toLocaleString();
  },
  set: (val) => {
    // 콤마 제거 후 숫자만 남김
    const num = val.replace(/,/g, '');
    if (isNaN(num)) return;
    amount.value = num;
  }
});

const assetOptions = [
  { id: 'STOCKS_KR', label: '국내주식', icon: '🇰🇷' },
  { id: 'STOCKS_GLB', label: '해외주식', icon: '🇺🇸' },
  { id: 'BONDS_KR', label: '국내채권', icon: '📜' },
  { id: 'BONDS_GLB', label: '해외채권', icon: '🌐' },
  { id: 'ALTERNATIVES', label: '대체투자', icon: '💎' },
  { id: 'FUNDS', label: '펀드', icon: '📊' },
  { id: 'CASH', label: '현금성자산', icon: '💰' }
];

// ✅ 투자 기간 상태 및 옵션
const horizon = ref('');
const horizonOptions = [
  { id: 'LT_1Y', label: '1년 이하' },
  { id: 'Y_1_3', label: '1~3년' },
  { id: 'Y_3_5', label: '3~5년' },
  { id: 'GTE_5Y', label: '5년 이상' }
];

// ✅ 금액 더하기 함수 추가
const addAmount = (val) => {
  // 현재 값이 없거나 숫자가 아니면 0으로 취급하고 더함
  const current = Number(amount.value) || 0;
  amount.value = current + val;
};

const toggleAsset = (id) => {
  if (selectedAssets.value.includes(id)) {
    selectedAssets.value = selectedAssets.value.filter(a => a !== id);
  } else {
    selectedAssets.value.push(id);
  }
};

const showLowProductWarning = ref(false); // [NEW] 경고 모달 상태

const confirmAutoAdditions = () => {
    allowAiAdditions.value = true;
    showLowProductWarning.value = false;
    generatePortfolio();
};

const generatePortfolio = async () => {
  if (!amount.value || amount.value <= 0) return alert('투자 금액을 입력해주세요.');
  if (!horizon.value) return alert('투자 기간을 선택해주세요.');
  if (selectedAssets.value.length === 0) return alert('최소 1개 이상의 선호 상품을 선택해주세요.');

  // [NEW] 3개 미만 선택 시 경고 (AI 자동 허용이 안 되어 있는 경우)
  if (selectedAssets.value.length < 3 && !allowAiAdditions.value) {
    showLowProductWarning.value = true;
    return;
  }

  try {
    const payload = {
      amount_krw: Number(amount.value),
      horizon_code: horizon.value,
      include_products: selectedAssets.value
    };

    // API 호출
    // authApi is already imported at the top level
    
    const response = await authApi.savePreference(payload);
    
    // 성공 시 결과 페이지로 이동 (쿼리 파라미터는 UI용, 실제 데이터는 백엔드에 저장됨)
    router.push({ 
      name: 'portfolio-result', 
      query: { 
        type, 
        amount: amount.value,
        horizon: horizon.value, 
        assets: JSON.stringify(selectedAssets.value),
        allow_ai_additions: allowAiAdditions.value
      } 
    });
  } catch (error) {
    console.error('Preference save failed:', error);
    alert('저장 중 오류가 발생했습니다.');
  }
};
</script>

<template>
  <DefaultLayout>
    <div class="max-w-2xl mx-auto px-6 py-16">
      
      <div class="bg-white rounded-3xl shadow-lg border border-gray-100 p-10 relative overflow-hidden">
        <!-- 배경 장식 -->
        <div class="absolute top-0 left-0 w-full h-2 bg-gray-100">
          <div class="h-full bg-[#283593] w-full"></div> 
        </div>

        <div class="text-sm font-bold text-gray-400 mb-8 tracking-widest text-center">포트폴리오 조건 설정</div>

        <!-- 1. 투자 금액 -->
        <div class="mb-10">
          <label class="block text-lg font-bold text-gray-900 mb-4"> 투자 가능 금액은 얼마인가요?</label>
          <div class="relative">
            <input 
              type="text" 
              v-model="formattedAmount" 
              placeholder="금액 입력 (예: 1,000,000)"
              class="w-full p-4 pl-4 pr-12 text-xl font-bold border-2 border-gray-200 rounded-xl focus:border-[#283593] focus:outline-none transition-colors"
            />
            <span class="absolute right-6 top-1/2 -translate-y-1/2 text-gray-500 font-bold">원</span>
          </div>
          
          <!-- ✅ 금액 추가 버튼 (클릭 시 addAmount 실행) -->
          <div class="flex gap-2 mt-3 overflow-x-auto pb-2 no-scrollbar">
            <button @click="addAmount(1000000)" class="px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm font-medium text-gray-600 hover:bg-[#283593] hover:text-white hover:border-[#283593] transition-colors whitespace-nowrap active:scale-95">
              +100만
            </button>
            <button @click="addAmount(5000000)" class="px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm font-medium text-gray-600 hover:bg-[#283593] hover:text-white hover:border-[#283593] transition-colors whitespace-nowrap active:scale-95">
              +500만
            </button>
            <button @click="addAmount(10000000)" class="px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm font-medium text-gray-600 hover:bg-[#283593] hover:text-white hover:border-[#283593] transition-colors whitespace-nowrap active:scale-95">
              +1,000만
            </button>
            <button @click="amount = ''" class="px-4 py-2 bg-red-50 border border-red-100 rounded-lg text-sm font-medium text-red-500 hover:bg-red-100 transition-colors whitespace-nowrap active:scale-95">
              초기화
            </button>
          </div>
        </div>

        <!-- 2. 투자 기간 -->
        <div class="mb-10">
          <label class="block text-lg font-bold text-gray-900 mb-4"> 투자 기간은 어떻게 되시나요?</label>
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <button 
              v-for="opt in horizonOptions" 
              :key="opt.id"
              @click="horizon = opt.id"
              class="py-4 rounded-xl border-2 font-bold transition-all hover:border-[#283593] hover:text-[#283593] active:scale-95"
              :class="horizon === opt.id ? 'border-[#283593] bg-blue-50 text-[#283593]' : 'border-gray-200 text-gray-500'"
            >
              {{ opt.label }}
            </button>
          </div>
        </div>

        <!-- 3. 선호 상품 -->
        <div class="mb-12">
          <label class="block text-lg font-bold text-gray-900 mb-2"> 포트폴리오에 꼭 담고 싶은 자산 유형은?</label>
          <p class="text-sm text-gray-500 mb-4 font-medium">
            (3개 이상 선택해야 AI가 원활하게 분석을 진행할 수 있어요.)
          </p>
          <div class="grid grid-cols-2 sm:grid-cols-3 gap-3">
            <button 
              v-for="opt in assetOptions" 
              :key="opt.id"
              @click="toggleAsset(opt.id)"
              class="p-4 rounded-xl border-2 transition-all flex flex-col items-center justify-center gap-2 h-28 hover:shadow-md active:scale-95"
              :class="selectedAssets.includes(opt.id) ? 'border-[#283593] bg-blue-50 text-[#283593] shadow-sm' : 'border-gray-100 hover:border-gray-300 text-gray-500'"
            >
              <span class="text-3xl">{{ opt.icon }}</span>
              <span class="font-bold text-sm">{{ opt.label }}</span>
            </button>
          </div>
        </div>

        <!-- 4. AI 확장 옵션 -->
        <div class="mb-10">
            <div class="flex items-center gap-3 bg-blue-50 p-4 rounded-xl border border-blue-100">
                <input 
                  type="checkbox" 
                  id="ai-additions-create" 
                  v-model="allowAiAdditions"
                  class="w-5 h-5 text-[#283593] rounded border-gray-300 focus:ring-[#283593]"
                >
                <label for="ai-additions-create" class="flex-1 cursor-pointer select-none">
                    <div class="font-bold text-gray-900">AI 자산 자동 배분 허용</div>
                    <div class="text-xs text-gray-500">선택하신 자산 외에 AI가 추가로 자산을 추가하여 자동 배분합니다.</div>
                </label>
            </div>
        </div>

        <button 
          @click="generatePortfolio"
          class="w-full py-5 bg-[#283593] text-white text-lg font-bold rounded-2xl shadow-lg hover:bg-[#1a237e] transition-transform hover:-translate-y-1 active:translate-y-0"
        >
          AI 포트폴리오 생성하기 
        </button>

      </div>
    </div>

    <!-- [NEW] 상품 개수 부족 경고 모달 -->
    <div v-if="showLowProductWarning" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
      <div class="bg-white rounded-2xl w-full max-w-sm p-8 shadow-2xl relative animate-fade-in-up text-center">
        <h2 class="text-xl font-bold mb-4 text-gray-900">AI 자동 배분 허용</h2>
        
        <p class="text-gray-600 mb-8 leading-relaxed text-sm">
          상품을 3개 이상 선택하지 않으면 AI가 포트폴리오를 생성하는데 어려움을 겪을 수 있어요.<br><br>
          <span class="font-bold text-[#283593]">AI가 자동으로 상품 추가 배분을<br>할 수 있도록 허용하시겠습니까?</span>
        </p>

        <div class="flex gap-3 justify-center">
          <button 
            @click="showLowProductWarning = false" 
            class="flex-1 px-4 py-3 border border-gray-300 rounded-xl font-bold text-gray-500 hover:bg-gray-50 transition-colors"
          >
            아니오
          </button>
          <button 
            @click="confirmAutoAdditions" 
            class="flex-1 px-4 py-3 bg-[#283593] text-white rounded-xl font-bold hover:bg-[#1a237e] shadow-lg"
          >
            예
          </button>
        </div>
      </div>
    </div>

  </DefaultLayout>
</template>

<style scoped>
/* 가로 스크롤바 숨김 */
.no-scrollbar::-webkit-scrollbar {
  display: none;
}
.no-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
.animate-fade-in-up {
  animation: fadeInUp 0.3s ease-out;
}
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>