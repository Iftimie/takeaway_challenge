import { test, expect } from '@playwright/test';
import { database } from './database.js';

test('real-admin-creates-restaurant-and-staff-cannot-open-form', async ({ page }) => {
  test.skip(Boolean(process.env.UI_BASE_URL), 'Requires isolated fixture database');
  try {
    database('seed-menu');
    async function login(email) {
      await page.goto('/ui/#/login');
      await page.getByLabel('Email', { exact: true }).fill(email);
      await page.getByLabel('Password', { exact: true }).fill('Browser-test-password-123!');
      await page.getByRole('button', { name: 'Log in', exact: true }).click();
      await expect(page.getByRole('button', { name: 'Log out', exact: true })).toBeVisible();
    }
    await login('browser-admin@example.com');
    await page.getByRole('link', { name: 'Restaurants', exact: true }).click();
    await expect(page.getByRole('listitem')).toHaveCount(2);
    await page.getByRole('link', { name: 'Create restaurant', exact: true }).click();
    await page.getByLabel('Restaurant name', { exact: true }).fill(' ');
    await page.getByLabel('Restaurant address', { exact: true }).fill('New Street 5');
    await page.getByRole('button', { name: 'Create restaurant', exact: true }).click();
    await expect(page.getByRole('alert')).toContainText('Enter a name');
    await page.getByLabel('Restaurant name', { exact: true }).fill('New Cafe');
    await page.getByRole('button', { name: 'Create restaurant', exact: true }).click();
    await expect(page.getByRole('status')).toContainText('Restaurant created: New Cafe');
    await page.getByRole('link', { name: 'Open restaurant menu', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'New Cafe', exact: true })).toBeVisible();
    await expect(page.getByText('No menu items yet.', { exact: true })).toBeVisible();
    await page.reload();
    await expect(page.getByRole('heading', { name: 'New Cafe', exact: true })).toBeVisible();
    await page.getByRole('link', { name: 'Restaurants', exact: true }).click();
    await page.getByRole('button', { name: 'Next', exact: true }).click();
    await expect(page.getByRole('listitem').filter({ hasText: 'New Cafe' })).toBeVisible();
    await page.getByRole('button', { name: 'Log out', exact: true }).click();
    await login('browser-staff@example.com');
    await expect(page.getByRole('link', { name: 'Create restaurant', exact: true })).toHaveCount(0);
    await page.goto('/ui/#/restaurants/new');
    await expect(page.getByText('Admin access required.', { exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Create restaurant', exact: true })).toHaveCount(0);
  } finally { database('clean'); }
});
