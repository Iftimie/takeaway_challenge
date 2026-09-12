import { test, expect } from '@playwright/test';
import { database } from './database.js';

test('real-cart-quantities-refresh-and-restaurant-replacement', async ({ page }) => {
  test.skip(Boolean(process.env.UI_BASE_URL), 'Requires isolated fixture database');
  try {
    database('seed');
    await page.goto('/ui/');
    await page.getByRole('listitem').filter({ hasText: 'Browser Restaurant 1' }).getByRole('link').click();
    await expect(page.getByRole('button', { name: 'Add Test Meal 2', exact: true })).toBeDisabled();
    await page.getByRole('button', { name: 'Add Test Meal 1', exact: true }).click();
    await page.getByRole('link', { name: 'Cart (1)', exact: true }).click();
    const quantity = page.getByLabel('Quantity for Test Meal 1', { exact: true });
    await quantity.fill('3'); await quantity.press('Tab');
    await expect(page.getByText('Estimated total: 37.50 EUR', { exact: true })).toBeVisible();
    await page.reload();
    await expect(quantity).toHaveValue('3');
    await page.getByRole('link', { name: 'Restaurants', exact: true }).click();
    await page.getByRole('listitem').filter({ hasText: 'Browser Restaurant 2' }).getByRole('link').click();
    page.once('dialog', dialog => dialog.dismiss());
    await page.getByRole('button', { name: 'Add Other Restaurant Meal', exact: true }).click();
    await expect(page.getByRole('link', { name: 'Cart (3)', exact: true })).toBeVisible();
    page.once('dialog', dialog => dialog.accept());
    await page.getByRole('button', { name: 'Add Other Restaurant Meal', exact: true }).click();
    await page.getByRole('link', { name: 'Cart (1)', exact: true }).click();
    await expect(page.getByRole('listitem')).toHaveCount(1);
    await expect(page.getByRole('listitem')).toContainText('Other Restaurant Meal');
    await page.getByRole('button', { name: 'Remove Other Restaurant Meal', exact: true }).click();
    await expect(page.getByText('Your cart is empty.', { exact: true })).toBeVisible();
    await page.reload();
    await expect(page.getByText('Your cart is empty.', { exact: true })).toBeVisible();
  } finally { database('clean'); }
});
