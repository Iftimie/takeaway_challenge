import { test, expect } from '@playwright/test';
import { database } from './database.js';

test('real-staff-menu-create-edit-availability-and-admin-access', async ({ page }) => {
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
    async function menu(number) {
      await page.getByRole('link', { name: 'Restaurants', exact: true }).click();
      await page.getByRole('listitem').filter({ hasText: `Browser Restaurant ${number}` }).getByRole('link').click();
      await expect(page.getByRole('heading', { name: 'Manage menu', exact: true })).toBeVisible();
    }
    await login('browser-staff@example.com');
    await menu(1);
    await page.getByLabel('Item name', { exact: true }).fill('New soup');
    await page.getByLabel('Price (EUR)', { exact: true }).fill('4.50');
    await page.getByRole('button', { name: 'Save menu item', exact: true }).click();
    await expect(page.getByText('Menu item saved.', { exact: true })).toBeVisible();
    await page.getByRole('button', { name: 'Next', exact: true }).click();
    await page.getByRole('button', { name: 'Edit New soup', exact: true }).click();
    await page.getByLabel('Price (EUR)', { exact: true }).fill('5.25');
    await page.getByLabel('Available', { exact: true }).uncheck();
    await page.getByRole('button', { name: 'Save menu item', exact: true }).click();
    await expect(page.getByRole('button', { name: 'Add New soup', exact: true })).toBeDisabled();
    await page.reload();
    await page.getByRole('button', { name: 'Next', exact: true }).click();
    await expect(page.getByRole('region', { name: 'Restaurant menu', exact: true })).toContainText('5.25 EUR');
    await menu(2);
    await page.getByRole('button', { name: 'Edit Other Restaurant Meal', exact: true }).click();
    await page.getByRole('button', { name: 'Save menu item', exact: true }).click();
    await expect(page.getByRole('alert')).toContainText('not assigned');
    await page.getByRole('button', { name: 'Log out', exact: true }).click();
    await login('browser-admin@example.com');
    await menu(2);
    await page.getByRole('button', { name: 'Edit Other Restaurant Meal', exact: true }).click();
    await page.getByLabel('Price (EUR)', { exact: true }).fill('10.00');
    await page.getByRole('button', { name: 'Save menu item', exact: true }).click();
    await expect(page.getByText('Menu item saved.', { exact: true })).toBeVisible();
  } finally { database('clean'); }
});
