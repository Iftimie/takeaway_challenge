export function registrationState() {
  return { loading: false, error: '', fields: {}, success: false };
}

export async function registerCustomer(state, form, fetcher = fetch) {
  if (state.loading) return;
  state.loading = true;
  state.error = '';
  state.fields = {};
  state.success = false;
  try {
    const response = await fetcher('/auth/register', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: form.email, password: form.password, name: form.name,
        default_address: form.default_address.trim() || null }),
    });
    if (response.status === 201) {
      state.success = true;
    } else if (response.status === 409) {
      state.fields.email = 'An account with this email already exists.';
    } else if (response.status === 422) {
      const body = await response.json();
      for (const error of body.detail) {
        const field = error.loc?.[1];
        if (['email', 'password', 'name', 'default_address'].includes(field)) {
          state.fields[field] = error.msg;
        }
      }
      state.error = 'Please check the highlighted fields.';
    } else {
      state.error = 'Could not create your account. Please try again.';
    }
  } catch {
    state.error = 'Could not confirm account creation. Try logging in, or retry registration.';
  } finally {
    state.loading = false;
  }
}
