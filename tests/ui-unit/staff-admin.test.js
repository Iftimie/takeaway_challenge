import { test } from 'node:test';
import assert from 'node:assert/strict';
import { staffAdminState, createStaff, assignStaff } from '../../app/ui/staff-admin.js';
const auth = () => ({ user: { role: 'admin' }, token: 'test' });
const form = { name: ' Staff ', email: 'staff@example.com', password: 'Password123!' };
test('staff creation sends only expected fields; assignment uses returned ID', async () => {
  const state = staffAdminState();
  await createStaff(state, auth(), { ...form, role: 'admin' }, async (url, options) => {
    assert.equal(url, '/staff'); assert.equal(options.headers.Authorization, 'Bearer test');
    assert.deepEqual(JSON.parse(options.body), { ...form, name: 'Staff' });
    return { status: 201, json: async () => ({ id: 5 }) };
  });
  await assignStaff(state, auth(), state.staff.id, 3, async (url, options) => {
    assert.equal(url, '/staff/5/restaurants/3'); assert.equal(options.method, 'POST');
    return { status: 201, json: async () => ({ staff_id: 5, restaurant_id: 3 }) };
  });
  assert.equal(state.assignment.restaurant_id, 3);
});
test('invalid input and non-admin roles cannot send writes', async () => {
  const state = staffAdminState(); const fail = () => assert.fail();
  await createStaff(state, auth(), { ...form, password: 'tiny' }, fail); assert.ok(state.error);
  for (const id of [0, 1.5, 2147483648]) {
    await assignStaff(state, auth(), id, 1, fail); assert.ok(state.error);
  }
  for (const role of ['staff', 'customer']) {
    await createStaff(state, { user: { role } }, form, fail);
    await assignStaff(state, { user: { role } }, 1, 2, fail);
    assert.equal(state.error, 'Admin access required.');
  }
});
test('duplicates, missing staff and expiry report errors without success', async () => {
  const state = staffAdminState(); const session = auth();
  await createStaff(state, session, form, async () => ({ status: 409 }));
  assert.equal(state.error, 'Email already registered.');
  for (const status of [404, 409]) {
    await assignStaff(state, session, 1, 2, async () => ({ status, json: async () => ({ detail: 'Assignment rejected' }) }));
    assert.equal(state.error, 'Assignment rejected'); assert.equal(state.assignment, null);
  }
  await createStaff(state, session, form, async () => ({ status: 401 }));
  assert.equal(session.user, null); assert.match(state.error, /expired/);
});
test('pending creation blocks duplicate requests and network failures remain uncertain', async () => {
  const state = staffAdminState(); let reject;
  const first = createStaff(state, auth(), form, () => new Promise((_, fail) => { reject = fail; }));
  await createStaff(state, auth(), form, () => assert.fail());
  reject(new Error()); await first;
  assert.equal(state.staff, null); assert.match(state.error, /may have been created/);
});
