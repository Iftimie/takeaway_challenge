import { test, expect } from '@playwright/test';

test('navigation and browser history update the visible view', async ({ page }) => {
  await page.goto('/ui/');
  await expect(page.getByRole('heading', { name: 'Restaurants', exact: true })).toBeVisible();
  await page.getByRole('link', { name: 'Log in', exact: true }).click();
  await expect(page).toHaveURL(/#\/login$/);
  await expect(page.getByRole('heading', { name: 'Log in', exact: true })).toBeVisible();
  await page.goBack();
  await expect(page.getByRole('heading', { name: 'Restaurants', exact: true })).toBeVisible();
  await page.goForward();
  await expect(page.getByRole('heading', { name: 'Log in', exact: true })).toBeVisible();
});

test('a direct hash URL survives refresh', async ({ page }) => {
  await page.goto('/ui/#/login');
  await expect(page.getByRole('heading', { name: 'Log in', exact: true })).toBeVisible();
  await page.reload();
  await expect(page).toHaveURL(/#\/login$/);
  await expect(page.getByRole('heading', { name: 'Log in', exact: true })).toBeVisible();
});
