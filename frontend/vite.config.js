import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  server: {
    proxy: {
      // Все запросы, начинающиеся с /api
      '/api': {
        // будут перенаправлены на ваш Flask-сервер
        target: 'http://127.0.0.1:5000',
        // Это необходимо, чтобы сервер бэкенда мог корректно обработать запрос
        changeOrigin: true,
      }
    }
  }
})
