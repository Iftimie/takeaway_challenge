import { test, expect } from '@playwright/test';
import { database } from './database.js';

test('real-menu-pagination-availability-and-restaurant-isolation', async ({ page }) => {
  test.skip(Boolean(process.env.UI_BASE_URL), 'Requires isolated fixture database');
  try {
    database('seed');
    await page.goto('/ui/');
    await page.getByRole('listitem').filter({ hasText: 'Browser Restaurant 1' }).getByRole('link').click();
    await expect(page.getByRole('heading', { name: 'Browser Restaurant 1', exact: true })).toBeVisible();
    await expect(page.getByRole('listitem')).toHaveCount(2);
    await expect(page.getByRole('listitem').filter({ hasText: 'Test Meal 2' })).toContainText('Unavailable');
    await expect(page.getByRole('listitem').first()).toContainText('12.50 EUR');
    await expect(page.getByText('Other Restaurant Meal', { exact: true })).toHaveCount(0);
    await page.getByRole('button', { name: 'Next', exact: true }).click();
    await expect(page.getByRole('listitem')).toHaveCount(1);
    await expect(page.getByRole('listitem')).toContainText('Test Meal 3');
    await expect(page.getByRole('button', { name: 'Next', exact: true })).toBeDisabled();
    await page.getByRole('button', { name: 'Previous', exact: true }).click();
    await expect(page.getByRole('listitem')).toHaveCount(2);
    await page.reload();
    await expect(page.getByRole('listitem')).toHaveCount(2);
    await page.getByRole('link', { name: 'Back to restaurants' }).click();
    await page.getByRole('listitem').filter({ hasText: 'Browser Restaurant 2' }).getByRole('link').click();
    await expect(page.getByRole('heading', { name: 'Browser Restaurant 2', exact: true })).toBeVisible();
    await expect(page.getByRole('listitem')).toHaveCount(1);
    await expect(page.getByRole('listitem')).toContainText('Other Restaurant Meal');
    await page.getByRole('link', { name: 'Back to restaurants' }).click();
    await expect(page.getByRole('heading', { name: 'Restaurants', exact: true })).toBeVisible();
    await page.getByRole('button', { name: 'Next', exact: true }).click();
    await page.getByRole('listitem').filter({ hasText: 'Browser Restaurant 3' }).getByRole('link').click();
    await expect(page.getByText('No menu items yet.', { exact: true })).toBeVisible();
    await page.goto('/ui/#/restaurants/2147483647/menu');
    await expect(page.getByRole('alert')).toContainText('Restaurant not found.');
  } finally { database('clean'); }
});
