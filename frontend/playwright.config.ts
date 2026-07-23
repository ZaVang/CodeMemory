import { defineConfig, devices } from '@playwright/test'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

export default defineConfig({
  testDir: path.resolve(__dirname, './tests'),
  timeout: 60000,
  retries: 1,
  use: {
    baseURL: 'http://127.0.0.1:5300',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: 'npm run dev -- --host 127.0.0.1',
    cwd: __dirname,
    url: 'http://127.0.0.1:5300',
    reuseExistingServer: !process.env.CI,
    timeout: 60000,
  },
})
