export const PAGE_SIZE = 2;

export async function getMenuPage(id, offset, fetcher = fetch) {
  const responses = await Promise.all([
    fetcher(`/restaurants/${id}`),
    fetcher(`/restaurants/${id}/menu-items?limit=${PAGE_SIZE}&offset=${offset}`),
  ]);
  if (responses.some(response => response.status === 404)) {
    throw new Error('Restaurant not found.');
  }
  if (responses.some(response => !response.ok)) throw new Error('Could not load menu. Please try again.');
  const [restaurant, items] = await Promise.all(responses.map(response => response.json()));
  return { restaurant, items };
}

export async function listRestaurants(offset, fetcher = fetch) {
  const response = await fetcher(`/restaurants?limit=${PAGE_SIZE}&offset=${offset}`);
  if (!response.ok) throw new Error('Could not load restaurants. Please try again.');
  return response.json();
}
