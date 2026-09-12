import { test, expect } from '@playwright/test';
import { database } from './database.js';

test('real-checkout-lost-response-refresh-and-retry-create-one-order', async ({ page }) => {
  test.skip(Boolean(process.env.UI_BASE_URL), 'Requires isolated fixture database');
  try {
    database('seed');
    await page.goto('/ui/');
    await page.getByRole('listitem').filter({ hasText: 'Browser Restaurant 1' }).getByRole('link').click();
    await page.getByRole('button', { name: 'Add Test Meal 1', exact: true }).click();
    await page.getByRole('link', { name: 'Cart (1)', exact: true }).click();
    await page.getByRole('link', { name: 'Checkout', exact: true }).click();
    await expect(page.getByText('as a customer, then return to checkout.', { exact: false })).toBeVisible();
    await page.getByRole('link', { name: 'Log in', exact: true }).first().click();
    await page.getByLabel('Email', { exact: true }).fill('browser-customer@example.com');
    await page.getByLabel('Password', { exact: true }).fill('Browser-test-password-123!');
    await page.getByRole('button', { name: 'Log in', exact: true }).click();
    await expect(page.getByText('Browser Customer (customer)', { exact: true })).toBeVisible();
    await page.getByRole('link', { name: 'Cart (1)', exact: true }).click();
    await page.getByRole('link', { name: 'Checkout', exact: true }).click();
    await expect(page.getByLabel('Delivery name', { exact: true })).toHaveValue('Browser Customer');
    await page.getByLabel('Delivery address', { exact: true }).fill('Delivery Street 10');
    let originalOrder;
    // Let the real server commit, then simulate losing its response on the network.
    await page.route('**/orders', async route => {
      const response = await route.fetch();
      expect(response.status()).toBe(201);
      originalOrder = await response.json();
      await route.abort();
    }, { times: 1 });
    await page.getByRole('button', { name: 'Place order', exact: true }).click();
    await expect(page.getByRole('alert')).toContainText('Could not confirm the order');
    await page.reload();
    await expect(page.getByText('Browser Customer — Delivery Street 10', { exact: true })).toBeVisible();
    const retry = page.waitForResponse(response => response.url().endsWith('/orders'));
    await page.getByRole('button', { name: 'Retry order', exact: true }).click();
    expect((await retry).status()).toBe(200);
    await expect(page.getByRole('heading', { name: 'Order confirmed', exact: true })).toBeVisible();
    await expect(page.getByText(`Order #${originalOrder.id} — pending`, { exact: true })).toBeVisible();
    await expect(page.getByText('Total: 12.50 EUR', { exact: true })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Cart (0)', exact: true })).toBeVisible();
    const orders = await page.evaluate(async () => (await fetch('/orders', {
      headers: { Authorization: `Bearer ${sessionStorage.getItem('takeaway.access_token')}` },
    })).json());
    expect(orders.map(order => order.id)).toEqual([originalOrder.id]);
  } finally { database('clean'); }
});
