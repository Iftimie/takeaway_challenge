import { test, expect } from '@playwright/test';
import { database } from './database.js';

test('demo-admin-staff-customer-full-order-lifecycle', async ({ page }) => {
  test.skip(Boolean(process.env.UI_BASE_URL), 'Demo requires the isolated fixture database');
  test.setTimeout(120_000);
  const password = 'Browser-test-password-123!';
  const restaurants = ['Demo Pizza House', 'Demo Green Kitchen'];
  const staffEmails = ['demo-staff-one@example.com', 'demo-staff-two@example.com'];
  const restaurantIds = [];
  let orderId;
  const link = name => page.getByRole('link', { name, exact: true });
  const button = name => page.getByRole('button', { name, exact: true });

  async function login(email, identity) {
    await link('Log in').click();
    await page.getByLabel('Email', { exact: true }).fill(email);
    await page.getByLabel('Password', { exact: true }).fill(password);
    await button('Log in').click();
    await expect(page.getByText(identity, { exact: true })).toBeVisible();
  }
  async function logout() {
    await button('Log out').click();
    await expect(button('Log in')).toBeVisible();
  }
  async function openMenu(name) {
    await link('Restaurants').click();
    await expect(page.getByRole('region', { name: 'Restaurant list' })).toHaveAttribute('aria-busy', 'false');
    while (await button('Previous').isEnabled()) {
      await button('Previous').click();
      await expect(page.getByRole('region', { name: 'Restaurant list' })).toHaveAttribute('aria-busy', 'false');
    }
    const row = page.getByRole('listitem').filter({ hasText: name });
    while (!(await row.count())) {
      await expect(button('Next')).toBeEnabled();
      await button('Next').click();
      await expect(page.getByRole('region', { name: 'Restaurant list' })).toHaveAttribute('aria-busy', 'false');
    }
    await row.getByRole('link', { name: 'View menu', exact: true }).click();
    await expect(page.getByRole('heading', { name, exact: true })).toBeVisible();
  }
  async function checkOrder(status) {
    await link('My orders').click();
    await link(`Order #${orderId}`).click();
    await expect(page.getByText(`Status: ${status}`, { exact: true })).toBeVisible();
    await expect(page.getByText('Total: 19.00 EUR', { exact: true })).toBeVisible();
    await expect(page.getByRole('listitem')).toHaveCount(2);
    await expect(page.getByText('Deliver to: Browser Customer — 25 Demo Avenue', { exact: true })).toBeVisible();
  }

  try {
    await test.step('01-admin-logs-in-and-lists-restaurants', async () => {
      database('seed-menu');
      await page.goto('/ui/');
      await login('browser-admin@example.com', 'Browser Admin (admin)');
      await link('Restaurants').click();
      await expect(page.getByRole('listitem')).toHaveCount(2);
      await expect(page.getByText('Browser Restaurant 1', { exact: true })).toBeVisible();
    });
    for (const [index, name] of restaurants.entries()) {
      await test.step(`02-admin-creates-restaurant-${index + 1}`, async () => {
        await link('Create restaurant').click();
        await page.getByLabel('Restaurant name', { exact: true }).fill(name);
        await page.getByLabel('Restaurant address', { exact: true }).fill(`${index + 1} Demo Square`);
        await button('Create restaurant').click();
        await expect(page.getByRole('status')).toContainText(`Restaurant created: ${name}`);
        await link('Open restaurant menu').click();
        await expect(page.getByText('No menu items yet.', { exact: true })).toBeVisible();
        restaurantIds.push(page.url().match(/restaurants\/(\d+)\/menu/)[1]);
      });
    }
    for (const [index, email] of staffEmails.entries()) {
      await test.step(`03-admin-creates-and-assigns-staff-${index + 1}`, async () => {
        await link('Manage staff').click();
        await page.getByLabel('Staff name', { exact: true }).fill(`Demo Staff ${index + 1}`);
        await page.getByLabel('Staff email', { exact: true }).fill(email);
        await page.getByLabel('Initial password', { exact: true }).fill(password);
        await button('Create staff').click();
        await expect(page.getByText(new RegExp(`Staff created: Demo Staff ${index + 1}`))).toBeVisible();
        await page.getByLabel('Restaurant ID', { exact: true }).fill(restaurantIds[index]);
        await button('Assign restaurant').click();
        await expect(page.getByText(new RegExp(`assigned to restaurant #${restaurantIds[index]}\\.`))).toBeVisible();
      });
    }
    await test.step('04-admin-logs-out-staff-one-logs-in', async () => {
      await logout(); await login(staffEmails[0], 'Demo Staff 1 (staff)');
      await openMenu(restaurants[0]);
    });
    for (const [name, price] of [['Margherita', '12.50'], ['Garlic Bread', '6.50'], ['Tiramisu', '5.00']]) {
      await test.step(`05-staff-adds-${name.toLowerCase().replaceAll(' ', '-')}`, async () => {
        await page.getByLabel('Item name', { exact: true }).fill(name);
        await page.getByLabel('Price (EUR)', { exact: true }).fill(price);
        await button('Save menu item').click();
        await expect(page.getByText('Menu item saved.', { exact: true })).toBeVisible();
        await expect(page.getByLabel('Item name', { exact: true })).toHaveValue('');
      });
    }
    await test.step('06-staff-checks-third-menu-item-on-page-two', async () => {
      await button('Next').click();
      await expect(button('Add Tiramisu')).toBeVisible();
    });
    await test.step('07-staff-logs-out-customer-logs-in', async () => {
      await logout(); await login('browser-customer@example.com', 'Browser Customer (customer)');
      await openMenu(restaurants[0]);
    });
    await test.step('08-customer-adds-two-items-and-reviews-cart', async () => {
      await button('Add Margherita').click(); await button('Add Garlic Bread').click();
      await link('Cart (2)').click();
      await expect(page.getByRole('listitem')).toHaveCount(2);
      await expect(page.getByText('Estimated total: 19.00 EUR', { exact: true })).toBeVisible();
    });
    await test.step('09-customer-checks-out', async () => {
      await link('Checkout').click();
      await page.getByLabel('Delivery address', { exact: true }).fill('25 Demo Avenue');
      await button('Place order').click();
      await expect(page.getByRole('heading', { name: 'Order confirmed', exact: true })).toBeVisible();
      const href = await link('View order details').getAttribute('href');
      orderId = href.split('/').at(-1);
      await expect(link('Cart (0)')).toBeVisible();
    });
    await test.step('10-customer-checks-pending-order-and-logs-out', async () => {
      await checkOrder('pending'); await logout();
    });
    await test.step('11-staff-logs-in-and-opens-the-order', async () => {
      await login(staffEmails[0], 'Demo Staff 1 (staff)');
      await openMenu(restaurants[0]); await link('Manage orders').click();
      await expect(page.getByRole('article', { name: `Order #${orderId}`, exact: true })).toBeVisible();
    });
    for (const [action, status] of [['Accept order', 'accepted'], ['Mark out for delivery', 'out_for_delivery'], ['Mark delivered', 'delivered']]) {
      await test.step(`12-staff-marks-order-${status.replaceAll('_', '-')}`, async () => {
        const order = page.getByRole('article', { name: `Order #${orderId}`, exact: true });
        await order.getByRole('button', { name: action, exact: true }).click();
        await expect(order).toContainText(`Status: ${status}`);
      });
    }
    await test.step('13-staff-logs-out-customer-confirms-delivery', async () => {
      await logout(); await login('browser-customer@example.com', 'Browser Customer (customer)');
      await checkOrder('delivered');
      await page.reload();
      await expect(page.getByText('Status: delivered', { exact: true })).toBeVisible();
    });
  } finally { database('clean'); }
});
