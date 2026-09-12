import { test } from 'node:test';
import assert from 'node:assert/strict';
import { ordersState, loadOrders, canGoNextOrders } from '../../app/ui/orders.js';
import { customerOrderId, viewForRoute } from '../../app/ui/routes.js';

const session = () => ({ user: { id: 1, role: 'customer' }, token: 'test' });
const reply = (status, data) => ({ status, ok: status === 200, json: async () => data });

test('order URLs validate IDs and list uses two-item authenticated pagination', async () => {
  assert.equal(customerOrderId('/orders/12'), 12);
  for (const path of ['/orders/0', '/orders/-1', '/orders/2147483648', '/orders/1/extra']) assert.equal(customerOrderId(path), 0);
  assert.equal(viewForRoute('/orders/12').title, 'Order details');
  const state = ordersState();
  await loadOrders(state, session(), 0, 2, async (url, options) => {
    assert.equal(url, '/orders?limit=2&offset=2');
    assert.equal(options.headers.Authorization, 'Bearer test');
    return reply(200, [{ id: 2 }, { id: 1 }]);
  });
  assert.equal(canGoNextOrders(state), true);
  state.offset = 10000;
  assert.equal(canGoNextOrders(state), false);
});

test('detail refresh replaces status; failures clear stale details and can retry', async () => {
  const state = ordersState(); const auth = session();
  await loadOrders(state, auth, 8, 0, async url => { assert.equal(url, '/orders/8'); return reply(200, { status: 'pending' }); });
  await loadOrders(state, auth, 8, 0, async () => reply(200, { status: 'accepted' }));
  assert.equal(state.order.status, 'accepted');
  await loadOrders(state, auth, 8, 0, async () => reply(404));
  assert.equal(state.order, null);
  assert.equal(state.error, 'Order not found.');
  await loadOrders(state, auth, 8, 0, async () => { throw new Error(); });
  assert.match(state.error, /Could not load/);
  await loadOrders(state, auth, 0, 0, async () => reply(200, []));
  assert.equal(state.loaded, true);
  assert.equal(state.error, '');
  assert.equal(canGoNextOrders(state), false);
});

test('expired login clears identity and non-customers send no request', async () => {
  const state = ordersState(); const auth = session();
  await loadOrders(state, auth, 0, 0, async () => reply(401));
  assert.equal(auth.user, null);
  assert.match(state.error, /expired/);
  for (const user of [null, { role: 'staff' }, { role: 'admin' }]) {
    await loadOrders(state, { user }, 0, 0, () => assert.fail('Must not send'));
  }
});

test('a second load is ignored while the first is pending', async () => {
  const state = ordersState(); let finish;
  const first = loadOrders(state, session(), 0, 0, () => new Promise(resolve => { finish = resolve; }));
  await loadOrders(state, session(), 0, 2, () => assert.fail('Duplicate request'));
  finish(reply(200, [])); await first;
  assert.equal(state.offset, 0);
});
