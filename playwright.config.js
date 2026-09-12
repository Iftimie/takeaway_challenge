import { defineConfig } from '@playwright/test';
import { python } from './tests/ui-browser/database.js';

const externalURL = process.env.UI_BASE_URL;
const localURL = 'http://127.0.0.1:8766';

export default defineConfig({
  testDir: './tests/ui-browser',
  globalSetup: './tests/ui-browser/database.js',
  workers: 1,
  retries: 0,
  reporter: 'list',
  use: {
    baseURL: externalURL || localURL,
    browserName: 'chromium',
    trace: 'retain-on-failure',
    video: 'on'
  },
  // An explicit URL uses an existing deployment; otherwise own a temporary server.
  webServer: externalURL ? undefined : {
    command: `"${python}" -m uvicorn app.main:app --host 127.0.0.1 --port 8766 --no-access-log`,
    env: {
      POSTGRES_DB: 'takeaway_browser_test', POSTGRES_USER: 'browser_test',
      POSTGRES_PASSWORD: 'browser_test_only', POSTGRES_HOST: '127.0.0.1',
      POSTGRES_PORT: '55432',
    },
    url: `${localURL}/ui/`,
    reuseExistingServer: false,
    stdout: 'ignore',
    stderr: 'ignore',
  },
});
