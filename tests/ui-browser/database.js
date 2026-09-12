import { execFileSync } from 'node:child_process';

export const python = process.platform === 'win32'
  ? '.venv/Scripts/python.exe' : '.venv/bin/python';

export function database(action) {
  execFileSync(python, ['tests/browser_db.py', action], { stdio: 'pipe' });
}

export default function setup() {
  if (process.env.UI_BASE_URL) return;
  database('prepare');
  return () => database('stop');
}
