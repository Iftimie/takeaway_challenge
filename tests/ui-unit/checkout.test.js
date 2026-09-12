import { test } from 'node:test';
import assert from 'node:assert/strict';
import { checkoutState, placeOrder } from '../../app/ui/checkout.js';

function fixture() {
  const values = new Map();
  const storage = { getItem: key => values.get(key) ?? null, setItem: (key, value) => values.set(key, value), removeItem: key => values.delete(key) };
  return { storage, state: checkoutState(storage), session: { user: { id: 1, role: 'customer' }, token: 'token' },
    cart: { restaurant: { id: 2 }, items: [{ id: 3, quantity: 2 }] }, details: { name: ' Name ', address: ' Address ' } };
}
const reply = (status, body = {}) => ({ status, json: async () => body });

test('uncertain checkout preserves key and payload across refresh and uses server total', async () => {
  const f = fixture(); const requests = [];
  await placeOrder(f.state, f.session, f.cart, f.details, f.storage, async (url, options) => {
    requests.push(options); throw new Error('Lost response');
  });
  const restored = checkoutState(f.storage);
  f.cart.items[0].quantity = 99;
  const order = await placeOrder(restored, f.session, f.cart, { name: 'Changed', address: 'Changed' }, f.storage, async (url, options) => {
    requests.push(options); return reply(200, { id: 7, total: '31.00' });
  });
  assert.deepEqual(requests[0], requests[1]);
  assert.equal(JSON.parse(requests[1].body).items[0].quantity, 2);
  assert.equal(order.total, '31.00');
  assert.equal(checkoutState(f.storage).pending, null);
});

test('rejected checkout permits correction while server failure retains the request', async () => {
  for (const status of [403, 404, 409, 422, 503]) {
    const f = fixture();
    await placeOrder(f.state, f.session, f.cart, f.details, f.storage, async () => reply(status));
    assert.equal(Boolean(f.state.pending), status === 503);
    assert.ok(f.state.error);
    assert.equal(f.state.order, null);
  }
});

test('expired authentication keeps checkout and rejects another customer', async () => {
  const f = fixture();
  await placeOrder(f.state, f.session, f.cart, f.details, f.storage, async () => reply(401));
  assert.equal(f.session.user, null);
  assert.ok(f.state.pending);
  f.session.user = { id: 2, role: 'customer' };
  await placeOrder(f.state, f.session, f.cart, f.details, f.storage, () => assert.fail('Must not send'));
  assert.match(f.state.error, /account that started/);
});

test('double submission sends once and successful creation returns confirmation', async () => {
  const f = fixture(); let finish; let calls = 0;
  const fetcher = () => { calls++; return new Promise(resolve => { finish = resolve; }); };
  const first = placeOrder(f.state, f.session, f.cart, f.details, f.storage, fetcher);
  await placeOrder(f.state, f.session, f.cart, f.details, f.storage, fetcher);
  assert.equal(calls, 1);
  finish(reply(201, { id: 8 })); await first;
  assert.equal(f.state.order.id, 8);
});

test('invalid input, staff access and unavailable storage never send an order', async () => {
  for (const problem of ['empty', 'staff', 'storage']) {
    const f = fixture();
    if (problem === 'empty') f.details.name = ' ';
    if (problem === 'staff') f.session.user.role = 'staff';
    if (problem === 'storage') f.storage.setItem = () => { throw new Error(); };
    await placeOrder(f.state, f.session, f.cart, f.details, f.storage, () => assert.fail('Must not send'));
    assert.ok(f.state.error);
    assert.equal(f.state.pending, null);
  }
});
