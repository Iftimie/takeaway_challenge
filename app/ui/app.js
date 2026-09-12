/* Hash navigation changes the view without reloading this page. */
import { routeFromHash, viewForRoute } from './routes.js';

Vue.createApp({
  data() {
    return { route: routeFromHash(window.location.hash) };
  },
  computed: {
    view() {
      return viewForRoute(this.route);
    },
  },
  mounted() {
    window.addEventListener('hashchange', () => {
      this.route = routeFromHash(window.location.hash);
    });
  },
}).mount('#app');
