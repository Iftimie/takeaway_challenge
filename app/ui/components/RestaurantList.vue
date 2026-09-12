<script>
export default {
  props: ['restaurants', 'pageSize', 'hasNextPage'],
  emits: ['load-page'],
};
</script>

<template>
  <section aria-label="Restaurant list" :aria-busy="restaurants.loading">
    <p v-if="restaurants.loading" role="status">Loading restaurants…</p>
    <div v-else-if="restaurants.error" role="alert">
      <p>{{ restaurants.error }}</p>
      <button @click="$emit('load-page', restaurants.offset)">Retry</button>
    </div>
    <template v-else-if="restaurants.loaded">
      <p v-if="restaurants.items.length === 0">{{ restaurants.offset === 0 ? 'No restaurants yet.' : 'No more restaurants.' }}</p>
      <ul v-else>
        <li v-for="restaurant in restaurants.items" :key="restaurant.id">
          <strong>{{ restaurant.name }}</strong><br>{{ restaurant.address }}
          <br><a :href="`#/restaurants/${restaurant.id}/menu`">View menu</a>
        </li>
      </ul>
    </template>
    <nav aria-label="Restaurant pages">
      <button @click="$emit('load-page', restaurants.offset - pageSize)" :disabled="restaurants.loading || restaurants.offset === 0">Previous</button>
      <span>Page {{ restaurants.offset / pageSize + 1 }}</span>
      <button @click="$emit('load-page', restaurants.offset + pageSize)" :disabled="!hasNextPage">Next</button>
    </nav>
  </section>
</template>
