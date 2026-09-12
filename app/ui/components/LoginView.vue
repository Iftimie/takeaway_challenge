<script>
export default {
  props: ['session', 'email', 'password'],
  emits: ['update:email', 'update:password', 'submit'],
};
</script>

<template>
  <section aria-label="Account">
    <p v-if="session.error" role="alert">{{ session.error }}</p>
    <p v-if="session.loading" role="status">Loading account…</p>
    <div v-if="session.user">
      <p role="status">Logged in as {{ session.user.email }}.</p>
    </div>
    <form v-else @submit.prevent="$emit('submit')">
      <p><label for="email">Email</label><br>
        <input id="email" type="email" :value="email" @input="$emit('update:email', $event.target.value)" autocomplete="username" required maxlength="320" :disabled="session.loading"></p>
      <p><label for="password">Password</label><br>
        <input id="password" type="password" :value="password" @input="$emit('update:password', $event.target.value)" autocomplete="current-password" required maxlength="128" :disabled="session.loading"></p>
      <button type="submit" :disabled="session.loading">Log in</button>
    </form>
  </section>
</template>
