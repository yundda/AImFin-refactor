import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      name: "home",
      component: () => import("@/pages/Home.vue"),
      meta: { requiresAuth: true }
    },
    {
      path: "/auth/login",
      name: "login",
      component: () => import("@/pages/auth/Login.vue")
    },
    {
      path: "/auth/signup",
      name: "signup",
      component: () => import("@/pages/auth/Signup.vue")
    },
    {
      path: "/user/mypage",
      name: "mypage",
      component: () => import("@/pages/user/MyPage.vue"),
      meta: { requiresAuth: true },
    },
    {
      path: "/survey",
      name: "survey",
      component: () => import("@/pages/Survey.vue"),
      meta: { requiresAuth: true },
    },
    {
      path: "/survey/result",
      name: "survey-result",
      component: () => import("@/pages/SurveyResult.vue"),
      meta: { requiresAuth: true },
    },
    {
      path: "/portfolio/create",
      name: "portfolio-create",
      component: () => import("@/pages/PortfolioCreate.vue"),
      meta: { requiresAuth: true },
    },
    {
      path: "/portfolio/result",
      name: "portfolio-result",
      component: () => import("@/pages/PortfolioResult.vue"),
      meta: { requiresAuth: true },
    },
    {
      path: "/portfolio/compare",
      name: "portfolio-compare",
      component: () => import("@/pages/PortfolioCompare.vue"),
      meta: { requiresAuth: true },
    },
    {
      path: "/onboarding/nickname",
      name: "nickname-setup",
      component: () => import("@/pages/onboarding/NicknameSetup.vue"),
    },
    {
      path: "/oauth/callback",
      name: "oauth-callback",
      component: () => import("@/pages/OauthCallback.vue"),
    },
  ],
});

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore();

  // 앱 시작 시 또는 새로고침 시 인증 상태 확인
  if (!authStore.isAuthenticated && !authStore.user) {
    await authStore.checkAuth();
  }

  // 1. 이동하려는 페이지가 '인증이 필요한(requiresAuth)' 페이지인지 확인
  if (to.matched.some((record) => record.meta.requiresAuth)) {
    // 2. 로그인 상태가 아니면 로그인 페이지로
    if (!authStore.isAuthenticated) {
      next({ name: "login" });
    } else {
      // 3. 로그인 상태면 통과
      next();
    }
  } else {
    // 4. 인증이 필요 없는 페이지 (로그인/회원가입 등)
    // 이미 로그인한 상태에서 로그인/회원가입 접근 시 홈으로 리다이렉트
    if (
      authStore.isAuthenticated &&
      (to.name === "login" || to.name === "signup")
    ) {
      next({ name: "home" });
    } else {
      next();
    }
  }
});

export default router;
