import { test, expect } from '@playwright/test';
import { database } from './database.js';

test('real-staff-orders-pagination-status-lifecycle-and-unassigned-denial', async ({ page }) => {
  test.skip(Boolean(process.env.UI_BASE_URL), 'Requires isolated fixture database');
  try {
    database('seed-staff-orders');
    await page.goto('/ui/#/login');
    await page.getByLabel('Email', { exact: true }).fill('browser-staff@example.com');
    await page.getByLabel('Password', { exact: true }).fill('Browser-test-password-123!');
    await page.getByRole('button', { name: 'Log in', exact: true }).click();
    await expect(page.getByRole('button', { name: 'Log out', exact: true })).toBeVisible();
    async function openOrders(number) {
      await page.getByRole('link', { name: 'Restaurants', exact: true }).click();
      await page.getByRole('listitem').filter({ hasText: `Browser Restaurant ${number}` }).getByRole('link').click();
      await page.getByRole('link', { name: 'Manage orders', exact: true }).click();
    }
    await openOrders(1);
    await expect(page.getByRole('article')).toHaveCount(2);
    await page.getByRole('button', { name: 'Next', exact: true }).click();
    await expect(page.getByRole('article')).toHaveCount(1);
    await expect(page).toHaveURL(/orders\?page=2$/);
    await page.reload();
    await expect(page.getByRole('article')).toHaveCount(1);
    await expect(page.getByText('Page 2', { exact: true })).toBeVisible();
    await page.goBack();
    await expect(page.getByRole('article')).toHaveCount(2);
    await page.goForward();
    await expect(page.getByRole('article')).toHaveCount(1);
    await expect(page.getByRole('button', { name: 'Next', exact: true })).toBeDisabled();
    await page.getByRole('button', { name: 'Previous', exact: true }).click();
    const order = page.getByRole('article').first();
    await order.getByRole('button', { name: 'Accept order', exact: true }).click();
    await expect(order).toContainText('Status: accepted');
    await order.getByRole('button', { name: 'Mark out for delivery', exact: true }).click();
    await order.getByRole('button', { name: 'Mark delivered', exact: true }).click();
    await expect(order).toContainText('Status: delivered');
    await expect(order.getByRole('button')).toHaveCount(0);
    await page.reload();
    await expect(order).toContainText('Status: delivered');
    await expect(page.getByRole('button', { name: 'Refresh', exact: true })).toHaveCount(0);
    await openOrders(2);
    await expect(page.getByRole('alert')).toContainText('not assigned');
    await expect(page.getByRole('article')).toHaveCount(0);
  } finally { database('clean'); }
});
