export const PAGE_SIZE = 2;

export async function listRestaurants(offset, fetcher = fetch) {
  const response = await fetcher(`/restaurants?limit=${PAGE_SIZE}&offset=${offset}`);
  if (!response.ok) throw new Error('Could not load restaurants. Please try again.');
  return response.json();
}
