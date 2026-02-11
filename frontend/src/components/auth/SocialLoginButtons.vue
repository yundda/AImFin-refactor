<script setup>
import { computed } from "vue";
import googleLogo from "@/assets/images/google-logo.png";
import kakaoLogo from "@/assets/images/kakao-logo.png";

const props = defineProps({
  mode: {
    type: String,
    default: "login",
    validator: (value) => ["login", "signup"].includes(value),
  },
});

const googleText = computed(() => {
  return props.mode === "login" ? "Google로 로그인하기" : "Google로 가입하기";
});

const kakaoText = computed(() => {
  return props.mode === "login"
    ? "카카오 계정으로 로그인하기"
    : "카카오 계정으로 가입하기";
});

// 환경변수에서 API URL 가져오기 (없으면 기본값)
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

const handleGoogleLogin = () => {
  // 구글 로그인 엔드포인트로 리다이렉트 (쿠키 인증 방식)
  window.location.href = `${API_URL}/users/auth/google/start`;
};

const handleKakaoLogin = () => {
  // 카카오 로그인 엔드포인트로 리다이렉트
  window.location.href = `${API_URL}/users/auth/kakao/start`;
};
</script>

<template>
  <div class="flex flex-col items-center mt-6 w-full space-y-3">
    <!-- 구분선 -->
    <div class="flex items-center w-full mb-2">
      <div class="flex-grow border-t border-gray-200"></div>
      <span
        class="flex-shrink-0 mx-4 text-xs text-gray-400 font-light tracking-widest"
        >또는</span
      >
      <div class="flex-grow border-t border-gray-200"></div>
    </div>

    <!-- 1. 구글 로그인 버튼 (흰색 배경) -->
    <button
      @click="handleGoogleLogin"
      class="w-full flex items-center justify-center bg-white border border-gray-300 rounded-md py-3 px-4 hover:bg-gray-50 transition-colors shadow-sm group"
    >
      <img :src="googleLogo" alt="Google" class="w-5 h-5 mr-3" />
      <span class="text-gray-700 font-medium text-sm group-hover:text-black">
        {{ googleText }}
      </span>
    </button>

    <!-- 2. 카카오 로그인 버튼 (노란색 배경 #FEE500) -->
    <button
      @click="handleKakaoLogin"
      class="w-full flex items-center justify-center bg-[#FEE500] rounded-md py-3 px-4 hover:bg-[#FDD835] transition-colors shadow-sm"
    >
      <!-- 카카오 아이콘 (로컬 이미지) -->
      <img :src="kakaoLogo" alt="Kakao" class="w-5 h-5 mr-3" />
      <!-- 카카오 텍스트 (보통 검정색보다는 아주 짙은 갈색/검정을 씁니다) -->
      <span class="text-[#3c1e1e] font-medium text-sm">
        {{ kakaoText }}
      </span>
    </button>
  </div>
</template>
