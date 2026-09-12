<script>
import { PAGE_SIZE } from '../api.js';
import { canGoNextOrders } from '../orders.js';
import { staffOrdersState, loadStaffOrders, advanceOrder, nextStatus } from '../staff-orders.js';
export default {
  props: ['session', 'restaurantId', 'page'],
  data() { return { orders: staffOrdersState(),
    actions: { pending: 'Accept order', accepted: 'Mark out for delivery', out_for_delivery: 'Mark delivered' } }; },
  computed: { hasNext() { return canGoNextOrders(this.orders); } },
  watch: {
    'session.user': { immediate: true, handler() { this.reset(); } },
    restaurantId() { this.reset(); },
  },
  methods: {
    reset() { this.orders = staffOrdersState(); this.load((this.page - 1) * PAGE_SIZE); },
    navigate(page) { window.location.hash = `/restaurants/${this.restaurantId}/orders?page=${page}`; },
    load(offset) { return loadStaffOrders(this.orders, this.session, this.restaurantId, offset); },
    advance(order) { return advanceOrder(this.orders, this.session, this.restaurantId, order); },
    nextStatus(status) { return nextStatus[status]; },
  },
};
</script>

<template>
  <section aria-label="Restaurant orders">
    <p>Restaurant #{{ restaurantId }}</p>
    <a :href="`#/restaurants/${restaurantId}/menu`">Back to menu</a>
    <p v-if="session.loading">Checking your account…</p>
    <p v-else-if="!session.user"><a href="#/login">Log in</a> as staff or admin to manage orders.</p>
    <p v-else-if="!['staff', 'admin'].includes(session.user.role)">Staff or admin access required.</p>
    <template v-else>
      <p v-if="orders.loading" role="status">Loading or updating orders…</p>
      <p v-if="orders.error" role="alert">{{ orders.error }}</p>
      <template v-else-if="orders.loaded">
        <p v-if="!orders.items.length">{{ orders.offset ? 'No more orders.' : 'No orders yet.' }}</p>
        <article v-for="order in orders.items" :key="order.id" :aria-label="`Order #${order.id}`">
          <h2>Order #{{ order.id }}</h2>
          <p>Status: {{ order.status }}</p>
          <p>{{ order.created_at }}</p>
          <p>Deliver to: {{ order.delivery_name }} — {{ order.delivery_address }}</p>
          <ul><li v-for="item in order.items" :key="item.menu_item_id">{{ item.name }} × {{ item.quantity }} — {{ item.unit_price }} EUR each</li></ul>
          <p>Total: {{ order.total }} {{ order.currency }}</p>
          <button v-if="nextStatus(order.status)" :disabled="orders.loading" @click="advance(order)">{{ actions[order.status] }}</button>
        </article>
      </template>
      <button :disabled="orders.loading || orders.offset === 0" @click="navigate(page - 1)">Previous</button>
      <span>Page {{ page }}</span>
      <button :disabled="!hasNext" @click="navigate(page + 1)">Next</button>
    </template>
  </section>
</template>
