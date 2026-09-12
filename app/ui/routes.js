const views = {
  '/restaurants': {
    title: 'Restaurants',
    description: 'Browse restaurants. Menu browsing is coming next.',
  },
  '/login': {
    title: 'Log in',
    description: 'Login will be available in a later UI milestone.',
  },
};

export function routeFromHash(hash) {
  return hash.slice(1) || '/restaurants';
}

export function viewForRoute(route) {
  return Object.hasOwn(views, route) ? views[route] : {
    title: 'Page not found', description: 'Choose a page from the navigation.',
  };
}
