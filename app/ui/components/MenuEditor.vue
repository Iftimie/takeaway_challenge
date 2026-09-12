<script>
import { editorState, saveMenuItem } from '../menu-editor.js';
export default {
  props: ['session', 'restaurantId', 'items'],
  emits: ['saved'],
  data() { return { state: editorState(), itemId: null, name: '', price: '', available: true }; },
  methods: {
    edit(item) {
      this.itemId = item?.id || null; this.name = item?.name || '';
      this.price = item?.price || ''; this.available = item?.available ?? true;
      this.state.error = ''; this.state.saved = false;
    },
    async save() {
      if (await saveMenuItem(this.state, this.session, this.restaurantId, this.itemId,
        { name: this.name, price: this.price, available: this.available })) {
        this.edit(null); this.state.saved = true; this.$emit('saved');
      }
    },
  },
};
</script>

<template>
  <section aria-label="Menu editor">
    <h2>Manage menu</h2>
    <p>Staff may save changes only for assigned restaurants. Admins may manage any restaurant.</p>
    <button :disabled="state.loading" @click="edit(null)">New menu item</button>
    <ul><li v-for="item in items" :key="item.id">
      <button :disabled="state.loading" @click="edit(item)">Edit {{ item.name }}</button>
    </li></ul>
    <h3>{{ itemId ? 'Edit menu item' : 'Create menu item' }}</h3>
    <p v-if="state.error" role="alert">{{ state.error }}</p>
    <p v-if="state.saved" role="status">Menu item saved.</p>
    <form @submit.prevent="save">
      <fieldset :disabled="state.loading">
        <label for="item-name">Item name</label>
        <input id="item-name" v-model="name" required maxlength="200">
        <label for="item-price">Price (EUR)</label>
        <input id="item-price" v-model="price" inputmode="decimal" required>
        <label><input v-model="available" type="checkbox">Available</label>
        <button>Save menu item</button>
      </fieldset>
    </form>
  </section>
</template>
