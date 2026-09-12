import { PAGE_SIZE } from './api.js';
import { authenticatedFetch } from './session.js';

export function ordersState() {
  return { items: [], order: null, offset: 0, loading: false, loaded: false, error: '' };
}

export function canGoNextOrders(state) {
  return state.loaded && !state.loading && !state.error && state.items.length === PAGE_SIZE
    && state.offset + PAGE_SIZE <= 10000;
}

export async function loadOrders(state, session, orderId = 0, offset = 0, fetcher = fetch) {
  if (state.loading || session.user?.role !== 'customer') return;
  state.loading = true;
  state.error = '';
  state.items = [];
  state.order = null;
  state.loaded = false;
  state.offset = offset;
  try {
    const url = orderId ? `/orders/${orderId}` : `/orders?limit=${PAGE_SIZE}&offset=${offset}`;
    const response = await authenticatedFetch(session, url, {}, fetcher);
    if (!response.ok) {
      state.error = response.status === 404 ? 'Order not found.'
        : response.status === 403 ? 'Customer access required.' : 'Could not load orders. Please retry.';
      return;
    }
    const data = await response.json();
    if (orderId) state.order = data;
    else state.items = data;
    state.loaded = true;
  } catch { state.error = session.error || 'Could not load orders. Please retry.'; }
  finally { state.loading = false; }
}
