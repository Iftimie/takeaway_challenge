"""Disposable browser database only; never reads the application .env."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.update({
    'POSTGRES_DB': 'takeaway_browser_test', 'POSTGRES_USER': 'browser_test',
    'POSTGRES_PASSWORD': 'browser_test_only', 'POSTGRES_HOST': '127.0.0.1',
    'POSTGRES_PORT': '55432',
})

from sqlalchemy import delete, text, select
from sqlalchemy.orm import Session
from app.db import get_engine
from app.models import Restaurant, MenuItem, User, Order, OrderItem, StaffAssignment
from app.auth.service import password_hasher


def compose(*args):
    subprocess.run(['docker', '--context', 'desktop-linux', 'compose', '-p',
                    'takeaway-browser-tests', '-f', str(ROOT / 'compose.browser-tests.yaml'),
                    *args], cwd=ROOT, check=True)


def fixtures(seed, orders=False, staff=False):
    # The fixed endpoint and identity check prevent cleanup of the normal DB.
    with Session(get_engine()) as session:
        if (session.scalar(text('SELECT current_database()')) != 'takeaway_browser_test'
                or session.scalar(text('SELECT current_user')) != 'browser_test'):
            raise RuntimeError('Refusing fixture changes outside the browser test database')
        session.execute(delete(StaffAssignment))
        session.execute(delete(OrderItem))
        session.execute(delete(Order))
        session.execute(delete(MenuItem))
        session.execute(delete(Restaurant))
        session.execute(delete(User))
        if seed:
            session.add(User(email='browser-customer@example.com', name='Browser Customer',
                             role='customer', password_hash=password_hasher.hash('Browser-test-password-123!')))
            restaurants = [Restaurant(name=f'Browser Restaurant {i}', address=f'Test Street {i}')
                           for i in range(1, 4)]
            session.add_all(restaurants)
            session.flush()
            session.add_all([MenuItem(restaurant_id=restaurants[0].id, name=f'Test Meal {i}',
                                     price='12.50', available=i != 2) for i in range(1, 4)])
            session.add(MenuItem(restaurant_id=restaurants[1].id, name='Other Restaurant Meal',
                                 price='9.00', available=True))
        if staff:
            worker = User(email='browser-staff@example.com', name='Browser Staff', role='staff',
                          password_hash=password_hasher.hash('Browser-test-password-123!'))
            session.add(worker)
            session.add(User(email='browser-admin@example.com', name='Browser Admin', role='admin',
                             password_hash=password_hasher.hash('Browser-test-password-123!')))
            session.flush()
            session.add(StaffAssignment(staff_id=worker.id, restaurant_id=restaurants[0].id))
        if orders:
            session.flush()
            customer = session.scalar(select(User))
            item = session.scalar(select(MenuItem).order_by(MenuItem.id))
            for index in range(3):
                order = Order(customer_id=customer.id, restaurant_id=item.restaurant_id,
                              delivery_name='Browser Customer', delivery_address='History Street 10',
                              status='pending', total='12.50', currency='EUR',
                              idempotency_key=f'history-{index}', request_fingerprint='0' * 64)
                session.add(order)
                session.flush()
                session.add(OrderItem(order_id=order.id, menu_item_id=item.id,
                                      name=item.name, unit_price=item.price, quantity=1))
        session.commit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare', 'seed', 'seed-orders', 'seed-menu', 'clean', 'stop'])
    action = parser.parse_args().action
    if action == 'prepare':
        try:
            compose('up', '-d', '--wait')
            subprocess.run([sys.executable, '-m', 'alembic', 'upgrade', 'head'], cwd=ROOT, check=True)
        except BaseException:
            compose('down')
            raise
    elif action == 'stop':
        compose('down')
    else:
        fixtures(action in ('seed', 'seed-orders', 'seed-menu'), orders=action == 'seed-orders', staff=action == 'seed-menu')
