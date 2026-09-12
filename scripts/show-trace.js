import { readdir } from 'node:fs/promises';
import { join, dirname, basename } from 'node:path';
import { createInterface } from 'node:readline/promises';
import { spawn } from 'node:child_process';
import { createRequire } from 'node:module';

async function findTraces(directory) {
  let entries;
  try {
    entries = await readdir(directory, { withFileTypes: true });
  } catch (error) {
    if (error.code === 'ENOENT') return [];
    throw error;
  }
  const traces = [];
  for (const entry of entries) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) traces.push(...await findTraces(path));
    else if (entry.name === 'trace.zip') traces.push(path);
  }
  return traces.sort();
}

const traces = await findTraces('test-results');
if (!traces.length) {
  console.log('No traces found. Run npm run test:trace first.');
} else {
  traces.forEach((path, index) => console.log(`${index + 1}. ${basename(dirname(path))}`));
  const prompt = createInterface({ input: process.stdin, output: process.stdout });
  const answer = await prompt.question('Open trace number (Enter to cancel): ');
  prompt.close();
  if (answer.trim()) {
    const index = Number(answer) - 1;
    if (!Number.isInteger(index) || index < 0 || index >= traces.length) {
      console.error('Invalid trace number.');
      process.exitCode = 1;
    } else {
      const require = createRequire(import.meta.url);
      const cli = require.resolve('@playwright/test/cli');
      // Pass the filename as an argument, never as shell command text.
      const child = spawn(process.execPath, [cli, 'show-trace', traces[index]], { stdio: 'inherit' });
      child.on('error', error => { console.error(error.message); process.exitCode = 1; });
      child.on('exit', code => { process.exitCode = code ?? 1; });
    }
  }
}
