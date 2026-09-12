import { authenticatedFetch } from './session.js';

const KEY = 'takeaway.checkout';

export function checkoutState(storage) {
  let pending = null;
  try { pending = JSON.parse(storage.getItem(KEY)); } catch { /* No saved checkout. */ }
  return { pending, loading: false, error: '', order: null };
}

export async function placeOrder(state, session, cart, details, storage, fetcher = fetch) {
  if (state.loading || session.loading) return;
  state.error = '';
  if (session.user?.role !== 'customer') {
    state.error = 'Log in as a customer to place an order.';
    return;
  }
  if (state.pending && state.pending.customerId !== session.user.id) {
    state.error = 'Log in with the account that started this checkout.';
    return;
  }
  state.loading = true;
  try {
    if (!state.pending) {
      if (!cart.items.length || !details.name.trim() || !details.address.trim()) {
        state.error = 'A cart, delivery name and address are required.';
        return;
      }
      const pending = {
        customerId: session.user.id, key: crypto.randomUUID(),
        payload: {
          restaurant_id: cart.restaurant.id,
          delivery_name: details.name.trim(), delivery_address: details.address.trim(),
          items: cart.items.map(item => ({ menu_item_id: item.id, quantity: item.quantity })),
        },
      };
      // Persist before sending: a refresh must not create a new key for an uncertain order.
      storage.setItem(KEY, JSON.stringify(pending));
      state.pending = pending;
    }
    const response = await authenticatedFetch(session, '/orders', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Idempotency-Key': state.pending.key },
      body: JSON.stringify(state.pending.payload),
    }, fetcher);
    if ([403, 404, 409, 422].includes(response.status)) {
      const messages = {
        403: 'Customer access required.',
        404: 'Restaurant not found. Please update your cart.',
        409: 'An item is unavailable or the request conflicts. Please review your cart.',
        422: 'Check your delivery details and cart items before trying again.',
      };
      storage.removeItem(KEY);
      state.pending = null;
      state.error = messages[response.status];
      return;
    }
    if (response.status !== 200 && response.status !== 201) throw new Error();
    const order = await response.json();
    storage.removeItem(KEY);
    state.pending = null;
    state.order = order;
    return order;
  } catch {
    state.error = session.error || (state.pending
      ? 'Could not confirm the order. Retry the saved request to check its outcome.'
      : 'Could not save checkout in this tab. No order was sent.');
  } finally { state.loading = false; }
}
