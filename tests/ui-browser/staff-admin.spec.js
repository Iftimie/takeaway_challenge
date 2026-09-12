import { test, expect } from '@playwright/test';
import { database } from './database.js';
test('real-admin-creates-assigns-staff-and-staff-can-manage-menu', async ({ page }) => {
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
    await page.getByRole('listitem').filter({ hasText: 'Browser Restaurant 1' }).getByRole('link').click();
    const menuURL = page.url(); const restaurantId = menuURL.match(/restaurants\/(\d+)\/menu/)[1];
    await page.getByRole('link', { name: 'Manage staff', exact: true }).click();
    await page.getByLabel('Staff name', { exact: true }).fill('New Staff');
    await page.getByLabel('Staff email', { exact: true }).fill('new-staff@example.com');
    await page.getByLabel('Initial password', { exact: true }).fill('Browser-test-password-123!');
    await page.getByRole('button', { name: 'Create staff', exact: true }).click();
    await expect(page.getByRole('status')).toContainText('Staff created: New Staff');
    await expect(page.getByLabel('Initial password', { exact: true })).toHaveValue('');
    await expect(page.getByLabel('Staff ID', { exact: true })).not.toHaveValue('');
    await page.getByLabel('Restaurant ID', { exact: true }).fill(restaurantId);
    await page.getByRole('button', { name: 'Assign restaurant', exact: true }).click();
    await expect(page.getByText(new RegExp(`assigned to restaurant #${restaurantId}`))).toBeVisible();
    await page.getByRole('button', { name: 'Assign restaurant', exact: true }).click();
    await expect(page.getByRole('alert')).toHaveText('Staff already assigned to restaurant');
    await page.getByRole('button', { name: 'Log out', exact: true }).click();
    await login('new-staff@example.com');
    await expect(page.getByRole('link', { name: 'Manage staff', exact: true })).toHaveCount(0);
    await page.goto(menuURL);
    await page.getByRole('button', { name: 'Edit Test Meal 1', exact: true }).click();
    await page.getByLabel('Price (EUR)', { exact: true }).fill('13.00');
    await page.getByRole('button', { name: 'Save menu item', exact: true }).click();
    await expect(page.getByText('Menu item saved.', { exact: true })).toBeVisible();
    await page.goto('/ui/#/staff');
    await expect(page.getByText('Admin access required.', { exact: true })).toBeVisible();
  } finally { database('clean'); }
});
