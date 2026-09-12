import { test, expect } from '@playwright/test';
import { database } from './database.js';

test('real-customer-registration-validation-duplicate-and-login', async ({ page }) => {
  test.skip(Boolean(process.env.UI_BASE_URL), 'Requires isolated fixture database');
  try {
    database('seed');
    await page.goto('/ui/#/register');
    await page.getByLabel('Email', { exact: true }).fill('browser-customer@example.com');
    await page.getByLabel('Password (8–128 characters)', { exact: true }).fill('New-customer-password!');
    await page.getByLabel('Name', { exact: true }).fill('   ');
    await page.getByRole('button', { name: 'Create account', exact: true }).click();
    await expect(page.getByRole('alert')).toHaveText('Please check the highlighted fields.');
    await expect(page.getByLabel('Name', { exact: true })).toHaveAttribute('aria-invalid', 'true');
    await page.getByLabel('Name', { exact: true }).fill('New Customer');
    await page.getByLabel('Password (8–128 characters)', { exact: true }).fill('New-customer-password!');
    await page.getByRole('button', { name: 'Create account', exact: true }).click();
    await expect(page.getByText('An account with this email already exists.', { exact: true })).toBeVisible();
    await page.getByLabel('Email', { exact: true }).fill('new-browser-customer@example.com');
    await page.getByLabel('Password (8–128 characters)', { exact: true }).fill('New-customer-password!');
    await page.getByRole('button', { name: 'Create account', exact: true }).click();
    await expect(page.getByText('Account created. You can now log in.', { exact: true })).toBeVisible();
    await page.getByRole('link', { name: 'Go to login', exact: true }).click();
    await page.getByLabel('Email', { exact: true }).fill('new-browser-customer@example.com');
    await page.getByLabel('Password', { exact: true }).fill('New-customer-password!');
    await page.getByRole('button', { name: 'Log in', exact: true }).click();
    await expect(page.getByText('New Customer (customer)', { exact: true })).toBeVisible();
  } finally { database('clean'); }
});
