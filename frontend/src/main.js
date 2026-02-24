import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { authApi } from './services/auth.api'

// import './style.css' // tailwind를 쓴다면 필요 (없으면 주석 처리)

const app = createApp(App)

app.use(createPinia())
app.use(router)

// 앱 마운트 전 CSRF 토큰 초기화 (금융 보안 정책)
authApi.initCsrf().then(() => {
    app.mount('#app')
}).catch(() => {
    // 초기화 실패해도 일단 마운트 (이후 API 요청 시 실패하며 에러 핸들링됨)
    app.mount('#app')
})