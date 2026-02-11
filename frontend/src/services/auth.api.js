import axios from "axios";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api";
const ACCESS_KEY = "access_token";
const REFRESH_KEY = "refresh_token";

const instance = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
  withCredentials: true, // 쿠키 대비용(로컬에선 영향 적음)
});

// ---- 요청 인터셉터: auth 엔드포인트는 Authorization 제외 ----
instance.interceptors.request.use((config) => {
  const url = config.url || "";
  const isAuthEndpoint =
    url.includes("/users/auth/login") ||
    url.includes("/users/auth/signup") ||
    url.includes("/users/auth/refresh") ||
    url.includes("/users/auth/logout");

  if (!isAuthEndpoint) {
    const access = localStorage.getItem(ACCESS_KEY);
    if (access) {
      config.headers = config.headers || {};
      if (!config.headers["Authorization"]) {
        config.headers["Authorization"] = `Bearer ${access}`;
      }
    }
  }
  return config;
});

// ---- 인증 API 래퍼 ----
export const authApi = {
  signup: (userData) => instance.post("/users/auth/signup", userData),

  // 일반 로그인: 응답 토큰을 localStorage에 저장
  login: async (credentials) => {
    const resp = await instance.post("/users/auth/login", credentials);
    const { access, refresh } = resp.data || {};
    if (access) {
      localStorage.setItem(ACCESS_KEY, access);
      instance.defaults.headers.common["Authorization"] = `Bearer ${access}`;
    }
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
    return resp;
  },

  logout: async () => {
    const refresh = localStorage.getItem(REFRESH_KEY);
    try {
      await instance.post("/users/auth/logout", { refresh });
    } finally {
      delete instance.defaults.headers.common["Authorization"];
      localStorage.removeItem(ACCESS_KEY);
      localStorage.removeItem(REFRESH_KEY);
    }
  },

  refreshToken: () => {
    const refresh = localStorage.getItem(REFRESH_KEY);
    return instance.post("/users/auth/refresh", { refresh });
  },

  // 프로필/설문/선호
  getProfile: () => instance.get("/users/profile"),
  updateNickname: (nickname) =>
    instance.patch("/users/profile/nickname", { nickname }),
  saveSurvey: (payload) => instance.post("/users/survey/save", payload),
  getSurvey: () => instance.get("/users/survey/current"),
  getSurveyStatus: () => instance.get("/users/survey/status"),
  savePreference: (payload) => instance.post("/users/preference/save", payload),

  // AI 분석
  recommendPortfolio: (payload) =>
    instance.post("/analysis/recommend/portfolio", payload),
  rebalancePortfolio: (portfolioId, payload) =>
    instance.post(`/analysis/rebalance/portfolio/${portfolioId}`, payload),
  comparePortfolio: (payload) =>
    instance.post("/analysis/compare/portfolio", payload),

  // 포트폴리오 관리
  getPortfolioList: () => instance.get("/portfolios/list"),
  getPortfolioDetail: (id) => instance.get(`/portfolios/${id}`),
  getRepresentativePortfolio: () => instance.get("/portfolios/representative"),
  savePortfolio: (payload) => instance.post("/portfolios/save", payload),
  updatePortfolio: (id, payload) =>
    instance.patch(`/portfolios/${id}/update`, payload),
  setRepresentative: (id) =>
    instance.post("/portfolios/representative", { id }),
  deletePortfolio: (id) => instance.delete(`/portfolios/${id}/delete`),

  // 이름만 다른 중복 함수(유지 필요 없으면 제거 가능)
  comparePortfolios: (payload) =>
    instance.post("/analysis/compare/portfolio", payload),
};

// 401 동시 요청 큐
const enqueue = (cb) => {
  (window.__refreshQueue = window.__refreshQueue || []).push(cb);
};
const flush = (newAccess) => {
  (window.__refreshQueue || []).forEach((cb) => cb(newAccess));
  window.__refreshQueue = [];
};


// ---- 응답 인터셉터: login/refresh 응답 토큰 동기화 + 401 자동 리프레시 ----
instance.interceptors.response.use(
  (res) => {
    try {
      const url = (res.config?.url || "").toString();
      const data = res.data || {};

      // ✅ 앞/뒤 슬래시 유무 상관없이 감지
      const isAuthCall = /\/?users\/auth\/(login|refresh)/.test(url);

      if (isAuthCall) {
        const { access, refresh } = data;
        if (access) {
          localStorage.setItem(ACCESS_KEY, access);
          instance.defaults.headers.common["Authorization"] = `Bearer ${access}`;
        }
        if (refresh) {
          localStorage.setItem(REFRESH_KEY, refresh);
        }
      }
    } catch (_) {}
    return res;
  },
  async (error) => {
    const original = error.config || {};
    const status = error.response?.status || 0;
    const url = (original?.url || "").toString();

    // ✅ 로그인/리프레시는 리프레시 루프 제외
    const isAuthCall = /\/?users\/auth\/(login|refresh)/.test(url);
    const hasRefresh = !!localStorage.getItem(REFRESH_KEY);

    if (status === 401 && !original._retry && !isAuthCall && hasRefresh) {
      original._retry = true;

      // 동시 401 → 큐잉
      if (window.__isRefreshing) {
        return new Promise((resolve, reject) => {
          (window.__refreshQueue = window.__refreshQueue || []).push(
            (newAccess) => {
              original.headers = original.headers || {};
              original.headers["Authorization"] = `Bearer ${newAccess}`;
              instance.request(original).then(resolve).catch(reject);
            }
          );
        });
      }

      window.__isRefreshing = true;
      try {
        const resp = await authApi.refreshToken();
        const { access, refresh } = resp.data || {};

        if (access) {
          localStorage.setItem(ACCESS_KEY, access);
          instance.defaults.headers.common["Authorization"] = `Bearer ${access}`;
        }
        if (refresh) {
          localStorage.setItem(REFRESH_KEY, refresh);
        }

        // 대기열 재시도
        const q = window.__refreshQueue || [];
        q.forEach((cb) => cb(access));
        window.__refreshQueue = [];
        window.__isRefreshing = false;

        original.headers = original.headers || {};
        if (access) {
          original.headers["Authorization"] = `Bearer ${access}`;
        }
        return instance.request(original);
      } catch (e) {
        window.__isRefreshing = false;
        window.__refreshQueue = [];
        localStorage.removeItem(ACCESS_KEY);
        localStorage.removeItem(REFRESH_KEY);
        return Promise.reject(e);
      }
    }

    return Promise.reject(error);
  }
);

export default instance;