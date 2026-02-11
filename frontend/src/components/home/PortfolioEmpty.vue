<script setup>
// ✅ 1. 라우터 기능 불러오기
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { authApi } from '@/services/auth.api';

// 이미지 에셋
import step1Img from '@/assets/images/step1.png';
import step2Img from '@/assets/images/step2.png';
import step3Img from '@/assets/images/step3.png';

// ✅ 2. 라우터 사용 준비
const router = useRouter();

// 프리뷰 모달 상태
const previewStep = ref(null); // 'survey', 'analysis', 'rebalance' or null

const openPreview = (type) => {
  previewStep.value = type;
};

const closePreview = () => {
  previewStep.value = null;
};

// 감각적인 문구들
const steps = [
  { 
    id: 'survey',
    step: 'STEP 01', 
    iconContent: '<path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z" />', 
    title: '나만의 투자 DNA 발견', 
    desc: '복잡한 고민 없이,\n몇 가지 질문으로 성향을 파악해요.' 
  },
  { 
    id: 'analysis',
    step: 'STEP 02', 
    iconContent: '<path stroke-linecap="round" stroke-linejoin="round" d="M8.25 3v1.5M4.5 8.25H3m18 0h-1.5M4.5 12H3m18 0h-1.5m-15 3.75H3m18 0h-1.5M8.25 19.5V21M12 3v1.5m0 15V21m3.75-18v1.5m0 15V21m-9-1.5h10.5a2.25 2.25 0 002.25-2.25V6.75a2.25 2.25 0 00-2.25-2.25H6.75A2.25 2.25 0 004.5 6.75v10.5a2.25 2.25 0 002.25 2.25z" />', 
    title: 'AI 포트폴리오 생성', 
    desc: '정교하게 짜여진 로직을 학습한 AI가\n최적의 포트폴리오를 생성합니다.' 
  },
  { 
    id: 'rebalance',
    step: 'STEP 03', 
    iconContent: '<path stroke-linecap="round" stroke-linejoin="round" d="M10.5 6h9.75M10.5 6a1.5 1.5 0 11-3 0m3 0a1.5 1.5 0 10-3 0M3.75 6H7.5m3 12h9.75m-9.75 0a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m-3.75 0H7.5m9-6h3.75m-3.75 0a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m-9.75 0h9.75" />', 
    title: '내 입맛대로 조정하는 포트폴리오', 
    desc: 'AI 분석 결과와 내 취향을 참고하여\n포트폴리오를 조정해보세요.' 
  }
];

// ✅ 3. 버튼 클릭 시 설문 여부 확인 후 이동
const startSurvey = async () => {
  try {
    const res = await authApi.getSurveyStatus();
    if (res.data && res.data.exists) {
      // 이미 설문 진행함 -> 바로 포트폴리오 생성
      router.push({ name: 'portfolio-create' });
    } else {
      // 설문 없음 -> 설문부터
      router.push('/survey');
    }
  } catch (e) {
    console.error("Survey check failed:", e);
    // 에러/비로그인 등 -> 일단 설문으로 이동 (가드나 리다이렉트 처리)
    router.push('/survey');
  }
};
</script>

