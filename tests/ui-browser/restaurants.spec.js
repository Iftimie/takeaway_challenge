import { test, expect } from '@playwright/test';
import { database } from './database.js';
import { PAGE_SIZE } from '../../app/ui/api.js';

test('real-database-pagination-shows-two-restaurants-then-the-third', async ({ page }) => {
  test.skip(Boolean(process.env.UI_BASE_URL), 'Fixtures are restricted to the isolated local test app');
  try {
    database('seed');
    await page.goto('/ui/');
    await expect(page.getByRole('listitem')).toHaveText([
      'Browser Restaurant 1Test Street 1', 'Browser Restaurant 2Test Street 2',
    ]);
    await page.getByRole('button', { name: 'Next', exact: true }).click();
    await expect(page.getByRole('listitem')).toHaveText(['Browser Restaurant 3Test Street 3']);
    await expect(page.getByRole('button', { name: 'Next', exact: true })).toBeDisabled();
    await page.getByRole('button', { name: 'Previous', exact: true }).click();
    await expect(page.getByRole('listitem')).toHaveCount(2);
  } finally {
    database('clean');
  }
});

test('restaurant-loading-pagination-and-empty-last-page', async ({ page }) => {
  let release;
  const gate = new Promise(resolve => { release = resolve; });
  await page.route('**/restaurants?*', async route => {
    await gate;
    const offset = new URL(route.request().url()).searchParams.get('offset');
    await route.fulfill({ json: offset === '0'
      ? Array.from({ length: PAGE_SIZE }, (_, i) => ({ id: i + 1, name: `Restaurant ${i + 1}`, address: 'Main Street' }))
      : [] });
  });
  await page.goto('/ui/');
  await expect(page.getByRole('status')).toHaveText('Loading restaurants…');
  await expect(page.getByRole('button', { name: 'Next', exact: true })).toBeDisabled();
  release();
  await expect(page.getByRole('listitem')).toHaveCount(PAGE_SIZE);
  await page.getByRole('button', { name: 'Next', exact: true }).click();
  await expect(page.getByText('No more restaurants.', { exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Next', exact: true })).toBeDisabled();
  await page.getByRole('button', { name: 'Previous', exact: true }).click();
  await expect(page.getByRole('listitem')).toHaveCount(PAGE_SIZE);
});

test('failed-request-can-be-retried-and-an-empty-catalog-is-explained', async ({ page }) => {
  let failed = false;
  await page.route('**/restaurants?*', route => {
    if (!failed) {
      failed = true;
      return route.fulfill({ status: 503, json: { detail: 'Unavailable' } });
    }
    return route.fulfill({ json: [] });
  });
  await page.goto('/ui/');
  await expect(page.getByRole('alert')).toContainText('Could not load restaurants');
  await page.getByRole('button', { name: 'Retry', exact: true }).click();
  await expect(page.getByText('No restaurants yet.', { exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Previous', exact: true })).toBeDisabled();
});
