import { listRestaurants, PAGE_SIZE } from './api.js';

export function restaurantState() {
  return { items: [], offset: 0, loading: false, error: '', loaded: false };
}

export function canGoNext(state) {
  return state.loaded && !state.loading && !state.error
    && state.items.length === PAGE_SIZE && state.offset + PAGE_SIZE <= 10000;
}

export async function loadRestaurants(state, offset, loader = listRestaurants) {
  if (state.loading) return;
  state.loading = true;
  state.error = '';
  state.offset = offset;
  state.items = [];
  try {
    state.items = await loader(offset);
    state.loaded = true;
  } catch {
    state.error = 'Could not load restaurants. Please try again.';
  } finally {
    state.loading = false;
  }
}
