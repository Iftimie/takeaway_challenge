import { test } from 'node:test';
import assert from 'node:assert/strict';
import { emptyCart, addItem, setQuantity, removeItem, totalCents, formatMoney, saveCart, restoreCart } from '../../app/ui/cart.js';
const restaurant = { id: 1, name: 'Cafe' };
const item = { id: 1, name: 'Soup', price: '0.10', available: true };

test('cart merges quantities and calculates exact cents', () => {
  const cart = emptyCart();
  addItem(cart, restaurant, item);
  addItem(cart, restaurant, item);
  addItem(cart, restaurant, { ...item, id: 2, price: '0.20' });
  assert.equal(cart.items.length, 2);
  assert.equal(formatMoney(totalCents(cart)), '0.40 EUR');
  setQuantity(cart, 1, 3);
  assert.equal(totalCents(cart), 50);
  removeItem(cart, 1); removeItem(cart, 2);
  assert.equal(cart.restaurant, null);
});

test('cart rejects unavailable items, other restaurants and invalid quantities', () => {
  const cart = emptyCart();
  assert.throws(() => addItem(cart, restaurant, { ...item, available: false }));
  addItem(cart, restaurant, item);
  assert.throws(() => addItem(cart, { id: 2 }, item));
  for (const quantity of [0, -1, 1.5, 101, NaN]) assert.throws(() => setQuantity(cart, 1, quantity));
  setQuantity(cart, 1, 100);
  assert.throws(() => addItem(cart, restaurant, item));
  assert.equal(cart.items[0].quantity, 100);
});

test('cart enforces maximum distinct items', () => {
  const cart = emptyCart();
  for (let id = 1; id <= 100; id++) addItem(cart, restaurant, { ...item, id });
  assert.throws(() => addItem(cart, restaurant, { ...item, id: 101 }));
  assert.equal(cart.items.length, 100);
});

test('cart survives storage round trip and tolerates corrupt storage', () => {
  let value;
  const storage = { setItem: (key, data) => { value = data; }, getItem: () => value, removeItem: () => { value = null; } };
  const cart = emptyCart(); addItem(cart, restaurant, item); saveCart(cart, storage);
  assert.deepEqual(restoreCart(storage), cart);
  value = '{invalid'; assert.deepEqual(restoreCart(storage), emptyCart());
  value = JSON.stringify({ ...cart, items: [{ ...cart.items[0], quantity: -1 }] });
  assert.deepEqual(restoreCart(storage), emptyCart());
  saveCart(emptyCart(), storage); assert.equal(value, null);
});
