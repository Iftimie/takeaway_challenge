import { test } from 'node:test';
import assert from 'node:assert/strict';
import { menuRestaurantId, viewForRoute } from '../../app/ui/routes.js';
import { getMenuPage } from '../../app/ui/api.js';
import { menuState, loadMenu, canGoNextMenu } from '../../app/ui/menu.js';

test('menu routes accept only valid restaurant IDs', () => {
  assert.equal(menuRestaurantId('/restaurants/123/menu'), 123);
  assert.equal(viewForRoute('/restaurants/123/menu').title, 'Menu');
  for (const route of ['/restaurants/0/menu', '/restaurants/no/menu', '/restaurants/2147483648/menu']) {
    assert.equal(menuRestaurantId(route), 0);
    assert.equal(viewForRoute(route).title, 'Page not found');
  }
});

test('menu client fetches restaurant and bounded menu page; reports missing restaurant', async () => {
  const urls = [];
  await getMenuPage(7, 2, async url => {
    urls.push(url);
    return { ok: true, json: async () => url.includes('menu-items') ? [] : { id: 7 } };
  });
  assert.deepEqual(urls, ['/restaurants/7', '/restaurants/7/menu-items?limit=2&offset=2']);
  await assert.rejects(getMenuPage(7, 0, async () => ({ status: 404 })), /Restaurant not found/);
});

test('menu load handles pagination, empty results and retry', async () => {
  const state = menuState(7);
  await loadMenu(state, 0, async () => ({ restaurant: { name: 'Cafe' }, items: [{ id: 1 }, { id: 2 }] }));
  assert.equal(canGoNextMenu(state), true);
  await loadMenu(state, 2, async () => { throw new Error('Network error'); });
  assert.equal(state.loading, false);
  assert.equal(canGoNextMenu(state), false);
  assert.match(state.error, /Could not load menu/);
  await loadMenu(state, 2, async () => ({ restaurant: { name: 'Cafe' }, items: [] }));
  assert.equal(state.error, '');
  assert.deepEqual(state.items, []);
  assert.equal(canGoNextMenu(state), false);
  await loadMenu(state, 0, async () => { throw new Error('Restaurant not found.'); });
  assert.equal(state.error, 'Restaurant not found.');
});
