import { defineConfig } from 'vite'

export default defineConfig({
  server: {
    host: '0.0.0.0',
    port: 4815,
    // 允许通过 ngrok 的临时域名访问开发服务器。
    allowedHosts: ['.ngrok-free.app', '.ngrok.app', '.trycloudflare.com'],
    proxy: {
      // 单一 ngrok 隧道同时转发前端和后端，避免浏览器访问远端时请求其自身 localhost。
      '/api': {
        target: 'http://api:8000',
        changeOrigin: true,
      },
    },
    watch: {
      // Docker Desktop/WSL 下文件事件可能不会透传，轮询可保证保存即更新。
      usePolling: true,
      interval: 250,
    },
  },
})
