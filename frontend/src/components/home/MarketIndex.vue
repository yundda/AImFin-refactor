<script setup>
import { ref, onMounted } from 'vue';
import { marketApi } from '@/services/market-index.api';

const indices = ref([]);
const loading = ref(true);

// 간단한 스파크라인(미니 차트) SVG 경로를 만드는 함수
const getSvgPath = (data, width = 60, height = 30) => {
  if (!data || data.length === 0) return '';

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min;
  
  // 데이터가 일직선일 경우 예외 처리
  if (range === 0) return `M0,${height / 2} L${width},${height / 2}`;

  const stepX = width / (data.length - 1);
  
  // 점들을 이어서 SVG 경로(Path) 문자열 생성
  const pathD = data.map((val, i) => {
    const x = i * stepX;
    // 값이 높을수록 y좌표는 작아야 함 (SVG 좌표계)
    const y = height - ((val - min) / range) * height; 
    return `${i === 0 ? 'M' : 'L'}${x},${y}`;
  }).join(' ');

  return pathD;
};

onMounted(async () => {
  try {
    indices.value = await marketApi.getIndices();
  } catch (error) {
    console.error('지수 로딩 실패', error);
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div class="w-full bg-white py-4 border-b border-gray-100">
    <div class="max-w-6xl mx-auto px-6">
      <!-- 로딩 상태 -->
      <div v-if="loading" class="flex space-x-6 animate-pulse">
        <div v-for="i in 3" :key="i" class="h-16 bg-gray-100 rounded-lg flex-1"></div>
      </div>

      <!-- 지수 리스트 -->
      <div v-else class="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-8">
        <div 
          v-for="item in indices" 
          :key="item.id" 
          class="flex items-center justify-between p-4 rounded-xl hover:bg-gray-50 transition-colors cursor-pointer group"
        >
          <!-- 왼쪽: 정보 -->
          <div>
            <div class="text-sm text-gray-500 font-medium mb-1">{{ item.name }}</div>
            <div class="flex items-end gap-2">
              <span class="text-lg font-bold text-gray-900 leading-none">
                {{ item.value.toLocaleString() }}
              </span>
              <span 
                class="text-xs font-medium leading-none mb-0.5"
                :class="item.isUp ? 'text-[#e22a40]' : 'text-[#2e68ff]'"
              >
                {{ item.isUp ? '+' : '' }}{{ item.change }} ({{ item.rate }}%)
              </span>
            </div>
          </div>

          <!-- 오른쪽: 미니 차트 -->
          <div class="w-[60px] h-[30px]">
            <svg width="60" height="30" viewBox="0 0 60 30" class="overflow-visible">
              <path
                :d="getSvgPath(item.chartData)"
                fill="none"
                :stroke="item.isUp ? '#e22a40' : '#2e68ff'"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>