<template>
  <div class="w-full max-w-6xl mx-auto mt-12 mb-20">
    
    <!-- 1. 히어로 섹션 (메인 타이틀) -->
    <div class="text-center mb-16 relative">
      <!-- 배경 장식 -->
      <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[300px] bg-gradient-to-r from-blue-100 to-purple-100 rounded-full blur-3xl opacity-50 -z-10"></div>

      <span class="inline-block py-1 px-3 rounded-full bg-blue-50 text-[#536dfe] text-xs font-bold tracking-wider mb-4 border border-blue-100">
        AI PORTFOLIO SERVICE
      </span>
      
      <h1 class="text-4xl md:text-5xl font-extrabold text-gray-900 leading-tight mb-6">
        AI와 함께하는 <span class="text-transparent bg-clip-text bg-gradient-to-r from-[#536dfe] to-purple-600">최적의 자산 배분</span>
      </h1>
      
      <p class="text-gray-500 text-lg mb-10 max-w-2xl mx-auto">
        AI의 분석과 비교 및 리밸런싱을 활용해<br/>
        최적의 포트폴리오를 구성해보세요.
      </p>

      <!-- 메인 CTA 버튼 -->
      <!-- ✅ @click="startSurvey"가 위에서 만든 함수를 실행합니다 -->
      <button 
        @click="startSurvey"
        class="group relative inline-flex items-center justify-center px-8 py-4 font-bold text-white transition-all duration-200 bg-[#283593] font-sans rounded-full hover:bg-[#1a237e] hover:shadow-lg hover:-translate-y-1 focus:outline-none ring-offset-2 focus:ring-2 ring-blue-400"
      >
        <span class="mr-2 text-lg"></span> 내 맞춤 포트폴리오 확인하기
        <svg class="w-5 h-5 ml-2 -mr-1 transition-transform group-hover:translate-x-1" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg"><path fill-rule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clip-rule="evenodd"></path></svg>
      </button>
    </div>

    <!-- 2. 프로세스 카드 (기능 소개) -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-8 px-4">
      <div 
        v-for="(item, index) in steps" 
        :key="index"
        class="bg-white rounded-2xl p-8 shadow-sm border border-gray-200 hover:shadow-xl hover:border-blue-100 transition-all duration-300 group cursor-pointer relative overflow-hidden"
        @click="openPreview(item.id)"
      >
        <!-- 카드 상단 장식바 -->
        <div class="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-gray-100 via-gray-200 to-gray-100 group-hover:from-[#536dfe] group-hover:to-purple-500 transition-all duration-500"></div>

        <div class="flex flex-col items-center text-center">
          <div class="mb-4 inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gray-50 text-3xl group-hover:scale-110 group-hover:bg-blue-50 transition-all duration-300">
             <svg xmlns="http://www.w3.org/2000/svg" class="w-8 h-8 text-[#536dfe]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
               <g v-html="item.iconContent"></g>
             </svg>
          </div>
          
          <div class="text-xs font-bold text-gray-400 mb-2 tracking-widest group-hover:text-[#536dfe] transition-colors">
            {{ item.step }}
          </div>
          
          <h3 class="text-xl font-bold text-gray-900 mb-3 group-hover:text-[#2C4768] transition-colors">
            {{ item.title }}
          </h3>
          
          <p class="text-sm text-gray-500 leading-relaxed whitespace-pre-line">
            {{ item.desc }}
          </p>
        </div>
      </div>
    </div>

  </div>

    <!-- 3. 프리뷰 모달 -->
    <div v-if="previewStep" class="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4 backdrop-blur-sm" @click.self="closePreview">
      <div 
        class="bg-white rounded-3xl shadow-2xl w-full overflow-hidden animate-fade-in ring-1 ring-gray-900/5 transition-all duration-300"
        :class="{
          'max-w-3xl': previewStep === 'survey',
          'max-w-lg': previewStep === 'analysis',
          'max-w-5xl': previewStep === 'rebalance'
        }"
      >
        
        <!-- 모달 헤더 -->
        <div class="px-6 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
          <h3 class="font-bold text-gray-900">
            <span v-if="previewStep === 'survey'">설문조사 미리보기</span>
            <span v-else-if="previewStep === 'analysis'">AI 분석 결과 미리보기</span>
            <span v-else-if="previewStep === 'rebalance'">포트폴리오 리밸런싱 미리보기</span>
          </h3>
          <button @click="closePreview" class="text-gray-400 hover:text-gray-900 transition-colors">
            <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
          </button>
        </div>

        <!-- 모달 컨텐츠 (이미지) -->
        <div class="p-0 bg-gray-50 min-h-[300px] flex items-center justify-center relative">
          
          <!-- 이미지 표시 영역 -->
          <img v-if="previewStep === 'survey'" :src="step1Img" class="w-full h-auto object-contain max-h-[70vh] rounded-lg shadow-sm" alt="설문조사 예시" />
          <img v-else-if="previewStep === 'analysis'" :src="step2Img" class="w-full h-auto object-contain max-h-[70vh] rounded-lg shadow-sm" alt="분석 결과 예시" />
          <img v-else-if="previewStep === 'rebalance'" :src="step3Img" class="w-full h-auto object-contain max-h-[70vh] rounded-lg shadow-sm" alt="리밸런싱 예시" />

        </div>
      </div>
    </div>

</template>

<style scoped>
@keyframes pulse-slow {
  0%, 100% { opacity: 0.5; transform: scale(1); }
  50% { opacity: 0.7; transform: scale(1.05); }
}
.blur-3xl {
  animation: pulse-slow 6s infinite;
}
</style>