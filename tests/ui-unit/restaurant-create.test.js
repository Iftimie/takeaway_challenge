import { test } from 'node:test';
import assert from 'node:assert/strict';
import { restaurantCreateState, createRestaurant } from '../../app/ui/restaurant-create.js';
const auth = () => ({ user: { role: 'admin' }, token: 'test' });
const form = { name: ' Cafe ', address: ' Main Street ' };
test('restaurant creation sends trimmed fields and uses server identity', async () => {
  const state = restaurantCreateState();
  await createRestaurant(state, auth(), { ...form, role: 'admin' }, async (url, options) => {
    assert.equal(url, '/restaurants'); assert.equal(options.method, 'POST');
    assert.equal(options.headers.Authorization, 'Bearer test');
    assert.deepEqual(JSON.parse(options.body), { name: 'Cafe', address: 'Main Street' });
    return { status: 201, json: async () => ({ id: 12, name: 'Cafe' }) };
  });
  assert.equal(state.restaurant.id, 12);
});
test('invalid restaurant fields and non-admins send no request', async () => {
  for (const data of [{ ...form, name: ' ' }, { ...form, address: ' ' }, { ...form, name: 'x'.repeat(201) }, { ...form, address: 'x'.repeat(1001) }]) {
    const state = restaurantCreateState();
    await createRestaurant(state, auth(), data, () => assert.fail()); assert.ok(state.error);
  }
  for (const role of ['staff', 'customer', undefined]) {
    const state = restaurantCreateState();
    await createRestaurant(state, { user: { role } }, form, () => assert.fail());
    assert.equal(state.error, 'Admin access required.');
  }
});
test('failed and uncertain creation never reports success and expiry clears login', async () => {
  for (const status of [401, 403, 422, 500]) {
    const state = restaurantCreateState(); const session = auth();
    await createRestaurant(state, session, form, async () => ({ status }));
    assert.equal(state.restaurant, null); assert.ok(state.error);
    if (status === 401) assert.equal(session.user, null);
  }
  const state = restaurantCreateState();
  await createRestaurant(state, auth(), form, async () => { throw new Error(); });
  assert.match(state.error, /Check the restaurant list/);
});
test('double submit creates only one request', async () => {
  const state = restaurantCreateState(); let finish;
  const first = createRestaurant(state, auth(), form, () => new Promise(resolve => { finish = resolve; }));
  await createRestaurant(state, auth(), form, () => assert.fail());
  finish({ status: 201, json: async () => ({ id: 1 }) }); await first;
  assert.equal(state.loading, false);
});
