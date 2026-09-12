<script>
import { restaurantCreateState, createRestaurant } from '../restaurant-create.js';
export default {
  props: ['session'],
  emits: ['created'],
  data() { return { state: restaurantCreateState(), name: '', address: '' }; },
  methods: {
    async submit() {
      await createRestaurant(this.state, this.session, { name: this.name, address: this.address });
      if (this.state.restaurant) { this.name = ''; this.address = ''; this.$emit('created'); }
    },
  },
};
</script>

<template>
  <section aria-label="Create restaurant">
    <p v-if="session.loading">Checking your account…</p>
    <p v-else-if="!session.user"><a href="#/login">Log in</a> as an admin to create a restaurant.</p>
    <p v-else-if="session.user.role !== 'admin'">Admin access required.</p>
    <template v-else>
      <div v-if="state.restaurant" role="status">
        <p>Restaurant created: {{ state.restaurant.name }} — {{ state.restaurant.address }}</p>
        <a :href="`#/restaurants/${state.restaurant.id}/menu`">Open restaurant menu</a>
      </div>
      <form v-else @submit.prevent="submit">
        <p v-if="state.error" role="alert">{{ state.error }}</p>
        <p v-if="state.loading" role="status">Creating restaurant…</p>
        <fieldset :disabled="state.loading">
          <label for="restaurant-name">Restaurant name</label><br>
          <input id="restaurant-name" v-model="name" required maxlength="200"><br>
          <label for="restaurant-address">Restaurant address</label><br>
          <textarea id="restaurant-address" v-model="address" required maxlength="1000"></textarea><br>
          <button>Create restaurant</button>
        </fieldset>
      </form>
    </template>
    <p><a href="#/restaurants">Back to restaurants</a></p>
  </section>
</template>
