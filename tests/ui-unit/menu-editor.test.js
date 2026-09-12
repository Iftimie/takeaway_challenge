import { test } from 'node:test';
import assert from 'node:assert/strict';
import { editorState, saveMenuItem } from '../../app/ui/menu-editor.js';
const form = { name: ' Soup ', price: '12.50', available: false };
const auth = () => ({ user: { role: 'staff' }, token: 'test' });

test('create and edit send explicit fields and decimal price strings', async () => {
  for (const id of [null, 4]) {
    const state = editorState();
    await saveMenuItem(state, auth(), 2, id, form, async (url, options) => {
      assert.equal(url, `/restaurants/2/menu-items${id ? '/4' : ''}`);
      assert.equal(options.method, id ? 'PATCH' : 'POST');
      assert.deepEqual(JSON.parse(options.body), { name: 'Soup', price: '12.50', available: false });
      assert.equal(options.headers.Authorization, 'Bearer test');
      return { ok: true };
    });
    assert.equal(state.saved, true);
  }
});
test('invalid price, name and customer access never send a write', async () => {
  for (const changes of [{ price: '0' }, { price: '1.234' }, { price: 'NaN' }, { name: ' ' }]) {
    const state = editorState();
    await saveMenuItem(state, auth(), 2, null, { ...form, ...changes }, () => assert.fail());
    assert.ok(state.error);
  }
  const state = editorState();
  await saveMenuItem(state, { user: { role: 'customer' } }, 2, null, form, () => assert.fail());
  assert.match(state.error, /Staff or admin/);
});
test('rejections and uncertain saves do not report success; expiry clears login', async () => {
  for (const status of [401, 403, 404, 422, 500]) {
    const state = editorState(); const session = auth();
    await saveMenuItem(state, session, 2, 4, form, async () => ({ ok: false, status }));
    assert.ok(state.error); assert.equal(state.saved, false);
    if (status === 401) assert.equal(session.user, null);
  }
});
