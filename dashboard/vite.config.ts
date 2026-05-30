import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000',
      '/articles': 'http://127.0.0.1:8000',
      '/search': 'http://127.0.0.1:8000',
      '/trending': 'http://127.0.0.1:8000',
      '/entities': 'http://127.0.0.1:8000'
    }
  }
})
