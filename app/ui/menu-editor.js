import { authenticatedFetch } from './session.js';

export function editorState() { return { loading: false, error: '', saved: false }; }

export async function saveMenuItem(state, session, restaurantId, itemId, form, fetcher = fetch) {
  if (state.loading) return;
  state.error = ''; state.saved = false;
  if (!['staff', 'admin'].includes(session.user?.role)) {
    state.error = 'Staff or admin access required.'; return;
  }
  if (!form.name.trim() || form.name.trim().length > 200 || !/^\d{1,8}(\.\d{1,2})?$/.test(form.price) || Number(form.price) <= 0) {
    state.error = 'Enter a name and a positive price with at most two decimal places.'; return;
  }
  state.loading = true;
  try {
    const response = await authenticatedFetch(session, `/restaurants/${restaurantId}/menu-items${itemId ? `/${itemId}` : ''}`, {
      method: itemId ? 'PATCH' : 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: form.name.trim(), price: form.price, available: form.available }),
    }, fetcher);
    if (!response.ok) {
      state.error = response.status === 403 ? 'You are not assigned to this restaurant.'
        : response.status === 404 ? 'Restaurant or menu item not found.'
          : response.status === 422 ? 'Check the name, price and availability.'
            : 'Could not confirm the save. Refresh the menu before trying again.';
      return;
    }
    state.saved = true;
    return true;
  } catch { state.error = session.error || 'Could not confirm the save. Refresh the menu before trying again.'; }
  finally { state.loading = false; }
}
