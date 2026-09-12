import { test, expect } from '@playwright/test';
import { database } from './database.js';

test('real-order-history-pagination-details-refresh-and-logout', async ({ page }) => {
  test.skip(Boolean(process.env.UI_BASE_URL), 'Requires isolated fixture database');
  try {
    database('seed-orders');
    await page.goto('/ui/#/login');
    await page.getByLabel('Email', { exact: true }).fill('browser-customer@example.com');
    await page.getByLabel('Password', { exact: true }).fill('Browser-test-password-123!');
    await page.getByRole('button', { name: 'Log in', exact: true }).click();
    await page.getByRole('link', { name: 'My orders', exact: true }).click();
    const links = page.getByRole('link', { name: /^Order #/ });
    await expect(links).toHaveCount(2);
    const first = await links.first().textContent();
    await page.getByRole('button', { name: 'Next', exact: true }).click();
    await expect(links).toHaveCount(1);
    await expect(page.getByRole('button', { name: 'Next', exact: true })).toBeDisabled();
    await page.getByRole('button', { name: 'Previous', exact: true }).click();
    await page.getByRole('link', { name: first, exact: true }).click();
    await expect(page.getByText('Deliver to: Browser Customer — History Street 10', { exact: true })).toBeVisible();
    await expect(page.getByText('Total: 12.50 EUR', { exact: true })).toBeVisible();
    await page.reload();
    await expect(page.getByRole('heading', { name: first, exact: true })).toBeVisible();
    const refreshed = page.waitForResponse(response => /\/orders\/\d+$/.test(response.url()));
    await page.getByRole('button', { name: 'Refresh', exact: true }).click();
    expect((await refreshed).status()).toBe(200);
    await expect(page.getByText('Status: pending', { exact: true })).toBeVisible();
    await page.goto('/ui/#/orders/2147483647');
    await expect(page.getByRole('alert')).toHaveText('Order not found.');
    await page.getByRole('button', { name: 'Log out', exact: true }).click();
    await page.goto('/ui/#/orders');
    await expect(page.getByText('as a customer to view your orders.', { exact: false })).toBeVisible();
    await expect(links).toHaveCount(0);
  } finally { database('clean'); }
});
