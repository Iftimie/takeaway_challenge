import { test } from 'node:test';
import assert from 'node:assert/strict';
import { listRestaurants, PAGE_SIZE } from '../../app/ui/api.js';
import { restaurantState, canGoNext, loadRestaurants } from '../../app/ui/restaurants.js';

test('API requests bounded pagination and rejects HTTP failures', async () => {
  assert.deepEqual(await listRestaurants(20, async url => {
    assert.equal(url, `/restaurants?limit=${PAGE_SIZE}&offset=20`);
    return { ok: true, json: async () => [{ id: 1 }] };
  }), [{ id: 1 }]);
  await assert.rejects(listRestaurants(0, async () => ({ ok: false })));
});

test('loading prevents duplicate requests and enables Next only for a full page', async () => {
  const state = restaurantState();
  let resolve;
  const pending = loadRestaurants(state, 0, () => new Promise(done => { resolve = done; }));
  assert.equal(state.loading, true);
  assert.equal(canGoNext(state), false);
  await loadRestaurants(state, 20, () => assert.fail('Duplicate request'));
  resolve(Array.from({ length: PAGE_SIZE }, (_, id) => ({ id })));
  await pending;
  assert.equal(state.loading, false);
  assert.equal(canGoNext(state), true);
  state.offset = 10000;
  assert.equal(canGoNext(state), false);
  await loadRestaurants(state, 20, async () => []);
  assert.equal(state.offset, 20);
  assert.equal(state.loaded, true);
  assert.equal(canGoNext(state), false);
});

test('failure hides stale data and retry recovers the requested page', async () => {
  const state = restaurantState();
  state.items = [{ id: 1 }];
  await loadRestaurants(state, 20, async () => { throw new Error('Network failure'); });
  assert.equal(state.offset, 20);
  assert.equal(state.loading, false);
  assert.ok(state.error);
  assert.deepEqual(state.items, []);
  assert.equal(canGoNext(state), false);
  await loadRestaurants(state, state.offset, async offset => {
    assert.equal(offset, 20);
    return [{ id: 21 }];
  });
  assert.equal(state.error, '');
  assert.deepEqual(state.items, [{ id: 21 }]);
});
