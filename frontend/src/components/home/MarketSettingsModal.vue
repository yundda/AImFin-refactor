<script setup>
import { ref, onMounted, watch } from 'vue';
import { marketApi } from '@/services/market-index.api';

const props = defineProps({
  isOpen: Boolean
});

const emit = defineEmits(['close', 'saved']);

const selectedIndices = ref([]);
const newTicker = ref("");
const loading = ref(false);

const predefined = [
  { label: '코스피', value: 'KS11' },
  { label: '코스닥', value: 'KQ11' },
  { label: '원/달러', value: 'USD/KRW' },
  { label: 'S&P 500', value: 'US500' },
  { label: '나스닥', value: 'IXIC' },
  { label: '다우 존스', value: 'DJI' },
  { label: '삼성전자', value: '005930' },
];

const nameMap = ref({});

// 초기화 시 프리셋 매핑 적용
predefined.forEach(p => nameMap.value[p.value] = p.label);

const fetchPref = async () => {
    loading.value = true;
    try {
        // 병렬 호출 (하나가 실패해도 나머지 처리)
        const [prefRes, indicesRes] = await Promise.allSettled([
            marketApi.getPreference(),
            marketApi.getIndices()
        ]);

        // 1. 인덱스 데이터로 이름 매핑 업데이트
        if (indicesRes.status === 'fulfilled' && Array.isArray(indicesRes.value)) {
            indicesRes.value.forEach(d => {
                if (d.id && d.name) nameMap.value[d.id] = d.name;
            });
        }

        // 2. 선호도 목록 적용
        if (prefRes.status === 'fulfilled' && prefRes.value && prefRes.value.indices) {
            selectedIndices.value = [...prefRes.value.indices];
        } else {
            // 실패하거나 없으면 (첫 로드 등) 기본값 유지할지, 아니면 빈 배열? 
            // 기존에 값이 있다면 건드리지 않음 (선택된 상태 유지)
            if (selectedIndices.value.length === 0) {
                 selectedIndices.value = ['USD/KRW', 'KS11', 'KQ11'];
            }
        }
    } catch (e) {
        console.error("fetchPref error", e);
    } finally {
        loading.value = false;
    }
};

onMounted(() => {
    if (props.isOpen) fetchPref();
});

watch(() => props.isOpen, (newVal) => {
    if (newVal) fetchPref();
});

const toggleIndex = (val) => {
    if (selectedIndices.value.includes(val)) {
        selectedIndices.value = selectedIndices.value.filter(x => x !== val);
    } else {
        selectedIndices.value.push(val);
    }
};

const searchResults = ref([]);
let searchTimer = null;

const onSearchInput = () => {
    if (searchTimer) clearTimeout(searchTimer);
    const query = newTicker.value.trim();
    if (!query) {
        searchResults.value = [];
        return;
    }
    
    // 300ms 디바운스
    searchTimer = setTimeout(async () => {
        const res = await marketApi.searchStocks(query);
        searchResults.value = res;
    }, 300);
};

const selectSearchResult = (item) => {
    // item: { name: "삼성전자", code: "005930" }
    nameMap.value[item.code] = item.name; // 이름 매핑 저장
    
    if (!selectedIndices.value.includes(item.code)) {
        selectedIndices.value.push(item.code);
    }
    newTicker.value = "";
    searchResults.value = [];
};

const addCustom = () => {
    const val = newTicker.value.trim().toUpperCase();
    if (val && !selectedIndices.value.includes(val)) {
        selectedIndices.value.push(val);
        newTicker.value = "";
    }
};

const save = async () => {
    loading.value = true;
    try {
        await marketApi.updatePreference(selectedIndices.value);
        emit('saved');
        emit('close');
    } catch (e) {
        alert("저장 실패");
    } finally {
        loading.value = false;
    }
};
</script>

<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
    <div class="bg-white rounded-lg shadow-xl w-[500px] min-h-[700px] p-6 max-h-[80vh] overflow-y-auto flex flex-col relative">
      <button @click="$emit('close')" class="absolute top-4 right-4 text-gray-400 hover:text-gray-600">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
      <h2 class="text-lg font-bold mb-4">티커 설정</h2>
      
      <p class="text-sm text-gray-500 mb-2">보고 싶은 지수나 티커를 선택하세요.</p>
      
      <!-- 인기 목록 -->
      <div class="flex flex-wrap gap-2 mb-4">
        <button 
            v-for="item in predefined" 
            :key="item.value"
            @click="toggleIndex(item.value)"
            class="px-3 py-1 rounded-full text-xs font-medium border transition-colors"
            :class="selectedIndices.includes(item.value) 
                ? 'bg-[#283593]/10 text-[#283593] border-[#283593]/20' 
                : 'bg-gray-50 text-gray-600 border-gray-200 hover:bg-gray-100'"
        >
            {{ item.label }}
        </button>
      </div>

      <!-- 선택된 목록 및 커스텀 추가 -->
      <div class="mb-4">
        <label class="block text-xs font-bold text-gray-700 mb-1">선택된 목록</label>
        <div class="flex flex-wrap gap-2 p-3 bg-gray-50 rounded min-h-[50px]">
            <span 
                v-for="ticker in selectedIndices" 
                :key="ticker"
                class="inline-flex items-center px-2 py-1 rounded bg-white border border-gray-200 text-xs text-gray-800"
            >
                {{ nameMap[ticker] || ticker }}
                <button @click="toggleIndex(ticker)" class="ml-1 text-gray-400 hover:text-red-500">×</button>
            </span>
            <span v-if="selectedIndices.length === 0" class="text-xs text-gray-400">선택된 항목 없음</span>
        </div>
      </div>

      <div class="mb-6">
        <label class="block text-xs font-bold text-gray-700 mb-1">직접 추가 (티커 또는 종목명)</label>
        <div class="flex gap-2 relative">
            <input 
                v-model="newTicker" 
                @keyup.enter="addCustom"
                @input="onSearchInput"
                type="text" 
                placeholder="예: 삼성전자, TSLA" 
                class="flex-1 border border-gray-300 rounded px-2 py-1 text-sm focus:outline-none focus:border-[#283593]"
            >
            <button @click="addCustom" class="bg-[#283593] text-white px-3 py-1 rounded text-sm hover:bg-[#1a237e]">추가</button>
            
            <!-- 검색 결과 드롭다운: 인풋 바로 아래 배치 -->
            <div v-if="searchResults.length > 0" class="absolute left-0 right-0 top-full mt-1 bg-white border border-gray-200 shadow-lg rounded max-h-60 overflow-y-auto z-50">
                <div 
                    v-for="item in searchResults" 
                    :key="item.code"
                    @click="selectSearchResult(item)"
                    class="px-3 py-2 hover:bg-gray-100 cursor-pointer text-sm flex justify-between items-center"
                >
                    <span>{{ item.name }}</span>
                    <span class="text-xs text-gray-400">{{ item.code }}</span>
                </div>
            </div>
        </div>
      </div>

      <div class="flex justify-end gap-2 mt-auto">
        <button @click="$emit('close')" class="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded text-sm">취소</button>
        <button @click="save" :disabled="loading" class="px-4 py-2 bg-[#283593] text-white rounded text-sm hover:bg-[#1a237e] disabled:opacity-50">
            {{ loading ? '저장 중...' : '저장' }}
        </button>
      </div>
    </div>
  </div>
</template>
