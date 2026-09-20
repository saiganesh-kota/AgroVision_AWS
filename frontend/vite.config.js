import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const BACKEND = 'http://localhost:5001'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // historyApiFallback: serve index.html for all non-asset routes
    // This fixes the "Not Found" error when you refresh on a React page
    // like /analysis or /recommendation — Vite serves index.html and
    // React Router handles the route client-side, as it should.
    historyApiFallback: true,
    proxy: {
      '/predict':          { target: BACKEND, changeOrigin: true },
      '/weather':          { target: BACKEND, changeOrigin: true },
      '/chat':             { target: BACKEND, changeOrigin: true },
      '/health':           { target: BACKEND, changeOrigin: true },
      '/dashboard':        { target: BACKEND, changeOrigin: true },
      '/health-trend':     { target: BACKEND, changeOrigin: true },
      '/health-breakdown': { target: BACKEND, changeOrigin: true },
      '/history':          { target: BACKEND, changeOrigin: true },
      '^/scan/.+':         { target: BACKEND, changeOrigin: true },  // only /scan/:id API calls, not /scan page
      '/fields':           { target: BACKEND, changeOrigin: true },
      '/geo-points':       { target: BACKEND, changeOrigin: true },
      '/uploads':          { target: BACKEND, changeOrigin: true },
      '/suppliers':        { target: BACKEND, changeOrigin: true },
      '/feedback':         { target: BACKEND, changeOrigin: true },
      '/schemes':          { target: BACKEND, changeOrigin: true },
      '/contacts':         { target: BACKEND, changeOrigin: true },
      '/pest-alerts':      { target: BACKEND, changeOrigin: true },
      '/soil-params':      { target: BACKEND, changeOrigin: true },
      '/weather-risk':     { target: BACKEND, changeOrigin: true },
      '/carbon-footprint': { target: BACKEND, changeOrigin: true },
      '/certificate':      { target: BACKEND, changeOrigin: true },
    }
  }
})
