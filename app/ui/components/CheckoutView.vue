<script>
import { totalCents, formatMoney } from '../cart.js';
export default {
  props: ['checkout', 'session', 'cart'],
  emits: ['submit'],
  data() { return { name: '', address: '' }; },
  watch: {
    'session.user': { immediate: true, handler(user) {
      if (user) { this.name = user.name; this.address = user.default_address || ''; }
    } },
  },
  methods: { totalCents, formatMoney },
};
</script>

<template>
  <section aria-label="Checkout">
    <p v-if="checkout.error" role="alert">{{ checkout.error }}</p>
    <template v-if="checkout.order">
      <h2>Order confirmed</h2>
      <a :href="`#/orders/${checkout.order.id}`">View order details</a>
      <p>Order #{{ checkout.order.id }} — {{ checkout.order.status }}</p>
      <ul><li v-for="item in checkout.order.items" :key="item.menu_item_id">{{ item.name }} × {{ item.quantity }} — {{ item.unit_price }} EUR each</li></ul>
      <p>Total: {{ checkout.order.total }} {{ checkout.order.currency }}</p>
    </template>
    <p v-else-if="session.loading">Checking your account…</p>
    <p v-else-if="!session.user"><a href="#/login">Log in</a> as a customer, then return to checkout.</p>
    <p v-else-if="session.user.role !== 'customer'">Only customers can place orders.</p>
    <template v-else-if="checkout.pending">
      <p>A saved checkout is awaiting confirmation. Retry uses the same details and cannot create a second order for this request.</p>
      <p>{{ checkout.pending.payload.delivery_name }} — {{ checkout.pending.payload.delivery_address }}</p>
      <button :disabled="checkout.loading" @click="$emit('submit', { name, address })">Retry order</button>
    </template>
    <p v-else-if="!cart.items.length">Your cart is empty.</p>
    <form v-else @submit.prevent="$emit('submit', { name, address })">
      <p>{{ cart.restaurant.name }} — Estimated total: {{ formatMoney(totalCents(cart)) }}</p>
      <p>The server checks current prices and availability when placing your order.</p>
      <label for="delivery-name">Delivery name</label>
      <input id="delivery-name" v-model="name" required maxlength="200" :disabled="checkout.loading">
      <label for="delivery-address">Delivery address</label>
      <textarea id="delivery-address" v-model="address" required maxlength="1000" :disabled="checkout.loading"></textarea>
      <button :disabled="checkout.loading">Place order</button>
    </form>
    <p v-if="checkout.loading" role="status">Placing order…</p>
    <a href="#/cart">Back to cart</a>
  </section>
</template>
