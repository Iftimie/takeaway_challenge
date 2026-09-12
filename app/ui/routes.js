const views = {
  '/register': { title: 'Create account', description: 'Register as a customer to place orders.' },
  '/restaurants': {
    title: 'Restaurants',
    description: 'Choose a restaurant to browse its menu.',
  },
  '/login': {
    title: 'Log in',
    description: 'Log in to your account. You can browse without logging in.',
  },
};

export function routeFromHash(hash) {
  return hash.slice(1) || '/restaurants';
}

export function viewForRoute(route) {
  if (menuRestaurantId(route)) return { title: 'Menu', description: 'Prices are in EUR.' };
  return Object.hasOwn(views, route) ? views[route] : {
    title: 'Page not found', description: 'Choose a page from the navigation.',
  };
}

export function menuRestaurantId(route) {
  const match = /^\/restaurants\/([1-9]\d*)\/menu$/.exec(route);
  const id = match ? Number(match[1]) : 0;
  return id <= 2147483647 ? id : 0;
}
