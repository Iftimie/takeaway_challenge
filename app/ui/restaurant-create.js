import { authenticatedFetch } from './session.js';

export function restaurantCreateState() { return { loading: false, error: '', restaurant: null }; }

export async function createRestaurant(state, session, form, fetcher = fetch) {
  if (state.loading) return;
  state.error = ''; state.restaurant = null;
  if (session.user?.role !== 'admin') { state.error = 'Admin access required.'; return; }
  const name = form.name.trim(); const address = form.address.trim();
  if (!name || name.length > 200 || !address || address.length > 1000) {
    state.error = 'Enter a name (up to 200 characters) and address (up to 1000 characters).'; return;
  }
  state.loading = true;
  try {
    const response = await authenticatedFetch(session, '/restaurants', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, address }),
    }, fetcher);
    if (response.status === 201) state.restaurant = await response.json();
    else state.error = response.status === 403 ? 'Admin access required.'
      : response.status === 422 ? 'Check the restaurant name and address.'
        : 'Could not confirm creation. Check the restaurant list before trying again.';
  } catch { state.error = session.error || 'Could not confirm creation. Check the restaurant list before trying again.'; }
  finally { state.loading = false; }
}
