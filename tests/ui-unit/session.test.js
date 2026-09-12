import { test } from 'node:test';
import assert from 'node:assert/strict';
import { sessionState, login, logout, restoreSession } from '../../app/ui/session.js';

test('login gets server profile and logout clears identity', async () => {
  const state = sessionState();
  await login(state, 'admin@example.com', 'test-password', async (url, options) => {
    if (url === '/auth/login') {
      assert.deepEqual(JSON.parse(options.body), { email: 'admin@example.com', password: 'test-password' });
      return { ok: true, json: async () => ({ access_token: 'token' }) };
    }
    assert.equal(options.headers.Authorization, 'Bearer token');
    return { ok: true, json: async () => ({ role: 'admin' }) };
  });
  assert.equal(state.user.role, 'admin');
  assert.equal(state.token, 'token');
  logout(state);
  assert.equal(state.token, '');
  assert.equal(state.user, null);
});

test('invalid credentials and profile failure never create a session', async () => {
  const state = sessionState();
  await login(state, 'a@example.com', 'bad', async () => ({ status: 401, ok: false }));
  assert.equal(state.error, 'Invalid email or password.');
  await login(state, 'a@example.com', 'password', async url => url === '/auth/login'
    ? { ok: true, json: async () => ({ access_token: 'token' }) } : { ok: false });
  assert.equal(state.token, '');
  assert.equal(state.user, null);
  assert.equal(state.loading, false);
});

test('expired login clears identity but network failure allows retry', async () => {
  const state = sessionState();
  state.token = 'token';
  state.user = { role: 'staff' };
  await restoreSession(state, async () => { throw new Error('offline'); });
  assert.equal(state.token, 'token');
  await restoreSession(state, async () => ({ status: 401 }));
  assert.equal(state.token, '');
  assert.equal(state.user, null);
  assert.match(state.error, /expired/);
});

test('saved token restores on refresh and is removed on expiry or logout', async () => {
  const values = new Map();
  const storage = { getItem: key => values.get(key), setItem: (key, value) => values.set(key, value),
    removeItem: key => values.delete(key) };
  const state = sessionState(storage);
  await login(state, 'a@example.com', 'password', async url => ({ ok: true, json: async () =>
    url === '/auth/login' ? { access_token: 'saved-token' } : { name: 'Alex' } }));
  const restored = sessionState(storage);
  await restoreSession(restored, async (url, options) => {
    assert.equal(options.headers.Authorization, 'Bearer saved-token');
    return { ok: true, json: async () => ({ name: 'Alex' }) };
  });
  assert.equal(restored.user.name, 'Alex');
  await restoreSession(restored, async () => ({ status: 401 }));
  assert.equal(values.size, 0);
  storage.setItem('takeaway.access_token', 'another-token');
  logout(state);
  assert.equal(values.size, 0);
});
