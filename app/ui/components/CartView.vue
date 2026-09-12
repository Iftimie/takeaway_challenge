<script>
import { totalCents, formatMoney } from '../cart.js';
export default {
  props: ['cart'],
  emits: ['quantity', 'remove'],
  methods: { totalCents, formatMoney },
};
</script>

<template>
  <section aria-label="Shopping cart">
    <p v-if="!cart.items.length">Your cart is empty.</p>
    <template v-else>
      <h2>{{ cart.restaurant.name }}</h2>
      <ul>
        <li v-for="item in cart.items" :key="item.id">
          <strong>{{ item.name }}</strong> — {{ formatMoney(item.cents) }} each
          <label :for="`quantity-${item.id}`">Quantity for {{ item.name }}</label>
          <input :id="`quantity-${item.id}`" type="number" min="1" max="100" step="1" :value="item.quantity"
            @change="$emit('quantity', item.id, Number($event.target.value)); $event.target.value = item.quantity">
          <span>{{ formatMoney(item.cents * item.quantity) }}</span>
          <button @click="$emit('remove', item.id)">Remove {{ item.name }}</button>
        </li>
      </ul>
      <p>Estimated total: {{ formatMoney(totalCents(cart)) }}</p>
      <p>Prices and availability will be checked when ordering.</p>
      <a href="#/checkout">Checkout</a>
      <br>
      <a :href="`#/restaurants/${cart.restaurant.id}/menu`">Back to menu</a>
    </template>
  </section>
</template>
