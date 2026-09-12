/* Hash navigation changes the view without reloading this page. */
const views = {
  '/restaurants': {
    title: 'Restaurants',
    description: 'Restaurant browsing will be available in the next UI milestone.',
  },
  '/login': {
    title: 'Log in',
    description: 'Login will be available in a later UI milestone.',
  },
};

Vue.createApp({
  data() {
    return { route: window.location.hash.slice(1) || '/restaurants' };
  },
  computed: {
    view() {
      return Object.hasOwn(views, this.route) ? views[this.route] : {
        title: 'Page not found', description: 'Choose a page from the navigation.',
      };
    },
  },
  mounted() {
    window.addEventListener('hashchange', () => {
      this.route = window.location.hash.slice(1) || '/restaurants';
    });
  },
}).mount('#app');
