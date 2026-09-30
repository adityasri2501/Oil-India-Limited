import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

const repositoryName = process.env.GITHUB_REPOSITORY?.split('/')[1];
const isUserOrOrganizationSite = repositoryName?.toLowerCase().endsWith('.github.io');
const githubPagesBase = repositoryName && !isUserOrOrganizationSite
  ? `/${repositoryName}/`
  : '/';

export default defineConfig({
  base: process.env.VITE_BASE_PATH || (process.env.GITHUB_ACTIONS ? githubPagesBase : '/'),
  plugins: [react(), tailwindcss()],
  server: {
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: process.env.PS120_API_TARGET || 'http://localhost:8000',
        changeOrigin: true,
        ws: true,
      },
    },
  },
});
