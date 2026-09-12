/* Hash navigation changes the view without reloading this page. */
import { routeFromHash, viewForRoute, menuRestaurantId } from './routes.js';
import { menuState, loadMenu, canGoNextMenu } from './menu.js';
import { PAGE_SIZE } from './api.js';
import { restaurantState, canGoNext, loadRestaurants } from './restaurants.js';

Vue.createApp({
  data() {
    return { route: routeFromHash(window.location.hash), restaurants: restaurantState(), pageSize: PAGE_SIZE, menu: menuState(0) };
  },
  computed: {
    view() {
      return viewForRoute(this.route);
    },
    hasNextPage() { return canGoNext(this.restaurants); },
    menuId() { return menuRestaurantId(this.route); },
    hasNextMenuPage() { return canGoNextMenu(this.menu); },
  },
  methods: {
    loadPage(offset) { return loadRestaurants(this.restaurants, offset); },
    loadMenuPage(offset) { return loadMenu(this.menu, offset); },
    loadView() {
      if (this.route === '/restaurants' && !this.restaurants.loaded) this.loadPage(0);
      if (this.menuId) {
        // Separate state per visit keeps late responses from changing another menu.
        this.menu = menuState(this.menuId);
        this.loadMenuPage(0);
      }
    },
  },
  mounted() {
    this.loadView();
    window.addEventListener('hashchange', () => {
      this.route = routeFromHash(window.location.hash);
      this.loadView();
    });
  },
}).mount('#app');
