<script setup>
import { computed } from 'vue';

const props = defineProps({
  assets: {
    type: Array, // Expected: Array of numbers [val1, val2, ...] OR Objects if refactored, but sticking to numbers for now based on usage
    required: true,
    default: () => []
  },
  labels: {
    type: Array,
    default: () => ['국내주식', '미국주식', '국내채권', '해외채권', '대체투자', '펀드', '현금성자산']
  },
  colors: {
    type: Array,
    default: () => ['#536dfe', '#3b82f6', '#10b981', '#34d399', '#f59e0b', '#8b5cf6', '#cbd5e1'] // 7 colors
    // STOCKS_KR(blue), STOCKS_GLB(lighter blue), BONDS_KR(green), BONDS_GLB(light green), ALTS(orange), FUNDS(purple), CASH(gray)
  },
  size: {
    type: String,
    default: 'w-20 h-20'
  },
  showTooltip: {
    type: Boolean,
    default: true
  }
});

const chartStyle = computed(() => {
  if (!props.assets || props.assets.length === 0) return 'background: #f3f4f6';
  
  let gradient = 'conic-gradient(';
  let currentPos = 0;
  
  props.assets.forEach((val, index) => {
    // If val is effectively 0, skip visual segment logic or just handle it naturally
    // conic-gradient handles 0-width segments fine
    const color = props.colors[index % props.colors.length];
    const segmentStart = currentPos;
    const segmentEnd = currentPos + val;
    
    gradient += `${color} ${segmentStart}% ${segmentEnd}%, `;
    currentPos = segmentEnd;
  });
  
  // Remove last comma and close
  gradient = gradient.slice(0, -2) + ')';
  
  return `background: ${gradient}`;
});

const sortedAssets = computed(() => {
  if (!props.assets) return [];
  return props.assets
    .map((val, i) => ({
      value: val,
      label: props.labels[i],
      color: props.colors[i % props.colors.length]
    }))
    .sort((a, b) => b.value - a.value);
});
</script>

<template>
  <div class="relative group cursor-help inline-block">
    
    <!-- 차트 본체 -->
    <div :class="[size, 'rounded-full relative shadow-sm flex-shrink-0']" :style="chartStyle">
      <div class="absolute inset-[20%] bg-white rounded-full flex items-center justify-center"></div>
    </div>

    <!-- ✅ 툴팁 수정: 위쪽(bottom-full) -> 왼쪽(right-full)으로 변경 -->
    <!-- z-index를 높여서 다른 요소 위로 뜨게 함 -->
    <!-- ✅ 툴팁 수정: 차트 정중앙에 오버레이 (잘림 방지) -->
    <div v-if="showTooltip" class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-48 bg-gray-900/95 text-white text-xs rounded-xl py-3 px-4 shadow-xl opacity-0 group-hover:opacity-100 transition-opacity duration-200 z-50 pointer-events-none backdrop-blur-sm border border-gray-700">
      
      <div class="flex flex-col gap-1.5">
        <div class="text-xs font-bold text-gray-400 mb-1 text-center">자산 구성</div>
        <div v-for="(item, i) in sortedAssets" :key="i" class="flex justify-between items-center" v-show="item.value > 0">
          <div class="flex items-center gap-1.5 overflow-hidden">
            <span class="w-1.5 h-1.5 rounded-full shrink-0" :style="{ backgroundColor: item.color }"></span>
            <span class="text-gray-200 truncate">{{ item.label || '기타' }}</span>
          </div>
          <span class="font-bold shrink-0 text-white">{{ item.value }}%</span>
        </div>
      </div>
    </div>

  </div>
</template>