const TOKEN_KEY = 'takeaway.access_token';

export function sessionState(storage = null) {
  return { token: '', user: null, loading: false, error: '', storage };
}

export function logout(state) {
  state.storage?.removeItem(TOKEN_KEY);
  state.token = '';
  state.user = null;
  state.error = '';
}

// Reuse this for future protected API calls; public browsing sends no token.
export async function authenticatedFetch(state, url, options = {}, fetcher = fetch) {
  const response = await fetcher(url, {
    ...options, headers: { ...options.headers, Authorization: `Bearer ${state.token}` },
  });
  if (response.status === 401) {
    logout(state);
    state.error = 'Your login has expired. Please log in again.';
    throw new Error(state.error);
  }
  return response;
}

export async function restoreSession(state, fetcher = fetch) {
  if (state.loading) return;
  state.token = state.storage?.getItem(TOKEN_KEY) || state.token;
  if (!state.token) return;
  state.loading = true;
  state.error = '';
  try {
    const response = await authenticatedFetch(state, '/users/me', {}, fetcher);
    if (!response.ok) throw new Error();
    state.user = await response.json();
  } catch {
    state.error ||= 'Could not load your account. Please try again.';
  } finally {
    state.loading = false;
  }
}

export async function login(state, email, password, fetcher = fetch) {
  if (state.loading) return;
  logout(state);
  state.loading = true;
  try {
    const response = await fetcher('/auth/login', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!response.ok) {
      state.error = response.status === 401 ? 'Invalid email or password.'
        : response.status === 422 ? 'Check your email and password.'
          : 'Could not log in. Please try again.';
      return;
    }
    const credentials = await response.json();
    // Only expose a logged-in session after the server confirms the user/role.
    const profile = await fetcher('/users/me', {
      headers: { Authorization: `Bearer ${credentials.access_token}` },
    });
    if (!profile.ok) throw new Error();
    const user = await profile.json();
    state.storage?.setItem(TOKEN_KEY, credentials.access_token);
    state.token = credentials.access_token;
    state.user = user;
  } catch {
    state.error = 'Could not log in. Please try again.';
  } finally {
    state.loading = false;
  }
}
