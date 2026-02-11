<!-- src/pages/OauthCallback.vue -->
<script setup>
import { onMounted } from "vue";
import { useRouter } from "vue-router";

import { useAuthStore } from "@/stores/auth";

const ACCESS_KEY = "access_token";
const REFRESH_KEY = "refresh_token";
const router = useRouter();
const authStore = useAuthStore();

onMounted(async () => {
  // URL 예: /oauth/callback#provider=google&access=...&refresh=...
  const hash = window.location.hash?.replace(/^#/, "") || "";
  const params = new URLSearchParams(hash);
  const access = params.get("access");
  const refresh = params.get("refresh");

  if (access) localStorage.setItem(ACCESS_KEY, access);
  if (refresh) localStorage.setItem(REFRESH_KEY, refresh);

  // 파싱 후 해시 제거(민감정보 흔적 제거)
  history.replaceState(null, "", window.location.pathname);
  
  // 유저 정보 로드 및 닉네임 체크
  await authStore.fetchUser();

  if (!authStore.user?.nickname) {
    router.replace("/onboarding/nickname");
  } else {
    router.replace("/");
  }
});
</script>

<template>
  <div class="p-6 text-sm text-gray-600">로그인 처리 중입니다…</div>
</template>
