<script>
import StaffOrdersView from './components/StaffOrdersView.vue';
import MenuEditor from './components/MenuEditor.vue';
import OrdersView from './components/OrdersView.vue';
import CheckoutView from './components/CheckoutView.vue';
import { checkoutState, placeOrder } from './checkout.js';
import CartView from './components/CartView.vue';
import { emptyCart, restoreCart, saveCart, addItem, setQuantity, removeItem } from './cart.js';
import RegisterView from './components/RegisterView.vue';
import LoginView from './components/LoginView.vue';
import RestaurantList from './components/RestaurantList.vue';
import MenuView from './components/MenuView.vue';
/* Hash navigation changes the view without reloading this page. */
import { routeFromHash, viewForRoute, menuRestaurantId, customerOrderId, staffRestaurantId, staffOrdersPage } from './routes.js';
import { menuState, loadMenu, canGoNextMenu } from './menu.js';
import { PAGE_SIZE } from './api.js';
import { restaurantState, canGoNext, loadRestaurants } from './restaurants.js';
import { sessionState, login, logout, restoreSession } from './session.js';

export default {
  components: { LoginView, RestaurantList, MenuView, RegisterView, CartView, CheckoutView, OrdersView, MenuEditor, StaffOrdersView },
  data() {
    return { route: routeFromHash(window.location.hash), restaurants: restaurantState(), pageSize: PAGE_SIZE, menu: menuState(0),
      session: sessionState(window.sessionStorage), email: '', password: '',
      cart: restoreCart(window.sessionStorage), cartMessage: '', checkout: checkoutState(window.sessionStorage) };
  },
  computed: {
    view() {
      return viewForRoute(this.route);
    },
    hasNextPage() { return canGoNext(this.restaurants); },
    menuId() { return menuRestaurantId(this.route); },
    orderId() { return customerOrderId(this.route); },
    staffRestaurantId() { return staffRestaurantId(this.route); },
    staffPage() { return staffOrdersPage(this.route); },
    hasNextMenuPage() { return canGoNextMenu(this.menu); },
  },
  methods: {
    cartLocked() {
      if (!this.checkout.pending && !this.checkout.loading) return false;
      this.cartMessage = 'Finish the saved checkout before changing your cart.';
      return true;
    },
    async submitOrder(details) {
      const order = await placeOrder(this.checkout, this.session, this.cart, details, window.sessionStorage);
      if (order) { this.cart = emptyCart(); saveCart(this.cart, window.sessionStorage); }
    },
    addToCart(item) {
      if (this.cartLocked()) return;
      this.checkout.order = null;
      if (!item.available) return;
      if (this.cart.restaurant && this.cart.restaurant.id !== this.menu.restaurant.id) {
        if (!window.confirm('Replace your cart with items from this restaurant?')) return;
        this.cart = emptyCart();
      }
      try {
        addItem(this.cart, this.menu.restaurant, item);
        saveCart(this.cart, window.sessionStorage);
        this.cartMessage = `${item.name} added to cart.`;
      } catch (error) { this.cartMessage = error.message; }
    },
    changeQuantity(id, quantity) {
      if (this.cartLocked()) return;
      try {
        setQuantity(this.cart, id, quantity);
        saveCart(this.cart, window.sessionStorage);
        this.cartMessage = '';
      } catch (error) { this.cartMessage = error.message; }
    },
    removeFromCart(id) {
      if (this.cartLocked()) return;
      removeItem(this.cart, id);
      saveCart(this.cart, window.sessionStorage);
      this.cartMessage = '';
    },
    async submitLogin() {
      const password = this.password;
      this.password = '';
      await login(this.session, this.email, password);
    },
    signOut() {
      if (this.checkout.loading) return;
      this.checkout.order = null;
      logout(this.session);
      // Keep an uncertain request so signing back in can resolve it safely.
      if (!this.checkout.pending) {
        this.cart = emptyCart();
        saveCart(this.cart, window.sessionStorage);
      }
      this.email = '';
      this.password = '';
      window.location.hash = '/login';
    },
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
    restoreSession(this.session);
    this.loadView();
    window.addEventListener('hashchange', () => {
      this.route = routeFromHash(window.location.hash);
      this.cartMessage = '';
      this.password = '';
      this.loadView();
    });
  },
};

</script>

<template>
  <div>
    <header>
      <strong>Takeaway Service</strong>
      <nav aria-label="Main navigation">
        <a href="#/restaurants" :aria-current="route === '/restaurants' ? 'page' : null">Restaurants</a>
        <a v-if="session.user?.role === 'customer'" href="#/orders">My orders</a>
        <a href="#/cart" :aria-current="route === '/cart' ? 'page' : null">Cart ({{ cart.items.reduce((sum, item) => sum + item.quantity, 0) }})</a>
        <a href="#/login" :aria-current="route === '/login' ? 'page' : null">{{ session.user ? 'Account' : 'Log in' }}</a>
        <span v-if="session.user">{{ session.user.name }} ({{ session.user.role }})</span>
        <a v-if="!session.user" href="#/register" :aria-current="route === '/register' ? 'page' : null">Register</a>
        <button v-if="session.user" @click="signOut" :disabled="session.loading || checkout.loading">Log out</button>
      </nav>
    </header>
    <main>
      <h1>{{ view.title }}</h1>
      <StaffOrdersView v-if="staffRestaurantId" :key="route" :session="session" :restaurant-id="staffRestaurantId" :page="staffPage" />
      <p v-if="menuId && ['staff', 'admin'].includes(session.user?.role)"><a :href="`#/restaurants/${menuId}/orders`">Manage orders</a></p>
      <OrdersView v-if="route === '/orders' || orderId" :session="session" :order-id="orderId" />
      <p>{{ view.description }}</p>
      <p v-if="cartMessage" role="status">{{ cartMessage }}</p>
      <p v-if="checkout.pending && route !== '/checkout'"><a href="#/checkout">Return to saved checkout</a></p>
      <CheckoutView v-if="route === '/checkout'" :checkout="checkout" :session="session" :cart="cart" @submit="submitOrder" />
      <CartView v-if="route === '/cart'" :cart="cart" @quantity="changeQuantity" @remove="removeFromCart" />
      <RegisterView v-if="route === '/register'" />
      <LoginView v-if="route === '/login'" :session="session" v-model:email="email" v-model:password="password" @submit="submitLogin" />
      <RestaurantList v-if="route === '/restaurants'" :restaurants="restaurants" :page-size="pageSize" :has-next-page="hasNextPage" @load-page="loadPage" />
      <MenuView v-if="menuId" :menu="menu" :page-size="pageSize" :has-next-menu-page="hasNextMenuPage" @load-page="loadMenuPage" @add-item="addToCart" />
      <MenuEditor v-if="menuId && menu.restaurant && ['staff', 'admin'].includes(session.user?.role)"
        :key="`${menuId}-${session.user.id}`" :session="session" :restaurant-id="menuId" :items="menu.items"
        @saved="loadMenuPage(menu.offset)" />
    </main>
    <footer>UI preview · <a href="/docs">API documentation</a></footer>
  </div>
</template>
