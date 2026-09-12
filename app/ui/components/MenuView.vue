<script>
export default {
  props: ['menu', 'pageSize', 'hasNextMenuPage'],
  emits: ['load-page'],
};
</script>

<template>
  <section aria-label="Restaurant menu" :aria-busy="menu.loading">
    <a href="#/restaurants">Back to restaurants</a>
    <h2 v-if="menu.restaurant">{{ menu.restaurant.name }}</h2>
    <p v-if="menu.loading" role="status">Loading menu…</p>
    <div v-else-if="menu.error" role="alert">
      <p>{{ menu.error }}</p>
      <button @click="$emit('load-page', menu.offset)">Retry</button>
    </div>
    <template v-else-if="menu.loaded">
      <p v-if="!menu.items.length">{{ menu.offset === 0 ? 'No menu items yet.' : 'No more menu items.' }}</p>
      <ul v-else>
        <li v-for="item in menu.items" :key="item.id">
          <strong>{{ item.name }}</strong> — {{ item.price }} {{ item.currency }}
          <span>{{ item.available ? 'Available' : 'Unavailable' }}</span>
        </li>
      </ul>
    </template>
    <nav aria-label="Menu pages">
      <button @click="$emit('load-page', menu.offset - pageSize)" :disabled="menu.loading || menu.offset === 0">Previous</button>
      <span>Page {{ menu.offset / pageSize + 1 }}</span>
      <button @click="$emit('load-page', menu.offset + pageSize)" :disabled="!hasNextMenuPage">Next</button>
    </nav>
  </section>
</template>
