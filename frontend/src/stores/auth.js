import { defineStore } from 'pinia';
import { ref } from 'vue';
import { authApi } from '@/services/auth.api';

export const useAuthStore = defineStore('auth', () => {
    const user = ref(null);
    const isAuthenticated = ref(false);

    // 현재 사용자 프로필 가져오기
    const fetchUser = async () => {
        try {
            const response = await authApi.getProfile();
            user.value = response.data;
            isAuthenticated.value = true;
            return response.data;
        } catch (error) {
            console.error('Failed to fetch user:', error);
            user.value = null;
            isAuthenticated.value = false;
            // throw error; // Don't throw, just clear state
        }
    };

    // 로그인 (일반)
    const login = async (id, password) => {
        try {
            // Note: Login.vue passes id/password, but API expects email/password
            await authApi.login({
                email: id,
                password: password
            });
            // 쿠키가 세팅되었으므로 프로필을 조회하면 됨
            await fetchUser();
        } catch (error) {
            console.error('Login failed:', error);
            throw error;
        }
    };

    // 로그아웃
    const logout = async () => {
        try {
            await authApi.logout();
        } catch (error) {
            console.warn('Logout API error:', error);
        } finally {
            user.value = null;
            isAuthenticated.value = false;
        }
    };

    // 앱 시작 시 세션 복구 시도
    const checkAuth = async () => {
        if (!isAuthenticated.value) {
            await fetchUser();
        }
    };

    return {
        user,
        isAuthenticated,
        fetchUser,
        login,
        logout,
        checkAuth
    };
});
