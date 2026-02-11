<script setup>
import { ref, onMounted } from 'vue';
import { marketApi } from '@/services/market-index.api';
import MarketSettingsModal from './MarketSettingsModal.vue';

const indices = ref([]);
const loading = ref(true);
const isSettingsOpen = ref(false);

const fetchData = async () => {
    loading.value = true;
    try {
        const data = await marketApi.getIndices();
        // 데이터가 모자라면 반복 (UI 효과용) - 와이드 스크린 대응을 위해 넉넉히 10번 반복
        if (data.length > 0) {
            indices.value = Array(10).fill(data).flat();
        } else {
            indices.value = [];
        }
    } catch (e) {
        console.error(e);
    } finally {
        loading.value = false;
    }
};

// 간단한 스파크라인 SVG 경로 생성 함수
const getSvgPath = (data, width = 60, height = 30) => {
  if (!data || data.length === 0) return '';
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const stepX = width / (data.length - 1);
  
  return data.map((val, i) => {
    const x = i * stepX;
    const y = height - ((val - min) / range) * height; 
    return `${i === 0 ? 'M' : 'L'}${x},${y}`;
  }).join(' ');
};

onMounted(() => {
  fetchData();
});
</script>

<template>
  <div class="w-full bg-white border-b border-gray-200 overflow-hidden h-14 flex items-center relative">
    <!-- 좌우 그라데이션 (부드러운 사라짐 효과) -->
    <div class="absolute left-0 top-0 bottom-0 w-20 bg-gradient-to-r from-white to-transparent z-10 pointer-events-none"></div>
    <div class="absolute right-0 top-0 bottom-0 w-20 bg-gradient-to-l from-white to-transparent z-10 pointer-events-none"></div>

    <!-- 설정 버튼 (우측 상단 고정, z-index 높게) -->
    <div class="absolute right-4 z-20">
        <button @click="isSettingsOpen = true" class="flex items-center gap-1.5 px-3 py-1.5 bg-[#283593] text-white rounded-full shadow-md hover:bg-[#1a237e] hover:shadow-lg transition-all text-xs font-bold group">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <span>관심 지수 설정</span>
        </button>
    </div>

    <!-- 흐르는 컨텐츠 트랙 -->
    <div class="flex items-center animate-marquee whitespace-nowrap hover:pause">
      <div 
        v-for="(item, index) in indices" 
        :key="index"
        class="flex items-center gap-3 px-8 border-r border-gray-100 last:border-0"
      >
        <!-- 미니 차트 -->
        <svg width="40" height="20" viewBox="0 0 60 30" class="overflow-visible opacity-80">
          <path
            :d="getSvgPath(item.chartData)"
            fill="none"
            :stroke="item.isUp ? '#e22a40' : '#2e68ff'"
            stroke-width="2.5"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>

        <!-- 지수 정보 -->
        <div class="flex flex-col">
          <span class="text-[11px] text-gray-500 font-bold leading-tight">{{ item.name }}</span>
          <div class="flex items-center gap-1 text-[11px]">
            <span class="font-bold text-gray-800">{{ item.value.toLocaleString() }}</span>
            <span :class="item.isUp ? 'text-[#e22a40]' : 'text-[#2e68ff]'">
              {{ item.isUp ? '+' : '' }}{{ item.change }} ({{ item.rate }}%)
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
  <MarketSettingsModal 
    :is-open="isSettingsOpen" 
    @close="isSettingsOpen = false"
    @saved="fetchData" 
  />
</template>

<style scoped>
@keyframes marquee {
  0% { transform: translateX(0); }
  100% { transform: translateX(-50%); } /* 데이터 양에 따라 조절 */
}

.animate-marquee {
  animation: marquee 200s linear infinite; /* 속도 조절: 숫자가 클수록 느림 */
}

/* 마우스 올리면 멈춤 */
.hover\:pause:hover {
  animation-play-state: paused;
}
</style>