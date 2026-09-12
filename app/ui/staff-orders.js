import { PAGE_SIZE } from './api.js';
import { authenticatedFetch } from './session.js';

export const nextStatus = { pending: 'accepted', accepted: 'out_for_delivery', out_for_delivery: 'delivered' };
export function staffOrdersState() { return { items: [], offset: 0, loading: false, loaded: false, error: '' }; }

export async function loadStaffOrders(state, session, restaurantId, offset = 0, fetcher = fetch) {
  if (state.loading || !['staff', 'admin'].includes(session.user?.role)) return;
  state.loading = true; state.error = ''; state.loaded = false; state.items = []; state.offset = offset;
  try {
    const response = await authenticatedFetch(session, `/restaurants/${restaurantId}/orders?limit=${PAGE_SIZE}&offset=${offset}`, {}, fetcher);
    if (!response.ok) {
      state.error = response.status === 403 ? 'You are not assigned to this restaurant.'
        : response.status === 404 ? 'Restaurant not found.' : 'Could not load orders. Please reload the page.';
      return;
    }
    state.items = await response.json(); state.loaded = true;
  } catch { state.error = session.error || 'Could not load orders. Please reload the page.'; }
  finally { state.loading = false; }
}

export async function advanceOrder(state, session, restaurantId, order, fetcher = fetch) {
  if (state.loading || state.error || !nextStatus[order.status] || !['staff', 'admin'].includes(session.user?.role)) return;
  state.loading = true;
  try {
    const response = await authenticatedFetch(session, `/restaurants/${restaurantId}/orders/${order.id}/status`, {
      method: 'PATCH', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: nextStatus[order.status] }),
    }, fetcher);
    if (!response.ok) {
      state.error = response.status === 409 ? 'Order status changed. Reload the page before trying again.'
        : response.status === 403 ? 'You are not assigned to this restaurant.'
          : 'Could not confirm the update. Reload the page before trying again.';
      return;
    }
    const updated = await response.json();
    state.items = state.items.map(item => item.id === updated.id ? updated : item);
  } catch { state.error = session.error || 'Could not confirm the update. Reload the page before trying again.'; }
  finally { state.loading = false; }
}
