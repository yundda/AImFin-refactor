<script setup>
import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import DefaultLayout from '@/layouts/DefaultLayout.vue';

const route = useRoute();
const router = useRouter();
const score = route.query.score || 0;
// 백엔드에서 전달된 profile 키 (Example: BALANCED)
const type = route.query.type || 'BALANCED';

const typeInfo = {
  CONSERVATIVE: { label: '안정형', icon: '🐢', color: 'bg-green-500', text: 'text-green-600', desc: '원금 보존을 최우선으로 하며, 안정적인 예적금 위주의 투자를 선호합니다.' },
  MODERATE_CONSERVATIVE: { label: '안정추구형', icon: '🐨', color: 'bg-teal-500', text: 'text-teal-600', desc: '안정성을 중시하지만, 예금 금리보다 높은 수익을 위해 일부 위험을 감수합니다.' },
  BALANCED: { label: '중립형', icon: '🦓', color: 'bg-blue-500', text: 'text-blue-600', desc: '위험과 수익의 균형을 중요하게 생각하며, 다양한 자산에 분산 투자합니다.' },
  GROWTH: { label: '적극투자형', icon: '🐅', color: 'bg-indigo-500', text: 'text-indigo-600', desc: '높은 수익을 기대하며 주식이나 펀드 등 위험 자산 투자에 적극적입니다.' },
  AGGRESSIVE: { label: '공격투자형', icon: '🦁', color: 'bg-purple-500', text: 'text-purple-600', desc: '시장 평균을 훨씬 상회하는 고수익을 목표로 과감하게 투자합니다.' }
};

const result = computed(() => typeInfo[type] || typeInfo['BALANCED']);

const goToCreate = () => {
  // 성향 정보를 가지고 다음 단계(조건 설정)로 이동
  router.push({ name: 'portfolio-create', query: { type } });
};
</script>

<template>
  <DefaultLayout>
    <div class="max-w-3xl mx-auto px-6 py-16 text-center">
      
      <div class="bg-white rounded-3xl shadow-lg border border-gray-100 p-12 relative overflow-hidden">
        <!-- 배경 장식 -->
        <div class="absolute top-0 left-0 w-full h-2 bg-gray-100">
          <div class="h-full bg-[#283593] w-1/2"></div> <!-- 진행률 50% -->
        </div>

        <div class="text-sm font-bold text-gray-400 mb-6 tracking-widest">성향 분석 완료</div>
        
        <div class="text-6xl mb-6 animate-bounce-slow">{{ result.icon }}</div>
        
        <h2 class="text-3xl font-extrabold text-gray-900 mb-4">
          당신의 투자 성향은<br/>
          <span :class="result.text">{{ result.label }}</span> 입니다
        </h2>
        
        <p class="text-gray-500 text-lg mb-12 max-w-lg mx-auto leading-relaxed">
          {{ result.desc }}
        </p>

        <div class="bg-gray-50 rounded-xl p-6 mb-10">
          <p class="text-gray-700 font-medium">
            투자 성향 분석이 완료되었습니다.<br/>
            다음으로 <span class="text-[#536dfe] font-bold">나만의 맞춤 포트폴리오</span>를 만들어볼까요?
          </p>
        </div>

        <div class="flex flex-col sm:flex-row gap-4 justify-center">
          <button @click="router.push('/survey')" class="px-8 py-4 border border-gray-300 rounded-xl font-bold text-gray-500 hover:bg-gray-50 transition-colors">
            성향 재진단하기
          </button>
          <button @click="goToCreate" class="px-8 py-4 bg-[#283593] text-white rounded-xl font-bold hover:bg-[#1a2f4d] shadow-lg transition-transform hover:-translate-y-1">
            포트폴리오 만들기 →
          </button>
        </div>
      </div>

    </div>
  </DefaultLayout>
</template>

<style scoped>
.animate-bounce-slow { animation: bounce 3s infinite; }
@keyframes bounce { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }
</style>