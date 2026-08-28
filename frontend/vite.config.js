import { defineConfig } from 'vite'

export default defineConfig({
  server: {
    host: '0.0.0.0',
    port: 4815,
    watch: {
      // Docker Desktop/WSL 下文件事件可能不会透传，轮询可保证保存即更新。
      usePolling: true,
      interval: 250,
    },
  },
})
