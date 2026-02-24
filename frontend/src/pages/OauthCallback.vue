<!-- src/pages/OauthCallback.vue -->
<script setup>
import { onMounted } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const router = useRouter();
const authStore = useAuthStore();

onMounted(async () => {
  // 사용자가 소셜 로그인을 성공하면 서버가 쿠키(HttpOnly)를 브라우저에 심어줍니다.
  // 이 페이지는 리다이렉트 완료 후 유저 정보를 가져와서 로그인 상태를 확정하는 역할을 합니다.
  
  try {
    // 유저 정보 로드 (이미 쿠키가 세팅되어 있으므로 인증 성공)
    await authStore.fetchUser();

    if (!authStore.user?.nickname) {
      router.replace("/onboarding/nickname");
    } else {
      router.replace("/");
    }
  } catch (error) {
    console.error("OAuth callback processing failed", error);
    router.replace("/login");
  } finally {
    // 민감한 정보(provider 등)가 포함되었을 수 있으므로 해시 제거
    history.replaceState(null, "", window.location.pathname);
  }
});
</script>

<template>
  <div class="flex items-center justify-center min-h-screen p-6 text-sm text-gray-600 bg-gray-50">
    <div class="text-center">
      <div class="mb-4 animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
      <p>보안 인증 처리 중입니다…</p>
    </div>
  </div>
</template>
