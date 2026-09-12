<script>
import { registrationState, registerCustomer } from '../registration.js';

export default {
  data() {
    return { state: registrationState(), email: '', password: '', name: '', default_address: '' };
  },
  methods: {
    async submit() {
      const form = { email: this.email, password: this.password, name: this.name, default_address: this.default_address };
      this.password = '';
      await registerCustomer(this.state, form);
      if (this.state.success) {
        this.email = this.name = this.default_address = '';
      }
    },
  },
};
</script>

<template>
  <section aria-label="Customer registration">
    <div v-if="state.success" role="status">
      <p>Account created. You can now log in.</p>
      <a href="#/login">Go to login</a>
    </div>
    <form v-else @submit.prevent="submit">
      <p v-if="state.error" role="alert">{{ state.error }}</p>
      <p v-if="state.loading" role="status">Creating account…</p>
      <p>
        <label for="register-email">Email</label><br>
        <input id="register-email" v-model="email" type="email" required maxlength="320" autocomplete="username" :disabled="state.loading" :aria-invalid="!!state.fields.email" aria-describedby="email-error">
        <span id="email-error" class="field-error">{{ state.fields.email }}</span>
      </p>
      <p>
        <label for="register-password">Password (8–128 characters)</label><br>
        <input id="register-password" v-model="password" type="password" required minlength="8" maxlength="128" autocomplete="new-password" :disabled="state.loading" :aria-invalid="!!state.fields.password" aria-describedby="password-error">
        <span id="password-error" class="field-error">{{ state.fields.password }}</span>
      </p>
      <p>
        <label for="register-name">Name</label><br>
        <input id="register-name" v-model="name" required maxlength="200" autocomplete="name" :disabled="state.loading" :aria-invalid="!!state.fields.name" aria-describedby="name-error">
        <span id="name-error" class="field-error">{{ state.fields.name }}</span>
      </p>
      <p>
        <label for="register-address">Default delivery address (optional)</label><br>
        <textarea id="register-address" v-model="default_address" maxlength="1000" autocomplete="street-address" :disabled="state.loading" :aria-invalid="!!state.fields.default_address" aria-describedby="address-error"></textarea>
        <span id="address-error" class="field-error">{{ state.fields.default_address }}</span>
      </p>
      <button type="submit" :disabled="state.loading">Create account</button>
      <p>Already registered? <a href="#/login">Go to login</a></p>
    </form>
  </section>
</template>
