export const CART_KEY = 'takeaway.cart';

export function emptyCart() { return { restaurant: null, items: [] }; }

export function priceInCents(price) {
  if (!/^\d{1,8}(\.\d{1,2})?$/.test(String(price))) throw new Error('Invalid price');
  const [whole, fraction = ''] = String(price).split('.');
  const cents = Number(whole) * 100 + Number(fraction.padEnd(2, '0'));
  if (cents <= 0) throw new Error('Invalid price');
  return cents;
}

export function addItem(cart, restaurant, item) {
  if (!item.available) throw new Error('This item is unavailable.');
  if (cart.restaurant && cart.restaurant.id !== restaurant.id) throw new Error('Choose one restaurant per cart.');
  const existing = cart.items.find(line => line.id === item.id);
  if (existing?.quantity === 100) throw new Error('Maximum quantity is 100.');
  if (!existing && cart.items.length === 100) throw new Error('Maximum 100 different items.');
  const cents = priceInCents(item.price);
  cart.restaurant = { id: restaurant.id, name: restaurant.name };
  if (existing) existing.quantity += 1;
  else cart.items.push({ id: item.id, name: item.name, cents, quantity: 1 });
}

export function setQuantity(cart, id, quantity) {
  if (!Number.isInteger(quantity) || quantity < 1 || quantity > 100) throw new Error('Quantity must be a whole number from 1 to 100.');
  const line = cart.items.find(item => item.id === id);
  if (line) line.quantity = quantity;
}

export function removeItem(cart, id) {
  cart.items = cart.items.filter(item => item.id !== id);
  if (!cart.items.length) cart.restaurant = null;
}

export function totalCents(cart) {
  return cart.items.reduce((total, item) => total + item.cents * item.quantity, 0);
}

export function formatMoney(cents) {
  return `${Math.floor(cents / 100)}.${String(cents % 100).padStart(2, '0')} EUR`;
}

export function saveCart(cart, storage) {
  if (cart.items.length) storage.setItem(CART_KEY, JSON.stringify(cart));
  else storage.removeItem(CART_KEY);
}

export function restoreCart(storage) {
  try {
    const cart = JSON.parse(storage.getItem(CART_KEY));
    const validId = id => Number.isInteger(id) && id > 0 && id <= 2147483647;
    if (!cart || !validId(cart.restaurant?.id) || typeof cart.restaurant.name !== 'string'
        || !Array.isArray(cart.items) || !cart.items.length || cart.items.length > 100
        || new Set(cart.items.map(item => item.id)).size !== cart.items.length
        || cart.items.some(item => !validId(item.id) || typeof item.name !== 'string'
          || !Number.isInteger(item.cents) || item.cents < 1 || item.cents > 9999999999
          || !Number.isInteger(item.quantity) || item.quantity < 1 || item.quantity > 100)) {
      return emptyCart();
    }
    return cart;
  } catch { return emptyCart(); }
}
