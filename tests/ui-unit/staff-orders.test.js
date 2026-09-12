import { test } from 'node:test';
import assert from 'node:assert/strict';
import { staffOrdersState, loadStaffOrders, advanceOrder } from '../../app/ui/staff-orders.js';
import { staffRestaurantId, staffOrdersPage } from '../../app/ui/routes.js';
const auth = () => ({ user: { role: 'staff' }, token: 'test' });
test('staff order URL page defaults and API offset boundary', () => {
  assert.equal(staffRestaurantId('/restaurants/3/orders?page=2'), 3);
  assert.equal(staffOrdersPage('/restaurants/3/orders?page=2'), 2);
  assert.equal(staffOrdersPage('/restaurants/3/orders?page=5001'), 5001);
  for (const value of ['', '0', '-1', '1.5', 'abc', '5002', '999999999999999999999']) {
    assert.equal(staffOrdersPage(`/restaurants/3/orders?page=${value}`), 1);
  }
  assert.equal(staffOrdersPage('/restaurants/3/orders'), 1);
});
test('staff list uses bounded authenticated pagination and validated routes', async () => {
  assert.equal(staffRestaurantId('/restaurants/3/orders'), 3);
  assert.equal(staffRestaurantId('/restaurants/2147483648/orders'), 0);
  const state = staffOrdersState();
  await loadStaffOrders(state, auth(), 3, 2, async (url, options) => {
    assert.equal(url, '/restaurants/3/orders?limit=2&offset=2');
    assert.equal(options.headers.Authorization, 'Bearer test');
    return { ok: true, json: async () => [] };
  });
  assert.equal(state.loaded, true); assert.deepEqual(state.items, []);
});
test('status changes advance one step and replace the server snapshot', async () => {
  const state = staffOrdersState(); state.items = [{ id: 1, status: 'pending' }];
  for (const status of ['accepted', 'out_for_delivery', 'delivered']) {
    await advanceOrder(state, auth(), 3, state.items[0], async (url, options) => {
      assert.equal(url, '/restaurants/3/orders/1/status');
      assert.deepEqual(JSON.parse(options.body), { status });
      return { ok: true, json: async () => ({ id: 1, status }) };
    });
    assert.equal(state.items[0].status, status);
  }
  await advanceOrder(state, auth(), 3, state.items[0], () => assert.fail('Delivered is terminal'));
});
test('conflict or network failure requires refresh before another update', async () => {
  for (const fetcher of [async () => ({ ok: false, status: 409 }), async () => { throw new Error(); }]) {
    const state = staffOrdersState(); const order = { id: 1, status: 'pending' };
    await advanceOrder(state, auth(), 3, order, fetcher);
    assert.match(state.error, /Reload the page/);
    await advanceOrder(state, auth(), 3, order, () => assert.fail('Refresh first'));
  }
});
test('permission and expiry errors clear list and customer cannot send updates', async () => {
  for (const status of [403, 401]) {
    const state = staffOrdersState(); state.items = [{ id: 1 }]; const session = auth();
    await loadStaffOrders(state, session, 3, 0, async () => ({ ok: false, status }));
    assert.deepEqual(state.items, []); assert.ok(state.error);
    if (status === 401) assert.equal(session.user, null);
  }
  await advanceOrder(staffOrdersState(), { user: { role: 'customer' } }, 3, { status: 'pending' }, () => assert.fail());
});
