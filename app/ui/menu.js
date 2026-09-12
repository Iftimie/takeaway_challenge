import { getMenuPage, PAGE_SIZE } from './api.js';

export function menuState(id) {
  return { id, restaurant: null, items: [], offset: 0, loading: false, loaded: false, error: '' };
}

export function canGoNextMenu(state) {
  return state.loaded && !state.loading && !state.error
    && state.items.length === PAGE_SIZE && state.offset + PAGE_SIZE <= 10000;
}

export async function loadMenu(state, offset, loader = getMenuPage) {
  if (state.loading) return;
  state.loading = true;
  state.error = '';
  state.offset = offset;
  state.items = [];
  try {
    const result = await loader(state.id, offset);
    state.restaurant = result.restaurant;
    state.items = result.items;
    state.loaded = true;
  } catch (error) {
    state.error = error.message === 'Restaurant not found.'
      ? error.message : 'Could not load menu. Please try again.';
  } finally {
    state.loading = false;
  }
}
