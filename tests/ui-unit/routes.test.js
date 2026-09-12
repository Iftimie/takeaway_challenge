import { test } from 'node:test';
import assert from 'node:assert/strict';
import { routeFromHash, viewForRoute } from '../../app/ui/routes.js';

test('empty hash selects restaurants', () => {
  for (const hash of ['', '#']) {
    assert.equal(routeFromHash(hash), '/restaurants');
    assert.equal(viewForRoute(routeFromHash(hash)).title, 'Restaurants');
  }
});

test('known hashes select their views', () => {
  for (const [hash, title] of [['#/restaurants', 'Restaurants'], ['#/login', 'Log in']]) {
    const view = viewForRoute(routeFromHash(hash));
    assert.equal(view.title, title);
    assert.equal(typeof view.description, 'string');
  }
});

test('unknown hashes select a fallback, including inherited object names', () => {
  for (const hash of ['#/missing', '#toString', '#__proto__']) {
    assert.equal(viewForRoute(routeFromHash(hash)).title, 'Page not found');
  }
});
