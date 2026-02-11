<script setup>
import { ref, computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import DefaultLayout from "@/layouts/DefaultLayout.vue";
import BaseInput from "@/components/common/BaseInput.vue";
import BaseToast from "@/components/common/BaseToast.vue";
import { authApi } from "@/services/auth.api"; // API import

const route = useRoute();
const router = useRouter();

// 상태 관리
const loading = ref(true);
const error = ref(null);
const resultData = ref(null);
const showModal = ref(false);
const saveForm = ref({ name: "", memo: "" });

// Toast 상태
const toast = ref({
  visible: false,
  message: '',
  type: 'success'
});

const showToast = (message, type = 'success') => {
  toast.value = { visible: true, message, type };
};

// URL 파라미터 파싱
const amount = Number(route.query.amount) || 0;
const horizon = route.query.horizon || "Y_1_3";
let mustBuckets = [];
try {
  mustBuckets = JSON.parse(route.query.assets || "[]");
} catch (e) {
  console.error("JSON parse error:", e);
}
const allowAiAdditions = route.query.allow_ai_additions === 'true'; // 기본 false

// API 호출
const fetchRecommendation = async () => {
  try {
    loading.value = true;
    const response = await authApi.recommendPortfolio({
      amount_krw: amount,
      horizon: horizon,
      must_buckets: mustBuckets,
      allow_ai_additions: allowAiAdditions
    });
    console.log("Portfolio Response:", response.data); // 디버깅용 로그
    resultData.value = response.data;
    // 저장 폼 기본 이름 설정
    saveForm.value.name = `${response.data.profile_label} 포트폴리오`;
  } catch (err) {
    console.error("Error fetching portfolio:", err);
    error.value =
      "분석 결과를 불러오는데 실패했습니다. 잠시 후 다시 시도해주세요.";
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  fetchRecommendation();
});

// 화면 표시용 Computed Properties
const profileLabel = computed(() => resultData.value?.profile_label || '분석 중');
const profileColor = computed(() => {
  return "bg-[#283593]";
});

// Editable allocations state
const editableAllocations = ref([]);

// Update editable allocations when resultData changes
const updateEditableAllocations = () => {
  if (resultData.value && resultData.value.final_allocations) {
    editableAllocations.value = JSON.parse(JSON.stringify(resultData.value.final_allocations));
  }
};

// Watch for data load
import { watch } from 'vue';
watch(resultData, () => {
  updateEditableAllocations();
});


const colorMap = {
  'STOCKS_KR': '#283593', 
  'STOCKS_GLB': '#3b82f6',
  'BONDS_KR': '#10b981', 
  'BONDS_GLB': '#34d399',
  'ALTERNATIVES': '#f59e0b', 
  'FUNDS': '#8b5cf6', 
  'CASH': '#cbd5e1'
};

const getColor = (bucket) => colorMap[bucket] || '#cccccc';

const pieStyle = computed(() => {
  if (editableAllocations.value.length === 0) return '';
  
  let gradient = 'conic-gradient(';
  let currentPos = 0;
  
  // Use editableAllocations for chart
  editableAllocations.value.forEach((item) => {
    // Normalize to 100% for chart if total != 100 (optional visual stability)
    // For now, just raw projection. If > 100, it wraps.
    const weight = Number(item.weight_pct) || 0;
    const start = currentPos;
    const end = currentPos + weight;
    const color = getColor(item.bucket);
    gradient += `${color} ${start}% ${end}%, `;
    currentPos = end;
  });

  gradient = gradient.slice(0, -2) + ")"; 
  return `background: ${gradient}`;
});



const formattedAmount = computed(() => amount.toLocaleString() + "원");

const savePortfolio = async () => {
  if (!saveForm.value.name) {
    showToast('이름을 입력해주세요.', 'warning');
    return;
  }

  try {
    const payload = {
      name: saveForm.value.name,
      amount_krw: amount,
      profile: resultData.value.profile,
      profile_label: resultData.value.profile_label,
      horizon_desc: resultData.value.horizon_desc,
      must_buckets: mustBuckets,
      allocations: editableAllocations.value,
      metrics: resultData.value.metrics,
      rationale: resultData.value.rationale,
      summary: resultData.value.summary,
      risks: resultData.value.risks,
    };

    await authApi.savePortfolio(payload);
    showToast('성공적으로 저장되었습니다!', 'success');
    
    // 토스트를 볼 시간을 준 뒤 이동
    setTimeout(() => {
        router.push('/user/mypage');
    }, 1200);
    
  } catch (err) {
    console.error("Save failed:", err);
    showToast('저장 중 오류가 발생했습니다.', 'error');
  }
};

// 메트릭 표시용
const expectedReturn = computed(
  () => resultData.value?.metrics?.expected_return_pct || 0
);
const riskScore = computed(() => resultData.value?.metrics?.risk_score || 0);
const rationale = computed(() => resultData.value?.rationale || '');
const summary = computed(() => resultData.value?.summary || ''); 
const assetLabels = {
  STOCKS_KR: '국내주식',
  STOCKS_GLB: '해외주식',
  BONDS_KR: '국내채권',
  BONDS_GLB: '해외채권',
  ALTERNATIVES: '대체투자',
  FUNDS: '펀드',
  CASH: '현금성자산'
};
</script>

<template>
  <DefaultLayout>
    <div class="max-w-4xl mx-auto px-6 py-12">
      <!-- 로딩 상태 -->
      <!-- 스켈레톤 로딩 상태 (Skeleton UI) -->
      <!-- 스켈레톤 로딩 상태 (Skeleton UI) -->
      <div v-if="loading">
        <!-- 상단 헤더 (텍스트) - Pulse 없음 -->
        <div class="text-center mb-10">
          <h2 class="text-2xl font-bold text-gray-900 mb-2">
            AI가 포트폴리오를 생성 중입니다<span class="loading-dots"></span>
          </h2>
          <p class="text-gray-500">잠시만 기다려주세요</p>
        </div>

        <!-- 스켈레톤 요소들 (Pulse 적용) -->
        <div class="animate-pulse">
            <!-- 뱃지 스켈레톤 -->
            <div class="h-8 bg-gray-300 rounded-full w-24 mx-auto mb-10"></div>

            <!-- 원형 차트 스켈레톤 -->
            <div class="w-64 h-64 bg-gray-300 rounded-full mx-auto mb-8"></div>

            <!-- 위험도 게이지 스켈레톤 -->
            <div class="h-3 bg-gray-300 rounded-full w-full max-w-xs mx-auto mb-12"></div>

            <!-- AI 코멘트 스켈레톤 -->
            <div class="bg-gray-100 p-6 rounded-xl text-left mb-10">
              <div class="h-6 bg-gray-300 rounded w-1/4 mb-4"></div>
              <div class="space-y-3">
                <div class="h-4 bg-gray-300 rounded w-full"></div>
                <div class="h-4 bg-gray-300 rounded w-5/6"></div>
                <div class="h-4 bg-gray-300 rounded w-4/6"></div>
              </div>
            </div>

            <!-- 자산 리스트 스켈레톤 -->
            <div class="bg-gray-50 p-6 rounded-xl">
              <div class="h-5 bg-gray-300 rounded w-1/4 mb-4"></div>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div class="h-20 bg-gray-300 rounded" v-for="n in 4" :key="n"></div>
              </div>
            </div>
        </div>
      </div>

      <!-- 에러 상태 -->
      <div
        v-else-if="error"
        class="text-center py-20 bg-white rounded-3xl shadow-lg border border-gray-100 p-10"
      >
        <div class="text-red-500 text-6xl mb-4">⚠️</div>
        <h3 class="text-xl font-bold text-gray-900 mb-2">
          오류가 발생했습니다
        </h3>
        <p class="text-gray-600 mb-8">{{ error }}</p>
        <button
          @click="router.push('/survey')"
          class="px-6 py-3 border border-gray-300 rounded-xl font-bold text-gray-600 hover:bg-gray-50"
        >
          다시 시도하기
        </button>
      </div>

      <!-- 결과 표시 -->
      <div
        v-else
        class="bg-white rounded-3xl shadow-lg border border-gray-100 overflow-hidden text-center p-10"
      >
        <div class="text-sm font-bold text-gray-400 mb-2">
          AI 맞춤 분석 결과
        </div>
        <h2 class="text-3xl font-bold text-gray-900 mb-2">
          나만의 AI 포트폴리오
        </h2>
        <p class="text-gray-500 mb-8">
          투자금
          <span class="font-bold text-[#283593]">{{ formattedAmount }}</span
          >, 기간
          <span class="font-bold text-gray-700">{{
            resultData.horizon_desc
          }}</span>
        </p>

        <span
          class="inline-block px-4 py-1.5 rounded-full text-white text-sm font-bold mb-10"
          :class="profileColor"
        >
          {{ profileLabel }}
        </span>

        <!-- 차트 영역 -->
        <div class="relative w-64 h-64 mx-auto rounded-full mb-8 shadow-lg scale-100 hover:scale-105 transition-transform duration-500" :style="pieStyle">
          <div class="absolute inset-4 bg-white rounded-full flex flex-col items-center justify-center shadow-inner">
            <span class="text-sm text-gray-400 font-medium">기대 수익률</span>
            <span class="text-3xl font-bold text-[#283593]">+{{ expectedReturn }}%</span>
          </div>
        </div>

        <!-- 위험도 게이지 (추가) -->
        <div class="max-w-xs mx-auto mb-12">
          <div class="flex justify-between items-end mb-2 px-1">
            <span class="text-xs font-bold text-gray-400">위험도</span>
            <span class="text-sm font-bold" :class="riskScore > 60 ? 'text-red-500' : (riskScore > 40 ? 'text-yellow-500' : 'text-green-500')">
              {{ riskScore }}점 ({{ riskScore > 60 ? '높음' : (riskScore > 40 ? '중간' : '낮음') }})
            </span>
          </div>
          <div class="h-3 w-full bg-gradient-to-r from-green-400 via-yellow-400 to-red-500 rounded-full relative">
            <div 
              class="absolute top-1/2 -translate-y-1/2 w-1 h-5 bg-gray-800 rounded-sm shadow-sm transition-all duration-1000 ease-out"
              :style="{ left: riskScore + '%' }"
            ></div>
          </div>
          <div class="flex justify-between text-[10px] text-gray-400 mt-1.5 font-medium px-1">
            <span>안전</span>
            <span>위험</span>
          </div>
        </div>

        <!-- AI 코멘트  -->
        <div class="bg-blue-50 p-6 rounded-xl text-left mb-10">
          <h4 class="font-bold text-[#283593] mb-2 flex items-center">
            <span class="text-xl mr-2">💡</span> AI 투자 전략
          </h4>
          <p class="text-gray-700 text-sm leading-relaxed whitespace-pre-wrap">{{ rationale }}</p>
        </div>

        <!-- 자산 배분 리스트 (Read-only) -->
        <div class="mb-12 bg-gray-50 p-6 rounded-xl">
          <div class="flex justify-between items-center mb-4 px-2">
            <span class="text-sm font-bold text-gray-500">자산 구성 정보</span>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
            <div
              v-for="(item, index) in editableAllocations"
              :key="item.bucket"
              class="flex flex-col bg-white p-3 rounded border border-gray-100"
            >
              <div class="flex justify-between items-center mb-2">
                <span class="font-medium text-gray-600 flex items-center gap-2">
                  <span class="w-2 h-2 rounded-full" :style="{ backgroundColor: getColor(item.bucket) }"></span>
                  {{ assetLabels[item.bucket] || item.bucket }}
                </span>
                <span class="font-bold text-gray-900">{{ item.weight_pct }}%</span>
              </div>
              <!-- 프로그레스 바 -->
              <div class="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
                <div class="h-full transition-[width,background-color] duration-300" :style="{ width: item.weight_pct + '%', backgroundColor: getColor(item.bucket) }"></div>
              </div>
            </div>
          </div>
        </div>


        <div class="flex gap-4 justify-center">
          <button
            @click="router.push({ name: 'portfolio-create', query: { type: resultData.profile } })"
            class="px-6 py-3 border border-gray-300 rounded-xl font-bold text-gray-600 hover:bg-gray-50"
          >
            재구성하기
          </button>
          <button
            @click="showModal = true"
            class="px-8 py-3 bg-[#283593] text-white rounded-xl font-bold hover:bg-[#1a237e] shadow-md"
          >
            내 포트폴리오에 저장
          </button>
        </div>
      </div>
    </div>

    <!-- 저장 모달 -->
    <div
      v-if="showModal"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 backdrop-blur-sm"
    >
      <div
        class="bg-white rounded-2xl w-full max-w-md p-8 shadow-2xl relative animate-fade-in-up"
      >
        <h3 class="text-xl font-bold mb-6">포트폴리오 저장</h3>
        <BaseInput label="포트폴리오 이름" v-model="saveForm.name" placeholder="예: 2024년 1억 만들기 플랜" />
        <div class="h-4"></div>
        <div class="flex gap-3 justify-end">
          <button
            @click="showModal = false"
            class="px-6 py-2.5 border border-gray-300 rounded-lg font-bold text-gray-500 hover:bg-gray-50"
          >
            취소
          </button>
          <button
            @click="savePortfolio"
            class="px-6 py-2.5 bg-[#283593] text-white rounded-lg font-bold hover:bg-[#1a237e]"
          >
            저장하기
          </button>
        </div>
      </div>
    </div>
    <!-- Toast -->
    <BaseToast 
      :visible="toast.visible" 
      :message="toast.message" 
      :type="toast.type" 
      @close="toast.visible = false" 
    />
  </DefaultLayout>
</template>

<style scoped>
.animate-fade-in-up {
  animation: fadeInUp 0.3s ease-out;
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

.loading-dots::after {
  content: '.';
  animation: dots 1.5s steps(3, end) infinite;
  display: inline-block;
  width: 1.5em; /* 점 3개 공간 확보 */
  text-align: left;
}


@keyframes dots {
  0% { content: ''; }
  25% { content: '.'; }
  50% { content: '..'; }
  75% { content: '...'; }
  100% { content: ''; }
}
</style>
