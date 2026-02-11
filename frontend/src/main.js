import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'

// import './style.css' // tailwind를 쓴다면 필요 (없으면 주석 처리)

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')