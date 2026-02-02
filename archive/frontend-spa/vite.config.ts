import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  
  return {
    plugins: [react()],
    server: {
      port: 5173,
      host: true,
      proxy: {
        '/api': {
          target: env.VITE_API_BASE_URL || 'http://localhost:5000',
          changeOrigin: true,
          secure: false
        },
        '/auth': {
          target: env.VITE_API_BASE_URL || 'http://localhost:5000', 
          changeOrigin: true,
          secure: false
        },
        '/socket.io': {
          target: env.VITE_WS_URL || 'http://localhost:5000',
          changeOrigin: true,
          ws: true
        }
      }
    },
    build: {
      outDir: 'dist',
      sourcemap: true,
      rollupOptions: {
        output: {
          manualChunks: {
            vendor: ['react', 'react-dom'],
            router: ['react-router-dom'],
            charts: ['recharts'],
            socket: ['socket.io-client']
          }
        }
      }
    },
    define: {
      global: 'globalThis'
    }
  };
});
