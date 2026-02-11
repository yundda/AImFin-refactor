<script setup>
import { computed, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import SimpleDonut from '@/components/common/SimpleDonut.vue';

const props = defineProps({
  portfolioData: {
    type: Object,
    required: true
  }
});

const router = useRouter();
const authStore = useAuthStore();

// API 데이터를 UI 포맷으로 변환
const portfolio = computed(() => {
  if (!props.portfolioData) return null;
  
  const p = props.portfolioData;
  const metrics = p.metrics || { expected_return_pct: 0, risk_score: 0 };
  
  // 자산 배분 집계 (7개 카테고리)
  const assetMap = {
    'STOCKS_KR': 0, 'STOCKS_GLB': 0,
    'BONDS_KR': 0, 'BONDS_GLB': 0,
    'ALTERNATIVES': 0, 'FUNDS': 0, 'CASH': 0
  };
  const bucketKeys = ['STOCKS_KR', 'STOCKS_GLB', 'BONDS_KR', 'BONDS_GLB', 'ALTERNATIVES', 'FUNDS', 'CASH'];

  if (p.allocations) {
    p.allocations.forEach(a => {
      if (assetMap.hasOwnProperty(a.bucket)) {
        assetMap[a.bucket] += (a.weight_pct || 0);
      }
    });
  }
  
  // Map object to array in specific order
  const assetsArray = bucketKeys.map(key => Number(assetMap[key].toFixed(1)));

  return {
    name: p.name,
    typeLabel: p.profile_label,
    amount: p.amount_krw,
    metrics: metrics,
    aiComment: p.summary || p.rationale || '', // AI 코멘트 (summary 우선)
    assets: assetsArray,
    typeCode: p.profile 
  };
});

// 통계 (API Metrics 사용)
const stats = computed(() => {
  if (!portfolio.value) return { returnRate: 0, riskScore: 0 };
  return {
    returnRate: portfolio.value.metrics.expected_return_pct,
    riskScore: portfolio.value.metrics.risk_score
  };
});

const formattedAmount = computed(() => {
  return portfolio.value ? Number(portfolio.value.amount).toLocaleString() : '0';
});

const nickname = computed(() => authStore.user?.nickname || '회원');

const assetsInfo = [
  { label: '국내주식', color: 'bg-[#283593]' },
  { label: '해외주식', color: 'bg-[#3b82f6]' },
  { label: '국내채권', color: 'bg-[#10b981]' },
  { label: '해외채권', color: 'bg-[#34d399]' },
  { label: '대체투자', color: 'bg-[#f59e0b]' },
  { label: '펀드', color: 'bg-[#8b5cf6]' },
  { label: '현금성자산', color: 'bg-[#cbd5e1]' },
];

const goToCompare = () => { showCompareModal.value = true; };
const modifyPortfolio = () => { router.push({ name: 'portfolio-create', query: { type: portfolio.value.typeCode } }); };

const sortedAssets = computed(() => {
  if (!portfolio.value || !portfolio.value.assets) return [];
  return portfolio.value.assets
    .map((val, i) => ({
      value: val,
      label: assetsInfo[i].label,
      color: assetsInfo[i].color // Class string in this file
    }))
    .sort((a, b) => b.value - a.value);
});

// Modal Logic
const showCreateModal = ref(false);
const showCompareModal = ref(false);

const openCreateModal = () => {
  showCreateModal.value = true;
};

const goToSurvey = () => {
  router.push('/survey');
};

const goToCreatePortfolio = () => {
  // 현재 포트폴리오의 성향 코드를 가져와서 전달
  const type = portfolio.value?.typeCode || 'BALANCED';
  router.push({ name: 'portfolio-create', query: { type } });
};

const startCompare = () => {
  router.push('/portfolio/compare');
};

const startRebalance = () => {
  // 사용자가 포트폴리오를 선택한 후 리밸런싱하도록 모드 전달
  router.push({ 
    path: '/portfolio/compare', 
    query: { mode: 'rebalance_select' } 
  });
};

const goToList = () => {
  router.push({ path: '/user/mypage', query: { view: 'list' } });
};
</script>

<template>
  <div v-if="portfolio" class="w-full max-w-6xl mx-auto mt-8 px-4 md:px-0">
    
    <div class="bg-white rounded-3xl shadow-lg border-2 border-gray-200 overflow-hidden p-8 md:p-12 relative">
      <div class="absolute top-0 right-0 w-64 h-64 bg-blue-50 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 opacity-50 pointer-events-none"></div>

      <!-- 상단 헤더 -->
      <div class="flex justify-between items-center mb-6 relative z-10">
        <!-- 대표 포트폴리오 배지 (테두리 스타일) -->
        <div class="inline-flex items-center gap-2 px-2 py-0.5 border border-[#283593] bg-white text-[#283593] text-[11px] font-bold rounded ml-5">
          <span class="w-1.5 h-1.5 rounded-full bg-[#283593]"></span>
          대표 포트폴리오
        </div>
        <button @click="goToList" class="flex items-center gap-1 text-sm font-bold text-gray-400 hover:text-[#283593] transition-colors">
          <span>마이 포트폴리오 리스트</span>
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-4 h-4"><path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" /></svg>
        </button>
      </div>

      <div class="flex flex-col lg:flex-row gap-12 items-start relative z-10 mb-12">
        
        <!-- 좌측: 텍스트 및 지표 -->
        <div class="flex-1 w-full">
          <h2 class="text-3xl md:text-4xl font-extrabold text-gray-900 mb-2 leading-tight pl-5">
            {{ portfolio.name }}
          </h2>
          <p class="text-gray-500 mb-12 pl-5">{{ portfolio.typeLabel }} 성향 기반의 AI 맞춤 전략입니다.</p>

          <div v-if="portfolio.aiComment" class="mb-8 bg-gray-50 rounded-2xl p-5 border border-gray-100">
            <h4 class="text-sm font-bold text-[#283593] mb-2 flex items-center gap-2">
              <span class="text-lg">💡</span> AI 투자 코멘트
            </h4>
            <div class="text-gray-700 text-sm leading-relaxed whitespace-pre-line font-medium">
              {{ portfolio.aiComment }}
            </div>
          </div>

          <!-- ✅ 핵심 지표 카드 -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <!-- 1. 총 자산 -->
            <div class="bg-gray-50 rounded-2xl p-5 border border-gray-100 flex flex-col justify-between">
              <div class="text-xs font-bold text-gray-400 mb-1">총 운용 자산</div>
              <div class="text-xl font-bold text-gray-900">{{ formattedAmount }}원</div>
            </div>

            <!-- 2. 예상 수익률 -->
            <div class="bg-gray-50 rounded-2xl p-5 border border-gray-100 flex flex-col justify-between">
              <div class="text-xs font-bold text-gray-400 mb-1">예상 연수익률</div>
              <div class="text-xl font-bold text-[#283593]">+{{ stats.returnRate }}%</div>
            </div>

            <!-- 3. 위험도 게이지 -->
            <div class="bg-gray-50 rounded-2xl p-5 border border-gray-100 sm:col-span-2">
              <div class="flex justify-between items-end mb-2 px-1">
                <span class="text-xs font-bold text-gray-400">위험도</span>
                <span class="text-sm font-bold" :class="stats.riskScore > 60 ? 'text-red-500' : (stats.riskScore > 40 ? 'text-yellow-500' : 'text-green-500')">
                  {{ stats.riskScore }}점 ({{ stats.riskScore > 60 ? '높음' : (stats.riskScore > 40 ? '중간' : '낮음') }})
                </span>
              </div>
              
              <!-- ✅ 그라데이션 게이지 바 -->
              <div class="h-3 w-full bg-gradient-to-r from-green-400 via-yellow-400 to-red-500 rounded-full relative shadow-inner">
                <div 
                  class="absolute top-1/2 -translate-y-1/2 w-1.5 h-6 bg-gray-800 border-2 border-white rounded-sm shadow-md transition-all duration-1000 ease-out"
                  :style="{ left: stats.riskScore + '%' }"
                ></div>
              </div>
              
              <div class="flex justify-between text-[10px] text-gray-400 mt-2 font-medium px-1">
                <span>안전</span>
                <span>위험</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 우측: 대형 차트 -->
        <div class="flex-1 flex flex-col items-center justify-center w-full pt-4">
          <div class="relative mb-8">
            <SimpleDonut :assets="portfolio.assets" size="w-72 h-72 md:w-80 md:h-80" />
            <div class="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span class="text-xs font-bold text-gray-400 mb-1 tracking-wider uppercase">포트폴리오 성향</span>
              <span class="text-2xl font-extrabold text-[#283593]">{{ portfolio.typeLabel }}</span>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-x-8 gap-y-3 w-full max-w-sm">
            <div v-for="(item, idx) in sortedAssets" :key="idx" class="flex items-center justify-between p-2 rounded-lg hover:bg-gray-50 transition-colors" v-show="item.value > 0">
              <div class="flex items-center gap-3">
                <span :class="['w-3 h-3 rounded-full shadow-sm', item.color]"></span>
                <span class="text-sm text-gray-600 font-medium">{{ item.label }}</span>
              </div>
              <span class="text-base font-bold text-gray-900">{{ item.value }}%</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 하단 버튼 -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-8 border-t border-gray-100">
        <button @click="goToCompare" class="flex items-center justify-center gap-3 py-4 rounded-xl border-2 border-gray-300 hover:border-[#283593] hover:text-[#283593] hover:bg-blue-50 transition-all group">
          <svg xmlns="http://www.w3.org/2000/svg" class="w-8 h-8 text-gray-400 group-hover:text-[#283593] transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 6a7.5 7.5 0 107.5 7.5h-7.5V6z" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 10.5H21A7.5 7.5 0 0013.5 3v7.5z" />
          </svg>
          <div class="text-left">
            <div class="font-bold text-gray-900 group-hover:text-[#283593]">포트폴리오 비교 / 리밸런싱 하기</div>
            <div class="text-xs text-gray-400">다른 전략과 수익률을 비교해보세요</div>
          </div>
        </button>
        <button @click="openCreateModal" class="flex items-center justify-center gap-3 py-4 rounded-xl bg-[#283593] hover:bg-[#1a237e] text-white transition-all shadow-md hover:shadow-lg group">
          <svg xmlns="http://www.w3.org/2000/svg" class="w-8 h-8 group-hover:rotate-90 transition-transform duration-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          <div class="text-left">
            <div class="font-bold">포트폴리오 생성하기</div>
            <div class="text-xs text-blue-100">새로운 투자 목표로 다시 만들기</div>
          </div>
        </button>
      </div>

    </div>

    <!-- Create Portfolio Modal -->
    <div v-if="showCreateModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-2xl w-full max-w-md p-8 shadow-2xl relative animate-fade-in-up text-center">
        <h3 class="text-xl font-bold mb-4 text-gray-900">투자 성향 재진단 안내</h3>
        
        <p class="text-gray-600 mb-8 leading-relaxed">
          {{ nickname }}님의 투자 성향은 현재<br>
          <span class="font-bold text-[#283593] text-lg">'{{ authStore.user.survey_profile_label }}'</span> 입니다.<br><br>
          <span class="text-sm text-gray-500">투자 성향 진단부터 다시 실시할까요?</span>
        </p>

        <div class="flex flex-col sm:flex-row gap-3 justify-center">
          <button 
            @click="goToCreatePortfolio" 
            class="flex-1 px-6 py-3 border border-gray-300 rounded-xl font-bold text-gray-500 hover:bg-gray-50 transition-colors order-2 sm:order-1"
          >
            아니오
          </button>
          <button 
            @click="goToSurvey" 
            class="flex-1 px-6 py-3 bg-[#283593] text-white rounded-xl font-bold hover:bg-[#1a237e] shadow-lg transition-transform hover:-translate-y-1 order-1 sm:order-2"
          >
            예
          </button>
        </div>
        
        <button @click="showCreateModal = false" class="absolute top-4 right-4 text-gray-400 hover:text-gray-600">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Compare/Rebalance Selection Modal -->
    <div v-if="showCompareModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-2xl w-full max-w-md p-8 shadow-2xl relative animate-fade-in-up text-center">
        <h3 class="text-xl font-bold mb-4 text-gray-900">어떤 작업을 진행할까요?</h3>
     

        <div class="flex flex-col gap-3">
          <button 
            @click="startCompare" 
            class="w-full px-6 py-4 border border-gray-200 rounded-xl hover:border-[#283593] hover:bg-blue-50 transition-all flex items-center justify-between group"
          >
            <div class="text-left">
              <div class="font-bold text-gray-900 group-hover:text-[#283593]">다른 포트폴리오와 비교</div>
              <div class="text-xs text-gray-500">내 포트폴리오 목록 중 하나와 비교합니다</div>
            </div>
            <svg xmlns="http://www.w3.org/2000/svg" class="w-8 h-8 text-gray-400 group-hover:text-[#283593] transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
            </svg>
          </button>

          <button 
            @click="startRebalance" 
            class="w-full px-6 py-4 border border-gray-200 rounded-xl hover:border-[#283593] hover:bg-blue-50 transition-all flex items-center justify-between group"
          >
             <div class="text-left">
              <div class="font-bold text-gray-900 group-hover:text-[#283593]">현재 구성 리밸런싱</div>
              <div class="text-xs text-gray-500">현재 포트폴리오의 비중을 조정하여 분석합니다</div>
            </div>
            <svg xmlns="http://www.w3.org/2000/svg" class="w-8 h-8 text-gray-400 group-hover:text-[#283593] transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 6a7.5 7.5 0 107.5 7.5h-7.5V6z" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 10.5H21A7.5 7.5 0 0013.5 3v7.5z" />
            </svg>
          </button>
        </div>
        
        <button @click="showCompareModal = false" class="absolute top-4 right-4 text-gray-400 hover:text-gray-600">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>

  </div>
</template>

<style scoped>
.animate-fade-in-up {
  animation: fadeInUp 0.3s ease-out;
}
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>