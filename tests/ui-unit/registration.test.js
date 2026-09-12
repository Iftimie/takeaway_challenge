import { test } from 'node:test';
import assert from 'node:assert/strict';
import { registrationState, registerCustomer } from '../../app/ui/registration.js';

const form = { email: 'a@example.com', password: 'test-password', name: 'Alex', default_address: '  ' };

test('registration sends only customer fields and accepts success', async () => {
  const state = registrationState();
  await registerCustomer(state, { ...form, role: 'admin' }, async (url, options) => {
    assert.equal(url, '/auth/register');
    assert.deepEqual(JSON.parse(options.body), { ...form, default_address: null });
    return { status: 201 };
  });
  assert.equal(state.success, true);
  assert.equal(state.loading, false);
});

test('duplicate and validation errors appear on the matching fields', async () => {
  const state = registrationState();
  await registerCustomer(state, form, async () => ({ status: 409 }));
  assert.match(state.fields.email, /already exists/);
  await registerCustomer(state, form, async () => ({ status: 422, json: async () => ({ detail: [
    { loc: ['body', 'name'], msg: 'Name is required' },
  ] }) }));
  assert.equal(state.fields.name, 'Name is required');
  assert.equal(state.fields.email, undefined);
  assert.equal(state.success, false);
});

test('network failure preserves retry and blocks concurrent submissions', async () => {
  const state = registrationState();
  let reject;
  const pending = registerCustomer(state, form, () => new Promise((resolve, fail) => { reject = fail; }));
  await registerCustomer(state, form, () => assert.fail('duplicate submission'));
  reject(new Error('offline'));
  await pending;
  assert.match(state.error, /Could not confirm/);
  assert.equal(state.loading, false);
});
