/* Hash navigation changes the view without reloading this page. */
import { routeFromHash, viewForRoute } from './routes.js';
import { PAGE_SIZE } from './api.js';
import { restaurantState, canGoNext, loadRestaurants } from './restaurants.js';

Vue.createApp({
  data() {
    return { route: routeFromHash(window.location.hash), restaurants: restaurantState(), pageSize: PAGE_SIZE };
  },
  computed: {
    view() {
      return viewForRoute(this.route);
    },
    hasNextPage() { return canGoNext(this.restaurants); },
  },
  methods: {
    loadPage(offset) { return loadRestaurants(this.restaurants, offset); },
  },
  mounted() {
    if (this.route === '/restaurants') this.loadPage(0);
    window.addEventListener('hashchange', () => {
      this.route = routeFromHash(window.location.hash);
      if (this.route === '/restaurants' && !this.restaurants.loaded) this.loadPage(0);
    });
  },
}).mount('#app');
