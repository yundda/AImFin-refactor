import axios from "axios";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

// CSRF 토큰을 메모리에 안전하게 보관 (XSS 방지)
let memoizedCsrfToken = "";

const instance = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
  withCredentials: true, // 쿠키 전송에 필수
});

// ---- 요청 인터셉터: CSRF 토큰 주입 ----
instance.interceptors.request.use((config) => {
  // GET, HEAD, OPTIONS, TRACE 이외의 요청에는 CSRF 토큰 필수
  const method = (config.method || "").toUpperCase();
  if (!["GET", "HEAD", "OPTIONS", "TRACE"].includes(method)) {
    if (memoizedCsrfToken) {
      config.headers["X-CSRFToken"] = memoizedCsrfToken;
    }
  }
  return config;
});

// ---- 인증 API 래퍼 ----
export const authApi = {
  // CSRF 토큰 초기화
  initCsrf: async () => {
    try {
      const resp = await instance.get("/users/auth/csrf");
      memoizedCsrfToken = resp.data.csrftoken;
      return memoizedCsrfToken;
    } catch (e) {
      console.error("CSRF initialization failed", e);
    }
  },

  signup: (userData) => instance.post("/users/auth/signup", userData),

  login: (credentials) => instance.post("/users/auth/login", credentials),

  logout: async () => {
    try {
      await instance.post("/users/auth/logout");
    } finally {
      // 로그아웃 시 메모리 초기화
      // (Refresh 쿠키도 서버에서 삭제됨)
    }
  },

  refreshToken: () => instance.post("/users/auth/refresh"),

  // 프로필/설문/선호
  getProfile: () => instance.get("/users/profile"),
  updateNickname: (nickname) => instance.patch("/users/profile/nickname", { nickname }),
  saveSurvey: (payload) => instance.post("/users/survey/save", payload),
  getSurvey: () => instance.get("/users/survey/current"),
  getSurveyStatus: () => instance.get("/users/survey/status"),
  savePreference: (payload) => instance.post("/users/preference/save", payload),

  // AI 분석
  recommendPortfolio: (payload) => instance.post("/analysis/recommend/portfolio", payload),
  rebalancePortfolio: (portfolioId, payload) => instance.post(`/analysis/rebalance/portfolio/${portfolioId}`, payload),
  comparePortfolio: (payload) => instance.post("/analysis/compare/portfolio", payload),

  // 포트폴리오 관리
  getPortfolioList: () => instance.get("/portfolios/list"),
  getPortfolioDetail: (id) => instance.get(`/portfolios/${id}`),
  getRepresentativePortfolio: () => instance.get("/portfolios/representative"),
  savePortfolio: (payload) => instance.post("/portfolios/save", payload),
  updatePortfolio: (id, payload) => instance.patch(`/portfolios/${id}/update`, payload),
  setRepresentative: (id) => instance.post("/portfolios/representative", { id }),
  deletePortfolio: (id) => instance.delete(`/portfolios/${id}/delete`),
};

// ---- 응답 인터셉터: 401 자동 리프레시 (Silent Refresh) ----
let isRefreshing = false;
let refreshSubscribers = [];

const subscribeTokenRefresh = (cb) => {
  refreshSubscribers.push(cb);
};

const onRefreshed = () => {
  refreshSubscribers.forEach((cb) => cb());
  refreshSubscribers = [];
};

instance.interceptors.response.use(
  (res) => res,
  async (error) => {
    const originalRequest = error.config;
    const status = error.response ? error.response.status : null;

    // 401 에러이며, 인증 관련 API가 아니고, 재시도한 적이 없을 때
    if (status === 401 && !originalRequest._retry && !originalRequest.url.includes("/users/auth/")) {
      if (isRefreshing) {
        return new Promise((resolve) => {
          subscribeTokenRefresh(() => {
            resolve(instance(originalRequest));
          });
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        await authApi.refreshToken();
        isRefreshing = false;
        onRefreshed();
        return instance(originalRequest);
      } catch (refreshError) {
        isRefreshing = false;
        refreshSubscribers = [];
        // 리프레시 실패 시 로그인 페이지로 유도 등을 위해 에러 전파
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default instance;