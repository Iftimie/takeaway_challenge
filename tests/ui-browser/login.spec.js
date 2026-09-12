import { test, expect } from '@playwright/test';
import { database } from './database.js';

test('real-login-logout-refresh-and-expired-session', async ({ page }) => {
  test.skip(Boolean(process.env.UI_BASE_URL), 'Requires isolated fixture database');
  try {
    database('seed');
    await page.goto('/ui/#/login');
    await page.getByLabel('Email', { exact: true }).fill('browser-customer@example.com');
    await page.getByLabel('Password', { exact: true }).fill('wrong-password');
    await page.getByRole('button', { name: 'Log in', exact: true }).click();
    await expect(page.getByRole('alert')).toHaveText('Invalid email or password.');
    await expect(page.getByLabel('Password', { exact: true })).toHaveValue('');
    async function signIn() {
      await page.getByLabel('Email', { exact: true }).fill('browser-customer@example.com');
      await page.getByLabel('Password', { exact: true }).fill('Browser-test-password-123!');
      await page.getByRole('button', { name: 'Log in', exact: true }).click();
      await expect(page.getByText('Browser Customer (customer)', { exact: true })).toBeVisible();
    }
    await signIn();
    await page.getByRole('button', { name: 'Log out', exact: true }).click();
    await expect(page.getByLabel('Email', { exact: true })).toHaveValue('');
    await page.reload();
    await expect(page.getByRole('button', { name: 'Log in', exact: true })).toBeVisible();
    await signIn();
    await page.reload();
    await expect(page.getByText('Browser Customer (customer)', { exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Refresh account', exact: true })).toHaveCount(0);
    // Expiration is simulated only for this request; login uses the real backend.
    await page.route('**/users/me', route => route.fulfill({ status: 401, json: { detail: 'Invalid or expired access token' } }));
    await page.reload();
    await expect(page.getByRole('alert')).toContainText('Your login has expired');
    await expect(page.getByRole('button', { name: 'Log out', exact: true })).toHaveCount(0);
  } finally { database('clean'); }
});
