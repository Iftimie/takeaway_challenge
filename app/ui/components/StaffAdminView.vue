<script>
import { staffAdminState, createStaff, assignStaff } from '../staff-admin.js';
export default {
  props: ['session'],
  data() { return { creation: staffAdminState(), assignment: staffAdminState(),
    name: '', email: '', password: '', staffId: '', restaurantId: '' }; },
  computed: { busy() { return this.creation.loading || this.assignment.loading; } },
  methods: {
    async create() {
      const password = this.password; this.password = '';
      await createStaff(this.creation, this.session, { name: this.name, email: this.email, password });
      if (this.creation.staff) { this.staffId = this.creation.staff.id; this.name = ''; this.email = ''; }
    },
    assign() { return assignStaff(this.assignment, this.session, Number(this.staffId), Number(this.restaurantId)); },
  },
};
</script>

<template>
  <section aria-label="Staff administration">
    <p v-if="session.loading">Checking your account…</p>
    <p v-else-if="!session.user"><a href="#/login">Log in</a> as an admin to manage staff.</p>
    <p v-else-if="session.user.role !== 'admin'">Admin access required.</p>
    <template v-else>
      <h2>Create staff account</h2>
      <p v-if="creation.error" role="alert">{{ creation.error }}</p>
      <p v-if="creation.staff" role="status">Staff created: {{ creation.staff.name }} (ID {{ creation.staff.id }})</p>
      <form @submit.prevent="create">
        <fieldset :disabled="busy">
          <label for="staff-name">Staff name</label><br>
          <input id="staff-name" v-model="name" required maxlength="200"><br>
          <label for="staff-email">Staff email</label><br>
          <input id="staff-email" v-model="email" type="email" required maxlength="320"><br>
          <label for="staff-password">Initial password</label><br>
          <input id="staff-password" v-model="password" type="password" autocomplete="new-password" required minlength="8" maxlength="128"><br>
          <button>Create staff</button>
        </fieldset>
      </form>
      <h2>Assign restaurant</h2>
      <p>Use the staff ID shown after creation (or an existing staff ID). Find the restaurant ID in its menu URL.</p>
      <p v-if="assignment.error" role="alert">{{ assignment.error }}</p>
      <p v-if="assignment.assignment" role="status">Staff #{{ assignment.assignment.staff_id }} assigned to restaurant #{{ assignment.assignment.restaurant_id }}.</p>
      <form @submit.prevent="assign">
        <fieldset :disabled="busy">
          <label for="staff-id">Staff ID</label><br>
          <input id="staff-id" v-model="staffId" type="number" required min="1" max="2147483647" step="1"><br>
          <label for="restaurant-id">Restaurant ID</label><br>
          <input id="restaurant-id" v-model="restaurantId" type="number" required min="1" max="2147483647" step="1"><br>
          <button>Assign restaurant</button>
        </fieldset>
      </form>
      <p v-if="busy" role="status">Saving…</p>
    </template>
  </section>
</template>
