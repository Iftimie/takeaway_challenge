import { defineConfig } from '@playwright/test';

const externalURL = process.env.UI_BASE_URL;
const localURL = 'http://127.0.0.1:8766';
const python = process.platform === 'win32'
  ? '.venv/Scripts/python.exe' : '.venv/bin/python';

export default defineConfig({
  testDir: './tests/ui-browser',
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
    url: `${localURL}/ui/`,
    reuseExistingServer: false,
    stdout: 'ignore',
    stderr: 'ignore',
  },
});
