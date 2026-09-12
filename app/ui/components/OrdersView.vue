<script>
import { PAGE_SIZE } from '../api.js';
import { ordersState, loadOrders, canGoNextOrders } from '../orders.js';
export default {
  props: ['session', 'orderId'],
  data() { return { orders: ordersState(), pageSize: PAGE_SIZE }; },
  computed: { hasNext() { return canGoNextOrders(this.orders); } },
  watch: {
    'session.user': { immediate: true, handler() { this.reset(); } },
    orderId() { this.reset(); },
  },
  methods: {
    reset() {
      // Late responses update only the old visit's state, never the new view.
      this.orders = ordersState();
      this.load(0);
    },
    load(offset) { return loadOrders(this.orders, this.session, this.orderId, offset); },
  },
};
</script>

<template>
  <section aria-label="Customer orders">
    <p v-if="session.loading">Checking your account…</p>
    <p v-else-if="!session.user"><a href="#/login">Log in</a> as a customer to view your orders.</p>
    <p v-else-if="session.user.role !== 'customer'">Only customers can view their order history here.</p>
    <template v-else>
      <button :disabled="orders.loading" @click="load(orders.offset)">Refresh</button>
      <p v-if="orders.loading" role="status">Loading orders…</p>
      <p v-else-if="orders.error" role="alert">{{ orders.error }}</p>
      <template v-else-if="orders.order">
        <h2>Order #{{ orders.order.id }}</h2>
        <p>Status: {{ orders.order.status }}</p>
        <p>Placed: {{ orders.order.created_at }}</p>
        <p>Restaurant #{{ orders.order.restaurant_id }}</p>
        <p>Deliver to: {{ orders.order.delivery_name }} — {{ orders.order.delivery_address }}</p>
        <ul><li v-for="item in orders.order.items" :key="item.menu_item_id">{{ item.name }} × {{ item.quantity }} — {{ item.unit_price }} EUR each</li></ul>
        <p>Total: {{ orders.order.total }} {{ orders.order.currency }}</p>
      </template>
      <template v-else-if="orders.loaded && !orderId">
        <p v-if="!orders.items.length">{{ orders.offset ? 'No more orders.' : 'No orders yet.' }}</p>
        <ul v-else>
          <li v-for="order in orders.items" :key="order.id">
            <a :href="`#/orders/${order.id}`">Order #{{ order.id }}</a>
            — {{ order.status }} — {{ order.total }} {{ order.currency }}
            <p>Restaurant #{{ order.restaurant_id }} · {{ order.created_at }}</p>
          </li>
        </ul>
      </template>
      <div v-if="!orderId">
        <button :disabled="orders.loading || orders.offset === 0" @click="load(orders.offset - pageSize)">Previous</button>
        <button :disabled="!hasNext" @click="load(orders.offset + pageSize)">Next</button>
      </div>
    </template>
    <p v-if="orderId"><a href="#/orders">Back to orders</a></p>
  </section>
</template>
