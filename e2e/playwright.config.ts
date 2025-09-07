import { defineConfig, devices } from '@playwright/test';

const baseURL = process.env.E2E_BASE_URL || 'http://127.0.0.1:5173';

export default defineConfig({
  testDir: './tests',
  retries: 2,
  timeout: 30_000,
  use: {
    baseURL,
    trace: 'on-first-retry'
  },
  reporter: [['list'], ['html', { open: 'never', outputFolder: 'playwright-report' }]],
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
});
