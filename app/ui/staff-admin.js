import { authenticatedFetch } from './session.js';

export function staffAdminState() { return { loading: false, error: '', staff: null, assignment: null }; }
export async function createStaff(state, session, form, fetcher = fetch) {
  if (state.loading) return;
  state.error = ''; state.staff = null;
  if (session.user?.role !== 'admin') { state.error = 'Admin access required.'; return; }
  if (!form.name.trim() || form.name.trim().length > 200 || !form.email.trim()
    || form.password.length < 8 || form.password.length > 128) {
    state.error = 'Check the name, email and password (8–128 characters).'; return;
  }
  state.loading = true;
  try {
    const response = await authenticatedFetch(session, '/staff', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: form.name.trim(), email: form.email.trim(), password: form.password }),
    }, fetcher);
    if (response.status === 201) state.staff = await response.json();
    else state.error = response.status === 409 ? 'Email already registered.'
      : response.status === 403 ? 'Admin access required.'
        : response.status === 422 ? 'Check the name, email and password.'
          : 'Could not confirm staff creation. The account may have been created; retrying may report an existing email.';
  } catch { state.error = session.error || 'Could not confirm staff creation. The account may have been created; retrying may report an existing email.'; }
  finally { state.loading = false; }
}

export async function assignStaff(state, session, staffId, restaurantId, fetcher = fetch) {
  if (state.loading) return;
  state.error = ''; state.assignment = null;
  if (session.user?.role !== 'admin') { state.error = 'Admin access required.'; return; }
  if (![staffId, restaurantId].every(id => Number.isInteger(id) && id >= 1 && id <= 2147483647)) {
    state.error = 'Enter valid staff and restaurant IDs.'; return;
  }
  state.loading = true;
  try {
    const response = await authenticatedFetch(session, `/staff/${staffId}/restaurants/${restaurantId}`, { method: 'POST' }, fetcher);
    if (response.status === 201) state.assignment = await response.json();
    else if ([404, 409].includes(response.status)) {
      const body = await response.json();
      state.error = body.detail;
    } else state.error = response.status === 403 ? 'Admin access required.'
      : 'Could not confirm assignment. Retrying may report that staff are already assigned.';
  } catch { state.error = session.error || 'Could not confirm assignment. Retrying may report that staff are already assigned.'; }
  finally { state.loading = false; }
}
